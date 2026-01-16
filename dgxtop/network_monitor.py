"""
Network I/O monitoring module for DGXTOP Ubuntu
Handles reading network interface statistics from:
- Regular interfaces: /sys/class/net/*/statistics/
- RoCE/InfiniBand interfaces: /sys/class/infiniband/*/ports/*/counters/
Calculates transfer speeds for both interface types
"""

import subprocess
import sys
import os
import pathlib

import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque
try:
    # Try relative import first (when used as package module)
    from .ibifc import parse_ibdev2netdev
except ImportError:
    # Fall back to absolute import (when run standalone)
    from ibifc import parse_ibdev2netdev

@dataclass
class NetworkStats:
    """Container for network interface statistics"""

    interface_name: str
    rx_bytes: int = 0  # Total bytes received
    tx_bytes: int = 0  # Total bytes transmitted
    rx_packets: int = 0  # Total packets received
    tx_packets: int = 0  # Total packets transmitted
    rx_errors: int = 0  # Receive errors
    tx_errors: int = 0  # Transmit errors
    rx_dropped: int = 0  # Receive dropped
    tx_dropped: int = 0  # Transmit dropped
    # Calculated rates (set after delta calculation)
    rx_bytes_per_sec: float = 0.0  # Receive rate
    tx_bytes_per_sec: float = 0.0  # Transmit rate
    rx_packets_per_sec: float = 0.0
    tx_packets_per_sec: float = 0.0


class NetworkMonitor:
    """Monitor network interface statistics for both regular and RoCE/InfiniBand interfaces
    
    Automatically detects interface type and uses the appropriate data source:
    - Regular interfaces: /sys/class/net/<interface>/statistics/
    - RoCE interfaces: /sys/class/infiniband/<device>/ports/<port>/counters/
    """

    # Interfaces to exclude from display
    EXCLUDED_INTERFACES = ("lo", "virbr", "docker", "br-", "veth")

    def __init__(self):
        self.netdev_path = "/proc/net/dev"
        self.previous_stats: Dict[str, NetworkStats] = {}
        self.last_update_time = time.time()
        # History tracking for sparklines (matches disk_monitor pattern)
        self.rx_history = deque(maxlen=60)
        self.tx_history = deque(maxlen=60)
        # Cache the InfiniBand device to interface mapping
        self._ibdev_mapping: Optional[Dict[str, str]] = None
        self._update_ibdev_mapping()

#------------------------------------------------------------------------------
    def _update_ibdev_mapping(self):
        """Update the InfiniBand device to network interface mapping"""
        try:
            self._ibdev_mapping = parse_ibdev2netdev()
        except (FileNotFoundError, subprocess.SubprocessError):
            # ibdev2netdev not available, no RoCE interfaces
            self._ibdev_mapping = {}

    def _is_roce_interface(self, interface_name: str) -> bool:
        """Check if interface is a RoCE (InfiniBand) interface"""
        if self._ibdev_mapping is None:
            self._update_ibdev_mapping()
        # Check if interface is in the mapping (bidirectional, so either direction works)
        return interface_name in self._ibdev_mapping

    def _get_ibdev_from_interface(self, interface_name: str) -> Optional[str]:
        """Get InfiniBand device name from network interface name"""
        if self._ibdev_mapping is None:
            self._update_ibdev_mapping()
        return self._ibdev_mapping.get(interface_name)

    def _read_roce_counters(self, device: str, port: int = 1) -> Optional[tuple]:
        """
        Reads RoCE counters from /sys/class/infiniband/<device>/ports/{port}/counters/
        Returns (tx_pkts, tx_bytes, rx_pkts, rx_bytes, rx_errors, tx_errors) or None on error
        """
        try:
            base = pathlib.Path(f"/sys/class/infiniband/{device}/ports/{port}/counters")
            
            tx_pkts_file = base / "port_xmit_packets"
            tx_bytes_file = base / "port_xmit_data"
            rx_pkts_file = base / "port_rcv_packets"
            rx_bytes_file = base / "port_rcv_data"
            tx_discard_file = base / "port_xmit_discards"
            rx_error_file = base / "port_rcv_errors"

            def read_counter_file(filepath: pathlib.Path) -> int:
                try:
                    with open(filepath, "r") as f:
                        return int(f.read().strip())
                except (IOError, ValueError):
                    return 0

            tx_pkts = read_counter_file(tx_pkts_file)
            tx_bytes = read_counter_file(tx_bytes_file)
            rx_pkts = read_counter_file(rx_pkts_file)
            rx_bytes = read_counter_file(rx_bytes_file)
            tx_discards = read_counter_file(tx_discard_file)
            rx_errors = read_counter_file(rx_error_file)
            
            return tx_pkts, tx_bytes, rx_pkts, rx_bytes, rx_errors, tx_discards
        except (IOError, OSError):
            return None

    def _is_displayable_interface(self, interface_name: str) -> bool:
        """Check if interface should be displayed (exclude virtual interfaces)"""
        # Exclude loopback and virtual interfaces
        for prefix in self.EXCLUDED_INTERFACES:
            if interface_name.startswith(prefix):
                return False
        return True

#------------------------------------------------------------------------------
    def _read_interface_stats(self, interface_name: str) -> Optional[NetworkStats]:
        """
        Read statistics for a network interface.
        For regular interfaces: reads from /sys/class/net/<interface>/statistics/
        For RoCE interfaces: reads from /sys/class/infiniband/{device}/ports/1/counters/
        """
        # Check if this is a RoCE interface
        if self._is_roce_interface(interface_name):
            # Get InfiniBand device name from interface name
            ib_device = self._get_ibdev_from_interface(interface_name)
            if ib_device is None:
                # Mapping not found, try regular interface stats
                return self._read_regular_interface_stats(interface_name)
            
            # Read RoCE counters from InfiniBand
            roce_data = self._read_roce_counters(ib_device, port=1)
            if roce_data is None:
                return None
            
            tx_pkts, tx_bytes, rx_pkts, rx_bytes, rx_errors, tx_errors = roce_data
            
            # RoCE counters: rx_bytes maps to port_rcv_data, tx_bytes to port_xmit_data
            # rx_errors from port_rcv_errors, tx_errors from port_xmit_discards
            return NetworkStats(
                interface_name=interface_name,
                rx_bytes=rx_bytes,
                tx_bytes=tx_bytes,
                rx_packets=rx_pkts,
                tx_packets=tx_pkts,
                rx_errors=rx_errors,
                tx_errors=tx_errors,
                rx_dropped=0,  # RoCE doesn't have dropped counters in standard location
                tx_dropped=0,
            )
        else:
            # Regular network interface - read from standard location
            return self._read_regular_interface_stats(interface_name)

    def _read_regular_interface_stats(self, interface_name: str) -> Optional[NetworkStats]:
        """Read statistics for a regular network interface from /sys/class/net/<interface>/statistics/"""
        base_path = f"/sys/class/net/{interface_name}/statistics"
        
        def read_stat_file(filename: str) -> int:
            try:
                with open(f"{base_path}/{filename}", "r") as f:
                    return int(f.read().strip())
            except (IOError, ValueError):
                return 0

        try:
            stat = NetworkStats(
                interface_name=interface_name,
                rx_bytes=read_stat_file("rx_bytes"),
                rx_packets=read_stat_file("rx_packets"),
                rx_errors=read_stat_file("rx_errors"),
                rx_dropped=read_stat_file("rx_dropped"),
                tx_bytes=read_stat_file("tx_bytes"),
                tx_packets=read_stat_file("tx_packets"),
                tx_errors=read_stat_file("tx_errors"),
                tx_dropped=read_stat_file("tx_dropped"),
            )
            return stat
        except IOError:
            # Interface doesn't exist or can't be read
            return None
#------------------------------------------------------------------------------
    def _get_available_interfaces(self) -> List[str]:
        """
        Get list of connected network interfaces

        Run ``nmcli device status`` and return a list of device names whose
        STATE column is exactly ``"connected"`` and does not contain
        (externally).
        """
        # --------------------------------------------------------------
        # 1️⃣  Execute the command
        # --------------------------------------------------------------
        try:
            result = subprocess.run(
                ["nmcli", "device", "status"],
                capture_output=True,
                text=True,
                check=True,          # raise if exit status != 0
            )
        except FileNotFoundError:
            sys.stderr.write("Error: nmcli not found in PATH.\n")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"Error running nmcli: {e.stderr}\n")
            sys.exit(1)

        # --------------------------------------------------------------
        # 2️⃣  Split output into lines and drop the header
        # --------------------------------------------------------------
        lines = result.stdout.strip().splitlines()
        if not lines:
            return []                     # nothing to parse

        data_lines = lines[1:]            # skip header
        connected_devices: List[str] = []

        # --------------------------------------------------------------
        # 3️⃣  Parse each line
        # --------------------------------------------------------------
        for line in data_lines:
            # ``split()`` collapses any whitespace and gives us the fields.
            parts = line.split()
            if len(parts) < 4:               # malformed line – ignore safely
                continue

            device, _, state, external = parts[0], parts[1], parts[2], parts[3]
            # ----------------------------------------------------------
            # 4️⃣  Keep ONLY when STATE is exactly "connected"
            # and external is not "(externally)"
            # ----------------------------------------------------------
            if state.strip() == "connected":
                if external.strip() != "(externally)":
                    connected_devices.append(device)

        return connected_devices
    # --------------------------------------------------------------
    def _parse_net_dev(self) -> List[NetworkStats]:
        """Parse network interface statistics from all available interfaces
        
        Handles both regular and RoCE interfaces automatically
        """
        stats = []
        available_interfaces = self._get_available_interfaces()

        for interface_name in available_interfaces:
            stat = self._read_interface_stats(interface_name)
            if stat:
                stats.append(stat)

        return stats

    def _calculate_transfer_rates(
        self, current_stats: List[NetworkStats]
    ) -> Dict[str, NetworkStats]:
        """Calculate transfer rates based on previous stats"""
        current_time = time.time()
        time_delta = current_time - self.last_update_time

        if time_delta <= 0:
            return {}

        result = {}

        for current in current_stats:
            if current.interface_name in self.previous_stats:
                previous = self.previous_stats[current.interface_name]

                # Calculate rates
                rx_bytes_delta = current.rx_bytes - previous.rx_bytes
                tx_bytes_delta = current.tx_bytes - previous.tx_bytes
                rx_packets_delta = current.rx_packets - previous.rx_packets
                tx_packets_delta = current.tx_packets - previous.tx_packets

                current.rx_bytes_per_sec = rx_bytes_delta / time_delta
                current.tx_bytes_per_sec = tx_bytes_delta / time_delta
                current.rx_packets_per_sec = rx_packets_delta / time_delta
                current.tx_packets_per_sec = tx_packets_delta / time_delta

                result[current.interface_name] = current
            else:
                # First time seeing this interface
                result[current.interface_name] = current

        # Update previous stats
        self.previous_stats = {stat.interface_name: stat for stat in current_stats}
        self.last_update_time = current_time

        # Update history for sparklines (store in bytes/sec for UI flexibility)
        # Only sum displayable interfaces to avoid double-counting
        total_rx = sum(
            s.rx_bytes_per_sec
            for s in current_stats
            if self._is_displayable_interface(s.interface_name)
        )
        total_tx = sum(
            s.tx_bytes_per_sec
            for s in current_stats
            if self._is_displayable_interface(s.interface_name)
        )
        self.rx_history.append(total_rx)
        self.tx_history.append(total_tx)

        return result

    def get_stats(self) -> Dict[str, NetworkStats]:
        """Get current network statistics with transfer rates"""
        current_stats = self._parse_net_dev()
        return self._calculate_transfer_rates(current_stats)

    def get_interface_stats_for_display(self) -> Dict[str, Dict[str, float]]:
        """Get network stats formatted for display (matches disk pattern)"""
        stats = self.get_stats()
        if not stats:
            return {}

        display_stats = {}
        for interface_name, stat in stats.items():
            if not self._is_displayable_interface(interface_name):
                continue

            display_stats[interface_name] = {
                "rx_rate": stat.rx_bytes_per_sec,
                "tx_rate": stat.tx_bytes_per_sec,
                "rx_packets": stat.rx_packets_per_sec,
                "tx_packets": stat.tx_packets_per_sec,
                "rx_errors": stat.rx_errors,
                "tx_errors": stat.tx_errors,
            }

        # Sort interfaces: Wi-Fi first, then other physical interfaces
        def get_interface_priority(interface_name: str) -> int:
            """Return priority for sorting - lower numbers appear first"""
            if interface_name.startswith("wl"):  # Wi-Fi interfaces
                return 0
            elif any(
                interface_name.startswith(prefix) for prefix in ("en", "eth", "em")
            ):  # Ethernet interfaces
                return 1
            else:
                return 2  # Other physical interfaces

        # Sort by priority, then alphabetically
        sorted_interfaces = sorted(
            display_stats.keys(), key=lambda x: (get_interface_priority(x), x)
        )

        # Create new dict with sorted order
        sorted_display_stats = {
            iface: display_stats[iface] for iface in sorted_interfaces
        }

        return sorted_display_stats

    def get_history(self) -> dict:
        """Get historical data for sparkline charts"""
        return {"rx": list(self.rx_history), "tx": list(self.tx_history)}

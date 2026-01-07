"""
Network I/O monitoring module for DGXTOP Ubuntu
Handles reading /sys/class/net/*/statistics/ and calculating transfer speeds
"""

import subprocess
import sys

import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

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
    """Monitor network interface statistics from /sys/class/net/*/statistics/"""

    # Interfaces to exclude from display
    EXCLUDED_INTERFACES = ("lo", "virbr", "docker", "br-", "veth")

    def __init__(self):
        self.netdev_path = "/proc/net/dev"
        self.previous_stats: Dict[str, NetworkStats] = {}
        self.last_update_time = time.time()
        # History tracking for sparklines (matches disk_monitor pattern)
        self.rx_history = deque(maxlen=60)
        self.tx_history = deque(maxlen=60)

    def _is_displayable_interface(self, interface_name: str) -> bool:
        """Check if interface should be displayed (exclude virtual interfaces)"""
        # Exclude loopback and virtual interfaces
        for prefix in self.EXCLUDED_INTERFACES:
            if interface_name.startswith(prefix):
                return False
        return True

    def _read_interface_stats(self, interface_name: str) -> Optional[NetworkStats]:
        """Read statistics for a specific interface from /sys/class/net/<interface>/statistics/"""
        base_path = f"/sys/class/net/{interface_name}/statistics"

        try:
            # Read all statistics files
            def read_stat_file(filename: str) -> int:
                try:
                    with open(f"{base_path}/{filename}", "r") as f:
                        return int(f.read().strip())
                except (IOError, ValueError):
                    return 0

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
        """Parse network interface statistics from /sys/class/net/*/statistics/"""
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

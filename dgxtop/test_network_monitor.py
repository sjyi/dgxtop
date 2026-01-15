#!/usr/bin/env python3
"""
Test program for network_monitor.py
Tests both regular network interfaces and RoCE/InfiniBand interfaces
"""

import sys
import time
try:
    # Try relative import first (when used as package module)
    from .network_monitor import NetworkMonitor, NetworkStats
except ImportError:
    # Fall back to absolute import (when run standalone)
    from network_monitor import NetworkMonitor, NetworkStats


def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    else:
        print(f"{'='*70}\n")


def format_bytes(bytes_val: float) -> str:
    """Format bytes with appropriate unit"""
    if bytes_val < 1024:
        return f"{bytes_val:.2f} B/s"
    elif bytes_val < 1024**2:
        return f"{bytes_val / 1024:.2f} KB/s"
    elif bytes_val < 1024**3:
        return f"{bytes_val / 1024**2:.2f} MB/s"
    else:
        return f"{bytes_val / 1024**3:.2f} GB/s"


def test_initialization():
    """Test NetworkMonitor initialization"""
    print_separator("Test 1: Initialization")
    try:
        monitor = NetworkMonitor()
        print("✓ NetworkMonitor initialized successfully")
        print(f"  - Excluded interfaces: {monitor.EXCLUDED_INTERFACES}")
        print(f"  - IB device mapping: {len(monitor._ibdev_mapping) if monitor._ibdev_mapping else 0} entries")
        if monitor._ibdev_mapping:
            print("  - RoCE interfaces found:")
            for iface, device in monitor._ibdev_mapping.items():
                if not iface.startswith("roce"):  # Show interface -> device mapping
                    print(f"    {iface} -> {device}")
        return monitor
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_interface_detection(monitor: NetworkMonitor):
    """Test interface detection methods"""
    print_separator("Test 2: Interface Detection")
    
    # Get available interfaces
    try:
        interfaces = monitor._get_available_interfaces()
        print(f"✓ Found {len(interfaces)} connected interfaces:")
        for iface in interfaces:
            is_roce = monitor._is_roce_interface(iface)
            is_displayable = monitor._is_displayable_interface(iface)
            roce_marker = " [RoCE]" if is_roce else ""
            display_marker = " [DISPLAYABLE]" if is_displayable else " [HIDDEN]"
            print(f"  - {iface}{roce_marker}{display_marker}")
            
            if is_roce:
                ib_device = monitor._get_ibdev_from_interface(iface)
                print(f"    → InfiniBand device: {ib_device}")
    except Exception as e:
        print(f"✗ Interface detection failed: {e}")
        import traceback
        traceback.print_exc()


def test_reading_stats(monitor: NetworkMonitor):
    """Test reading statistics from interfaces"""
    print_separator("Test 3: Reading Interface Statistics")
    
    try:
        interfaces = monitor._get_available_interfaces()
        if not interfaces:
            print("⚠ No interfaces available for testing")
            return
        
        for iface in interfaces:  # Test all interfaces
            print(f"\n  Testing interface: {iface}")
            stat = monitor._read_interface_stats(iface)
            
            if stat:
                print(f"    ✓ Successfully read stats")
                print(f"    - RX Bytes: {stat.rx_bytes:,}")
                print(f"    - TX Bytes: {stat.tx_bytes:,}")
                print(f"    - RX Packets: {stat.rx_packets:,}")
                print(f"    - TX Packets: {stat.tx_packets:,}")
                print(f"    - RX Errors: {stat.rx_errors}")
                print(f"    - TX Errors: {stat.tx_errors}")
                print(f"    - RX Dropped: {stat.rx_dropped}")
                print(f"    - TX Dropped: {stat.tx_dropped}")
            else:
                print(f"    ✗ Failed to read stats (interface may not exist or be accessible)")
    except Exception as e:
        print(f"✗ Reading stats failed: {e}")
        import traceback
        traceback.print_exc()


def test_rate_calculation(monitor: NetworkMonitor):
    """Test rate calculation over time"""
    print_separator("Test 4: Rate Calculation (2 samples)")
    
    try:
        print("  Collecting first sample...")
        stats1 = monitor.get_stats()
        print(f"  ✓ First sample: {len(stats1)} interfaces")
        
        # Wait a bit for rates to be meaningful
        print("  Waiting 2 seconds for rate calculation...")
        time.sleep(2)
        
        print("  Collecting second sample...")
        stats2 = monitor.get_stats()
        print(f"  ✓ Second sample: {len(stats2)} interfaces")
        
        print("\n  Rate Statistics:")
        for iface_name in sorted(stats2.keys()):  # Show all interfaces
            stat = stats2[iface_name]
            print(f"\n    Interface: {iface_name}")
            print(f"      RX Rate: {format_bytes(stat.rx_bytes_per_sec)}")
            print(f"      TX Rate: {format_bytes(stat.tx_bytes_per_sec)}")
            print(f"      RX Packets/s: {stat.rx_packets_per_sec:.2f}")
            print(f"      TX Packets/s: {stat.tx_packets_per_sec:.2f}")
    except Exception as e:
        print(f"✗ Rate calculation failed: {e}")
        import traceback
        traceback.print_exc()


def test_display_format(monitor: NetworkMonitor):
    """Test display formatting"""
    print_separator("Test 5: Display Format")
    
    try:
        display_stats = monitor.get_interface_stats_for_display()
        print(f"✓ Display stats: {len(display_stats)} interfaces")
        
        if display_stats:
            print("\n  Formatted Statistics:")
            for iface, stats in display_stats.items():  # Show all interfaces
                print(f"\n    {iface}:")
                print(f"      RX: {format_bytes(stats['rx_rate'])}")
                print(f"      TX: {format_bytes(stats['tx_rate'])}")
                print(f"      RX Packets/s: {stats['rx_packets']:.2f}")
                print(f"      TX Packets/s: {stats['tx_packets']:.2f}")
                print(f"      Errors: {stats['rx_errors'] + stats['tx_errors']}")
    except Exception as e:
        print(f"✗ Display format failed: {e}")
        import traceback
        traceback.print_exc()


def test_history(monitor: NetworkMonitor):
    """Test history tracking"""
    print_separator("Test 6: History Tracking")
    
    try:
        # Collect a few samples to build history
        print("  Collecting 5 samples for history...")
        for i in range(5):
            monitor.get_stats()
            time.sleep(0.5)
        
        history = monitor.get_history()
        print(f"✓ History collected")
        print(f"  - RX history: {len(history['rx'])} samples")
        print(f"  - TX history: {len(history['tx'])} samples")
        
        if history['rx']:
            print(f"  - Latest RX: {format_bytes(history['rx'][-1])}")
        if history['tx']:
            print(f"  - Latest TX: {format_bytes(history['tx'][-1])}")
    except Exception as e:
        print(f"✗ History tracking failed: {e}")
        import traceback
        traceback.print_exc()


def test_roce_specific(monitor: NetworkMonitor):
    """Test RoCE-specific functionality"""
    print_separator("Test 7: RoCE-Specific Tests")
    
    try:
        interfaces = monitor._get_available_interfaces()
        roce_interfaces = [iface for iface in interfaces if monitor._is_roce_interface(iface)]
        
        if not roce_interfaces:
            print("⚠ No RoCE interfaces found")
            print("  (This is normal if ibdev2netdev is not available or no RoCE interfaces are connected)")
            return
        
        print(f"✓ Found {len(roce_interfaces)} RoCE interface(s)")
        
        for iface in roce_interfaces:
            print(f"\n  Testing RoCE interface: {iface}")
            ib_device = monitor._get_ibdev_from_interface(iface)
            print(f"    InfiniBand device: {ib_device}")
            
            # Test reading RoCE counters directly
            roce_data = monitor._read_roce_counters(ib_device, port=1)
            if roce_data:
                tx_pkts, tx_bytes, rx_pkts, rx_bytes, rx_errors, tx_errors = roce_data
                print(f"    ✓ RoCE counters read successfully:")
                print(f"      TX Packets: {tx_pkts:,}")
                print(f"      TX Bytes: {tx_bytes:,}")
                print(f"      RX Packets: {rx_pkts:,}")
                print(f"      RX Bytes: {rx_bytes:,}")
                print(f"      RX Errors: {rx_errors}")
                print(f"      TX Errors: {tx_errors}")
            else:
                print(f"    ✗ Failed to read RoCE counters")
            
            # Test reading via interface stats
            stat = monitor._read_interface_stats(iface)
            if stat:
                print(f"    ✓ Interface stats via unified method:")
                print(f"      RX Bytes: {stat.rx_bytes:,}")
                print(f"      TX Bytes: {stat.tx_bytes:,}")
    except Exception as e:
        print(f"✗ RoCE-specific test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  NetworkMonitor Test Suite")
    print("="*70)
    
    # Test 1: Initialization
    monitor = test_initialization()
    if monitor is None:
        print("\n✗ Cannot continue without NetworkMonitor instance")
        sys.exit(1)
    
    # Test 2: Interface Detection
    test_interface_detection(monitor)
    
    # Test 3: Reading Stats
    test_reading_stats(monitor)
    
    # Test 4: Rate Calculation
    test_rate_calculation(monitor)
    
    # Test 5: Display Format
    test_display_format(monitor)
    
    # Test 6: History
    test_history(monitor)
    
    # Test 7: RoCE Specific
    test_roce_specific(monitor)
    
    print_separator("Test Summary")
    print("✓ All tests completed\n")


if __name__ == "__main__":
    main()

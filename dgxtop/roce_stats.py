import pathlib

def get_roce_counters(device: str = "roceP2p1s0f1", port: int = 1):
    """
    Reads the raw counters from /sys/class/infiniband/<device>/ports/1/counters/...
    Returns (tx_pkts, tx_bytes, rx_pkts, rx_bytes).

    Device choices are: roce01s0f0, rocep1s0f1, roceP2p1s0f0, roceP2p1s0f1

    For testing purposes, only roceP2p1s0f1 will be used.

    The following files will be read to retrieve the appropriate stats
    for packets and bytes

    port_xmit_data
    port_xmit_packets

    port_rcv_data
    port_rcv_packets

    port_xmit_discards
    port_rcv_errors

    """
    base = pathlib.Path(f"/sys/class/infiniband/{device}/ports/{port}/counters")
    # print(f"Counters directory: {base}")
    # The actual files are named e.g. tx_pkts, tx_bytes, etc.
    # Example:
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
    
    return tx_pkts, tx_bytes, rx_pkts, rx_bytes, (rx_errors + tx_discards)


from time import sleep
from roce_stats import get_roce_counters

def monitor(interval: float = 1.0):
    """Print a live counter every `interval` seconds."""
    tx_p, tx_b, rx_p, rx_b, er = get_roce_counters()
    tx_p_old = tx_p
    tx_b_old = tx_b 
    rx_p_old = rx_p
    rx_b_old = rx_b
    er_old = er

    while True:
        sleep(interval)
        tx_p, tx_b, rx_p, rx_b, er = get_roce_counters()

        tx_p_diff = tx_p - tx_p_old
        tx_b_diff = tx_b - tx_b_old
        rx_p_diff = rx_p - rx_p_old
        rx_b_diff = rx_b - rx_b_old
        er_diff = er - er_old

        tx_p_old = tx_p
        tx_b_old = tx_b 
        rx_p_old = rx_p
        rx_b_old = rx_b
        er_old = er

        print(f"Tx {tx_p_diff:}, pkts, {tx_b_diff:,} B Rx: {rx_p_diff:,} pkts, {rx_b_diff:,} B Err: {er_diff}")

if __name__ == "__main__":
    monitor(2.0)

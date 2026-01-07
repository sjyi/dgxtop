#!/usr/bin/env python3
"""
Return a list of NM device names whose STATE column is exactly "connected".

The script:
  1. Executes ``nmcli device status``.
  2. Skips the header line.
  3. Splits each line on whitespace to obtain the columns:
        DEVICE  TYPE  STATE   CONNECTED‑TO …
  4. Keeps a device only when the STATE column, after stripping surrounding
     whitespace, equals the literal string "connected".
  5. Prints the matching device names (one per line) or returns them as a
     Python list when imported.
"""

import subprocess
import sys
from typing import List


def get_connected_devices() -> List[str]:
    """
    Run ``nmcli device status`` and return a list of device names whose
    STATE column is exactly ``"connected"``.
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
                print(f"appending Device: {device}, State: {state}, External: {external}")
    return connected_devices


# ----------------------------------------------------------------------
# 5️⃣  Command‑line interface (optional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    devices = get_connected_devices()
    if devices:
        print("\n".join(devices))
    else:
        print("(no devices are in the exact 'connected' state)", file=sys.stderr)
        sys.exit(0)


import subprocess
import re


def parse_ibdev2netdev(output=None):
    """
    Parse ibdev2netdev output and create bidirectional lookup dictionary.
    
    Args:
        output: Optional string output. If None, runs ibdev2netdev command.
    
    Returns:
        dict that maps device -> interface and interface -> device
    """
    if output is None:
        result = subprocess.run(['ibdev2netdev'], capture_output=True, text=True)
        output = result.stdout
    
    mapping = {}
    
    # Pattern: device port N ==> interface (Status)
    pattern = r'^(\S+)\s+port\s+\d+\s+==>\s+(\S+)\s+\(\w+\)'
    
    for line in output.strip().split('\n'):
        match = re.match(pattern, line)
        if match:
            device, interface = match.groups()
            # Bidirectional mapping
            mapping[device] = interface
            mapping[interface] = device
    
    return mapping


if __name__ == '__main__':
    sample_output = """rocep1s0f0 port 1 ==> enp1s0f0np0 (Down)
rocep1s0f1 port 1 ==> enp1s0f1np1 (Up)
roceP2p1s0f0 port 1 ==> enP2p1s0f0np0 (Down)
roceP2p1s0f1 port 1 ==> enP2p1s0f1np1 (Up)"""

    mapping = parse_ibdev2netdev(sample_output)
   
    dev_name = "rocep1s0f0"
    ifc_name = "enp1s0f1np1"

    # Lookup by device -> returns interface
    print(f"{dev_name} -> {mapping[dev_name]}")      
    
    # Lookup by interface -> returns device
    print(f"{ifc_name} -> {mapping[ifc_name]}")     
    
    # Safe lookup with .get()
    print(mapping.get('unknown', 'not found'))  # not found

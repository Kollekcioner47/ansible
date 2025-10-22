#!/usr/bin/env python3
import json, subprocess

def scan_network(subnet="10.0.3.0/24"):
    result = subprocess.check_output(["nmap", "-p22", "--open", subnet,"-oG","-"]).decode()
    hosts = [line.split()[1] for line in result.split('\n') if "Ports: 22/open" in line]
    return {
        "_meta":{"hostvars": {h: {"ansible_user": "engineer"} for h in hosts}},
        "all": {"hosts": hosts}
    }
if __name__ == "__main__":
    print(json.dumps(scan_network()))

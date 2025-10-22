#!/usr/bin/env python3
import json, subprocess

users_to_try = ["engineer","sa"]

def scan_network_for_ssh(subnet="10.0.3.0/24"):
    try:
        nmap_cmd = ["nmap", "-p", "22", "--open", "-oG","-", subnet]
        output = subprocess.check_output(nmap_cmd).decode()
        hosts= []
        for line in output.splitlines():
            if "Ports: 22/open" in line:
                parts = line.split()
                for part in parts:
                    if part.startswith("Host:"):
                        hosts.append(part.split("Host:")[1])
        return hosts
    except Exception as e:
        return []
def is_linux_host(ip, user):
    try:
        ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", f"{user}@{ip}", "uname"]
        output = subprocess.check_output(ssh_cmd, stderr=subprocess.DEVNULL).decode().strip()
        return output == "Linux"
    except Exception:
        return False
    
def scan_network():
    subnet = "10.0.3.0/24"
    hosts_found = scan_network_for_ssh(subnet)
    valid_hosts = {}

    for ip in hosts_found:
        for user in users_to_try:
            if is_linux_host(ip, user):
                valid_hosts[ip] = user
                break
    return {
        "_meta": {
            "hostvars": {
                ip: {"ansible_user": user, "ansible_system": "Linux"} for ip, user in valid_hosts.items()
            }
        },
        "all": {
            "hosts": list(valid_hosts.keys())
        }
    }
if __name__ == "__main__":
    print(json.dumps(scan_network()))

#!/usr/bin/env python3
import json, subprocess

def is_linux_host(ip):
    try:
        # Простая проверка через SSH без аутентификации
        result = subprocess.run([
            "ssh", "-o", "ConnectTimeout=3", 
            "-o", "BatchMode=yes",
            f"engineer@{ip}", "uname"
        ], capture_output=True, timeout=5)
        return result.returncode == 0 and "Linux" in result.stdout.decode()
    except:
        return False

def scan_network(subnet="10.0.3.0/24"):
    result = subprocess.check_output(["nmap", "-p22", "--open", subnet,"-oG","-"]).decode()
    hosts = [line.split()[1] for line in result.split('\n') if "Ports: 22/open" in line]
    
    # Фильтруем только Linux хосты
    linux_hosts = [h for h in hosts if is_linux_host(h)]
    
    return {
        "_meta":{"hostvars": {h: {"ansible_user": "engineer"} for h in linux_hosts}},
        "all": {"hosts": linux_hosts}
    }

if __name__ == "__main__":
    print(json.dumps(scan_network()))

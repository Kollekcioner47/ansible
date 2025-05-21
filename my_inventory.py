#!/usr/bin/env python3
import json, subprocess

hosts = ["srv1","srv2"]

inventory = {"all": {"hosts":[]}, "_meta": {"hostvars":{}}}

for h in hosts:
    result = subprocess.run(["dig", "+short", h],
                            capture_output=True, text=True)
    ip = result.stdout.strip().split("\h")[0]
    inventory["all"]["hosts"].append(h)
    inventory["_meta"]["hostvars"][h] = {"ansible_host": ip}

print(json.dumps(inventory))
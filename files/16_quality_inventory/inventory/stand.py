#!/usr/bin/env python3
"""Внешний инвентарь учебного стенда: плагин ansible.builtin.script.

Ansible вызывает файл двумя способами:

  inventory/stand.py --list        — отдай весь инвентарь;
  inventory/stand.py --host web1   — отдай переменные одного хоста.

Ответ на --list — один объект JSON: ключи, кроме служебного _meta, —
имена групп (у группы бывают hosts, vars и children), а в _meta.hostvars
лежат переменные хостов: так Ansible получает их одним запросом.

Скрипт обязан быть исполняемым (chmod +x) и печатать только JSON.
"""

import json
import sys

HOSTS = {"web1": "10.0.2.11", "web2": "10.0.2.12", "db1": "10.0.2.13"}
SSH_USER = "engineer"
SSH_KEY = "/home/engineer/.ssh/id_ed25519"

# Группы по назначению и группы из групп.
GROUPS = {"web": ["web1", "web2"], "db": ["db1"]}
CHILDREN = {"linux": ["web", "db"], "debian": ["web"], "redhat": ["db"]}


def inventory() -> dict:
    """Собирает инвентарь. Ничего не печатает: данные проверяются
    отдельно от запуска скрипта."""
    hostvars = {
        name: {
            "ansible_host": address,
            "ansible_user": SSH_USER,
            "ansible_ssh_private_key_file": SSH_KEY,
        }
        for name, address in HOSTS.items()
    }
    data = {"_meta": {"hostvars": hostvars}, "all": {"children": ["linux"]}}
    for group, hosts in GROUPS.items():
        data[group] = {"hosts": hosts}
    for group, children in CHILDREN.items():
        data[group] = {"children": children}
    return data


def main(argv=None) -> int:
    """Печатает JSON. Это и есть работа скрипта как программы."""
    args = list(sys.argv[1:] if argv is None else argv)
    if "--host" in args:
        # Запасной режим: Ansible спрашивает переменные одного хоста.
        name = args[args.index("--host") + 1]
        payload = inventory()["_meta"]["hostvars"].get(name, {})
    else:
        payload = inventory()
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

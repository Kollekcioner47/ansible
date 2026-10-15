#!/usr/bin/env python3
"""Переводит короткие имена фактов на форму ansible_facts['...'].

Зачем: в ansible-core подстановка top-level фактов (ansible_os_family
и подобные) объявлена устаревшей — предупреждение INJECT_FACTS_AS_VARS,
удаление в версии 2.24. Плейбуки, роли и шаблоны, написанные до этого,
надо перевести на ansible_facts['os_family'].

Это служебный инструмент для обновления старых материалов, а не часть
лабораторных работ: в практиках курса код уже переведён.

Что делает:

  * находит короткие имена фактов в файлах .yml, .yaml, .j2, .cfg
    и .fact и заменяет их на ansible_facts['имя'] (вложенные факты —
    на ansible_facts['имя']['ключ']);
  * НЕ трогает строки с `filter=ansible_...`: это шаблон имени факта
    в модуле setup, там префикс остаётся;
  * НЕ переписывает комментарии: в них о старых именах говорится
    словами, и менять их смысл нельзя;
  * НЕ трогает печатный вывод модуля ("ansible_os_family": "Debian")
    и переменные подключения (ansible_host, ansible_user и прочие);
  * не заходит в каталоги archive/ и .git/;
  * безопасен при повторном запуске: уже переведённая форма
    ansible_facts['os_family'] повторно не меняется.

Запуск:

    python tools/fix_short_facts.py <каталог>            показать, что изменится
    python tools/fix_short_facts.py <каталог> --write    изменить файлы

Без каталога берётся текущий. Код возврата 1, если что-то найдено
в режиме просмотра, и 0, если расхождений нет.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Короткое имя факта -> имя ключа внутри ansible_facts.
FACTS = [
    "os_family", "distribution_major_version", "distribution_version",
    "distribution_release", "distribution", "hostname", "fqdn",
    "default_ipv4", "all_ipv4_addresses", "memtotal_mb", "memfree_mb",
    "swaptotal_mb", "swapfree_mb", "processor_vcpus", "processor_cores",
    "processor_count", "memory_mb", "mounts", "date_time", "kernel",
    "pkg_mgr", "service_mgr", "architecture", "virtualization_type",
    "virtualization_role", "machine_id", "machine", "nodename", "domain",
    "interfaces", "apparmor", "selinux", "cmdline", "lsb", "bios_version",
    "product_name", "product_serial", "uptime_seconds", "python_version",
    "system", "system_vendor", "env", "dns", "fips", "iscsi_iqn",
]
FACTS.sort(key=len, reverse=True)
NAMES = "|".join(FACTS)

KEY_ACCESS = re.compile(r"(?<!ansible_facts)\['ansible_(%s)'\]" % NAMES)
DOTTED_DEFAULT = re.compile(r"\bansible_default_ipv4\.address\b")
DOTTED_TIME = re.compile(r"\bansible_date_time\.iso8601\b")
LOCAL = re.compile(r"(?<!\[')\bansible_local(?!'\])")
BARE = re.compile(r"\bansible_(%s)\b" % NAMES)
BRACKETED_LOCAL = re.compile(r"ansible_facts\['ansible_local'\]((?:\.\w+)+)")

PROTECT = "XKEEPXansible_"
EXTENSIONS = {".yml", ".yaml", ".j2", ".cfg", ".fact"}
SKIP_DIRS = {"archive", ".git", ".ansible", "collections", "_pylibs"}


def _migrate_line(text: str) -> tuple[str, int]:
    """Переводит одну строку. Возвращает (строка, число замен)."""
    count = 0
    text, _ = re.subn(r"filter=ansible_", "filter=" + PROTECT, text)

    text, n = re.subn(KEY_ACCESS,
                      lambda m: "['ansible_facts']['%s']" % m.group(1), text)
    count += n
    text, n = re.subn(DOTTED_DEFAULT,
                      "ansible_facts['default_ipv4']['address']", text)
    count += n
    text, n = re.subn(DOTTED_TIME,
                      "ansible_facts['date_time']['iso8601']", text)
    count += n
    text, n = re.subn(LOCAL, "ansible_facts['ansible_local']", text)
    count += n
    for name in FACTS:
        text, n = re.subn(r"\bansible_%s\b" % re.escape(name),
                          "ansible_facts['%s']" % name, text)
        count += n

    def brackets(match: re.Match) -> str:
        chain = re.findall(r"\.(\w+)", match.group(1))
        return "ansible_facts['ansible_local']" + "".join(
            "['%s']" % part for part in chain)

    text, n = re.subn(BRACKETED_LOCAL, brackets, text)
    count += n
    text = text.replace(PROTECT, "ansible_")
    return text, count


def migrate(text: str) -> tuple[str, int]:
    """Переводит текст целиком, пропуская комментарии и строки filter=."""
    count = 0
    out = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("#") or "filter=ansible_" in line:
            out.append(line)
            continue
        new_line, n = _migrate_line(line)
        count += n
        out.append(new_line)
    return "".join(out), count


def scan(root: Path, write: bool) -> int:
    changed = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        text = path.read_text(encoding="utf-8")
        new, count = migrate(text)
        if count and new != text:
            changed.append((count, rel.as_posix()))
            if write:
                path.write_text(new, encoding="utf-8")
    mode = "ИЗМЕНЕНО" if write else "БУДЕТ ИЗМЕНЕНО (просмотр)"
    print(f"{mode}: файлов {len(changed)}, замен {sum(c for c, _ in changed)}")
    for count, rel in sorted(changed, reverse=True):
        print(f"  {count:3}  {rel}")
    if not write and changed:
        print("\nПовторите запуск с ключом --write, чтобы применить.")
        return 1
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--write"]
    write = "--write" in sys.argv
    root = Path(args[0] if args else ".").resolve()
    if not root.is_dir():
        print(f"каталог не найден: {root}", file=sys.stderr)
        return 2
    print(f"Каталог: {root}")
    return scan(root, write)


if __name__ == "__main__":
    sys.exit(main())

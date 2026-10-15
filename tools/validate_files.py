#!/usr/bin/env python3
"""Проверка содержимого файлов курса по Ansible.

Скрипт разбирает то, что лежит в files/: инвентарь, ansible.cfg,
плейбуки, роли, шаблоны Jinja2, требования Galaxy, сценарий molecule,
внешний инвентарь. Он не проверяет смысл материала — он ловит
ошибки, которые не видны глазом:

  * YAML, который не разбирается (и в каком месте);
  * повторяющийся ключ в одной задаче — YAML оставляет последний,
    и первый молча теряется (на этом ломалась прежняя версия курса:
    два ключа notify в одной задаче);
  * задача без name, плей без hosts, роль без meta;
  * пароль открытым текстом там, где его быть не должно;
  * шаблон Jinja2 с несбалансированными {{ }} и {% %};
  * адреса из прежней версии курса, попавшие в новые файлы.

Отдельный случай — файлы с намеренной ошибкой (`*_broken.yml`):
они битые специально, на них показывают разбор сообщения YAML.
Такой файл обязан не разбираться, и скрипт проверяет именно это.

Запуск из корня репозитория:

    python tools/validate_files.py

Для глубокой проверки нужны PyYAML и Jinja2:

    pip install pyyaml jinja2

Без них скрипт работает, но разбор YAML и шаблонов пропускает
и говорит об этом в итоге.
"""

from __future__ import annotations

import configparser
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

# Вывод в UTF-8: в русской консоли Windows иначе получается мусор.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
    HAVE_YAML = True
except ImportError:  # pragma: no cover - зависит от окружения
    HAVE_YAML = False

try:
    import jinja2
    HAVE_JINJA2 = True
except ImportError:  # pragma: no cover
    HAVE_JINJA2 = False


ROOT = Path(__file__).resolve().parent.parent
FILES = ROOT / "files"

errors: list[str] = []
warnings: list[str] = []
notes: list[str] = []


def err(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# YAML: разбор и поиск повторяющихся ключей
# ---------------------------------------------------------------------------

if HAVE_YAML:

    class UniqueKeyLoader(yaml.SafeLoader):
        """Загрузчик, который ругается на повторяющийся ключ.

        Обычный yaml.safe_load молча оставляет последнее значение,
        и именно так в прежней версии курса терялся обработчик:
        в задаче было два ключа notify.
        """

    def _construct_mapping(loader, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                mark = key_node.start_mark
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"повторяющийся ключ {key!r} (строка {mark.line + 1})",
                    mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
    )


def load_yaml(path: Path):
    """Разбирает YAML. Возвращает (данные, текст ошибки)."""
    if not HAVE_YAML:
        return None, None
    text = read_text(path)
    try:
        return yaml.load(text, Loader=UniqueKeyLoader), None
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f"строка {mark.line + 1}, столбец {mark.column + 1}" if mark else "место неизвестно"
        problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        return None, f"{where}: {problem}"


def parse_yaml(path: Path):
    data, problem = load_yaml(path)
    if problem:
        err(f"{rel(path)}: YAML не разбирается — {problem}")
        return None
    return data


# ---------------------------------------------------------------------------
# Плейбуки, задачи, роли
# ---------------------------------------------------------------------------

PLAY_KEYS = {
    "name", "hosts", "become", "become_user", "gather_facts", "vars",
    "vars_files", "tasks", "pre_tasks", "post_tasks", "handlers", "roles",
    "tags", "serial", "strategy", "max_fail_percentage", "any_errors_fatal",
    "throttle", "order", "force_handlers", "ignore_unreachable",
    "collections", "module_defaults", "environment", "no_log",
    "run_once", "check_mode", "diff", "connection", "remote_user",
}
TASK_KEYS = {
    "name", "when", "tags", "become", "become_user", "loop", "loop_control",
    "with_items", "register", "until", "retries", "delay", "notify",
    "ignore_errors", "failed_when", "changed_when", "block", "rescue",
    "always", "delegate_to", "delegate_facts", "run_once", "vars",
    "environment", "no_log", "args", "listen", "check_mode", "diff",
    "connection", "remote_user", "local_action", "any_errors_fatal",
    "throttle", "serial", "collections", "module_defaults", "action",
    "async", "poll", "loop_var", "until_condition", "ignore_unreachable",
}


def check_playbook(path: Path, data) -> None:
    if data is None:
        return
    if not isinstance(data, list):
        err(f"{rel(path)}: плейбук должен быть списком play, а не {type(data).__name__}")
        return
    for index, play in enumerate(data, start=1):
        where = f"{rel(path)}: play №{index}"
        if not isinstance(play, dict):
            err(f"{where} — это не словарь")
            continue
        if "import_playbook" in play:
            if "name" not in play:
                warn(f"{where}: import_playbook без name")
            continue
        if "hosts" not in play:
            err(f"{where}: нет ключа hosts")
        if "name" not in play:
            warn(f"{where}: нет ключа name — в выводе будет «PLAY [...]» без названия")
        if not ({"tasks", "roles", "pre_tasks", "post_tasks", "import_role",
                 "include_role", "import_tasks", "include_tasks"} & set(play)):
            warn(f"{where}: нет ни tasks, ни roles — play ничего не делает")
        unknown = set(play) - PLAY_KEYS
        if unknown:
            warn(f"{where}: неизвестные ключи play: {', '.join(sorted(unknown))}")
        for key in ("tasks", "pre_tasks", "post_tasks", "handlers"):
            for task in play.get(key) or []:
                check_task(path, task, f"{where}/{key}")


MODULE_HINT = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+\.[a-z0-9_]+$|^[a-z][a-z0-9_]*$")


def check_task(path: Path, task, where: str) -> None:
    if not isinstance(task, dict):
        err(f"{rel(path)}: {where} — задача не словарь")
        return
    name = task.get("name")
    if not name:
        warn(f"{rel(path)}: {where} — задача без name")
    module_keys = [
        k for k in task
        if k not in TASK_KEYS and not k.startswith("with_")
        and MODULE_HINT.match(str(k))
    ]
    if not module_keys and not ({"block", "rescue", "always", "import_tasks",
                                 "include_tasks", "import_role", "include_role",
                                 "meta", "set_fact", "debug", "include_vars"} & set(task)):
        warn(f"{rel(path)}: {where} — не найден модуль задачи")
    for nested in ("block", "rescue", "always"):
        for sub in task.get(nested) or []:
            check_task(path, sub, f"{where}/{nested}")


def check_role(path: Path) -> None:
    """Проверяет структуру роли по каталогу с tasks/main.yml."""
    role_dir = path.parent.parent
    required = {
        "tasks": "задачи",
        "handlers": "обработчики",
        "defaults": "переменные по умолчанию",
        "meta": "описание роли",
    }
    for directory, purpose in required.items():
        if not (role_dir / directory).is_dir():
            warn(f"{rel(role_dir)}: у роли нет каталога {directory}/ ({purpose})")
    meta = role_dir / "meta" / "main.yml"
    if meta.is_file():
        data = parse_yaml(meta)
        if isinstance(data, dict):
            info = data.get("galaxy_info")
            if not isinstance(info, dict):
                warn(f"{rel(meta)}: нет раздела galaxy_info")
            else:
                for field in ("author", "description", "license"):
                    if field not in info:
                        warn(f"{rel(meta)}: в galaxy_info нет поля {field}")
    tasks = role_dir / "tasks" / "main.yml"
    data = parse_yaml(tasks)
    if isinstance(data, list):
        if not data:
            err(f"{rel(tasks)}: файл задач роли пуст")
        for task in data:
            check_task(tasks, task, "tasks/main")
    templates = list((role_dir / "templates").glob("*.j2")) if (role_dir / "templates").is_dir() else []
    files = [p for p in (role_dir / "files").rglob("*") if p.is_file()] if (role_dir / "files").is_dir() else []
    if not templates and not files:
        warn(f"{rel(role_dir)}: у роли нет ни templates/, ни files/ — проверьте, нужны ли они")


# ---------------------------------------------------------------------------
# Отдельные проверки файлов курса
# ---------------------------------------------------------------------------

REQUIRED_INVENTORY_GROUPS = [
    "[web]", "[db]", "[linux:children]", "[debian:children]", "[redhat:children]",
]
REQUIRED_HOSTS = {
    "web1": "10.0.2.11",
    "web2": "10.0.2.12",
    "db1": "10.0.2.13",
}


def check_inventory(path: Path) -> None:
    text = read_text(path)
    lines = [line.strip() for line in text.splitlines()]
    for group in REQUIRED_INVENTORY_GROUPS:
        if group not in lines:
            err(f"{rel(path)}: нет группы {group}")
    for host, address in REQUIRED_HOSTS.items():
        if not re.search(rf"^{host}\s+ansible_host={re.escape(address)}\b", text, re.M):
            err(f"{rel(path)}: хост {host} не привязан к адресу {address}")
    if "ansible_password" in text:
        err(f"{rel(path)}: пароль в инвентаре (ansible_password) — так нельзя даже в учебном курсе")
    if "192.168" in text or "10.0.2.6" in text:
        warn(f"{rel(path)}: похоже, остались адреса из другой подсети")


def check_ansible_cfg(path: Path) -> None:
    parser = configparser.ConfigParser()
    try:
        parser.read_string(read_text(path))
    except configparser.Error as exc:
        err(f"{rel(path)}: не разбирается как INI — {exc}")
        return
    if parser.has_section("default") and not parser.has_section("defaults"):
        err(f"{rel(path)}: секция [default] — Ansible читает [defaults], такая настройка молча игнорируется")
    if not parser.has_section("defaults"):
        err(f"{rel(path)}: нет секции [defaults]")
    if parser.has_section("defaults"):
        keys = {k.lower() for k in parser["defaults"]}
        # Проект может выбирать окружение ключом -i: тогда рядом
        # с ansible.cfg лежит каталог inventory/ и параметр не нужен.
        has_inventory_dir = (path.parent / "inventory").is_dir()
        for key in ("inventory", "host_key_checking"):
            if key in keys:
                continue
            if key == "inventory" and has_inventory_dir:
                continue
            warn(f"{rel(path)}: в [defaults] нет параметра {key}")
        if "host_key_checking" in keys and parser["defaults"]["host_key_checking"].strip().lower() not in ("false", "no", "0"):
            notes.append(f"{rel(path)}: host_key_checking не false — в учебном стенде это лишние вопросы")


SECRET_PATTERNS = [
    (re.compile(r"ansible_password\s*[:=]\s*(?!{{)\S+"), "пароль в переменных подключения"),
    (re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), "закрытый ключ в репозитории"),
    (re.compile(r"vault_password\s*[:=]\s*(?!{{)\S+"), "пароль Vault открытым текстом"),
    (re.compile(r"password\s*[:=]\s*(?!{{|\"{{)[A-Za-z0-9!@#$%^&*_-]{6,}"), "похоже на пароль открытым текстом"),
]
ALLOWED_SECRET_VALUES = ("Console47", "MyStrongPassword", "SyperPass", "{{ vault_", "{{vault_")


def check_secrets(path: Path, text: str) -> None:
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern, what in SECRET_PATTERNS:
            if not pattern.search(line):
                continue
            if any(allowed in line for allowed in ALLOWED_SECRET_VALUES):
                continue
            if "no_log" in line:
                continue
            err(f"{rel(path)}:{number}: {what} — {line.strip()[:70]}")


SHORT_FACT = re.compile(
    r"(?<!\[')ansible_("
    r"os_family|distribution_major_version|distribution_version|"
    r"distribution_release|distribution|hostname|fqdn|default_ipv4|"
    r"all_ipv4_addresses|memtotal_mb|memfree_mb|swaptotal_mb|"
    r"processor_vcpus|processor_cores|mounts|date_time|kernel|pkg_mgr|"
    r"service_mgr|architecture|virtualization_type|virtualization_role|"
    r"machine_id|machine|nodename|domain|interfaces|apparmor|selinux|"
    r"cmdline|bios_version|product_name|uptime_seconds|python_version|"
    r"system|env|ansible_local"
    r")(?!'\])"
)


def check_short_facts(path: Path, text: str) -> None:
    """Ловит короткие имена фактов в файлах кода.

    В комментариях о них говорить можно, в коде — нет: в ansible-core
    2.24 подстановка top-level фактов удаляется.
    """
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#") or "filter=ansible_" in line:
            continue
        match = SHORT_FACT.search(line)
        if match:
            err(f"{rel(path)}:{number}: короткое имя факта ansible_{match.group(1)} — "
                f"в ansible-core 2.24 такие имена удаляются, нужна форма ansible_facts['{match.group(1)}']")


def check_template(path: Path, text: str) -> None:
    if not HAVE_JINJA2:
        return
    environment = jinja2.Environment(undefined=jinja2.ChainableUndefined)
    try:
        environment.parse(text)
    except jinja2.TemplateSyntaxError as exc:
        err(f"{rel(path)}:{exc.lineno}: синтаксис Jinja2 — {exc.message}")
        return
    for open_tag, close_tag in (("{{", "}}"), ("{%", "%}")):
        if text.count(open_tag) != text.count(close_tag):
            err(f"{rel(path)}: не сбалансированы {open_tag} {close_tag} "
                f"({text.count(open_tag)} против {text.count(close_tag)})")
    if re.search(r"\${{", text):
        notes.append(f"{rel(path)}: есть ${{ — это переменная оболочки или nginx, а не Jinja2")


def check_requirements(path: Path) -> None:
    data = parse_yaml(path)
    if not isinstance(data, dict):
        err(f"{rel(path)}: ожидается словарь с ключами roles и collections")
        return
    roles = data.get("roles") or []
    collections = data.get("collections") or []
    if not roles:
        warn(f"{rel(path)}: не описана ни одна роль")
    if not collections:
        warn(f"{rel(path)}: не описана ни одна коллекция")
    for role in roles:
        if isinstance(role, str):
            warn(f"{rel(path)}: роль {role} без закреплённой версии")
        elif isinstance(role, dict) and not (role.get("version") or role.get("src")):
            warn(f"{rel(path)}: роль {role.get('name')} без версии")
    names = {c if isinstance(c, str) else c.get("name") for c in collections}
    for required in ("ansible.posix", "community.general"):
        if required not in names:
            err(f"{rel(path)}: нет коллекции {required}, а курс её использует")


def check_molecule(directory: Path) -> None:
    scenario = directory / "molecule" / "default"
    if not scenario.is_dir():
        err(f"{rel(directory)}: нет сценария molecule/default")
        return
    molecule_yml = scenario / "molecule.yml"
    data = parse_yaml(molecule_yml) if molecule_yml.is_file() else None
    if isinstance(data, dict):
        driver = data.get("driver") or {}
        name = driver.get("name") if isinstance(driver, dict) else driver
        if name != "delegated":
            err(f"{rel(molecule_yml)}: драйвер molecule — {name}, в стенде без Docker нужен delegated")
    verify = scenario / "verify.yml"
    if not verify.is_file():
        err(f"{rel(scenario)}: нет verify.yml — проверять результат будет нечем")
    else:
        text = read_text(verify)
        if "ansible.builtin.assert" not in text:
            warn(f"{rel(verify)}: в проверке нет ansible.builtin.assert")


def check_external_inventory(script: Path) -> None:
    """Запускает внешний инвентарь и проверяет форму ответа."""
    text = read_text(script)
    namespace: dict = {"__name__": "course_inventory_check"}
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(compile(text, str(script), "exec"), namespace)
    except SystemExit:
        pass
    except Exception as exc:  # noqa: BLE001 - показываем студенту причину
        err(f"{rel(script)}: внешний инвентарь падает — {type(exc).__name__}: {exc}")
        return

    payload = None
    for name in ("inventory", "get_inventory", "main"):
        candidate = namespace.get(name)
        if callable(candidate):
            try:
                payload = candidate()
            except Exception as exc:  # noqa: BLE001
                err(f"{rel(script)}: функция {name}() падает — {type(exc).__name__}: {exc}")
                return
            break
    if payload is None:
        printed = buffer.getvalue().strip()
        if not printed:
            err(f"{rel(script)}: внешний инвентарь ничего не вывел и не отдал inventory()")
            return
        try:
            payload = json.loads(printed)
        except json.JSONDecodeError as exc:
            err(f"{rel(script)}: вывод внешнего инвентаря — не JSON ({exc})")
            return

    if not isinstance(payload, dict):
        err(f"{rel(script)}: инвентарь должен быть словарём групп")
        return
    if "_meta" not in payload or "hostvars" not in payload.get("_meta", {}):
        err(f"{rel(script)}: нет _meta.hostvars — Ansible не получит переменные хостов")
    groups = {k: v for k, v in payload.items() if k != "_meta"}
    if "all" not in groups:
        warn(f"{rel(script)}: нет группы all")
    hosts = {h for value in groups.values() if isinstance(value, dict)
             for h in (value.get("hosts") or [])}
    if not hosts:
        err(f"{rel(script)}: ни одного хоста в группах")
    for host in REQUIRED_HOSTS:
        if host not in hosts:
            warn(f"{rel(script)}: хост {host} не попал во внешний инвентарь")


FORBIDDEN_PATHS = ["10.0.2.6", "10.0.2.14"]


def check_forbidden(path: Path, text: str) -> None:
    for bad in FORBIDDEN_PATHS:
        if bad in text:
            err(f"{rel(path)}: адрес {bad} из прежней версии курса")


# ---------------------------------------------------------------------------
# Обход files/
# ---------------------------------------------------------------------------

def walk_files() -> None:
    if not FILES.is_dir():
        err("Каталог files/ не найден")
        return

    for path in sorted(FILES.rglob("*")):
        if path.is_dir():
            continue
        name = path.name
        suffix = path.suffix.lower()
        text = read_text(path)

        if path.stat().st_size == 0:
            err(f"{rel(path)}: файл пуст")
            continue

        check_secrets(path, text)
        check_forbidden(path, text)

        if name.endswith((".yml", ".yaml")) and (
            "_broken" in path.stem or "_invalid" in path.stem
        ):
            # Файл с намеренной ошибкой: на нём показывают разбор.
            # Он обязан НЕ разбираться — это и есть проверка.
            data, problem = load_yaml(path)
            if HAVE_YAML and problem is None:
                warn(f"{rel(path)}: назван намеренно битым, но YAML разбирается")
            continue

        if name.endswith((".yml", ".yaml")):
            check_short_facts(path, text)
            data = parse_yaml(path)
            if data is not None:
                if path.name in ("site.yml", "playbook.yml", "admin_tasks.yml") or (
                    isinstance(data, list)
                    and data
                    and isinstance(data[0], dict)
                    and ({"hosts", "import_playbook"} & set(data[0]))
                ):
                    check_playbook(path, data)
                elif path.parent.name in ("tasks", "handlers"):
                    for task in data if isinstance(data, list) else []:
                        check_task(path, task, path.stem)
                elif path.parent.name == "meta" and path.name == "main.yml":
                    pass
        elif name == "requirements.yml":
            check_requirements(path)
        elif suffix == ".j2":
            check_template(path, text)
            check_short_facts(path, text)
        elif name == "ansible.cfg":
            check_ansible_cfg(path)
        elif name == "inventory.ini":
            check_inventory(path)

    for role_tasks in sorted(FILES.rglob("tasks/main.yml")):
        check_role(role_tasks)

    for module_yml in sorted(FILES.rglob("molecule.yml")):
        check_molecule(module_yml.parent.parent.parent)

    for script in sorted(FILES.rglob("inventory/*.py")):
        check_external_inventory(script)


def check_repository_files() -> None:
    """Проверки, которые касаются репозитория, а не только files/."""
    gitignore = ROOT / ".gitignore"
    if gitignore.is_file():
        text = read_text(gitignore)
        for needed in (".vault_pass", "collections/", "*.retry"):
            if needed not in text:
                warn(f".gitignore: нет правила для {needed}")
    else:
        err(".gitignore не найден")

    for pattern in ("**/vault_pass*", "**/.vault_pass", "**/*.vault_pass"):
        for found in ROOT.glob(pattern):
            if found.is_file():
                err(f"{rel(found)}: файл с паролем Vault не должен лежать в репозитории")


def main() -> int:
    print(f"Проверка файлов курса: {ROOT}")
    print("-" * 73)
    if not HAVE_YAML:
        notes.append("PyYAML не установлен: разбор YAML пропущен (pip install pyyaml)")
    if not HAVE_JINJA2:
        notes.append("Jinja2 не установлен: разбор шаблонов пропущен (pip install jinja2)")

    walk_files()
    check_repository_files()

    if notes:
        print(f"\nЗАМЕЧАНИЯ ({len(notes)}):")
        for item in sorted(set(notes)):
            print(f"  ~ {item}")
    if warnings:
        print(f"\nПРЕДУПРЕЖДЕНИЯ ({len(warnings)}):")
        for item in warnings:
            print(f"  ! {item}")
    if errors:
        print(f"\nОШИБКИ ({len(errors)}):")
        for item in errors:
            print(f"  x {item}")
        print("\nПроверка не пройдена.")
        return 1

    print("\nПроверка пройдена: ошибок нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

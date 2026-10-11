# files/16_quality_inventory — проект итоговой работы трека «5 дней»

Готовый проект практики 16: роль `web_admin` из практики 10, сценарий
`molecule` с драйвером `delegated`, настройки `ansible-lint` и внешний
инвентарь. Каждый файл напечатан в тексте практики `16_quality_inventory.txt`
в том же виде.

## Что за файлы

| Файл | К какому шагу | Зачем |
|---|---|---|
| `.ansible-lint` | шаг 4 | настройки линтера: `skip_list`, `warn_list`, `exclude_paths` |
| `ansible.cfg` | шаги 1, 14 | инвентарь, `enable_plugins`, `collections_path`, `roles_path`, кэш инвентаря |
| `inventory/stand.py` | шаги 12, 13 | внешний инвентарь: плагин `ansible.builtin.script` |
| `inventory/stand.ini` | шаг 15 | тот же стенд статически, для сравнения |
| `site.yml` | шаг 17 | плейбук, который запускается по внешнему инвентарю |
| `molecule/default/molecule.yml` | шаг 7 | сценарий проверки роли, драйвер `delegated` |
| `molecule/default/prepare.yml` | шаг 8 | проверка, что сценарий попал на нужные машины стенда |
| `molecule/default/converge.yml` | шаг 8 | применение роли `web_admin` |
| `molecule/default/verify.yml` | шаг 10 | проверки через `ansible.builtin.assert` |
| `roles/web_admin/` | шаги 2–4 | копия роли из `files/10_roles/roles/web_admin` |

`inventory/stand.py` — единственный исполняемый скрипт в материалах
курса, и он же предмет изучения: динамическая инвентаризация. По общему
правилу в `files/` готовых скриптов нет, здесь сделано исключение
осознанно. Скрипту нужен бит исполнения:

```
chmod +x inventory/stand.py
```

## Как запускать

Скопировать проект и работать из его каталога — линтер, Ansible
и molecule ищут свои настройки в текущем каталоге:

```
mkdir -p ~/ansible-lab/16_quality_inventory
cp -r /путь/к/репозиторию/files/16_quality_inventory/. ~/ansible-lab/16_quality_inventory/
cd ~/ansible-lab/16_quality_inventory
chmod +x inventory/stand.py
```

Проверка кода:

```
ansible-lint
ansible-playbook --syntax-check site.yml
ansible-playbook --list-tasks site.yml
```

Проверка роли в сценарии molecule (машины — web1 и web2 из стенда,
они должны быть доступны по SSH):

```
molecule test
```

Отдельные шаги сценария: `molecule create`, `molecule converge`,
`molecule idempotence`, `molecule verify`, `molecule destroy`.

Внешний инвентарь:

```
ansible-inventory --graph
ansible-inventory --list
ansible-inventory --host web1
```

Лицензия: код — MIT, тексты — CC BY-NC-SA 4.0.

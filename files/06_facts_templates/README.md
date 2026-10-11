# files/06_facts_templates — файлы практики 6

Здесь лежат файлы практики 6 «Факты и шаблоны Jinja2». Это не готовое
решение практики, а те самые файлы, которые студент набирает руками:
их содержимое напечатано и в тексте практики.

## Что за файлы и к какому шагу

| Файл | Шаг практики | Что это |
|---|---|---|
| `01_facts.yml` | шаги 1–3 | Плейбук: печатает выбранные факты (`ansible.builtin.debug`) и проверяет предположения о хосте (`ansible.builtin.assert`) |
| `02_custom_facts.yml` | шаг 4 | Плейбук: раскладывает настраиваемые факты в `/etc/ansible/facts.d` и показывает `ansible_local` |
| `facts.d/site.fact` | шаг 4 | Настраиваемый факт в формате INI: владелец, роль, версия стенда |
| `facts.d/hardware.fact` | шаг 4 | Настраиваемый факт в формате JSON: модель, ядра, память |
| `03_index_template.yml` | шаг 8 | Плейбук: разворачивает главную страницу сайта из шаблона |
| `templates/index.j2` | шаг 8 | Шаблон главной страницы: имя хоста, адрес, семейство ОС, владелец из `ansible_local` |
| `04_motd.yml` | шаг 9 | Плейбук: раскладывает `/etc/motd` из шаблона |
| `templates/motd.j2` | шаг 9 | Шаблон `/etc/motd` с циклом по `groups['linux']` и адресами из `hostvars` |
| `05_hostvars.yml` | шаг 10 | Плейбук: показывает `hostvars`, `groups`, `group_names` и фильтры Jinja2 |

Плейбук шага 11 (`validate`) и шага 12 (`gather_facts: false`) отдельными
файлами не выкладывается: это короткие фрагменты, они приведены прямо
в тексте практики.

## Как этим пользоваться

Файлы практики 6 складываются в рабочий каталог курса на управляющей
машине `control` рядом с инвентарём из практики 2:

```
/home/engineer/ansible-lab/
├── ansible.cfg
├── inventory.ini
├── group_vars/
├── host_vars/
├── 01_facts.yml
├── 02_custom_facts.yml
├── 03_index_template.yml
├── 04_motd.yml
├── 05_hostvars.yml
├── facts.d/
│   ├── site.fact
│   └── hardware.fact
└── templates/
    ├── index.j2
    └── motd.j2
```

Скопировать готовое можно так (каталог `files/06_facts_templates` — из
репозитория курса):

```
cd ~/ansible-lab
mkdir -p templates facts.d
cp 01_facts.yml 02_custom_facts.yml 03_index_template.yml 04_motd.yml 05_hostvars.yml ~/ansible-lab/
cp templates/index.j2 templates/motd.j2 ~/ansible-lab/templates/
cp facts.d/site.fact facts.d/hardware.fact ~/ansible-lab/facts.d/
```

Порядок запуска — по номерам файлов:

```
ansible-playbook 01_facts.yml
ansible-playbook 02_custom_facts.yml
ansible-playbook 03_index_template.yml --limit web
ansible-playbook 04_motd.yml
ansible-playbook 05_hostvars.yml
```

Файлы `templates/` и `facts.d/` лежат рядом с плейбуками не случайно:
модуль `template` ищет относительный `src` в каталоге `templates/`
рядом с плейбуком, модуль `copy` — в каталоге, который указан в `src`
(у нас `facts.d/`). Если перенести шаблон в другое место, задача упадёт
с ошибкой `Could not find or access ...`.

## На что обратить внимание

* **Каталог `facts.d` здесь — только заготовка.** На узле файлы должны
  лежать в `/etc/ansible/facts.d/`, иначе Ansible их не увидит: он
  читает ровно этот путь (он же `fact_path` модуля `setup`).
* **Два play в `02_custom_facts.yml`** — не случайность. Набор фактов
  собирается в начале play, до задач, поэтому факты, положенные первым
  play, видны только во втором.
* **`ansible_local.site.general.owner`** — имя файла, имя секции, имя
  ключа. Для INI-файла секция обязательна, поэтому путь на один уровень
  длиннее, чем для JSON-файла (`ansible_local.hardware.cpu_cores`).
* **`--limit web`** в шаге 8 нужен потому, что на `db1` нет веб-сервера.
  Условие `when`, которое заменит `--limit`, появится в практике 7.
* **Адреса и пароли.** `10.0.2.11`, `10.0.2.12`, `10.0.2.13` — учебные
  адреса стенда курса. Пароль `Console47` — учебное значение
  из практики 1; в этих файлах он не встречается.

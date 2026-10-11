# files/14_complex_projects — учебный проект практики 14

Проект целиком: точка входа, три плейбука, два окружения, роль
`web_admin` из практики 10, файл общих проверок и пример секретов.
Содержимое каждого файла напечатано и в тексте практики
`14_complex_projects.txt`.

## Структура

```
14_complex_projects/
├── ansible.cfg                 настройки Ansible для проекта
├── site.yml                    точка входа: только import_playbook
├── inventory/
│   ├── dev.ini                 окружение dev: группа dev
│   └── prod.ini                окружение prod: группа prod
├── group_vars/
│   ├── all/
│   │   ├── vars.yml            переменные всех машин проекта
│   │   └── vault.yml.example   образец файла секретов окружения
│   ├── dev.yml                 переменные окружения dev
│   └── prod.yml                переменные окружения prod
├── playbooks/
│   ├── webservers.yml          веб-часть: роль web_admin, serial
│   ├── db.yml                  настройка db1 (Rocky Linux 10)
│   └── report.yml              отчёт о парке на управляющей машине
├── tasks/
│   └── common_checks.yml       общие проверки машины
└── roles/
    └── web_admin/              копия роли из практики 10
```

## Как запускать

Проект запускается из своего каталога: `ansible.cfg` и каталоги
`group_vars`, `roles` Ansible ищет рядом с плейбуком.

```
mkdir -p ~/ansible-lab/14_complex_projects
cp -r /путь/к/репозиторию/files/14_complex_projects/. \
    ~/ansible-lab/14_complex_projects/
cd ~/ansible-lab/14_complex_projects

ansible-playbook --syntax-check site.yml -i inventory/dev.ini
ansible-playbook site.yml -i inventory/dev.ini
ansible-playbook site.yml -i inventory/prod.ini
```

Окружение выбирается **только** ключом `-i`. Инвентаря по умолчанию
в `ansible.cfg` нет намеренно: запуск без `-i` уходит на
`/etc/ansible/hosts` и предупреждает, что машин не найдено.

## Два окружения: чем отличаются

| | dev | prod |
|---|---|---|
| Инвентарь | `inventory/dev.ini` | `inventory/prod.ini` |
| Группа окружения | `dev` | `prod` |
| Переменные | `group_vars/dev.yml` | `group_vars/prod.yml` |
| Обновление парка | `update_serial: "100%"` — все машины разом | `update_serial: 1` — по одной машине |
| Заголовок страницы | `DEV: учебный стенд курса Ansible` | `PROD: учебный стенд курса Ansible` |
| Подпись в отчёте | «пробный парк» | «боевой парк» |

Сам `site.yml`, все три плейбука и роль от окружения не зависят:
различие вынесено в `group_vars`. На учебном стенде машин три,
поэтому адреса в обоих инвентарях одни и те же; в рабочем проекте
у prod был бы свой парк машин.

## Порядок работы

1. `playbooks/webservers.yml` — роль `web_admin` на `web1` и `web2`,
   общие проверки статическим `import_tasks`, обновление партиями
   по `serial`.
2. `playbooks/db.yml` — каталог для резервных копий и файл-описание
   на `db1`; общие проверки включены динамически, ключом
   `include_tasks` с `apply`.
3. `playbooks/report.yml` — каждая машина считает свою строку отчёта,
   а записывает её один хост на управляющей машине: `delegate_to:
   localhost` и `run_once: true`. Файл отчёта —
   `reports/fleet-report.txt`.

## Секреты

`group_vars/all/vault.yml.example` — образец: скопируйте его
в `group_vars/all/vault.yml`, впишите свои значения и зашифруйте
командой `ansible-vault encrypt group_vars/all/vault.yml`.
`vault.yml.example` в репозитории не зашифрован намеренно: своим
паролем его прочитать нельзя, а курс обещает проверяемый материал.
Рабочий файл `vault.yml` в репозиторий не попадает.

Лицензия: код проекта — MIT, учебные тексты — CC BY-NC-SA 4.0.

# files/09_admin_tasks — файлы практики 9

Здесь лежат файлы практики 9 «Административные задачи»: плейбуки шагов,
переменные по семействам ОС, шаблоны sudoers и юнитов systemd. Это не
готовое решение «запусти и сдай», а те самые файлы, которые студент
набирает руками: их содержимое напечатано и в тексте практики
`9_admin_tasks.txt`.

Файлы рассчитаны на рабочий каталог курса `/home/engineer/ansible-lab`
на управляющей машине `control`: там уже лежат `inventory.ini`,
`ansible.cfg` и `group_vars/` из практики 2. Каталог `vars/` из этой
практики дополняет `group_vars/`, а не заменяет его.

## Что за файлы и к какому шагу

| Файл | Шаг практики | Что это |
|---|---|---|
| `02_users.yml` | шаг 3 | Пользователи и группы: `ansible.builtin.group`, `ansible.builtin.user`, пароль хэшем, `remove: true`, `ansible.posix.authorized_key` |
| `03_sudoers.yml` | шаг 4 | Файл `/etc/sudoers.d/engineer-nopass` из шаблона, права `0440`, проверка `visudo -cf` |
| `04_packages.yml` | шаг 5 | Пакеты и репозитории: `apt`, `dnf`, установка списком через `loop`, `deb822_repository`, `yum_repository` |
| `05_services.yml` | шаг 6 | Службы: `ansible.builtin.systemd_service`, `masked`, `daemon_reload`, свой юнит и таймер из шаблона |
| `06_firewall.yml` | шаг 7 | Одно намерение двумя модулями: `community.general.ufw` на Ubuntu, `ansible.posix.firewalld` на Rocky |
| `07_reboot.yml` | шаг 9 | Перезагрузка с ожиданием: `ansible.builtin.reboot`, `wait_for_connection` |
| `admin_tasks.yml` | шаг 10 | Итоговый плейбук: всё перечисленное плюс время, cron и `ansible.posix.sysctl`; повторный прогон — `changed=0` |
| `templates/engineer-nopass.j2` | шаг 4 | Содержимое файла в `/etc/sudoers.d` |
| `templates/timezone-check.service.j2` | шаг 6 | Юнит-служба `timezone-check.service` |
| `templates/timezone-check.timer.j2` | шаг 6 | Таймер `timezone-check.timer`, запускающий эту службу раз в сутки |
| `vars/Debian.yml` | шаги 2–10 | Переменные для Ubuntu 26.04: `apache2`, `ufw`, группы `sudo`, пакет `python3-debian` |
| `vars/RedHat.yml` | шаги 2–10 | Переменные для Rocky Linux 10: `httpd`, `firewalld`, группы `wheel`, пакет `python3-firewall` |

## Как этим пользоваться

Скопируйте каталоги и файлы в рабочий каталог курса, сохранив
структуру (`templates/` и `vars/` — это каталоги):

```
cd ~/ansible-lab
cp -r /путь/к/репозиторию/files/09_admin_tasks/. .
```

Проверьте, что получилось:

```
tree -L 2 ~/ansible-lab
```

Шаги практики запускаются по порядку и каждый — отдельным плейбуком:

```
ansible-playbook 02_users.yml
ansible-playbook 03_sudoers.yml
ansible-playbook 04_packages.yml
ansible-playbook 05_services.yml
ansible-playbook 06_firewall.yml
ansible-playbook admin_tasks.yml
```

Все команды выполняются из каталога `~/ansible-lab`, иначе Ansible
не найдёт `ansible.cfg`, `inventory.ini` и каталог `vars/`.

## На что обратить внимание

* **`admin_tasks.yml` — тот же набор задач, что и в файлах шагов, но
  собранный в один плейбук.** Он не «импортирует» их: `import_playbook`
  и `include_tasks` — тема практики 14, и здесь они не используются.
  Поэтому при первом запуске шагов изменения уже будут внесены, и
  итоговый плейбук покажет `changed=0` сразу. Это правильный результат,
  а не признак того, что он ничего не делает.
* **Перезагрузки в `admin_tasks.yml` нет.** Перезагрузка — действие,
  а не состояние; она живёт в `07_reboot.yml` и по умолчанию выключена
  переменной `reboot_allowed`.
* **`vars/` и `group_vars/` пересекаются.** Значения `web_package`,
  `web_service` и `firewall_package` уже заданы в `group_vars/debian.yml`
  и `group_vars/redhat.yml` из практики 2. Здесь они повторены, чтобы
  набор файлов практики читался целиком. Держать одно значение в двух
  местах — плохая практика, и в рабочем проекте так делать не нужно:
  молча победит то, что прочитано позже, а `include_vars` приоритетнее
  `group_vars`.
* **Пароль передаётся хэшем.** В `02_users.yml` и `admin_tasks.yml`
  стоит учебный пароль `Console47`, обёрнутый в фильтр
  `password_hash('sha512', ...)`. Соль задана явно: без неё хэш менялся
  бы на каждом прогоне и плейбук никогда не давал бы `changed=0`.
  В рабочем проекте пароль берут из Vault (практика 5), а не из текста
  плейбука.
* **На Ubuntu сначала открывается 22/tcp, и только потом включается
  ufw.** Политика по умолчанию — `deny` для входящих, и включение ufw
  без правила для SSH отрезает управляющей машине доступ к узлу.
* **`state: latest` в этих файлах не используется намеренно.** Об этом
  в практике есть отдельный шаг: обновление версий на парке — решение,
  а не привычка.

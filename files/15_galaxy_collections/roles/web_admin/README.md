# Роль `web_admin`

Ставит веб-сервер (`apache2` на Debian, `httpd` на RedHat), включает его
и оставляет запущенным, раскладывает страницу сайта из шаблона `index.j2`
и оформление `style.css`, открывает порт сайта и порт SSH в межсетевом
экране (`ufw` на Ubuntu, `firewalld` на Rocky). Условий по имени машины
в роли нет: ветка выбирается по факту `ansible_os_family`.

## Requirements

* `ansible-core` 2.19 или новее;
* коллекции `ansible.posix` (модуль `firewalld`) и `community.general`
  (модуль `ufw`);
* права `root` на управляемой машине: роль ставит пакеты, пишет в `/etc`
  и управляет службами, поэтому в play нужен `become: true`;
* собранные факты узла: роль читает `ansible_os_family`.

## Role Variables

Переопределяемые значения лежат в `defaults/main.yml`. Описание
аргументов с типами и значениями по умолчанию — в
`meta/argument_specs.yml`; посмотреть его можно командой
`ansible-doc -t role web_admin`.

| Переменная | Тип | По умолчанию | Что делает |
|---|---|---|---|
| `web_admin_deploy_site` | `bool` | `false` | разворачивать ли страницу сайта |
| `web_admin_site_title` | `str` | `Учебный стенд курса Ansible` | заголовок страницы |
| `web_admin_owner` | `str` | `не назначен` | владелец машины на странице |
| `web_admin_port` | `int` | `80` | порт сайта, открывается в межсетевом экране |
| `web_admin_ssh_port` | `int` | `22` | порт SSH, остаётся открытым всегда |
| `web_admin_site_root` | `path` | `/var/www/html` | каталог сайта |
| `web_admin_index_file` | `str` | `index.html` | имя главной страницы |
| `web_admin_style_file` | `str` | `style.css` | имя файла оформления |
| `web_admin_service_state` | `str` | `started` | состояние службы веб-сервера |
| `web_admin_service_enabled` | `bool` | `true` | автозапуск службы |

Значения, которые роль фиксирует, лежат в `vars/main.yml`:
`web_admin_supported_families` (список семейств ОС, с которыми роль
умеет работать) и `web_admin_family_settings` (имена пакетов, служб
и межсетевых экранов по семействам). Их переопределяет только
`--extra-vars`: это не «значения по умолчанию», а факт операционной
системы. Поэтому в `meta/argument_specs.yml` их нет.

## Dependencies

Зависимостей нет: `dependencies: []` в `meta/main.yml`. Коллекции —
не зависимости роли, а требование к управляющей машине: их ставит
`ansible-galaxy` по файлу `requirements.yml` проекта.

## Example Playbook

Вызов роли на всех машинах стенда с развёрнутой страницей сайта:

```yaml
- name: Веб-сервер и сайт на узлах стенда
  hosts: linux
  become: true
  gather_facts: true
  roles:
    - role: web_admin
      vars:
        web_admin_deploy_site: true
        web_admin_port: 8080
```

Тот же вызов через `include_role`, когда роль нужна в середине списка
задач:

```yaml
- name: Развернуть сайт на машинах группы web
  ansible.builtin.include_role:
    name: web_admin
  vars:
    web_admin_deploy_site: true
```

## Argument Validation

`meta/argument_specs.yml` описывает аргументы точки входа `main`.
Проверка запускается перед первой задачей роли: неверный тип значения
(например `web_admin_port: "8080/tcp"` вместо числа) или неизвестный
аргумент останавливают роль с текстом `Validation of arguments failed`.
Значения, которые просто лежат в `group_vars` и не описаны в спецификации,
проверка не трогает.

## Idempotence

Повторный прогон даёт `changed=0` при условии, что шаблон `index.j2`
не содержит меняющихся подстановок (даты, времени, случайных значений).

## License

MIT

## Author Information

Учебный стенд курса «Практическое использование Ansible», пользователь
`engineer`.

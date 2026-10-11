# Роль `web_admin`

Ставит и включает веб-сервер (`apache2` на Debian, `httpd` на
RedHat), раскладывает страницу сайта из шаблона `index.j2`
и оформление `style.css`, открывает порт в `ufw` или `firewalld`,
перезапускает службу обработчиком только при изменении шаблона.
Условий по имени машины нет: ветка выбирается по факту
`ansible_os_family`. Нужны коллекции `ansible.posix` и
`community.general`, факты узла и права `root`.

Переопределяемые значения — в `defaults/main.yml`
(`web_admin_deploy_site`, `web_admin_site_title`, `web_admin_port`
и другие). Значения, которые роль фиксирует
(`web_admin_supported_families`, `web_admin_family_settings`),
лежат в `vars/main.yml`: их перекрывает только `--extra-vars`.
Зависимостей нет. Лицензия — MIT.

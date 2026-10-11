# files/10_roles — учебный проект практики 10

Готовый проект итоговой работы трёхдневного трека: роль `web_admin`
и всё, что нужно, чтобы запустить её одной командой. Содержимое
каждого файла напечатано и в тексте практики `10_roles.txt`.

Состав: `ansible.cfg`, `inventory.ini`, `site.yml`, `group_vars/`
(`all.yml`, `web.yml`) и `roles/web_admin/` (`tasks`, `handlers`,
`defaults`, `vars`, `files`, `templates`, `meta`, `README.md`).

Запуск — из каталога проекта:

```
cp -r /путь/к/репозиторию/files/10_roles/. ~/ansible-lab/10_roles/
cd ~/ansible-lab/10_roles
ansible-playbook site.yml
```

На `web1` и `web2` появляется сайт из шаблона и порт 80 в `ufw`,
на `db1` — `httpd` и порт 80 в `firewalld`. Повторный прогон даёт
`changed=0`. Лицензия: код — MIT, тексты — CC BY-NC-SA 4.0.

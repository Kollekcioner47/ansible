# files/15_galaxy_collections — материалы практики 15

Учебный проект практики «Galaxy, коллекции и системные роли RHEL»:
готовые роли из Galaxy, коллекции, документация своей роли и заготовка
скелета. Содержимое каждого файла напечатано и в тексте практики
`15_galaxy_collections.txt`, поэтому на занятии код набирают вместе
с преподавателем, а сюда смотрят, если что-то не набралось.

## Что за файлы и к какому шагу

* `ansible.cfg` — настройки проекта. Шаг 2. Здесь важны `roles_path`
  (где искать роли и куда их ставит `ansible-galaxy`) и
  `collections_path` (где искать коллекции). Значение из `ansible.cfg`
  заменяет список по умолчанию, а не дополняет его.
* `requirements.yml` — роли и коллекции одним файлом, версии
  закреплены. Шаги 3 и 4. Установка целиком:
  `ansible-galaxy install -r requirements.yml`.
* `requirements.min.yml` — минимальный набор для стенда: только
  коллекции, без готовых ролей. Шаг 10. Установка:
  `ansible-galaxy collection install -r requirements.min.yml`.
* `01_galaxy_role.yml` — использование готовой роли `geerlingguy.nginx`.
  Шаг 5. Дополнительная переменная `nginx_vhosts` переводит nginx на
  порт 8080, чтобы не спорить с `apache2` из практики 10 за порт 80.
* `02_system_role_timesync.yml` — системная роль RHEL `timesync` на
  узле `db1`. Шаг 12. Требует пакета `rhel-system-roles` на Rocky Linux.
* `03_collections_check.yml` — проверка, какие коллекции и каких
  версий установлены. Шаг 11. Ничего не меняет: спрашивает
  `ansible-galaxy collection list --format json` и сверяет ответ.
* `roles/web_admin/meta/argument_specs.yml` — описание аргументов
  своей роли с типами и значениями по умолчанию. Шаг 13. Кладётся
  в уже существующую роль `web_admin` из практики 10.
* `roles/web_admin/README.md` — документация своей роли. Шаг 13.
  Кладётся туда же, вместо заготовки, которую создал `ansible-galaxy`.
* `skeleton/` — заготовка своего скелета роли для
  `ansible-galaxy role init --role-skeleton`. Шаг 7. Внутри два
  шаблона: `skeleton/README.md.j2` и `skeleton/meta/main.yml.j2`.
  Расширение `.j2` означает «отрендерить Jinja2 и отбросить
  расширение»: из `meta/main.yml.j2` получится `meta/main.yml`.

## Как использовать

Собрать проект практики из этого каталога и проекта практики 10:
инвентарь, роль `web_admin`, плейбук `site.yml` и каталог `group_vars`
берутся оттуда, чтобы не заводить вторые копии. Порядок команд важен:
сначала копируется роль из практики 10, потом поверх неё ложится
этот каталог — он добавляет в роль файлы `meta/argument_specs.yml`
и `README.md`.

```
mkdir -p ~/ansible-lab/15_galaxy/roles
cp -r ~/ansible-lab/10_roles/roles/web_admin ~/ansible-lab/15_galaxy/roles/
cp -r /путь/к/репозиторию/files/15_galaxy_collections/. ~/ansible-lab/15_galaxy/
cp ~/ansible-lab/10_roles/inventory.ini ~/ansible-lab/15_galaxy/
cp ~/ansible-lab/10_roles/site.yml ~/ansible-lab/15_galaxy/
cp -r ~/ansible-lab/10_roles/group_vars ~/ansible-lab/15_galaxy/
cd ~/ansible-lab/15_galaxy
```

`site.yml` нужен, чтобы было что запускать: он вызывает роль
`web_admin` и берёт значения из `group_vars`, в том числе порт 80 —
порт apache2. С nginx из практики 12, который слушает 8080, он
не спорит. Оба файла уже напечатаны и разобраны в практике 10,
поэтому в этом каталоге лежат только новые файлы практики 15.
Прогон `ansible-playbook site.yml -e web_admin_port=8080` — это
проверка `meta/argument_specs.yml` из шага 13 и пункта 6 практики.

Дальше по шагам практики:

```
ansible-galaxy install -r requirements.yml
ansible-playbook 01_galaxy_role.yml
ansible-galaxy role init --role-skeleton=./skeleton my_role
ansible-galaxy collection list
ansible-playbook 03_collections_check.yml
ansible-playbook 02_system_role_timesync.yml
ansible-doc -t role web_admin
```

Каталоги `galaxy_roles/`, `roles/` и `collections/` создаются при
установке; в репозитории курса их нет — там лежат только исходные
файлы проекта.

Лицензия: код — MIT, тексты — CC BY-NC-SA 4.0.

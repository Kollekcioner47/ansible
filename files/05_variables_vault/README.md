# files/05_variables_vault — файлы практики 5

Здесь лежат файлы практики 5 «Переменные и секреты». Это не готовое
решение практики, а те самые файлы, которые студент набирает руками:
их содержимое напечатано и в тексте практики.

## Что за файлы и к какому шагу

| Файл | Шаг практики | Что это |
|---|---|---|
| `01_vars_play.yml` | шаги 2, 4 | Переменные в `vars` плейбука; опыт с `web_port` в четырёх местах (пятое — `vars_files`, шаг 11) |
| `02_register.yml` | шаги 6, 7 | `register`, поля `rc`/`stdout`/`stdout_lines`/`changed`, `changed_when`, `set_fact` |
| `03_vars_files.yml` | шаги 11, 13 | `vars_files`, файл настроек с паролем из Vault, `assert`, `no_log` |
| `vars/app.yml` | шаг 11 | Переменные приложения: подключаются директивой `vars_files` |
| `extra_vars.yml` | шаг 12 | Внешние переменные: запуск с `-e @extra_vars.yml` |
| `group_vars/all/vault.yml.example` | шаг 9 | Образец файла секретов: учебные заглушки и команда `ansible-vault encrypt` |
| `README.md` | — | Этот файл |

## Как этим пользоваться

Рабочий каталог курса — `/home/engineer/ansible-lab` на машине
`control`. Плейбуки и файл внешних переменных кладутся в него
целиком:

```
cd files/05_variables_vault
cp 01_vars_play.yml 02_register.yml 03_vars_files.yml ~/ansible-lab/
mkdir -p ~/ansible-lab/vars
cp vars/app.yml ~/ansible-lab/vars/
cp extra_vars.yml ~/ansible-lab/
```

Путь `vars/app.yml` важен дважды: каталог `vars` должен лежать рядом
с плейбуком (иначе `vars_files` его не найдёт), а внутри плейбука он
записан именно как `vars/app.yml`, а не как `app.yml`.

Образец секретов копируется отдельно, под другим именем, и только
потом шифруется:

```
cd ~/ansible-lab
mkdir -p group_vars/all
cp <репозиторий>/files/05_variables_vault/group_vars/all/vault.yml.example \
    group_vars/all/vault.yml
ansible-vault encrypt group_vars/all/vault.yml
```

## На что обратить внимание

* **Образец не зашифрован и не может быть зашифрован в репозитории.**
  Файл `group_vars/all/vault.yml.example` лежит открытым текстом: в нём
  учебные заглушки. Настоящий `vault.yml` появляется только на стенде
  и только после `ansible-vault encrypt`. Расширение `.example` не
  случайно: Ansible читает в `group_vars/` файлы с расширениями
  `.yml`, `.yaml`, `.json` и файлы без расширения, а `.example`
  не читает — образец не попадёт в переменные по ошибке.
* **Каталог `group_vars/all/` вытесняет файл `group_vars/all.yml`.**
  Ansible ищет переменные группы так: сначала каталог с именем группы
  (`group_vars/all`), и, найдя его, на этом останавливается. Файл
  `group_vars/all.yml` из практики 2 после создания каталога больше
  не читается. Поэтому его содержимое переносится в
  `group_vars/all/vars.yml` — рядом с `vault.yml`. Проверка:
  `ansible-inventory --host web1` должен по-прежнему показывать
  `ansible_user` и `lab_owner`.
* **Секрет живёт в зашифрованном файле, а ссылка на него — в обычном.**
  В `group_vars/all/vars.yml` пишется строка
  `db_password: "{{ vault_db_password }}"`, а сам `vault_db_password`
  лежит в `group_vars/all/vault.yml`.
* **Файл с паролем Vault в репозиторий не кладут.** Пароль лежит
  вне репозитория, например в `/home/engineer/.vault_pass`, права
  `0600`, а имя файла добавлено в `.gitignore`.
* **Учебные метки порта.** В `extra_vars.yml`, `vars/app.yml` и
  `01_vars_play.yml` встречаются числа 8081, 8082 и 8083; на стенде
  к ним добавляется 8080 из `host_vars/web1.yml` (шаг 2 практики).
  Это учебные метки для опыта с приоритетом переменных: рабочий порт
  веб-сервера в курсе один — 80, и ни один плейбук на 8080–8083
  не слушает.
* **Учебные значения.** `MyStrongPassword` и `Console47` в образце
  секретов помечены как учебные: на своём стенде их заменяют.

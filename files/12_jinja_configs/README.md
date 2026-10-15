# files/12_jinja_configs — файлы практики 12

Здесь лежат файлы практики 12 «Jinja2 для настоящих конфигов»: шаблоны,
переменные и плейбуки. Это не готовое решение практики, а те самые файлы,
которые студент набирает руками: их содержимое напечатано и в тексте
практики.

## Что за файлы и к какому шагу

Шаблоны, каталог templates/:

    nginx_vhost.j2      шаги 2–4   виртуальный хост: server_name, root, location
    nginx_upstream.j2   шаг 3      upstream и map для метки сайта
    sshd_config.j2      шаг 5      sshd_config циклом по словарю sshd_params
    motd.j2             шаг 7      /etc/motd: факты машины и машины группы linux
    resolv.conf.j2      шаг 9      /etc/resolv.conf из переменных
    chrony.conf.j2      шаг 9      /etc/chrony.conf из переменных
    notice.j2           шаг 12     объявление для lookup('template', ...)

Переменные, каталог vars/: nginx.yml — шаги 2–4, sshd.yml — шаги 5–6.
Данные для lookup, каталог data/: notice.txt — шаг 12.

Плейбуки, в порядке запуска:

    01_nginx.yml   шаги 2–4   виртуальный хост nginx на порту 8080 и upstream
    02_sshd.yml    шаги 5–6   sshd_config на web1 и db1
    03_motd.yml    шаги 7–9   motd и resolv.conf на группе linux, chrony на db1
    04_lookup.yml  шаг 12     lookup file, env и template
    05_slurp.yml   шаг 13     чтение /etc/motd на группе linux и сверка с шаблоном

Фрагменты, которых нет отдельными файлами (управление пробелами,
фильтры и тесты, Jinja2 в when и loop), напечатаны в тексте практики.

## Как этим пользоваться

Файлы складываются в рабочий каталог курса ~/ansible-lab на управляющей
машине control, рядом с инвентарём из практики 2. Каталоги vars/,
templates/ и data/ лежат рядом с плейбуками: модуль template ищет src
в каталоге templates/, vars_files — относительно каталога плейбука.
Команды копирования выполняются из этого каталога в репозитории курса:

    cd ~/ansible-lab
    mkdir -p vars templates data
    cp vars/*.yml ~/ansible-lab/vars/
    cp templates/*.j2 ~/ansible-lab/templates/
    cp data/notice.txt ~/ansible-lab/data/
    cp 0*.yml ~/ansible-lab/

Порядок запуска:

    ansible-playbook 01_nginx.yml --diff
    ansible-playbook 02_sshd.yml --diff
    ansible-playbook 03_motd.yml --diff
    ansible-playbook 04_lookup.yml
    ansible-playbook 05_slurp.yml

## На что обратить внимание

* Перед первым запуском 02_sshd.yml держите открытым второй сеанс SSH:
  шаблон заменяет sshd_config целиком, а не правит одну строку.
* trim_blocks и lstrip_blocks выставлены в задачах template явно: без
  lstrip_blocks в конфиг попадают строки из одних пробелов.
* Комментарии {# ... #} в готовый конфиг не попадают, а комментарии «#»
  попадают: они нужны тому, кто читает файл на узле.
* В конфиге nginx знак $ принадлежит nginx, а {{ }} — Jinja2.
* nginx слушает 8080, а не 80: порт 80 на web1 и web2 занят apache2,
  который поставили практики 9 и 10. Поэтому 01_nginx.yml убирает
  виртуальный хост по умолчанию, который пакет nginx ставит сам:
  тот слушает 80 и не дал бы nginx запуститься.
* Во всех задачах template стоит backup: true: прежний файл остаётся
  рядом с новым, с суффиксом даты.
* У задач template в 01_nginx.yml нет validate: в команде проверки
  обязателен %s, иначе задача падает с «validate must contain %s»,
  а подставить путь к нашему фрагменту нечем — nginx -t -c <файл>
  проверяет временный файл как полный конфиг и падает на директиве
  server. Поэтому проверка вынесена в отдельные задачи nginx -t:
  одна идёт до раскладки наших файлов (конфигурация могла быть
  сломана раньше, и виноват тогда не плейбук), вторая — после.
  Если вторая не прошла, плейбук убирает добавленные файлы,
  проверяет конфигурацию снова и останавливает прогон. Для одного
  файла validate работает: 02_sshd.yml проверяет sshd -t -f %s.
* 05_slurp.yml идёт по той же группе linux, что и 03_motd.yml: файл
  разворачивался на трёх машинах, значит и сверять его надо на трёх.
* Если у вас другой адрес DNS, поправьте resolv_nameservers
  в 03_motd.yml: файл /etc/resolv.conf перезаписывается шаблоном.

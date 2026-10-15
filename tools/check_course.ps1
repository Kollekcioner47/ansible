# check_course.ps1 — проверка структуры и оформления курса по Ansible.
#
# Скрипт не проверяет смысл: он ловит механические расхождения,
# которые человек пропускает. Забытая практика в оглавлении,
# разъехавшиеся часы в программах, потерянная секция, ссылка
# на несуществующий файл, маркдаун-разметка в текстовой практике.
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File tools\check_course.ps1
#
# Код возврата: 0 — расхождений нет, 1 — есть ошибки.
# Предупреждения на код возврата не влияют.

[CmdletBinding()]
param(
    [string]$Root = ''
)

if (-not $Root) {
    if ($PSScriptRoot) {
        $Root = Split-Path -Parent $PSScriptRoot
    }
    else {
        $Root = (Get-Location).Path
    }
}

$ErrorActionPreference = 'Stop'
$script:Errors = New-Object System.Collections.Generic.List[string]
$script:Warnings = New-Object System.Collections.Generic.List[string]

function Add-Error([string]$Message) { $script:Errors.Add($Message) | Out-Null }
function Add-Warn([string]$Message) { $script:Warnings.Add($Message) | Out-Null }

function Read-Utf8([string]$Path) {
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8) -split "`r?`n"
}

$Root = (Resolve-Path -LiteralPath $Root).Path
Write-Host "Проверка курса: $Root"
Write-Host ("-" * 73)

# -------------------------------------------------------------------------
# 1. Состав репозитория
# -------------------------------------------------------------------------

$practiceFiles = @(
    '1_install.txt', '2_inventory.txt', '3_yaml_ad_hoc.txt', '4_playbooks.txt',
    '5_variables_vault.txt', '6_facts_templates.txt', '7_conditions_loops.txt',
    '8_files.txt', '9_admin_tasks.txt', '10_roles.txt',
    '11_regex_configs.txt', '12_jinja_configs.txt', '13_storage_lvm.txt',
    '14_complex_projects.txt', '15_galaxy_collections.txt', '16_quality_inventory.txt'
)
$appFiles = @('app_1_commands.txt', 'app_2_troubleshooting.txt', 'app_3_windows_network.txt')
$otherFiles = @(
    'README.md', 'МЕТОДИКА_курса.md', 'ПЛАН_ПРАКТИК.md',
    'ПРОГРАММА_3_дня.md', 'ПРОГРАММА_5_дней.md',
    'LICENSE', 'LICENSE-CONTENT', '.gitignore',
    'tools/validate_files.py', 'tools/check_course.ps1',
    'archive/README.txt'
)

foreach ($f in ($practiceFiles + $appFiles + $otherFiles)) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $f))) {
        Add-Error "Не найден обязательный файл: $f"
    }
}

# Каталог прежней версии курса.
if (-not (Test-Path -LiteralPath (Join-Path $Root 'archive/Ansible.pptx'))) {
    Add-Error 'В archive/ нет презентации прежней версии (Ansible.pptx)'
}
if (-not (Test-Path -LiteralPath (Join-Path $Root 'archive/Практика'))) {
    Add-Error 'В archive/ нет каталога с прежними заметками (archive/Практика)'
}

# -------------------------------------------------------------------------
# 2. Оглавление README и часы
# -------------------------------------------------------------------------

$readmePath = Join-Path $Root 'README.md'
$readmeHours = @{}
if (Test-Path -LiteralPath $readmePath) {
    $readme = Read-Utf8 $readmePath

    foreach ($p in ($practiceFiles + $appFiles)) {
        if (-not ($readme -match [regex]::Escape("($p)"))) {
            Add-Error "README.md не ссылается на файл $p"
        }
    }
    foreach ($p in @('ПРОГРАММА_3_дня.md', 'ПРОГРАММА_5_дней.md', 'archive/README.txt')) {
        if (-not ($readme -match [regex]::Escape("($p)"))) {
            Add-Warn "README.md не ссылается на $p"
        }
    }

    # Строка оглавления: | N | тема | [файл](файл) | часы | трек | о чём |
    $sum = 0
    foreach ($line in $readme) {
        if ($line -notmatch '^\|\s*\d+\s*\|') { continue }
        $cells = $line.Split('|')
        if ($cells.Count -ne 8) { continue }
        $fileCell = $cells[3]
        $hourCell = $cells[4].Trim()
        if ($fileCell -notmatch '\]\((\d+_[a-z_]+\.txt)\)') { continue }
        $file = $Matches[1]
        if ($hourCell -notmatch '^\d+([,.]\d+)?$') {
            Add-Error "В оглавлении README у практики $file не число в колонке «Часы»: '$hourCell'"
            continue
        }
        $hours = [double]($hourCell -replace ',', '.')
        $readmeHours[$file] = $hours
        $sum += $hours
    }
    if ([math]::Abs($sum - 40) -gt 0.001) {
        Add-Error "Сумма часов в оглавлении README равна $sum, а должна быть 40"
    }
    foreach ($p in $practiceFiles) {
        if (-not $readmeHours.ContainsKey($p)) {
            Add-Error "В оглавлении README нет строки с часами для $p"
        }
    }
}

function Get-PracticeHours([string]$File) {
    if ($readmeHours.ContainsKey($File)) { return $readmeHours[$File] }
    return 2
}

# -------------------------------------------------------------------------
# 3. Программы треков: обязательные модули и суммы часов
# -------------------------------------------------------------------------

function Test-ProgramFile([string]$Path, [double]$ExpectedTotal, [int]$ExpectedModules) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $lines = Read-Utf8 $Path
    $name = Split-Path -Leaf $Path
    $sum = 0.0
    $modules = @()
    foreach ($line in $lines) {
        if ($line -notmatch '^\|\s*\d+\s*\|') { continue }
        $cells = $line.Split('|')
        if ($cells.Count -ne 8) { continue }
        $hourCell = $cells[3].Trim()
        if ($hourCell -notmatch '^\d+([,.]\d+)?$') { continue }
        $modules += [int]$cells[1].Trim()
        $sum += [double]($hourCell -replace ',', '.')
    }
    if ([math]::Abs($sum - $ExpectedTotal) -gt 0.001) {
        Add-Error "$name : сумма часов по модулям равна $sum, а должна быть $ExpectedTotal"
    }
    if ($modules.Count -ne $ExpectedModules) {
        Add-Error "$name : модулей $($modules.Count), а должно быть $ExpectedModules"
    }
    $expected = 1..$ExpectedModules
    if (($modules -join ',') -ne ($expected -join ',')) {
        Add-Error "$name : номера модулей не совпадают с ожидаемыми 1..$ExpectedModules"
    }
    foreach ($key in @('Стенд', 'Форма контроля')) {
        if (-not ($lines -match [regex]::Escape($key))) {
            Add-Warn "$name : нет раздела со словами «$key»"
        }
    }
}

Test-ProgramFile (Join-Path $Root 'ПРОГРАММА_3_дня.md') 24 10
Test-ProgramFile (Join-Path $Root 'ПРОГРАММА_5_дней.md') 40 16

# -------------------------------------------------------------------------
# 4. Оформление практик
# -------------------------------------------------------------------------

$requiredSections = @(
    'ЧТО МЫ СДЕЛАЕМ',
    'ЧТО ПОНАДОБИТСЯ',
    'ЧАСТЬ 1.',
    'ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК',
    'ПРОВЕРКА РЕЗУЛЬТАТА',
    'ЧТО ДАЛЬШЕ'
)
$markers = @(
    'ПОЧЕМУ ИМЕННО ТАК:', 'ЗАЧЕМ ЭТО В РАБОТЕ:', 'ЧЕГО НЕ ДЕЛАТЬ:',
    'ВАЖНО:', 'ИСПРАВЛЕНО:', 'ПРОВЕРКА:'
)
# Адреса из прежней версии курса: в новом стенде их быть не должно.
# Прежние адреса легко скопировать вместе с примером из старой версии.
$forbiddenInPractices = @{
    '10.0.2.6'  = 'адрес из прежней версии курса (целевой сервер GitLab)'
    '10.0.2.14' = 'адрес из прежней версии курса (узел node2)'
}

$checkIndex = 0
foreach ($file in $practiceFiles) {
    $checkIndex++
    $path = Join-Path $Root $file
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $lines = Read-Utf8 $path
    $expectedNumber = $checkIndex

    if ($lines[0] -notmatch "^Практика $expectedNumber\.\s+\S") {
        Add-Error "$file : первая строка должна быть «Практика $expectedNumber. Название», а там: '$($lines[0])'"
    }
    foreach ($section in $requiredSections) {
        if (-not ($lines -match [regex]::Escape($section))) {
            Add-Error "$file : нет обязательной секции «$section»"
        }
    }
    $markerCount = 0
    foreach ($m in $markers) {
        $markerCount += ($lines | Where-Object { $_.StartsWith($m) }).Count
    }
    if ($markerCount -lt 5) {
        Add-Error "$file : пометок вида ПОЧЕМУ/ЗАЧЕМ/ВАЖНО всего $markerCount, нужно не меньше 5"
    }
    $problemCount = ($lines | Where-Object { $_.StartsWith('ПРОБЛЕМА:') }).Count
    if ($problemCount -lt 3) {
        Add-Error "$file : блоков «ПРОБЛЕМА:» всего $problemCount, нужно не меньше 3"
    }

    $minLines = switch ([int](Get-PracticeHours $file)) {
        3 { 450 }
        4 { 500 }
        default { 400 }
    }
    if ($lines.Count -lt $minLines) {
        Add-Error "$file : строк $($lines.Count), а для такого объёма нужно не меньше $minLines"
    }
    if ($lines.Count -gt 1800) {
        Add-Warn "$file : строк $($lines.Count) — практика длиннее ориентира (1800)"
    }

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $n = $i + 1

        if ($line -match '^[=#]{5,}$' -and $line.Length -ne 73) {
            Add-Error "$file : строка $n — разделитель длиной $($line.Length), а нужно ровно 73"
        }
        if ($line -match '^#{1,6}\s') {
            Add-Error "$file : строка $n — маркдаун-заголовок в текстовой практике"
        }
        if ($line -match '\*\*[^\s*]') {
            Add-Error "$file : строка $n — маркдаун-выделение ** в текстовой практике"
        }
        if ($line -match "`t") {
            Add-Error "$file : строка $n — символ табуляции"
        }
        if ($line.Length -gt 88 -and $line -notmatch '^\s' -and $line -notmatch '^[=#]{5,}$') {
            Add-Warn "$file : строка $n не перенесена ($($line.Length) символов): $($line.Substring(0, 40))..."
        }
        # Короткие имена фактов: в ansible-core они устарели
        # (INJECT_FACTS_AS_VARS, удаление в 2.24). Не считаются:
        # строки фильтра модуля setup, ключи в напечатанном выводе
        # модуля ("ansible_os_family": "Debian"), комментарии и проза
        # без отступа. Код с отступом проверяется и тогда, когда
        # в строке есть русский комментарий.
        if ($line -notmatch 'filter=ansible_' -and
            $line -notmatch '"\s*ansible_' -and
            $line -notmatch '^\s*#' -and
            ($line -match '^\s' -or $line -notmatch '[А-Яа-яЁё]') -and
            $line -match "(?<!\[')ansible_(os_family|distribution_major_version|distribution_version|distribution_release|distribution|hostname|fqdn|default_ipv4|all_ipv4_addresses|memtotal_mb|memfree_mb|swaptotal_mb|processor_vcpus|processor_cores|mounts|date_time|kernel|pkg_mgr|service_mgr|architecture|virtualization_type|virtualization_role|machine_id|machine|nodename|domain|interfaces|apparmor|selinux|cmdline|bios_version|product_name|uptime_seconds|python_version|system|env|ansible_local)(?!'\])") {
            Add-Warn "$file : строка $n — короткое имя факта ($($Matches[1])): в ansible-core 2.24 такие имена удаляются, нужна форма ansible_facts['...']"
        }

        foreach ($bad in $forbiddenInPractices.Keys) {
            if ($line -match [regex]::Escape($bad)) {
                Add-Error "$file : строка $n — «$bad»: $($forbiddenInPractices[$bad])"
            }
        }
    }

    # Ссылки на files/ должны существовать.
    foreach ($line in $lines) {
        foreach ($m in [regex]::Matches($line, 'files/[A-Za-z0-9_./-]+')) {
            $rel = $m.Value.TrimEnd('.', ',', ')', ':')
            $target = Join-Path $Root $rel
            if (-not (Test-Path -LiteralPath $target)) {
                Add-Error "$file : ссылка на несуществующий путь $rel"
            }
        }
    }
}

# -------------------------------------------------------------------------
# 5. Приложения
# -------------------------------------------------------------------------

foreach ($app in $appFiles) {
    $path = Join-Path $Root $app
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $lines = Read-Utf8 $path
    if ($lines.Count -lt 150) {
        Add-Error "$app : строк $($lines.Count), приложение не должно быть короче 150"
    }
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^[=#]{5,}$' -and $lines[$i].Length -ne 73) {
            Add-Error "$app : строка $($i + 1) — разделитель длиной $($lines[$i].Length), а нужно ровно 73"
        }
    }
}
if (Test-Path -LiteralPath (Join-Path $Root 'app_2_troubleshooting.txt')) {
    $app2 = Read-Utf8 (Join-Path $Root 'app_2_troubleshooting.txt')
    $pc = ($app2 | Where-Object { $_.StartsWith('ПРОБЛЕМА:') }).Count
    if ($pc -lt 20) {
        Add-Error "app_2_troubleshooting.txt : блоков «ПРОБЛЕМА:» всего $pc, нужно не меньше 20"
    }
}

# -------------------------------------------------------------------------
# 6. Каталоги files/
# -------------------------------------------------------------------------

for ($i = 1; $i -le 16; $i++) {
    $prefix = '{0:d2}' -f $i
    $dirs = Get-ChildItem -LiteralPath (Join-Path $Root 'files') -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "^${prefix}_" }
    if ($i -eq 1) {
        if ($dirs) { Add-Error "files/ : у практики 1 не должно быть каталога с файлами" }
        continue
    }
    if (-not $dirs) {
        Add-Error "files/ : нет каталога files/${prefix}_имя для практики $i"
        continue
    }
    foreach ($d in $dirs) {
        if (-not (Test-Path -LiteralPath (Join-Path $d.FullName 'README.md'))) {
            Add-Error "files/$($d.Name) : нет README.md"
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $Root 'files')) {
    $scripts = Get-ChildItem -LiteralPath (Join-Path $Root 'files') -Recurse -File |
        Where-Object { $_.Extension -in @('.sh', '.bash', '.ps1', '.cmd', '.bat') }
    foreach ($s in $scripts) {
        Add-Error "files/ : готовый скрипт $($s.Name) — в materials курса их быть не должно"
    }
    $py = Get-ChildItem -LiteralPath (Join-Path $Root 'files') -Recurse -File -Filter '*.py'
    foreach ($p in $py) {
        $allowed = (Join-Path $Root 'files/16_quality_inventory')
        if (-not $p.FullName.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) {
            Add-Error "files/ : python-скрипт $($p.Name) разрешён только во внешнем инвентаре (files/16_quality_inventory)"
        }
    }
}

# -------------------------------------------------------------------------
# 7. Лицензии и архив
# -------------------------------------------------------------------------

if (Test-Path -LiteralPath (Join-Path $Root 'LICENSE')) {
    $lic = Get-Content -LiteralPath (Join-Path $Root 'LICENSE') -Raw -Encoding UTF8
    if ($lic -notmatch 'MIT License') { Add-Error 'LICENSE : это не текст лицензии MIT' }
}
if (Test-Path -LiteralPath (Join-Path $Root 'LICENSE-CONTENT')) {
    $lic = Get-Content -LiteralPath (Join-Path $Root 'LICENSE-CONTENT') -Raw -Encoding UTF8
    if ($lic -notmatch 'CC BY-NC-SA 4\.0') { Add-Error 'LICENSE-CONTENT : не упомянута лицензия CC BY-NC-SA 4.0' }
    if ($lic -notmatch 'Ansible') { Add-Error 'LICENSE-CONTENT : нет названия курса' }
}
if (Test-Path -LiteralPath (Join-Path $Root 'archive/README.txt')) {
    $arc = Read-Utf8 (Join-Path $Root 'archive/README.txt')
    if ($arc.Count -lt 100) { Add-Error 'archive/README.txt : слишком короткий разбор прежней версии' }
    foreach ($key in @('Ansible.pptx', 'Практика/')) {
        if (-not ($arc -match [regex]::Escape($key))) {
            Add-Error "archive/README.txt : не упомянуто содержимое каталога ($key)"
        }
    }
}

# -------------------------------------------------------------------------
# Итог
# -------------------------------------------------------------------------

Write-Host ""
if ($script:Warnings.Count -gt 0) {
    Write-Host "ПРЕДУПРЕЖДЕНИЯ ($($script:Warnings.Count)):" -ForegroundColor Yellow
    foreach ($w in $script:Warnings) { Write-Host "  ! $w" -ForegroundColor Yellow }
    Write-Host ""
}
if ($script:Errors.Count -gt 0) {
    Write-Host "ОШИБКИ ($($script:Errors.Count)):" -ForegroundColor Red
    foreach ($e in $script:Errors) { Write-Host "  x $e" -ForegroundColor Red }
    Write-Host ""
    Write-Host "Проверка не пройдена." -ForegroundColor Red
    exit 1
}
Write-Host "Проверка пройдена: расхождений нет." -ForegroundColor Green
exit 0

param([Parameter(Mandatory=$true)][string]$MevcutProje)
$ErrorActionPreference = 'Stop'
$exportRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$exportApp = Join-Path $exportRoot 'uygulama'
$sourceApp = (Resolve-Path -LiteralPath $MevcutProje).Path
if ($sourceApp -eq $exportApp) { throw 'Kaynak ortam ile hedef uygulama aynı klasör olamaz.' }
foreach ($name in @('.venv', '.venv-cad', 'tools')) {
    $source = Join-Path $sourceApp $name
    $target = Join-Path $exportApp $name
    if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw ('Kaynak dizin yok: ' + $source) }
    if (Test-Path -LiteralPath $target) { throw ('Hedef zaten var; değiştirilmedi: ' + $target) }
}
foreach ($name in @('.venv', '.venv-cad', 'tools')) {
    New-Item -ItemType Junction -Path (Join-Path $exportApp $name) -Target (Join-Path $sourceApp $name) | Out-Null
}
Write-Output 'Mevcut ortam yalnız bu depo içinde bağlandı. Global PATH ve kaynak proje değiştirilmedi.'

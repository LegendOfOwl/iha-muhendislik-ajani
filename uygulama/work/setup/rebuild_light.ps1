param([string]$PythonBase)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location -LiteralPath $projectRoot
if (-not $PythonBase) {
    $config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'tool_config.json') -Raw | ConvertFrom-Json
    $PythonBase = Join-Path $config.python_base 'python.exe'
}
if (-not (Test-Path -LiteralPath $PythonBase -PathType Leaf)) {
    throw 'Python tabani bulunamadi. Mevcut Python 3.12 yolunu -PythonBase parametresiyle belirtin.'
}
$version = & $PythonBase -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $version -ne '3.12') { throw 'Bu kilitli paketler Windows x64 Python 3.12 icindir.' }
foreach ($definition in @(@('.venv', 'requirements-core.txt'), @('.venv-cad', 'requirements-cad.txt'))) {
    $environmentPath = Join-Path $projectRoot $definition[0]
    $pythonPath = Join-Path $environmentPath 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        & $PythonBase -m venv $environmentPath
        if ($LASTEXITCODE -ne 0) { throw 'Python ortami olusturulamadi.' }
    } else {
        & $PythonBase -m venv --upgrade $environmentPath
        if ($LASTEXITCODE -ne 0) { throw 'Python ortami tabani yenilenemedi.' }
    }
    & $pythonPath -m pip install --only-binary=:all: --require-hashes -r (Join-Path $PSScriptRoot $definition[1])
    if ($LASTEXITCODE -ne 0) { throw 'Paket kurulumu basarisiz.' }
    & $pythonPath -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Bagimlilik kontrolu basarisiz.' }
}
& (Join-Path $projectRoot '.venv\Scripts\python.exe') -X utf8 (Join-Path $projectRoot 'work\tests\run_checks.py')
exit $LASTEXITCODE

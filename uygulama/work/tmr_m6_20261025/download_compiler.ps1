$ErrorActionPreference='Stop'
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'compiler_plan.json') -Raw | ConvertFrom-Json
$cache=Join-Path $PSScriptRoot 'sources/compiler_packages'
New-Item -ItemType Directory -Path $cache -Force | Out-Null
$items=$plan.packages | ForEach-Object -Parallel {
    $p=$_
    $archive=Join-Path $using:cache $p.FILENAME
    try {
        if ($p.url -notlike 'https://mirror.msys2.org/mingw/ucrt64/*') { throw 'Unexpected package host' }
        if (-not (Test-Path -LiteralPath $archive)) {
            Invoke-WebRequest -Uri $p.url -OutFile $archive -TimeoutSec 90
        }
        $actual=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $p.SHA256SUM) { throw 'Official database SHA256 mismatch' }
        [pscustomobject]@{name=$p.NAME;file=$archive;sha256=$actual;status='verified';utc=[DateTime]::UtcNow.ToString('o')}
    } catch {
        [pscustomobject]@{name=$p.NAME;file=$archive;status='failed';error=$_.Exception.Message;utc=[DateTime]::UtcNow.ToString('o')}
    }
} -ThrottleLimit 4
$items | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'compiler_downloads.json') -Encoding utf8
$items | Select-Object name,status | Format-Table
if (@($items | Where-Object status -ne 'verified').Count -gt 0) { throw 'A scoped compiler package failed' }

$ErrorActionPreference = 'Stop'
$sourceDir = Join-Path $PSScriptRoot 'sources'
$entries = @(
    @('https://arxiv.org/pdf/2601.15522v1', 'arxiv_2601_15522v1.pdf'),
    @('https://arxiv.org/html/2509.18178v1', 'foam_agent_2509_18178v1.html'),
    @('https://arxiv.org/html/2602.11689v1', 'coding_agents_2602_11689v1.html'),
    @('https://arxiv.org/html/2605.06607v1', 'cfd_scientist_2605_06607v1.html'),
    @('https://nas.nasa.gov/LAVA/unst_docs/tutorials/onera_M6/onera_M6/', 'lava_m6.html'),
    @('https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html', 'nasa_grid_convergence.html'),
    @('https://tmbwg.github.io/turbmodels/flatplate.html', 'tmr_flatplate.html')
)
$results = foreach ($entry in $entries) {
    $dest = Join-Path $sourceDir $entry[1]
    try {
        if (-not (Test-Path -LiteralPath $dest)) {
            Invoke-WebRequest -Uri $entry[0] -OutFile $dest -TimeoutSec 40
        }
        [pscustomobject]@{file=$entry[1]; url=$entry[0]; status='archived'; utc=[DateTime]::UtcNow.ToString('o')}
    } catch {
        [pscustomobject]@{file=$entry[1]; url=$entry[0]; status='failed'; error=$_.Exception.Message; utc=[DateTime]::UtcNow.ToString('o')}
    }
}
$results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sourceDir 'windows_download_log.json') -Encoding utf8
$results | Select-Object file,status | Format-Table

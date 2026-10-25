$ErrorActionPreference='Stop'
$sourceDir=Join-Path $PSScriptRoot 'sources'
$items=@(
 @('https://www.nasa.gov/wp-content/uploads/2026/02/flatplategrids-grids.zip','flatplategrids-grids.zip'),
 @('https://raw.githubusercontent.com/su2code/Tutorials/master/compressible_flow/Turbulent_Flat_Plate/turb_SA_flatplate.cfg','turb_SA_flatplate.cfg'),
 @('https://tmbwg.github.io/turbmodels/flatplate.html','flatplate.html'),
 @('https://tmbwg.github.io/turbmodels/flatplate_grids.html','flatplate_grids.html'),
 @('https://tmbwg.github.io/turbmodels/flatplate_sa.html','flatplate_sa.html'),
 @('https://tmbwg.github.io/turbmodels/FlatPlate/SA/cfl3d_typical.inp','cfl3d_typical.inp'),
 @('https://su2code.github.io/tutorials/Turbulent_Flat_Plate/','SU2_tutorial.html')
)
$records=foreach($entry in $items){
 $p=Join-Path $sourceDir $entry[1]
 if(-not(Test-Path -LiteralPath $p)){Invoke-WebRequest -Uri $entry[0] -OutFile $p -TimeoutSec 60}
 [pscustomobject]@{url=$entry[0];file=$entry[1];sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $p).Length;retrieved_or_verified_utc=[DateTime]::UtcNow.ToString('o')}
}
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sourceDir 'input_sources_manifest.json') -Encoding utf8
$records | Select-Object file,bytes

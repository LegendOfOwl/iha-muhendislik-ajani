$ErrorActionPreference='Stop'
$caseDir=Join-Path $PSScriptRoot '../../outputs/simulations/flatplate_SAneg_20261025_v1'
foreach($role in @('coarse','medium','fine')){if(-not(Test-Path -LiteralPath (Join-Path $caseDir "$role/prediction_frozen.json"))){throw 'Baseline predictions must be frozen first'}}
if(Test-Path -LiteralPath (Join-Path $caseDir 'nested_seed/contract.json')){if(-not(Test-Path -LiteralPath (Join-Path $caseDir 'fine_nested/prediction_frozen.json'))){throw 'Nested prediction must also be frozen before references'}}
$sourceDir=Join-Path $PSScriptRoot 'sources'
$items=@('cf_convergence.dat','drag_convergence.dat','cf_plate.dat','mut_0.97.dat','flatplate_u.dat','flatplate_u%2By%2B.dat')
$records=foreach($name in $items){
 $url='https://tmbwg.github.io/turbmodels/FlatPlate/SA/'+$name
 $p=Join-Path $sourceDir ([Uri]::UnescapeDataString($name))
 if(-not(Test-Path -LiteralPath $p)){Invoke-WebRequest -Uri $url -OutFile $p -TimeoutSec 45}
 [pscustomobject]@{url=$url;file=(Split-Path -Leaf $p);sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $p).Length;retrieved_or_verified_utc=[DateTime]::UtcNow.ToString('o')}
}
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sourceDir 'reference_manifest.json') -Encoding utf8
$records | Select-Object file,bytes

$ErrorActionPreference='Stop'
$sourceDir=Join-Path $PSScriptRoot 'sources'
$items=@(
 @('https://tmbwg.github.io/turbmodels/Onerawingnumerics_grids/AileM6_with_sharp_TE.stp','AileM6_with_sharp_TE.stp'),
 @('https://tmbwg.github.io/turbmodels/Onerawingnumerics_val/case_2308.dat','case_2308.dat'),
 @('https://tmbwg.github.io/turbmodels/Onerawingnumerics_val/SA/combined_forces_pitchmom_maxmut.dat','combined_forces_pitchmom_maxmut.dat'),
 @('https://tmbwg.github.io/turbmodels/Onerawingnumerics_val/SA/CFL3D_OM6_A3p06_CPCF.dat','CFL3D_OM6_A3p06_CPCF.dat'),
 @('https://tmbwg.github.io/turbmodels/Onerawingnumerics_val/SA/cfl3d_OM6sampleinput_L2.inp','cfl3d_OM6sampleinput_L2.inp'),
 @('https://su2code.github.io/docs_v7/Physical-Definition/','SU2_physical_definition.html')
)
$records=foreach($entry in $items){
 $p=Join-Path $sourceDir $entry[1]
 if(-not(Test-Path -LiteralPath $p)){Invoke-WebRequest -Uri $entry[0] -OutFile $p -TimeoutSec 45}
 [pscustomobject]@{url=$entry[0];file=$entry[1];sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $p).Length;downloaded_utc=[DateTime]::UtcNow.ToString('o')}
}
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sourceDir 'case_sources_manifest.json') -Encoding utf8
$records | Select-Object file,bytes | Format-Table

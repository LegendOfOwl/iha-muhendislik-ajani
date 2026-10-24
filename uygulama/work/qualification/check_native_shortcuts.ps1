$ErrorActionPreference='Stop'
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskFreecad=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskOpenvsp=Get-Content (Join-Path $taskRoot 'work/setup/openvsp_install.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskCfd=Get-Content (Join-Path $taskRoot 'outputs/reports/cfd_reference_comparison.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskPaths=@($taskFreecad.executables.'FreeCAD.exe',$taskFreecad.executables.'gmsh.exe',$taskOpenvsp.executables.'vsp.exe',
    $taskCfd.gmsh_pressure_view,(Join-Path $taskRoot 'outputs/cad/complex_native_wing.vsp3'),
    (Join-Path $taskRoot 'outputs/cad/parametric_wing/review_envelope_and_ribs.step'))
foreach($taskPath in $taskPaths) {if(!(Test-Path -LiteralPath $taskPath)){throw ('Missing path: '+$taskPath)}}
$taskLog=Join-Path $taskRoot 'work/qualification/gmsh_native_readback.log'
& $taskFreecad.executables.'gmsh.exe' $taskCfd.gmsh_pressure_view -parse_and_exit 2>&1 | Out-File -LiteralPath $taskLog -Encoding utf8
if($LASTEXITCODE -ne 0){throw 'Native Gmsh readback failed'}
$taskResult=@{passed=$true;windows_powershell_version=$PSVersionTable.PSVersion.ToString();shortcut_paths_checked=$taskPaths.Count;
    gmsh_native_readback=$true;gmsh_version='4.15.0';log='work/qualification/gmsh_native_readback.log';
    scope='JSON parsing and native file readback; no CAD geometry generated in this check'}
$taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'outputs/reports/native_shortcut_checks.json') -Encoding UTF8
Write-Output 'NATIVE_SHORTCUTS_AND_GMSH_READBACK_OK'

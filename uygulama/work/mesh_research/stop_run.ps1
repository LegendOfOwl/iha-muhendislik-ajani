param([Parameter(Mandatory=$true)][string]$CaseName,[Parameter(Mandatory=$true)][string]$Reason,[int]$Checkpoint=1000)
$ErrorActionPreference='Stop'
if (-not $CaseName.StartsWith('v3_')) {throw 'Only this study owned runs may be stopped'}
$studyRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../outputs/projects/proje-15cce2de02/simulations'))
$trialDir = [IO.Path]::GetFullPath((Join-Path $studyRoot $CaseName))
if (-not $trialDir.StartsWith($studyRoot + [IO.Path]::DirectorySeparatorChar)) {throw 'Case outside study root'}
$info = Get-Content -LiteralPath (Join-Path $trialDir 'process.json') | ConvertFrom-Json
$native = Get-Process -Id $info.pid -ErrorAction Stop
$expectedNative = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../tools/su2/v8.5.0/bin/SU2_CFD.exe'))
if (($native.ProcessName -ne 'SU2_CFD') -or ($native.Path -ne $expectedNative)) {throw 'Process identity mismatch'}
$stamp = '{0:D6}' -f $Checkpoint
foreach ($file in @("restart_flow_$stamp.dat","surface_flow_$stamp.vtu","flow_$stamp.vtu")) {
    if (-not (Test-Path -LiteralPath (Join-Path $trialDir $file))) {throw "Required checkpoint file missing: $file"}
}
@{reason=$Reason;checkpoint=$Checkpoint;timestamp_utc=[DateTime]::UtcNow.ToString('o');pid=$info.pid;process_path=$native.Path} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $trialDir 'manual_stop_request.json') -Encoding utf8
Stop-Process -Id $info.pid -Force
Write-Output "Preserved $CaseName checkpoint $Checkpoint and stopped the owned native process."

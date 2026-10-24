$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskCompiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$taskSource=Join-Path $taskRoot 'work/agent/Launcher.cs'
$taskOutput=Join-Path $taskRoot 'outputs/Muhendislik-Merkezi.exe'
& $taskCompiler /nologo /target:winexe /optimize+ /reference:System.Windows.Forms.dll /reference:System.Drawing.dll ('/out:'+$taskOutput) $taskSource
if($LASTEXITCODE -ne 0){throw 'EXE derlenemedi'}
Write-Output 'EXE_BUILD_OK'

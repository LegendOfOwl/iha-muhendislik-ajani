param([switch]$SelfTest)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$projectRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$numericPython=Join-Path $projectRoot '.venv/Scripts/python.exe'
$projectScript=Join-Path $projectRoot 'work/agent/project.py'
$outputsRoot=Join-Path $projectRoot 'outputs'
$script:activeProcess=$null
$script:actionButtons=New-Object System.Collections.Generic.List[System.Windows.Forms.Button]
$form=New-Object System.Windows.Forms.Form
$form.Text='İHA Mühendislik — Proje Merkezi'
$form.ClientSize=New-Object System.Drawing.Size(1000,720)
$form.StartPosition='CenterScreen'
$form.MinimumSize=$form.Size
$form.BackColor=[System.Drawing.Color]::FromArgb(241,244,248)
$form.Font=New-Object System.Drawing.Font('Segoe UI',10)
$header=New-Object System.Windows.Forms.Panel
$header.SetBounds(0,0,1000,92)
$header.BackColor=[System.Drawing.Color]::FromArgb(19,39,59)
$form.Controls.Add($header)
function LabelAt($parent,$text,$x,$y,$w,$h,$size=10,$white=$false) {
    $label=New-Object System.Windows.Forms.Label
    $label.Text=$text; $label.SetBounds($x,$y,$w,$h)
    $label.Font=New-Object System.Drawing.Font('Segoe UI',$size)
    if ($white) { $label.ForeColor=[System.Drawing.Color]::White }
    $parent.Controls.Add($label)
    return $label
}
$null=LabelAt $header 'İHA MÜHENDİSLİK' 28 16 800 32 19 $true
$null=LabelAt $header 'Görev ver → araçlar çalışsın → çizim, hesap ve kanıt birlikte kaydedilsin' 30 54 920 26 10 $true
$null=LabelAt $form '1   Görevini kendi cümlelerinle yaz' 28 114 720 32 14
$taskInput=New-Object System.Windows.Forms.TextBox
$taskInput.Multiline=$true; $taskInput.AcceptsReturn=$true
$taskInput.ScrollBars='Vertical'; $taskInput.SetBounds(30,153,940,102)
$form.Controls.Add($taskInput)
$null=LabelAt $form 'Örnek: İki kanat adayını aynı koşullarda analiz et; kaynakları, çizimleri ve açık kontrolleri raporla.' 30 264 940 40 9
function ButtonAt($text,$x,$y,$w,$handler,$isAction=$false) {
    $button=New-Object System.Windows.Forms.Button
    $button.Text=$text; $button.SetBounds($x,$y,$w,40)
    $button.FlatStyle='Flat'; $button.BackColor=[System.Drawing.Color]::White
    $button.Add_Click($handler)
    $form.Controls.Add($button)
    if ($isAction) {$script:actionButtons.Add($button)}
    return $button
}
$launch=ButtonAt 'Ajanla çalışmaya başla' 30 308 280 {
    if ([string]::IsNullOrWhiteSpace($taskInput.Text)) {return}
    $inbox=Join-Path $projectRoot 'work/agent/inbox'
    [System.IO.Directory]::CreateDirectory($inbox) | Out-Null
    $requestPath=Join-Path $inbox (([Guid]::NewGuid().ToString())+'.json')
    $request=@{request=$taskInput.Text;kind='engineering'} | ConvertTo-Json
    [System.IO.File]::WriteAllText($requestPath,$request,(New-Object System.Text.UTF8Encoding($false)))
    $argsList=@('-X','utf8',('"'+$projectScript+'"'),'submit',('"'+$requestPath+'"'))
    Start-Process -FilePath $numericPython -ArgumentList $argsList -WorkingDirectory $projectRoot -WindowStyle Hidden
    $activity.Text='Görev kaydedildi. Codex görev penceresi açılıyor; aynı ChatGPT hesabını kullanır.'
}
$launch.BackColor=[System.Drawing.Color]::FromArgb(12,109,112)
$launch.ForeColor=[System.Drawing.Color]::White
$null=ButtonAt 'Proje durumunu aç' 330 308 220 {Start-Process -FilePath (Join-Path $outputsRoot 'Proje-Ozeti.html')}
$null=ButtonAt 'Çıktı klasörü' 570 308 190 {Start-Process -FilePath explorer.exe -ArgumentList ('"'+$outputsRoot+'"')}
$null=ButtonAt 'Kullanım kılavuzu' 780 308 190 {Start-Process -FilePath notepad.exe -ArgumentList ('"'+(Join-Path $outputsRoot 'Baslangic.md')+'"')}
$null=LabelAt $form '2   Araçları dene ve sonuçları incele' 28 374 840 34 14
function StartCheck($suite) {
    if ($script:activeProcess) {return}
    $logs=Join-Path $projectRoot 'work/agent/ui-logs'
    [System.IO.Directory]::CreateDirectory($logs)|Out-Null
    $script:outLog=Join-Path $logs ($suite+'-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
    $script:errLog=$script:outLog+'.err'
    $argsList=@('-X','utf8',('"'+$projectScript+'"'),'run',$suite)
    $script:activeProcess=Start-Process -FilePath $numericPython -ArgumentList $argsList -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $script:outLog -RedirectStandardError $script:errLog
    foreach ($button in $script:actionButtons) {$button.Enabled=$false}
    $activity.Text='Çalışıyor: '+$suite+'. Pencereyi açık bırakabilirsin. Ham sonuçlar ayrıca kaydediliyor.'
}
$null=ButtonAt 'Kanat analizi (VLM)' 30 420 220 {StartCheck 'complex-vlm'} $true
$null=ButtonAt 'CFD (SU2, ~10 dk)' 270 420 220 {StartCheck 'cfd'} $true
$null=ButtonAt 'Parametrik CAD' 510 420 220 {StartCheck 'geometry'} $true
$null=ButtonAt 'Yapısal analiz (FEM)' 750 420 220 {StartCheck 'fem'} $true
$null=ButtonAt 'CFD alanını aç' 30 474 220 {
    $report=Get-Content (Join-Path $outputsRoot 'reports/cfd_reference_comparison.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $meta=Get-Content (Join-Path $projectRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Start-Process -FilePath $meta.executables.'gmsh.exe' -ArgumentList ('"'+$report.gmsh_pressure_view+'"')
}
$null=ButtonAt 'OpenVSP modelini aç' 270 474 220 {
    $meta=Get-Content (Join-Path $projectRoot 'work/setup/openvsp_install.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $modelPath=Join-Path $outputsRoot 'cad/complex_native_wing.vsp3'
    if (!(Test-Path $modelPath)) {$modelPath=Join-Path $outputsRoot 'cad/aircraft_demo.vsp3'}
    Start-Process -FilePath $meta.executables.'vsp.exe' -ArgumentList ('"'+$modelPath+'"')
}
$null=ButtonAt 'FreeCAD modelini aç' 510 474 220 {
    $meta=Get-Content (Join-Path $projectRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $env:FREECAD_USER_HOME=Join-Path $projectRoot 'work/freecad/home'
    $env:FREECAD_USER_DATA=Join-Path $projectRoot 'work/freecad/data'
    $env:FREECAD_USER_TEMP=Join-Path $projectRoot 'work/freecad/temp'
    $modelPath=Join-Path $outputsRoot 'cad/parametric_wing/review_envelope_and_ribs.step'
    if (!(Test-Path $modelPath)) {$modelPath=Join-Path $outputsRoot 'cad/cantilever_qualification.FCStd'}
    Start-Process -FilePath $meta.executables.'FreeCAD.exe' -ArgumentList ('"'+$modelPath+'"')
}
$null=ButtonAt 'Gerçek proje girdileri' 750 474 220 {Start-Process -FilePath explorer.exe -ArgumentList ('"'+(Join-Path $outputsRoot 'data/project')+'"')}
$activity=New-Object System.Windows.Forms.TextBox
$activity.Multiline=$true; $activity.ReadOnly=$true; $activity.ScrollBars='Vertical'
$activity.SetBounds(30,542,940,113); $activity.BackColor=[System.Drawing.Color]::White
$activity.Text="Hazır. Düğmeler kayıtlı yeterlilik örneklerini yeniden çalıştırır; kendi profilin ve koşulların için üstte görev yaz.`r`nCFD ve VLM sürükleme kontrolleri henüz tam kabul edilmedi. Ayrıntılar güncel proje raporunda."
$form.Controls.Add($activity)
$null=LabelAt $form 'Model üretimi ve testlerin geçmesi, ölçülere uygunluk veya uçuşa elverişlilik garantisi değildir.' 30 674 940 30 9
$timer=New-Object System.Windows.Forms.Timer
$timer.Interval=1000
$timer.Add_Tick({
    if ($script:activeProcess) {
        if (Test-Path $script:outLog) {$activity.Text=[System.IO.File]::ReadAllText($script:outLog)}
        if ($script:activeProcess.HasExited) {
            $activity.AppendText("`r`nTamamlandı. Çıkış: "+$script:activeProcess.ExitCode+". Güncel sonuç: outputs/reports.")
            if ((Test-Path $script:errLog) -and (Get-Item $script:errLog).Length -gt 0) {$activity.AppendText("`r`n"+[System.IO.File]::ReadAllText($script:errLog))}
            $script:activeProcess=$null
            foreach ($button in $script:actionButtons) {$button.Enabled=$true}
        }
    }
})
if ($SelfTest) {
    $form.StartPosition='Manual'
    $form.Location=New-Object System.Drawing.Point(-30000,-30000)
    $form.ShowInTaskbar=$false
    $form.Show()
    [System.Windows.Forms.Application]::DoEvents()
    $bitmap=New-Object System.Drawing.Bitmap($form.Width,$form.Height)
    $form.DrawToBitmap($bitmap,(New-Object System.Drawing.Rectangle(0,0,$form.Width,$form.Height)))
    $bitmap.Save((Join-Path $outputsRoot 'plots/engineering_hub.png'))
    $bitmap.Dispose(); $form.Dispose()
    Write-Output 'HUB_RENDER_OK'
} else {
    $timer.Start()
    [System.Windows.Forms.Application]::Run($form)
    $timer.Stop(); $timer.Dispose()
}

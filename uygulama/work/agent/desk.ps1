param([switch]$SelfTest)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskPython=Join-Path $taskRoot '.venv/Scripts/python.exe'
$taskRunner=Join-Path $taskRoot 'work/agent/project.py'
$taskOut=Join-Path $taskRoot 'outputs'
$script:job=$null
$script:buttons=New-Object System.Collections.Generic.List[System.Windows.Forms.Button]
$form=New-Object System.Windows.Forms.Form
$form.Text='İHA Mühendislik Merkezi'
$form.ClientSize=New-Object System.Drawing.Size(1000,780)
$form.MinimumSize=$form.Size
$form.StartPosition='CenterScreen'
$form.BackColor=[System.Drawing.Color]::FromArgb(242,246,249)
$form.Font=New-Object System.Drawing.Font('Segoe UI',10)
function Label($parent,$text,$x,$y,$w,$h,$size=10) {
    $c=New-Object System.Windows.Forms.Label
    $c.Text=$text; $c.SetBounds($x,$y,$w,$h); $c.Font=New-Object System.Drawing.Font('Segoe UI',$size)
    $parent.Controls.Add($c); return $c
}
function TextBox($parent,$x,$y,$w,$h,$multi=$false) {
    $c=New-Object System.Windows.Forms.TextBox
    $c.SetBounds($x,$y,$w,$h); $c.Multiline=$multi
    if($multi){$c.ScrollBars='Vertical'; $c.AcceptsReturn=$true}
    $parent.Controls.Add($c); return $c
}
function Button($parent,$text,$x,$y,$w,$handler,$jobButton=$false) {
    $c=New-Object System.Windows.Forms.Button
    $c.Text=$text; $c.SetBounds($x,$y,$w,42); $c.FlatStyle='Flat'; $c.BackColor=[System.Drawing.Color]::White
    $c.Add_Click($handler); $parent.Controls.Add($c)
    if($jobButton){$script:buttons.Add($c)}
    return $c
}
function OpenOutput($relative) {
    $p=Join-Path $taskOut $relative
    if(Test-Path -LiteralPath $p){Start-Process -FilePath $p}
    else{[System.Windows.Forms.MessageBox]::Show('Bu çıktı henüz oluşmadı.','Mühendislik Merkezi')|Out-Null}
}
function StartJob($arguments,$label) {
    if($script:job){return}
    $folder=Join-Path $taskRoot 'work/agent/ui-logs'; [System.IO.Directory]::CreateDirectory($folder)|Out-Null
    $script:log=Join-Path $folder ((Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString()+'.txt')
    $script:err=$script:log+'.err'
    $script:label=$label
    $script:job=Start-Process -FilePath $taskPython -ArgumentList $arguments -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $script:log -RedirectStandardError $script:err
    foreach($button in $script:buttons){$button.Enabled=$false}
    $activity.Text=$label+' çalışıyor. Sonuçlar ve ham kayıtlar proje klasörüne yazılıyor.'
}
function StartSuite($suite,$label) {StartJob @('-X','utf8',('"'+$taskRunner+'"'),'run',$suite) $label}
$header=New-Object System.Windows.Forms.Panel
$header.SetBounds(0,0,1000,88); $header.BackColor=[System.Drawing.Color]::FromArgb(18,42,61); $form.Controls.Add($header)
$title=Label $header 'İHA MÜHENDİSLİK MERKEZİ' 25 12 950 36 20; $title.ForeColor=[System.Drawing.Color]::White
$sub=Label $header 'Kısıtlar → kaynaklı adaylar → CAD ve analiz → kabul kontrolleri → karşılaştırmalı rapor' 27 53 950 25 10; $sub.ForeColor=[System.Drawing.Color]::White
$tabs=New-Object System.Windows.Forms.TabControl
$tabs.SetBounds(22,104,956,540); $form.Controls.Add($tabs)
$requestTab=New-Object System.Windows.Forms.TabPage; $requestTab.Text='1  Görev ve kısıtlar'; $tabs.TabPages.Add($requestTab)
$analysisTab=New-Object System.Windows.Forms.TabPage; $analysisTab.Text='2  Analizler ve programlar'; $tabs.TabPages.Add($analysisTab)
$resultsTab=New-Object System.Windows.Forms.TabPage; $resultsTab.Text='3  Sonuçlar ve durum'; $tabs.TabPages.Add($resultsTab)
$null=Label $requestTab 'Ne tasarlayalım veya karşılaştıralım?' 18 15 900 27 13
$request=TextBox $requestTab 20 47 900 78 $true
$null=Label $requestTab 'Bildiğin kısıtları gir. Boş alan bilinmiyor olarak kalır; metindeki diğer koşullar da göreve eklenir.' 20 135 900 27 9
$specs=@(
    @('target_speed_kmh','Hedef hız (km/sa)'),@('endurance_min','Uçuş süresi (dakika)'),
    @('payload_kg','Faydalı yük (kg)'),@('altitude_m','İrtifa (m)'),
    @('max_span_m','En fazla açıklık (m)'),@('max_mass_kg','En fazla toplam kütle (kg)'),
    @('max_stall_kmh','En fazla stall hızı (km/sa)'),@('budget_try','En fazla bütçe (TL)'))
$script:fields=@{}
for($i=0;$i -lt $specs.Count;$i++){
    $x=20+($i%4)*226; $y=174+[math]::Floor($i/4)*69
    $null=Label $requestTab $specs[$i][1] $x $y 218 24 9
    $script:fields[$specs[$i][0]]=TextBox $requestTab $x ($y+25) 204 28
}
$null=Label $requestTab 'Aday tarama sınırı' 20 317 176 25 9
$candidateLimit=New-Object System.Windows.Forms.NumericUpDown
$candidateLimit.SetBounds(196,315,65,28); $candidateLimit.Minimum=1; $candidateLimit.Maximum=30; $candidateLimit.Value=6; $requestTab.Controls.Add($candidateLimit)
$null=Label $requestTab 'CFD yapılacak en fazla aday' 292 317 225 25 9
$cfdLimit=New-Object System.Windows.Forms.NumericUpDown
$cfdLimit.SetBounds(523,315,65,28); $cfdLimit.Minimum=1; $cfdLimit.Maximum=30; $cfdLimit.Value=3; $requestTab.Controls.Add($cfdLimit)
$null=Label $requestTab 'Hedef: adayları gerekçeleriyle elemek; taranmayan olasılıklar ve açık kontroller raporda görünür.' 20 358 900 40 9
function SubmitTask($saveOnly) {
    if([string]::IsNullOrWhiteSpace($request.Text)){
        [System.Windows.Forms.MessageBox]::Show('Önce görevini yaz.','Görev gerekli')|Out-Null; return
    }
    if($cfdLimit.Value -gt $candidateLimit.Value){[System.Windows.Forms.MessageBox]::Show('CFD aday sayısı toplam aday sayısından fazla olamaz.')|Out-Null; return}
    $constraints=@{}; foreach($key in $script:fields.Keys){$constraints[$key]=$script:fields[$key].Text}
    $payload=@{request=$request.Text;constraints=$constraints;options=@{candidate_limit=[int]$candidateLimit.Value;cfd_candidate_limit=[int]$cfdLimit.Value}}
    $folder=Join-Path $taskRoot 'work/agent/inbox'; [System.IO.Directory]::CreateDirectory($folder)|Out-Null
    $p=Join-Path $folder ([guid]::NewGuid().ToString()+'.json')
    [System.IO.File]::WriteAllText($p,($payload|ConvertTo-Json -Depth 8),(New-Object System.Text.UTF8Encoding($false)))
    $arguments=@('-X','utf8',('"'+$taskRunner+'"'),'submit',('"'+$p+'"'))
    if($saveOnly){$arguments+='--save-only'}
    StartJob $arguments $(if($saveOnly){'Görev kaydı'}else{'Görev kaydı ve ajan başlatma'})
}
$go=Button $requestTab 'Görevi kaydet ve ajanla başla' 20 418 332 {SubmitTask $false} $true
$go.BackColor=[System.Drawing.Color]::FromArgb(10,112,117); $go.ForeColor=[System.Drawing.Color]::White
$null=Button $requestTab 'Yalnız kaydet' 371 418 180 {SubmitTask $true} $true
$null=Button $requestTab 'Kullanım kılavuzu' 574 418 200 {OpenOutput 'Baslangic.md'}
$null=Label $analysisTab 'Kayıtlı yeterlilik örnekleri' 18 17 900 28 14
$null=Label $analysisTab 'Bu düğmeler araç sınamalarını çalıştırır. Kendi tasarımın için ilk sekmeden görev ver.' 20 52 900 43 10
$null=Button $analysisTab 'Parametrik kanat CAD' 20 106 272 {StartSuite 'geometry' 'Parametrik CAD'} $true
$null=Button $analysisTab 'Kanat analizi (VLM)' 322 106 272 {StartSuite 'complex-vlm' 'Native VSPAERO'} $true
$null=Button $analysisTab 'SU2: viskoz CFD' 624 106 272 {StartSuite 'cfd' 'SU2 CFD (~10 dk)'} $true
$null=Button $analysisTab 'Elmer: Navier–Stokes' 20 165 272 {StartSuite 'elmer-cfd' 'Elmer CFD doğrulaması'} $true
$null=Button $analysisTab 'Yapısal analiz (FEM)' 322 165 272 {StartSuite 'fem' 'FreeCAD/CalculiX'} $true
$null=Button $analysisTab 'Koşullu karşılaştırmayı yenile' 624 165 272 {StartSuite 'comparison' 'Kanıtlı eleme/sıralama'} $true
$null=Label $analysisTab 'Programları ve son dosyaları aç' 18 238 900 30 14
$null=Button $analysisTab 'CFD basınç alanı (Gmsh)' 20 284 272 {
    $meta=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8|ConvertFrom-Json
    $report=Get-Content (Join-Path $taskOut 'reports/cfd_reference_comparison.json') -Raw -Encoding UTF8|ConvertFrom-Json
    Start-Process -FilePath $meta.executables.'gmsh.exe' -ArgumentList ('"'+$report.gmsh_pressure_view+'"')
}
$null=Button $analysisTab 'OpenVSP: kanadı aç' 322 284 272 {
    $meta=Get-Content (Join-Path $taskRoot 'work/setup/openvsp_install.json') -Raw -Encoding UTF8|ConvertFrom-Json
    Start-Process -FilePath $meta.executables.'vsp.exe' -ArgumentList ('"'+(Join-Path $taskOut 'cad/complex_native_wing.vsp3')+'"')
}
$null=Button $analysisTab 'FreeCAD: parçaları aç' 624 284 272 {
    $meta=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8|ConvertFrom-Json
    $env:FREECAD_USER_HOME=Join-Path $taskRoot 'work/freecad/home'; $env:FREECAD_USER_DATA=Join-Path $taskRoot 'work/freecad/data'; $env:FREECAD_USER_TEMP=Join-Path $taskRoot 'work/freecad/temp'
    Start-Process -FilePath $meta.executables.'FreeCAD.exe' -ArgumentList ('"'+(Join-Path $taskOut 'cad/parametric_wing/review_envelope_and_ribs.step')+'"')
}
$null=Button $analysisTab 'ElmerGUI uygulamasını aç' 20 343 272 {
    $p=Join-Path $taskRoot 'work/setup/elmer_install.json'
    if(!(Test-Path $p)){[System.Windows.Forms.MessageBox]::Show('Elmer kurulumu henüz tamamlanmadı.')|Out-Null;return}
    $meta=Get-Content $p -Raw -Encoding UTF8|ConvertFrom-Json
    $prefix=Split-Path (Split-Path $meta.executables.'ElmerSolver.exe')
    $env:ELMER_HOME=$prefix; $env:ELMERGUI_HOME=Join-Path $prefix 'share/ElmerGUI'; $env:ELMER_LIB=Join-Path $prefix 'share/elmersolver/lib'
    $taskOldPath=$env:PATH
    try{$env:PATH=(Join-Path $prefix 'bin')+';'+(Join-Path $prefix 'lib')+';'+$taskOldPath;Start-Process -FilePath $meta.executables.'ElmerGUI.exe' -WorkingDirectory $taskRoot}
    finally{$env:PATH=$taskOldPath}
}
$null=Button $analysisTab 'Ham çıktılar' 322 343 272 {Start-Process -FilePath explorer.exe -ArgumentList ('"'+(Join-Path $taskOut 'simulations')+'"')}
$null=Button $analysisTab 'Elmer basınç alanı (Gmsh)' 624 343 272 {
    $meta=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8|ConvertFrom-Json
    $report=Get-Content (Join-Path $taskOut 'reports/elmer_cfd_qualification.json') -Raw -Encoding UTF8|ConvertFrom-Json
    Start-Process -FilePath $meta.executables.'gmsh.exe' -ArgumentList ('"'+$report.field_view.gmsh_pressure+'"')
}
$null=Label $analysisTab 'Kurulumlar proje içindedir. Araçların dosya/komut girişleri korunur; ajan bu arayüzü kullanmak zorunda değildir.' 20 417 900 60 10
$null=Label $resultsTab 'Kabul durumu ve karşılaştırma' 18 18 900 28 14
$null=Label $resultsTab 'CFD veya geometri kontrolü eksik adaya nihai kazanan etiketi verilmez. Ön sıralama koşullu gösterilir.' 20 56 900 48 10
$null=Button $resultsTab 'Güncel iş akışı raporu' 20 119 425 {OpenOutput 'reports/hafif_cfd_ve_is_akisi.html'}
$null=Button $resultsTab 'Projenin bütün durumu' 475 119 425 {OpenOutput 'Proje-Ozeti.html'}
$null=Button $resultsTab 'CAD / VLM / SU2 ayrıntıları' 20 181 425 {OpenOutput 'reports/muhendislik_seviyesi_ve_cfd.html'}
$null=Button $resultsTab 'Aday karşılaştırma tablosu' 475 181 425 {OpenOutput 'reports/candidate_comparison.html'}
$null=Button $resultsTab 'Görev kayıtları' 20 243 425 {Start-Process -FilePath explorer.exe -ArgumentList ('"'+(Join-Path $taskOut 'data/tasks')+'"')}
$null=Button $resultsTab 'Gerçek İHA girdileri' 475 243 425 {Start-Process -FilePath explorer.exe -ArgumentList ('"'+(Join-Path $taskOut 'data/project')+'"')}
$null=Label $resultsTab 'Mevcut sınır' 20 328 900 25 13
$null=Label $resultsTab 'Araçlar çalışıyor. Keyfi uçak geometrisinde otomatik ve doğrulanmış CFD, tam CAD eşdeğerliği ve bütün uçak uygunluğu henüz tamamlanmadı. Gerçek proje verisi olmadan uçak seçilmez.' 20 368 900 95 11
$activity=TextBox $form 25 662 950 62 $true
$activity.ReadOnly=$true
$activity.Text='Hazır. Kısıtlarını gir veya bu sohbette görev ver. Bilinmeyenler açık kalır; sonuçlar raporda kanıtlarıyla yer alır.'
$null=Label $form 'ANSYS sonraki aşamada. Hesap süresi, program adından çok ağ ve akış fiziğine bağlıdır.' 25 738 950 25 9
$timer=New-Object System.Windows.Forms.Timer; $timer.Interval=1000
$timer.Add_Tick({
    if($script:job -and $script:job.HasExited){
        $code=$script:job.ExitCode
        $activity.Text=$script:label+': '+$(if($code -eq 0){'çalışma tamamlandı. Kabul durumunu ilgili rapordan incele.'}else{'tamamlanamadı. Girdi veya araç hatasını kontrol et.'})
        if($code -ne 0 -and (Test-Path $script:err)){$activity.AppendText("`r`n"+([System.IO.File]::ReadAllText($script:err)))}
        $script:job=$null; foreach($button in $script:buttons){$button.Enabled=$true}
    }
})
if($SelfTest){
    $form.StartPosition='Manual';$form.Location=New-Object System.Drawing.Point(-30000,-30000);$form.ShowInTaskbar=$false;$form.Show()
    for($i=0;$i -lt $tabs.TabPages.Count;$i++){
        $tabs.SelectedIndex=$i;[System.Windows.Forms.Application]::DoEvents()
        $bitmap=New-Object System.Drawing.Bitmap($form.Width,$form.Height)
        $form.DrawToBitmap($bitmap,(New-Object System.Drawing.Rectangle(0,0,$form.Width,$form.Height)))
        $bitmap.Save((Join-Path $taskOut ('plots/engineering_desk_tab'+($i+1)+'.png')))
        $bitmap.Dispose()
    }
    $form.Dispose();Write-Output 'ENGINEERING_DESK_RENDER_OK'
}else{$timer.Start();[System.Windows.Forms.Application]::Run($form);$timer.Dispose()}

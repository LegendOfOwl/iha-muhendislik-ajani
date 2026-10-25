param([switch]$SelfTest,[string]$InitialProject='iha')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskPython=Join-Path $taskRoot '.venv/Scripts/python.exe'
$taskRunner=Join-Path $PSScriptRoot 'project.py'
$taskProjects=Join-Path $PSScriptRoot 'projects.py'
$script:selected=$null;$script:loading=$true;$script:job=$null;$script:summary=$null
$script:projectItems=@();$script:actionButtons=New-Object System.Collections.Generic.List[System.Windows.Forms.Button]
function QuoteArg([string]$s){return '"'+[regex]::Replace([regex]::Replace($s,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}
function Backend($arguments){
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$taskPython;$info.Arguments=(@('-X','utf8',$taskProjects)+$arguments|ForEach-Object{QuoteArg $_}) -join ' '
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WorkingDirectory=$taskRoot
    $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    $info.StandardOutputEncoding=New-Object Text.UTF8Encoding($false)
    $p=[Diagnostics.Process]::Start($info);$text=$p.StandardOutput.ReadToEnd();$err=$p.StandardError.ReadToEnd();$p.WaitForExit()
    if($p.ExitCode -ne 0){try{$message=($text|ConvertFrom-Json).error}catch{$message=$err};throw $message}
    return ($text|ConvertFrom-Json)
}
function Label($parent,$text,$x,$y,$w,$h,$size=10){
    $c=New-Object Windows.Forms.Label;$c.Text=$text;$c.SetBounds($x,$y,$w,$h);$c.Font=New-Object Drawing.Font('Segoe UI',$size);$parent.Controls.Add($c);return $c
}
function TextBox($parent,$x,$y,$w,$h,$multi=$false){
    $c=New-Object Windows.Forms.TextBox;$c.SetBounds($x,$y,$w,$h);$c.Multiline=$multi
    if($multi){$c.ScrollBars='Vertical';$c.AcceptsReturn=$true};$parent.Controls.Add($c);return $c
}
function Button($parent,$text,$x,$y,$w,$handler){
    $c=New-Object Windows.Forms.Button;$c.Text=$text;$c.SetBounds($x,$y,$w,40);$c.FlatStyle='Flat';$c.BackColor=[Drawing.Color]::White
    $c.Add_Click({try{& $this.Tag}catch{[Windows.Forms.MessageBox]::Show($_.Exception.Message,'İşlem tamamlanamadı')|Out-Null}})
    $c.Tag=$handler;$parent.Controls.Add($c);return $c
}
$form=New-Object Windows.Forms.Form;$form.Text='Mühendislik Merkezi — Projeler';$form.ClientSize=New-Object Drawing.Size(1180,810)
$form.StartPosition='CenterScreen';$form.MinimumSize=New-Object Drawing.Size(1120,790);$form.Font=New-Object Drawing.Font('Segoe UI',10)
$form.BackColor=[Drawing.Color]::FromArgb(242,246,249)
$header=New-Object Windows.Forms.Panel;$header.Dock='Top';$header.Height=74;$header.BackColor=[Drawing.Color]::FromArgb(18,42,61);$form.Controls.Add($header)
$title=Label $header 'MÜHENDİSLİK MERKEZİ' 22 12 800 32 19;$title.ForeColor=[Drawing.Color]::White
$subtitle=Label $header 'Projeyi seç · görev, CAD, analiz ve raporlarını aynı yerde tut' 24 46 950 24 10;$subtitle.ForeColor=[Drawing.Color]::White
$status=New-Object Windows.Forms.Label;$status.Dock='Bottom';$status.Height=42;$status.Padding=New-Object Windows.Forms.Padding(16,10,8,6)
$status.Text='Hazır. Arayüz ve ajan aynı proje dosyalarını kullanır.';$form.Controls.Add($status)
$split=New-Object Windows.Forms.SplitContainer;$split.Size=New-Object Drawing.Size(1180,690);$split.Dock='Fill';$split.SplitterDistance=250;$split.FixedPanel='Panel1';$split.BackColor=[Drawing.Color]::FromArgb(230,238,244);$form.Controls.Add($split);$split.BringToFront()
$leftTitle=New-Object Windows.Forms.Label;$leftTitle.Text='PROJELER';$leftTitle.Dock='Top';$leftTitle.Height=42;$leftTitle.Padding=New-Object Windows.Forms.Padding(14,14,0,0);$split.Panel1.Controls.Add($leftTitle)
$projectList=New-Object Windows.Forms.ListBox;$projectList.Dock='Fill';$projectList.BorderStyle='None';$projectList.Font=New-Object Drawing.Font('Segoe UI',11)
$projectList.ItemHeight=48;$projectList.DrawMode='OwnerDrawFixed';$projectList.DisplayMember='name';$split.Panel1.Controls.Add($projectList);$projectList.BringToFront()
$projectList.Add_DrawItem({param($sender,$e)
    if($e.Index -lt 0){return};$item=$sender.Items[$e.Index];$e.DrawBackground()
    $brush=New-Object Drawing.SolidBrush($e.ForeColor)
    $e.Graphics.DrawString($item.name,$sender.Font,$brush,$e.Bounds.X+10,$e.Bounds.Y+5)
    $small=New-Object Drawing.Font('Segoe UI',8);$kind=if($item.kind -eq 'qualification'){'Doğrulama / örnek'}else{'Mühendislik projesi'}
    $e.Graphics.DrawString($kind,$small,$brush,$e.Bounds.X+11,$e.Bounds.Y+27);$small.Dispose();$brush.Dispose();$e.DrawFocusRectangle()
})
$leftBottom=New-Object Windows.Forms.Panel;$leftBottom.Dock='Bottom';$leftBottom.Height=100;$split.Panel1.Controls.Add($leftBottom);$leftBottom.BringToFront()
$null=Button $leftBottom '+ Yeni proje' 12 8 216 {NewProject}
$null=Button $leftBottom 'Projeleri yenile' 12 54 216 {LoadProjects $script:selected}
$projectList.BringToFront()
$body=New-Object Windows.Forms.Panel;$body.Dock='Fill';$body.Padding=New-Object Windows.Forms.Padding(14,0,12,0);$split.Panel2.Controls.Add($body)
$projectHeader=New-Object Windows.Forms.Label;$projectHeader.Dock='Top';$projectHeader.Height=58;$projectHeader.Font=New-Object Drawing.Font('Segoe UI',18);$projectHeader.Padding=New-Object Windows.Forms.Padding(8,12,0,0);$body.Controls.Add($projectHeader)
$tabs=New-Object Windows.Forms.TabControl;$tabs.Dock='Fill';$body.Controls.Add($tabs);$tabs.BringToFront()
$overview=New-Object Windows.Forms.TabPage;$overview.Text='Proje özeti';$tabs.TabPages.Add($overview)
$taskTab=New-Object Windows.Forms.TabPage;$taskTab.Text='Görev ve kısıtlar';$tabs.TabPages.Add($taskTab)
$filesTab=New-Object Windows.Forms.TabPage;$filesTab.Text='Proje dosyaları';$tabs.TabPages.Add($filesTab)
$runsTab=New-Object Windows.Forms.TabPage;$runsTab.Text='Görevler ve çalışmalar';$tabs.TabPages.Add($runsTab)
$scope=Label $overview '' 22 20 810 48 11
$counts=Label $overview '' 22 86 810 45 16
$cadLabel=Label $overview '' 22 150 810 45 11
$null=Label $overview 'CAD programı' 22 204 130 26 10
$cadTool=New-Object Windows.Forms.ComboBox;$cadTool.DropDownStyle='DropDownList';$cadTool.SetBounds(154,200,230,30);$cadTool.DisplayMember='label';$overview.Controls.Add($cadTool)
foreach($c in @([pscustomobject]@{id='auto';label='Dosya türüne göre seç'},[pscustomobject]@{id='freecad';label='FreeCAD'},[pscustomobject]@{id='openvsp';label='OpenVSP'})){$null=$cadTool.Items.Add($c)}
$null=Button $overview 'CAD programını aç' 410 195 332 {OpenCadProgram}
$null=Button $overview 'Projenin CAD dosyalarını seç' 22 237 350 {$filter.SelectedItem='CAD';$tabs.SelectedTab=$filesTab;RefreshFiles}
$null=Button $overview 'Bu projeye görev ver' 392 237 350 {$tabs.SelectedTab=$taskTab}
$null=Button $overview 'Raporları incele' 22 294 350 {$filter.SelectedItem='Rapor';$tabs.SelectedTab=$filesTab;RefreshFiles}
$null=Button $overview 'Proje klasörünü aç' 392 294 350 {OpenFolder}
$notice=Label $overview '' 22 374 810 122 11
$null=Label $overview 'İçe aktarılan bir CAD dosyasının analiz edilebilmesi için uygun fizik ve ağ tanımı ayrıca hazırlanır.' 22 535 810 55 9
$request=TextBox $taskTab 18 44 805 80 $true
$null=Label $taskTab 'Bu projede ne yapalım?' 18 13 800 25 12
$null=Label $taskTab 'Bildiğin kısıtları gir. Boş alanlar bilinmiyor kalır; taslak proje değiştirince korunur.' 18 134 800 28 9
$specs=@(@('target_speed_kmh','Hedef hız (km/sa)'),@('endurance_min','Uçuş süresi (dk)'),@('payload_kg','Faydalı yük (kg)'),@('altitude_m','İrtifa (m)'),@('max_span_m','En fazla açıklık (m)'),@('max_mass_kg','En fazla kütle (kg)'),@('max_stall_kmh','En fazla stall (km/sa)'),@('budget_try','En fazla bütçe (TL)'))
$script:fields=@{}
for($i=0;$i -lt $specs.Count;$i++){$x=18+($i%4)*204;$y=176+[math]::Floor($i/4)*68;$null=Label $taskTab $specs[$i][1] $x $y 199 24 9;$script:fields[$specs[$i][0]]=TextBox $taskTab $x ($y+24) 188 28}
$null=Label $taskTab 'Aday sınırı' 18 325 100 25 9
$candidateLimit=New-Object Windows.Forms.NumericUpDown;$candidateLimit.SetBounds(124,322,64,28);$candidateLimit.Minimum=1;$candidateLimit.Maximum=30;$candidateLimit.Value=6;$taskTab.Controls.Add($candidateLimit)
$null=Label $taskTab 'CFD aday sınırı' 240 325 130 25 9
$cfdLimit=New-Object Windows.Forms.NumericUpDown;$cfdLimit.SetBounds(380,322,64,28);$cfdLimit.Minimum=1;$cfdLimit.Maximum=30;$cfdLimit.Value=3;$taskTab.Controls.Add($cfdLimit)
$null=Label $taskTab '“Ajanla başlat” bu proje bilgileriyle ayrı bir Codex penceresi açar. Bu sohbetten devam için yalnız kaydet.' 18 379 810 58 10
$null=Button $taskTab 'Yalnız bu projeye kaydet' 18 458 315 {SubmitTask $true}
$go=Button $taskTab 'Kaydet ve ajanla başlat' 353 458 315 {SubmitTask $false};$go.BackColor=[Drawing.Color]::FromArgb(10,112,117);$go.ForeColor=[Drawing.Color]::White
$filter=New-Object Windows.Forms.ComboBox;$filter.DropDownStyle='DropDownList';$filter.SetBounds(18,18,210,30);$filter.Items.AddRange(@('Tümü','CAD','Rapor','Alan / analiz','Görsel','Girdi'));$filter.SelectedIndex=0;$filesTab.Controls.Add($filter)
$null=Button $filesTab 'Dosyaları yenile' 248 14 180 {RefreshSummary}
$fileList=New-Object Windows.Forms.ListView;$fileList.View='Details';$fileList.FullRowSelect=$true;$fileList.MultiSelect=$false;$fileList.SetBounds(18,70,810,410)
foreach($col in @(@('Tür',105),@('Dosya',330),@('Konum',280),@('Boyut',85))){$null=$fileList.Columns.Add($col[0],[int]$col[1])};$filesTab.Controls.Add($fileList)
$fileOpen=Button $filesTab 'Seçili dosyayı aç' 18 500 220 {OpenSelected}
$fileActive=Button $filesTab 'Aktif CAD olarak seç' 258 500 240 {SetActive}
$fileImport=Button $filesTab 'CAD / girdi dosyası ekle' 518 500 280 {ImportFile}
$fileHint=Label $filesTab 'Dosyalar yalnız seçili projeye aittir. CAD, bağlı programında; basınç .pos dosyası Gmsh ile açılır.' 18 557 810 55 9
$taskList=New-Object Windows.Forms.ListView;$taskList.View='Details';$taskList.FullRowSelect=$true;$taskList.MultiSelect=$false;$taskList.SetBounds(18,48,810,255)
$null=$taskList.Columns.Add('Durum',110);$null=$taskList.Columns.Add('Görev',490);$null=$taskList.Columns.Add('Kayıt',190);$runsTab.Controls.Add($taskList)
$null=Label $runsTab 'Bu projenin görevleri' 18 15 810 27 12
$null=Button $runsTab 'Görev kaydını aç' 18 320 220 {if($taskList.SelectedItems.Count){OpenTask $false}}
$null=Button $runsTab 'Seçili görevi ajanla aç' 258 320 260 {if($taskList.SelectedItems.Count){OpenTask $true}}
$null=Label $runsTab 'Hazırlanmış proje tanımını çalıştır' 18 388 810 30 12
$suite=New-Object Windows.Forms.ComboBox;$suite.DropDownStyle='DropDownList';$suite.SetBounds(18,430,520,30);$suite.DisplayMember='label';$runsTab.Controls.Add($suite)
$runButton=Button $runsTab 'Çalıştır' 560 422 240 {RunSelected}
$runReason=Label $runsTab '' 18 483 810 100 10
$script:suiteChoices=@(
    [pscustomobject]@{id='geometry';label='Kanat tanımından CAD üret'},[pscustomobject]@{id='complex-vlm';label='Kanat tanımından ön analiz (VSPAERO)'},
    [pscustomobject]@{id='profile-cfd';label='Hazırlanmış profil için ağ ve CFD'},[pscustomobject]@{id='cfd';label='SU2 RANS yeterlilik örneği'},
    [pscustomobject]@{id='elmer-cfd';label='Elmer Navier–Stokes yeterlilik örneği'},[pscustomobject]@{id='fem';label='Yapısal yeterlilik örneği'},[pscustomobject]@{id='aerostruct';label='OpenAeroStruct aeroelastik optimizasyon örneği'},[pscustomobject]@{id='comparison';label='Koşullu karşılaştırma örneği'},[pscustomobject]@{id='reliability';label='Kayıtlı sonuçların güvenilirliğini yeniden denetle'})
foreach($s in $script:suiteChoices){$null=$suite.Items.Add($s)};$suite.SelectedIndex=0
function Payload{
    $c=@{};foreach($key in $script:fields.Keys){$c[$key]=$script:fields[$key].Text}
    return @{project_id=$script:selected;request=$request.Text;constraints=$c;options=@{candidate_limit=[int]$candidateLimit.Value;cfd_candidate_limit=[int]$cfdLimit.Value}}
}
function TempPayload($data){
    $folder=Join-Path $taskRoot 'work/agent/inbox';[IO.Directory]::CreateDirectory($folder)|Out-Null;$p=Join-Path $folder ([guid]::NewGuid().ToString()+'.json')
    [IO.File]::WriteAllText($p,($data|ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)));return $p
}
function SaveDraft{if(!$SelfTest -and !$script:loading -and $script:selected){$p=TempPayload (Payload);$null=Backend @('draft-save',$script:selected,$p)}}
function LoadDraft{
    $d=Backend @('draft',$script:selected);$request.Text=[string]$d.request
    foreach($key in $script:fields.Keys){$script:fields[$key].Text=[string]$d.constraints.$key}
    $candidateLimit.Value=if($d.options.candidate_limit){[int]$d.options.candidate_limit}else{6}
    $cfdLimit.Value=if($d.options.cfd_candidate_limit){[int]$d.options.cfd_candidate_limit}else{3}
}
function LoadProjects($select){
    SaveDraft;$script:loading=$true;$items=@(Backend @('list'));$projectList.Items.Clear()
    foreach($p in $items){$null=$projectList.Items.Add($p)}
    $index=0;for($i=0;$i -lt $projectList.Items.Count;$i++){if($projectList.Items[$i].id -eq $select){$index=$i}}
    $projectList.SelectedIndex=$index;$script:loading=$false;SelectProject
}
function SelectProject{
    if($script:loading -or !$projectList.SelectedItem){return};SaveDraft;$script:selected=$projectList.SelectedItem.id
    $script:loading=$true;LoadDraft;$script:loading=$false;RefreshSummary
}
function RefreshSummary{
    if(!$script:selected){return};$script:summary=Backend @('summary',$script:selected)
    $p=$script:summary.project;$projectHeader.Text=$p.name;$scope.Text=$script:summary.scope_note
    $cad=@($script:summary.files|Where-Object{$_.group -eq 'CAD'}).Count;$reports=@($script:summary.files|Where-Object{$_.group -eq 'Rapor'}).Count
    $counts.Text=[string]$cad+' CAD dosyası   ·   '+$script:summary.tasks.Count+' görev   ·   '+$reports+' rapor dosyası'
    $cadLabel.Text=if($p.active_cad){'Aktif CAD: '+[IO.Path]::GetFileName($p.active_cad.path)}else{'Aktif CAD seçilmedi. Proje dosyalarından bir model seçebilir veya CAD dosyası ekleyebilirsin.'}
    $script:settingCadTool=$true;$tool=if($p.cad_tool){$p.cad_tool}else{'auto'}
    for($i=0;$i -lt $cadTool.Items.Count;$i++){if($cadTool.Items[$i].id -eq $tool){$cadTool.SelectedIndex=$i}};$script:settingCadTool=$false
    $notice.Text=if($script:summary.active_cad_changed){'Aktif CAD dosyası değişti. Önceki analizlerle geometri eşleştirmesi yeniden kontrol edilmeli.'}elseif($p.kind -eq 'qualification'){'Buradaki hazır çalışmalar araç doğrulama örnekleridir. Bunlar gerçek İHA tasarımına aktarılmış kabul edilmez.'}else{'Görevler ve sonuçlar bu projeye bağlı tutulur. Yeni geometri için uygun CAD/analiz tanımı ve CFD ağı hazırlanması gerekebilir.'}
    RefreshFiles;$taskList.Items.Clear()
    foreach($t in $script:summary.tasks){$row=New-Object Windows.Forms.ListViewItem([string]$t.status);$null=$row.SubItems.Add([string]$t.request);$null=$row.SubItems.Add([string]$t.id);$row.Tag=$t;$null=$taskList.Items.Add($row)}
    UpdateAction
}
function RefreshFiles{
    if(!$script:summary){return};$fileList.BeginUpdate();$fileList.Items.Clear()
    foreach($f in $script:summary.files){if($filter.SelectedItem -ne 'Tümü' -and $f.group -ne $filter.SelectedItem){continue}
        $row=New-Object Windows.Forms.ListViewItem([string]$f.group);$null=$row.SubItems.Add([string]$f.name);$null=$row.SubItems.Add([string]$f.path);$null=$row.SubItems.Add(('{0:N0} KB' -f ($f.bytes/1024)));$row.Tag=$f;$null=$fileList.Items.Add($row)}
    $fileList.EndUpdate()
}
function UpdateAction{
    if(!$script:summary -or !$suite.SelectedItem){return};$id=$suite.SelectedItem.id;$a=$script:summary.actions.$id
    $runButton.Enabled=(!$script:job -and [bool]$a.ready);$runReason.Text=if($a.ready){$a.note}else{$a.reason}
}
function NewProject{
    $dialog=New-Object Windows.Forms.Form;$dialog.Text='Yeni mühendislik projesi';$dialog.ClientSize=New-Object Drawing.Size(440,154);$dialog.StartPosition='CenterParent';$dialog.FormBorderStyle='FixedDialog';$dialog.MaximizeBox=$false;$dialog.MinimizeBox=$false
    $null=Label $dialog 'Proje adı' 15 15 400 24;$name=TextBox $dialog 15 44 406 28
    $ok=Button $dialog 'Oluştur' 232 93 188 {$this.FindForm().DialogResult=[Windows.Forms.DialogResult]::OK};$dialog.AcceptButton=$ok
    if($dialog.ShowDialog($form) -eq 'OK'){$p=Backend @('new',$name.Text);LoadProjects $p.id;$tabs.SelectedTab=$taskTab};$dialog.Dispose()
}
function StartWorker($arguments,$label){
    if($script:job){return};$logs=Join-Path $taskRoot 'work/agent/ui-logs';[IO.Directory]::CreateDirectory($logs)|Out-Null
    $script:log=Join-Path $logs ([guid]::NewGuid().ToString()+'.txt');$script:err=$script:log+'.err';$script:jobProject=$script:selected;$script:jobLabel=$label
    $text=($arguments|ForEach-Object{QuoteArg $_}) -join ' '
    $script:job=Start-Process -FilePath $taskPython -ArgumentList $text -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $script:log -RedirectStandardError $script:err
    $status.Text=$script:summary.project.name+': '+$label+' çalışıyor.';UpdateAction
}
function SubmitTask($saveOnly){
    if($script:job){return};SaveDraft;$p=TempPayload (Payload);$argsList=@('-X','utf8',$taskRunner,'submit',$p)
    if($saveOnly){$argsList+='--save-only'};StartWorker $argsList $(if($saveOnly){'Görev kaydı'}else{'Görev ve ayrı Codex penceresi'})
}
function OpenTask($agent){
    $t=$taskList.SelectedItems[0].Tag;$p=Join-Path $taskRoot $t.path
    if($agent){StartWorker @('-X','utf8',$taskRunner,'agent',$p) 'Seçili görev için ajan başlatma'}else{Start-Process notepad.exe -ArgumentList (QuoteArg $p)}
}
function RunSelected{if($suite.SelectedItem){StartWorker @('-X','utf8',$taskRunner,'run',$suite.SelectedItem.id,'--project',$script:selected) $suite.SelectedItem.label}}
function OpenFolder{Start-Process explorer.exe -ArgumentList (QuoteArg (Join-Path $taskRoot $script:summary.project.artifact_root))}
function SetActive{if(!$fileList.SelectedItems.Count){return};$f=$fileList.SelectedItems[0].Tag;$null=Backend @('active-cad',$script:selected,$f.path);RefreshSummary}
function OpenCadProgram{
    $active=$script:summary.project.active_cad;$tool=$cadTool.SelectedItem.id;$model=$null
    if($active){$model=(Backend @('check-file',$script:selected,$active.path)).full_path}
    if($tool -eq 'auto'){$tool=if($model -and [IO.Path]::GetExtension($model).ToLowerInvariant() -eq '.vsp3'){'openvsp'}else{'freecad'}}
    if($tool -eq 'openvsp'){$meta=Get-Content (Join-Path $taskRoot 'work/setup/openvsp_install.json') -Raw -Encoding UTF8|ConvertFrom-Json;$exe=$meta.executables.'vsp.exe';if($model -and [IO.Path]::GetExtension($model).ToLowerInvariant() -ne '.vsp3'){$model=$null}}
    else{
        $meta=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8|ConvertFrom-Json;$exe=$meta.executables.'FreeCAD.exe'
        $env:FREECAD_USER_HOME=Join-Path $taskRoot 'work/freecad/home';$env:FREECAD_USER_DATA=Join-Path $taskRoot 'work/freecad/data';$env:FREECAD_USER_TEMP=Join-Path $taskRoot 'work/freecad/temp'
        if($model -and [IO.Path]::GetExtension($model).ToLowerInvariant() -eq '.vsp3'){$model=$null}
    }
    $options=@{FilePath=$exe;WorkingDirectory=(Join-Path $taskRoot $script:summary.project.artifact_root)}
    if($model){$options.ArgumentList=QuoteArg $model};Start-Process @options
    $status.Text=if($model){'Seçili projenin aktif modeli açılıyor.'}else{'CAD programı açılıyor. Kaydederken seçili projenin CAD klasörünü kullan.'}
}
function ImportFile{
    $d=New-Object Windows.Forms.OpenFileDialog;$d.Title='Seçili projeye CAD veya girdi dosyası ekle';$d.Filter='CAD ve girdiler|*.step;*.stp;*.FCStd;*.vsp3;*.stl;*.brep;*.iges;*.igs;*.dat;*.json'
    if($d.ShowDialog($form) -eq 'OK'){$null=Backend @('import',$script:selected,$d.FileName);RefreshSummary};$d.Dispose()
}
function OpenSelected{
    if(!$fileList.SelectedItems.Count){return};$f=$fileList.SelectedItems[0].Tag;$checked=Backend @('check-file',$script:selected,$f.path);$path=$checked.full_path;$ext=[IO.Path]::GetExtension($path).ToLowerInvariant()
    if($ext -eq '.vsp3'){$meta=Get-Content (Join-Path $taskRoot 'work/setup/openvsp_install.json') -Raw -Encoding UTF8|ConvertFrom-Json;$exe=$meta.executables.'vsp.exe'}
    elseif($ext -in @('.step','.stp','.fcstd','.stl','.brep','.iges','.igs')){
        $meta=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8|ConvertFrom-Json;$exe=$meta.executables.'FreeCAD.exe'
        $env:FREECAD_USER_HOME=Join-Path $taskRoot 'work/freecad/home';$env:FREECAD_USER_DATA=Join-Path $taskRoot 'work/freecad/data';$env:FREECAD_USER_TEMP=Join-Path $taskRoot 'work/freecad/temp'
    }elseif($ext -in @('.pos','.msh')){$meta=Get-Content (Join-Path $taskRoot 'work/setup/freecad_install.json') -Raw -Encoding UTF8|ConvertFrom-Json;$exe=$meta.executables.'gmsh.exe'}
    elseif($ext -in @('.json','.log','.cfg','.sif','.dat','.md')){$exe='notepad.exe'}
    elseif($ext -in @('.vtu','.su2')){Start-Process explorer.exe -ArgumentList ('/select,'+(QuoteArg $path));return}
    else{Start-Process -FilePath $path;return}
    Start-Process -FilePath $exe -ArgumentList (QuoteArg $path) -WorkingDirectory (Join-Path $taskRoot $script:summary.project.artifact_root)
}
$projectList.Add_SelectedIndexChanged({if(!$script:loading){try{SelectProject}catch{[Windows.Forms.MessageBox]::Show($_.Exception.Message)|Out-Null}}})
$filter.Add_SelectedIndexChanged({RefreshFiles});$suite.Add_SelectedIndexChanged({UpdateAction});$fileList.Add_DoubleClick({try{OpenSelected}catch{[Windows.Forms.MessageBox]::Show($_.Exception.Message)|Out-Null}})
$cadTool.Add_SelectedIndexChanged({if(!$script:settingCadTool -and $script:selected){try{$null=Backend @('cad-tool',$script:selected,$cadTool.SelectedItem.id)}catch{[Windows.Forms.MessageBox]::Show($_.Exception.Message)|Out-Null}}})
$timer=New-Object Windows.Forms.Timer;$timer.Interval=800
$timer.Add_Tick({if($script:job -and $script:job.HasExited){
    $code=$script:job.ExitCode;$status.Text=$script:jobLabel+$(if($code -eq 0){': çalışma tamamlandı; kabul durumu raporda.'}else{': tamamlanamadı; girdi veya araç kaydını incele.'})
    if($code -ne 0 -and (Test-Path $script:err)){$err=[IO.File]::ReadAllText($script:err);[Windows.Forms.MessageBox]::Show($err,'İşlem sonucu')|Out-Null}
    $script:job=$null;RefreshSummary
}})
$form.Add_FormClosing({try{SaveDraft}catch{}})
function LayoutBody{
    $w=[Math]::Max(600,$filesTab.ClientSize.Width-36);$h=[Math]::Max(300,$filesTab.ClientSize.Height-180)
    $fileList.SetBounds(18,70,$w,$h);$bw=[int](($w-24)/3);$y=82+$h
    $fileOpen.SetBounds(18,$y,$bw,40);$fileActive.SetBounds((30+$bw),$y,$bw,40);$fileImport.SetBounds((42+2*$bw),$y,$bw,40)
    $fileHint.SetBounds(18,($y+47),$w,48);$taskList.Width=$w
}
$form.Add_SizeChanged({LayoutBody});$tabs.Add_SizeChanged({LayoutBody})
LoadProjects $InitialProject
if($SelfTest){
    $form.StartPosition='Manual';$form.Location=New-Object Drawing.Point(-30000,-30000);$form.ShowInTaskbar=$false;$form.Show()
    foreach($id in @('iha','qualification')){
        for($i=0;$i -lt $projectList.Items.Count;$i++){if($projectList.Items[$i].id -eq $id){$projectList.SelectedIndex=$i}}
        foreach($index in @(0,1,2,3)){$tabs.SelectedIndex=$index;[Windows.Forms.Application]::DoEvents();$bmp=New-Object Drawing.Bitmap($form.Width,$form.Height);$form.DrawToBitmap($bmp,(New-Object Drawing.Rectangle(0,0,$form.Width,$form.Height)));$bmp.Save((Join-Path $taskRoot ('outputs/plots/projects_'+$id+'_'+$index+'.png')));$bmp.Dispose()}
        $tabs.SelectedTab=$overview
        ($overview.Controls|Where-Object{$_ -is [Windows.Forms.Button] -and $_.Text -eq 'Projenin CAD dosyalarını seç'}).PerformClick()
        if($tabs.SelectedTab -ne $filesTab -or $filter.SelectedItem -ne 'CAD'){throw 'CAD gezinme düğmesi çalışmadı'}
        $tabs.SelectedTab=$overview
        ($overview.Controls|Where-Object{$_ -is [Windows.Forms.Button] -and $_.Text -eq 'Bu projeye görev ver'}).PerformClick()
        if($tabs.SelectedTab -ne $taskTab){throw 'Görev gezinme düğmesi çalışmadı'}
    }
    $form.Dispose();Write-Output 'PROJECT_DESK_RENDER_OK'
}else{$timer.Start();[Windows.Forms.Application]::Run($form);$timer.Dispose()}

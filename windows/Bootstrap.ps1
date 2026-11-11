# Native Windows fallback for machines without Python. No commands are required from the user.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object System.Windows.Forms.Form
$form.Text = 'LIN4CRE SENTINEL Setup'
$form.Size = New-Object System.Drawing.Size(560, 360)
$form.StartPosition = 'CenterScreen'
$form.BackColor = [System.Drawing.Color]::FromArgb(13, 21, 17)
$form.ForeColor = [System.Drawing.Color]::FromArgb(220, 232, 222)
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$title = New-Object System.Windows.Forms.Label
$title.Text = 'SENTINEL needs one component before setup'
$title.Location = New-Object System.Drawing.Point(32, 28)
$title.Size = New-Object System.Drawing.Size(490, 35)
$title.Font = New-Object System.Drawing.Font('Segoe UI', 16)
$form.Controls.Add($title)
$text = New-Object System.Windows.Forms.Label
$text.Text = "Python is needed to inspect your computer and run the local setup assistant.`n`nNothing has been changed. If you continue, SENTINEL will ask Windows Package Manager to install Python from the official python.org package. The installer and Windows may show additional security prompts."
$text.Location = New-Object System.Drawing.Point(35, 85)
$text.Size = New-Object System.Drawing.Size(465, 135)
$form.Controls.Add($text)
$status = New-Object System.Windows.Forms.Label
$status.Location = New-Object System.Drawing.Point(35, 245)
$status.Size = New-Object System.Drawing.Size(465, 25)
$form.Controls.Add($status)
$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = 'Not now'
$cancel.Location = New-Object System.Drawing.Point(315, 285)
$cancel.Size = New-Object System.Drawing.Size(90, 34)
$cancel.Add_Click({ $form.Close() })
$form.Controls.Add($cancel)
$install = New-Object System.Windows.Forms.Button
$install.Text = 'Install Python & continue'
$install.Location = New-Object System.Drawing.Point(115, 285)
$install.Size = New-Object System.Drawing.Size(180, 34)
$install.BackColor = [System.Drawing.Color]::FromArgb(183, 239, 114)
$install.ForeColor = [System.Drawing.Color]::FromArgb(20, 31, 22)
$install.FlatStyle = 'Flat'
$install.Add_Click({
  $install.Enabled = $false
  $status.Text = 'Checking Windows Package Manager…'
  $form.Refresh()
  try {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Windows Package Manager was not found. Install App Installer from Microsoft, then open SENTINEL Setup again.' }
    $backup = Join-Path $env:LOCALAPPDATA 'LIN4CRE\SENTINEL\backups\pre-python-install'
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    Get-Date -Format o | Set-Content -Path (Join-Path $backup 'timestamp.txt')
    $status.Text = 'Python installation is running. Follow any Windows prompts…'
    $form.Refresh()
    $process = Start-Process winget -ArgumentList @('install','--exact','--id','Python.Python.3.12','--source','winget','--accept-package-agreements','--accept-source-agreements','--silent','--disable-interactivity') -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Python installer returned exit code $($process.ExitCode). No success is being assumed. Close this window and retry, or use the installation report for support." }
    $status.Text = 'Python installed. Close this window and open SENTINEL Setup again to verify it.'
    [System.Windows.Forms.MessageBox]::Show('Python installation completed. SENTINEL will verify it when you open Setup again.', 'SENTINEL Setup') | Out-Null
  } catch {
    $status.Text = 'Installation did not complete.'
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'SENTINEL Setup — verification failed') | Out-Null
    $install.Enabled = $true
  }
})
$form.Controls.Add($install)
[void]$form.ShowDialog()

#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$InstallRoot,
    [string]$Python,
    [string]$ReportPath,
    [switch]$VerifyOnly,
    [switch]$SkipRequirements,
    [switch]$SkipServices
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$apiPort = 8000
$hostPort = 8765
$deployDirectories = @('backend', 'host_companion', 'windows', 'scripts', 'docs', 'dist')
$deployFiles = @('requirements.txt', 'README.md', 'LICENSE', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md', 'SUPPORT.md', 'START-HERE.txt')
$excludedParts = @('__pycache__', 'node_modules', '.git', '.venv', 'data', 'host_data', 'logs')
$warnings = [System.Collections.Generic.List[string]]::new()

function Resolve-Interpreter {
    param([string]$Requested)
    if ($Requested) {
        if (-not (Test-Path -LiteralPath $Requested -PathType Leaf)) { throw "The requested interpreter does not exist: $Requested" }
        return (Resolve-Path -LiteralPath $Requested).Path
    }
    $candidates = @()
    $localPython = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path -LiteralPath $localPython -PathType Container) {
        Get-ChildItem -LiteralPath $localPython -Directory | Sort-Object -Property Name -Descending | ForEach-Object {
            $candidates += (Join-Path $_.FullName 'pythonw.exe')
        }
    }
    foreach ($base in @('C:\', $env:ProgramFiles)) {
        foreach ($version in @('Python313', 'Python312', 'Python311')) {
            $candidates += (Join-Path (Join-Path $base $version) 'pythonw.exe')
        }
    }
    foreach ($name in @('pythonw.exe', 'python.exe')) {
        $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command -and $command.Source -and ($command.Source -notlike '*\WindowsApps\*')) { $candidates += $command.Source }
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf) -and ($candidate -notlike '*\WindowsApps\*')) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw 'No usable Python interpreter was found. Install Python 3.12 or pass -Python explicitly.'
}

function Stop-ListeningProcess {
    param([int]$Port)
    $stopped = @()
    try { $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue } catch { $listeners = @() }
    foreach ($listener in @($listeners)) {
        $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            $stopped += [PSCustomObject]@{ Port = $Port; ProcessId = $process.Id; Name = $process.ProcessName }
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    return $stopped
}

function Test-ServiceReady {
    param([string]$Path, [int]$Port)
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port$Path" -TimeoutSec 3 -UseBasicParsing
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Start-LoggedService {
    param([string]$Executable, [string[]]$Arguments, [string]$WorkingDirectory, [string]$LogPath, [string]$Name)
    # The service is launched through a command file so its output is written to
    # the log directly. Redirecting a long-lived child from PowerShell would keep
    # this script alive until that child exits.
    $launcher = "$LogPath.$Name.cmd"
    $quoted = ($Arguments | ForEach-Object { "`"$_`"" }) -join ' '
    @(
        '@echo off'
        "cd /d `"$WorkingDirectory`""
        "`"$Executable`" $quoted >> `"$LogPath`" 2>&1"
    ) | Set-Content -LiteralPath $launcher -Encoding ascii
    Start-Process -FilePath $launcher -WorkingDirectory $WorkingDirectory -WindowStyle Hidden | Out-Null
    return $launcher
}

$resolvedSource = (Resolve-Path -LiteralPath $SourceRoot).Path
$required = @('backend\main.py', 'host_companion\server.py', 'windows\SentinelSetup.pyw', 'requirements.txt', 'dist\index.html')
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $resolvedSource $_) -PathType Leaf) })
if ($missing.Count -gt 0) {
    throw "The source root is not a built SENTINEL release. Missing: $($missing -join ', ')"
}

$resolvedInstall = $null
if (-not $VerifyOnly) {
    $resolvedInstall = (New-Item -ItemType Directory -Path $InstallRoot -Force).FullName
    $copied = 0
    $bytes = 0L
    foreach ($directory in $deployDirectories) {
        $source = Join-Path $resolvedSource $directory
        if (-not (Test-Path -LiteralPath $source -PathType Container)) { continue }
        foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse -Force) {
            $relative = $file.FullName.Substring($resolvedSource.Length).TrimStart('\')
            $skip = $false
            foreach ($name in $excludedParts) {
                if ($relative -like "$name\*" -or $relative -like "*\$name\*") { $skip = $true; break }
            }
            if ($skip -or $file.Extension -eq '.pyc') { continue }
            $target = Join-Path $resolvedInstall $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $target -Force
            $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
            $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash
            if ($sourceHash -ne $targetHash) { throw "Deployment hash mismatch: $relative" }
            $copied++
            $bytes += $file.Length
        }
    }
    foreach ($name in $deployFiles) {
        $source = Join-Path $resolvedSource $name
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { continue }
        $target = Join-Path $resolvedInstall $name
        Copy-Item -LiteralPath $source -Destination $target -Force
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash
        $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash
        if ($sourceHash -ne $targetHash) { throw "Deployment hash mismatch: $name" }
        $copied++
        $bytes += (Get-Item -LiteralPath $source).Length
    }
    Write-Host "Deployment copied and hash-verified: $resolvedInstall ($copied files, $bytes bytes)" -ForegroundColor Green
} else {
    $resolvedInstall = (Resolve-Path -LiteralPath $InstallRoot).Path
    Write-Host "Verification only. Not modifying $resolvedInstall" -ForegroundColor Cyan
}

$interpreter = Resolve-Interpreter -Requested $Python
$pythonExe = $interpreter -replace 'pythonw\.exe$', 'python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) { $pythonExe = $interpreter }

$requirementsInstalled = $false
if (-not $VerifyOnly -and -not $SkipRequirements) {
    $requirements = Join-Path $resolvedInstall 'requirements.txt'
    if (Test-Path -LiteralPath $requirements -PathType Leaf) {
        Write-Host 'Installing the declared local runtime packages…' -ForegroundColor Cyan
        $result = & $pythonExe -m pip install --disable-pip-version-check --no-input -r $requirements 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Requirement installation failed. Output: $(($result | Select-Object -Last 20) -join ' ')" }
        $requirementsInstalled = $true
    }
}

$configDirectory = Join-Path $env:LOCALAPPDATA 'LIN4CRE\SENTINEL'
New-Item -ItemType Directory -Path $configDirectory -Force | Out-Null
$tokenFile = Join-Path $configDirectory 'companion-token.txt'
$pairedFile = Join-Path $resolvedInstall 'host_data\host-token'
$token = $null
if (Test-Path -LiteralPath $pairedFile -PathType Leaf) { $token = (Get-Content -LiteralPath $pairedFile -Raw).Trim() }
if (-not $token -and (Test-Path -LiteralPath $tokenFile -PathType Leaf)) { $token = (Get-Content -LiteralPath $tokenFile -Raw).Trim() }
if (-not $token) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    $warnings.Add('A new local companion token was generated because none was recorded.')
}
if ($token.Length -lt 32) { throw 'The local companion token is invalid. Deployment stopped without changing the pairing.' }
New-Item -ItemType Directory -Path (Split-Path -Parent $pairedFile) -Force | Out-Null
Set-Content -LiteralPath $pairedFile -Value $token -Encoding utf8 -NoNewline
Set-Content -LiteralPath $tokenFile -Value $token -Encoding utf8 -NoNewline

$stopped = @()
$started = @()
if (-not $VerifyOnly -and -not $SkipServices) {
    $stopped += Stop-ListeningProcess -Port $apiPort
    $stopped += Stop-ListeningProcess -Port $hostPort
    Start-Sleep -Seconds 2
    $logs = Join-Path $configDirectory 'logs'
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    $environment = @{
        SENTINEL_HOST_TOKEN = $token
        SENTINEL_HOST_COMPANION_URL = "http://127.0.0.1:$hostPort"
        SENTINEL_HOST = '127.0.0.1'
        SENTINEL_PORT = "$apiPort"
    }
    foreach ($name in $environment.Keys) { Set-Item -Path "Env:$name" -Value $environment[$name] }
    $companion = Start-LoggedService -Executable $interpreter -Arguments @('-m', 'host_companion') -WorkingDirectory $resolvedInstall -LogPath (Join-Path $logs 'companion.log') -Name 'companion'
    $core = Start-LoggedService -Executable $interpreter -Arguments @('-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', "$apiPort") -WorkingDirectory $resolvedInstall -LogPath (Join-Path $logs 'sentinel.log') -Name 'core'
    $started += @(
        [PSCustomObject]@{ Service = 'host_companion'; Launcher = $companion; Port = $hostPort },
        [PSCustomObject]@{ Service = 'core'; Launcher = $core; Port = $apiPort }
    )
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if ((Test-ServiceReady -Path '/v1/status' -Port $hostPort) -and (Test-ServiceReady -Path '/api/health' -Port $apiPort)) { break }
        Start-Sleep -Milliseconds 500
    }
}

$coreStatus = $null
$companionStatus = $null
try { $coreStatus = (Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/api/health" -TimeoutSec 10 -UseBasicParsing).Content | ConvertFrom-Json } catch { $warnings.Add("Core health check failed: $($_.Exception.Message)") }
try { $companionStatus = (Invoke-WebRequest -Uri "http://127.0.0.1:$hostPort/v1/status" -TimeoutSec 10 -UseBasicParsing).Content | ConvertFrom-Json } catch { $warnings.Add("Host companion health check failed: $($_.Exception.Message)") }
if (-not $coreStatus -or $coreStatus.status -ne 'operational') { throw 'The core service did not report operational. Deployment is not assumed successful.' }
if (-not $companionStatus -or $companionStatus.status -ne 'operational') { throw 'The host companion did not report operational. Deployment is not assumed successful.' }

$version = $null
try { $version = $coreStatus.version } catch { }
$report = [ordered]@{
    schema = 'lin4cre.sentinel.deployment/v1'
    generated_at = [DateTimeOffset]::Now.ToString('o')
    source_root = $resolvedSource
    install_root = $resolvedInstall
    verify_only = [bool]$VerifyOnly
    deployed_version = $version
    interpreter = $interpreter
    requirements_installed = $requirementsInstalled
    services_stopped = $stopped
    services_started = $started
    core_status = $coreStatus
    companion_status = $companionStatus
    warnings = $warnings
    notes = @(
        'Deployment replaces application code only. The database, recovery points, audit history and settings are not touched.',
        'The host companion token pairing is preserved. A new token is generated only when none was recorded.',
        'Both services must report operational before this deployment is treated as successful.'
    )
}
if ($ReportPath) {
    $resolvedReport = $PSCmdlet.GetUnresolvedProviderPathFromPSPath($ReportPath)
    $reportDirectory = Split-Path -Parent $resolvedReport
    if ($reportDirectory) { New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null }
    [System.IO.File]::WriteAllText($resolvedReport, ($report | ConvertTo-Json -Depth 10), [System.Text.UTF8Encoding]::new($false))
    $reportHash = Get-FileHash -Algorithm SHA256 -LiteralPath $resolvedReport
    Write-Host "Deployment report written: $resolvedReport" -ForegroundColor Green
    Write-Host "SHA256: $($reportHash.Hash)" -ForegroundColor Cyan
}
Write-Host "SENTINEL deployment verified: version $version" -ForegroundColor Green
Write-Host "Install root: $resolvedInstall" -ForegroundColor Cyan
$warnings | ForEach-Object { Write-Warning $_ }

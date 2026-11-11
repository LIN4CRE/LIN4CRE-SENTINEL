#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false

function Invoke-ReadOnlyCommand {
    param([string]$Name, [scriptblock]$Command)
    try {
        return [PSCustomObject]@{ Available = $true; Result = @(& $Command 2>&1 | ForEach-Object { "$_" }) }
    } catch {
        return [PSCustomObject]@{ Available = $false; Result = @(); Error = $_.Exception.Message }
    }
}

$resolvedOutput = $PSCmdlet.GetUnresolvedProviderPathFromPSPath($OutputPath)
if (Test-Path -LiteralPath $resolvedOutput) {
    throw "Refusing to overwrite an existing audit file: $resolvedOutput"
}
$outputDirectory = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$software = [ordered]@{}
foreach ($app in @('docker', 'ollama', 'opencode', 'python', 'git', 'node', 'npm', 'pwsh')) {
    $found = Get-Command $app -ErrorAction SilentlyContinue
    if ($found) {
        $version = Invoke-ReadOnlyCommand -Name $app -Command { & $app --version 2>&1 | Select-Object -First 3 }
        $software[$app] = [ordered]@{ Path = $found.Source; Version = $version.Result }
    } else {
        $software[$app] = [ordered]@{ Path = $null; Version = @(); Available = $false }
    }
}

$projects = @()
foreach ($root in @('D:\Projects', 'D:\AI', 'E:\AI')) {
    if (Test-Path -LiteralPath $root) {
        foreach ($directory in Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue) {
            if (Test-Path -LiteralPath (Join-Path $directory.FullName '.git')) {
                $branch = git -C $directory.FullName branch --show-current 2>$null
                $dirty = git -C $directory.FullName status --porcelain 2>$null
                $projects += [PSCustomObject]@{
                    Root = $root
                    Project = $directory.Name
                    Branch = "$branch"
                    UncommittedChanges = [bool]$dirty
                }
            }
        }
    }
}

$drives = Get-PSDrive -Name C, D, E -ErrorAction SilentlyContinue | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        FreeGB = if ($null -ne $_.Free) { [math]::Round($_.Free / 1GB, 2) } else { $null }
        UsedGB = if ($null -ne $_.Used) { [math]::Round($_.Used / 1GB, 2) } else { $null }
    }
}

$report = [ordered]@{
    schema = 'lin4cre.sentinel.pc-audit/v1'
    audit = 'LIN4CRE SENTINEL read-only Windows PC audit'
    generated_at = [DateTimeOffset]::Now.ToString('o')
    host = [ordered]@{
        windows = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber
        powershell = $PSVersionTable.PSVersion.ToString()
        ram_gb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
        cpu = Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
        gpu = Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion
    }
    drives = @($drives)
    software = $software
    docker = [ordered]@{
        compose = (Invoke-ReadOnlyCommand 'docker-compose' { docker compose version }).Result
        info = (Invoke-ReadOnlyCommand 'docker-info' { docker info --format '{{json .}}' }).Result
        containers = (Invoke-ReadOnlyCommand 'docker-ps' { docker ps -a --format '{{json .}}' }).Result
        storage = (Invoke-ReadOnlyCommand 'docker-df' { docker system df }).Result
        volumes = (Invoke-ReadOnlyCommand 'docker-volumes' { docker volume ls }).Result
    }
    ollama = [ordered]@{
        models = (Invoke-ReadOnlyCommand 'ollama-list' { ollama list }).Result
        running = (Invoke-ReadOnlyCommand 'ollama-ps' { ollama ps }).Result
    }
    opencode = [ordered]@{
        locations = @(& where.exe opencode 2>$null | ForEach-Object { "$_" })
        config_candidates = @(
            (Join-Path $env:USERPROFILE '.config\opencode'),
            (Join-Path $env:USERPROFILE '.opencode'),
            (Join-Path $env:APPDATA 'opencode'),
            (Join-Path $env:LOCALAPPDATA 'opencode')
        ) | ForEach-Object { [PSCustomObject]@{ Path = $_; Exists = Test-Path -LiteralPath $_ } }
    }
    wsl = (Invoke-ReadOnlyCommand 'wsl-list' { wsl --list --verbose }).Result
    git_projects = $projects
    notes = @(
        'This audit does not install, remove, restart or reconfigure software.',
        'No environment variables, API keys, model weights or file contents are collected.',
        'Docker commands are read-only and may return an unavailable result when Docker Desktop is stopped.'
    )
}

$json = $report | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($resolvedOutput, $json, [System.Text.UTF8Encoding]::new($false))
$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $resolvedOutput
Write-Host "SENTINEL audit written: $resolvedOutput" -ForegroundColor Green
Write-Host "SHA256: $($hash.Hash)" -ForegroundColor Cyan
Write-Host 'Import this actual JSON file in SENTINEL → Setup & sources → Windows audit.'

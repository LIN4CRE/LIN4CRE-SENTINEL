#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$BackupRoot,
    [switch]$IncludeOllamaModels
)

$ErrorActionPreference = 'Stop'
$timestamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$destination = Join-Path $PSCmdlet.GetUnresolvedProviderPathFromPSPath($BackupRoot) "sentinel-$timestamp-$([Guid]::NewGuid().ToString('N').Substring(0,6))"
$files = [System.Collections.Generic.List[object]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

function Copy-VerifiedTree {
    param([string]$Source, [string]$Destination, [string[]]$ExcludeDirectories = @())
    if (-not (Test-Path -LiteralPath $Source)) { return }
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $arguments = @($Source, $Destination, '/E', '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP')
    if ($ExcludeDirectories.Count -gt 0) { $arguments += @('/XD') + $ExcludeDirectories }
    & robocopy @arguments | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "robocopy failed for $Source with exit code $LASTEXITCODE" }
    $sourceRoot = (Resolve-Path -LiteralPath $Source).Path.TrimEnd('\')
    $destinationRoot = (Resolve-Path -LiteralPath $Destination).Path.TrimEnd('\')
    foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -File -Recurse -Force) {
        $relative = $file.FullName.Substring($sourceRoot.Length).TrimStart('\')
        $skip = $false
        foreach ($excluded in $ExcludeDirectories) {
            if ($relative -like "*$excluded*") { $skip = $true; break }
        }
        if ($skip) { continue }
        $copied = Join-Path $destinationRoot $relative
        if (-not (Test-Path -LiteralPath $copied)) { throw "Backup verification failed; missing $copied" }
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
        $copiedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $copied).Hash
        if ($sourceHash -ne $copiedHash) { throw "Backup hash mismatch: $relative" }
        $files.Add([PSCustomObject]@{ Source = $file.FullName; Backup = $copied; Bytes = $file.Length; SHA256 = $copiedHash; Verified = $true })
    }
}

New-Item -ItemType Directory -Path $destination -Force | Out-Null
if (Test-Path -LiteralPath $ProjectRoot) {
    Copy-VerifiedTree -Source $ProjectRoot -Destination (Join-Path $destination 'Project') -ExcludeDirectories @('node_modules', 'dist', '.venv', '__pycache__', 'backups')
} else {
    $warnings.Add("Project root did not exist and was not backed up: $ProjectRoot")
}

$configTargets = @(
    @{ Source = (Join-Path $env:USERPROFILE '.config\opencode'); Name = 'OpenCode-config' },
    @{ Source = (Join-Path $env:USERPROFILE '.opencode'); Name = 'OpenCode-home' },
    @{ Source = (Join-Path $env:APPDATA 'opencode'); Name = 'OpenCode-roaming' },
    @{ Source = (Join-Path $env:LOCALAPPDATA 'opencode'); Name = 'OpenCode-local' }
)
foreach ($target in $configTargets) {
    if (Test-Path -LiteralPath $target.Source) {
        Copy-VerifiedTree -Source $target.Source -Destination (Join-Path $destination $target.Name)
    }
}

$ollamaRoot = Join-Path $env:USERPROFILE '.ollama'
if (Test-Path -LiteralPath $ollamaRoot) {
    if ($IncludeOllamaModels) {
        Copy-VerifiedTree -Source $ollamaRoot -Destination (Join-Path $destination 'Ollama-complete')
    } else {
        $configDestination = Join-Path $destination 'Ollama-config'
        New-Item -ItemType Directory -Path $configDestination -Force | Out-Null
        Get-ChildItem -LiteralPath $ollamaRoot -File -Force | ForEach-Object {
            $copied = Join-Path $configDestination $_.Name
            Copy-Item -LiteralPath $_.FullName -Destination $copied
            $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $copied).Hash
            if ($hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash) { throw "Ollama config hash mismatch: $($_.Name)" }
            $files.Add([PSCustomObject]@{ Source = $_.FullName; Backup = $copied; Bytes = $_.Length; SHA256 = $hash; Verified = $true })
        }
        $warnings.Add('Ollama model weights were excluded. Re-run with -IncludeOllamaModels before any operation that could alter or delete them.')
    }
}

$metadata = Join-Path $destination 'Metadata'
New-Item -ItemType Directory -Path $metadata -Force | Out-Null
$commands = [ordered]@{
    'docker-info.txt' = { docker info }
    'docker-containers.txt' = { docker ps -a --no-trunc }
    'docker-images.txt' = { docker images --digests --no-trunc }
    'docker-volumes.txt' = { docker volume ls }
    'ollama-models.txt' = { ollama list }
    'wsl-distributions.txt' = { wsl --list --verbose }
}
foreach ($entry in $commands.GetEnumerator()) {
    try { & $entry.Value 2>&1 | Out-File -LiteralPath (Join-Path $metadata $entry.Key) -Encoding utf8 }
    catch { $warnings.Add("Could not collect $($entry.Key): $($_.Exception.Message)") }
}

$manifest = [ordered]@{
    schema = 'lin4cre.sentinel.backup/v1'
    created_at = [DateTimeOffset]::UtcNow.ToString('o')
    backup_root = $destination
    source_project = $ProjectRoot
    include_ollama_models = [bool]$IncludeOllamaModels
    files_verified = $true
    file_count = $files.Count
    total_bytes = ($files | Measure-Object -Property Bytes -Sum).Sum
    files = $files
    warnings = $warnings
    restore_notes = 'Stop dependent applications before restoring. Verify hashes again, restore to a separate recovery location first, and never overwrite the only copy of an existing installation.'
}
$manifestPath = Join-Path $destination 'manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$manifestHash = Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath
Set-Content -LiteralPath (Join-Path $destination 'manifest.sha256') -Value "$($manifestHash.Hash)  manifest.json" -Encoding ascii

Write-Host "Verified backup created: $destination" -ForegroundColor Green
Write-Host "Files verified: $($files.Count)" -ForegroundColor Cyan
Write-Host "Manifest: $manifestPath" -ForegroundColor Cyan
$warnings | ForEach-Object { Write-Warning $_ }
Write-Host 'Keep this manifest. Guarded SENTINEL setup requires its path and rechecks the manifest status.'

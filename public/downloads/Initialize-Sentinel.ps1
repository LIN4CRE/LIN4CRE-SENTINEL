#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$DataRoot,
    [Parameter(Mandatory = $true)][string]$ArchiveRoot,
    [Parameter(Mandatory = $true)][string]$BackupManifest
)

$ErrorActionPreference = 'Stop'
$manifestPath = $PSCmdlet.GetUnresolvedProviderPathFromPSPath($BackupManifest)
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw 'Backup manifest not found. Run Backup-Sentinel.ps1 first; setup is blocked.'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'lin4cre.sentinel.backup/v1' -or -not $manifest.files_verified) {
    throw 'The backup manifest is missing or does not attest verified file hashes. Setup is blocked.'
}
$manifestDirectory = Split-Path -Parent $manifestPath
foreach ($file in $manifest.files) {
    if (-not $file.Verified) { throw "Unverified backup entry: $($file.Backup)" }
    if (-not (Test-Path -LiteralPath $file.Backup -PathType Leaf)) { throw "Backed-up file is missing: $($file.Backup)" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.Backup).Hash
    if ($actual -ne $file.SHA256) { throw "Backup hash verification failed: $($file.Backup)" }
}
Write-Host "Backup manifest and $($manifest.files.Count) copied file hashes re-verified." -ForegroundColor Green

$paths = @(
    $ProjectRoot,
    $DataRoot,
    (Join-Path $DataRoot 'agents'),
    (Join-Path $DataRoot 'intelligence'),
    (Join-Path $DataRoot 'opportunities'),
    (Join-Path $DataRoot 'scope-rules'),
    (Join-Path $DataRoot 'research'),
    (Join-Path $DataRoot 'evidence'),
    (Join-Path $DataRoot 'reports'),
    (Join-Path $DataRoot 'earnings'),
    (Join-Path $DataRoot 'dashboard'),
    $ArchiveRoot,
    (Join-Path $ArchiveRoot 'models'),
    (Join-Path $ArchiveRoot 'datasets'),
    (Join-Path $ArchiveRoot 'cybergym'),
    (Join-Path $ArchiveRoot 'docker-data'),
    (Join-Path $ArchiveRoot 'backups')
)
foreach ($path in $paths) {
    $resolved = $PSCmdlet.GetUnresolvedProviderPathFromPSPath($path)
    if (-not (Test-Path -LiteralPath $resolved)) {
        New-Item -ItemType Directory -Path $resolved | Out-Null
        Write-Host "Created $resolved"
    } elseif (Test-Path -LiteralPath $resolved -PathType Container) {
        Write-Host "Kept existing $resolved" -ForegroundColor DarkGray
    } else {
        throw "A file blocks the required directory: $resolved"
    }
}

$marker = Join-Path $DataRoot 'setup.json'
if (Test-Path -LiteralPath $marker) { throw "Refusing to overwrite existing setup marker: $marker" }
[ordered]@{
    schema = 'lin4cre.sentinel.setup/v1'
    created_at = [DateTimeOffset]::UtcNow.ToString('o')
    project_root = $ProjectRoot
    data_root = $DataRoot
    archive_root = $ArchiveRoot
    backup_manifest = $manifestPath
    installed_components = @('folder-foundations-only')
    testing_engine_enabled = $false
} | ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding utf8

Write-Host 'SENTINEL folder foundations created without installing or changing existing software.' -ForegroundColor Green
Write-Host 'Next: inspect the machine-specific plan. Do not deploy PentAGI or download CyberGym data yet.'

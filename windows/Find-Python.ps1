# Locate a usable CPython interpreter on this PC.
#
# Prints the full path to pythonw.exe (or python.exe) and nothing else, so the
# result can be captured by SentinelSetup.cmd and by Bootstrap.ps1. The
# Microsoft Store alias stub is deliberately ignored: it opens a store page
# instead of running an interpreter.
$ErrorActionPreference = 'SilentlyContinue'

$folders = New-Object System.Collections.Generic.List[string]

$registryRoots = @(
    @{ Hive = [Microsoft.Win32.Registry]::CurrentUser; Path = 'SOFTWARE\Python\PythonCore' },
    @{ Hive = [Microsoft.Win32.Registry]::LocalMachine; Path = 'SOFTWARE\Python\PythonCore' },
    @{ Hive = [Microsoft.Win32.Registry]::LocalMachine; Path = 'SOFTWARE\WOW6432Node\Python\PythonCore' }
)
foreach ($root in $registryRoots) {
    try {
        $key = $root.Hive.OpenSubKey($root.Path)
        if (-not $key) { continue }
        foreach ($name in $key.GetSubKeyNames()) {
            try {
                $install = $key.OpenSubKey("$name\InstallPath")
                if ($install) {
                    $path = $install.GetValue('')
                    if ($path) { $folders.Add([string]$path) }
                    $install.Close()
                }
            } catch { }
        }
        $key.Close()
    } catch { }
}

$localPython = Join-Path $env:LOCALAPPDATA 'Programs\Python'
if (Test-Path -LiteralPath $localPython -PathType Container) {
    Get-ChildItem -LiteralPath $localPython -Directory | Sort-Object -Property Name -Descending | ForEach-Object {
        $folders.Add($_.FullName)
    }
}

foreach ($base in @('C:\', $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
    if (-not $base) { continue }
    foreach ($version in @('Python313', 'Python312', 'Python311', 'Python310')) {
        $folder = Join-Path $base $version
        if (Test-Path -LiteralPath $folder -PathType Container) { $folders.Add($folder) }
    }
}

foreach ($name in @('pythonw.exe', 'python.exe')) {
    $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command -and $command.Source -and ($command.Source -notlike '*\WindowsApps\*')) {
        $folders.Add((Split-Path -Parent $command.Source))
    }
}

foreach ($folder in $folders) {
    foreach ($name in @('pythonw.exe', 'python.exe')) {
        $full = Join-Path $folder $name
        if ((Test-Path -LiteralPath $full -PathType Leaf) -and ($full -notlike '*\WindowsApps\*')) {
            Write-Output $full
            exit 0
        }
    }
}

exit 1

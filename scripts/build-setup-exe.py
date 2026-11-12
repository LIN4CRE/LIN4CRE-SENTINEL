"""Build the standalone one-click SENTINEL setup assets.

Two launchers are produced:

* ``LIN4CRE-SENTINEL-Setup.exe`` — a single-file application that needs no
  Python on the machine. Windows Smart App Control blocks newly built
  unsigned executables until they earn a reputation, so it cannot be the only
  option.
* ``LIN4CRE-SENTINEL-Setup.cmd`` — the same one-click flow using only tools
  that ship with Windows. It is not subject to executable reputation and
  therefore works on every machine, including those with Smart App Control
  switched on.

Both locate an existing installation, install the official release when it is
missing, find a real Python interpreter and open the graphical setup manager.
"""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
NAME = 'LIN4CRE-SENTINEL-Setup'
ENTRY = ROOT / 'windows' / 'SentinelLauncher.pyw'
COMMAND_LAUNCHER = ROOT / 'windows' / 'Install-Sentinel.cmd'
ICON = ROOT / 'docs' / 'images' / 'sentinel.ico'
WORK = ROOT / 'build' / 'setup-exe'
DOWNLOADS = ROOT / 'public' / 'downloads'


def main() -> int:
    if not ENTRY.is_file():
        print(f'Setup executable skipped: {ENTRY} is missing')
        return 0
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print('Setup executable skipped: PyInstaller is not installed (pip install pyinstaller)')
        return 0

    command = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm', '--clean', '--onefile', '--windowed',
        '--name', NAME,
        '--distpath', str(WORK / 'dist'),
        '--workpath', str(WORK / 'build'),
        '--specpath', str(WORK),
        '--collect-submodules', 'sentinel_runtime',
    ]
    if ICON.is_file():
        command += ['--icon', str(ICON)]
    command.append(str(ENTRY))

    print('Building the one-click setup executable…')
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print('Setup executable build failed; no success is assumed.')
        return result.returncode

    built = WORK / 'dist' / f'{NAME}.exe'
    if not built.is_file():
        print('Setup executable build did not produce the expected file.')
        return 1
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    target = DOWNLOADS / built.name
    shutil.copy2(built, target)
    shutil.copy2(built, ROOT / 'dist' / 'downloads' / built.name)
    print(f'Created {target} ({target.stat().st_size} bytes)')

    if COMMAND_LAUNCHER.is_file():
        command_target = DOWNLOADS / f'{NAME}.cmd'
        shutil.copy2(COMMAND_LAUNCHER, command_target)
        shutil.copy2(COMMAND_LAUNCHER, ROOT / 'dist' / 'downloads' / command_target.name)
        print(f'Created {command_target} ({command_target.stat().st_size} bytes)')
    else:
        print(f'Command launcher missing: {COMMAND_LAUNCHER}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

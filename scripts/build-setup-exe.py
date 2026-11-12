"""Build the standalone one-click SENTINEL setup executable.

The launcher only uses the Python standard library, so the resulting single
file runs on a machine with no Python installed at all. It installs the
official release archive on first use and then opens the graphical setup
manager.
"""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
NAME = 'LIN4CRE-SENTINEL-Setup'
ENTRY = ROOT / 'windows' / 'SentinelLauncher.pyw'
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
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Shared Windows runtime helpers for the SENTINEL setup manager and launcher.

Only the Python standard library is used here so these helpers work on a machine
that has a Python interpreter but none of SENTINEL's declared dependencies.
They locate the installed application, locate a real CPython interpreter
(ignoring the Microsoft Store alias stub) and install the official release
archive when the application is not present yet.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

APP_NAME = 'LIN4CRE SENTINEL'
RELEASE_URL = 'https://github.com/LIN4CRE/LIN4CRE-SENTINEL/releases/latest/download/LIN4CRE-SENTINEL-Windows-Setup.zip'
ARCHIVE_NAME = 'LIN4CRE-SENTINEL-Windows-Setup.zip'
STORE_ALIAS = 'windowsapps'


def local_app_data() -> Path:
    value = os.environ.get('LOCALAPPDATA')
    return Path(value) if value else Path.home() / 'AppData' / 'Local'


def install_root() -> Path:
    """Folder that holds the installed application and the local token/logs."""
    return local_app_data() / 'LIN4CRE' / 'SENTINEL'


def default_app_root() -> Path:
    """Folder the launcher installs the application into when it is missing."""
    return install_root() / 'app'


def persisted_install_path() -> Path:
    return install_root() / 'install-path.txt'


def remember_install_path(path: Path) -> None:
    try:
        target = persisted_install_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(path), encoding='utf-8')
    except OSError:
        pass


def is_app_dir(path: Path) -> bool:
    try:
        return (
            (path / 'backend' / 'main.py').is_file()
            and (path / 'windows' / 'SentinelSetup.pyw').is_file()
            and (path / 'requirements.txt').is_file()
        )
    except OSError:
        return False


def candidate_app_dirs() -> list[Path]:
    """Every folder that could hold an installed copy, most likely first."""
    roots: list[Path] = []
    env = os.environ.get('SENTINEL_PROJECT_DIR', '').strip()
    if env:
        roots.append(Path(env))
    marker = persisted_install_path()
    try:
        if marker.is_file():
            recorded = marker.read_text(encoding='utf-8').strip()
            if recorded:
                roots.append(Path(recorded))
    except OSError:
        pass
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        roots.extend([exe_dir, exe_dir.parent, exe_dir / 'LIN4CRE-SENTINEL'])
    else:
        roots.append(Path(__file__).resolve().parent.parent)
    home = Path.home()
    roots.extend([home / 'LIN4CRE-SENTINEL', home / 'SENTINEL'])
    roots.extend([default_app_root(), install_root()])
    for base in (home / 'Desktop', home / 'Downloads', home / 'Documents', home):
        try:
            roots.extend(child for child in base.iterdir() if child.is_dir())
        except OSError:
            continue
    return roots


def find_app_dir() -> Path | None:
    """Return an existing installation of the application, if there is one."""
    seen: set[str] = set()
    for root in candidate_app_dirs():
        try:
            key = str(root.resolve()).lower()
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        if is_app_dir(root):
            return root
    return None


def _registry_python_dirs() -> list[Path]:
    """Installation folders recorded in the Windows registry."""
    folders: list[Path] = []
    try:
        import winreg
    except ImportError:
        return folders
    roots = (
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Python\PythonCore'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Python\PythonCore'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Python\PythonCore'),
    )
    for hive, key_path in roots:
        try:
            with winreg.OpenKey(hive, key_path) as handle:
                index = 0
                while True:
                    try:
                        name = winreg.EnumKey(handle, index)
                    except OSError:
                        break
                    index += 1
                    for suffix in (r'\InstallPath', r'\ExecutablePath'):
                        try:
                            with winreg.OpenKey(handle, name + suffix) as subkey:
                                value, _ = winreg.QueryValueEx(subkey, '')
                        except OSError:
                            continue
                        if not value:
                            continue
                        path = Path(str(value))
                        folders.append(path if path.suffix.lower() == '.exe' else path.parent)
                        break
        except OSError:
            continue
    return folders


def _candidate_python_files() -> list[Path]:
    candidates: list[Path] = []
    current = Path(sys.executable)
    # In a frozen build sys.executable is the launcher itself, not an interpreter.
    if not getattr(sys, 'frozen', False) and current.is_file() and STORE_ALIAS not in str(current).lower():
        candidates.append(current)
    for folder in _registry_python_dirs():
        for name in ('pythonw.exe', 'python.exe'):
            candidates.append(folder / name)
    local = local_app_data() / 'Programs' / 'Python'
    if local.is_dir():
        try:
            for child in sorted(local.iterdir(), reverse=True):
                for name in ('pythonw.exe', 'python.exe'):
                    candidates.append(child / name)
        except OSError:
            pass
    for base in (Path('C:\\'), Path(os.environ.get('ProgramFiles', r'C:\Program Files'))):
        for version in ('Python313', 'Python312', 'Python311', 'Python310'):
            for name in ('pythonw.exe', 'python.exe'):
                candidates.append(base / version / name)
    for name in ('pythonw.exe', 'python.exe'):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    launcher = shutil.which('py.exe') or shutil.which('py')
    if launcher:
        try:
            result = subprocess.run(
                [launcher, '-3', '-c', 'import sys; print(sys.executable)'],
                capture_output=True, text=True, timeout=25,
            )
        except Exception:
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            executable = Path(result.stdout.strip())
            candidates.append(executable.with_name('pythonw.exe'))
            candidates.append(executable)
    return candidates


def _prefer_windowed(candidate: Path) -> Path:
    """Use pythonw.exe when it exists so no console window is opened."""
    if candidate.name.lower() == 'python.exe':
        sibling = candidate.with_name('pythonw.exe')
        try:
            if sibling.is_file():
                return sibling
        except OSError:
            pass
    return candidate


def find_python() -> Path | None:
    """Return a usable CPython interpreter, ignoring the Microsoft Store alias."""
    for candidate in _candidate_python_files():
        try:
            if candidate.is_file() and STORE_ALIAS not in str(candidate).lower():
                return _prefer_windowed(candidate)
        except OSError:
            continue
    return None


def download_release(destination: Path, progress=None) -> Path:
    """Download the official release archive."""
    request = urllib.request.Request(RELEASE_URL, headers={'User-Agent': APP_NAME})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=180) as response:
        total = int(response.headers.get('Content-Length') or 0)
        with destination.open('wb') as handle:
            while True:
                chunk = response.read(262144)
                if not chunk:
                    break
                handle.write(chunk)
                if progress is not None:
                    progress(handle.tell(), total)
    return destination


def extract_release(archive: Path, destination: Path) -> Path:
    """Extract the release archive into ``destination`` and return it."""
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        names = [item.filename for item in bundle.infolist() if item.filename.strip()]
        tops = {name.split('/')[0] for name in names}
        prefix = tops.pop() + '/' if len(tops) == 1 else ''
        for item in bundle.infolist():
            if prefix and not item.filename.startswith(prefix):
                continue
            relative = item.filename[len(prefix):]
            if not relative:
                continue
            target = (destination / relative).resolve()
            if not str(target).startswith(str(root)):
                raise RuntimeError('The download contains an unsafe path and was not extracted.')
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(item) as source, target.open('wb') as handle:
                shutil.copyfileobj(source, handle)
    return destination


def install_from_release(destination: Path | None = None, progress=None) -> Path:
    """Download and install the official release; returns the app folder."""
    destination = destination or default_app_root()
    archive = install_root() / ARCHIVE_NAME
    download_release(archive, progress)
    extract_release(archive, destination)
    try:
        archive.unlink()
    except OSError:
        pass
    if not is_app_dir(destination):
        raise RuntimeError('The downloaded archive did not contain a usable SENTINEL installation.')
    remember_install_path(destination)
    return destination


def launch_setup(app_dir: Path, python: Path) -> None:
    """Open the graphical setup manager with the given interpreter.

    The window is started through the Windows shell rather than as a direct
    child process. A direct child would inherit the frozen launcher's working
    directory and file handles, which breaks the one-file builder's own
    temporary-directory cleanup.
    """
    script = app_dir / 'windows' / 'SentinelSetup.pyw'
    if not script.is_file():
        raise RuntimeError('The setup manager is missing from the installation.')
    if python.name.lower() not in ('python.exe', 'pythonw.exe'):
        raise RuntimeError(f'{python} is not a Python interpreter.')
    arguments = f'"{script}"'
    try:
        import ctypes
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 'open', str(python), arguments, str(app_dir), 1,
        )
        if int(result) > 32:
            return
    except Exception:
        pass
    env = os.environ.copy()
    env['SENTINEL_PROJECT_DIR'] = str(app_dir)
    subprocess.Popen(
        [str(python), str(script)],
        cwd=str(app_dir),
        env=env,
        creationflags=getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0),
        close_fds=True,
    )

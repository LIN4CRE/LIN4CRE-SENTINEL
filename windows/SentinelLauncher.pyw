"""LIN4CRE SENTINEL one-click launcher.

Double-click this file (or the packaged ``LIN4CRE-SENTINEL-Setup.exe``) and it
handles everything that can be handled automatically:

* finds an existing SENTINEL installation, or downloads and installs the
  official release archive into ``%LOCALAPPDATA%\\LIN4CRE\\SENTINEL\\app``;
* locates a real CPython interpreter through the registry and the standard
  install folders, ignoring the Microsoft Store alias stub;
* only asks for help when Python is genuinely missing, by opening the native
  bootstrap window;
* finally opens the graphical setup manager, which starts the private local
  services and inspects this PC.

No command line is required at any point.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinel_runtime import (  # noqa: E402
    APP_NAME,
    default_app_root,
    find_app_dir,
    find_python,
    install_from_release,
    is_app_dir,
    launch_setup,
    remember_install_path,
)

BG = '#0d1511'
PANEL = '#142019'
FG = '#d8e4da'
MUTED = '#8b9a8f'
ACCENT = '#b7ef72'


class Launcher:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME + ' — Setup')
        self.root.geometry('560x300')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.status = tk.Label(
            self.root, text='Preparing SENTINEL…', bg=BG, fg=FG,
            font=('Segoe UI', 11), wraplength=520, justify='left',
        )
        self.status.pack(padx=30, pady=(34, 12))
        self.detail = tk.Label(
            self.root, text='', bg=BG, fg=MUTED, font=('Segoe UI', 9),
            wraplength=520, justify='left',
        )
        self.detail.pack(padx=30)
        self.bar = ttk.Progressbar(self.root, mode='determinate', length=500)
        self.bar.pack(padx=30, pady=22)
        self.cancel = tk.Button(self.root, text='Cancel', bg='#24352a', fg=FG, relief='flat', command=self.root.destroy)
        self.cancel.pack(pady=(0, 22))
        self.root.protocol('WM_DELETE_WINDOW', self.root.destroy)
        threading.Thread(target=self.prepare, daemon=True).start()

    def say(self, message: str, detail: str = '') -> None:
        self.root.after(0, self._say, message, detail)

    def _say(self, message: str, detail: str) -> None:
        self.status.configure(text=message)
        self.detail.configure(text=detail)

    def progress(self, written: int, total: int) -> None:
        if total <= 0:
            return
        value = max(0, min(100, int(written * 100 / total)))
        self.root.after(0, self.bar.configure, {'value': value})

    def prepare(self) -> None:
        try:
            self.say('Looking for SENTINEL…', 'Checking this computer for an existing installation.')
            app = find_app_dir()
            if app is None:
                self.say('Downloading SENTINEL…', 'Fetching the official release. This only happens once.')
                app = install_from_release(default_app_root(), self.progress)
                self.say('SENTINEL installed.', str(app))
            else:
                remember_install_path(app)
                self.say('SENTINEL found.', str(app))
            self.bar.configure(value=100)
            self.say('Checking for Python…', 'Looking for an installed interpreter.')
            python = find_python()
            if python is None:
                self.say('Python is required.', 'Opening the native bootstrap window.')
                self.run_bootstrap(app)
                return
            self.say('Starting the setup assistant…', str(app))
            launch_setup(app, python)
            self.root.after(1200, self.root.destroy)
        except Exception as error:  # noqa: BLE001 - the window must report any failure
            self.root.after(0, self.failed, str(error))

    def run_bootstrap(self, app: Path) -> None:
        script = app / 'windows' / 'Bootstrap.ps1'
        flags = 0
        if os.name == 'nt':
            flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
        subprocess.Popen(
            ['powershell.exe', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA', '-File', str(script), '-AppDir', str(app)],
            cwd=str(app),
            creationflags=flags,
            close_fds=True,
        )
        self.root.after(1500, self.root.destroy)

    def failed(self, message: str) -> None:
        choice = messagebox.askyesno(
            APP_NAME,
            'Automatic setup did not finish.\n\n' + message + '\n\n'
            'Choose the SENTINEL folder manually instead?',
            parent=self.root,
        )
        if choice:
            folder = filedialog.askdirectory(parent=self.root, title='Select the LIN4CRE SENTINEL folder')
            if folder and is_app_dir(Path(folder)):
                remember_install_path(Path(folder))
                python = find_python()
                if python is None:
                    self.run_bootstrap(Path(folder))
                    return
                launch_setup(Path(folder), python)
                self.root.destroy()
                return
        self.root.destroy()


def main() -> int:
    Launcher().root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""LIN4CRE SENTINEL graphical Windows setup manager. No terminal commands required.

Run SentinelSetup.cmd. The UI uses the same signed operation/approval routes as the
web console. Host mutations remain allowlisted and are never executed at startup.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_NAME = 'LIN4CRE SENTINEL'
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
HOST_PORT = 8765
API_PORT = 8000
BG = '#0d1511'
PANEL = '#142019'
FG = '#d8e4da'
MUTED = '#8b9a8f'
ACCENT = '#b7ef72'


class Api:
    def __init__(self) -> None:
        self.token = ''

    def request(self, path: str, method: str = 'GET', body: dict | None = None, host: bool = False) -> dict | list:
        port = HOST_PORT if host else API_PORT
        headers = {'Content-Type': 'application/json'}
        if host:
            headers['X-Sentinel-Token'] = self.token
        request = urllib.request.Request(
            f'http://127.0.0.1:{port}{path}', method=method,
            data=None if body is None else json.dumps(body).encode(), headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors='replace')
            try:
                detail = json.loads(detail).get('detail', detail)
            except Exception:
                pass
            raise RuntimeError(str(detail)) from error


class SetupWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME + ' — Setup')
        self.geometry('1050x740')
        self.minsize(850, 620)
        self.configure(bg=BG)
        self.api = Api()
        self.events: queue.Queue = queue.Queue()
        self.processes: list[subprocess.Popen] = []
        self.inspection: dict = {}
        self.components: dict[str, dict] = {}
        self.selected: dict[str, tk.BooleanVar] = {}
        self.operation: dict = {}
        self.busy = False
        self.report_path = PROJECT / 'data' / 'installation-report.json'
        self._style()
        self._build()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.process_events)
        self.after(250, self.prepare_local_services)

    def _style(self) -> None:
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background=BG)
        style.configure('Panel.TFrame', background=PANEL)
        style.configure('TLabel', background=BG, foreground=FG, font=('Segoe UI', 10))
        style.configure('Muted.TLabel', foreground=MUTED, font=('Segoe UI', 9))
        style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'))
        style.configure('Heading.TLabel', background=PANEL, font=('Segoe UI', 12, 'bold'))
        style.configure('Panel.TLabel', background=PANEL)
        style.configure('PanelMuted.TLabel', background=PANEL, foreground=MUTED, font=('Segoe UI', 9))
        style.configure('TButton', padding=(13, 9), background='#24352a', foreground=FG, borderwidth=0, font=('Segoe UI', 9))
        style.map('TButton', background=[('active', '#314837'), ('disabled', '#1b2720')])
        style.configure('Accent.TButton', background=ACCENT, foreground='#162012', font=('Segoe UI', 9, 'bold'))
        style.map('Accent.TButton', background=[('active', '#ccfa93'), ('disabled', '#506344')])
        style.configure('Danger.TButton', background='#542f2b', foreground='#f1bbb1')
        style.configure('Treeview', background='#111b15', foreground=FG, fieldbackground='#111b15', rowheight=33, borderwidth=0, font=('Segoe UI', 9))
        style.configure('Treeview.Heading', background='#1a2920', foreground=MUTED, borderwidth=0, font=('Segoe UI', 8, 'bold'))
        style.map('Treeview', background=[('selected', '#2a4030')])
        style.configure('TCheckbutton', background=PANEL, foreground=FG)
        style.map('TCheckbutton', background=[('active', PANEL)])

    def _build(self) -> None:
        top = ttk.Frame(self, padding=(28, 22))
        top.pack(fill='x')
        ttk.Label(top, text='LIN4CRE / LOCAL AI OPERATIONS', style='Muted.TLabel').pack(anchor='w')
        ttk.Label(top, text='Set up SENTINEL', style='Title.TLabel').pack(anchor='w', pady=(5, 3))
        ttk.Label(top, text='Real inspection. Explicit permission. Verified recovery. No command line required.', style='Muted.TLabel').pack(anchor='w')

        body = ttk.Frame(self, padding=(28, 0))
        body.pack(fill='both', expand=True)
        left = ttk.Frame(body, style='Panel.TFrame', padding=18)
        left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(body, style='Panel.TFrame', padding=18, width=280)
        right.pack(side='right', fill='y', padx=(14, 0))
        right.pack_propagate(False)

        actionbar = ttk.Frame(left, style='Panel.TFrame')
        actionbar.pack(fill='x')
        ttk.Label(actionbar, text='Your computer', style='Heading.TLabel').pack(side='left')
        self.scan_button = ttk.Button(actionbar, text='Inspect this PC', style='Accent.TButton', command=self.scan)
        self.scan_button.pack(side='right')
        self.status = ttk.Label(left, text='Starting the private local services… Nothing will be installed automatically.', style='PanelMuted.TLabel', wraplength=650)
        self.status.pack(anchor='w', pady=(13, 10))

        columns = ('component', 'installed', 'status')
        self.tree = ttk.Treeview(left, columns=columns, show='headings', height=12)
        for column, title, width in [('component', 'COMPONENT', 180), ('installed', 'DETECTED VERSION', 160), ('status', 'VERIFIED STATE', 320)]:
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, minwidth=100)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.show_component)
        self.detail = tk.Text(left, height=8, wrap='word', bg='#0e1812', fg=MUTED, insertbackground=FG, relief='flat', padx=10, pady=10, font=('Consolas', 9))
        self.detail.pack(fill='x', pady=(10, 0))
        self.detail.insert('1.0', 'No inspection has completed. Select “Inspect this PC” for a read-only hardware, software and service check.')
        self.detail.configure(state='disabled')

        ttk.Label(right, text='Guided setup', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(right, text='Choose components only after inspection. SENTINEL creates a plan; you review it; only then can it run.', style='PanelMuted.TLabel', wraplength=235).pack(anchor='w', pady=(10, 16))
        ttk.Label(right, text='Missing components to install', style='Panel.TLabel').pack(anchor='w')
        self.choices = ttk.Frame(right, style='Panel.TFrame')
        self.choices.pack(fill='x', pady=(5, 12))
        ttk.Label(self.choices, text='Inspect first to see available choices.', style='PanelMuted.TLabel', wraplength=235).pack(anchor='w')
        self.install_button = ttk.Button(right, text='Plan selected installations', command=self.plan_install, state='disabled')
        self.install_button.pack(fill='x', pady=3)
        ttk.Button(right, text='Plan health repair', command=self.plan_repair).pack(fill='x', pady=3)
        ttk.Button(right, text='Create verified backup', command=self.backup).pack(fill='x', pady=3)
        ttk.Button(right, text='Save installation report', command=self.export_report).pack(fill='x', pady=3)
        ttk.Button(right, text='Open AI operations console', command=lambda: webbrowser.open(f'http://127.0.0.1:{API_PORT}/assistant')).pack(fill='x', pady=(14, 3))
        ttk.Button(right, text='Open recovery centre', command=lambda: webbrowser.open(f'http://127.0.0.1:{API_PORT}/recovery')).pack(fill='x', pady=3)
        ttk.Separator(right).pack(fill='x', pady=15)
        ttk.Button(right, text='Emergency stop', style='Danger.TButton', command=self.emergency_stop).pack(fill='x')
        ttk.Label(right, text='Stops active operations and revokes testing permissions. It does not delete data.', style='PanelMuted.TLabel', wraplength=235).pack(anchor='w', pady=(7, 0))

        footer = ttk.Frame(self, padding=(28, 16))
        footer.pack(fill='x')
        ttk.Label(footer, text='£0 third-party software target  ·  Local services only  ·  Human approval required', style='Muted.TLabel').pack(side='left')
        ttk.Button(footer, text='Close', command=self.close).pack(side='right')

    def run_async(self, description: str, function) -> None:
        if self.busy:
            return
        self.busy = True
        self.status.configure(text=description)
        def work():
            try:
                result = function()
                self.events.put(('done', description, result))
            except Exception as error:
                self.events.put(('error', description, str(error)))
        threading.Thread(target=work, daemon=True).start()

    def process_events(self) -> None:
        try:
            while True:
                kind, description, result = self.events.get_nowait()
                self.busy = False
                if kind == 'error':
                    self.status.configure(text=f'Verification failed or action unavailable: {result}')
                    messagebox.showerror('SENTINEL — action not completed', str(result), parent=self)
                elif kind == 'inspection':
                    self.inspection = result
                    self.render_inspection()
                    self.status.configure(text='Inspection complete. Results below came from this computer; no changes were made.')
                elif kind == 'plan':
                    self.operation = result
                    self.status.configure(text='Plan ready. Review every action before approving it.')
                    self.show_plan(result)
                elif kind == 'execution':
                    self.operation = result
                    self.status.configure(text=f"Operation finished with status: {result.get('status', 'unknown').upper()}. Review verification details.")
                    self.show_result(result)
                    self.scan()
                elif kind == 'backup':
                    self.status.configure(text=f"Backup status: {result.get('status', 'unknown')}. Open the recovery centre to review integrity and host-backup details.")
                    messagebox.showinfo('SENTINEL backup', json.dumps(result, indent=2), parent=self)
                elif kind == 'report':
                    self.status.configure(text=f'Installation report saved to {result}')
                    messagebox.showinfo('Installation report', f'Saved:\n{result}', parent=self)
                elif kind == 'services':
                    self.status.configure(text='Private local services are ready. Start with a read-only PC inspection.')
                    self.scan()
                elif kind == 'stopped':
                    self.status.configure(text='Emergency stop activated. Active operations were asked to stop and testing permissions revoked.')
                else:
                    self.status.configure(text=f'{description} completed.')
        except queue.Empty:
            pass
        self.after(100, self.process_events)

    def prepare_local_services(self) -> None:
        import importlib.util
        missing = [name for name in ('fastapi', 'uvicorn', 'httpx', 'pydantic', 'psutil') if importlib.util.find_spec(name) is None]
        if missing:
            explanation = 'SENTINEL needs its declared local Python packages (' + ', '.join(missing) + ').\n\nInstall them from requirements.txt now? This uses pip and may download free/open-source packages. No third-party AI subscription is included.'
            if not messagebox.askyesno('Authorise local runtime installation', explanation, parent=self):
                self.status.configure(text='Setup is waiting. Local runtime packages were not installed; no service health is assumed.')
                return
            def install_runtime():
                marker = PROJECT / 'data' / 'backups' / 'pre-runtime-install.txt'
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(f'Before local runtime installation: {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\n', encoding='utf-8')
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(PROJECT / 'requirements.txt')], cwd=PROJECT, capture_output=True, text=True, timeout=1200)
                if result.returncode != 0:
                    raise RuntimeError('Package installation failed; success is not assumed.\n' + (result.stderr or result.stdout)[-3000:])
                self._start_services()
                return True
            self.run_async('Installing the authorised local runtime', install_runtime)
        else:
            self.start_local_services()

    def start_local_services(self) -> None:
        self.run_async('Starting local services', self._start_services)

    def _start_services(self) -> None:
        config_dir = Path(os.environ.get('LOCALAPPDATA', str(PROJECT / 'data'))) / 'LIN4CRE' / 'SENTINEL'
        config_dir.mkdir(parents=True, exist_ok=True)
        token_file = config_dir / 'companion-token.txt'
        if token_file.exists():
            token = token_file.read_text(encoding='utf-8').strip()
        else:
            token = secrets.token_urlsafe(32)
            token_file.write_text(token, encoding='utf-8')
        if len(token) < 32:
            raise RuntimeError('The local companion token is invalid. Setup stopped without making changes.')
        paired_file = PROJECT / 'host_data' / 'host-token'
        paired_file.parent.mkdir(parents=True, exist_ok=True)
        if paired_file.exists() and len(paired_file.read_text(encoding='utf-8').strip()) >= 32:
            # Preserve an existing pairing rather than silently replacing credentials.
            token = paired_file.read_text(encoding='utf-8').strip()
            token_file.write_text(token, encoding='utf-8')
        else:
            temporary = paired_file.with_suffix('.tmp')
            temporary.write_text(token, encoding='utf-8')
            os.replace(temporary, paired_file)
        self.api.token = token
        try:
            os.chmod(paired_file, 0o600)
            if os.name == 'nt':
                subprocess.run(['icacls', str(paired_file), '/inheritance:r', '/grant:r', f'{__import__("getpass").getuser()}:(R,W)'], check=False, capture_output=True, timeout=15)
        except OSError:
            pass
        env = os.environ.copy()
        env.update({
            'SENTINEL_HOST_TOKEN': token,
            'SENTINEL_HOST_COMPANION_URL': f'http://127.0.0.1:{HOST_PORT}',
            'SENTINEL_HOST': '127.0.0.1',
            'SENTINEL_PORT': str(API_PORT),
        })
        logs = config_dir / 'logs'
        logs.mkdir(exist_ok=True)
        if not self._alive(HOST_PORT):
            log = (logs / 'companion.log').open('ab')
            self.processes.append(subprocess.Popen([sys.executable, '-m', 'host_companion'], cwd=PROJECT, env=env, stdout=log, stderr=log, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)))
        if not self._alive(API_PORT):
            log = (logs / 'sentinel.log').open('ab')
            self.processes.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(API_PORT)], cwd=PROJECT, env=env, stdout=log, stderr=log, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)))
        deadline = time.time() + 35
        while time.time() < deadline:
            if self._alive(HOST_PORT) and self._alive(API_PORT):
                return True
            if any(process.poll() not in (None, 0) for process in self.processes):
                raise RuntimeError(f'A local service stopped during startup. Read the logs in {logs}. No installation success is assumed.')
            time.sleep(0.5)
        raise RuntimeError(f'Local services did not become ready. Check port availability and logs in {logs}.')

    @staticmethod
    def _alive(port: int) -> bool:
        try:
            path = '/v1/status' if port == HOST_PORT else '/api/health'
            with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=1) as response:
                return response.status == 200
        except Exception:
            return False

    def scan(self) -> None:
        def inspect():
            result = self.api.request('/v1/inspect', host=True)
            self.events.put(('inspection', 'Inspection', result))
            return result
        if not self.busy:
            self.busy = True
            self.status.configure(text='Read-only inspection in progress: hardware, storage, dependencies, versions, services, models and configuration…')
            threading.Thread(target=inspect, daemon=True).start()

    def render_inspection(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.components = {item['key']: item for item in self.inspection.get('components', [])}
        for key, item in self.components.items():
            self.tree.insert('', 'end', iid=key, values=(item['name'], item.get('installed_version') or 'Not installed', item.get('status') or 'No Data Available'))
        for widget in self.choices.winfo_children():
            widget.destroy()
        self.selected = {}
        for key, item in self.components.items():
            if item.get('status') in ('missing', 'unhealthy', 'outdated') and key in ('docker_desktop', 'ollama', 'opencode', 'python', 'nodejs', 'git'):
                variable = tk.BooleanVar(value=False)
                self.selected[key] = variable
                ttk.Checkbutton(self.choices, text=item['name'], variable=variable).pack(anchor='w', pady=2)
        if not self.selected:
            ttk.Label(self.choices, text='No supported missing or unhealthy components were detected. No Data Available for other installers.', style='PanelMuted.TLabel', wraplength=235).pack(anchor='w')
        self.install_button.configure(state='normal' if self.selected else 'disabled')

    def show_component(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item = self.components[selection[0]]
        self.detail.configure(state='normal')
        self.detail.delete('1.0', 'end')
        self.detail.insert('1.0', json.dumps(item, indent=2))
        self.detail.configure(state='disabled')

    def plan_install(self) -> None:
        selected = [key for key, variable in self.selected.items() if variable.get()]
        if not selected:
            messagebox.showinfo('Choose components', 'Select at least one missing or unhealthy component first.', parent=self)
            return
        self.run_async('Creating an installation plan', lambda: self.api.request('/api/operations/install', 'POST', {'components': selected}))

    def plan_repair(self) -> None:
        categories = [key for key, item in self.components.items() if item.get('status') in ('unhealthy', 'missing') and key in ('docker_desktop', 'ollama')]
        if not categories:
            messagebox.showinfo('No supported repair target', 'No unhealthy Docker or Ollama installation was detected. Use PC inspection for current details.', parent=self)
            return
        self.run_async('Creating a repair plan', lambda: self.api.request('/api/operations/repair', 'POST', {'component': categories[0]}))

    def show_plan(self, operation: dict) -> None:
        plan = operation.get('plan', {})
        summary = [f"Operation: {operation.get('title')}", f"Status: {operation.get('status')}", f"Plan hash: {operation.get('plan_hash')}", '']
        for index, action in enumerate(plan.get('actions', []), 1):
            summary.extend([f'{index}. {action.get("description")}', f'   Registered action: {action.get("action")}', f'   Parameters: {json.dumps(action.get("parameters", {}))}'])
        summary.extend(['', f'Rollback: {plan.get("rollback", "See operation details")}', 'Approval expires: ' + str(operation.get('expires_at'))])
        if not messagebox.askokcancel('Review the exact operation', '\n'.join(summary) + '\n\nSelect OK to approve and start this exact plan. Select Cancel to leave it unapproved.', parent=self):
            return
        self.run_async('Recording explicit approval', lambda: self.approve(operation))

    def approve(self, operation: dict) -> dict:
        canonical = json.dumps(operation['plan'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        if digest != operation['plan_hash']:
            raise RuntimeError('Plan hash mismatch. Approval was refused.')
        approved = self.api.request(f"/api/operations/{operation['id']}/approve", 'POST', {'confirmed': True, 'plan_hash': digest})
        result = approved
        deadline = time.time() + 3900
        while result.get('status') not in ('succeeded', 'failed', 'partial', 'cancelled') and time.time() < deadline:
            time.sleep(1)
            result = self.api.request(f"/api/operations/{operation['id']}")
        self.events.put(('execution', 'Execution', result))
        return result

    def show_result(self, operation: dict) -> None:
        messagebox.showinfo('Operation result', json.dumps({'status': operation.get('status'), 'result': operation.get('result'), 'error': operation.get('error'), 'verification': operation.get('verification')}, indent=2), parent=self)

    def backup(self) -> None:
        self.run_async('Creating and verifying a recovery point', lambda: self.api.request('/api/operations/backup', 'POST'))

    def export_report(self) -> None:
        def export():
            report = self.api.request('/api/operations/installation-report')
            path = filedialog.asksaveasfilename(parent=self, title='Save actual installation report', defaultextension='.json', initialfile='SENTINEL-installation-report.json', filetypes=[('JSON report', '*.json')])
            if not path:
                return 'No file selected'
            Path(path).write_text(json.dumps(report, indent=2), encoding='utf-8')
            self.report_path = Path(path)
            self.events.put(('report', 'Installation report', path))
            return path
        self.run_async('Collecting actual installation results', export)

    def emergency_stop(self) -> None:
        if messagebox.askyesno('Emergency stop', 'Stop active operations and revoke testing permissions now?', parent=self):
            self.run_async('Emergency stop', lambda: self.api.request('/api/operations/emergency-stop', 'POST'))

    def close(self) -> None:
        if self.busy and not messagebox.askyesno('Operation in progress', 'A local action is still running. Closing this window will not cancel it. Close the setup window?', parent=self):
            return
        # Leave services running for the web console; no application or model is uninstalled.
        self.destroy()


if __name__ == '__main__':
    try:
        SetupWindow().mainloop()
    except Exception as error:
        try:
            messagebox.showerror('SENTINEL setup failed', str(error))
        except Exception:
            pass
        raise

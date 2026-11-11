import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AlertTriangle, ArrowDownToLine, BookOpenCheck, Check, CheckCircle2, ChevronRight, CircleDollarSign, Clipboard, CloudOff, Copy, Database, Download, ExternalLink, FileCheck2, FileInput, FileJson, FolderCheck, HardDrive, KeyRound, Laptop, Link2, Loader2, LockKeyhole, RefreshCw, Server, Settings2, ShieldCheck, ShieldX, TerminalSquare, Upload, ZapOff } from 'lucide-react'
import { api, download, patch, post } from '../api'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import type { Settings } from '../types'
import { copyText, date } from '../utils'
import { Badge, Button, Field, FormGrid, Modal, Notice, PageHeader } from '../components/UI'

function CopyButton({ text }: { text: string }) {
  const toast = useToast()
  return <button className="copy-button" onClick={async () => { await copyText(text); toast('Command copied') }} title="Copy command"><Copy size={15} /></button>
}

export default function SettingsPage() {
  const { settings, sources, dashboard, refresh } = useData()
  const [params] = useSearchParams()
  const [ollamaUrl, setOllamaUrl] = useState(settings?.ollama_url || '')
  const [model, setModel] = useState(settings?.ollama_model || '')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ connected: boolean; error?: string; models: { name: string; size?: number }[] } | null>(null)
  const [killOpen, setKillOpen] = useState(false)
  const [backup, setBackup] = useState<{ file: string; sha256: string; bytes: number; download_url: string } | null>(null)
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  useEffect(() => { setOllamaUrl(settings?.ollama_url || ''); setModel(settings?.ollama_model || '') }, [settings])
  useEffect(() => { const id = params.get('section'); if (id) window.setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100) }, [params])
  const saveSettings = async (values: Partial<Settings>, message: string) => {
    setSaving(true)
    try { await patch('/settings', values); toast(message); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to save settings', 'error') }
    finally { setSaving(false) }
  }
  const testOllama = async () => {
    setTesting(true); setTestResult(null)
    try { const result = await post<typeof testResult>('/ai/ollama/test', { url: ollamaUrl }); setTestResult(result); if (result?.connected) toast('Ollama connection verified') }
    catch (error) { toast(error instanceof Error ? error.message : 'Connection test failed', 'error') }
    finally { setTesting(false) }
  }
  const importAudit = async (file?: File) => {
    if (!file) return
    try { const parsed = JSON.parse(await file.text()); await post('/system/pc-audit', parsed); toast('Windows PC audit imported'); await refresh() }
    catch (error) { toast(error instanceof Error ? `Audit import failed: ${error.message}` : 'Audit import failed', 'error') }
  }
  const createBackup = async () => {
    setSaving(true)
    try { const result = await post<typeof backup>('/system/backup'); setBackup(result); toast('SQLite backup and SHA-256 manifest created'); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Backup failed', 'error') }
    finally { setSaving(false) }
  }
  const auditCommand = `pwsh -ExecutionPolicy Bypass -File .\\scripts\\Invoke-SentinelAudit.ps1 -OutputPath .\\sentinel-pc-audit.json`
  const backupCommand = `pwsh -ExecutionPolicy Bypass -File .\\scripts\\Backup-Sentinel.ps1 -ProjectRoot D:\\Projects\\LIN4CRE-SENTINEL -BackupRoot E:\\AI\\SENTINEL\\backups`
  const setupCommand = `pwsh -ExecutionPolicy Bypass -File .\\scripts\\Initialize-Sentinel.ps1 -ProjectRoot D:\\Projects\\LIN4CRE-SENTINEL -DataRoot D:\\AI\\SENTINEL -ArchiveRoot E:\\AI\\SENTINEL -BackupManifest <verified-manifest.json>`
  return <>
    <PageHeader eyebrow="WORKSTATION, SAFETY & PROVENANCE" title="Setup with evidence, not assumptions." description="Audit the Windows host, verify recovery, connect local inference and inspect every upstream source before installing research tooling." />
    <div className="settings-layout"><nav className="settings-nav"><a href="#safety"><ShieldCheck size={16} />Safety controls</a><a href="#pc-audit"><Laptop size={16} />Windows audit</a><a href="#backups"><HardDrive size={16} />Backups & export</a><a href="#ai"><Server size={16} />Hybrid AI</a><a href="#sources"><BookOpenCheck size={16} />Verified sources</a></nav><div className="settings-content">
      <section className="panel settings-section" id="safety"><div className="settings-section-head"><div className="settings-icon"><ShieldCheck size={20} /></div><div><h2>Operating controls</h2><p>Fixed product policy and your immediate stop mechanism.</p></div></div>
        <div className="policy-grid"><div><span>AI strategy</span><strong>Hybrid · local first</strong><small>External AI disabled</small></div><div><span>Opportunity scope</span><strong>Cash only</strong><small>Hard eligibility gate</small></div><div><span>Autonomy</span><strong>Human approval</strong><small>Testing and submission</small></div><div><span>Spend ceiling</span><strong>£0</strong><small>No paid API provider configured</small></div></div>
        <div className="fixed-control"><div><CloudOff size={18} /><span><strong>Live testing engine</strong><small>Not installed or connected in milestone one</small></span></div><Badge value="Disabled" tone="muted" /></div><div className="fixed-control"><div><LockKeyhole size={18} /><span><strong>Autonomous submissions</strong><small>Not technically available</small></span></div><Badge value="Disabled" tone="muted" /></div>
        <div className={settings?.kill_switch ? 'kill-zone active' : 'kill-zone'}><div><ZapOff size={21} /><span><strong>{settings?.kill_switch ? 'Research is stopped' : 'Global kill switch'}</strong><small>{settings?.kill_switch ? 'All pending and active approvals were revoked.' : 'Immediately revokes every pending and active test approval.'}</small></span></div><Button variant={settings?.kill_switch ? 'secondary' : 'danger'} onClick={() => settings?.kill_switch ? saveSettings({ kill_switch: false }, 'Kill switch reset; approvals still require review') : setKillOpen(true)}>{settings?.kill_switch ? 'Reset kill switch' : 'Stop all research'}</Button></div>
      </section>
      <section className="panel settings-section" id="pc-audit"><div className="settings-section-head"><div className="settings-icon"><Laptop size={20} /></div><div><h2>Windows workstation audit</h2><p>Read-only inspection of your existing setup. No installs, restarts or configuration changes.</p></div><Badge value={(dashboard?.counts.pc_audits || 0) > 0 ? 'operational' : 'pending'} /></div>
        <Notice tone="warning">This workspace cannot see your Windows drives or current installations. Run the supplied script locally and import its actual JSON output; no audit result has been assumed.</Notice>
        <div className="setup-steps"><div><span>1</span><div><strong>Open PowerShell 7 in the project folder</strong><p>The script checks Windows, drives, Docker, WSL, Ollama, OpenCode, runtimes and Git worktrees.</p></div></div><div><span>2</span><div><strong>Run the read-only audit</strong><p>It writes only the JSON report you explicitly request.</p></div></div><div><span>3</span><div><strong>Import the resulting JSON below</strong><p>SENTINEL stores it locally for the machine-specific installation plan.</p></div></div></div>
        <div className="command-block"><TerminalSquare size={17} /><code>{auditCommand}</code><CopyButton text={auditCommand} /></div>
        <div className="settings-actions"><a className="button button-secondary" href="/downloads/Invoke-SentinelAudit.ps1" download><ArrowDownToLine size={16} />Download audit script</a><label className="button button-primary"><FileInput size={16} />Import actual audit JSON<input type="file" hidden accept=".json,application/json" onChange={e => importAudit(e.target.files?.[0])} /></label></div>
      </section>
      <section className="panel settings-section" id="backups"><div className="settings-section-head"><div className="settings-icon"><HardDrive size={20} /></div><div><h2>Backup, restore & data export</h2><p>Create consistent SQLite snapshots and preserve existing Windows configuration before setup.</p></div></div>
        <h3 className="settings-subhead">Existing workstation — before folder setup</h3><p className="settings-description">Backs up existing OpenCode/Ollama configuration, project files and Docker metadata to a new timestamped folder with SHA-256 manifest. It does not overwrite source files.</p><div className="command-block"><TerminalSquare size={17} /><code>{backupCommand}</code><CopyButton text={backupCommand} /></div><div className="settings-actions"><a className="button button-secondary" href="/downloads/Backup-Sentinel.ps1" download><Download size={16} />Backup script</a><a className="button button-secondary" href="/downloads/Initialize-Sentinel.ps1" download><FolderCheck size={16} />Guarded folder setup</a></div>
        <h3 className="settings-subhead">Guarded D: / E: folder creation</h3><div className="command-block"><TerminalSquare size={17} /><code>{setupCommand}</code><CopyButton text={setupCommand} /></div>
        <div className="backup-local"><div><Database size={19} /><span><strong>Current SENTINEL database</strong><small>Online SQLite backup plus SHA-256 sidecar. Restore requires stopping the application.</small></span></div><Button disabled={saving} onClick={createBackup} icon={<HardDrive size={16} />}>{saving ? 'Creating…' : 'Create verified backup'}</Button></div>
        {backup && <div className="backup-result"><CheckCircle2 size={19} /><div><strong>{backup.file}</strong><span>{backup.bytes.toLocaleString()} bytes · SHA-256 {backup.sha256}</span></div><button onClick={() => download(backup.download_url)}><Download size={16} /></button></div>}
        <label className="confirmation-check backup-confirm"><input type="checkbox" checked={!!settings?.setup_backup_verified} onChange={e => saveSettings({ setup_backup_verified: e.target.checked }, e.target.checked ? 'Backup verification recorded' : 'Backup verification cleared')} /><span>I have checked the backup manifest and recovery instructions for my workstation. This records my attestation; it does not claim SENTINEL tested a Windows restore.</span></label>
        <div className="settings-actions"><Button variant="secondary" icon={<FileJson size={16} />} onClick={() => download('/api/system/export')}>Export all local records (JSON)</Button></div>
      </section>
      <section className="panel settings-section" id="ai"><div className="settings-section-head"><div className="settings-icon"><Server size={20} /></div><div><h2>Hybrid AI — local first</h2><p>Verify your existing Ollama endpoint. No inference request is made until you test it.</p></div><Badge value={testResult?.connected ? 'operational' : 'pending'} /></div>
        <FormGrid><Field label="Ollama endpoint" full hint="Only localhost, 127.0.0.1 or host.docker.internal are accepted."><input value={ollamaUrl} onChange={e => setOllamaUrl(e.target.value)} /></Field></FormGrid>
        <div className="settings-actions"><Button variant="secondary" disabled={testing} icon={testing ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />} onClick={testOllama}>{testing ? 'Testing actual connection…' : 'Test Ollama connection'}</Button></div>
        {testResult && <div className={testResult.connected ? 'connection-result connected' : 'connection-result'}>{testResult.connected ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}<div><strong>{testResult.connected ? `Connected · ${testResult.models.length} installed model(s)` : 'No verified Ollama connection'}</strong><p>{testResult.connected ? 'Models reported by your actual endpoint are listed below.' : testResult.error || 'The endpoint did not respond. This is an unavailable connection, not a simulated success.'}</p></div></div>}
        {testResult?.connected && <Field label="Default local model" hint="Only models returned by your endpoint are listed"><select value={model} onChange={e => setModel(e.target.value)}><option value="">Select a verified installed model</option>{testResult.models.map(item => <option key={item.name} value={item.name}>{item.name}{item.size ? ` · ${(item.size / 1e9).toFixed(1)} GB` : ''}</option>)}</select></Field>}
        <div className="settings-actions"><Button disabled={saving || !model || !testResult?.connected} onClick={() => saveSettings({ ollama_url: ollamaUrl, ollama_model: model }, 'Verified local model configuration saved')}>Save local AI configuration</Button></div>
        <div className="external-ai"><div><CloudOff size={19} /><span><strong>Optional external AI is off</strong><small>No keys are stored, no data leaves this workspace and no paid calls can occur. Provider integration is deliberately deferred until current limits, privacy terms and free-model IDs are rechecked.</small></span></div><Badge value="rejected" /></div>
      </section>
      <section className="panel settings-section" id="sources"><div className="settings-section-head"><div className="settings-icon"><BookOpenCheck size={20} /></div><div><h2>Upstream repositories & policies</h2><p>Checked {date(sources?.checked_at)}. Verification of a source is not approval to deploy it.</p></div></div>
        <div className="repo-list">{sources?.repositories.map(repo => <article key={repo.name}><div className="repo-head"><div><strong>{repo.name}</strong><a href={repo.url} target="_blank" rel="noreferrer">{repo.repository}<ExternalLink size={12} /></a></div><Badge value={repo.status} /></div><p>{repo.role}</p><dl><div><dt>Cost</dt><dd>{repo.cost}</dd></div><div><dt>Caution</dt><dd>{repo.caution}</dd></div></dl></article>)}</div>
        <h3 className="settings-subhead">Platform & provider policy references</h3><div className="policy-sources">{sources?.policies.map(policy => <a key={policy.name} href={policy.url} target="_blank" rel="noreferrer"><BookOpenCheck size={17} /><div><strong>{policy.name}</strong><p>{policy.summary}</p><span>Checked {date(policy.checked_at)}</span></div><ExternalLink size={14} /></a>)}</div>
        <Notice><strong>No payout guarantee.</strong> Programme scope, platform rules, free-model quotas and prices can change. Re-check the current canonical source before every testing or spending decision.</Notice>
      </section>
    </div></div>
    {killOpen && <Modal title="Activate the global kill switch?" description="This is an immediate fail-closed action." onClose={() => setKillOpen(false)}><Notice tone="danger">Every pending and active test approval will be revoked. No new approval can be granted until you deliberately reset the switch.</Notice><div className="modal-actions"><Button variant="secondary" onClick={() => setKillOpen(false)}>Keep current state</Button><Button variant="danger" icon={<ZapOff size={16} />} onClick={async () => { await saveSettings({ kill_switch: true }, 'Kill switch activated; approvals revoked'); setKillOpen(false) }}>Stop all research</Button></div></Modal>}
  </>
}

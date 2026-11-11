import { useCallback, useEffect, useState } from 'react'
import { ArchiveRestore, CheckCircle2, ChevronRight, Clock3, Database, FileCheck2, FileJson, FolderCog, HardDrive, History, Loader2, Plus, RefreshCw, ShieldCheck } from 'lucide-react'
import { Operation, RecoveryPoint, operationsApi } from '../operations'
import { useToast } from '../ToastContext'
import { date, money } from '../utils'
import { Badge, Button, EmptyState, Field, Modal, Notice, PageHeader, StatCard } from '../components/UI'
import OperationCard from '../components/OperationCard'

function size(bytes: number) {
  if (!Number.isFinite(bytes)) return 'No Data Available'
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KiB`
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MiB`
  return `${(bytes / 1024 ** 3).toFixed(2)} GiB`
}

export default function Recovery() {
  const [points, setPoints] = useState<RecoveryPoint[]>([])
  const [operations, setOperations] = useState<Operation[]>([])
  const [busy, setBusy] = useState(false)
  const [verifying, setVerifying] = useState<string | null>(null)
  const [restorePoint, setRestorePoint] = useState<RecoveryPoint | null>(null)
  const [components, setComponents] = useState<string[]>(['database', 'files', 'config'])
  const toast = useToast()
  const refresh = useCallback(async () => {
    try { const [recovery, items] = await Promise.all([operationsApi.recovery(), operationsApi.list()]); setPoints(recovery); setOperations(items.filter(item => ['backup', 'restore'].includes(item.kind))) }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to load recovery data', 'error') }
  }, [toast])
  useEffect(() => { refresh() }, [refresh])
  const backup = async () => {
    setBusy(true)
    try { await operationsApi.backup(); toast('Recovery operation completed; review host-backup status'); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Backup failed', 'error') }
    finally { setBusy(false) }
  }
  const verify = async (point: RecoveryPoint) => {
    setVerifying(point.id)
    try { const result = await operationsApi.verifyRecovery(point.id); toast(result.status === 'verified' ? 'Every recovery file and database check passed' : 'Recovery point failed verification', result.status === 'verified' ? 'success' : 'error'); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Verification failed', 'error') }
    finally { setVerifying(null) }
  }
  const restore = async () => {
    if (!restorePoint) return
    setBusy(true)
    try { await operationsApi.restore(restorePoint.id, components); toast('Restore plan created; review the exact operation'); setRestorePoint(null); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Restore planning failed', 'error') }
    finally { setBusy(false) }
  }
  const latest = points.find(point => point.status === 'verified')
  const total = points.reduce((sum, point) => sum + point.size_bytes, 0)
  return <>
    <PageHeader eyebrow="BACKUP & DISASTER RECOVERY" title="A backup only counts when it verifies." description="Dated recovery points for the database, configuration, evidence and reports — with safety copies, selective restore and automatic rollback." actions={<Button icon={<Plus size={16} />} disabled={busy} onClick={backup}>{busy ? 'Creating & verifying…' : 'Back up everything'}</Button>} />
    <div className="stats-grid"><StatCard label="Recovery points" value={points.length} note="No automatic deletion of the last good copy" icon={<History size={19} />} /><StatCard label="Latest verified" value={latest ? date(latest.created_at) : 'No Data'} note={latest ? latest.label : 'Create and verify a recovery point'} icon={<ShieldCheck size={19} />} accent={!!latest} /><StatCard label="Recovery storage" value={size(total)} note="Measured manifest file totals" icon={<HardDrive size={19} />} /><StatCard label="Restore safety" value="Automatic" note="New safety point before every restore" icon={<ArchiveRestore size={19} />} /></div>
    <div className="recovery-principles"><div><Database size={18} /><span><strong>Database integrity checked</strong>SQLite online backup, integrity and foreign-key checks.</span></div><div><FileCheck2 size={18} /><span><strong>Every file hashed</strong>SHA-256 manifests detect missing, changed or corrupted content.</span></div><div><FolderCog size={18} /><span><strong>Credentials stay separate</strong>API keys, host tokens and model weights are not copied into plaintext backups.</span></div></div>
    {operations.filter(item => ['pending_approval', 'running', 'failed', 'partial'].includes(item.status)).slice(0, 3).map(item => <OperationCard key={item.id} operation={item} onChanged={refresh} />)}
    <section className="panel recovery-panel"><div className="panel-head"><div><span className="panel-kicker">DATED RECOVERY POINTS</span><h2>Choose a known-good state</h2></div><Button variant="ghost" size="sm" icon={<RefreshCw size={14} />} onClick={refresh}>Refresh</Button></div>
      {!points.length ? <EmptyState icon={<HardDrive size={25} />} title="No recovery points available" description="Create your first verified backup before installing, updating or repairing components. SENTINEL also creates safety points automatically before consequential operations." /> : <div className="recovery-list">{points.map(point => <article className="recovery-item" key={point.id}><div className="recovery-icon"><ArchiveRestore size={20} /></div><div className="recovery-info"><div><h3>{point.label}</h3><Badge value={point.status} dot /></div><span>{date(point.created_at, true)} · {point.kind.replaceAll('_', ' ')} · SENTINEL {point.source_version}</span><code>{point.id}</code><div className="recovery-includes">{point.includes.slice(0, 6).map(item => <span key={item}>{item}</span>)}{point.includes.length > 6 && <span>+{point.includes.length - 6} more</span>}</div></div><div className="recovery-size"><strong>{size(point.size_bytes)}</strong><span>{point.sha256.slice(0, 12)}…</span>{point.restored_at && <small>Restored {date(point.restored_at, true)}</small>}</div><div className="recovery-actions"><Button size="sm" variant="secondary" disabled={verifying === point.id} icon={verifying === point.id ? <Loader2 size={14} className="spin" /> : <CheckCircle2 size={14} />} onClick={() => verify(point)}>{verifying === point.id ? 'Verifying…' : 'Verify'}</Button><Button size="sm" disabled={point.status !== 'verified'} onClick={() => { setRestorePoint(point); setComponents(['database', 'files', 'config']) }}>Restore<ChevronRight size={14} /></Button></div></article>)}</div>}
    </section>
    <div className="recovery-footnote"><ShieldCheck size={16} /><p><strong>Restoration never starts from an unverified backup.</strong> A fresh safety point is created first. If database verification fails, SENTINEL attempts to restore that pre-restore state automatically.</p></div>
    {restorePoint && <Modal title="Choose what to restore" description={`${restorePoint.label} · ${date(restorePoint.created_at, true)}`} onClose={() => setRestorePoint(null)}>
      <Notice tone="warning">This creates a restore plan only. Nothing changes until you review and approve the operation. A new safety point will be created immediately before restoration.</Notice>
      <div className="restore-options">{[['database', 'Database & records', 'Programmes, research, settings, operations, reports and earnings'], ['files', 'Evidence & research files', 'Evidence, reports, research and other data folders'], ['config', 'Agent & application configuration', 'Non-secret agent settings, prompts and configuration files']].map(([id, title, description]) => <label key={id}><input type="checkbox" checked={components.includes(id)} onChange={() => setComponents(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id])} /><div><strong>{title}</strong><span>{description}</span></div></label>)}</div>
      <p className="credential-warning">Credentials and model weights are not restored from these recovery points. You will need to re-authorise them through the secured setup flow.</p>
      <div className="modal-actions"><Button variant="secondary" onClick={() => setRestorePoint(null)}>Cancel</Button><Button disabled={!components.length || busy} onClick={restore}>Create restore plan</Button></div>
    </Modal>}
  </>
}

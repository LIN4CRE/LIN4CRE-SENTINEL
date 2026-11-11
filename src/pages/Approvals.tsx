import { useState } from 'react'
import { Check, CheckCircle2, ChevronDown, ClipboardCheck, Clock3, FileKey2, Gauge, History, ShieldCheck, ShieldX, Target, X, XCircle, ZapOff } from 'lucide-react'
import { post } from '../api'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import type { Approval } from '../types'
import { date, label } from '../utils'
import { Badge, Button, EmptyState, Field, Modal, Notice, PageHeader } from '../components/UI'

export default function Approvals() {
  const { approvals, refresh, settings } = useData()
  const [decision, setDecision] = useState<{ approval: Approval; action: 'approved' | 'rejected' | 'revoked' } | null>(null)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [view, setView] = useState<'pending' | 'active' | 'history'>('pending')
  const toast = useToast()
  const pending = approvals.filter(item => item.status === 'pending')
  const active = approvals.filter(item => item.status === 'approved' && new Date(item.expires_at) > new Date())
  const history = approvals.filter(item => !pending.includes(item) && !active.includes(item))
  const visible = view === 'pending' ? pending : view === 'active' ? active : history
  const submit = async () => {
    if (!decision) return
    setSaving(true)
    try { await post(`/approvals/${decision.approval.id}/decision`, { decision: decision.action, note }); toast(`Test approval ${decision.action}`); setDecision(null); setNote(''); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to record decision', 'error') }
    finally { setSaving(false) }
  }
  const openDecision = (approval: Approval, action: 'approved' | 'rejected' | 'revoked') => { setDecision({ approval, action }); setNote('') }
  return <>
    <PageHeader eyebrow="HUMAN AUTHORISATION" title="Your approval is the execution boundary." description="Review exact assets, methods, request limits and expiry. Approval creates an audit record — it does not launch a scan." />
    {settings?.kill_switch && <Notice tone="danger"><strong>The global kill switch is active.</strong> New approvals are blocked until you deliberately reset it in Setup & sources.</Notice>}
    <div className="approval-summary"><div><ClipboardCheck size={20} /><span>Awaiting decision<strong>{pending.length}</strong></span></div><div><ShieldCheck size={20} /><span>Active envelopes<strong>{active.length}</strong></span></div><div><History size={20} /><span>Decision history<strong>{history.length}</strong></span></div><p><ShieldX size={17} />Destructive testing, data extraction and autonomous submission are outside this system’s authority.</p></div>
    <div className="filter-tabs approval-tabs">{([['pending', `Pending (${pending.length})`], ['active', `Active (${active.length})`], ['history', `History (${history.length})`]] as const).map(([value, text]) => <button key={value} className={view === value ? 'active' : ''} onClick={() => setView(value)}>{text}</button>)}</div>
    {visible.length === 0 ? <section className="panel"><EmptyState icon={<FileKey2 size={25} />} title={view === 'pending' ? 'No approval requests' : view === 'active' ? 'No active test approvals' : 'No decision history yet'} description={view === 'pending' ? 'Open an eligible programme and select exact in-scope assets to request a time-limited test approval.' : 'Approval records will appear here when a real request matches this view.'} /></section> : <div className="approval-list">{visible.map(approval => {
      const expired = new Date(approval.expires_at) <= new Date()
      return <article className="panel approval-card" key={approval.id}>
        <div className="approval-card-head"><div><div className="approval-id">APR-{approval.id.slice(0, 8).toUpperCase()}</div><h2>{approval.programme_name}</h2><span>{approval.platform} · requested {date(approval.requested_at, true)}</span></div><Badge value={expired && approval.status === 'approved' ? 'revoked' : approval.status} dot /></div>
        <div className="approval-envelope"><section><h3><Target size={15} />Authorised assets</h3><div className="asset-list">{approval.assets.map(asset => <code key={asset}>{asset}</code>)}</div></section><section><h3><CheckCircle2 size={15} />Permitted methods</h3><ul className="method-list">{approval.methods.map(method => <li key={method}>{label(method)}</li>)}</ul></section></div>
        <div className="approval-meta"><span><Gauge size={15} /><b>{approval.rate_limit}</b> request{approval.rate_limit === 1 ? '' : 's'} / second maximum</span><span><Clock3 size={15} />{expired ? 'Expired ' : 'Expires '}{date(approval.expires_at, true)}</span><span title={approval.scope_hash}><ShieldCheck size={15} />Scope hash {approval.scope_hash.slice(0, 10)}…</span></div>
        {approval.decision_note && <div className="decision-note"><strong>Decision note</strong><p>{approval.decision_note}</p></div>}
        {approval.status === 'pending' && <div className="approval-actions"><Button variant="secondary" icon={<X size={16} />} onClick={() => openDecision(approval, 'rejected')}>Reject request</Button><Button disabled={settings?.kill_switch} icon={<Check size={16} />} onClick={() => openDecision(approval, 'approved')}>Review & approve</Button></div>}
        {approval.status === 'approved' && !expired && <div className="approval-actions"><span className="no-execution"><ShieldCheck size={14} />No live testing engine connected</span><Button variant="danger" size="sm" icon={<ZapOff size={15} />} onClick={() => openDecision(approval, 'revoked')}>Revoke now</Button></div>}
      </article>
    })}</div>}
    {decision && <Modal title={`${decision.action === 'approved' ? 'Approve' : decision.action === 'rejected' ? 'Reject' : 'Revoke'} test request?`} description={`${decision.approval.programme_name} · APR-${decision.approval.id.slice(0, 8).toUpperCase()}`} onClose={() => setDecision(null)}>
      {decision.action === 'approved' ? <Notice tone="warning">By approving, you confirm that you have personally checked the current programme policy, every listed asset is eligible, and every selected method is permitted. No testing is started by this action.</Notice> : <Notice>This decision will be written to the append-only audit trail.</Notice>}
      <div className="decision-recap"><span>{decision.approval.assets.length} exact assets</span><span>{decision.approval.methods.length} methods</span><span>{decision.approval.rate_limit} req/s maximum</span></div>
      <Field label="Decision note" hint="Optional, but recommended for future compliance review"><textarea rows={4} value={note} onChange={e => setNote(e.target.value)} placeholder="Policy checks, constraints or reason for this decision…" /></Field>
      <div className="modal-actions"><Button variant="secondary" onClick={() => setDecision(null)}>Cancel</Button><Button variant={decision.action === 'approved' ? 'primary' : 'danger'} disabled={saving} onClick={submit}>{saving ? 'Recording…' : `Confirm ${decision.action}`}</Button></div>
    </Modal>}
  </>
}

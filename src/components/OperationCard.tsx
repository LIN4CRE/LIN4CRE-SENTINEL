import { useState } from 'react'
import { AlertTriangle, ArrowRight, Check, CheckCircle2, ChevronDown, ChevronRight, Clock3, Loader2, LockKeyhole, Play, RefreshCw, ShieldCheck, X, XCircle } from 'lucide-react'
import { Operation, operationPlanHash, operationsApi } from '../operations'
import { useToast } from '../ToastContext'
import { date, label } from '../utils'
import { Badge, Button, Modal, Notice } from './UI'

export function PlanDetails({ operation }: { operation: Operation }) {
  const plan = operation.plan
  return <div className="operation-plan">
    {plan.recovery_point_id && <div className="plan-recovery"><span>Recovery point</span><code>{plan.recovery_point_id}</code></div>}
    {plan.components && <div className="plan-recovery"><span>Components to restore</span><strong>{plan.components.join(', ')}</strong></div>}
    {plan.actions?.map((action, index) => <div className="plan-action" key={`${action.action}-${index}`}><span>{index + 1}</span><div><strong>{label(action.action)}</strong><p>{action.component || action.model || 'SENTINEL core / registered host action'}</p>{action.version && <code>{action.previous_version || 'Not installed'} → {action.version}</code>}{action.patch && <details className="patch-review"><summary>Review complete proposed diff</summary><pre>{action.patch}</pre></details>}</div>{action.action === 'install_wsl' && <Badge value="admin required" tone="amber" />}</div>)}
    {plan.rollback_plan && <div className="rollback-note"><ShieldCheck size={14} />A registered rollback plan is included if verification fails.</div>}
  </div>
}

export default function OperationCard({ operation, onChanged, compact = false }: { operation: Operation; onChanged: () => void; compact?: boolean }) {
  const [approvalOpen, setApprovalOpen] = useState(false)
  const [expanded, setExpanded] = useState(!compact)
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const toast = useToast()
  const approve = async () => {
    setBusy(true)
    try {
      const hash = await operationPlanHash(operation.plan)
      await operationsApi.approve(operation.id, hash)
      toast('Approved plan started; verification will follow')
      setApprovalOpen(false); setConfirmed(false); onChanged()
    } catch (error) { toast(error instanceof Error ? error.message : 'Approval failed', 'error') }
    finally { setBusy(false) }
  }
  const retry = async () => {
    setBusy(true)
    try { await operationsApi.retry(operation.id); toast('A fresh approval request was created'); onChanged() }
    catch (error) { toast(error instanceof Error ? error.message : 'Retry failed', 'error') }
    finally { setBusy(false) }
  }
  const cancel = async () => {
    setBusy(true)
    try { await operationsApi.cancel(operation.id); toast('Pending operation cancelled'); onChanged() }
    catch (error) { toast(error instanceof Error ? error.message : 'Cancel failed', 'error') }
    finally { setBusy(false) }
  }
  const running = ['running', 'queued'].includes(operation.status)
  return <article className={`operation-card operation-${operation.status}`}>
    <div className="operation-card-head"><div className={`operation-kind operation-kind-${operation.kind}`}><LockKeyhole size={16} /></div><div className="operation-title"><div><span>{label(operation.kind)}</span><code>OP-{operation.id.slice(0, 8).toUpperCase()}</code></div><h3>{operation.title}</h3><small>{date(operation.created_at, true)}</small></div><Badge value={operation.status} dot={running} /><button className="operation-expand" onClick={() => setExpanded(!expanded)} aria-label="Toggle operation details">{expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button></div>
    <div className="operation-description">{operation.description}</div>
    {running && <div className="operation-progress"><Loader2 size={15} className="spin" /><span>{operation.status === 'queued' ? 'Approved — waiting to start' : 'Executing the signed plan and verifying real results…'}</span><div><i /></div></div>}
    {expanded && <>
      <PlanDetails operation={operation} />
      {operation.error && <Notice tone="danger"><strong>Operation failed</strong><br />{operation.error}</Notice>}
      {operation.result && <div className="operation-result"><h4>Actual result</h4>{operation.result.message && <p>{operation.result.message}</p>}{operation.result.host_backup_error && <Notice tone="warning">Host configuration backup was unavailable: {operation.result.host_backup_error}</Notice>}{operation.result.rollback_performed && <Notice tone="warning">The update failed verification and a rollback was performed. Check the recorded result before retrying.</Notice>}{operation.verification && <div className="verification-list">{operation.verification.map((item, index) => <div key={index}>{item.verified ? <CheckCircle2 size={14} /> : <XCircle size={14} />}<span>{item.component || item.model || `Check ${index + 1}`}</span><strong>{item.verified ? 'Verified' : 'Failed'}</strong></div>)}</div>}<details><summary>Technical result</summary><pre>{JSON.stringify(operation.result, null, 2)}</pre></details></div>}
    </>}
    <div className="operation-footer"><span>{operation.risk.replaceAll('_', ' ')} · {operation.rollback_available ? 'rollback available' : 'no automatic rollback'}</span><div>{operation.status === 'failed' && <Button size="sm" variant="secondary" icon={<RefreshCw size={14} />} disabled={busy} onClick={retry}>Retry with new approval</Button>}{operation.status === 'pending_approval' && <><Button size="sm" variant="ghost" disabled={busy} onClick={cancel}>Cancel</Button><Button size="sm" icon={<Play size={14} />} onClick={() => setApprovalOpen(true)}>Review & approve</Button></>}{operation.status === 'succeeded' && <span className="operation-complete"><Check size={14} />Verified complete</span>}</div></div>
    {approvalOpen && <Modal title="Approve this exact operation?" description={`${operation.title} · OP-${operation.id.slice(0, 8).toUpperCase()}`} onClose={() => setApprovalOpen(false)}>
      <Notice tone={operation.risk === 'data_restore' ? 'danger' : 'warning'}><strong>{operation.risk === 'data_restore' ? 'This changes restored data.' : 'This changes your system.'}</strong> The AI cannot execute this plan until you approve it. A recovery point is created before host changes.</Notice>
      <PlanDetails operation={operation} />
      <div className="approval-facts"><div><span>Permission role</span><strong>{operation.approval_role}</strong></div><div><span>Cost added by SENTINEL</span><strong>£0</strong></div><div><span>Rollback</span><strong>{operation.rollback_available ? 'Registered where available' : 'Not guaranteed'}</strong></div></div>
      {operation.plan.actions?.some(action => ['install_component', 'install_wsl'].includes(action.action)) && <p className="admin-explanation"><AlertTriangle size={15} />Windows may display a UAC prompt if a component requires administrator access. This is needed only for Windows services, features, networking or shared runtimes. No reboot will be requested automatically.</p>}
      <label className="confirmation-check"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I have reviewed every action, understand the risk and authorise this exact plan. I know approval does not guarantee installer success.</span></label>
      <div className="modal-actions"><Button variant="secondary" onClick={() => setApprovalOpen(false)}>Do not run</Button><Button disabled={!confirmed || busy} onClick={approve} icon={<ShieldCheck size={16} />}>{busy ? 'Authorising…' : 'Approve & run'}</Button></div>
    </Modal>}
  </article>
}

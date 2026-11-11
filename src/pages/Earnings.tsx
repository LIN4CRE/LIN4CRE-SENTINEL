import { FormEvent, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BadgePoundSterling, CircleDollarSign, Clock3, FileCheck2, Landmark, Plus, ReceiptText, ShieldCheck, WalletCards } from 'lucide-react'
import { post } from '../api'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import { date, label, money } from '../utils'
import { Badge, Button, EmptyState, Field, FormGrid, Modal, Notice, PageHeader, StatCard } from '../components/UI'

export default function Earnings() {
  const { payments, reports, dashboard, refresh } = useData()
  const [params, setParams] = useSearchParams()
  const [open, setOpen] = useState(params.get('new') === '1')
  const accepted = reports.filter(item => ['accepted', 'resolved'].includes(item.status))
  const [form, setForm] = useState({ report_id: accepted[0]?.id || '', amount: '', currency: 'GBP', status: 'awarded', awarded_at: '', paid_at: '', reference: '', notes: '' })
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const totals = (status: string) => payments.filter(item => item.status === status).reduce<Record<string, number>>((acc, item) => ({ ...acc, [item.currency]: (acc[item.currency] || 0) + item.amount }), {})
  const displayTotals = (status: string, empty = '£0.00') => { const values = totals(status); const entries = Object.entries(values); return entries.length ? entries.map(([currency, amount]) => money(amount, currency, 2)).join(' · ') : empty }
  const close = () => { setOpen(false); if (params.has('new')) { params.delete('new'); setParams(params, { replace: true }) } }
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setSaving(true)
    try { await post(`/reports/${form.report_id}/payments`, { ...form, amount: Number(form.amount) }); toast(`Actual ${form.status} bounty recorded`); close(); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to record bounty', 'error') }
    finally { setSaving(false) }
  }
  return <>
    <PageHeader eyebrow="FINANCIAL SOURCE OF TRUTH" title="Earnings are real, or they are zero." description="Track programme decisions, awarded bounties and money actually received. No projected income is mixed into these totals." actions={<Button icon={<Plus size={16} />} disabled={!accepted.length} onClick={() => setOpen(true)}>Record actual bounty</Button>} />
    <div className="stats-grid earnings-stats"><StatCard label="Paid to you" value={displayTotals('paid')} note={`${payments.filter(item => item.status === 'paid').length} verified payment record(s)`} icon={<Landmark size={19} />} accent /><StatCard label="Awarded, unpaid" value={displayTotals('awarded')} note="Programme award entries only" icon={<Clock3 size={19} />} /><StatCard label="Accepted reports" value={dashboard?.counts.accepted_reports ?? 0} note="Accepted or resolved externally" icon={<FileCheck2 size={19} />} /><StatCard label="Submitted reports" value={dashboard?.counts.submitted_reports ?? 0} note="Human-recorded submissions" icon={<ReceiptText size={19} />} /></div>
    {!accepted.length && <Notice>Record a bounty only after updating a report to the programme’s actual <strong>Accepted</strong> or <strong>Resolved</strong> decision.</Notice>}
    <section className="panel earnings-panel"><div className="panel-head"><div><span className="panel-kicker">BOUNTY LEDGER</span><h2>Awards & payments</h2></div><span className="live-db"><ShieldCheck size={14} />Actual entries only</span></div>
      {!payments.length ? <EmptyState icon={<WalletCards size={25} />} title="No bounty data available" description="No income is claimed. Accepted reports, awards and paid amounts will appear here only after you enter their actual platform outcomes." /> : <div className="responsive-table"><table className="data-table"><thead><tr><th>Report</th><th>Programme</th><th>Status</th><th>Amount</th><th>Awarded</th><th>Paid</th><th>Reference</th></tr></thead><tbody>{payments.map(payment => <tr key={payment.id}><td><strong>{payment.title}</strong><small className="table-sub">{payment.platform_report_id || `Report ${payment.report_id.slice(0, 8)}`}</small></td><td>{payment.programme_name}</td><td><Badge value={payment.status} dot /></td><td><strong className="table-money">{money(payment.amount, payment.currency, 2)}</strong></td><td>{date(payment.awarded_at)}</td><td>{date(payment.paid_at)}</td><td>{payment.reference || '—'}</td></tr>)}</tbody></table></div>}
    </section>
    <div className="finance-notes"><article><CircleDollarSign size={18} /><div><h3>Expected value is not earnings</h3><p>Opportunity scores and estimated return per hour never appear in this ledger.</p></div></article><article><BadgePoundSterling size={18} /><div><h3>Multi-currency totals stay separate</h3><p>SENTINEL does not invent exchange rates or silently convert award amounts.</p></div></article></div>
    {open && <Modal title="Record actual bounty" description="Enter the programme’s real award or payment outcome. This is not a payout forecast." onClose={close}>
      {!accepted.length ? <Notice tone="warning">No accepted or resolved reports are available.</Notice> : <form onSubmit={submit}>
        <Field label="Accepted report" required full><select required value={form.report_id} onChange={e => setForm({ ...form, report_id: e.target.value })}>{accepted.map(report => <option key={report.id} value={report.id}>{report.title} · {report.programme_name}</option>)}</select></Field>
        <FormGrid><Field label="Amount" required><input type="number" min="0.01" step="0.01" required value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} /></Field><Field label="Currency" required><select value={form.currency} onChange={e => setForm({ ...form, currency: e.target.value })}><option>GBP</option><option>USD</option><option>EUR</option></select></Field><Field label="Ledger state" required><select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}><option value="awarded">Awarded by programme</option><option value="paid">Actually paid</option></select></Field><Field label="Award date"><input type="date" value={form.awarded_at} onChange={e => setForm({ ...form, awarded_at: e.target.value })} /></Field>{form.status === 'paid' && <Field label="Actual payment date" required><input type="date" required value={form.paid_at} onChange={e => setForm({ ...form, paid_at: e.target.value })} /></Field>}<Field label="Payment / bounty reference"><input value={form.reference} onChange={e => setForm({ ...form, reference: e.target.value })} /></Field><Field label="Notes" full><textarea rows={3} value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></Field></FormGrid>
        <div className="modal-actions"><Button type="button" variant="secondary" onClick={close}>Cancel</Button><Button disabled={saving || !form.report_id} type="submit">{saving ? 'Recording…' : 'Record actual bounty'}</Button></div>
      </form>}
    </Modal>}
  </>
}

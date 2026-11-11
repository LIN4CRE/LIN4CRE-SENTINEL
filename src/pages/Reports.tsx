import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowDownToLine, CheckCircle2, ChevronRight, CircleDollarSign, ExternalLink, FileCheck2, FileText, Send, ShieldCheck } from 'lucide-react'
import { download, patch } from '../api'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import type { Report } from '../types'
import { date, label } from '../utils'
import { Badge, Button, EmptyState, Field, FormGrid, Modal, Notice, PageHeader } from '../components/UI'

const statuses = ['draft', 'ready', 'submitted', 'triaged', 'accepted', 'resolved', 'duplicate', 'informative', 'not_applicable', 'rejected']
export default function Reports() {
  const { reports, refresh } = useData()
  const [selected, setSelected] = useState<Report | null>(null)
  const [updating, setUpdating] = useState<Report | null>(null)
  const [status, setStatus] = useState('draft')
  const [platformId, setPlatformId] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [saving, setSaving] = useState(false)
  const [filter, setFilter] = useState('all')
  const toast = useToast(); const navigate = useNavigate()
  const visible = reports.filter(item => filter === 'all' || (filter === 'decided' ? ['accepted', 'resolved', 'duplicate', 'informative', 'not_applicable', 'rejected'].includes(item.status) : item.status === filter))
  const openUpdate = (report: Report) => { setUpdating(report); setStatus(report.status); setPlatformId(report.platform_report_id); setConfirmed(false); setSelected(null) }
  const save = async () => {
    if (!updating) return; setSaving(true)
    try { await patch(`/reports/${updating.id}`, { status, platform_report_id: platformId, human_confirmation: confirmed }); toast('External report status recorded'); setUpdating(null); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to update report', 'error') }
    finally { setSaving(false) }
  }
  return <>
    <PageHeader eyebrow="EVIDENCE-BACKED DISCLOSURE" title="Reports you can stand behind." description="Generated only from human-validated records. SENTINEL prepares and exports; you review and submit on the programme platform." />
    <div className="report-principles"><div><ShieldCheck size={18} /><span><strong>Human validation required</strong>No draft can bypass the evidence lock.</span></div><div><Send size={18} /><span><strong>No autonomous submission</strong>External submission is always your action.</span></div><div><FileText size={18} /><span><strong>AI-use transparency</strong>Research disclosures remain in the report.</span></div></div>
    <div className="filter-tabs report-tabs">{['all', 'draft', 'ready', 'submitted', 'accepted', 'decided'].map(value => <button className={filter === value ? 'active' : ''} key={value} onClick={() => setFilter(value)}>{value === 'all' ? `All (${reports.length})` : label(value)}</button>)}</div>
    {!visible.length ? <section className="panel"><EmptyState icon={<FileCheck2 size={25} />} title={reports.length ? 'No reports in this view' : 'No reports generated'} description={reports.length ? 'Choose another report status.' : 'A report becomes available only after a real research record has complete evidence and your explicit validation.'} action={!reports.length && <Button variant="secondary" onClick={() => navigate('/research')}>Open research records</Button>} /></section> : <section className="panel report-list"><div className="responsive-table"><table className="data-table"><thead><tr><th>Report</th><th>Programme</th><th>Severity</th><th>Status</th><th>Last updated</th><th></th></tr></thead><tbody>{visible.map(report => <tr key={report.id} onClick={() => setSelected(report)}><td><div className="report-title"><FileText size={17} /><div><strong>{report.title}</strong><span>{report.platform_report_id || `Local ID ${report.id.slice(0, 8)}`}</span></div></div></td><td>{report.programme_name}<small className="table-sub">{report.platform}</small></td><td><Badge value={report.severity || 'unrated'} /></td><td><Badge value={report.status} dot /></td><td>{date(report.updated_at, true)}</td><td><ChevronRight size={16} /></td></tr>)}</tbody></table></div></section>}
    {selected && <Modal title={selected.title || 'Report'} description={`${selected.programme_name} · ${selected.platform}`} onClose={() => setSelected(null)} wide>
      <div className="report-detail-head"><Badge value={selected.status} dot /><span>Local report {selected.id.slice(0, 8)}</span><span>Updated {date(selected.updated_at, true)}</span></div>
      {['duplicate', 'informative', 'not_applicable', 'rejected'].includes(selected.status) && <Notice tone="warning">This programme decision is recorded for learning and reporting accuracy. It is not counted as an accepted vulnerability or income.</Notice>}
      <pre className="report-content">{selected.content_md}</pre>
      <div className="modal-actions"><Button variant="secondary" icon={<ArrowDownToLine size={16} />} onClick={() => download(`/api/reports/${selected.id}/download`)}>Download Markdown</Button><Button onClick={() => openUpdate(selected)}>Record external status</Button>{['accepted', 'resolved'].includes(selected.status) && <Button icon={<CircleDollarSign size={16} />} onClick={() => navigate('/earnings?new=1')}>Record bounty</Button>}</div>
    </Modal>}
    {updating && <Modal title="Record external report status" description="This does not contact HackerOne, Intigriti, Bugcrowd or any programme." onClose={() => setUpdating(null)}>
      <Notice>Update this record only from the actual programme platform. SENTINEL has no submission integration and never assumes a programme decision.</Notice>
      <FormGrid><Field label="Actual platform status" required><select value={status} onChange={e => setStatus(e.target.value)}>{statuses.map(value => <option key={value} value={value}>{label(value)}</option>)}</select></Field><Field label="Platform report ID / URL slug"><input value={platformId} onChange={e => setPlatformId(e.target.value)} placeholder="Recorded after external submission" /></Field></FormGrid>
      {status === 'submitted' && <label className="confirmation-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /><span>I confirm that I personally reviewed this report and submitted it on the programme platform.</span></label>}
      <div className="modal-actions"><Button variant="secondary" onClick={() => setUpdating(null)}>Cancel</Button><Button disabled={saving || (status === 'submitted' && !confirmed)} onClick={save}>{saving ? 'Recording…' : 'Record actual status'}</Button></div>
    </Modal>}
  </>
}

import { FormEvent, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, CheckCircle2, ChevronRight, ClipboardCheck, FileCheck2, FileText, FlaskConical, LockKeyhole, Plus, ShieldCheck, Target } from 'lucide-react'
import { patch, post } from '../api'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import type { Finding } from '../types'
import { date, label } from '../utils'
import { Badge, Button, EmptyState, Field, FormGrid, FormSection, Modal, Notice, PageHeader } from '../components/UI'

const blank = { programme_id: '', title: '', asset: '', vulnerability_class: '', severity: 'unrated', summary: '', reproduction_steps: '', impact: '', evidence: '', remediation: '', ai_disclosure: '' }

function FindingForm({ initial, onClose, onSaved }: { initial: Finding | null; onClose: () => void; onSaved: () => void }) {
  const { programmes, approvals } = useData()
  const activeApprovals = approvals.filter(item => item.status === 'approved' && new Date(item.expires_at) > new Date())
  const approvedIds = [...new Set(activeApprovals.map(item => item.programme_id))]
  const available = programmes.filter(item => approvedIds.includes(item.id))
  const [form, setForm] = useState(initial ? { ...initial } as typeof blank : { ...blank, programme_id: available[0]?.id || '' })
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const programme = programmes.find(item => item.id === form.programme_id)
  const approvedAssets = activeApprovals.filter(item => item.programme_id === form.programme_id).flatMap(item => item.assets)
  const assets = initial ? [initial.asset] : [...new Set(approvedAssets)]
  const set = (key: keyof typeof blank, value: string) => setForm(current => ({ ...current, [key]: value }))
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setSaving(true)
    try {
      if (initial) await patch(`/findings/${initial.id}`, { title: form.title, vulnerability_class: form.vulnerability_class, severity: form.severity, summary: form.summary, reproduction_steps: form.reproduction_steps, impact: form.impact, evidence: form.evidence, remediation: form.remediation, ai_disclosure: form.ai_disclosure })
      else await post('/findings', form)
      toast(initial ? 'Research evidence updated' : 'Research record created as a draft'); onSaved()
    } catch (error) { toast(error instanceof Error ? error.message : 'Unable to save research', 'error') }
    finally { setSaving(false) }
  }
  return <Modal title={initial ? 'Update research evidence' : 'Create research record'} description="Record only actual observations and evidence. Findings begin unvalidated." onClose={onClose} wide>
    {!initial && <Notice><ClipboardCheck size={16} /> Only assets covered by a current human test approval can be selected. This control is enforced by the backend.</Notice>}
    <form onSubmit={submit}>
      <FormSection title="Finding identity"><FormGrid>
        <Field label="Programme" required><select required disabled={!!initial} value={form.programme_id} onChange={e => { set('programme_id', e.target.value); set('asset', '') }}>{available.map(item => <option value={item.id} key={item.id}>{item.name} · {item.platform}</option>)}{initial && <option value={initial.programme_id}>{initial.programme_name}</option>}</select></Field>
        <Field label="Exact approved asset" required><select required disabled={!!initial} value={form.asset} onChange={e => set('asset', e.target.value)}><option value="">Select an asset</option>{assets.map(asset => <option key={asset}>{asset}</option>)}</select></Field>
        <Field label="Finding title" required full><input required value={form.title} onChange={e => set('title', e.target.value)} placeholder="Specific vulnerability and affected component" /></Field>
        <Field label="Vulnerability class" required><input required value={form.vulnerability_class} onChange={e => set('vulnerability_class', e.target.value)} placeholder="e.g. Access control" /></Field>
        <Field label="Researcher severity assessment"><select value={form.severity} onChange={e => set('severity', e.target.value)}><option value="unrated">Unrated</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></Field>
      </FormGrid></FormSection>
      <FormSection title="Observed security issue"><Field label="Summary" full><textarea rows={4} value={form.summary} onChange={e => set('summary', e.target.value)} placeholder="What you directly observed; avoid generic AI-generated descriptions." /></Field><Field label="Reproduction steps" full><textarea rows={6} value={form.reproduction_steps} onChange={e => set('reproduction_steps', e.target.value)} placeholder={'1. Actual first step\n2. Actual second step\n3. Observed result'} /></Field></FormSection>
      <FormSection title="Proof & impact"><Field label="Security impact" full><textarea rows={4} value={form.impact} onChange={e => set('impact', e.target.value)} placeholder="Specific, demonstrated impact without data theft or unnecessary access." /></Field><Field label="Evidence" full hint="Redact secrets and unnecessary personal data. Reference locally stored evidence precisely."><textarea rows={6} value={form.evidence} onChange={e => set('evidence', e.target.value)} placeholder="Observed requests/responses, screenshots or local evidence references…" /></Field><Field label="Suggested remediation" full><textarea rows={3} value={form.remediation} onChange={e => set('remediation', e.target.value)} /></Field><Field label="AI-use disclosure" full hint="Describe any AI assistance accurately; platform rules may require disclosure."><textarea rows={3} value={form.ai_disclosure} onChange={e => set('ai_disclosure', e.target.value)} placeholder="Tools used, how output was verified, and what you personally tested." /></Field></FormSection>
      <div className="modal-actions"><Button variant="secondary" type="button" onClick={onClose}>Cancel</Button><Button type="submit" disabled={saving || (!initial && !available.length)} icon={<FlaskConical size={16} />}>{saving ? 'Saving…' : 'Save research record'}</Button></div>
    </form>
  </Modal>
}

export default function Research() {
  const { findings, programmes, approvals, settings, refresh } = useData()
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Finding | null>(null)
  const [selected, setSelected] = useState<Finding | null>(null)
  const [validating, setValidating] = useState<Finding | null>(null)
  const [name, setName] = useState(settings?.researcher_name || '')
  const [confirmed, setConfirmed] = useState(false)
  const [saving, setSaving] = useState(false)
  const [filter, setFilter] = useState('all')
  const toast = useToast(); const navigate = useNavigate()
  const active = approvals.filter(item => item.status === 'approved' && new Date(item.expires_at) > new Date())
  const visible = findings.filter(item => filter === 'all' || item.status === filter)
  const saved = async () => { setFormOpen(false); setEditing(null); setSelected(null); await refresh() }
  const validate = async () => {
    if (!validating) return; setSaving(true)
    try { await post(`/findings/${validating.id}/validate`, { researcher_name: name, confirmed }); toast('Finding human-validated and evidence-locked'); setValidating(null); setConfirmed(false); await refresh() }
    catch (error) { toast(error instanceof Error ? error.message : 'Validation failed', 'error') }
    finally { setSaving(false) }
  }
  const generate = async (finding: Finding) => {
    try { await post(`/findings/${finding.id}/report`); toast('Report generated from validated evidence'); await refresh(); navigate('/reports') }
    catch (error) { toast(error instanceof Error ? error.message : 'Report generation failed', 'error') }
  }
  return <>
    <PageHeader eyebrow="EVIDENCE-LED RESEARCH" title="Research records, not vulnerability claims." description="Capture direct observations under an active approval. Only complete, personally reproduced evidence can be human-validated." actions={<Button icon={<Plus size={16} />} disabled={!active.length} onClick={() => setFormOpen(true)}>New research record</Button>} />
    {!active.length && <Notice tone="warning"><strong>No active test approval.</strong> Request and approve exact scope before creating a research record. <button className="notice-link" onClick={() => navigate('/opportunities')}>Open opportunities</button></Notice>}
    <div className="research-stats"><div><span>Research records</span><strong>{findings.length}</strong></div><div><span>In investigation</span><strong>{findings.filter(item => item.status === 'investigating' || item.status === 'draft').length}</strong></div><div><span>Human validated</span><strong>{findings.filter(item => item.status === 'validated').length}</strong></div><div><span>Active approvals</span><strong>{active.length}</strong></div></div>
    <div className="filter-tabs research-tabs">{['all', 'draft', 'investigating', 'validated', 'rejected'].map(value => <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>{value === 'all' ? 'All records' : label(value)}</button>)}</div>
    {!visible.length ? <section className="panel"><EmptyState icon={<FlaskConical size={25} />} title={findings.length ? 'No records in this state' : 'No findings recorded'} description={findings.length ? 'Choose another research status.' : 'No vulnerabilities are claimed. Create a record only after authorised research produces actual observations.'} /></section> : <div className="finding-grid">{visible.map(finding => <button className="panel finding-card" key={finding.id} onClick={() => setSelected(finding)}><div className="finding-card-top"><Badge value={finding.status} dot /><Badge value={finding.severity} /></div><h2>{finding.title}</h2><p>{finding.programme_name}</p><code><Target size={13} />{finding.asset}</code><div className="finding-card-foot"><span>{finding.vulnerability_class}</span><span>{date(finding.updated_at)}<ChevronRight size={15} /></span></div></button>)}</div>}
    {(formOpen || editing) && <FindingForm initial={editing} onClose={() => { setFormOpen(false); setEditing(null) }} onSaved={saved} />}
    {selected && <Modal title={selected.title} description={`${selected.programme_name} · ${selected.vulnerability_class}`} onClose={() => setSelected(null)} wide>
      <div className="finding-detail-status"><Badge value={selected.status} dot /><Badge value={selected.severity} /><span><Target size={14} />{selected.asset}</span></div>
      {selected.status === 'validated' && <Notice tone="success"><strong>Human validated</strong> by {selected.validated_by} on {date(selected.validated_at, true)}. Evidence fields are locked to preserve report integrity.</Notice>}
      <div className="evidence-sections">{[['Summary', selected.summary], ['Reproduction steps', selected.reproduction_steps], ['Security impact', selected.impact], ['Evidence', selected.evidence], ['Suggested remediation', selected.remediation], ['AI-use disclosure', selected.ai_disclosure]].map(([title, content]) => <section key={title}><h3>{title}</h3><pre className={!content ? 'not-provided' : ''}>{content || 'Not provided.'}</pre></section>)}</div>
      <div className="modal-actions"><Button variant="secondary" onClick={() => setSelected(null)}>Close</Button>{selected.status !== 'validated' && selected.status !== 'rejected' && <><Button variant="secondary" onClick={() => { setEditing(selected); setSelected(null) }}>Edit evidence</Button><Button icon={<ShieldCheck size={16} />} onClick={() => { setValidating(selected); setSelected(null) }}>Review & validate</Button></>}{selected.status === 'validated' && !selected.report_id && <Button icon={<FileCheck2 size={16} />} onClick={() => generate(selected)}>Generate report</Button>}{selected.report_id && <Button icon={<ArrowRight size={16} />} onClick={() => navigate('/reports')}>Open report</Button>}</div>
    </Modal>}
    {validating && <Modal title="Personally validate this finding" description={validating.title} onClose={() => setValidating(null)}>
      <Notice tone="warning">Validation is a human attestation. Confirm only if you personally reproduced and understand the issue, checked its scope and verified the security impact.</Notice>
      <div className="validation-checklist"><div className={validating.summary ? 'complete' : ''}><CheckCircle2 size={16} />Specific summary</div><div className={validating.reproduction_steps ? 'complete' : ''}><CheckCircle2 size={16} />Reproduction steps</div><div className={validating.impact ? 'complete' : ''}><CheckCircle2 size={16} />Security impact</div><div className={validating.evidence ? 'complete' : ''}><CheckCircle2 size={16} />Direct evidence</div></div>
      <Field label="Your name / researcher handle" required><input required value={name} onChange={e => setName(e.target.value)} /></Field>
      <label className="confirmation-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /><span>I personally investigated, reproduced and confirm this finding. I understand this locks its evidence fields.</span></label>
      <div className="modal-actions"><Button variant="secondary" onClick={() => setValidating(null)}>Cancel</Button><Button disabled={!confirmed || !name.trim() || saving} onClick={validate} icon={<LockKeyhole size={16} />}>{saving ? 'Validating…' : 'Validate & lock evidence'}</Button></div>
    </Modal>}
  </>
}

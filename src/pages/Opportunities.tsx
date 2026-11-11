import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowDownUp, ArrowUpRight, CalendarCheck, CheckCircle2, ChevronRight, CircleDollarSign, Clock3, Download, ExternalLink, FileInput, Filter, Globe2, Info, ListChecks, Plus, Radar, Search, ShieldAlert, ShieldCheck, SlidersHorizontal, Target, Upload, XCircle } from 'lucide-react'
import { api, patch, post } from '../api'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import type { Approval, Programme } from '../types'
import { date, isoInHours, money, percent } from '../utils'
import { Badge, Button, EmptyState, Field, FormGrid, FormSection, InlineLink, Modal, Notice, PageHeader, ScoreRing } from '../components/UI'

const emptyForm = {
  name: '', platform: 'HackerOne', handle: '', programme_url: '', policy_url: '', reward_criteria_url: '',
  currency: 'GBP', reward_min: '', reward_max: '', realistic_reward: '', assets: '', automation_policy: 'unspecified',
  ai_policy: 'human_required', payout_process: 'unspecified', source_checked_at: '', probability_valid: '',
  competition_risk: '', estimated_hours: '', notes: '',
}
type FormState = typeof emptyForm

function ProgrammeForm({ initial, onClose, onSaved }: { initial: Programme | null; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<FormState>(initial ? {
    ...emptyForm, ...initial,
    reward_min: String(initial.reward_min), reward_max: String(initial.reward_max),
    realistic_reward: initial.realistic_reward?.toString() || '', assets: initial.assets.join('\n'),
    probability_valid: initial.probability_valid === null ? '' : String(initial.probability_valid * 100),
    competition_risk: initial.competition_risk === null ? '' : String(initial.competition_risk * 100),
    estimated_hours: initial.estimated_hours?.toString() || '', source_checked_at: initial.source_checked_at.slice(0, 10),
  } as FormState : emptyForm)
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const set = (key: keyof FormState, value: string) => setForm(current => ({ ...current, [key]: value }))
  const optionalNumber = (value: string) => value === '' ? null : Number(value)
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setSaving(true)
    const payload = {
      ...form,
      reward_min: Number(form.reward_min || 0), reward_max: Number(form.reward_max || 0),
      realistic_reward: optionalNumber(form.realistic_reward), assets: form.assets.split('\n').map(item => item.trim()).filter(Boolean),
      probability_valid: form.probability_valid === '' ? null : Number(form.probability_valid) / 100,
      competition_risk: form.competition_risk === '' ? null : Number(form.competition_risk) / 100,
      estimated_hours: optionalNumber(form.estimated_hours),
    }
    try {
      if (initial) await patch(`/programmes/${initial.id}`, payload)
      else await post('/programmes', payload)
      toast(initial ? 'Programme and ranking updated' : 'Real programme recorded and evaluated')
      onSaved()
    } catch (error) { toast(error instanceof Error ? error.message : 'Unable to save programme', 'error') }
    finally { setSaving(false) }
  }
  return <Modal title={initial ? `Review ${initial.name}` : 'Record a real programme'} description="Enter only details verified from the programme’s current canonical sources. Empty estimates remain unscored." onClose={onClose} wide>
    <form onSubmit={submit}>
      <FormSection title="Source of truth" description="Recognition-only programmes are automatically rejected by the cash-only gate.">
        <FormGrid>
          <Field label="Programme name" required><input required value={form.name} onChange={e => set('name', e.target.value)} placeholder="Canonical programme name" /></Field>
          <Field label="Platform" required><select disabled={!!initial} value={form.platform} onChange={e => set('platform', e.target.value)}><option>HackerOne</option><option>Intigriti</option><option>Bugcrowd</option><option>Other</option></select></Field>
          <Field label="Programme URL" required full><input type="url" required value={form.programme_url} onChange={e => set('programme_url', e.target.value)} placeholder="https://platform.example/programme" /></Field>
          <Field label="Policy / scope URL" required><input type="url" required value={form.policy_url} onChange={e => set('policy_url', e.target.value)} placeholder="https://…" /></Field>
          <Field label="Severity & reward criteria URL" required><input type="url" required value={form.reward_criteria_url} onChange={e => set('reward_criteria_url', e.target.value)} placeholder="https://…" /></Field>
          <Field label="Source personally checked on" required><input type="date" max={new Date().toISOString().slice(0, 10)} required value={form.source_checked_at} onChange={e => set('source_checked_at', e.target.value)} /></Field>
          <Field label="Platform handle" hint="Optional; not used for scoring"><input value={form.handle} disabled={!!initial} onChange={e => set('handle', e.target.value)} /></Field>
        </FormGrid>
      </FormSection>
      <FormSection title="Rewards & authorised scope">
        <FormGrid>
          <Field label="Currency"><select disabled={!!initial} value={form.currency} onChange={e => set('currency', e.target.value)}><option>GBP</option><option>USD</option><option>EUR</option></select></Field>
          <Field label="Published minimum reward"><input type="number" min="0" step="any" value={form.reward_min} onChange={e => set('reward_min', e.target.value)} /></Field>
          <Field label="Published maximum reward" required><input type="number" min="0" step="any" required value={form.reward_max} onChange={e => set('reward_max', e.target.value)} /></Field>
          <Field label="Realistic target reward" hint="Your conservative estimate, not the advertised maximum"><input type="number" min="0" step="any" value={form.realistic_reward} onChange={e => set('realistic_reward', e.target.value)} /></Field>
          <Field label="Eligible assets — one per line" required full hint="Exact domains, wildcard scopes, applications or repositories as published. No out-of-scope assets."><textarea required rows={4} value={form.assets} onChange={e => set('assets', e.target.value)} placeholder={'app.example.com\n*.example.com'} /></Field>
          <Field label="Proposed automation permission" required><select value={form.automation_policy} onChange={e => set('automation_policy', e.target.value)}><option value="unspecified">Unspecified — needs review</option><option value="allowed">Explicitly allowed</option><option value="approval_required">Allowed with approval</option><option value="prohibited">Prohibited</option></select></Field>
          <Field label="AI-use policy" required><select value={form.ai_policy} onChange={e => set('ai_policy', e.target.value)}><option value="human_required">AI allowed; human verification required</option><option value="allowed">Explicitly allowed</option><option value="unspecified">Unspecified — needs review</option><option value="prohibited">Prohibited</option></select></Field>
          <Field label="Payout process"><select value={form.payout_process} onChange={e => set('payout_process', e.target.value)}><option value="unspecified">Not yet verified</option><option value="documented">Documented and checked</option></select></Field>
        </FormGrid>
      </FormSection>
      <FormSection title="Researcher estimates" description="These inputs drive the ranking. SENTINEL never invents probabilities or treats scores as payout predictions.">
        <FormGrid>
          <Field label="Probability of a valid finding (%)" hint="Your evidence-based estimate, 0–100"><input type="number" min="0" max="100" step="any" value={form.probability_valid} onChange={e => set('probability_valid', e.target.value)} /></Field>
          <Field label="Competition / duplicate risk (%)" hint="0 = low risk, 100 = very high"><input type="number" min="0" max="100" step="any" value={form.competition_risk} onChange={e => set('competition_risk', e.target.value)} /></Field>
          <Field label="Estimated investigation hours"><input type="number" min="0.1" step="any" value={form.estimated_hours} onChange={e => set('estimated_hours', e.target.value)} /></Field>
          <Field label="Verification notes" full><textarea rows={3} value={form.notes} onChange={e => set('notes', e.target.value)} placeholder="Policy caveats, rate limits, exclusions, verification notes…" /></Field>
        </FormGrid>
      </FormSection>
      <div className="modal-actions"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button disabled={saving} type="submit" icon={<ShieldCheck size={16} />}>{saving ? 'Evaluating…' : initial ? 'Save & re-evaluate' : 'Record & evaluate'}</Button></div>
    </form>
  </Modal>
}

function ImportForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [text, setText] = useState('')
  const [errors, setErrors] = useState<{ index: number; name: string; error: string }[]>([])
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const readFile = async (file?: File) => { if (file) setText(await file.text()) }
  const submit = async () => {
    setSaving(true); setErrors([])
    try {
      const parsed = JSON.parse(text)
      if (!Array.isArray(parsed)) throw new Error('The JSON root must be an array of programme objects.')
      const result = await post<{ imported: Programme[]; errors: typeof errors }>('/programmes/import', parsed)
      setErrors(result.errors)
      toast(`${result.imported.length} programme${result.imported.length === 1 ? '' : 's'} imported; ${result.errors.length} rejected`)
      if (!result.errors.length) onSaved()
      else if (result.imported.length) onSaved()
    } catch (error) { toast(error instanceof Error ? error.message : 'Import failed', 'error') }
    finally { setSaving(false) }
  }
  const template = () => {
    const content = JSON.stringify([{ name: '', platform: 'HackerOne', handle: '', programme_url: '', policy_url: '', reward_criteria_url: '', currency: 'GBP', reward_min: 0, reward_max: 0, realistic_reward: null, assets: [], automation_policy: 'unspecified', ai_policy: 'human_required', payout_process: 'unspecified', source_checked_at: '', probability_valid: null, competition_risk: null, estimated_hours: null, notes: '' }], null, 2)
    const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }))
    const a = document.createElement('a'); a.href = url; a.download = 'sentinel-programme-import-template.json'; a.click(); URL.revokeObjectURL(url)
  }
  return <Modal title="Import verified programme data" description="JSON only. SENTINEL validates every entry and does not infer missing scope, rewards or permissions." onClose={onClose} wide>
    <Notice>There is no anonymous live-platform connector in this milestone. Export or transcribe current canonical programme data, then import it for local evaluation.</Notice>
    <div className="import-actions"><label className="button button-secondary"><Upload size={16} />Choose JSON file<input type="file" accept="application/json,.json" hidden onChange={e => readFile(e.target.files?.[0])} /></label><Button variant="ghost" icon={<Download size={16} />} onClick={template}>Blank schema template</Button></div>
    <Field label="Programme JSON array" full><textarea className="code-input" rows={15} value={text} onChange={e => setText(e.target.value)} placeholder="Paste real programme records here…" /></Field>
    {errors.length > 0 && <div className="import-errors">{errors.map(error => <div key={error.index}><XCircle size={15} /><strong>Row {error.index + 1}: {error.name}</strong><span>{error.error}</span></div>)}</div>}
    <div className="modal-actions"><Button variant="secondary" onClick={onClose}>Close</Button><Button disabled={!text.trim() || saving} onClick={submit} icon={<FileInput size={16} />}>{saving ? 'Validating…' : 'Validate & import'}</Button></div>
  </Modal>
}

const methods = [
  { id: 'passive_review', label: 'Passive policy and asset review' },
  { id: 'manual_browser', label: 'Manual browser investigation' },
  { id: 'non_destructive_http', label: 'Non-destructive HTTP requests' },
  { id: 'source_review', label: 'Authorised source-code review' },
]
function ApprovalForm({ programme, onClose, onSaved }: { programme: Programme; onClose: () => void; onSaved: () => void }) {
  const [assets, setAssets] = useState<string[]>([])
  const [selectedMethods, setSelectedMethods] = useState<string[]>(['passive_review'])
  const [rate, setRate] = useState(1)
  const [expiry, setExpiry] = useState(24)
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const toggle = (value: string, list: string[], setter: (next: string[]) => void) => setter(list.includes(value) ? list.filter(item => item !== value) : [...list, value])
  const submit = async () => {
    setSaving(true)
    try { await post(`/programmes/${programme.id}/approvals`, { assets, methods: selectedMethods, rate_limit: rate, expires_at: isoInHours(expiry) }); toast('Approval request recorded; no testing has been launched'); onSaved() }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to request approval', 'error') }
    finally { setSaving(false) }
  }
  return <Modal title="Request test approval" description={`${programme.name} · exact scope and a short expiry are mandatory.`} onClose={onClose}>
    <Notice tone="warning">Approval only records your authorisation decision. The live testing engine is not enabled in this milestone.</Notice>
    <FormSection title="Exact eligible assets">
      <div className="check-list">{programme.assets.map(asset => <label key={asset}><input type="checkbox" checked={assets.includes(asset)} onChange={() => toggle(asset, assets, setAssets)} /><span>{asset}</span></label>)}</div>
    </FormSection>
    <FormSection title="Permitted methods"><div className="check-list">{methods.map(method => <label key={method.id}><input type="checkbox" checked={selectedMethods.includes(method.id)} onChange={() => toggle(method.id, selectedMethods, setSelectedMethods)} /><span>{method.label}</span></label>)}</div></FormSection>
    <FormGrid><Field label="Maximum requests / second"><input type="number" min="1" max="60" value={rate} onChange={e => setRate(Number(e.target.value))} /></Field><Field label="Approval expires after"><select value={expiry} onChange={e => setExpiry(Number(e.target.value))}><option value={1}>1 hour</option><option value={4}>4 hours</option><option value={24}>24 hours</option><option value={72}>72 hours</option></select></Field></FormGrid>
    <div className="modal-actions"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button disabled={!assets.length || !selectedMethods.length || saving} onClick={submit} icon={<ListChecks size={16} />}>Submit for my approval</Button></div>
  </Modal>
}

function ScoreInfo({ onClose }: { onClose: () => void }) {
  const factors = [['Realistic bounty', '25%'], ['Valid-bug probability', '25%'], ['Eligible assets', '15%'], ['Testing permission', '15%'], ['Competition / duplicate risk', '10%'], ['Investigation time', '10%']]
  return <Modal title="How opportunity ranking works" description="Transparent heuristics, not an AI payout promise." onClose={onClose}>
    <div className="weight-list">{factors.map(([name, weight]) => <div key={name}><span>{name}</span><strong>{weight}</strong></div>)}</div>
    <h4 className="modal-subtitle">Estimated return per hour</h4><div className="formula">realistic reward × valid-bug probability × (1 − competition risk) ÷ estimated hours</div>
    <Notice>Only eligible programmes with all four researcher estimates receive a score. Review-required and rejected programmes never rise in the paid-opportunity queue.</Notice>
  </Modal>
}

function ProgrammeDetail({ programme, onClose, onEdit, onApproval }: { programme: Programme; onClose: () => void; onEdit: () => void; onApproval: () => void }) {
  return <Modal title={programme.name} description={`${programme.platform} · last source check ${date(programme.source_checked_at)}`} onClose={onClose} wide>
    <div className="detail-top"><div className="detail-score"><ScoreRing score={programme.score} size="large" /><div><Badge value={programme.eligibility_status} dot /><p>{programme.score === null ? 'Complete policy gates and estimates to rank.' : 'Weighted opportunity score'}</p></div></div><div className="detail-value"><span>ESTIMATED RETURN / HOUR</span><strong>{programme.expected_value_per_hour === null ? '—' : money(programme.expected_value_per_hour, programme.currency, 2)}</strong><small>Heuristic, before duplicates or programme decisions</small></div></div>
    {programme.eligibility_reasons.length > 0 && <Notice tone={programme.eligibility_status === 'rejected' ? 'danger' : 'warning'}><strong>{programme.eligibility_status === 'rejected' ? 'Rejected by policy gates' : 'Review required'}</strong><ul>{programme.eligibility_reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></Notice>}
    <div className="detail-grid">
      <section><h3>Opportunity</h3><dl className="key-values"><div><dt>Published rewards</dt><dd>{money(programme.reward_min, programme.currency)} – {money(programme.reward_max, programme.currency)}</dd></div><div><dt>Realistic target</dt><dd>{money(programme.realistic_reward, programme.currency)}</dd></div><div><dt>Valid-finding estimate</dt><dd>{percent(programme.probability_valid)}</dd></div><div><dt>Competition risk</dt><dd>{percent(programme.competition_risk)}</dd></div><div><dt>Investigation time</dt><dd>{programme.estimated_hours ? `${programme.estimated_hours} hours` : 'Not estimated'}</dd></div></dl></section>
      <section><h3>Testing envelope</h3><dl className="key-values"><div><dt>Automation</dt><dd><Badge value={programme.automation_policy} /></dd></div><div><dt>AI policy</dt><dd><Badge value={programme.ai_policy} /></dd></div><div><dt>Payout process</dt><dd>{programme.payout_process === 'documented' ? 'Documented' : 'Not verified'}</dd></div><div><dt>Eligible assets</dt><dd>{programme.assets.length}</dd></div></dl></section>
    </div>
    <section className="detail-section"><h3>Recorded eligible scope</h3><div className="asset-list">{programme.assets.map(asset => <code key={asset}><Target size={13} />{asset}</code>)}</div></section>
    {programme.score_breakdown && <section className="detail-section"><h3>Score breakdown</h3><div className="factor-table">{programme.score_breakdown.map(factor => <div key={factor.key}><span>{factor.key.replaceAll('_', ' ')}</span><div className="factor-track"><i style={{ width: `${factor.factor * 100}%` }} /></div><small>{factor.weight}%</small><strong>{factor.points}</strong></div>)}</div></section>}
    <section className="detail-section"><h3>Canonical sources</h3><div className="source-links"><a href={programme.programme_url} target="_blank" rel="noreferrer">Programme <ExternalLink size={13} /></a><a href={programme.policy_url} target="_blank" rel="noreferrer">Policy & scope <ExternalLink size={13} /></a>{programme.reward_criteria_url && <a href={programme.reward_criteria_url} target="_blank" rel="noreferrer">Reward criteria <ExternalLink size={13} /></a>}</div></section>
    {programme.notes && <section className="detail-section"><h3>Researcher notes</h3><p className="notes-text">{programme.notes}</p></section>}
    <div className="modal-actions"><Button variant="secondary" onClick={onEdit}>Review / edit</Button><Button disabled={programme.eligibility_status === 'rejected'} onClick={onApproval} icon={<ShieldCheck size={16} />}>Request test approval</Button></div>
  </Modal>
}

export default function Opportunities() {
  const { programmes, refresh, loading, settings } = useData()
  const [params, setParams] = useSearchParams()
  const [formOpen, setFormOpen] = useState(params.get('new') === '1')
  const [importOpen, setImportOpen] = useState(false)
  const [scoreOpen, setScoreOpen] = useState(false)
  const [editing, setEditing] = useState<Programme | null>(null)
  const [selected, setSelected] = useState<Programme | null>(null)
  const [approvalFor, setApprovalFor] = useState<Programme | null>(null)
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState('score')
  const [search, setSearch] = useState(params.get('q') || '')
  const query = params.get('q') || ''
  useEffect(() => { setSearch(query) }, [query])
  const visible = useMemo(() => programmes.filter(programme => {
    const matchesFilter = filter === 'all' || programme.eligibility_status === filter || (filter === 'unscored' && programme.score === null)
    const haystack = `${programme.name} ${programme.platform} ${programme.assets.join(' ')}`.toLowerCase()
    return matchesFilter && haystack.includes(search.toLowerCase())
  }).sort((a, b) => sort === 'name' ? a.name.localeCompare(b.name) : sort === 'reward' ? b.reward_max - a.reward_max : (b.score ?? -1) - (a.score ?? -1)), [programmes, filter, search, sort])
  const closeForm = () => { setFormOpen(false); setEditing(null); if (params.has('new')) { params.delete('new'); setParams(params, { replace: true }) } }
  const saved = async () => { closeForm(); setImportOpen(false); setApprovalFor(null); await refresh() }
  const openDetail = async (programme: Programme) => {
    try { setSelected(await api<Programme>(`/programmes/${programme.id}`)) } catch { setSelected(programme) }
  }
  return <>
    <PageHeader eyebrow="OPPORTUNITY INTELLIGENCE" title="Paid research, ranked with discipline." description="Record current cash programmes, enforce policy gates and prioritise conservative expected return — never advertised rewards alone." actions={<><Button variant="secondary" icon={<Upload size={16} />} onClick={() => setImportOpen(true)}>Import JSON</Button><Button icon={<Plus size={16} />} onClick={() => setFormOpen(true)}>Record programme</Button></>} />
    <div className="policy-strip"><div><ShieldCheck size={18} /><span><strong>Cash-only gate active</strong> · recognition-only and prohibited-method programmes are rejected</span></div><button onClick={() => setScoreOpen(true)}><Info size={15} />Scoring methodology</button></div>
    <section className="panel opportunity-panel">
      <div className="table-toolbar"><div className="filter-tabs">{[['all', 'All'], ['eligible', 'Eligible'], ['review_required', 'Needs review'], ['rejected', 'Rejected'], ['unscored', 'Unscored']].map(([value, text]) => <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>{text}{value === 'all' && <span>{programmes.length}</span>}</button>)}</div><div className="table-tools"><label className="small-search"><Search size={15} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search scope or programme" /></label><select value={sort} onChange={e => setSort(e.target.value)} aria-label="Sort programmes"><option value="score">Rank by score</option><option value="reward">Maximum reward</option><option value="name">Programme name</option></select></div></div>
      {loading ? <div className="loading-block">Reading verified programme records…</div> : visible.length === 0 ? <EmptyState icon={<Radar size={25} />} title={programmes.length ? 'No programmes match this view' : 'No opportunity data available'} description={programmes.length ? 'Change the filters or search to see other recorded programmes.' : 'SENTINEL starts empty by design. Add a real, currently verified cash-paying programme to build your research queue.'} action={!programmes.length && <Button icon={<Plus size={16} />} onClick={() => setFormOpen(true)}>Record first programme</Button>} /> : <div className="responsive-table"><table className="data-table opportunity-table"><thead><tr><th>Rank</th><th>Programme</th><th>Eligibility</th><th>Realistic reward</th><th>Assets</th><th>Est. return / hr</th><th>Score</th><th></th></tr></thead><tbody>{visible.map((programme, index) => <tr key={programme.id} onClick={() => openDetail(programme)}><td><span className="rank-number">{String(index + 1).padStart(2, '0')}</span></td><td><div className="programme-cell"><div className={`platform-mark platform-${programme.platform.toLowerCase()}`}>{programme.name.slice(0, 1).toUpperCase()}</div><div><strong>{programme.name}</strong><span>{programme.platform} · checked {date(programme.source_checked_at)}</span></div></div></td><td><Badge value={programme.eligibility_status} dot /></td><td><strong className="table-money">{money(programme.realistic_reward, programme.currency)}</strong><small className="table-sub">max {money(programme.reward_max, programme.currency)}</small></td><td><span className="asset-count"><Globe2 size={14} />{programme.assets.length}</span></td><td><strong className="table-money">{programme.expected_value_per_hour === null ? '—' : money(programme.expected_value_per_hour, programme.currency, 2)}</strong></td><td><div className="score-cell"><ScoreRing score={programme.score} /><span>{programme.score === null ? 'Unscored' : 'Weighted'}</span></div></td><td><ChevronRight size={17} className="row-chevron" /></td></tr>)}</tbody></table></div>}
    </section>
    <div className="table-footnote"><Info size={14} /> Ranking uses your estimates and the recorded policy. It does not predict acceptance, duplication or payment.</div>
    {(formOpen || editing) && <ProgrammeForm initial={editing} onClose={closeForm} onSaved={saved} />}
    {importOpen && <ImportForm onClose={() => setImportOpen(false)} onSaved={saved} />}
    {scoreOpen && <ScoreInfo onClose={() => setScoreOpen(false)} />}
    {selected && <ProgrammeDetail programme={selected} onClose={() => setSelected(null)} onEdit={() => { setEditing(selected); setSelected(null) }} onApproval={() => { setApprovalFor(selected); setSelected(null) }} />}
    {approvalFor && <ApprovalForm programme={approvalFor} onClose={() => setApprovalFor(null)} onSaved={saved} />}
  </>
}

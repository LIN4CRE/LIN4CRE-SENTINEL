import { useNavigate } from 'react-router-dom'
import { ArrowRight, BadgePoundSterling, Check, CheckCircle2, ChevronRight, CircleDollarSign, ClipboardCheck, Clock3, Database, FileCheck2, FlaskConical, FolderInput, LockKeyhole, Plus, Radar, ScanSearch, ShieldCheck, Sparkles, Target, TerminalSquare, ZapOff } from 'lucide-react'
import { useData } from '../DataContext'
import { date, money } from '../utils'
import { Badge, Button, EmptyState, PageHeader, ScoreRing, StatCard } from '../components/UI'

export default function Dashboard() {
  const { dashboard, programmes, settings, health } = useData()
  const navigate = useNavigate()
  const counts = dashboard?.counts
  const paid = dashboard?.paid || []
  const paidDisplay = paid.length ? paid.map(item => money(item.total, item.currency, 2)).join(' · ') : money(0, 'GBP', 2)
  const ranked = programmes.filter(item => item.eligibility_status === 'eligible' && item.score !== null).slice(0, 4)
  const setup = [
    { label: 'Import read-only PC audit', done: (counts?.pc_audits || 0) > 0, action: () => navigate('/settings?section=pc-audit'), cta: 'Open audit import' },
    { label: 'Verify backup and recovery path', done: !!settings?.setup_backup_verified, action: () => navigate('/settings?section=backups'), cta: 'Review backups' },
    { label: 'Verify local Ollama installation', done: !!settings?.ollama_model, action: () => navigate('/settings?section=ai'), cta: 'Test connection' },
    { label: 'Record first real cash programme', done: (counts?.programmes || 0) > 0, action: () => navigate('/opportunities?new=1'), cta: 'Record programme' },
  ]
  const completed = setup.filter(item => item.done).length
  const pipeline = [
    { label: 'Discovery', detail: 'Cash programmes recorded', count: counts?.programmes || 0, icon: Radar },
    { label: 'Intelligence', detail: 'Eligible & ranked', count: counts?.eligible || 0, icon: ScanSearch },
    { label: 'Approval', detail: 'Awaiting your decision', count: counts?.pending_approvals || 0, icon: ClipboardCheck },
    { label: 'Research', detail: 'Evidence records', count: counts?.findings || 0, icon: FlaskConical },
    { label: 'Validation', detail: 'Human confirmed', count: counts?.validated_findings || 0, icon: ShieldCheck },
    { label: 'Reports', detail: 'Submitted externally', count: counts?.submitted_reports || 0, icon: FileCheck2 },
    { label: 'Earnings', detail: 'Actual paid records', count: dashboard?.paid.length || 0, icon: CircleDollarSign },
  ]
  return <>
    <PageHeader eyebrow="LIN4CRE / RESEARCH OPERATIONS" title="Command centre" description="Autonomous intelligence. Explicit authorisation. Evidence before claims." actions={<><Button variant="secondary" icon={<Plus size={16} />} onClick={() => navigate('/opportunities?new=1')}>Record programme</Button><Button icon={<Sparkles size={16} />} onClick={() => navigate('/assistant')}>Ask SENTINEL</Button></>} />
    <section className="command-hero">
      <div className="hero-orbit"><div className="orbit-ring orbit-one" /><div className="orbit-ring orbit-two" /><Radar size={30} /></div>
      <div className="hero-copy"><div className="hero-kicker"><span />MILESTONE 02 · AI OPERATIONS ONLINE</div><h2>Build a research operation.<br /><em>Not a wall of guesses.</em></h2><p>SENTINEL ranks only source-verified cash opportunities and keeps every test, validation and submission under your control.</p></div>
      <div className="hero-controls"><div><LockKeyhole size={17} /><span>Testing engine</span><strong>Disabled</strong></div><div><ClipboardCheck size={17} /><span>Submissions</span><strong>Human only</strong></div><div><BadgePoundSterling size={17} /><span>Spend ceiling</span><strong>£0</strong></div></div>
    </section>
    <div className="stats-grid">
      <StatCard label="Cash opportunities" value={counts?.programmes ?? '—'} note={`${counts?.eligible || 0} eligible · recorded sources only`} icon={<Radar size={19} />} />
      <StatCard label="Pending approvals" value={counts?.pending_approvals ?? '—'} note="Nothing runs without authorisation" icon={<ClipboardCheck size={19} />} />
      <StatCard label="Validated findings" value={counts?.validated_findings ?? '—'} note={`${counts?.findings || 0} total research records`} icon={<ShieldCheck size={19} />} />
      <StatCard label="Bounties received" value={paidDisplay} note="Actual paid entries only" icon={<CircleDollarSign size={19} />} accent />
    </div>
    <div className="dashboard-grid">
      <section className="panel priority-panel">
        <div className="panel-head"><div><span className="panel-kicker">AI OPPORTUNITY INTELLIGENCE</span><h2>Priority research queue</h2></div>{programmes.length > 0 && <button className="text-button" onClick={() => navigate('/opportunities')}>View all<ArrowRight size={14} /></button>}</div>
        {ranked.length ? <div className="priority-list">{ranked.map((programme, index) => <button key={programme.id} onClick={() => navigate(`/opportunities?q=${encodeURIComponent(programme.name)}`)}><span className="priority-rank">0{index + 1}</span><div className="priority-name"><strong>{programme.name}</strong><span>{programme.platform} · {programme.assets.length} eligible assets</span></div><div className="priority-return"><strong>{programme.expected_value_per_hour === null ? '—' : money(programme.expected_value_per_hour, programme.currency, 2)}</strong><span>est. return / hr</span></div><ScoreRing score={programme.score} /><ChevronRight size={16} /></button>)}</div> : <EmptyState compact icon={<Target size={22} />} title={programmes.length ? 'No ranked opportunities yet' : 'No opportunity data available'} description={programmes.length ? 'Complete policy gates and researcher estimates to produce a ranking.' : 'Add a real programme and its current policy. SENTINEL will reject non-cash or prohibited opportunities before ranking.'} action={<Button variant="secondary" size="sm" icon={<Plus size={15} />} onClick={() => navigate('/opportunities?new=1')}>{programmes.length ? 'Review programmes' : 'Record first programme'}</Button>} />}
      </section>
      <section className="panel safety-panel">
        <div className="panel-head"><div><span className="panel-kicker">FAIL-CLOSED CONTROLS</span><h2>Safety envelope</h2></div><Badge value={settings?.kill_switch ? 'revoked' : 'operational'} dot /></div>
        <div className="safety-list">
          <div><span className="safety-icon"><Check size={15} /></span><div><strong>Exact scope allowlist</strong><p>Every asset must match a recorded eligible scope.</p></div></div>
          <div><span className="safety-icon"><Check size={15} /></span><div><strong>Human test approval</strong><p>Short-lived, method-specific and revocable.</p></div></div>
          <div><span className="safety-icon"><Check size={15} /></span><div><strong>Evidence before validation</strong><p>Reproduction, impact and evidence are mandatory.</p></div></div>
          <div><span className="safety-icon"><Check size={15} /></span><div><strong>No autonomous submission</strong><p>Only you can record an external submission.</p></div></div>
        </div>
        <button className="kill-control" onClick={() => navigate('/settings?section=safety')}><ZapOff size={16} /><span>{settings?.kill_switch ? 'Kill switch active — review controls' : 'Global kill switch ready'}</span><ChevronRight size={15} /></button>
      </section>
    </div>
    <section className="panel pipeline-panel">
      <div className="panel-head"><div><span className="panel-kicker">CONTROLLED WORKFLOW</span><h2>Research pipeline</h2></div><span className="live-db"><Database size={13} />SQLite live records</span></div>
      <div className="pipeline">{pipeline.map((stage, index) => <div className="pipeline-stage" key={stage.label}><div className="pipeline-icon"><stage.icon size={18} /><span>{stage.count}</span></div><strong>{stage.label}</strong><p>{stage.detail}</p>{index < pipeline.length - 1 && <ChevronRight className="pipeline-arrow" size={16} />}</div>)}</div>
    </section>
    <div className="dashboard-grid lower-grid">
      <section className="panel setup-panel">
        <div className="panel-head"><div><span className="panel-kicker">BACKUP-FIRST INSTALLATION</span><h2>Workstation readiness</h2></div><span className="setup-fraction">{completed}/{setup.length}</span></div>
        <div className="setup-progress"><i style={{ width: `${completed / setup.length * 100}%` }} /></div>
        <div className="setup-list">{setup.map((item, index) => <button key={item.label} onClick={item.action}><span className={item.done ? 'setup-check done' : 'setup-check'}>{item.done ? <Check size={14} /> : index + 1}</span><div><strong>{item.label}</strong><span>{item.done ? 'Recorded in local core' : item.cta}</span></div><ChevronRight size={15} /></button>)}</div>
      </section>
      <section className="panel activity-panel">
        <div className="panel-head"><div><span className="panel-kicker">APPEND-ONLY HISTORY</span><h2>Recent activity</h2></div><button className="text-button" onClick={() => navigate('/audit')}>Audit trail<ArrowRight size={14} /></button></div>
        <div className="activity-list">{dashboard?.recent_activity.slice(0, 5).map(event => <div key={event.id}><span className="activity-dot" /><div><strong>{event.message}</strong><span>{date(event.timestamp, true)}</span></div></div>)}</div>
      </section>
    </div>
    <div className="truth-note"><ShieldCheck size={16} /><p><strong>No simulated success.</strong> Empty states, zero totals and unavailable connections are shown exactly as they are. Programme acceptance and payment can never be guaranteed.</p></div>
  </>
}

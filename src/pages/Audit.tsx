import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Database, Download, FileJson, LockKeyhole, ScrollText, Search, ShieldCheck } from 'lucide-react'
import { useData } from '../DataContext'
import { date, label } from '../utils'
import { Badge, Button, EmptyState, PageHeader } from '../components/UI'

export default function Audit() {
  const { audit } = useData()
  const [query, setQuery] = useState('')
  const [type, setType] = useState('all')
  const [expanded, setExpanded] = useState<number | null>(null)
  const types = [...new Set(audit.map(item => item.entity_type))]
  const visible = useMemo(() => audit.filter(item => (type === 'all' || item.entity_type === type) && `${item.message} ${item.event_type} ${item.entity_id}`.toLowerCase().includes(query.toLowerCase())), [audit, query, type])
  const exportJson = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ exported_at: new Date().toISOString(), events: visible }, null, 2)], { type: 'application/json' }))
    const a = document.createElement('a'); a.href = url; a.download = `sentinel-audit-${new Date().toISOString().slice(0, 10)}.json`; a.click(); URL.revokeObjectURL(url)
  }
  return <>
    <PageHeader eyebrow="IMMUTABLE OPERATIONS HISTORY" title="Every decision leaves a trail." description="Append-only local records for programme changes, approvals, evidence validation, report outcomes and payments." actions={<Button variant="secondary" icon={<Download size={16} />} onClick={exportJson} disabled={!visible.length}>Export current view</Button>} />
    <div className="audit-integrity"><div><LockKeyhole size={19} /><span><strong>Database-enforced append-only log</strong>UPDATE and DELETE triggers reject changes to audit events.</span></div><div><Database size={18} />{audit.length} recorded event{audit.length === 1 ? '' : 's'}</div></div>
    <section className="panel audit-panel"><div className="table-toolbar"><div className="filter-tabs">{['all', ...types].map(value => <button key={value} className={type === value ? 'active' : ''} onClick={() => setType(value)}>{value === 'all' ? 'All events' : label(value)}</button>)}</div><label className="small-search"><Search size={15} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search activity" /></label></div>
      {!visible.length ? <EmptyState icon={<ScrollText size={24} />} title="No matching audit events" description="The audit trail has no records matching these filters." /> : <div className="audit-list">{visible.map(event => <div className="audit-event" key={event.id}><button className="audit-event-main" onClick={() => setExpanded(expanded === event.id ? null : event.id)}><span className="event-chevron">{expanded === event.id ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</span><span className="event-time">{date(event.timestamp, true)}<small>#{event.id}</small></span><span className="event-message"><strong>{event.message}</strong><small>{event.event_type}</small></span><Badge value={event.entity_type} /><span className="event-id">{event.entity_id ? event.entity_id.slice(0, 8) : '—'}</span></button>{expanded === event.id && <div className="event-details"><div><span>Entity type</span><strong>{event.entity_type}</strong></div><div><span>Entity ID</span><code>{event.entity_id || 'Not applicable'}</code></div><pre>{JSON.stringify(event.details, null, 2)}</pre></div>}</div>)}</div>}
    </section>
  </>
}

import { ReactNode, useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, BadgePoundSterling, BookOpenCheck, ChevronRight, CircleDollarSign, ClipboardCheck, FileCheck2, FlaskConical, HardDrive, LayoutDashboard, Menu, Radar, ScrollText, Search, Settings2, ShieldCheck, Sparkles, Wrench, X, ZapOff } from 'lucide-react'
import { useData } from '../DataContext'
import { cx } from '../utils'
import { Logo } from './UI'

const nav = [
  { to: '/', label: 'Command centre', icon: LayoutDashboard, end: true },
  { to: '/assistant', label: 'Ask SENTINEL', icon: Sparkles },
  { to: '/opportunities', label: 'Opportunities', icon: Radar },
  { to: '/research', label: 'Research', icon: FlaskConical },
  { to: '/approvals', label: 'Approvals', icon: ClipboardCheck, count: true },
  { to: '/reports', label: 'Reports', icon: FileCheck2 },
  { to: '/earnings', label: 'Earnings', icon: CircleDollarSign },
]
export function Layout({ children }: { children: ReactNode }) {
  const { dashboard, settings, health } = useData()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        navigate('/assistant')
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [navigate])
  const pending = dashboard?.counts.pending_approvals || 0
  const search = (event: React.FormEvent) => { event.preventDefault(); navigate(`/opportunities${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`); setMobileOpen(false) }
  return <div className="app-shell">
    <aside className={cx('sidebar', mobileOpen && 'sidebar-open')}>
      <div className="sidebar-head"><Logo /><button className="mobile-close" onClick={() => setMobileOpen(false)}><X size={20} /></button></div>
      <div className="workspace-label"><span className="workspace-icon">S</span><div><strong>Research operations</strong><span>Local workspace</span></div><ChevronRight size={14} /></div>
      <nav className="main-nav">
        <div className="nav-section">OPERATIONS</div>
        {nav.map(item => <NavLink key={item.to} to={item.to} end={item.end} onClick={() => setMobileOpen(false)} className={({ isActive }) => cx('nav-item', isActive && 'active')}><item.icon size={18} /><span>{item.label}</span>{item.count && pending > 0 ? <b>{pending}</b> : null}</NavLink>)}
        <div className="nav-section nav-section-second">SYSTEM</div>
        <NavLink to="/maintenance" onClick={() => setMobileOpen(false)} className={({ isActive }) => cx('nav-item', isActive && 'active')}><Wrench size={18} /><span>Maintenance</span></NavLink>
        <NavLink to="/recovery" onClick={() => setMobileOpen(false)} className={({ isActive }) => cx('nav-item', isActive && 'active')}><HardDrive size={18} /><span>Recovery</span></NavLink>
        <NavLink to="/audit" onClick={() => setMobileOpen(false)} className={({ isActive }) => cx('nav-item', isActive && 'active')}><ScrollText size={18} /><span>Audit trail</span></NavLink>
        <NavLink to="/settings" onClick={() => setMobileOpen(false)} className={({ isActive }) => cx('nav-item', isActive && 'active')}><Settings2 size={18} /><span>Setup & sources</span></NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="local-card"><div><ShieldCheck size={17} /><strong>Local-first</strong></div><p>No live testing engine.<br />No automatic submissions.</p><div className="spend-row"><span>Spend ceiling</span><b>£0</b></div></div>
        <div className="core-status"><i className={health?.status === 'operational' ? 'online' : ''} /><span>Core {health?.status || 'connecting'}</span><small>v{health?.version || '0.1.0'}</small></div>
      </div>
    </aside>
    {mobileOpen && <div className="sidebar-scrim" onClick={() => setMobileOpen(false)} />}
    <div className="main-column">
      <header className="topbar">
        <button className="mobile-menu" onClick={() => setMobileOpen(true)}><Menu size={20} /></button>
        <form className="global-search" onSubmit={search}><Search size={16} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search recorded opportunities…" aria-label="Search opportunities" /><kbd>↵</kbd></form>
        <div className="topbar-right"><span className="verified-note"><BookOpenCheck size={15} /> Sources checked 11 Nov 2026</span><button className={cx('approval-bell', pending > 0 && 'has-pending')} onClick={() => navigate('/approvals')} title="Pending approvals"><ClipboardCheck size={18} />{pending > 0 && <b>{pending}</b>}</button><div className={cx('mode-chip', settings?.kill_switch && 'mode-stopped')}><Activity size={14} /><span>{settings?.kill_switch ? 'Research stopped' : 'Approval mode'}</span></div></div>
      </header>
      {settings?.kill_switch && <div className="kill-banner"><ZapOff size={17} /><strong>Kill switch active.</strong> All test approvals were revoked. Intelligence records remain available.<button onClick={() => navigate('/settings')}>Review controls</button></div>}
      <main className="main-content">{children}</main>
      <footer className="app-footer"><span>LIN4CRE SENTINEL · Human-controlled security research</span><span><BadgePoundSterling size={13} /> No payout is guaranteed</span></footer>
    </div>
  </div>
}

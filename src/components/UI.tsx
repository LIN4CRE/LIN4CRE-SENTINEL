import { ReactNode, useEffect } from 'react'
import { AlertCircle, ArrowRight, Check, Inbox, X } from 'lucide-react'
import { cx, label } from '../utils'

export function Logo({ compact = false }: { compact?: boolean }) {
  return <div className={cx('brand', compact && 'brand-compact')}>
    <svg className="brand-mark" viewBox="0 0 44 44" fill="none" aria-hidden="true">
      <path d="M22 3 38 9v11c0 10.2-6.5 17.1-16 21C12.5 37.1 6 30.2 6 20V9l16-6Z" stroke="currentColor" strokeWidth="1.6" />
      <path d="M22 10v24M10 22h24" stroke="currentColor" strokeWidth="1.2" opacity=".45" />
      <circle cx="22" cy="22" r="6.5" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="22" cy="22" r="2" fill="currentColor" />
    </svg>
    {!compact && <div><strong>LIN4CRE</strong><span>SENTINEL</span></div>}
  </div>
}

export function Badge({ value, tone, dot = false }: { value: string; tone?: string; dot?: boolean }) {
  const inferred = tone || ({
    eligible: 'green', approved: 'green', validated: 'green', paid: 'green', accepted: 'green', resolved: 'green', operational: 'green',
    review_required: 'amber', pending: 'amber', awarded: 'amber', investigating: 'blue', submitted: 'blue', triaged: 'blue', ready: 'blue',
    rejected: 'red', revoked: 'red', prohibited: 'red', duplicate: 'muted', draft: 'muted', unrated: 'muted',
  } as Record<string, string>)[value] || 'muted'
  return <span className={`badge badge-${inferred}`}>{dot && <i />}{label(value)}</span>
}

export function Button({ children, variant = 'primary', size = 'md', icon, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; size?: 'sm' | 'md'; icon?: ReactNode }) {
  return <button className={cx('button', `button-${variant}`, `button-${size}`, className)} {...props}>{icon}{children}</button>
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description: string; actions?: ReactNode }) {
  return <header className="page-header">
    <div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1><p>{description}</p></div>
    {actions && <div className="page-actions">{actions}</div>}
  </header>
}

export function EmptyState({ icon, title, description, action, compact = false }: { icon?: ReactNode; title: string; description: string; action?: ReactNode; compact?: boolean }) {
  return <div className={cx('empty-state', compact && 'empty-compact')}>
    <div className="empty-icon">{icon || <Inbox size={22} />}</div>
    <h3>{title}</h3><p>{description}</p>{action}
  </div>
}

export function Modal({ title, description, children, onClose, wide = false }: { title: string; description?: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', handler); document.body.style.overflow = '' }
  }, [onClose])
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section className={cx('modal', wide && 'modal-wide')} role="dialog" aria-modal="true" aria-label={title}>
      <div className="modal-head"><div><h2>{title}</h2>{description && <p>{description}</p>}</div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={19} /></button></div>
      <div className="modal-body">{children}</div>
    </section>
  </div>
}

export function Field({ label: title, hint, children, required = false, full = false }: { label: string; hint?: string; children: ReactNode; required?: boolean; full?: boolean }) {
  return <label className={cx('field', full && 'field-full')}><span>{title}{required && <b> *</b>}</span>{children}{hint && <small>{hint}</small>}</label>
}

export function FormGrid({ children }: { children: ReactNode }) { return <div className="form-grid">{children}</div> }
export function FormSection({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return <section className="form-section"><div className="form-section-title"><h3>{title}</h3>{description && <p>{description}</p>}</div>{children}</section>
}

export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'warning' | 'success' | 'danger' }) {
  return <div className={`notice notice-${tone}`}>{tone === 'success' ? <Check size={17} /> : <AlertCircle size={17} />}<div>{children}</div></div>
}

export function StatCard({ label: title, value, note, icon, accent = false }: { label: string; value: ReactNode; note: string; icon: ReactNode; accent?: boolean }) {
  return <article className={cx('stat-card', accent && 'stat-accent')}><div className="stat-top"><span>{title}</span><div className="stat-icon">{icon}</div></div><strong>{value}</strong><small>{note}</small></article>
}

export function ScoreRing({ score, size = 'normal' }: { score: number | null; size?: 'normal' | 'large' }) {
  return <div className={cx('score-ring', size === 'large' && 'score-ring-large')} style={{ '--score': `${(score || 0) * 3.6}deg` } as React.CSSProperties}>
    <div><strong>{score === null ? '—' : score}</strong>{score !== null && <span>/100</span>}</div>
  </div>
}

export function InlineLink({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return <button className="inline-link" onClick={onClick}>{children}<ArrowRight size={14} /></button>
}

export function Spinner() { return <span className="spinner" aria-label="Loading" /> }

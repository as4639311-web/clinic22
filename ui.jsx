import { useEffect, useRef } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  Activity, Apple, ArrowDownRight, ArrowRight, ArrowUpRight, Bell, BookOpen, Brain, CalendarDays, ChevronLeft,
  Dumbbell, HeartPulse, Home, IdCard, ListChecks, Minus, Plus, Smile,
} from 'lucide-react'
import { useApp } from '../state'

export const SERVICE_ICON = { mental: Brain, fitness: Dumbbell, sports_medicine: Activity, nutrition: Apple, education: BookOpen }
export const DOMAIN_ICON = { mental: Brain, physical: HeartPulse, nutrition: Apple, general: Smile }
export const DOMAIN_COLOR = { mental: 'var(--mental)', physical: 'var(--fitness)', nutrition: 'var(--nutrition)', general: 'var(--education)' }
export const PLAN_SERVICE = { training: 'fitness', nutrition: 'nutrition', mental: 'mental' }

export function ServiceIcon({ service, size = 22 }) {
  const Icon = SERVICE_ICON[service] || Activity
  const c = `var(--${service})`
  return (
    <span className="svc-dot" style={{ background: `color-mix(in srgb, ${c} 16%, transparent)`, color: c }} aria-hidden="true">
      <Icon size={size} strokeWidth={1.75} />
    </span>
  )
}

export function TopBar({ title, back = false, actions = null }) {
  const nav = useNavigate()
  const { t } = useApp()
  return (
    <header className="topbar">
      {back && (
        <button className="icon-btn" onClick={() => nav(-1)} aria-label={t('back')}>
          <ArrowRight size={22} className="back-ico" style={{ transform: 'var(--back-flip)' }} />
        </button>
      )}
      <h1>{title}</h1>
      {actions}
    </header>
  )
}

export function BellButton({ unread }) {
  const nav = useNavigate()
  const { t } = useApp()
  return (
    <button className="icon-btn" onClick={() => nav('/notifications')} aria-label={t('notifications')}>
      <Bell size={22} strokeWidth={1.75} />
      {unread > 0 && <span className="dot" />}
    </button>
  )
}

export function BottomNav() {
  const { t } = useApp()
  const items = [
    { to: '/', icon: Home, label: t('nav_home'), end: true },
    { to: '/appointments', icon: CalendarDays, label: t('nav_appointments') },
    { to: '/book', icon: Plus, label: t('nav_book'), book: true },
    { to: '/plans', icon: ListChecks, label: t('nav_plans') },
    { to: '/card', icon: IdCard, label: t('nav_card') },
  ]
  return (
    <nav className="bottomnav" aria-label="Main">
      <ul>
        {items.map(({ to, icon: Icon, label, end, book }) => (
          <li key={to} className={book ? 'book' : undefined}>
            <NavLink to={to} end={end}>
              {book ? (
                <>
                  <span className="fab"><Icon size={28} strokeWidth={2.25} /></span>
                  <small>{label}</small>
                </>
              ) : (
                <>
                  <Icon size={24} strokeWidth={1.75} />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}

export function Sheet({ open, onClose, title, children }) {
  const ref = useRef(null)
  useEffect(() => {
    if (!open) return
    const prev = document.activeElement
    ref.current?.querySelector('input, button, textarea, select')?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('keydown', onKey); prev?.focus?.() }
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="scrim" onClick={onClose}>
      <div className="sheet" role="dialog" aria-modal="true" aria-label={title} ref={ref} onClick={(e) => e.stopPropagation()}>
        <div className="grabber" />
        {title && <h2>{title}</h2>}
        {children}
      </div>
    </div>
  )
}

export const Spinner = () => <div className="center" role="status"><div className="spinner" /><span className="sr-only">Loading</span></div>

export function Empty({ icon: Icon, text, action }) {
  return (
    <div className="empty">
      {Icon && <Icon size={36} strokeWidth={1.5} />}
      <p>{text}</p>
      {action}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  const { errText } = useApp()
  return <Empty text={errText(error)} action={onRetry && <button className="btn btn-ghost" onClick={onRetry}>↻</button>} />
}

export function Initials({ name, size }) {
  const parts = (name || '').replace(/^(د\.|أ\.|Dr\.)\s*/, '').split(' ').filter(Boolean)
  const ini = parts.slice(0, 2).map((p) => p[0]).join('')
  return <span className="avatar" style={size ? { inlineSize: size, blockSize: size } : undefined} aria-hidden="true">{ini}</span>
}

export function Trend({ trend }) {
  const { t } = useApp()
  const Icon = trend === 'improving' ? ArrowUpRight : trend === 'needs_attention' ? ArrowDownRight : Minus
  return <span className={`trend ${trend}`}><Icon size={16} aria-hidden="true" />{t(`trend_${trend}`)}</span>
}

/** Tiny line, no axes — beside indicators. */
export function Sparkline({ values = [], color = 'var(--primary)', width = 72, height = 26 }) {
  if (values.length < 2) return null
  const min = Math.min(...values), max = Math.max(...values), span = max - min || 1
  const pts = values.map((v, i) => [(i / (values.length - 1)) * (width - 4) + 2, height - 2 - ((v - min) / span) * (height - 4)])
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join('')
  const last = pts.at(-1)
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true" style={{ direction: 'ltr' }}>
      <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={last[0]} cy={last[1]} r="3" fill={color} />
    </svg>
  )
}

/** Line chart with a shaded normal range and labelled first/last points. Time always runs left→right. */
export function LineChart({ points = [], color = 'var(--primary)', range, unit = '', height = 160 }) {
  const { fmtDate, fmtNum } = useApp()
  if (points.length < 2) return null
  const W = 320, H = height, px = 14, top = 18, bottom = 26
  const vals = points.map((p) => p.v)
  let lo = Math.min(...vals), hi = Math.max(...vals)
  if (range?.[0] != null) lo = Math.min(lo, range[0])
  if (range?.[1] != null && range[1] < hi * 1.6) hi = Math.max(hi, range[1])
  const pad = (hi - lo || 1) * 0.12
  lo -= pad; hi += pad
  const X = (i) => px + (i / (points.length - 1)) * (W - 2 * px)
  const Y = (v) => top + (1 - (v - lo) / (hi - lo)) * (H - top - bottom)
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(p.v).toFixed(1)}`).join('')
  const band = range && range[0] != null && range[1] != null
    ? { y: Y(Math.min(range[1], hi)), h: Y(Math.max(range[0], lo)) - Y(Math.min(range[1], hi)) } : null
  const first = points[0], last = points.at(-1)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${fmtNum(first.v)} → ${fmtNum(last.v)} ${unit}`} style={{ direction: 'ltr', display: 'block' }}>
      {band && <rect x={px} y={band.y} width={W - 2 * px} height={Math.max(0, band.h)} fill="color-mix(in srgb, var(--good) 12%, transparent)" rx="6" />}
      <path d={d} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      {points.map((p, i) => <circle key={i} cx={X(i)} cy={Y(p.v)} r={i === points.length - 1 ? 4.5 : 2.5} fill={i === points.length - 1 ? color : 'var(--surface)'} stroke={color} strokeWidth="2" />)}
      <text x={X(points.length - 1)} y={Y(last.v) - 10} textAnchor="end" fontSize="13" fontWeight="600" fill="var(--ink)">{fmtNum(last.v)}</text>
      <text x={X(0)} y={Y(first.v) - 10} textAnchor="start" fontSize="12" fill="var(--ink-2)">{fmtNum(first.v)}</text>
      <text x={px} y={H - 6} fontSize="11" fill="var(--ink-2)">{fmtDate(first.t)}</text>
      <text x={W - px} y={H - 6} fontSize="11" fill="var(--ink-2)" textAnchor="end">{fmtDate(last.t)}</text>
    </svg>
  )
}

export function ProgressRing({ value = 0, size = 60, color = 'var(--primary)', label }) {
  const r = (size - 8) / 2, c = 2 * Math.PI * r
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={label ?? `${Math.round(value * 100)}%`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth="7" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
        strokeDasharray={`${c * value} ${c}`} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" fontSize="14" fontWeight="700" fill="var(--ink)">{Math.round(value * 100)}%</text>
    </svg>
  )
}

/** Where a value sits relative to its normal range. */
export function RangeBar({ value, range }) {
  const [lo, hi] = range || []
  if (lo == null || hi == null) return null
  const min = Math.min(lo, value) - (hi - lo) * 0.3, max = Math.max(hi, value) + (hi - lo) * 0.3
  const pos = (v) => ((v - min) / (max - min)) * 100
  return (
    <div className="rangebar" aria-hidden="true">
      <div className="ok" style={{ insetInlineStart: `${pos(lo)}%`, inlineSize: `${pos(hi) - pos(lo)}%` }} />
      <div className="mark" style={{ insetInlineStart: `${pos(value)}%` }} />
    </div>
  )
}

export function Chevron() {
  return <ChevronLeft size={20} className="chev" style={{ transform: 'var(--chev-flip)' }} aria-hidden="true" />
}

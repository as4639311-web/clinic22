import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Check, LifeBuoy, MessageCircle, Settings, Sparkles, Video } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { BellButton, Chevron, PLAN_SERVICE, ServiceIcon, Spinner, TopBar } from '../components/ui'
import { relative } from '../utils'

const FACES = ['😞', '🙁', '😐', '🙂', '😄']

export default function Home() {
  const { t, pick, session, fmtDate, fmtTime, locale } = useApp()
  const upcoming = useData('/appointments?scope=upcoming')
  const today = useData('/plans/today')
  const checkin = useData('/card/checkin/today')
  const notes = useData('/notifications')
  const hour = new Date().getHours()
  const first = (session.user.full_name || '').split(' ')[0]
  const next = upcoming.data?.[0]
  const unread = (notes.data?.items || []).filter((n) => !n.read).length + (notes.data?.smart || []).filter((s) => s.priority !== 'low').length

  return (
    <>
      <TopBar
        title={t('appName')}
        actions={
          <>
            <BellButton unread={unread} />
            <Link className="icon-btn" to="/settings" aria-label={t('settings')}><Settings size={22} strokeWidth={1.75} /></Link>
          </>
        }
      />
      <div className="page">
        <div className="greet">
          <h2>{hour < 12 ? t('goodMorning') : t('goodEvening')}{locale === 'ar' ? '، ' : ', '}{first}</h2>
          <p className="muted">{t('todaySummary')}</p>
        </div>

        <section className="section" aria-labelledby="h-next">
          <h3 id="h-next">{t('nextAppointment')}</h3>
          {upcoming.loading ? <Spinner /> : next ? (
            <Link to={`/appointments/${next.id}`} className="next-appt" style={{ '--c': `var(--${next.service})`, textDecoration: 'none', color: 'inherit' }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <ServiceIcon service={next.service} />
                <div style={{ flex: 1 }}>
                  <div className="title" style={{ fontWeight: 600 }}>{pick(next.specialist.name)}</div>
                  <div className="muted small">{t(`svc_${next.service}`)} · {t(`mode_${next.mode}`)}</div>
                </div>
                <span className="badge good">{relative(next.starts_at, t)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="num">{fmtDate(next.starts_at, { weekday: 'long', day: 'numeric', month: 'long' })} · {fmtTime(next.starts_at)}</span>
                {next.mode !== 'in_person' && <span className="btn btn-soft" style={{ minBlockSize: 40 }}><Video size={18} />{t('join')}</span>}
              </div>
            </Link>
          ) : (
            <div className="panel empty">
              <p>{t('noUpcoming')}</p>
              <Link to="/book" className="btn btn-primary">{t('bookNow')}</Link>
            </div>
          )}
        </section>

        <CheckIn done={checkin.data?.done} onSaved={() => checkin.setData({ done: true })} />

        <section className="section" aria-labelledby="h-tasks">
          <div className="section-head">
            <h3 id="h-tasks">{t('todayTasks')}</h3>
            {today.data?.tasks?.length > 0 && (
              <span className="muted small">{t('tasksDone', { done: today.data.tasks.filter((x) => x.done).length, total: today.data.tasks.length })}</span>
            )}
          </div>
          {today.loading ? <Spinner /> : today.data?.tasks?.length ? (
            <TaskList data={today.data} setData={today.setData} />
          ) : <div className="panel empty"><p>{t('noTasks')}</p></div>}
        </section>

        <section className="section" aria-labelledby="h-quick">
          <h3 id="h-quick">{t('quick')}</h3>
          <div className="list">
            <QuickRow to="/library" icon={<BookOpen size={22} />} label={t('library')} />
            <QuickRow to="/messages" icon={<MessageCircle size={22} />} label={t('messages')} />
            <QuickRow to="/assistant" icon={<Sparkles size={22} />} label={t('assistant')} />
            <QuickRow to="/urgent" icon={<LifeBuoy size={22} />} label={t('urgent')} tone="var(--error)" />
          </div>
        </section>
      </div>
    </>
  )
}

function QuickRow({ to, icon, label, tone }) {
  return (
    <Link to={to} className="row">
      <span className="svc-dot" style={{ background: `color-mix(in srgb, ${tone || 'var(--primary)'} 14%, transparent)`, color: tone || 'var(--primary)' }}>{icon}</span>
      <span className="grow title">{label}</span>
      <Chevron />
    </Link>
  )
}

export function TaskList({ data, setData }) {
  const { pick, t } = useApp()
  async function toggle(task) {
    const done = !task.done
    setData({ ...data, tasks: data.tasks.map((x) => (x.id === task.id ? { ...x, done } : x)) })
    try { await api.post('/plans/log', { item_id: task.id, day: data.date, done }) } catch {
      setData({ ...data, tasks: data.tasks.map((x) => (x.id === task.id ? { ...x, done: task.done } : x)) })
    }
  }
  return (
    <div className="list">
      {data.tasks.map((task) => (
        <div key={task.id} className={`task${task.done ? ' done' : ''}`}>
          <button className="check" role="checkbox" aria-checked={task.done} aria-label={pick(task.title)} onClick={() => toggle(task)}>
            <Check size={16} strokeWidth={3} />
          </button>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="title" style={{ fontWeight: 500 }}>{pick(task.title)}</div>
            <div className="muted small">{t(`plan_${task.plan_kind}`)}{task.duration_min ? ` · ${t('minutes', { n: task.duration_min })}` : ''}</div>
          </div>
          <span style={{ inlineSize: 10, blockSize: 10, borderRadius: 4, background: `var(--${PLAN_SERVICE[task.plan_kind]})` }} aria-hidden="true" />
        </div>
      ))}
    </div>
  )
}

function CheckIn({ done, onSaved }) {
  const { t, notify, errText } = useApp()
  const [v, setV] = useState({ mood: 0, energy: 0, sleep_hours: 7 })
  if (done === undefined) return null
  if (done) return <p className="panel muted small" style={{ display: 'flex', gap: 8, alignItems: 'center' }}><Check size={18} color="var(--good)" />{t('checkinDone')}</p>

  async function save() {
    try {
      await api.post('/card/checkin', v)
      notify(t('checkinDone'))
      onSaved()
    } catch (e) { notify(errText(e)) }
  }
  return (
    <section className="panel section" aria-labelledby="h-check">
      <h3 id="h-check">{t('checkinTitle')}</h3>
      {['mood', 'energy'].map((k) => (
        <div key={k} className="field">
          <span className="small muted">{t(k === 'mood' ? 'checkinMood' : 'checkinEnergy')}</span>
          <div className="faces" role="radiogroup" aria-label={t(k === 'mood' ? 'checkinMood' : 'checkinEnergy')}>
            {FACES.map((f, i) => (
              <button key={i} role="radio" aria-checked={v[k] === i + 1} aria-pressed={v[k] === i + 1} aria-label={`${i + 1}/5`}
                onClick={() => setV({ ...v, [k]: i + 1 })}>{f}</button>
            ))}
          </div>
        </div>
      ))}
      <div className="field">
        <label htmlFor="sleep" className="small muted">{t('checkinSleep')}: <b className="num" style={{ color: 'var(--ink)' }}>{v.sleep_hours}</b></label>
        <input id="sleep" type="range" min="3" max="11" step="0.5" value={v.sleep_hours} style={{ accentColor: 'var(--primary)' }}
          onChange={(e) => setV({ ...v, sleep_hours: Number(e.target.value) })} />
      </div>
      <button className="btn btn-primary" disabled={!v.mood || !v.energy} onClick={save}>{t('checkinSave')}</button>
    </section>
  )
}

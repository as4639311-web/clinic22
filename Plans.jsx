import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Check, ListChecks, MessageSquareText } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { Chevron, Empty, ErrorBox, PLAN_SERVICE, ProgressRing, ServiceIcon, Sheet, Spinner, TopBar } from '../components/ui'
import { TaskList } from './Home'
import { isoDay } from '../utils'

export function Plans() {
  const { t, pick } = useApp()
  const plans = useData('/plans')
  const today = useData('/plans/today')
  return (
    <>
      <TopBar title={t('nav_plans')} />
      <div className="page">
        {plans.loading ? <Spinner /> : plans.error ? <ErrorBox error={plans.error} onRetry={plans.reload} /> : !plans.data.length ? (
          <Empty icon={ListChecks} text={t('noPlans')} action={<Link to="/book" className="btn btn-primary">{t('bookNow')}</Link>} />
        ) : (
          <>
            <div className="list">
              {plans.data.map((p) => (
                <Link key={p.id} to={`/plans/${p.id}`} className="row">
                  <ServiceIcon service={PLAN_SERVICE[p.kind]} />
                  <span className="grow">
                    <span className="title">{pick(p.title)}</span><br />
                    <span className="muted small">{t(`plan_${p.kind}`)}{p.specialist ? ` · ${t('byWith', { name: pick(p.specialist.name) })}` : ''}</span>
                  </span>
                  {p.adherence_week != null && <ProgressRing value={p.adherence_week} size={52} color={`var(--${PLAN_SERVICE[p.kind]})`} label={`${t('adherenceWeek')} ${Math.round(p.adherence_week * 100)}%`} />}
                  <Chevron />
                </Link>
              ))}
            </div>
            {today.data?.tasks?.length > 0 && (
              <section className="section">
                <h3>{t('todayTasks')}</h3>
                <TaskList data={today.data} setData={today.setData} />
              </section>
            )}
          </>
        )}
      </div>
    </>
  )
}

export function PlanDetail() {
  const { id } = useParams()
  const { t, pick, fmtDate, notify, errText } = useApp()
  const { data: p, loading, error, reload, setData } = useData(`/plans/${id}`)
  const todayIdx = (new Date().getDay() + 6) % 7 // Monday = 0
  const [day, setDay] = useState(todayIdx)
  const [ask, setAsk] = useState(false)
  const [msg, setMsg] = useState('')

  if (loading) return <><TopBar title="" back /><Spinner /></>
  if (error) return <><TopBar title="" back /><ErrorBox error={error} onRetry={reload} /></>

  const weekStart = new Date(); weekStart.setDate(weekStart.getDate() - todayIdx)
  const dateOf = (i) => { const d = new Date(weekStart); d.setDate(weekStart.getDate() + i); return isoDay(d) }
  const isDone = (itemId, i) => p.done_this_week.some((x) => x.item_id === itemId && x.day === dateOf(i))
  const items = p.items.filter((x) => x.weekday === day)
  const color = `var(--${PLAN_SERVICE[p.kind]})`

  async function toggle(item) {
    const done = !isDone(item.id, day)
    const d = dateOf(day)
    const next = done ? [...p.done_this_week, { item_id: item.id, day: d }] : p.done_this_week.filter((x) => !(x.item_id === item.id && x.day === d))
    setData({ ...p, done_this_week: next })
    try { await api.post('/plans/log', { item_id: item.id, day: d, done }) } catch (e) { notify(errText(e)); reload() }
  }
  async function sendChange() {
    try {
      await api.post(`/plans/${p.id}/change-request`, { message: msg })
      setAsk(false); setMsg(''); notify(t('changeSent'))
    } catch (e) { notify(errText(e)) }
  }

  return (
    <>
      <TopBar title={t(`plan_${p.kind}`)} back />
      <div className="page">
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <ServiceIcon service={PLAN_SERVICE[p.kind]} />
          <div>
            <h2>{pick(p.title)}</h2>
            <p className="muted small">{p.specialist && t('byWith', { name: pick(p.specialist.name) })} · {t('version', { v: p.version })}</p>
          </div>
        </div>

        {p.suggest_review && (
          <div className="hint" role="note" style={{ display: 'grid', gap: 10 }}>
            <p>{t('reviewSuggest')}</p>
            <button className="btn btn-primary" style={{ justifySelf: 'start' }} onClick={() => setAsk(true)}>{t('requestChange')}</button>
          </div>
        )}

        <div className="weekgrid" role="tablist" aria-label={t('wd')[day]}>
          {t('wds').map((label, i) => {
            const dayItems = p.items.filter((x) => x.weekday === i)
            return (
              <button key={i} role="tab" aria-selected={day === i} aria-pressed={day === i} onClick={() => setDay(i)} aria-label={t('wd')[i]}>
                <span style={{ fontWeight: i === todayIdx ? 700 : 500 }}>{label}</span>
                <span className="num muted">{new Date(dateOf(i) + 'T12:00').getDate()}</span>
                <span className="pips">{dayItems.slice(0, 4).map((x) => <i key={x.id} className={i <= todayIdx && isDone(x.id, i) ? 'on' : ''} />)}</span>
              </button>
            )
          })}
        </div>

        <section className="section">
          <h3>{t('wd')[day]}</h3>
          {!items.length ? <p className="muted">{t('noTasks')}</p> : (
            <div className="list">
              {items.map((it) => {
                const done = isDone(it.id, day)
                return (
                  <div key={it.id} className={`task${done ? ' done' : ''}`} style={{ alignItems: 'flex-start' }}>
                    <button className="check" role="checkbox" aria-checked={done} aria-label={pick(it.title)} disabled={day > todayIdx}
                      onClick={() => toggle(it)} style={{ marginBlockStart: 2 }}><Check size={16} strokeWidth={3} /></button>
                    <div style={{ flex: 1 }}>
                      <div className="title" style={{ fontWeight: 600 }}>{pick(it.title)}</div>
                      {pick(it.detail) && <p className="muted small">{pick(it.detail)}</p>}
                      {it.duration_min && <span className="badge" style={{ marginBlockStart: 6 }}>{t('minutes', { n: it.duration_min })}</span>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        <section className="panel section">
          <h3>{t('adherence6')}</h3>
          <div className="bars">
            {p.weekly_adherence.map((w) => (
              <div key={w.week_end}>
                <b className="num">{w.adherence == null ? '–' : `${Math.round(w.adherence * 100)}%`}</b>
                <i className={`bar${w.adherence != null && w.adherence < 0.6 ? ' low' : ''}`}
                  style={{ blockSize: `${(w.adherence || 0) * 72}px`, background: w.adherence != null && w.adherence >= 0.6 ? color : undefined }} />
                <small className="num">{fmtDate(w.week_end, { day: 'numeric', month: 'numeric' })}</small>
              </div>
            ))}
          </div>
        </section>

        <button className="btn btn-ghost btn-block" onClick={() => setAsk(true)}><MessageSquareText size={20} />{t('requestChange')}</button>
      </div>

      <Sheet open={ask} onClose={() => setAsk(false)} title={t('requestChange')}>
        <textarea className="input" aria-label={t('requestChange')} placeholder={t('changePh')} value={msg} onChange={(e) => setMsg(e.target.value)} />
        <button className="btn btn-primary btn-block" disabled={msg.trim().length < 2} onClick={sendChange}>{t('send')}</button>
      </Sheet>
    </>
  )
}

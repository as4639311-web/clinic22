import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CalendarDays, CalendarPlus, Lock, MessageCircle, RotateCcw, Video } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { Chevron, Empty, ErrorBox, Initials, ServiceIcon, Sheet, Spinner, TopBar } from '../components/ui'
import { downloadIcs, relative } from '../utils'

export function Appointments() {
  const { t, pick, fmtDate, fmtTime } = useApp()
  const [scope, setScope] = useState('upcoming')
  const { data, loading, error, reload } = useData(`/appointments?scope=${scope}`, [scope])

  return (
    <>
      <TopBar title={t('nav_appointments')} />
      <div className="page">
        <div className="segmented" role="tablist">
          {['upcoming', 'past'].map((s) => (
            <button key={s} role="tab" aria-selected={scope === s} aria-pressed={scope === s} onClick={() => setScope(s)}>{t(s)}</button>
          ))}
        </div>
        {loading ? <Spinner /> : error ? <ErrorBox error={error} onRetry={reload} /> : !data.length ? (
          <Empty icon={CalendarDays} text={scope === 'upcoming' ? t('noUpcoming') : t('noPast')}
            action={scope === 'upcoming' && <Link to="/book" className="btn btn-primary">{t('bookNow')}</Link>} />
        ) : (
          <div className="list">
            {data.map((a) => (
              <Link key={a.id} to={`/appointments/${a.id}`} className="row">
                <ServiceIcon service={a.service} />
                <span className="grow">
                  <span className="title">{pick(a.specialist.name)}</span><br />
                  <span className="muted small num">{fmtDate(a.starts_at, { weekday: 'short', day: 'numeric', month: 'short' })} · {fmtTime(a.starts_at)} · {t(`mode_${a.mode}`)}</span>
                </span>
                {scope === 'upcoming'
                  ? <span className="badge good">{relative(a.starts_at, t)}</span>
                  : <span className={`badge${a.status === 'cancelled' ? ' warn' : ''}`}>{t(`st_${a.status}`)}</span>}
                <Chevron />
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export function AppointmentDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { t, pick, fmtDate, fmtTime, notify, errText } = useApp()
  const { data: a, loading, error, reload, setData } = useData(`/appointments/${id}`)
  const [confirmCancel, setConfirmCancel] = useState(false)
  const [resched, setResched] = useState(false)

  if (loading) return <><TopBar title="" back /><Spinner /></>
  if (error) return <><TopBar title="" back /><ErrorBox error={error} onRetry={reload} /></>
  const upcoming = a.status === 'booked' && new Date(a.starts_at) > new Date(Date.now() - 3600e3)
  const joinable = upcoming && a.mode !== 'in_person' && new Date(a.starts_at) - Date.now() < 15 * 60e3

  async function cancel() {
    try {
      setData(await api.post(`/appointments/${a.id}/cancel`))
      setConfirmCancel(false)
      notify(t('cancelled'))
    } catch (e) { notify(errText(e)) }
  }

  return (
    <>
      <TopBar title={t(`svc_${a.service}`)} back />
      <div className="page">
        <div className="panel" style={{ display: 'grid', gap: 14, borderInlineStart: `4px solid var(--${a.service})` }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Initials name={pick(a.specialist.name)} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>{pick(a.specialist.name)}</div>
              <div className="muted small">{pick(a.specialist.title)}</div>
            </div>
            <span className={`badge${a.status === 'cancelled' ? ' warn' : a.status === 'booked' ? ' good' : ''}`}>{t(`st_${a.status}`)}</span>
          </div>
          <dl className="kv">
            <dt>{t('step_time')}</dt><dd className="num">{fmtDate(a.starts_at, { weekday: 'long', day: 'numeric', month: 'long' })} · {fmtTime(a.starts_at)}</dd>
            <dt>{t('sessionType')}</dt><dd>{t(`mode_${a.mode}`)}</dd>
            {a.reason && <><dt>{t('reason').replace(/ \(.*\)/, '')}</dt><dd>{a.reason}</dd></>}
            {a.shared_sections?.length > 0 && <><dt>{t('share')}</dt><dd>{a.shared_sections.map((s) => t(`sec_${s}`)).join('، ')}</dd></>}
          </dl>
          {upcoming && a.mode !== 'in_person' && (
            <button className="btn btn-primary" disabled={!joinable}><Video size={20} />{t('join')}{!joinable && ` · ${relative(a.starts_at, t)}`}</button>
          )}
        </div>

        {a.summary && (
          <section className="panel section">
            <h3 style={{ display: 'flex', gap: 6, alignItems: 'center' }}>{a.sensitive && <Lock size={16} />}{t('sessionSummary')}</h3>
            <p>{a.summary}</p>
          </section>
        )}

        <div className="list">
          <Link to={`/messages/${a.specialist.id}`} className="row"><MessageCircle size={22} color="var(--primary)" /><span className="grow">{t('message')}</span><Chevron /></Link>
          {upcoming && (
            <>
              <button className="row" onClick={() => downloadIcs({ title: `${t('appName')}: ${pick(a.specialist.name)}`, start: a.starts_at, minutes: a.duration_min })}>
                <CalendarPlus size={22} color="var(--primary)" /><span className="grow">{t('addToCalendar')}</span><Chevron />
              </button>
              <button className="row" onClick={() => setResched(true)}><CalendarDays size={22} color="var(--primary)" /><span className="grow">{t('reschedule')}</span><Chevron /></button>
            </>
          )}
          {!upcoming && (
            <button className="row" onClick={() => nav(`/book?service=${a.service}&specialist=${a.specialist.id}`)}>
              <RotateCcw size={22} color="var(--primary)" /><span className="grow">{t('bookNow')}</span><Chevron />
            </button>
          )}
        </div>
        {upcoming && <button className="btn btn-danger btn-block" onClick={() => setConfirmCancel(true)}>{t('cancel')}</button>}
      </div>

      <Sheet open={confirmCancel} onClose={() => setConfirmCancel(false)} title={t('cancelConfirm')}>
        <div className="btn-row">
          <button className="btn btn-danger" style={{ flex: 1 }} onClick={cancel}>{t('cancel')}</button>
          <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setConfirmCancel(false)}>{t('keep')}</button>
        </div>
      </Sheet>
      <Reschedule open={resched} appt={a} onClose={() => setResched(false)} onDone={(x) => { setData(x); setResched(false); notify(t('rescheduled')) }} />
    </>
  )
}

function Reschedule({ open, appt, onClose, onDone }) {
  const { t, fmtDate, fmtTime, errText } = useApp()
  const [days, setDays] = useState(null)
  const [day, setDay] = useState(null)
  const [slot, setSlot] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    if (!open) return
    api.get(`/specialists/${appt.specialist.id}/availability?days=14`).then((d) => {
      setDays(d)
      setDay(d.find((x) => x.slots.length)?.date)
    }).catch((e) => setErr(errText(e)))
  }, [open, appt.specialist.id, errText])

  async function save() {
    try { onDone(await api.post(`/appointments/${appt.id}/reschedule`, { starts_at: slot })) } catch (e) { setErr(errText(e)) }
  }
  const slots = days?.find((d) => d.date === day)?.slots || []
  return (
    <Sheet open={open} onClose={onClose} title={t('reschedule')}>
      {!days ? <Spinner /> : (
        <>
          <div className="days">
            {days.map((d) => (
              <button key={d.date} className="day" aria-pressed={day === d.date} disabled={!d.slots.length} onClick={() => { setDay(d.date); setSlot(null) }}>
                <span className="small">{fmtDate(d.date + 'T12:00', { weekday: 'short' })}</span>
                <b className="num">{new Date(d.date + 'T12:00').getDate()}</b>
              </button>
            ))}
          </div>
          <div className="slots">
            {slots.map((s) => <button key={s} className="slot num" aria-pressed={slot === s} onClick={() => setSlot(s)}>{fmtTime(s)}</button>)}
          </div>
          {err && <p className="error-text" role="alert">{err}</p>}
          <button className="btn btn-primary btn-block" disabled={!slot} onClick={save}>{t('reschedule')}</button>
        </>
      )}
    </Sheet>
  )
}

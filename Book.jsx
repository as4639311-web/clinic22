import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CalendarPlus, CheckCircle2, HelpCircle, Star } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { Chevron, ErrorBox, Initials, ServiceIcon, Sheet, Spinner, TopBar } from '../components/ui'
import { downloadIcs } from '../utils'

const SERVICES = ['mental', 'fitness', 'sports_medicine', 'nutrition', 'education']
const SECTION_FOR = { mental: 'mental', fitness: 'physical', sports_medicine: 'physical', nutrition: 'nutrition', education: 'goals' }

export default function Book() {
  const { t } = useApp()
  const [params] = useSearchParams()
  const [step, setStep] = useState(params.get('specialist') ? 2 : params.get('service') ? 1 : 0)
  const [service, setService] = useState(params.get('service'))
  const [specialist, setSpecialist] = useState(null)
  const [slot, setSlot] = useState(null)
  const [mode, setMode] = useState(null)
  const [result, setResult] = useState(null)

  // rebook shortcut: /book?service=x&specialist=id
  useEffect(() => {
    const id = params.get('specialist')
    if (id) api.get(`/specialists/${id}`).then((s) => { setSpecialist(s); setService(s.service); setMode(s.modes[0]) }).catch(() => setStep(0))
  }, [params])

  if (result) return <Success appt={result} />
  const titles = [t('step_service'), t('step_specialist'), t('step_time'), t('step_confirm')]

  return (
    <>
      <TopBar title={t('book_title')} />
      <div className="page">
        <div className="steps" aria-hidden="true">{titles.map((_, i) => <span key={i} className={i <= step ? 'on' : ''} />)}</div>
        <h2 aria-live="polite">{titles[step]}</h2>
        {step > 0 && (
          <button className="btn btn-ghost" style={{ justifySelf: 'start' }} onClick={() => setStep(step - 1)}>{t('back')}</button>
        )}
        {step === 0 && <StepService onPick={(s) => { setService(s); setStep(1) }} />}
        {step === 1 && <StepSpecialist service={service} onPick={(sp, firstSlot) => {
          setSpecialist(sp); setMode(sp.modes[0]); setSlot(firstSlot || null); setStep(firstSlot ? 3 : 2)
        }} />}
        {step === 2 && specialist && <StepTime specialist={specialist} slot={slot} setSlot={setSlot} mode={mode} setMode={setMode} onNext={() => setStep(3)} />}
        {step === 3 && specialist && slot && <StepConfirm specialist={specialist} slot={slot} mode={mode} service={service}
          onEditTime={() => setStep(2)} onBooked={setResult} />}
      </div>
    </>
  )
}

function StepService({ onPick }) {
  const { t } = useApp()
  const [quiz, setQuiz] = useState(false)
  const answers = [['q1a', 'mental'], ['q1b', 'fitness'], ['q1c', 'sports_medicine'], ['q1d', 'nutrition'], ['q1e', 'education']]
  return (
    <>
      <div className="services">
        {SERVICES.map((s) => (
          <button key={s} className={`svc${s === 'education' ? ' wide' : ''}`} style={{ '--c': `var(--${s})` }} onClick={() => onPick(s)}>
            <ServiceIcon service={s} size={24} />
            <div>
              <div style={{ fontWeight: 600 }}>{t(`svc_${s}`)}</div>
              <div className="muted small">{t(`svcd_${s}`)}</div>
            </div>
          </button>
        ))}
      </div>
      <button className="row panel" onClick={() => setQuiz(true)}>
        <HelpCircle size={24} color="var(--primary)" />
        <span className="grow"><span className="title">{t('notSure')}</span><br /><span className="muted small">{t('notSureDesc')}</span></span>
        <Chevron />
      </button>
      <Sheet open={quiz} onClose={() => setQuiz(false)} title={t('q1')}>
        <div className="list">
          {answers.map(([k, svc]) => (
            <button key={k} className="row" onClick={() => { setQuiz(false); onPick(svc) }}>
              <ServiceIcon service={svc} />
              <span className="grow">{t(k)}<br /><span className="muted small">{t('suggested', { s: t(`svc_${svc}`) })}</span></span>
              <Chevron />
            </button>
          ))}
        </div>
      </Sheet>
    </>
  )
}

function StepSpecialist({ service, onPick }) {
  const { t, pick, fmtDate, fmtTime } = useApp()
  const [gender, setGender] = useState('')
  const [mode, setMode] = useState('')
  const q = new URLSearchParams({ service, ...(gender && { gender }), ...(mode && { mode }) })
  const { data, error, loading, reload } = useData(`/specialists?${q}`, [gender, mode])
  const soonest = data?.find((s) => s.next_slot)

  return (
    <>
      <div className="chips" role="group" aria-label={t('filters')}>
        {[['', t('any')], ['female', t('female')], ['male', t('male')]].map(([v, l]) => (
          <button key={v || 'g'} className="chip" aria-pressed={gender === v} onClick={() => setGender(v)}>{l}</button>
        ))}
        {['in_person', 'video'].map((m) => (
          <button key={m} className="chip" aria-pressed={mode === m} onClick={() => setMode(mode === m ? '' : m)}>{t(`mode_${m}`)}</button>
        ))}
      </div>
      {loading ? <Spinner /> : error ? <ErrorBox error={error} onRetry={reload} /> : (
        <div className="list">
          {soonest && (
            <button className="row" onClick={() => onPick(soonest, soonest.next_slot)}>
              <span className="svc-dot" style={{ background: 'var(--primary-soft)', color: 'var(--primary)' }}><CalendarPlus size={22} /></span>
              <span className="grow"><span className="title">{t('anySpecialist')}</span><br />
                <span className="muted small num">{t('anySpecialistDesc')}: {fmtDate(soonest.next_slot, { weekday: 'short', day: 'numeric', month: 'short' })} {fmtTime(soonest.next_slot)}</span></span>
              <Chevron />
            </button>
          )}
          {data.map((s) => (
            <button key={s.id} className="row" onClick={() => onPick(s)}>
              <Initials name={pick(s.name)} />
              <span className="grow">
                <span className="title">{pick(s.name)}</span><br />
                <span className="muted small">{pick(s.title)}</span><br />
                <span className="small" style={{ display: 'inline-flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}><Star size={14} fill="var(--warn)" color="var(--warn)" />{s.rating}</span>
                  <span className="muted">{t('years', { n: s.years })}</span>
                  {s.next_slot && <span className="badge good num">{fmtDate(s.next_slot, { weekday: 'short', day: 'numeric' })} {fmtTime(s.next_slot)}</span>}
                </span>
              </span>
              <Chevron />
            </button>
          ))}
        </div>
      )}
    </>
  )
}

function StepTime({ specialist, slot, setSlot, mode, setMode, onNext }) {
  const { t, fmtDate, fmtTime, locale } = useApp()
  const { data, loading, error, reload } = useData(`/specialists/${specialist.id}/availability?days=14`)
  const [day, setDay] = useState(null)
  useEffect(() => {
    if (data && !day) setDay((slot && data.find((d) => d.date === slot.slice(0, 10))?.date) || data.find((d) => d.slots.length)?.date || data[0].date)
  }, [data, day, slot])
  if (loading) return <Spinner />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const slots = data.find((d) => d.date === day)?.slots || []

  return (
    <>
      <div className="field">
        <span className="small muted">{t('sessionType')}</span>
        <div className="segmented" role="group" aria-label={t('sessionType')}>
          {specialist.modes.map((m) => <button key={m} aria-pressed={mode === m} onClick={() => setMode(m)}>{t(`mode_${m}`)}</button>)}
        </div>
      </div>
      <div className="days" role="group" aria-label={t('step_time')}>
        {data.map((d) => {
          const dt = new Date(d.date + 'T12:00')
          return (
            <button key={d.date} className="day" aria-pressed={day === d.date} disabled={!d.slots.length} onClick={() => { setDay(d.date); setSlot(null) }}>
              <span className="small">{dt.toLocaleDateString(locale === 'ar' ? 'ar-AE' : 'en-GB', { weekday: 'short' })}</span>
              <b className="num">{dt.toLocaleDateString(locale === 'ar' ? 'ar-AE' : 'en-GB', { day: 'numeric' })}</b>
            </button>
          )
        })}
      </div>
      {day && <p className="muted small">{fmtDate(day + 'T12:00', { weekday: 'long', day: 'numeric', month: 'long' })}</p>}
      {slots.length ? (
        <div className="slots">
          {slots.map((s) => <button key={s} className="slot num" aria-pressed={slot === s} onClick={() => setSlot(s)}>{fmtTime(s)}</button>)}
        </div>
      ) : <p className="muted">{t('noSlots')}</p>}
      <button className="btn btn-primary btn-block" disabled={!slot || !mode} onClick={onNext}>{t('next')}</button>
    </>
  )
}

function StepConfirm({ specialist, slot, mode, service, onEditTime, onBooked }) {
  const { t, pick, fmtDate, fmtTime, errText } = useApp()
  const defaults = useMemo(() => [SECTION_FOR[service], 'history'], [service])
  const [shared, setShared] = useState(defaults)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const options = ['history', 'physical', 'nutrition', 'mental', 'goals']
  const toggle = (s) => setShared(shared.includes(s) ? shared.filter((x) => x !== s) : [...shared, s])

  async function confirm() {
    setBusy(true); setErr('')
    try {
      onBooked(await api.post('/appointments', { specialist_id: specialist.id, starts_at: slot, mode, reason: reason || null, shared_sections: shared }))
    } catch (e) {
      setErr(errText(e))
      if (e.code === 'slot_unavailable') setTimeout(onEditTime, 1500)
    } finally { setBusy(false) }
  }

  return (
    <>
      <div className="panel" style={{ display: 'grid', gap: 12 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <ServiceIcon service={service} />
          <div>
            <div style={{ fontWeight: 600 }}>{pick(specialist.name)}</div>
            <div className="muted small">{pick(specialist.title)}</div>
          </div>
        </div>
        <dl className="kv">
          <dt>{t('step_time')}</dt>
          <dd className="num">{fmtDate(slot, { weekday: 'long', day: 'numeric', month: 'long' })} · {fmtTime(slot)}</dd>
          <dt>{t('sessionType')}</dt><dd>{t(`mode_${mode}`)}</dd>
        </dl>
        <button className="btn btn-ghost" style={{ justifySelf: 'start', minBlockSize: 40 }} onClick={onEditTime}>{t('reschedule')}</button>
      </div>
      <div className="field">
        <label htmlFor="reason">{t('reason')}</label>
        <textarea id="reason" className="input" placeholder={t('reasonPh')} value={reason} onChange={(e) => setReason(e.target.value)} maxLength={1000} />
      </div>
      <fieldset className="panel" style={{ margin: 0 }}>
        <legend style={{ fontWeight: 600, paddingInline: 4 }}>{t('shareWith')}</legend>
        {options.map((s) => (
          <label key={s} className="check-row">
            <input type="checkbox" checked={shared.includes(s)} onChange={() => toggle(s)} />
            <span>{t(`sec_${s}`)}</span>
          </label>
        ))}
        <p className="muted small">{t('shareHint')}</p>
      </fieldset>
      {err && <p className="error-text" role="alert">{err}</p>}
      <button className="btn btn-primary btn-block" disabled={busy} onClick={confirm}>{t('confirmBook')}</button>
    </>
  )
}

function Success({ appt }) {
  const { t, pick, fmtDate, fmtTime } = useApp()
  const nav = useNavigate()
  return (
    <div className="page">
      <div className="success">
        <span className="ring"><CheckCircle2 size={48} /></span>
        <h1>{t('booked')}</h1>
        <p className="num">{pick(appt.specialist.name)}<br />{fmtDate(appt.starts_at, { weekday: 'long', day: 'numeric', month: 'long' })} · {fmtTime(appt.starts_at)}</p>
        <p className="muted">{t('bookedDesc')}</p>
      </div>
      <button className="btn btn-ghost btn-block" onClick={() => downloadIcs({
        title: `${t('appName')}: ${pick(appt.specialist.name)}`, start: appt.starts_at, minutes: appt.duration_min,
      })}><CalendarPlus size={20} />{t('addToCalendar')}</button>
      <button className="btn btn-primary btn-block" onClick={() => nav('/appointments', { replace: true })}>{t('viewAppointments')}</button>
      <Link to="/" className="btn btn-block" style={{ color: 'var(--primary)' }}>{t('nav_home')}</Link>
    </div>
  )
}

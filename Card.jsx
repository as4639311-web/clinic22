import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ChevronDown, Droplet, FileDown, Info, Lock, Plus, Share2, Users } from 'lucide-react'
import { useApp, useData } from '../state'
import { api, isUnlocked, setUnlock } from '../api/client'
import {
  Chevron, DOMAIN_COLOR, DOMAIN_ICON, ErrorBox, LineChart, ProgressRing, RangeBar, ServiceIcon, Sheet, Sparkline, Spinner, TopBar, Trend,
} from '../components/ui'

const DOMAINS = ['mental', 'physical', 'nutrition', 'general']

export default function Card() {
  const { t, pick, fmtDate, fmtTime, fmtNum } = useApp()
  const [unlockKey, setUnlockKey] = useState(0)
  const card = useData('/card', [unlockKey])
  const [tlDomain, setTlDomain] = useState('')
  const timeline = useData(`/card/timeline${tlDomain ? `?domain=${tlDomain}` : ''}`, [tlDomain, unlockKey])
  const [unlockOpen, setUnlockOpen] = useState(false)
  const [detail, setDetail] = useState(null) // {name, unit, range, color, kind}
  const [measure, setMeasure] = useState(false)

  // re-lock automatically when the unlock window ends
  useEffect(() => {
    if (!isUnlocked()) return
    const id = setTimeout(() => setUnlockKey((k) => k + 1), 5 * 60e3 + 500)
    return () => clearTimeout(id)
  }, [unlockKey])

  if (card.loading && !card.data) return <><TopBar title={t('card_title')} /><Spinner /></>
  if (card.error) return <><TopBar title={t('card_title')} /><ErrorBox error={card.error} onRetry={card.reload} /></>
  const c = card.data
  const p = c.profile
  const visibleTo = c.active_shares.map((s) => pick(s.specialist.name)).join('، ')

  return (
    <>
      <TopBar title={t('card_title')} />
      <div className="page">
        {/* 1. who */}
        <section className="idcard" aria-label={t('card_title')}>
          <div className="who">
            <span className="avatar" aria-hidden="true">{p.full_name.slice(0, 1)}</span>
            <div>
              <h2 style={{ fontSize: '1.375rem' }}>{p.full_name}</h2>
              <p className="meta num">
                {p.age != null && t('age', { n: p.age })}{p.gender && ` · ${t(p.gender)}`} · <bdi style={{ whiteSpace: 'nowrap' }}>{t('fileNo', { n: p.file_number })}</bdi>
              </p>
            </div>
          </div>
          {(c.alerts.allergies.length > 0 || c.alerts.blood_type) && (
            <div className="tags">
              {c.alerts.allergies.map((a, i) => <span key={i} className="tag"><AlertTriangle size={14} />{t('allergy')}: {pick(a)}</span>)}
              {c.alerts.blood_type && <span className="tag"><Droplet size={14} />{t('bloodType')} <bdi>{c.alerts.blood_type}</bdi></span>}
            </div>
          )}
          <div className="actions no-print">
            <Link to="/card/share" className="btn"><Share2 size={18} />{t('share')}</Link>
            <button className="btn" onClick={() => window.print()}><FileDown size={18} />{t('export')}</button>
          </div>
        </section>

        {/* 2. how I am now */}
        <section className="section" aria-labelledby="h-status">
          <h3 id="h-status">{t('status')}</h3>
          <div className="indicators">
            {c.indicators.map((ind) => {
              const Icon = DOMAIN_ICON[ind.domain]
              const color = DOMAIN_COLOR[ind.domain]
              if (ind.locked) {
                return (
                  <button key={ind.domain} className="ind locked" style={{ '--c': color }} onClick={() => setUnlockOpen(true)}>
                    <Lock size={22} />
                    <span style={{ fontWeight: 600, color: 'var(--ink)' }}>{t(`dom_${ind.domain}`)}</span>
                    <span className="small">{t('unlockToView')}</span>
                  </button>
                )
              }
              if (ind.empty) {
                return (
                  <div key={ind.domain} className="ind" style={{ '--c': color }}>
                    <span className="label"><Icon size={16} color={color} />{t(`dom_${ind.domain}`)}</span>
                    <span className="muted small">{t('noData')}</span>
                  </div>
                )
              }
              const kind = ind.domain === 'general' ? { kind: 'mood' } : { assessment: ind.label.en }
              return (
                <button key={ind.domain} className="ind" style={{ '--c': color }}
                  onClick={() => setDetail({ title: pick(ind.label), unit: ind.unit, color, ...kind })}>
                  <span className="label"><Icon size={16} color={color} />{t(`dom_${ind.domain}`)}</span>
                  <span className="value num">{fmtNum(ind.value)} <small>{ind.unit}</small></span>
                  <span className="muted small" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{pick(ind.label)}</span>
                  <span className="foot">
                    <Trend trend={ind.trend} />
                    <Sparkline values={ind.spark} color={color} width={56} />
                  </span>
                </button>
              )
            })}
          </div>
        </section>

        {/* 3. what's next */}
        {c.next_appointment && (
          <section className="section">
            <h3>{t('nextAppointment')}</h3>
            {c.next_appointment.locked ? (
              <div className="panel muted" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Lock size={18} />{fmtDate(c.next_appointment.starts_at, { weekday: 'long', day: 'numeric', month: 'long' })}
              </div>
            ) : (
              <Link to={`/appointments/${c.next_appointment.id}`} className="row panel">
                <ServiceIcon service={c.next_appointment.service} />
                <span className="grow">
                  <span className="title">{pick(c.next_appointment.specialist.name)}</span><br />
                  <span className="muted small num">{fmtDate(c.next_appointment.starts_at, { weekday: 'long', day: 'numeric', month: 'long' })} · {fmtTime(c.next_appointment.starts_at)}</span>
                </span>
                <Chevron />
              </Link>
            )}
          </section>
        )}

        {/* 4. latest results */}
        <section className="section" aria-labelledby="h-results">
          <h3 id="h-results">{t('latestResults')}</h3>
          <div className="list">
            {c.recent_results.map((r) => (
              <button key={r.id} className="row" style={{ display: 'block' }}
                onClick={() => setDetail({ title: pick(r.name), unit: r.unit, range: r.range, color: DOMAIN_COLOR[r.domain], assessment: r.name.en, note: r.note })}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'baseline' }}>
                  <span className="title">{pick(r.name)}</span>
                  <span className="num" style={{ fontWeight: 700, fontSize: '1.125rem' }}>{fmtNum(r.value)} <span className="muted small" style={{ fontWeight: 400 }}>{r.unit}</span></span>
                </div>
                <RangeBar value={r.value} range={r.range} />
                <div className="small" style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                  <span className={`badge${r.status === 'normal' ? ' good' : ' warn'}`}>{t(`st_${r.status}`)}</span>
                  <span className="muted num">
                    {r.range[0] != null && t('normalRange', { lo: fmtNum(r.range[0]), hi: fmtNum(r.range[1]) })}
                    {r.previous != null && ` · ${t('prev', { v: fmtNum(r.previous) })}`}
                  </span>
                </div>
                {r.note && <p className="small" style={{ marginBlockStart: 8, color: 'var(--ink-2)' }}>{pick(r.note)}</p>}
              </button>
            ))}
          </div>
        </section>

        {/* 5. goals */}
        <section className="section" aria-labelledby="h-goals">
          <div className="section-head">
            <h3 id="h-goals">{t('goals')}</h3>
            <button className="btn btn-soft no-print" style={{ minBlockSize: 40 }} onClick={() => setMeasure(true)}><Plus size={18} />{t('addMeasurement')}</button>
          </div>
          <div className="list">
            {c.goals.map((g) => (
              <div key={g.id} className="row goal">
                <ProgressRing value={g.progress} size={60} color={DOMAIN_COLOR[g.domain]} />
                <div>
                  <div className="title">{pick(g.title)}</div>
                  <div className="muted small num">
                    {fmtNum(g.current_value)} / {fmtNum(g.target_value)} {g.unit}
                    {g.target_date && ` · ${t('targetBy', { d: fmtDate(g.target_date, { day: 'numeric', month: 'short' }) })}`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 6. medical history */}
        <details className="fold">
          <summary>{t('history')}<ChevronDown size={20} className="muted" /></summary>
          <div className="body">
            <dl className="kv">
              {[['h_chronic', 'chronic_conditions'], ['h_meds', 'medications'], ['h_allergies', 'allergies'], ['h_injuries', 'injuries'], ['h_surgeries', 'surgeries'], ['h_family', 'family_history']].map(([k, f]) => (
                <div key={f} style={{ display: 'contents' }}>
                  <dt>{t(k)}</dt>
                  <dd>{c.history[f].length ? c.history[f].map(pick).join('، ') : <span className="muted">{t('none')}</span>}</dd>
                </div>
              ))}
            </dl>
          </div>
        </details>

        {/* 7. timeline */}
        <section className="section" aria-labelledby="h-tl">
          <h3 id="h-tl">{t('timeline')}</h3>
          <div className="chips no-print">
            <button className="chip" aria-pressed={!tlDomain} onClick={() => setTlDomain('')}>{t('all')}</button>
            {DOMAINS.filter((d) => !c.locked_sections.includes(d)).map((d) => (
              <button key={d} className="chip" aria-pressed={tlDomain === d} onClick={() => setTlDomain(d)}>{t(`dom_${d}`)}</button>
            ))}
          </div>
          {timeline.loading ? <Spinner /> : (
            <ol className="timeline panel">
              {(timeline.data || []).slice(0, 12).map((e, i) => (
                <li key={i} style={{ '--c': DOMAIN_COLOR[e.domain] }}>
                  <span className="pin" aria-hidden="true" />
                  <div>
                    <div className="small muted num">{fmtDate(e.at, { day: 'numeric', month: 'short', year: 'numeric' })} · {t(`ev_${e.type}`)}</div>
                    <div style={{ fontWeight: 600 }}>{pick(e.title)}</div>
                    {e.detail && <p className="small muted">{e.detail}</p>}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>

        {visibleTo && (
          <Link to="/card/share" className="row panel no-print">
            <Users size={22} color="var(--primary)" />
            <span className="grow small">{t('sharedWith', { names: visibleTo })}</span>
            <Chevron />
          </Link>
        )}
      </div>

      <UnlockSheet open={unlockOpen} onClose={() => setUnlockOpen(false)} onUnlocked={() => { setUnlockOpen(false); setUnlockKey((k) => k + 1) }} />
      <DetailSheet detail={detail} onClose={() => setDetail(null)} />
      <MeasureSheet open={measure} onClose={() => setMeasure(false)} onSaved={() => { setMeasure(false); card.reload() }} />
    </>
  )
}

function UnlockSheet({ open, onClose, onUnlocked }) {
  const { t, errText } = useApp()
  const [pw, setPw] = useState('')
  const [err, setErr] = useState('')
  async function submit(e) {
    e.preventDefault()
    try {
      const r = await api.post('/card/unlock', { password: pw, sections: ['mental'] })
      setUnlock(r.unlock_token, r.expires_in)
      setPw(''); setErr('')
      onUnlocked()
    } catch (x) { setErr(errText(x)) }
  }
  return (
    <Sheet open={open} onClose={onClose} title={t('unlockTitle')}>
      <p className="muted">{t('unlockDesc')}</p>
      <form className="section" onSubmit={submit}>
        <div className="field">
          <label htmlFor="unlock-pw">{t('password')}</label>
          <input id="unlock-pw" className="input" type="password" dir="ltr" autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} />
        </div>
        {err && <p className="error-text" role="alert">{err}</p>}
        <button className="btn btn-primary btn-block" disabled={!pw}><Lock size={18} />{t('unlock')}</button>
      </form>
    </Sheet>
  )
}

function DetailSheet({ detail, onClose }) {
  const { t, pick } = useApp()
  const path = detail ? (detail.assessment ? `/card/series?days=365&assessment=${encodeURIComponent(detail.assessment)}` : `/card/series?days=30&kind=${detail.kind}`) : null
  const { data, loading } = useData(path, [path])
  return (
    <Sheet open={!!detail} onClose={onClose} title={detail?.title}>
      {loading ? <Spinner /> : data?.length > 1 ? (
        <LineChart points={data} color={detail.color} range={detail.range} unit={detail.unit} />
      ) : <p className="muted">{t('noData')}</p>}
      {detail?.range?.[0] != null && (
        <p className="small muted" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ inlineSize: 14, blockSize: 10, borderRadius: 3, background: 'color-mix(in srgb, var(--good) 25%, transparent)' }} />
          {t('normalRange', { lo: detail.range[0], hi: detail.range[1] })}
        </p>
      )}
      {detail?.note && (
        <div className="hint"><b>{t('noteFrom')}</b><p>{pick(detail.note)}</p></div>
      )}
      <Link to="/assistant" className="btn btn-ghost" onClick={onClose}><Info size={18} />{t('whatMeans')}</Link>
    </Sheet>
  )
}

function MeasureSheet({ open, onClose, onSaved }) {
  const { t, notify, errText } = useApp()
  const [kg, setKg] = useState('')
  async function save() {
    try {
      await api.post('/card/measurements', { kind: 'weight', value: Number(kg) })
      notify(t('saved')); setKg(''); onSaved()
    } catch (e) { notify(errText(e)) }
  }
  return (
    <Sheet open={open} onClose={onClose} title={t('addMeasurement')}>
      <div className="field">
        <label htmlFor="kg">{t('weight')} (kg)</label>
        <input id="kg" className="input num" type="number" inputMode="decimal" step="0.1" min="20" max="300" dir="ltr" value={kg} onChange={(e) => setKg(e.target.value)} />
      </div>
      <button className="btn btn-primary btn-block" disabled={!kg || Number(kg) < 20} onClick={save}>{t('saveMeasure')}</button>
    </Sheet>
  )
}

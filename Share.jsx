import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { Initials, Sheet, Spinner, TopBar } from '../components/ui'

const SECTIONS = ['profile', 'history', 'physical', 'nutrition', 'mental', 'goals', 'appointments', 'plans']

export default function Share() {
  const { t, pick, fmtDate, fmtTime, notify, errText } = useApp()
  const shares = useData('/shares')
  const specialists = useData('/specialists')
  const log = useData('/shares/access-log')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ sections: ['physical', 'nutrition'], specialist_id: null, duration: 'month' })

  const toggle = (s) => setForm({ ...form, sections: form.sections.includes(s) ? form.sections.filter((x) => x !== s) : [...form.sections, s] })

  async function create() {
    try {
      await api.post('/shares', form)
      notify(t('shared')); setOpen(false); shares.reload(); log.reload()
    } catch (e) { notify(errText(e)) }
  }
  async function revoke(id) {
    try { await api.post(`/shares/${id}/revoke`); notify(t('revoked')); shares.reload(); log.reload() } catch (e) { notify(errText(e)) }
  }

  const active = (shares.data || []).filter((s) => s.active)
  return (
    <>
      <TopBar title={t('share_title')} back />
      <div className="page">
        <button className="btn btn-primary btn-block" onClick={() => setOpen(true)}>{t('shareNow')}</button>

        <section className="section">
          <h3>{t('activeShares')}</h3>
          {shares.loading ? <Spinner /> : !active.length ? <p className="muted">{t('noShares')}</p> : (
            <div className="list">
              {active.map((s) => (
                <div key={s.id} className="row" style={{ alignItems: 'flex-start' }}>
                  <Initials name={pick(s.specialist.name)} />
                  <div className="grow">
                    <div className="title">{pick(s.specialist.name)}</div>
                    <div className="small">{s.sections.map((x) => t(`sec_${x}`)).join('، ')}</div>
                    <div className="muted small">{s.expires_at ? t('expires', { d: fmtDate(s.expires_at, { day: 'numeric', month: 'long' }) }) : t('noExpiry')}</div>
                  </div>
                  <button className="btn btn-danger" style={{ minBlockSize: 40 }} onClick={() => revoke(s.id)}>{t('revoke')}</button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="section">
          <h3 style={{ display: 'flex', gap: 6, alignItems: 'center' }}><ShieldCheck size={20} color="var(--primary)" />{t('accessLog')}</h3>
          <div className="list">
            {(log.data || []).slice(0, 15).map((e, i) => (
              <div key={i} className="row" style={{ minBlockSize: 52 }}>
                <span className="grow small">
                  {e.actor === 'self' ? t('actor_self') : e.actor} — {t(`act_${e.action}`)}
                  {e.section && e.section !== 'card' && `: ${e.section.split(',').map((x) => t(`sec_${x}`)).join('، ')}`}
                </span>
                <span className="muted small num">{fmtDate(e.at)} {fmtTime(e.at)}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <Sheet open={open} onClose={() => setOpen(false)} title={t('share_title')}>
        <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
          <legend style={{ fontWeight: 600 }}>{t('share_choose')}</legend>
          {SECTIONS.map((s) => (
            <label key={s} className="check-row">
              <input type="checkbox" checked={form.sections.includes(s)} onChange={() => toggle(s)} />{t(`sec_${s}`)}
            </label>
          ))}
        </fieldset>
        <div className="field">
          <label htmlFor="sp">{t('share_with')}</label>
          <select id="sp" className="input" value={form.specialist_id ?? ''} onChange={(e) => setForm({ ...form, specialist_id: Number(e.target.value) || null })}>
            <option value="">—</option>
            {(specialists.data || []).map((s) => <option key={s.id} value={s.id}>{pick(s.name)} — {pick(s.title)}</option>)}
          </select>
        </div>
        <div className="field">
          <span style={{ fontWeight: 500 }}>{t('share_duration')}</span>
          <div className="segmented">
            {['session', 'month', 'until_revoked'].map((d) => (
              <button key={d} aria-pressed={form.duration === d} onClick={() => setForm({ ...form, duration: d })}>{t(`dur_${d}`)}</button>
            ))}
          </div>
        </div>
        <button className="btn btn-primary btn-block" disabled={!form.specialist_id || !form.sections.length} onClick={create}>{t('shareNow')}</button>
      </Sheet>
    </>
  )
}

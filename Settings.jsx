import { Link } from 'react-router-dom'
import { Cpu, LogOut, ShieldCheck } from 'lucide-react'
import { useApp, useData } from '../state'
import { Chevron, TopBar } from '../components/ui'

export default function Settings() {
  const { t, prefs, updatePrefs, signOut, session } = useApp()
  const ai = useData('/assistant/status')
  return (
    <>
      <TopBar title={t('settings')} back />
      <div className="page">
        <section className="section">
          <h3>{t('language')}</h3>
          <div className="segmented">
            <button aria-pressed={prefs.locale === 'ar'} onClick={() => updatePrefs({ locale: 'ar' })} lang="ar">العربية</button>
            <button aria-pressed={prefs.locale === 'en'} onClick={() => updatePrefs({ locale: 'en' })} lang="en">English</button>
          </div>
        </section>
        <section className="section">
          <h3>{t('appearance')}</h3>
          <div className="segmented">
            {['light', 'dark', 'system'].map((th) => (
              <button key={th} aria-pressed={prefs.theme === th} onClick={() => updatePrefs({ theme: th })}>{t(`th_${th}`)}</button>
            ))}
          </div>
        </section>
        <section className="section">
          <h3>{t('privacy')}</h3>
          <div className="list">
            <Link to="/card/share" className="row"><ShieldCheck size={22} color="var(--primary)" /><span className="grow">{t('manageSharing')}</span><Chevron /></Link>
            <div className="row">
              <Cpu size={22} color="var(--primary)" />
              <span className="grow">{t('aiModel')}<br /><span className="muted small" dir="ltr">{ai.data ? `${ai.data.provider} · ${ai.data.model}` : '…'}</span></span>
            </div>
          </div>
        </section>
        <section className="section">
          <h3>{t('account')}</h3>
          <div className="panel">
            <div style={{ fontWeight: 600 }}>{session.user.full_name}</div>
            <div className="muted small" dir="ltr" style={{ textAlign: 'start' }}>{session.user.email}</div>
          </div>
          <button className="btn btn-danger btn-block" onClick={signOut}><LogOut size={20} className="flip" />{t('signOut')}</button>
        </section>
      </div>
    </>
  )
}

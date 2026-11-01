import { Ambulance, HeartHandshake, MessageCircle, Phone } from 'lucide-react'
import { useApp } from '../state'
import { TopBar } from '../components/ui'

export default function Emergency() {
  const { t } = useApp()
  return (
    <>
      <TopBar title={t('emergencyTitle')} back />
      <div className="page">
        <p style={{ fontSize: '1.125rem' }}>{t('emergencyIntro')}</p>
        <a href="tel:999" className="btn btn-block" style={{ background: 'var(--error)', color: '#fff', minBlockSize: 56, fontSize: '1.125rem' }}>
          <Phone size={22} />{t('callEmergency')}
        </a>
        <a href="tel:998" className="btn btn-ghost btn-block" style={{ minBlockSize: 56 }}><Ambulance size={22} />{t('callAmbulance')}</a>
        <div className="list">
          <a href="tel:+971000000000" className="row">
            <MessageCircle size={22} color="var(--primary)" />
            <span className="grow"><span className="title">{t('onCall')}</span><br /><span className="muted small">{t('onCallDesc')}</span></span>
          </a>
        </div>
        <p className="muted" style={{ display: 'flex', gap: 8, alignItems: 'center' }}><HeartHandshake size={20} color="var(--primary)" />{t('youAreNotAlone')}</p>
      </div>
    </>
  )
}

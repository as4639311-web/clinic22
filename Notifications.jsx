import { Link } from 'react-router-dom'
import { Bell, CalendarClock, ClipboardList, FlaskConical, MessageCircle, Smile } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { Empty, ErrorBox, Spinner, TopBar } from '../components/ui'

const ICON = { appointment: CalendarClock, plan: ClipboardList, message: MessageCircle, result: FlaskConical, checkin: Smile }

export default function Notifications() {
  const { t, pick, fmtDate } = useApp()
  const { data, loading, error, reload, setData } = useData('/notifications')
  async function readAll() {
    await api.post('/notifications/read-all').catch(() => {})
    setData({ ...data, items: data.items.map((n) => ({ ...n, read: true })) })
  }
  const link = (s) => (s.kind === 'checkin' ? '/' : s.ref?.appointment_id ? `/appointments/${s.ref.appointment_id}` : '/')

  return (
    <>
      <TopBar title={t('notifications')} back
        actions={data?.items?.some((n) => !n.read) && <button className="btn" style={{ color: 'var(--primary)' }} onClick={readAll}>{t('markAllRead')}</button>} />
      <div className="page">
        {loading ? <Spinner /> : error ? <ErrorBox error={error} onRetry={reload} /> : (
          <>
            {data.smart.length > 0 && (
              <section className="section">
                <h3>{t('forYouNow')}</h3>
                <div className="list">
                  {data.smart.map((s, i) => {
                    const Icon = ICON[s.kind] || Bell
                    return (
                      <Link key={i} to={link(s)} className="row" style={s.priority === 'high' ? { background: 'var(--primary-soft)' } : undefined}>
                        <Icon size={22} color="var(--primary)" />
                        <span className="grow"><span className="title">{pick(s.title)}</span><br /><span className="muted small">{pick(s.body)}</span></span>
                      </Link>
                    )
                  })}
                </div>
              </section>
            )}
            {!data.items.length && !data.smart.length ? <Empty icon={Bell} text={t('noNotifications')} /> : (
              <div className="list">
                {data.items.map((n) => {
                  const Icon = ICON[n.kind] || Bell
                  return (
                    <div key={n.id} className="row" style={{ alignItems: 'flex-start' }}>
                      <Icon size={22} color={n.read ? 'var(--ink-2)' : 'var(--primary)'} />
                      <span className="grow">
                        <span className="title" style={{ fontWeight: n.read ? 500 : 700 }}>{pick(n.title)}</span><br />
                        <span className="muted small">{pick(n.body)}</span>
                      </span>
                      <span className="muted small">{fmtDate(n.created_at)}</span>
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}

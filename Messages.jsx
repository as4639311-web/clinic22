import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Lock, MessageCircle, Send } from 'lucide-react'
import { useApp, useData } from '../state'
import { api } from '../api/client'
import { Chevron, Empty, ErrorBox, Initials, Spinner, TopBar } from '../components/ui'

export function Messages() {
  const { t, pick, fmtDate } = useApp()
  const { data, loading, error, reload } = useData('/messages/threads')
  return (
    <>
      <TopBar title={t('messages')} back />
      <div className="page">
        {loading ? <Spinner /> : error ? <ErrorBox error={error} onRetry={reload} /> : !data.length ? <Empty icon={MessageCircle} text={t('noThreads')} /> : (
          <div className="list">
            {data.map((th) => (
              <Link key={th.specialist.id} to={`/messages/${th.specialist.id}`} className="row">
                <Initials name={pick(th.specialist.name)} />
                <span className="grow">
                  <span className="title">{pick(th.specialist.name)}</span><br />
                  <span className="muted small" style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {th.last ? th.last.body : pick(th.specialist.title)}
                  </span>
                </span>
                {th.last && <span className="muted small">{fmtDate(th.last.created_at)}</span>}
                {th.unread > 0 && <span className="badge good">{th.unread}</span>}
                <Chevron />
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export function Thread() {
  const { id } = useParams()
  const { t, pick, fmtTime, errText, notify } = useApp()
  const sp = useData(`/specialists/${id}`)
  const { data, loading, error, reload, setData } = useData(`/messages/${id}`)
  const [text, setText] = useState('')
  const end = useRef(null)
  useEffect(() => end.current?.scrollIntoView({ block: 'end' }), [data])

  async function send(e) {
    e.preventDefault()
    if (!text.trim()) return
    try {
      const m = await api.post('/messages', { specialist_id: Number(id), body: text.trim() })
      setData([...(data || []), m]); setText('')
    } catch (x) { notify(errText(x)) }
  }
  return (
    <>
      <TopBar title={sp.data ? pick(sp.data.name) : ''} back />
      <div className="page">
        <p className="muted small" style={{ display: 'flex', gap: 6, alignItems: 'center', justifyContent: 'center' }}><Lock size={14} />{t('secureNote')}</p>
        {loading ? <Spinner /> : error ? <ErrorBox error={error} onRetry={reload} /> : (
          <div className="chat" aria-live="polite">
            {data.map((m) => (
              <div key={m.id} className={`bubble ${m.sender === 'user' ? 'me' : 'them'}`}>
                {m.body}<time className="num">{fmtTime(m.created_at)}</time>
              </div>
            ))}
            <div ref={end} />
          </div>
        )}
      </div>
      {!error && (
        <div className="composer">
          <form onSubmit={send}>
            <input className="input" aria-label={t('typeMessage')} placeholder={t('typeMessage')} value={text} onChange={(e) => setText(e.target.value)} />
            <button className="btn btn-primary" aria-label={t('send')} disabled={!text.trim()}><Send size={20} className="flip" /></button>
          </form>
        </div>
      )}
    </>
  )
}

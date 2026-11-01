import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LifeBuoy, Send } from 'lucide-react'
import { useApp } from '../state'
import { api } from '../api/client'
import { TopBar } from '../components/ui'

export default function Assistant() {
  const { t, locale, errText } = useApp()
  const [msgs, setMsgs] = useState([{ role: 'assistant', content: t('assistantIntro') }])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef(null)
  useEffect(() => end.current?.scrollIntoView({ block: 'end' }), [msgs, busy])

  async function send(e) {
    e.preventDefault()
    const q = text.trim()
    if (!q || busy) return
    const history = msgs.slice(1).map(({ role, content }) => ({ role, content }))
    setMsgs((m) => [...m, { role: 'user', content: q }])
    setText(''); setBusy(true)
    try {
      const r = await api.post('/assistant/chat', { message: q, locale, history })
      setMsgs((m) => [...m, { role: 'assistant', content: r.reply, safety: r.safety }])
    } catch (x) {
      setMsgs((m) => [...m, { role: 'assistant', content: errText(x), error: true }])
    } finally { setBusy(false) }
  }

  return (
    <>
      <TopBar title={t('assistant')} back />
      <div className="page">
        <div className="chat" aria-live="polite">
          {msgs.map((m, i) => (
            <div key={i} className={`bubble ${m.role === 'user' ? 'me' : 'them'}${m.safety ? ' safety' : ''}`}>
              {m.content}
              {m.safety && <Link to="/urgent" className="btn btn-primary" style={{ marginBlockStart: 10, display: 'flex' }}><LifeBuoy size={18} />{t('urgent')}</Link>}
            </div>
          ))}
          {busy && <div className="bubble them muted">{t('thinking')}</div>}
          <div ref={end} />
        </div>
      </div>
      <div className="composer">
        <form onSubmit={send}>
          <input className="input" aria-label={t('askSomething')} placeholder={t('askSomething')} value={text} onChange={(e) => setText(e.target.value)} />
          <button className="btn btn-primary" aria-label={t('send')} disabled={!text.trim() || busy}><Send size={20} className="flip" /></button>
        </form>
      </div>
    </>
  )
}

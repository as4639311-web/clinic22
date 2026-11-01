import { useState } from 'react'
import { HeartHandshake, Languages, Moon, Sun } from 'lucide-react'
import { useApp } from '../state'
import { api } from '../api/client'

export default function Login() {
  const { t, signIn, errText, prefs, updatePrefs } = useApp()
  const [mode, setMode] = useState('in')
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e, override) {
    e?.preventDefault()
    setBusy(true)
    setError('')
    const body = override || form
    try {
      const res = mode === 'in' || override
        ? await api.post('/auth/login', { email: body.email, password: body.password })
        : await api.post('/auth/register', { ...body, locale: prefs.locale })
      signIn(res)
    } catch (err) {
      setError(errText(err))
    } finally {
      setBusy(false)
    }
  }

  const dark = document.documentElement.dataset.theme === 'dark'
  return (
    <div className="auth">
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 4 }}>
        <button className="icon-btn" onClick={() => updatePrefs({ locale: prefs.locale === 'ar' ? 'en' : 'ar' })} aria-label={t('language')}>
          <Languages size={22} />
        </button>
        <button className="icon-btn" onClick={() => updatePrefs({ theme: dark ? 'light' : 'dark' })} aria-label={t('appearance')}>
          {dark ? <Sun size={22} /> : <Moon size={22} />}
        </button>
      </div>
      <div className="brand">
        <span className="mark"><HeartHandshake size={28} /></span>
        <div>
          <h1>{t('appName')}</h1>
          <p className="muted">{t('tagline')}</p>
        </div>
      </div>

      <form className="section" onSubmit={submit} noValidate>
        {mode === 'up' && (
          <div className="field">
            <label htmlFor="name">{t('fullName')}</label>
            <input id="name" className="input" autoComplete="name" value={form.full_name} onChange={set('full_name')} required />
          </div>
        )}
        <div className="field">
          <label htmlFor="email">{t('email')}</label>
          <input id="email" className="input" type="email" inputMode="email" autoComplete="email" dir="ltr" value={form.email} onChange={set('email')} required />
        </div>
        <div className="field">
          <label htmlFor="pw">{t('password')}</label>
          <input id="pw" className="input" type="password" autoComplete={mode === 'in' ? 'current-password' : 'new-password'} dir="ltr" value={form.password} onChange={set('password')} required minLength={8} />
        </div>
        {error && <p className="error-text" role="alert">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy}>{mode === 'in' ? t('signIn') : t('signUp')}</button>
        <button type="button" className="btn btn-soft btn-block" disabled={busy}
          onClick={() => submit(null, { email: 'demo@tawazun.app', password: 'Demo@1234' })}>
          {t('useDemo')}
        </button>
      </form>

      <p className="muted" style={{ textAlign: 'center' }}>
        {mode === 'in' ? t('noAccount') : t('haveAccount')}{' '}
        <button className="btn" style={{ padding: '0 6px', minBlockSize: 0, color: 'var(--primary)', background: 'none' }}
          onClick={() => { setMode(mode === 'in' ? 'up' : 'in'); setError('') }}>
          {mode === 'in' ? t('signUp') : t('signIn')}
        </button>
      </p>
    </div>
  )
}

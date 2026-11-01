/* App-wide state: preferences (language, theme), auth session, toasts. */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { STRINGS } from './i18n/strings'
import { api, setTokens } from './api/client'

const Ctx = createContext(null)
const PREFS_KEY = 'tw.prefs'
const SESSION_KEY = 'tw.session'

function readJSON(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}

export function AppProvider({ children }) {
  const [prefs, setPrefs] = useState(() => ({ locale: 'ar', theme: 'system', ...readJSON(PREFS_KEY, {}) }))
  // session in sessionStorage: medical app → signed out when the browser closes
  const [session, setSession] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem(SESSION_KEY)) } catch { return null }
  })
  const [toast, setToast] = useState(null)

  setTokens({ access: session?.token })

  // language + direction
  useEffect(() => {
    const el = document.documentElement
    el.lang = prefs.locale
    el.dir = prefs.locale === 'ar' ? 'rtl' : 'ltr'
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)) } catch { /* private mode */ }
  }, [prefs])

  // theme (follows the system when set to automatic, live)
  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      document.documentElement.dataset.theme = prefs.theme === 'system' ? (mq.matches ? 'dark' : 'light') : prefs.theme
    }
    apply()
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [prefs.theme])

  const updatePrefs = useCallback((patch) => {
    setPrefs((p) => ({ ...p, ...patch }))
    if (session) api.patch('/auth/me', patch).catch(() => {}) // saved to the account too
  }, [session])

  const signIn = useCallback(({ access_token, user }) => {
    const s = { token: access_token, user }
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(s))
    setTokens({ access: access_token })
    setSession(s)
    setPrefs((p) => ({ ...p, locale: user.locale || p.locale, theme: user.theme || p.theme }))
  }, [])

  const signOut = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY)
    setTokens({ access: null, unlock: null })
    setSession(null)
  }, [])

  useEffect(() => {
    const onExpired = () => signOut()
    window.addEventListener('tw:unauthorized', onExpired)
    return () => window.removeEventListener('tw:unauthorized', onExpired)
  }, [signOut])

  const notify = useCallback((msg) => {
    setToast(msg)
    clearTimeout(window.__twToast)
    window.__twToast = setTimeout(() => setToast(null), 2800)
  }, [])

  const i18n = useMemo(() => {
    const dict = STRINGS[prefs.locale]
    const t = (key, vars) => {
      let s = dict[key] ?? STRINGS.en[key] ?? key
      if (vars && typeof s === 'string') for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v)
      return s
    }
    const pick = (bi) => (bi && typeof bi === 'object' ? bi[prefs.locale] || bi.en || bi.ar : bi ?? '')
    const tag = prefs.locale === 'ar' ? 'ar-AE' : 'en-GB'
    const fmtDate = (iso, opts = { day: 'numeric', month: 'short' }) => (iso ? new Date(iso).toLocaleDateString(tag, opts) : '')
    const fmtTime = (iso) => (iso ? new Date(iso).toLocaleTimeString(tag, { hour: 'numeric', minute: '2-digit' }) : '')
    const fmtNum = (n, d = 1) => (n == null ? '–' : Number(n).toLocaleString(tag, { maximumFractionDigits: d }))
    return { t, pick, fmtDate, fmtTime, fmtNum, locale: prefs.locale, dir: prefs.locale === 'ar' ? 'rtl' : 'ltr' }
  }, [prefs.locale])

  const errText = useCallback((e) => {
    const key = `err_${e?.code || 'generic'}`
    return STRINGS[prefs.locale][key] || STRINGS[prefs.locale].err_generic
  }, [prefs.locale])

  const value = { prefs, updatePrefs, session, signIn, signOut, notify, errText, ...i18n }
  return (
    <Ctx.Provider value={value}>
      {children}
      {toast && <div className="toast" role="status" aria-live="polite">{toast}</div>}
    </Ctx.Provider>
  )
}

export const useApp = () => useContext(Ctx)

/** Small data hook: loads on mount / when deps change; returns {data, error, loading, reload, setData}. */
export function useData(path, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path })
  const load = useCallback(() => {
    if (!path) return
    setState((s) => ({ ...s, loading: true }))
    api.get(path)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...deps])
  useEffect(load, [load])
  return { ...state, reload: load, setData: (data) => setState((s) => ({ ...s, data })) }
}

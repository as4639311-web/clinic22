/* Thin fetch wrapper. Base URL comes from VITE_API_URL in the root .env / .env.prod. */
const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '')

let tokens = { access: null, unlock: null, unlockUntil: 0 }

export function setTokens(patch) {
  tokens = { ...tokens, ...patch }
}

export function setUnlock(token, seconds) {
  tokens.unlock = token
  tokens.unlockUntil = Date.now() + seconds * 1000
  window.dispatchEvent(new Event('tw:unlock'))
}

export function isUnlocked() {
  return !!tokens.unlock && Date.now() < tokens.unlockUntil
}

export class ApiError extends Error {
  constructor(status, code) {
    super(code)
    this.status = status
    this.code = code
  }
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' }
  if (tokens.access) headers.Authorization = `Bearer ${tokens.access}`
  if (isUnlocked()) headers['X-Unlock-Token'] = tokens.unlock
  let res
  try {
    res = await fetch(BASE + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch {
    throw new ApiError(0, 'network')
  }
  if (res.status === 401 && tokens.access && !path.startsWith('/auth/login') && !path.startsWith('/card/unlock')) {
    window.dispatchEvent(new Event('tw:unauthorized'))
  }
  if (!res.ok) {
    let code = 'generic'
    try {
      const j = await res.json()
      if (typeof j.detail === 'string') code = j.detail
    } catch { /* not json */ }
    throw new ApiError(res.status, code)
  }
  return res.status === 204 ? null : res.json()
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b = {}) => request('POST', p, b),
  patch: (p, b) => request('PATCH', p, b),
}

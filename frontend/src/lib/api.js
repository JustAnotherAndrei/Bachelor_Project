// Tiny fetch wrapper:
//   - always sends cookies (credentials: 'include')
//   - injects the CSRF header on state-changing methods (double-submit pattern)
//   - throws { status, detail } on non-2xx so callers can `.catch`

const CSRF_COOKIE = 'sequre_csrf'
const CSRF_HEADER = 'X-CSRF-Token'

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export async function api(path, { method = 'GET', body, headers = {} } = {}) {
  const opts = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...headers },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)

  if (method !== 'GET' && method !== 'HEAD') {
    const csrf = readCookie(CSRF_COOKIE)
    if (csrf) opts.headers[CSRF_HEADER] = csrf
  }

  const res = await fetch(path, opts)
  if (!res.ok) {
    let detail
    try { detail = (await res.json()).detail } catch { detail = res.statusText }
    throw { status: res.status, detail }
  }
  if (res.status === 204) return null
  return res.json()
}

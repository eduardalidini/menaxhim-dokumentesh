import { getAuth } from './auth'

const BASE_HEADERS: Record<string, string> = {
  Accept: 'application/json',
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const { accessToken } = getAuth()

  const headers = new Headers(init.headers)
  Object.entries(BASE_HEADERS).forEach(([k, v]) => {
    if (!headers.has(k)) headers.set(k, v)
  })

  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  const res = await fetch(path, {
    ...init,
    headers,
  })

  if (!res.ok) {
    let payload: unknown = null
    try {
      payload = await res.json()
    } catch {
      // ignore
    }
    throw { status: res.status, payload }
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return res.text()
}

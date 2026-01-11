import { getAuth } from './auth'

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined

const BASE_HEADERS: Record<string, string> = {
  Accept: 'application/json',
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const { accessToken } = getAuth()

  const url = /^https?:\/\//i.test(path)
    ? path
    : `${(API_BASE_URL || '').replace(/\/$/, '')}${path.startsWith('/') ? '' : '/'}${path}`

  const headers = new Headers(init.headers)
  Object.entries(BASE_HEADERS).forEach(([k, v]) => {
    if (!headers.has(k)) headers.set(k, v)
  })

  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  const res = await fetch(url, {
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

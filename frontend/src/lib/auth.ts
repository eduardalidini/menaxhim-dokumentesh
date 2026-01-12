export type Role = 'staf' | 'sekretaria' | 'admin'

type AuthState = {
  accessToken: string | null
  role: Role | null
  email: string | null
}

const ACCESS_TOKEN_KEY = 'access_token'
const ROLE_KEY = 'role'

export function getAuth(): AuthState {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
  const roleRaw = localStorage.getItem(ROLE_KEY)
  const role = roleRaw === 'staf' || roleRaw === 'sekretaria' || roleRaw === 'admin' ? roleRaw : null

  let email: string | null = null
  if (accessToken) {
    try {
      const parts = accessToken.split('.')
      if (parts.length >= 2) {
        const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
        const padded = payload + '='.repeat((4 - (payload.length % 4)) % 4)
        const json = atob(padded)
        const obj = JSON.parse(json)
        email = typeof obj?.email === 'string' ? obj.email : null
      }
    } catch {
      email = null
    }
  }

  return { accessToken, role, email }
}

export function setAuth(accessToken: string, role: Role) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(ROLE_KEY, role)
}

export function clearAuth() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
}

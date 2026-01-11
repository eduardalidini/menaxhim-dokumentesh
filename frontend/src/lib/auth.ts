export type Role = 'staf' | 'sekretaria' | 'admin'

type AuthState = {
  accessToken: string | null
  role: Role | null
}

const ACCESS_TOKEN_KEY = 'access_token'
const ROLE_KEY = 'role'

export function getAuth(): AuthState {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
  const roleRaw = localStorage.getItem(ROLE_KEY)
  const role = roleRaw === 'staf' || roleRaw === 'sekretaria' || roleRaw === 'admin' ? roleRaw : null
  return { accessToken, role }
}

export function setAuth(accessToken: string, role: Role) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(ROLE_KEY, role)
}

export function clearAuth() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
}

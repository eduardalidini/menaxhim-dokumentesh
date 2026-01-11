import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearAuth, getAuth } from '../lib/auth'

function linkClass({ isActive }: { isActive: boolean }) {
  return [
    'rounded-md px-3 py-2 text-sm font-medium',
    isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100',
  ].join(' ')
}

export default function AppLayout() {
  const navigate = useNavigate()
  const { role } = getAuth()

  function logout() {
    clearAuth()
    navigate('/login')
  }

  const canUpload = role === 'sekretaria' || role === 'admin'
  const isAdmin = role === 'admin'

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <div className="font-semibold">Menaxhimi i Dokumenteve</div>
            <nav className="flex items-center gap-2">
              <NavLink to="/dokumente" className={linkClass}>
                Dokumente
              </NavLink>
              <NavLink to="/arkiva" className={linkClass}>
                Arkiva
              </NavLink>
              {canUpload ? (
                <NavLink to="/ngarko" className={linkClass}>
                  Ngarko
                </NavLink>
              ) : null}
              {isAdmin ? (
                <NavLink to="/drive" className={linkClass}>
                  Drive
                </NavLink>
              ) : null}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-sm text-slate-600">Roli: {role ?? '—'}</div>
            <button
              className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
              onClick={logout}
              type="button"
            >
              Dil
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

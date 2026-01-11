import { useMemo, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import { setAuth } from '../lib/auth'

type LocationState = { from?: string }

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as LocationState | null)?.from || '/dokumente'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = useMemo(() => email.trim() && password.trim(), [email, password])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit) return

    setError(null)
    setLoading(true)
    try {
      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      setAuth(res.access_token, res.role)
      navigate(from, { replace: true })
    } catch (err: any) {
      const msg = err?.payload?.error?.message || 'Gabim gjatë kyçjes'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
        <h1 className="mb-6 text-center text-2xl font-semibold">Kyçu</h1>

        <form onSubmit={onSubmit} className="rounded-xl border bg-white p-6 shadow-sm">
          <label className="block text-sm font-medium text-slate-700">Email</label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />

          <label className="mt-4 block text-sm font-medium text-slate-700">Fjalëkalimi</label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />

          {error ? <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <button
            className="mt-5 w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            type="submit"
            disabled={!canSubmit || loading}
          >
            {loading ? 'Duke u kyçur...' : 'Kyçu'}
          </button>
        </form>
      </div>
    </div>
  )
}

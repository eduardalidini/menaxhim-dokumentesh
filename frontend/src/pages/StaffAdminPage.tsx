import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { apiFetch } from '../lib/api'
import { getAuth } from '../lib/auth'

type AllowedEmail = { email: string; created_at: string }

type Role = 'staf' | 'sekretaria'

export default function StaffAdminPage() {
  const { role } = getAuth()
  const isAdmin = role === 'admin'

  const [allowed, setAllowed] = useState<AllowedEmail[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [allowEmail, setAllowEmail] = useState('')

  const [newEmail, setNewEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState<Role>('staf')

  const canCreateUser = useMemo(() => {
    return newEmail.trim() && newPassword.trim() && (newRole === 'staf' || newRole === 'sekretaria')
  }, [newEmail, newPassword, newRole])

  async function refresh() {
    setError(null)
    const res = await apiFetch('/api/admin/allowed-emails', { method: 'GET' })
    setAllowed((res as any)?.items || [])
  }

  useEffect(() => {
    if (!isAdmin) return
    setLoading(true)
    refresh()
      .catch((e: any) => {
        const msg = e?.payload?.error?.message || 'Gabim gjatë ngarkimit të listës'
        setError(msg)
      })
      .finally(() => setLoading(false))
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="rounded-md border bg-white p-4 text-sm text-slate-700">Vetëm admin-i mund ta menaxhojë stafin.</div>
    )
  }

  async function addAllowed(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      await apiFetch('/api/admin/allowed-emails', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: allowEmail.trim().toLowerCase() }),
      })
      setAllowEmail('')
      setSuccess('Email u shtua në listën e lejuar')
      await refresh()
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  async function removeAllowed(email: string) {
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      await apiFetch(`/api/admin/allowed-emails/${encodeURIComponent(email)}`, { method: 'DELETE' })
      setSuccess('Email u hoq nga lista')
      await refresh()
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  async function createUser(e: FormEvent) {
    e.preventDefault()
    if (!canCreateUser) return

    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const res = await apiFetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newEmail.trim().toLowerCase(), password: newPassword, role: newRole }),
      })
      setNewEmail('')
      setNewPassword('')
      setNewRole('staf')
      const status = (res as any)?.status
      setSuccess(status === 'updated' ? 'Përdoruesi u përditësua' : 'Përdoruesi u krijua')
      await refresh()
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold">Stafi</h1>
      <p className="mt-2 text-slate-600">
        Admin-i mund të regjistrojë përdorues të stafit (email + fjalëkalim). Email-i ruhet gjithashtu në listën e lejuar.
      </p>

      {loading ? <div className="mt-3 text-sm text-slate-600">Duke punuar...</div> : null}
      {error ? <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {success ? <div className="mt-3 rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</div> : null}

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold">Shto email të lejuar</h2>
          <form onSubmit={addAllowed} className="mt-3">
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2"
              value={allowEmail}
              onChange={(e) => setAllowEmail(e.target.value)}
              type="email"
              required
            />
            <button
              className="mt-3 rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              type="submit"
              disabled={loading}
            >
              Shto
            </button>
          </form>

          <div className="mt-5">
            <div className="text-sm font-medium text-slate-700">Lista e lejuar</div>
            <div className="mt-2 divide-y rounded-md border bg-white">
              {allowed.length === 0 ? (
                <div className="p-3 text-sm text-slate-600">Nuk ka emaile.</div>
              ) : (
                allowed.map((x) => (
                  <div key={x.email} className="flex items-center justify-between gap-3 p-3">
                    <div>
                      <div className="text-sm font-medium">{x.email}</div>
                      <div className="text-xs text-slate-500">{x.created_at}</div>
                    </div>
                    <button
                      type="button"
                      className="rounded-md border px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
                      onClick={() => removeAllowed(x.email)}
                      disabled={loading}
                    >
                      Hiq
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold">Krijo përdorues stafi</h2>
          <form onSubmit={createUser} className="mt-3">
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              type="email"
              required
            />

            <label className="mt-4 block text-sm font-medium text-slate-700">Fjalëkalimi</label>
            <input
              className="mt-1 w-full rounded-md border px-3 py-2"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              type="password"
              required
            />

            <label className="mt-4 block text-sm font-medium text-slate-700">Roli</label>
            <select
              className="mt-1 w-full rounded-md border bg-white px-3 py-2"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as Role)}
            >
              <option value="staf">staf</option>
              <option value="sekretaria">sekretaria</option>
            </select>

            <button
              className="mt-4 rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              type="submit"
              disabled={!canCreateUser || loading}
            >
              Krijo
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

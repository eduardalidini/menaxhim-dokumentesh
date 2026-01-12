import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../lib/api'
import { getAuth } from '../lib/auth'

export default function DrivePage() {
  const { role, accessToken } = getAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [status, setStatus] = useState<{ connected: boolean; connected_at: string | null; updated_at: string | null } | null>(null)

  const isAllowedRole = role === 'admin' || role === 'sekretaria' || role === 'staf'

  const driveConnected = useMemo(() => {
    return !!status?.connected
  }, [status])

  async function loadStatus() {
    const res = await apiFetch('/api/drive/status', { method: 'GET' })
    setStatus(res as any)
  }

  useEffect(() => {
    if (!isAllowedRole) return
    loadStatus().catch(() => {
      // ignore
    })

    const params = new URLSearchParams(window.location.search)
    const drive = params.get('drive')
    const at = params.get('at')
    if (drive === 'connected') {
      setSuccess(`Google Drive u lidh me sukses${at ? ` (${at})` : ''}.`)
      params.delete('drive')
      params.delete('at')
      const next = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ''}`
      window.history.replaceState({}, '', next)
      loadStatus().catch(() => {
        // ignore
      })
    }
  }, [isAllowedRole])

  async function connect() {
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      if (!accessToken) {
        throw new Error('Nuk je i kyçur (mungon token). Kyçu përsëri.')
      }
      const res = await apiFetch('/api/drive/auth/url', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      const authUrl = (res as any)?.auth_url
      if (!authUrl) throw new Error('Mungon auth_url nga serveri')
      window.location.href = authUrl
    } catch (e: any) {
      const msg = e?.payload?.error?.message || e?.message || 'Gabim gjatë lidhjes me Google Drive'
      setError(msg)
      setLoading(false)
    }
  }

  async function disconnect() {
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      await apiFetch('/api/drive/disconnect', { method: 'POST' })
      setSuccess('Google Drive u shkëput.')
      await loadStatus()
    } catch (e: any) {
      const msg = e?.payload?.error?.message || e?.message || 'Gabim gjatë shkëputjes'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Google Drive</h1>
      <p className="mt-2 text-slate-600">
        Këtu lidhet llogaria Google Drive që do të përdoret nga backend-i për ngarkime dhe menaxhim dokumentesh.
      </p>

      {!isAllowedRole ? (
        <div className="mt-4 rounded-md border bg-white p-4 text-sm text-slate-700">Nuk ke akses në këtë faqe.</div>
      ) : (
        <div className="mt-4 rounded-md border bg-white p-4">
          <div className="mb-3 rounded-md bg-slate-50 p-3 text-sm text-slate-700">
            <div className="font-medium">
              Statusi: {driveConnected ? 'I lidhur' : 'Jo i lidhur'}
            </div>
            {driveConnected ? (
              <div className="mt-1 text-xs text-slate-600">
                Lidhur: {status?.connected_at || '—'} | Përditësuar: {status?.updated_at || '—'}
              </div>
            ) : null}
          </div>

          {!accessToken ? (
            <div className="mb-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
              Mungon token-i i kyçjes. Bëj <span className="font-medium">Dil</span> dhe kyçu përsëri si admin.
            </div>
          ) : null}
          <button
            className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            type="button"
            onClick={connect}
            disabled={loading}
          >
            {loading ? 'Duke hapur Google...' : 'Lidh Google Drive'}
          </button>

          {driveConnected ? (
            <button
              className="ml-2 rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
              type="button"
              onClick={disconnect}
              disabled={loading}
            >
              Shkëput
            </button>
          ) : null}

          {success ? <div className="mt-3 rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</div> : null}

          {error ? <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <div className="mt-3 text-xs text-slate-500">
            Pas autorizimit, do të ridrejtoheni nga Google te backend-i. Nëse shihni faqen e docs të backend-it,
            thjesht kthehuni te aplikacioni.
          </div>
        </div>
      )}
    </div>
  )
}

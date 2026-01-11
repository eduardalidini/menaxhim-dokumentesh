import { useState } from 'react'
import { apiFetch } from '../lib/api'
import { getAuth } from '../lib/auth'

export default function DrivePage() {
  const { role, accessToken } = getAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isAdmin = role === 'admin'

  async function connect() {
    setError(null)
    setLoading(true)
    try {
      if (!accessToken) {
        throw new Error('Nuk je i kyçur (mungon token). Kyçu përsëri si admin.')
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

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Google Drive</h1>
      <p className="mt-2 text-slate-600">
        Këtu lidhet llogaria Google Drive që do të përdoret nga backend-i për ngarkime dhe menaxhim dokumentesh.
      </p>

      {!isAdmin ? (
        <div className="mt-4 rounded-md border bg-white p-4 text-sm text-slate-700">
          Vetëm admin-i mund ta lidhë Google Drive.
        </div>
      ) : (
        <div className="mt-4 rounded-md border bg-white p-4">
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

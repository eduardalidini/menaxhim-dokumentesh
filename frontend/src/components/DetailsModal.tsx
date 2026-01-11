import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/api'
import type { DocumentItem } from '../lib/types'

type Props = {
  open: boolean
  docId: number | null
  onClose: () => void
}

export default function DetailsModal({ open, docId, onClose }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [doc, setDoc] = useState<DocumentItem | null>(null)

  useEffect(() => {
    if (!open || !docId) return

    let cancelled = false
    setLoading(true)
    setError(null)
    setDoc(null)

    apiFetch(`/api/documents/${docId}`)
      .then((d) => {
        if (cancelled) return
        setDoc(d)
      })
      .catch((e: any) => {
        if (cancelled) return
        const msg = e?.payload?.error?.message || 'Nuk u arrit të merret dokumenti'
        setError(msg)
      })
      .finally(() => {
        if (cancelled) return
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [open, docId])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-2xl rounded-xl border bg-white p-5 shadow-lg">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-lg font-semibold">Detajet</div>
            {doc ? <div className="mt-1 text-sm text-slate-600">ID: {doc.id}</div> : null}
          </div>
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50"
            onClick={onClose}
          >
            Mbyll
          </button>
        </div>

        {loading ? <div className="mt-4 text-sm text-slate-600">Duke ngarkuar...</div> : null}
        {error ? <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

        {doc ? (
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <div className="text-xs font-medium text-slate-500">Titulli</div>
              <div className="text-sm">{doc.title}</div>
            </div>
            <div>
              <div className="text-xs font-medium text-slate-500">Kategoria</div>
              <div className="text-sm">{doc.category}</div>
            </div>
            <div>
              <div className="text-xs font-medium text-slate-500">Statusi</div>
              <div className="text-sm">{doc.status}</div>
            </div>
            <div>
              <div className="text-xs font-medium text-slate-500">Lloji i skedarit</div>
              <div className="text-sm">{doc.file_type}</div>
            </div>
            <div className="sm:col-span-2">
              <div className="text-xs font-medium text-slate-500">Përshkrimi</div>
              <div className="text-sm">{doc.description || '—'}</div>
            </div>
            <div className="sm:col-span-2">
              <div className="text-xs font-medium text-slate-500">Tags</div>
              <div className="text-sm">{doc.tags || '—'}</div>
            </div>

            <div>
              <div className="text-xs font-medium text-slate-500">Krijuar</div>
              <div className="text-sm">{new Date(doc.created_at).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs font-medium text-slate-500">Përditësuar</div>
              <div className="text-sm">{new Date(doc.updated_at).toLocaleString()}</div>
            </div>

            <div className="sm:col-span-2">
              <div className="text-xs font-medium text-slate-500">Përmbledhje</div>
              <div className="text-sm">{doc.ai_summary || 'Summary not available'}</div>
            </div>

            <div className="sm:col-span-2">
              <div className="text-xs font-medium text-slate-500">Drive</div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <a
                  href={doc.web_view_link}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
                >
                  Hape në Drive
                </a>
                <div className="text-xs text-slate-500">drive_file_id: {doc.drive_file_id}</div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { apiFetch } from '../lib/api'
import type { DocumentItem } from '../lib/types'

type Props = {
  open: boolean
  doc: DocumentItem | null
  onClose: () => void
  onReplaced: (updated: DocumentItem) => void
}

export default function ReplaceFileModal({ open, doc, onClose, onReplaced }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = useMemo(() => !!doc && !!file && !loading, [doc, file, loading])

  useEffect(() => {
    if (!open) return
    setError(null)
    setFile(null)
    setTitle('')
  }, [open])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!doc || !file) return

    setLoading(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      if (title.trim()) form.append('title', title.trim())

      const updated = await apiFetch(`/api/documents/${doc.id}/file`, {
        method: 'PUT',
        body: form,
      })

      onReplaced(updated)
      onClose()
      setFile(null)
      setTitle('')
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim gjatë zëvendësimit'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (!open || !doc) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-lg rounded-xl border bg-white p-5 shadow-lg">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-lg font-semibold">Zëvendëso skedarin</div>
            <div className="mt-1 text-sm text-slate-600">Dokumenti: {doc.title}</div>
          </div>
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50"
            onClick={onClose}
            disabled={loading}
          >
            Mbyll
          </button>
        </div>

        <div className="mt-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
          Kujdes: Ky veprim përditëson të njëjtin skedar në Drive (Strategjia A).
        </div>

        <form onSubmit={onSubmit} className="mt-4">
          <input
            type="file"
            accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={(e) => {
              const f = e.target.files?.[0] || null
              setFile(f)
              if (f) {
                const stem = f.name.replace(/\.[^/.]+$/, '')
                setTitle(stem)
              }
            }}
          />

          <div className="mt-3">
            <div className="text-xs font-medium text-slate-500">Titulli (opsional)</div>
            <input
              type="text"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Titulli i ri"
            />
          </div>

          {error ? <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <button
            type="submit"
            className="mt-4 rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            disabled={!canSubmit}
          >
            {loading ? 'Duke zëvendësuar...' : 'Konfirmo'}
          </button>
        </form>
      </div>
    </div>
  )
}

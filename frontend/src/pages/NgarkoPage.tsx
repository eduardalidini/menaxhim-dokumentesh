import { useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import { getAuth } from '../lib/auth'

type Category = 'request' | 'decision' | 'form' | 'announcement'

export default function NgarkoPage() {
  const navigate = useNavigate()
  const { role } = getAuth()

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState<Category>('request')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canUpload = role === 'sekretaria' || role === 'admin'
  const canSubmit = useMemo(() => {
    return canUpload && !!file && title.trim().length > 0 && !!category && !loading
  }, [canUpload, file, title, category, loading])

  if (!canUpload) {
    return (
      <div className="rounded-md border bg-white p-4">
        <div className="font-medium">Nuk ke të drejtë</div>
        <div className="mt-1 text-sm text-slate-600">Kjo faqe është vetëm për Sekretaria/Admin.</div>
      </div>
    )
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit || !file) return

    setError(null)
    setLoading(true)

    try {
      const form = new FormData()
      form.append('file', file)
      form.append('title', title.trim())
      form.append('category', category)
      if (description.trim()) form.append('description', description.trim())
      if (tags.trim()) form.append('tags', tags.trim())

      await apiFetch('/api/documents', {
        method: 'POST',
        body: form,
      })

      navigate('/dokumente', { replace: true })
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim gjatë ngarkimit'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold">Ngarko dokument</h1>
      <div className="mt-1 text-sm text-slate-600">Ngarko PDF/DOCX dhe ruaj metadata.</div>

      <form onSubmit={onSubmit} className="mt-4 max-w-2xl rounded-xl border bg-white p-5">
        <label className="block text-sm font-medium text-slate-700">Skedari (pdf/docx)</label>
        <input
          className="mt-1"
          type="file"
          accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />

        <label className="mt-4 block text-sm font-medium text-slate-700">Titulli *</label>
        <input
          className="mt-1 w-full rounded-md border px-3 py-2"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <label className="mt-4 block text-sm font-medium text-slate-700">Kategoria *</label>
        <select
          className="mt-1 w-full rounded-md border bg-white px-3 py-2"
          value={category}
          onChange={(e) => setCategory(e.target.value as Category)}
        >
          <option value="request">request</option>
          <option value="decision">decision</option>
          <option value="form">form</option>
          <option value="announcement">announcement</option>
        </select>

        <label className="mt-4 block text-sm font-medium text-slate-700">Përshkrimi</label>
        <textarea
          className="mt-1 w-full rounded-md border px-3 py-2"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />

        <label className="mt-4 block text-sm font-medium text-slate-700">Tags</label>
        <input
          className="mt-1 w-full rounded-md border px-3 py-2"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="p.sh. student, 2026, provim"
        />

        {error ? <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
        {loading ? <div className="mt-3 text-sm text-slate-600">Duke ngarkuar...</div> : null}

        <button
          type="submit"
          disabled={!canSubmit}
          className="mt-5 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? 'Duke dërguar...' : 'Ngarko'}
        </button>
      </form>
    </div>
  )
}

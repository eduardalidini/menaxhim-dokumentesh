import { useEffect, useRef, useState } from 'react'
import { apiFetch } from '../lib/api'
import type { DocumentItem } from '../lib/types'

type AiCacheEntry = {
  summary: string
  expires_at_ms: number
  generations: number
}

const AI_SUMMARY_CACHE_TTL_MS = 10 * 60 * 1000
const AI_SUMMARY_CACHE_MAX_GENERATIONS = Number.POSITIVE_INFINITY
const aiSummaryCache = new Map<string, AiCacheEntry>()

function cleanupAiSummaryCache(nowMs: number) {
  for (const [k, v] of aiSummaryCache.entries()) {
    if (v.expires_at_ms <= nowMs) aiSummaryCache.delete(k)
  }
}

function buildAiCacheKey(doc: Pick<DocumentItem, 'id' | 'updated_at' | 'drive_file_id'>) {
  return `${doc.id}:${doc.updated_at}:${doc.drive_file_id}`
}

type Props = {
  open: boolean
  docId: number | null
  onClose: () => void
}

export default function DetailsModal({ open, docId, onClose }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [doc, setDoc] = useState<DocumentItem | null>(null)

  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)
  const [aiFullText, setAiFullText] = useState<string>('')
  const [aiExpanded, setAiExpanded] = useState(false)
  const aiRequestKeyRef = useRef<string | null>(null)

  useEffect(() => {
    if (!open || !docId) return

    let cancelled = false
    setLoading(true)
    setError(null)
    setDoc(null)
    setAiLoading(false)
    setAiError(null)
    setAiFullText('')
    setAiExpanded(false)
    aiRequestKeyRef.current = null

    apiFetch(`/api/documents/${docId}`)
      .then((d) => {
        if (cancelled) return
        setDoc(d)

        const nowMs = Date.now()
        cleanupAiSummaryCache(nowMs)
        const key = buildAiCacheKey(d)
        aiRequestKeyRef.current = key

        const cached = aiSummaryCache.get(key)
        const cachedActive = !!cached && cached.expires_at_ms > nowMs

        if (cachedActive && cached?.summary) {
          setAiError(null)
          setAiLoading(false)
          setAiFullText(cached.summary)
          return
        }

        const generations = cachedActive ? cached?.generations || 0 : 0
        if (generations >= AI_SUMMARY_CACHE_MAX_GENERATIONS) {
          setAiLoading(false)
          setAiError('U arrit limiti i gjenerimeve për këtë dokument. Provo më vonë.')
          return
        }

        const nextGenerations = generations + 1
        const nextEntry: AiCacheEntry = {
          summary: cachedActive ? cached?.summary || '' : '',
          generations: nextGenerations,
          expires_at_ms: nowMs + AI_SUMMARY_CACHE_TTL_MS,
        }
        aiSummaryCache.set(key, nextEntry)

        setAiLoading(true)
        setAiError(null)
        setAiFullText('')

        apiFetch(`/api/documents/${d.id}/ai-summary`, {
          method: 'POST',
        })
          .then((res: any) => {
            if (cancelled) return
            if (aiRequestKeyRef.current !== key) return
            const summary = (res?.ai_summary as string | undefined) || ''
            const prev = aiSummaryCache.get(key)
            const entry: AiCacheEntry = {
              summary,
              generations: prev?.generations || nextGenerations,
              expires_at_ms: prev?.expires_at_ms || Date.now() + AI_SUMMARY_CACHE_TTL_MS,
            }
            aiSummaryCache.set(key, entry)
            setAiFullText(summary)
          })
          .catch((e: any) => {
            if (cancelled) return
            if (aiRequestKeyRef.current !== key) return
            const msg = e?.payload?.error?.message || 'Gabim gjatë gjenerimit të përmbledhjes nga AI'
            setAiError(msg)
          })
          .finally(() => {
            if (cancelled) return
            if (aiRequestKeyRef.current !== key) return
            setAiLoading(false)
          })
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

  useEffect(() => {
    if (open) return
    setAiLoading(false)
    setAiError(null)
    setAiFullText('')
    setAiExpanded(false)
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-2xl max-h-[95vh] overflow-y-auto rounded-xl border bg-white p-5 shadow-lg">
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
            <div>
              <div className="text-xs font-medium text-slate-500">Ngarkuar nga</div>
              <div className="text-sm">{doc.uploaded_by_email || '—'}</div>
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
              <div className="text-xs font-medium text-slate-500">Përmbledhje nga AI</div>
              {aiError ? <div className="mt-2 rounded-md bg-red-50 p-3 text-sm text-red-700">{aiError}</div> : null}
              {!aiError ? (
                <div className="mt-1 w-full">
                  <div
                    className={`text-sm whitespace-pre-wrap break-words leading-relaxed ${
                      aiExpanded ? '' : 'max-h-24 overflow-hidden'
                    }`}
                  >
                  {aiLoading && !aiFullText ? (
                    <div className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  ) : (
                    aiFullText || '—'
                  )}
                  </div>

                  {!aiLoading && !aiError && aiFullText ? (
                    <div className="mt-2">
                      <button
                        type="button"
                        className="text-xs font-medium text-slate-700 underline underline-offset-2 hover:text-slate-900"
                        onClick={() => setAiExpanded((v) => !v)}
                      >
                        {aiExpanded ? 'Mbyll' : 'Zgjero'}
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : null}
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

import { useEffect, useMemo, useState } from 'react'
import ConfirmDialog from '../components/ConfirmDialog'
import DetailsModal from '../components/DetailsModal'
import DocumentsFilters from '../components/DocumentsFilters'
import DocumentsTable from '../components/DocumentsTable'
import Pagination from '../components/Pagination'
import ReplaceFileModal from '../components/ReplaceFileModal'
import { apiFetch } from '../lib/api'
import { getAuth } from '../lib/auth'
import type { DocumentItem } from '../lib/types'

type ListResponse = {
  items: DocumentItem[]
  page: number
  page_size: number
}

function buildQuery(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined) return
    const s = String(v).trim()
    if (!s) return
    search.set(k, s)
  })
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export default function ArkivaPage() {
  const { role, email } = getAuth()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const [items, setItems] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [detailsOpen, setDetailsOpen] = useState(false)
  const [detailsDocId, setDetailsDocId] = useState<number | null>(null)

  const [unarchiveOpen, setUnarchiveOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [selected, setSelected] = useState<DocumentItem | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const [replaceOpen, setReplaceOpen] = useState(false)
  const [replaceDoc, setReplaceDoc] = useState<DocumentItem | null>(null)

  const listUrl = useMemo(() => {
    return (
      '/api/documents' +
      buildQuery({
        query,
        category,
        status: 'archived',
        from: from || undefined,
        to: to || undefined,
        page,
        page_size: pageSize,
      })
    )
  }, [query, category, from, to, page, pageSize])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    apiFetch(listUrl)
      .then((res: ListResponse) => {
        if (cancelled) return
        setItems(res.items || [])
      })
      .catch((e: any) => {
        if (cancelled) return
        const msg = e?.payload?.error?.message || 'Gabim gjatë marrjes së dokumenteve'
        setError(msg)
        setItems([])
      })
      .finally(() => {
        if (cancelled) return
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [listUrl])

  function onClearFilters() {
    setQuery('')
    setCategory('')
    setFrom('')
    setTo('')
    setPage(1)
  }

  function openDetails(docId: number) {
    setDetailsDocId(docId)
    setDetailsOpen(true)
  }

  function requestUnarchive(doc: DocumentItem) {
    setSelected(doc)
    setUnarchiveOpen(true)
  }

  function requestDelete(doc: DocumentItem) {
    setSelected(doc)
    setDeleteOpen(true)
  }

  function requestReplace(doc: DocumentItem) {
    setReplaceDoc(doc)
    setReplaceOpen(true)
  }

  async function doUnarchive() {
    if (!selected) return
    setActionLoading(true)
    try {
      await apiFetch(`/api/documents/${selected.id}/unarchive`, {
        method: 'PATCH',
      })

      setItems((prev) => prev.filter((d) => d.id !== selected.id))
      setUnarchiveOpen(false)
      setSelected(null)
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim gjatë rikthimit nga arkivi'
      setError(msg)
    } finally {
      setActionLoading(false)
    }
  }

  async function doDelete() {
    if (!selected) return
    setActionLoading(true)
    try {
      await apiFetch(`/api/documents/${selected.id}`, {
        method: 'DELETE',
      })
      setItems((prev) => prev.filter((d) => d.id !== selected.id))
      setDeleteOpen(false)
      setSelected(null)
    } catch (e: any) {
      const msg = e?.payload?.error?.message || 'Gabim gjatë fshirjes'
      setError(msg)
    } finally {
      setActionLoading(false)
    }
  }

  function onReplaced(updated: DocumentItem) {
    setItems((prev) => prev.map((d) => (d.id === updated.id ? updated : d)))
  }

  return (
    <div>
      <h1 className="text-xl font-semibold">Arkiva</h1>
      <div className="mt-1 text-sm text-slate-600">Dokumentet e arkivuara</div>

      <div className="mt-4">
        <DocumentsFilters
          query={query}
          category={category}
          from={from}
          to={to}
          onChange={(next) => {
            if (next.query !== undefined) setQuery(next.query)
            if (next.category !== undefined) setCategory(next.category)
            if (next.from !== undefined) setFrom(next.from)
            if (next.to !== undefined) setTo(next.to)
            setPage(1)
          }}
          onClear={onClearFilters}
        />
      </div>

      {error ? <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {loading ? <div className="mt-4 text-sm text-slate-600">Duke ngarkuar...</div> : null}

      <div className="mt-4">
        <DocumentsTable
          items={items}
          role={role}
          currentEmail={email}
          showManageActions={true}
          showUnarchiveAction={true}
          onDetails={openDetails}
          onArchive={() => undefined}
          onUnarchive={requestUnarchive}
          onDelete={requestDelete}
          onReplace={requestReplace}
        />
      </div>

      <Pagination
        page={page}
        pageSize={pageSize}
        onChangePage={setPage}
        onChangePageSize={(s) => {
          setPageSize(s)
          setPage(1)
        }}
      />

      <DetailsModal open={detailsOpen} docId={detailsDocId} onClose={() => setDetailsOpen(false)} />

      <ConfirmDialog
        open={unarchiveOpen}
        title="Kthe dokumentin nga arkivi?"
        description={selected ? `"${selected.title}" do të kthehet si active.` : undefined}
        confirmText="Kthe"
        onConfirm={doUnarchive}
        onClose={() => {
          if (actionLoading) return
          setUnarchiveOpen(false)
          setSelected(null)
        }}
        loading={actionLoading}
      />

      <ConfirmDialog
        open={deleteOpen}
        title="Fshi përgjithmonë?"
        description={
          selected
            ? `"${selected.title}" do të fshihet nga DB dhe Drive. Ky veprim nuk kthehet.`
            : undefined
        }
        confirmText="Fshi"
        destructive
        onConfirm={doDelete}
        onClose={() => {
          if (actionLoading) return
          setDeleteOpen(false)
          setSelected(null)
        }}
        loading={actionLoading}
      />

      <ReplaceFileModal
        open={replaceOpen}
        doc={replaceDoc}
        onClose={() => {
          setReplaceOpen(false)
          setReplaceDoc(null)
        }}
        onReplaced={onReplaced}
      />
    </div>
  )
}

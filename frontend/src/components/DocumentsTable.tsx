import type { Role } from '../lib/auth'
import type { DocumentItem } from '../lib/types'

type Props = {
  items: DocumentItem[]
  role: Role | null
  currentEmail: string | null
  showManageActions?: boolean
  onDetails: (docId: number) => void
  onArchive: (doc: DocumentItem) => void
  onDelete: (doc: DocumentItem) => void
  onReplace: (doc: DocumentItem) => void
}

export default function DocumentsTable({
  items,
  role,
  currentEmail,
  showManageActions = true,
  onDetails,
  onArchive,
  onDelete,
  onReplace,
}: Props) {
  const isAdmin = role === 'admin'

  return (
    <div className="overflow-x-auto rounded-xl border bg-white">
      <table className="min-w-full border-separate border-spacing-0">
        <thead>
          <tr className="text-left text-xs font-semibold text-slate-600">
            <th className="border-b px-4 py-3">Titulli</th>
            <th className="border-b px-4 py-3">Kategoria</th>
            <th className="border-b px-4 py-3">Lloji</th>
            <th className="border-b px-4 py-3">Statusi</th>
            <th className="border-b px-4 py-3">Ngarkuar nga</th>
            <th className="border-b px-4 py-3">Krijuar</th>
            <th className="border-b px-4 py-3">Përditësuar</th>
            <th className="border-b px-4 py-3">Veprime</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d) => (
            <tr key={d.id} className="text-sm">
              <td className="border-b px-4 py-3">
                <div className="font-medium text-slate-900">{d.title}</div>
                {d.tags ? <div className="mt-1 text-xs text-slate-500">Tags: {d.tags}</div> : null}
              </td>
              <td className="border-b px-4 py-3 text-slate-700">{d.category}</td>
              <td className="border-b px-4 py-3 text-slate-700">{d.file_type}</td>
              <td className="border-b px-4 py-3 text-slate-700">{d.status}</td>
              <td className="border-b px-4 py-3 text-slate-700">{d.uploaded_by_email || '—'}</td>
              <td className="border-b px-4 py-3 text-slate-700">{new Date(d.created_at).toLocaleDateString()}</td>
              <td className="border-b px-4 py-3 text-slate-700">{new Date(d.updated_at).toLocaleDateString()}</td>
              <td className="border-b px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  {(() => {
                    const isOwner = !!currentEmail && !!d.uploaded_by_email && d.uploaded_by_email === currentEmail
                    const canManageDoc = isAdmin || isOwner
                    return (
                      <>
                  <a
                    href={d.web_view_link}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-slate-50"
                  >
                    Shiko
                  </a>
                  <button
                    type="button"
                    className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-slate-50"
                    onClick={() => onDetails(d.id)}
                  >
                    Detaje
                  </button>

                  {showManageActions ? (
                    <>
                      <button
                        type="button"
                        className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
                        disabled={!canManageDoc}
                        onClick={() => onReplace(d)}
                        title={!canManageDoc ? 'Vetëm ngarkuesi/Admin' : undefined}
                      >
                        Zëvendëso
                      </button>

                      <button
                        type="button"
                        className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
                        disabled={!canManageDoc || d.status === 'archived'}
                        onClick={() => onArchive(d)}
                        title={!canManageDoc ? 'Vetëm ngarkuesi/Admin' : undefined}
                      >
                        Arkivo
                      </button>

                      <button
                        type="button"
                        className="rounded-md border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
                        disabled={!canManageDoc}
                        onClick={() => onDelete(d)}
                        title={!canManageDoc ? 'Vetëm ngarkuesi/Admin' : undefined}
                      >
                        Fshi
                      </button>
                    </>
                  ) : null}
                      </>
                    )
                  })()}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {items.length === 0 ? <div className="p-6 text-sm text-slate-600">Nuk ka rezultate.</div> : null}
    </div>
  )
}

import type { Role } from '../lib/auth'
import type { DocumentItem } from '../lib/types'

type Props = {
  items: DocumentItem[]
  role: Role | null
  showManageActions?: boolean
  onDetails: (docId: number) => void
  onArchive: (doc: DocumentItem) => void
  onDelete: (doc: DocumentItem) => void
  onReplace: (doc: DocumentItem) => void
}

export default function DocumentsTable({
  items,
  role,
  showManageActions = true,
  onDetails,
  onArchive,
  onDelete,
  onReplace,
}: Props) {
  const canManage = role === 'sekretaria' || role === 'admin'
  const canDelete = role === 'admin'

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
                        disabled={!canManage}
                        onClick={() => onReplace(d)}
                        title={!canManage ? 'Vetëm Sekretaria/Admin' : undefined}
                      >
                        Zëvendëso
                      </button>

                      <button
                        type="button"
                        className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
                        disabled={!canManage || d.status === 'archived'}
                        onClick={() => onArchive(d)}
                        title={!canManage ? 'Vetëm Sekretaria/Admin' : undefined}
                      >
                        Arkivo
                      </button>

                      <button
                        type="button"
                        className="rounded-md border border-red-200 bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
                        disabled={!canDelete}
                        onClick={() => onDelete(d)}
                        title={!canDelete ? 'Vetëm Admin' : undefined}
                      >
                        Fshi
                      </button>
                    </>
                  ) : null}
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

type Props = {
  page: number
  pageSize: number
  onChangePage: (page: number) => void
  onChangePageSize: (pageSize: number) => void
}

export default function Pagination({ page, pageSize, onChangePage, onChangePageSize }: Props) {
  return (
    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        <div className="text-sm text-slate-600">Madhësia e faqes</div>
        <select
          className="rounded-md border bg-white px-2 py-1 text-sm"
          value={pageSize}
          onChange={(e) => onChangePageSize(Number(e.target.value))}
        >
          {[10, 20, 50, 100].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          className="rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
          disabled={page <= 1}
          onClick={() => onChangePage(Math.max(1, page - 1))}
        >
          Prev
        </button>
        <div className="text-sm text-slate-700">Faqja: {page}</div>
        <button
          type="button"
          className="rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50"
          onClick={() => onChangePage(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  )
}

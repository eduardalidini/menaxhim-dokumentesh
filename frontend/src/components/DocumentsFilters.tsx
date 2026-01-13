type Props = {
  query: string
  category: string
  from: string
  to: string
  onChange: (next: Partial<{ query: string; category: string; from: string; to: string }>) => void
  onClear: () => void
}

export default function DocumentsFilters({ query, category, from, to, onChange, onClear }: Props) {
  return (
    <div className="rounded-xl border bg-white p-4">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-700">Kërko</label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            placeholder="Titulli..."
            value={query}
            onChange={(e) => onChange({ query: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Kategoria</label>
          <select
            className="mt-1 w-full rounded-md border bg-white px-3 py-2"
            value={category}
            onChange={(e) => onChange({ category: e.target.value })}
          >
            <option value="">Të gjitha</option>
            <option value="request">request</option>
            <option value="decision">decision</option>
            <option value="form">form</option>
            <option value="announcement">announcement</option>
          </select>
        </div>

        <div className="flex items-end justify-end">
          <button
            type="button"
            className="w-full rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50"
            onClick={onClear}
          >
            Pastro filtrat
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-5">
        <div>
          <label className="block text-sm font-medium text-slate-700">Nga</label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            type="date"
            value={from}
            onChange={(e) => onChange({ from: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Deri</label>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            type="date"
            value={to}
            onChange={(e) => onChange({ to: e.target.value })}
          />
        </div>
        <div className="md:col-span-3" />
      </div>
    </div>
  )
}

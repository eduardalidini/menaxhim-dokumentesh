type Props = {
  open: boolean
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  destructive?: boolean
  loading?: boolean
  onConfirm: () => void
  onClose: () => void
}

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmText = 'Konfirmo',
  cancelText = 'Anulo',
  destructive = false,
  loading = false,
  onConfirm,
  onClose,
}: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-xl border bg-white p-5 shadow-lg">
        <div className="text-lg font-semibold">{title}</div>
        {description ? <div className="mt-2 text-sm text-slate-600">{description}</div> : null}

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            className="rounded-md border px-3 py-2 text-sm font-medium hover:bg-slate-50"
            onClick={onClose}
            disabled={loading}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={[
              'rounded-md px-3 py-2 text-sm font-medium text-white disabled:opacity-50',
              destructive ? 'bg-red-600 hover:bg-red-500' : 'bg-slate-900 hover:bg-slate-800',
            ].join(' ')}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Duke vepruar...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

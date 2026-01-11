import { Link } from 'react-router-dom'

export default function PublicHomePage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Menaxhim Dokumentesh</h1>
        <p className="mt-3 text-slate-700">
          Aplikacion për menaxhimin e dokumenteve: ngarkim, kërkim, arkivim dhe menaxhim i skedarëve në Google Drive.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/login"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Kyçu
          </Link>
          <Link to="/privacy" className="rounded-md border bg-white px-4 py-2 text-sm hover:bg-slate-50">
            Privacy Policy
          </Link>
          <Link to="/terms" className="rounded-md border bg-white px-4 py-2 text-sm hover:bg-slate-50">
            Terms
          </Link>
        </div>

        <div className="mt-10 border-t pt-6 text-sm text-slate-600">
          <div>Kontakt: (vendos email-in tënd këtu)</div>
        </div>
      </main>
    </div>
  )
}

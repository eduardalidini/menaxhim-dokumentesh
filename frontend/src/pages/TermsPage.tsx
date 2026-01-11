import { Link } from 'react-router-dom'

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Terms of Service</h1>
        <p className="mt-3 text-slate-700">
          Duke përdorur aplikacionin Menaxhim Dokumentesh, pranoni këto kushte përdorimi.
        </p>

        <h2 className="mt-8 text-xl font-semibold">Përdorimi i aplikacionit</h2>
        <ul className="mt-3 list-disc pl-5 text-slate-700">
          <li>Përdoruesit duhet të jenë të autorizuar nga administratori.</li>
          <li>Nuk lejohet ngarkimi i përmbajtjeve të paligjshme ose të paautorizuara.</li>
          <li>Administratori menaxhon lidhjen me Google Drive.</li>
        </ul>

        <h2 className="mt-8 text-xl font-semibold">Përgjegjësia</h2>
        <p className="mt-3 text-slate-700">
          Aplikacioni ofrohet “as is”. Administratori është përgjegjës për konfigurimin dhe akseset.
        </p>

        <h2 className="mt-8 text-xl font-semibold">Kontakt</h2>
        <p className="mt-3 text-slate-700">Për pyetje rreth kushteve, kontakto: eduardi.alidini@gmail.com</p>

        <div className="mt-10 border-t pt-6 text-sm">
          <Link to="/" className="text-slate-700 underline">
            Kthehu te Home
          </Link>
        </div>
      </main>
    </div>
  )
}

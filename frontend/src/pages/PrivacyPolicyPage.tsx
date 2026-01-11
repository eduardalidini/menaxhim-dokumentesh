import { Link } from 'react-router-dom'

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Privacy Policy</h1>
        <p className="mt-3 text-slate-700">
          Kjo faqe përshkruan mënyrën se si aplikacioni Menaxhim Dokumentesh mbledh, përdor dhe mbron të dhënat.
        </p>

        <h2 className="mt-8 text-xl font-semibold">Të dhënat që përpunohen</h2>
        <ul className="mt-3 list-disc pl-5 text-slate-700">
          <li>Kredencialet e hyrjes (email dhe fjalëkalim i hash-uar në server).</li>
          <li>Metadata të dokumenteve (titull, kategori, status, data, lidhja e skedarit në Drive).</li>
          <li>Skedarët ruhen në Google Drive të lidhur nga administratori.</li>
        </ul>

        <h2 className="mt-8 text-xl font-semibold">Google Drive OAuth</h2>
        <p className="mt-3 text-slate-700">
          Aplikacioni përdor OAuth 2.0 për të autorizuar akses në Google Drive vetëm për qëllimin e ruajtjes dhe
          menaxhimit të skedarëve të dokumenteve. Një refresh token ruhet në server për të mbajtur lidhjen aktive.
        </p>

        <h2 className="mt-8 text-xl font-semibold">Ruajtja dhe siguria</h2>
        <p className="mt-3 text-slate-700">
          Të dhënat ruhen në bazë të të dhënave (PostgreSQL) dhe aksesohen vetëm nga përdorues të autentikuar.
        </p>

        <h2 className="mt-8 text-xl font-semibold">Kontakt</h2>
        <p className="mt-3 text-slate-700">Për pyetje rreth privatësisë, kontakto: eduardi.alidini@gmail.com</p>

        <div className="mt-10 border-t pt-6 text-sm">
          <Link to="/" className="text-slate-700 underline">
            Kthehu te Home
          </Link>
        </div>
      </main>
    </div>
  )
}

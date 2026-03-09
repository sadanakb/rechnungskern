export const metadata = {
  title: 'Impressum — RechnungsKern',
  description: 'Impressum und Anbieterkennzeichnung gemaess § 5 TMG',
}

export default function ImpressumPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold mb-8">Impressum</h1>

      <div className="space-y-6 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold mb-2">Angaben gemaess § 5 TMG</h2>
          <p>
            RechnungsKern<br />
            {process.env.NEXT_PUBLIC_COMPANY_NAME || '[Nicht konfiguriert]'}<br />
            {process.env.NEXT_PUBLIC_COMPANY_STREET || '[Nicht konfiguriert]'}<br />
            {process.env.NEXT_PUBLIC_COMPANY_CITY || '[Nicht konfiguriert]'}<br />
            Deutschland
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2">Kontakt</h2>
          <p>
            E-Mail: kontakt@rechnungskern.de<br />
            Telefon: {process.env.NEXT_PUBLIC_COMPANY_PHONE || '[Nicht konfiguriert]'}
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2">Umsatzsteuer-ID</h2>
          <p>
            Umsatzsteuer-Identifikationsnummer gemaess § 27a UStG:<br />
            {process.env.NEXT_PUBLIC_COMPANY_VAT_ID || '[Nicht konfiguriert]'}
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2">Verantwortlich fuer den Inhalt nach § 18 Abs. 2 MStV</h2>
          <p>
            {process.env.NEXT_PUBLIC_COMPANY_RESPONSIBLE_NAME || '[Nicht konfiguriert]'}<br />
            {process.env.NEXT_PUBLIC_COMPANY_RESPONSIBLE_ADDRESS || '[Nicht konfiguriert]'}
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2">EU-Streitschlichtung</h2>
          <p>
            Die Europaeische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:{' '}
            <a href="https://ec.europa.eu/consumers/odr/" className="underline" style={{ color: 'rgb(var(--primary))' }}>
              https://ec.europa.eu/consumers/odr/
            </a>
          </p>
          <p className="mt-2">
            Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
            Verbraucherschlichtungsstelle teilzunehmen.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2">Haftungsausschluss</h2>
          <p>
            Die Inhalte dieser Website wurden mit groesster Sorgfalt erstellt. Fuer die Richtigkeit,
            Vollstaendigkeit und Aktualitaet der Inhalte koennen wir jedoch keine Gewaehr uebernehmen.
          </p>
        </section>
      </div>
    </main>
  )
}

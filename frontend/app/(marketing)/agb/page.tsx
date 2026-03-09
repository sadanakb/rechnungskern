export const metadata = {
  title: 'AGB — RechnungsKern',
  description: 'Allgemeine Geschaeftsbedingungen von RechnungsKern',
}

export default function AGBPage() {
  const company = process.env.NEXT_PUBLIC_COMPANY_NAME || 'RechnungsKern'

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold mb-8">Allgemeine Geschaeftsbedingungen</h1>

      {/* Warning banner */}
      <div className="mb-8 rounded-lg border border-amber-400 bg-amber-50 px-6 py-4 text-amber-900 dark:border-amber-500 dark:bg-amber-950/40 dark:text-amber-200">
        <p className="font-semibold">
          Entwurf — Diese AGB sind ein Muster und wurden nicht anwaltlich geprueft.
          Eine rechtliche Ueberpruefung wird dringend empfohlen.
        </p>
      </div>

      <p className="mb-6 opacity-70 text-sm">Stand: Maerz 2026</p>

      <div className="space-y-8 leading-relaxed">
        {/* §1 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;1 Geltungsbereich</h2>
          <p className="mb-2">
            (1) Diese Allgemeinen Geschaeftsbedingungen (nachfolgend &bdquo;AGB&ldquo;) gelten fuer
            saemtliche Vertraege zwischen {company} (nachfolgend &bdquo;Anbieter&ldquo;) und dem
            Kunden (nachfolgend &bdquo;Nutzer&ldquo;) ueber die Nutzung der unter{' '}
            <strong>rechnungskern.de</strong> bereitgestellten Software-as-a-Service-Loesung
            (nachfolgend &bdquo;Dienst&ldquo; oder &bdquo;Plattform&ldquo;).
          </p>
          <p className="mb-2">
            (2) Abweichende, entgegenstehende oder ergaenzende AGB des Nutzers werden nicht
            Vertragsbestandteil, es sei denn, der Anbieter stimmt ihrer Geltung ausdruecklich
            schriftlich zu.
          </p>
          <p>
            (3) Der Nutzer erklaert sich mit diesen AGB einverstanden, indem er sich fuer den Dienst
            registriert oder diesen nutzt.
          </p>
        </section>

        {/* §2 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;2 Vertragsgegenstand</h2>
          <p className="mb-2">
            (1) Gegenstand des Vertrages ist die Bereitstellung der webbasierten
            SaaS-Rechnungssoftware &bdquo;{company}&ldquo; zur Erstellung, Verwaltung und
            Archivierung von Rechnungen, Angeboten und weiteren Geschaeftsdokumenten.
          </p>
          <p className="mb-2">
            (2) Der Anbieter stellt die Plattform ueber das Internet zur Nutzung bereit. Der Nutzer
            erhaelt ein nicht-exklusives, nicht uebertragbares, zeitlich auf die Vertragslaufzeit
            beschraenktes Nutzungsrecht.
          </p>
          <p>
            (3) Der genaue Funktionsumfang ergibt sich aus der jeweils aktuellen
            Leistungsbeschreibung auf der Webseite des Anbieters sowie dem vom Nutzer gewaehlten
            Tarifplan.
          </p>
        </section>

        {/* §3 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;3 Registrierung und Nutzerkonto</h2>
          <p className="mb-2">
            (1) Die Nutzung des Dienstes setzt eine Registrierung voraus. Der Nutzer ist
            verpflichtet, bei der Registrierung wahrheitsgemaesse und vollstaendige Angaben zu
            machen und diese aktuell zu halten.
          </p>
          <p className="mb-2">
            (2) Der Nutzer ist fuer die Geheimhaltung seiner Zugangsdaten selbst verantwortlich.
            Er hat den Anbieter unverzueglich zu informieren, wenn er Kenntnis von einer
            unberechtigten Nutzung seines Kontos erhaelt.
          </p>
          <p className="mb-2">
            (3) Jeder Nutzer darf nur ein Konto anlegen. Das Konto ist nicht uebertragbar.
          </p>
          <p>
            (4) Der Anbieter ist berechtigt, Nutzerkonten zu sperren oder zu loeschen, wenn
            begruendete Anhaltspunkte fuer einen Verstoss gegen diese AGB oder geltendes Recht
            vorliegen.
          </p>
        </section>

        {/* §4 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;4 Leistungsbeschreibung</h2>
          <p className="mb-2">
            (1) Der Anbieter stellt dem Nutzer folgende Kernfunktionen bereit:
          </p>
          <ul className="list-disc pl-6 mb-2 space-y-1">
            <li>Erstellung und Verwaltung von Rechnungen, Angeboten und Gutschriften</li>
            <li>Kundenverwaltung und Kontaktdatenbank</li>
            <li>Automatische Rechnungsnummernvergabe</li>
            <li>PDF-Export und E-Mail-Versand von Dokumenten</li>
            <li>OCR-basierte Belegerfassung (je nach Tarif)</li>
            <li>Dashboard mit Umsatzuebersichten</li>
          </ul>
          <p className="mb-2">
            (2) Der Anbieter behaelt sich vor, den Funktionsumfang zu erweitern, zu aendern oder
            Funktionen einzustellen, sofern dies fuer den Nutzer zumutbar ist und keine wesentliche
            Einschraenkung der vertraglich vereinbarten Leistung darstellt.
          </p>
          <p>
            (3) Der Nutzer traegt die Verantwortung fuer die Richtigkeit der von ihm eingegebenen
            Daten, insbesondere hinsichtlich steuerrechtlicher und handelsrechtlicher
            Anforderungen.
          </p>
        </section>

        {/* §5 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">
            &sect;5 Verguetung und Zahlungsbedingungen
          </h2>
          <p className="mb-2">
            (1) Die Nutzung des Dienstes kann kostenlose und kostenpflichtige Tarifplaene umfassen.
            Die jeweils gueltigen Preise ergeben sich aus der Preisliste auf der Webseite des
            Anbieters.
          </p>
          <p className="mb-2">
            (2) Alle Preise verstehen sich, sofern nicht anders angegeben, als Nettopreise
            zuzueglich der gesetzlichen Umsatzsteuer.
          </p>
          <p className="mb-2">
            (3) Die Abrechnung erfolgt, je nach gewaehltem Tarif, monatlich oder jaehrlich im
            Voraus. Rechnungen werden dem Nutzer elektronisch bereitgestellt.
          </p>
          <p className="mb-2">
            (4) Der Nutzer ermaechtigt den Anbieter zum Einzug der faelligen Betraege per
            SEPA-Lastschrift oder Kreditkarte, sofern ein entsprechendes Zahlungsmittel hinterlegt
            ist. Alternativ ist eine Zahlung per Ueberweisung moeglich.
          </p>
          <p>
            (5) Kommt der Nutzer mit einer Zahlung in Verzug, ist der Anbieter berechtigt, den
            Zugang zum Dienst nach vorheriger Mahnung mit angemessener Fristsetzung einzuschraenken
            oder zu sperren. Die Pflicht zur Zahlung der vereinbarten Verguetung bleibt hiervon
            unberuehrt.
          </p>
        </section>

        {/* §6 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;6 Verfuegbarkeit und Wartung</h2>
          <p className="mb-2">
            (1) Der Anbieter ist bemueht, eine moeglichst hohe Verfuegbarkeit des Dienstes zu
            gewaehrleisten. Eine Verfuegbarkeit von 99,5 % im Jahresmittel wird angestrebt, bezogen
            auf 24 Stunden am Tag, 7 Tage die Woche. Ausgenommen hiervon sind Zeiten planmaessiger
            Wartung sowie Stoerungen, die ausserhalb des Einflussbereichs des Anbieters liegen
            (hoehere Gewalt, Stoerungen bei Drittanbietern etc.).
          </p>
          <p className="mb-2">
            (2) Wartungsarbeiten werden, soweit moeglich, ausserhalb der ueblichen Geschaeftszeiten
            durchgefuehrt und rechtzeitig angekuendigt.
          </p>
          <p>
            (3) Der Anbieter haftet nicht fuer Unterbrechungen oder Leistungsminderungen, die auf
            Umstaende zurueckzufuehren sind, die ausserhalb seines Einflussbereichs liegen,
            insbesondere Stoerungen der Internetverbindung des Nutzers oder Ausfaelle von
            Drittdiensten.
          </p>
        </section>

        {/* §7 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;7 Datenschutz</h2>
          <p className="mb-2">
            (1) Der Anbieter erhebt, verarbeitet und nutzt personenbezogene Daten des Nutzers nur
            im Rahmen der geltenden Datenschutzgesetze, insbesondere der
            Datenschutz-Grundverordnung (DSGVO) und des Bundesdatenschutzgesetzes (BDSG).
          </p>
          <p className="mb-2">
            (2) Einzelheiten zur Datenverarbeitung, insbesondere zu Art, Umfang und Zweck der
            Erhebung sowie zu den Rechten des Nutzers, sind in der{' '}
            <a
              href="/datenschutz"
              className="underline"
              style={{ color: 'rgb(var(--primary))' }}
            >
              Datenschutzerklaerung
            </a>{' '}
            dargelegt.
          </p>
          <p className="mb-2">
            (3) Sofern der Nutzer den Dienst zur Verarbeitung personenbezogener Daten Dritter
            einsetzt (z.&thinsp;B. Kundendaten auf Rechnungen), handelt der Anbieter als
            Auftragsverarbeiter im Sinne von Art. 28 DSGVO. Ein entsprechender
            Auftragsverarbeitungsvertrag (AVV) wird auf Anfrage bereitgestellt.
          </p>
          <p>
            (4) Der Nutzer ist dafuer verantwortlich, dass er die erforderlichen Rechtsgrundlagen
            fuer die Verarbeitung personenbezogener Daten Dritter ueber den Dienst einholt.
          </p>
        </section>

        {/* §8 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;8 Haftungsbeschraenkung</h2>
          <p className="mb-2">
            (1) Der Anbieter haftet unbeschraenkt fuer Vorsatz und grobe Fahrlaessigkeit sowie
            fuer Schaeden aus der Verletzung des Lebens, des Koerpers oder der Gesundheit.
          </p>
          <p className="mb-2">
            (2) Bei leichter Fahrlaessigkeit haftet der Anbieter nur bei Verletzung einer
            wesentlichen Vertragspflicht (Kardinalpflicht). In diesem Fall ist die Haftung auf den
            vertragstypischen, vorhersehbaren Schaden begrenzt.
          </p>
          <p className="mb-2">
            (3) Die Haftung fuer mittelbare Schaeden, Folgeschaeden, entgangenen Gewinn oder
            Datenverlust ist — soweit gesetzlich zulaessig — ausgeschlossen.
          </p>
          <p className="mb-2">
            (4) Die vorstehenden Haftungsbeschraenkungen gelten auch zugunsten der Erfuellungsgehilfen
            und gesetzlichen Vertreter des Anbieters.
          </p>
          <p>
            (5) Der Anbieter haftet nicht fuer die inhaltliche Richtigkeit der vom Nutzer erstellten
            Dokumente (z.&thinsp;B. Rechnungen). Die steuer- und handelsrechtliche Konformitaet
            obliegt dem Nutzer.
          </p>
        </section>

        {/* §9 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;9 Gewaehrleistung</h2>
          <p className="mb-2">
            (1) Der Anbieter gewaehrleistet, dass der Dienst im Wesentlichen der
            Leistungsbeschreibung entspricht und frei von wesentlichen Maengeln bereitgestellt wird.
          </p>
          <p className="mb-2">
            (2) Der Nutzer ist verpflichtet, Maengel unverzueglich nach deren Entdeckung schriftlich
            oder per E-Mail an{' '}
            <a
              href="mailto:kontakt@rechnungskern.de"
              className="underline"
              style={{ color: 'rgb(var(--primary))' }}
            >
              kontakt@rechnungskern.de
            </a>{' '}
            zu melden und dabei den Mangel moeglichst genau zu beschreiben.
          </p>
          <p className="mb-2">
            (3) Bei Vorliegen eines Mangels ist der Anbieter zur Nachbesserung berechtigt. Schlaegt
            die Nachbesserung nach angemessener Frist fehl, kann der Nutzer die Verguetung mindern
            oder — bei erheblichen Maengeln — den Vertrag ausserordentlich kuendigen.
          </p>
          <p>
            (4) Gewaehrleistungsansprueche verjaehren zwoelf Monate nach ihrer Entstehung, sofern
            gesetzlich zulaessig.
          </p>
        </section>

        {/* §10 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">
            &sect;10 Vertragslaufzeit und Kuendigung
          </h2>
          <p className="mb-2">
            (1) Der Vertrag wird auf unbestimmte Zeit geschlossen, sofern nicht ein befristeter
            Tarif gewaehlt wurde.
          </p>
          <p className="mb-2">
            (2) Bei monatlicher Abrechnung kann der Vertrag von beiden Seiten mit einer Frist von
            14 Tagen zum Ende des jeweiligen Abrechnungszeitraums gekuendigt werden.
          </p>
          <p className="mb-2">
            (3) Bei jaehrlicher Abrechnung kann der Vertrag mit einer Frist von einem Monat zum
            Ende der jeweiligen Vertragslaufzeit gekuendigt werden. Wird nicht fristgerecht
            gekuendigt, verlaengert sich der Vertrag automatisch um ein weiteres Jahr.
          </p>
          <p className="mb-2">
            (4) Das Recht zur ausserordentlichen Kuendigung aus wichtigem Grund bleibt beiden
            Parteien vorbehalten. Ein wichtiger Grund liegt insbesondere vor, wenn der Nutzer
            wesentlich gegen diese AGB verstoesst oder mit der Zahlung trotz Mahnung laenger als
            30 Tage in Verzug ist.
          </p>
          <p className="mb-2">
            (5) Die Kuendigung hat schriftlich oder in Textform (z.&thinsp;B. per E-Mail) zu
            erfolgen.
          </p>
          <p>
            (6) Nach Vertragsende wird der Anbieter dem Nutzer seine Daten fuer einen Zeitraum
            von 30 Tagen zum Export bereitstellen. Nach Ablauf dieser Frist werden die Daten
            unwiderruflich geloescht, sofern keine gesetzlichen Aufbewahrungspflichten
            entgegenstehen.
          </p>
        </section>

        {/* §11 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;11 Aenderungen der AGB</h2>
          <p className="mb-2">
            (1) Der Anbieter behaelt sich vor, diese AGB mit Wirkung fuer die Zukunft zu aendern,
            sofern die Aenderung unter Beruecksichtigung der Interessen des Anbieters fuer den
            Nutzer zumutbar ist.
          </p>
          <p className="mb-2">
            (2) Der Anbieter wird den Nutzer ueber Aenderungen mindestens sechs Wochen vor deren
            Inkrafttreten per E-Mail informieren. Widerspricht der Nutzer nicht innerhalb von
            sechs Wochen nach Zugang der Aenderungsmitteilung, gelten die geaenderten AGB als
            angenommen. Der Anbieter wird den Nutzer in der Aenderungsmitteilung auf die Bedeutung
            der Frist und die Folgen des Schweigens gesondert hinweisen.
          </p>
          <p>
            (3) Widerspricht der Nutzer der Aenderung, besteht der Vertrag zu den bisherigen
            Bedingungen fort. Der Anbieter ist in diesem Fall berechtigt, den Vertrag ordentlich
            zum naechstmoeglichen Termin zu kuendigen.
          </p>
        </section>

        {/* §12 */}
        <section>
          <h2 className="text-xl font-semibold mb-2">&sect;12 Schlussbestimmungen</h2>
          <p className="mb-2">
            (1) Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts
            (CISG).
          </p>
          <p className="mb-2">
            (2) Ist der Nutzer Kaufmann, juristische Person des oeffentlichen Rechts oder
            oeffentlich-rechtliches Sondervermoegen, ist ausschliesslicher Gerichtsstand fuer alle
            Streitigkeiten aus oder im Zusammenhang mit diesem Vertrag der Sitz des Anbieters.
          </p>
          <p className="mb-2">
            (3) Sollte eine Bestimmung dieser AGB unwirksam oder undurchfuehrbar sein oder werden,
            so wird die Wirksamkeit der uebrigen Bestimmungen hierdurch nicht beruehrt. An die
            Stelle der unwirksamen oder undurchfuehrbaren Bestimmung tritt diejenige wirksame und
            durchfuehrbare Regelung, die dem wirtschaftlichen Zweck der unwirksamen bzw.
            undurchfuehrbaren Bestimmung am naechsten kommt (salvatorische Klausel).
          </p>
          <p>
            (4) Nebenabreden, Aenderungen und Ergaenzungen dieses Vertrages beduerfen der Textform.
            Dies gilt auch fuer die Aufhebung dieses Textformerfordernisses.
          </p>
        </section>

        {/* Contact */}
        <section className="rounded-lg border p-6" style={{ borderColor: 'rgb(var(--border))', backgroundColor: 'rgb(var(--card))' }}>
          <h2 className="text-xl font-semibold mb-2">Kontakt</h2>
          <p>
            Bei Fragen zu diesen AGB wenden Sie sich bitte an:{' '}
            <a
              href="mailto:kontakt@rechnungskern.de"
              className="underline"
              style={{ color: 'rgb(var(--primary))' }}
            >
              kontakt@rechnungskern.de
            </a>
          </p>
        </section>
      </div>
    </main>
  )
}

export const FIELD_HELP: Record<string, { title: string; description: string; example?: string }> = {
  invoice_number: {
    title: 'Rechnungsnummer (BT-1)',
    description: 'Eine eindeutige, fortlaufende Nummer für diese Rechnung. Wird automatisch generiert, kann aber angepasst werden. Lücken in der Nummerierung sind seit 2017 erlaubt.',
    example: 'RE-2026-0042',
  },
  invoice_date: {
    title: 'Rechnungsdatum (BT-2)',
    description: 'Das Ausstellungsdatum der Rechnung. Kann das heutige Datum oder ein Datum in der Vergangenheit sein (z.B. bei nachträglicher Rechnungsstellung). Darf nicht in der Zukunft liegen.',
    example: '2026-03-09',
  },
  due_date: {
    title: 'Fälligkeitsdatum (BT-9)',
    description: 'Bis wann die Rechnung bezahlt werden soll. Üblich sind 14 oder 30 Tage nach Rechnungsdatum. Wird automatisch aus den Zahlungsbedingungen berechnet.',
    example: '2026-04-15',
  },
  buyer_reference: {
    title: 'Leitweg-ID / Buyer Reference (BT-10)',
    description: 'Die Leitweg-ID ist eine Kennung des Rechnungsempfängers, die bei öffentlichen Auftraggebern Pflicht ist. Bei privaten Unternehmen können Sie hier eine Bestellnummer oder Projektreferenz eintragen. Falls nicht bekannt, tragen Sie "n/a" ein.',
    example: '04011000-1234512345-35',
  },
  seller_vat_id: {
    title: 'USt-IdNr. Verkäufer (BT-31)',
    description: 'Ihre Umsatzsteuer-Identifikationsnummer. Diese beginnt in Deutschland immer mit "DE" gefolgt von 9 Ziffern. Sie erhalten diese vom Bundeszentralamt für Steuern.',
    example: 'DE123456789',
  },
  buyer_vat_id: {
    title: 'USt-IdNr. Käufer (BT-48)',
    description: 'Die Umsatzsteuer-Identifikationsnummer Ihres Kunden. Optional bei Inlandsrechnungen, aber empfohlen für den Vorsteuerabzug.',
    example: 'DE987654321',
  },
  iban: {
    title: 'IBAN (BT-84)',
    description: 'Ihre internationale Bankkontonummer. In Deutschland 22 Zeichen lang, beginnt mit "DE". Diese wird auf der Rechnung als Zahlungsinformation angegeben.',
    example: 'DE89 3704 0044 0532 0130 00',
  },
  bic: {
    title: 'BIC / SWIFT (BT-86)',
    description: 'Der Bank Identifier Code Ihrer Bank. 8 oder 11 Zeichen lang. Finden Sie auf Ihrem Kontoauszug oder im Online-Banking.',
    example: 'COBADEFFXXX',
  },
  payment_account_name: {
    title: 'Kontoinhaber (BT-85)',
    description: 'Name des Kontoinhabers. Muss mit dem Namen auf dem Bankkonto übereinstimmen.',
    example: 'Max Mustermann',
  },
  seller_endpoint_id: {
    title: 'Elektronische Adresse Verkäufer (BT-34)',
    description: 'Ihre elektronische Adresse für den E-Rechnungsempfang. In den meisten Fällen ist das Ihre E-Mail-Adresse. Bei PEPPOL-Teilnehmern die PEPPOL-ID.',
    example: 'rechnung@meinefirma.de',
  },
  buyer_endpoint_id: {
    title: 'Elektronische Adresse Käufer (BT-49)',
    description: 'Die elektronische Adresse Ihres Kunden. Meistens die E-Mail-Adresse des Rechnungsempfängers.',
    example: 'buchhaltung@kunde.de',
  },
  seller_endpoint_scheme: {
    title: 'Endpoint Schema (BT-34-1)',
    description: 'Das Schema der elektronischen Adresse. "EM" für E-Mail (Standard), "0088" für GLN, "0204" für Leitweg-ID. Wählen Sie "EM" wenn Sie unsicher sind.',
    example: 'EM',
  },
  buyer_endpoint_scheme: {
    title: 'Endpoint Schema Käufer (BT-49-1)',
    description: 'Das Schema der elektronischen Adresse des Käufers. Gleiche Optionen wie beim Verkäufer. "EM" für E-Mail ist der Standard.',
    example: 'EM',
  },
  tax_rate: {
    title: 'Steuersatz',
    description: 'Der Umsatzsteuersatz. In Deutschland üblich: 19% (Regelsteuersatz) oder 7% (ermäßigt, z.B. für Lebensmittel, Bücher, Kunstwerke). Kleinunternehmer nach §19 UStG wählen 0%.',
    example: '19',
  },
  net_amount: {
    title: 'Nettobetrag',
    description: 'Der Rechnungsbetrag ohne Umsatzsteuer. Die Summe aller Einzelpositionen vor Steuer.',
    example: '1.000,00 EUR',
  },
  gross_amount: {
    title: 'Bruttobetrag',
    description: 'Der Gesamtbetrag inklusive Umsatzsteuer. Netto + MwSt = Brutto. Dieser Betrag wird vom Kunden bezahlt.',
    example: '1.190,00 EUR',
  },
  currency: {
    title: 'Währung (BT-5)',
    description: 'Der ISO 4217 Währungscode. Für deutsche Rechnungen fast immer EUR. Andere Beispiele: USD (US-Dollar), CHF (Schweizer Franken), GBP (Britisches Pfund).',
    example: 'EUR',
  },
  payment_terms: {
    title: 'Zahlungsziel (Tage)',
    description: 'Anzahl Tage ab Rechnungsdatum, bis die Rechnung bezahlt werden muss. Üblich: 14 Tage (kurz), 30 Tage (Standard), 60 Tage (lang). Das Fälligkeitsdatum wird automatisch berechnet.',
    example: '30',
  },
  credit_note_reason: {
    title: 'Grund der Gutschrift',
    description: 'Warum wird diese Gutschrift ausgestellt? Der Grund erscheint auf der Gutschrift und im DATEV-Export. Gängige Gründe: Storno, Fehllieferung, Preisnachlass, Reklamation, Teilstorno.',
    example: 'Storno der Rechnung RE-2026-0041',
  },
  team_role: {
    title: 'Rolle im Team',
    description: 'Owner: Volle Kontrolle, kann die Organisation löschen und alle Einstellungen ändern. Admin: Kann Rechnungen erstellen, Mitglieder einladen und Einstellungen ändern. Member: Kann Rechnungen erstellen und einsehen, aber keine Einstellungen ändern.',
  },
  datev_berater_nr: {
    title: 'DATEV Beraternummer',
    description: 'Die 5-stellige Beraternummer Ihres Steuerberaters. Erhalten Sie von Ihrem Steuerberater. Wird für den DATEV-Export benötigt.',
    example: '12345',
  },
  datev_mandant_nr: {
    title: 'DATEV Mandantennummer',
    description: 'Ihre 5-stellige Mandantennummer bei Ihrem Steuerberater. Erhalten Sie von Ihrem Steuerberater.',
    example: '67890',
  },
  webhook_url: {
    title: 'Webhook URL',
    description: 'Die URL an die RechnungsWerk Ereignisse sendet (z.B. wenn eine Rechnung erstellt oder bezahlt wird). Muss eine gültige HTTPS-URL sein die POST-Requests entgegennimmt.',
    example: 'https://meine-app.de/api/webhooks/rechnungswerk',
  },
}

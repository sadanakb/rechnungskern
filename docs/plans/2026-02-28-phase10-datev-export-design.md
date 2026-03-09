# Phase 10: DATEV-Export Design

**Date:** 2026-02-28
**Status:** Approved
**Author:** Brainstorming session

---

## Ziel

DATEV EXTF Buchungsstapel-Export (v700) direkt aus RechnungsKern heraus — auf Basis der Phase-9-SKR03-Kategorisierung. Steuerberater können die ZIP-Datei direkt in DATEV Kanzlei-Rechnungswesen importieren.

---

## Entscheidungen

| Entscheidung | Wahl | Begründung |
|---|---|---|
| Export-Modus | Sync-Download (ZIP Response) | KMU-Volumina <500 Rechnungen/Quartal, kein ARQ nötig |
| Nicht-kategorisierte Rechnungen | Ausschließen + Warnung | Steuerberater braucht vollständige SKR03-Daten |
| Beraternummer/Mandantennummer | In Org-Settings speichern | EXTF-Pflichtfelder, müssen pro Organisation konfiguriert sein |
| DATEV Format | EXTF v700 | Industriestandard, alle modernen DATEV-Kanzleiprogramme |
| E-Mail | "An Steuerberater senden" Button | Nutzt Phase-8-E-Mail-Infrastruktur (send_email ARQ task) |

---

## Architektur

### Backend — neue Dateien

**`backend/app/datev_formatter.py`** — Pure-Function-Modul (kein DB-Zugriff):
```
format_buchungsstapel(invoices, org_settings) -> str
format_stammdaten(contacts) -> str
build_extf_header(org_settings, from_date, to_date) -> str
```

**`backend/app/routers/datev.py`** — FastAPI Router:
```
GET  /api/datev/export?from_month=YYYY-MM&to_month=YYYY-MM  → StreamingResponse (application/zip)
POST /api/datev/send-email                                   → 200 OK
```

**`backend/alembic/versions/phase10_datev_settings.py`** — Migration:
```
organizations.datev_berater_nr  VARCHAR(5)  NULL
organizations.datev_mandant_nr  VARCHAR(5)  NULL
organizations.steuerberater_email VARCHAR(200) NULL
```

### Frontend — 2 Seiten

**`/settings`** — neue Sektion "DATEV-Konfiguration":
- Input: Beraternummer (5-stellig, /^\d{5}$/)
- Input: Mandantennummer (5-stellig)
- Input: Steuerberater-E-Mail (optional)
- Save-Button → PUT /api/organizations/settings

**`/berichte`** — neuer Export-Block:
- Monats-Picker (Von/Bis)
- Statusanzeige: "X von Y Rechnungen kategorisiert"
- Button: "ZIP Exportieren" → GET /api/datev/export (Browser-Download)
- Button: "An Steuerberater senden" → POST /api/datev/send-email (nur wenn steuerberater_email konfiguriert)

---

## DATEV EXTF Format v700

### Buchungsstapel.csv

**Zeile 1 — EXTF Header:**
```
EXTF;700;21;Buchungsstapel;3;{timestamp};{Beraternummer};{Mandantennummer};{WJ-Beginn};{Datumsbereich-Von};{Datumsbereich-Bis};{Bezeichnung};;;0;EUR;
```

**Zeile 2 — Spaltenbeschriftungen:**
```
Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Kurs;BU-Schlüssel;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Belegfeld 1;Buchungstext;Konto
```

**Zeilen 3+ — Buchungszeilen:**
```
1190,00;S;EUR;;0;10000;0101;RE-2024-001;Büromaterial;4930
```

Feldmapping:
- `Umsatz` ← `invoice.total_amount` (Komma als Dezimaltrennzeichen)
- `S/H` ← immer `S` (Soll = Ausgabe) für Eingangsrechnungen
- `WKZ` ← `EUR` (hardcoded)
- `Konto` ← `invoice.skr03_account`
- `Gegenkonto` ← Lieferantennummer (aus Contacts, 5-stellig, ab 70000)
- `Belegdatum` ← `invoice.invoice_date` (DDMM Format)
- `Belegfeld1` ← `invoice.invoice_number`
- `Buchungstext` ← `invoice.description[:60]` (max 60 Zeichen)

### Stammdaten.csv

Kreditoren-Stammdaten (Lieferanten):
```
Konto;Kontobeschriftung;Sprachkennung
70001;Muster GmbH;0
70002;Schmidt KG;0
```

---

## Datenfluss

```
User wählt Zeitraum (Von/Bis Monat)
  → GET /api/datev/export?from_month=2024-01&to_month=2024-12
  → Auth: JWT Bearer, _resolve_org_id()
  → Query: invoices WHERE org_id=X AND skr03_account IS NOT NULL AND invoice_date BETWEEN ...
  → datev_formatter.format_buchungsstapel(invoices, org.settings)
  → datev_formatter.format_stammdaten(contacts_from_invoices)
  → zipfile.ZipFile in memory → BytesIO
  → StreamingResponse(content=zip_bytes, media_type="application/zip")
  → Browser speichert als "DATEV_2024-01_2024-12.zip"
```

---

## Test-Coverage (neue Datei `tests/test_datev_export.py`)

| Test | Was wird geprüft |
|---|---|
| `test_extf_header_contains_berater_nr` | EXTF-Zeile 1 enthält konfigurierte Beraternummer |
| `test_export_excludes_uncategorized` | Rechnungen ohne skr03_account fehlen im Export |
| `test_zip_contains_two_files` | ZIP enthält genau 2 Dateien |
| `test_decimal_comma_formatting` | 1190.00 → "1190,00" in CSV |
| `test_send_email_attaches_zip` | E-Mail-Endpoint sendet ZIP als Anhang |
| `test_export_empty_period_returns_error` | 400 wenn keine kategorisierten Rechnungen im Zeitraum |

---

## Task-Übersicht (für Implementation Plan)

| # | Task | Dateien |
|---|---|---|
| 1 | DATEV Formatter (pure functions, TDD) | `datev_formatter.py` + Tests |
| 2 | Organization Settings: DATEV-Felder + Migration | `models.py`, `alembic/phase10_datev_settings.py` |
| 3 | DATEV Router: Export-Endpoint | `routers/datev.py` + Tests |
| 4 | DATEV Router: Send-Email-Endpoint | `routers/datev.py` erweitern |
| 5 | Backend-Registration + Org Settings API | `main.py`, `routers/organizations.py` |
| 6 | Frontend Settings: DATEV-Konfiguration-Sektion | `app/(dashboard)/settings/page.tsx` |
| 7 | Frontend Berichte: Export-UI + Wizard | `app/(dashboard)/berichte/page.tsx` |
| 8 | Final Verification + Changelog v1.0.0 + Merge | Changelog, Tests, Merge |

# RechnungsWerk — Backlog & Roadmap

Stand: 2026-03-04

---

## Prio HOCH

### Gutschriften / Stornos
Negativ-Rechnungen, gesetzlich noetig fuer Korrekturen. Verknuepfung mit Original-Rechnung, korrekte Nummernkreise.

### Lieferscheine
Standard-Feature bei allen Wettbewerbern. Eigenes Dokumentenmodell mit Bezug zu Rechnungen/Angeboten.

### KI-Strategie
Welche Modelle (Claude, Mistral, Ollama), Kosten, Architektur. Intelligente Belegerfassung, automatische Kategorisierung, Vorschlaege.

### Alembic-Migration
`create_all()` durch Alembic ersetzen fuer PostgreSQL-Produktion. Versionierte Schema-Migrationen.

### Deployment-Guide
Hetzner + Coolify Setup, SSL, DNS fuer Subdomains. Docker-Compose fuer Self-Hosting.

---

## Prio MITTEL

### Bankanbindung (FinTS/HBCI)
Automatischer Zahlungsabgleich. Offene Rechnungen mit Banktransaktionen matchen.

### Belegerfassung per Foto
Mobile Kamera → OCR. PWA-Integration mit Kamera-API.

### Multi-Waehrung
USD, CHF, GBP Support. Wechselkurse, Umrechnung, Ausweisung in Berichten.

### E-Mail-Integration
Automatischer Rechnungsversand per SMTP. Templates, Tracking, Zustellstatus.

---

## Prio NIEDRIG

### Buchhaltung (EUeR/GuV)
Grundlegende Buchhaltungsfunktionen. SKR03/SKR04 Kontenrahmen.

### Lohnabrechnung
Integration oder Verweis auf Drittanbieter (DATEV, Lexware).

### White-Label
Kunden koennen eigenes Branding nutzen. Custom Domain, Logo, Farben.

### Plugin-System
Erweiterbarkeit durch Drittanbieter-Plugins. API-basiert.

---

## Wettbewerbs-Vorteile (beibehalten!)

| Feature | sevdesk | lexoffice | easybill | Billomat | RechnungsWerk |
|---------|---------|-----------|----------|----------|---------------|
| Self-Hosting | - | - | - | - | Ja |
| Open Source | - | - | - | - | Ja |
| Kundenportal | - | Eingeschraenkt | - | - | Ja |
| API + Webhooks | Ja | Eingeschraenkt | Ja | Ja | Ja |
| PWA + Offline | - | - | - | - | Ja |
| AI-Chat | - | - | - | - | Ja |
| ZUGFeRD + XRechnung | Ja | Ja | Ja | Ja | Ja |

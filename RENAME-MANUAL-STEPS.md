# RechnungsKern — Manuelle Schritte nach dem Rename

## Erledigt (automatisch)
- [x] Alle Code-Dateien umbenannt (RechnungsKern → RechnungsKern)
- [x] Alle Domains aktualisiert (rechnungskern.de → rechnungskern.de)
- [x] Alle E-Mail-Adressen aktualisiert
- [x] Neue Logos eingebunden (stacked + horizontal)
- [x] Dark-Mode Logo-Varianten erstellt

## Manuelle Schritte (TODO)

### DNS & Hosting
- [ ] DNS-Einträge für rechnungskern.de konfigurieren
- [ ] SSL-Zertifikate für rechnungskern.de erstellen (Caddy macht das automatisch)
- [ ] Alte Domain rechnungskern.de als Redirect einrichten

### Datenbank
- [ ] PostgreSQL-Datenbank umbenennen: `ALTER DATABASE rechnungskern RENAME TO rechnungskern;`
- [ ] Oder: Neue DB erstellen und Daten migrieren

### Object Storage
- [ ] Hetzner Object Storage: S3-Bucket "rechnungskern-files" → "rechnungskern-files" umbenennen (oder neuen Bucket erstellen und Dateien kopieren)

### E-Mail
- [ ] Mailserver/Provider: E-Mail-Adressen @rechnungskern.de einrichten
  - noreply@rechnungskern.de
  - contact@rechnungskern.de
  - datenschutz@rechnungskern.de

### GitHub
- [ ] Repository umbenennen: github.com/sadanakb/rechnungswerk → rechnungskern
- [ ] GitHub URLs im Code nach Repo-Umbenennung aktualisieren

### Externe Dienste
- [ ] Stripe: Webhook-URLs aktualisieren auf api.rechnungskern.de
- [ ] Peppol: Registrierung auf neuen Domainnamen aktualisieren
- [ ] Push-Notification Service: URLs aktualisieren

### PWA & App Stores
- [ ] PWA-Icons neu generieren (`cd frontend && python scripts/generate-icons.py`)
- [ ] Falls in App Stores gelistet: Name und URLs aktualisieren

### Monitoring & Analytics
- [ ] Sentry/Error-Tracking: Projekt umbenennen
- [ ] Analytics: Neue Domain tracken

### Rechtliches
- [ ] Impressum auf rechnungskern.de verifizieren
- [ ] Datenschutzerklärung mit neuer Domain prüfen
- [ ] AGB mit neuem Produktnamen prüfen

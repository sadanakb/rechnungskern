# Checkpoint — 2026-03-02 15:20

## Ziel
Phase 15: Security Audit Follow-Up — 13 Findings aus priorisierter Audit-Liste abarbeiten.

## Erledigt
- [x] #1 KRITISCH: Batch-Status-Endpoint Auth + Org-Check (Dateien: backend/app/routers/invoices.py, backend/app/ocr/batch_processor.py)
- [x] #2 KRITISCH: Frontend Batch-Polling URL-Fix /api/upload-ocr-batch → /api/batch (Dateien: frontend/lib/api.ts)
- [x] #3 HOCH: API-Key Scope-Enforcement mit require_scope() (Dateien: backend/app/auth_jwt.py, backend/app/routers/external_api.py)
- [x] #4 HOCH: IMAP SSRF-Schutz — Host-Validierung, Port-Restrict, Audit-Log, User-scoped Cache (Dateien: backend/app/routers/email.py)
- [x] #5 HOCH: Team-Invite-Token Persistenz — TeamInvite Model, SHA256-Hash, 7-Tage-Expiry, Accept-Endpoint (Dateien: backend/app/models.py, backend/app/routers/teams.py, backend/alembic/versions/phase13_team_invites.py)
- [x] #6 HOCH: SVG-Upload entfernt, Magic-Byte-Validierung, Extension aus Content-Type (Dateien: backend/app/routers/onboarding.py)
- [x] #7 MITTEL: Portal-PDF Path-Traversal-Schutz mit realpath + Base-Dir-Check (Dateien: backend/app/routers/portal.py)
- [x] #8 MITTEL: GDPR Token-Expiry (24h) + Query-String Deprecation-Warning (Dateien: backend/app/routers/gdpr.py)
- [x] #9 MITTEL: Contact-Form Input-Laengen-Limits + EmailStr (Dateien: backend/app/routers/contact.py)
- [x] #10 MITTEL: AI-Chat Rate-Limit 20/min, Categorize 30/min, Summary 10/min (Dateien: backend/app/routers/ai.py)
- [x] #11 MITTEL: ESLint Flat-Config Migration (eslint.config.mjs) — 0 Errors, 15 Warnings (Dateien: frontend/eslint.config.mjs, frontend/package.json)
- [x] #12 MITTEL: E2E settings.spec.ts Locator getByRole('heading') (Dateien: frontend/e2e/settings.spec.ts)
- [x] #13 NIEDRIG-MITTEL: Legacy auth.py → _auth_legacy.py, Imports aktualisiert (Dateien: backend/app/_auth_legacy.py, backend/app/main.py, 3 Test-Dateien)
- [x] Email-Test-Fix: _validate_imap_host Mock in 5 Tests (Dateien: backend/tests/test_email_router.py)

## Offen
- [ ] Full Backend Test Suite Ergebnis abwarten (laeuft gerade)
- [ ] Git Commit erstellen

## Entscheidungen
- Batch-Status: org_id auf BatchJob gespeichert, Legacy-Jobs ohne org_id werden toleriert
- API-Key Scopes: Leere Scopes = alles erlaubt (Backward-Compat), non-empty = enforced
- IMAP SSRF: socket.getaddrinfo + ipaddress-Check blockt Private/Reserved/Loopback/Link-Local
- Team-Invite: SHA256-Hash in DB, 7-Tage-Expiry, Single-Use, Accept braucht JWT
- SVG komplett entfernt: Nur PNG/JPEG/WebP mit Magic-Byte-Validierung
- Portal PDF: os.path.realpath + startswith(ZUGFERD_BASE) gegen Path-Traversal
- Legacy auth.py: Umbenannt statt geloescht (Tests nutzen es noch)

## Build/Test-Status
- Frontend Tests: 77/77 passed
- ESLint: 0 errors, 15 warnings
- Email Tests: 10/10 passed
- Legacy-Import Tests: 24/24 passed
- Full Backend Suite: Laeuft (Task bw28zh766)
- Letzter Commit: 17be2ae security(phase14)

## Naechster Schritt
1. Full Backend Test Suite Ergebnis abwarten
2. git add + git commit -m "security(phase15): audit follow-up — 13 findings fixed"
3. Optional: Frontend Build pruefen

# Checkpoint — 2026-03-07

## Ziel
Execute Task 1 (Preisseite bereinigen) + Task 2 (Feature-Gating vervollstaendigen) from the launch-blocker plan.

## Erledigt
- [x] Task 1: Preisseite bereinigt — Banking-Integration und UStVA-Voranmeldung als "(geplant)" markiert und included:false gesetzt (Datei: frontend/app/(marketing)/preise/page.tsx)
- [x] Task 2a: DATEV-Export gated mit require_feature("datev_export") auf beide Endpoints (Datei: backend/app/routers/datev.py)
- [x] Task 2b: API-Keys gated mit require_feature("api_access") auf alle 3 Endpoints (Datei: backend/app/routers/api_keys.py)
- [x] Task 2c: Kontakt-Limit (max 10 fuer Free) implementiert mit check_plan_limit() (Datei: backend/app/routers/contacts.py)
- [x] Task 2d: Rechnungs-Limit (max 5/Monat fuer Free) implementiert mit check_plan_limit() (Datei: backend/app/routers/invoices.py)
- [x] check_plan_limit() Hilfsfunktion in feature_gate.py hinzugefuegt (Datei: backend/app/feature_gate.py)
- [x] 8 neue Tests geschrieben und bestanden (Datei: backend/tests/test_feature_gate_enforcement.py)
- [x] Frontend Build erfolgreich
- [x] 46 Tests bestanden (alle relevanten Testdateien)

## Offen
- [ ] Commit erstellen
- [ ] Optional: recurring.py und webhooks.py gaten (api_access feature?)

## Entscheidungen
- Banking-Integration und UStVA-Voranmeldung als "(geplant)" + included:false statt komplett entfernt
- datev.py und api_keys.py: require_feature() als Depends ersetzt get_current_user (boolean gate)
- contacts.py und invoices.py: check_plan_limit() inline im Endpoint (count-based limit)
- recurring.py und webhooks.py nicht gegated — kein klares Feature-Flag

## Build/Test-Status
- Build: OK (Frontend + Backend)
- Tests: 46/46 bestanden (feature_gate, contacts, datev, api_keys, invoices_api)
- Letzter Commit: c5a8299

## Naechster Schritt
Commit erstellen

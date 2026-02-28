# Checkpoint — 2026-02-28 Phase 12 Complete

## Ziel
RechnungsWerk SaaS — Phase 12: Kunden-Portal Online-Zahlung

## Erledigt
- [x] Phase 1: Core Invoice CRUD + XRechnung
- [x] Phase 2: AI Integration (OCR + Kategorisierung)
- [x] Phase 3: Multi-Tenancy + Organization Model
- [x] Phase 4: Abonnement + Stripe Billing
- [x] Phase 5: Enterprise Features (Webhooks, Audit Log, Templates)
- [x] Phase 6: ZUGFeRD + GOBD Export
- [x] Phase 7: CSV Import + Onboarding
- [x] Phase 8: ARQ Background Tasks + Kundenportal + E-Mail
- [x] Phase 9: AI Chat + WebSocket + Real-Time Notifications
- [x] Phase 10: DATEV Export + Steuerberater-Integration
- [x] Phase 11: Push Notifications (Firebase) + GDPR Controls
- [x] Phase 12: Kunden-Portal Online-Zahlung (Stripe Connect Express + PayPal)

## Offen
- [ ] Phase 13: (zu definieren)

## Entscheidungen
- PayPal via Stripe Connect nicht supported (manuelle Genehmigung nötig) → PayPal als simple paypal_link-URL
- Stripe Connect Express mit 0,5% Platform-Fee via application_fee_amount
- client_secret in DB gespeichert für Idempotenz

## Build/Test-Status
- Build: OK
- Tests: alle bestanden
- Letzter Commit: release v1.2.0

## Naechster Schritt
Phase 13 planen (User-Feedback abwarten)

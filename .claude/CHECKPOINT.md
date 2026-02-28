# Checkpoint — 2026-02-28 12:00

## Ziel
RechnungsWerk — production-ready German e-invoicing SaaS, alle Phasen 1-9 abgeschlossen.

## Erledigt
- [x] Phase 1: Marktreife (Multi-Tenant Auth, Landing Page, Stripe, PWA, MDX Blog)
- [x] Phase 2: Features + SEO (Mahnwesen, Cmd+K, TanStack Table, pSEO 10 Branchen × 16 Bundesländer)
- [x] Phase 3: Launch-Readiness (Error Boundaries, Security Headers, Alembic, Feature Gating, Glossar)
- [x] Phase 4: Completeness & Polish (Profil, Passwort-Reset, E-Mail-Verifizierung, Stripe Billing, Teams)
- [x] Phase 5: Integrations & Growth (Webhooks, API-Keys, Audit-Log, Templates, Bulk-Ops, Reports, CI/CD)
- [x] Phase 6: UX Hardening (Invoice Detail, ZUGFeRD Export, Notifications, Onboarding, PWA, Print, Filter)
- [x] Phase 7: Business Logic (Payment Status, Contacts, Sequences, Rate Limiting, CSV Import, Stats, Overdue)
- [x] Phase 8: Production Excellence + Kundenportal (ARQ, Webhook Retry, S3 Storage, Share Links, Portal, Email)
- [x] Phase 9: KI-Suite + Echtzeit (GPT-4o-mini, WebSocket, Chat-Assistent, SKR03-Kategorisierung, Monatszusammenfassung)

## Entscheidungen
- Auth: get_current_user returns dict; _resolve_org_id() via OrganizationMember join
- Route-Ordering: Named routes vor /{invoice_id} (autocomplete, stats, check-overdue, bulk-delete, share-link, send-email)
- Rate Limiter: conftest.py autouse Fixture reset_rate_limiter() — limiter._storage.reset() zwischen Tests
- CSS: rgb(var(--primary)) usw. — nie hardcoded Colors im Dashboard
- ARQ: Graceful degradation — arq_pool = None wenn Redis nicht verfügbar, sync fallback
- Portal: /portal/[token] outside route groups — standalone public page ohne Dashboard-Layout
- Storage: STORAGE_BACKEND=local (default) or s3, konfigurierbar via ENV
- KI: GPT-4o-mini Primary (Standard), Claude Haiku (Complex/Chat), Ollama (Dev-Fallback)
- WebSocket: /ws?token=<jwt>, ConnectionManager Singleton in app/ws.py, notify_org helper
- Chat: Streaming SSE via StreamingResponse(media_type="text/event-stream"), Tool Use für DB-Queries
- SKR03: Async ARQ-Task categorize_invoice_task nach Invoice-Save, WS-Event invoice.categorized
- Summary: Redis-Cache 24h, strftime("%Y-%m") für SQLite Datumsfilterung

## Build/Test-Status
- Backend: 436 Tests bestanden, 0 Fehler
- Frontend: 114 Seiten gebaut, 0 TypeScript-Fehler
- Master: latest — Phase 9 gemergt (feat: merge Phase 9 — KI-Suite + Echtzeit)

## Neue Dateien Phase 9
- backend/app/ws.py — ConnectionManager, notify_org
- backend/app/routers/ai.py — POST /categorize, GET /monthly-summary, POST /chat (SSE)
- backend/alembic/versions/phase9_ai_columns.py — skr03_account, ai_category, ai_categorized_at
- frontend/contexts/WebSocketContext.tsx — WebSocketProvider, useWebSocket, Sonner toasts
- frontend/components/ai/ChatWidget.tsx — floating chat widget, SSE streaming

## Naechster Schritt
Phase 10 planen falls gewünscht. Mögliche Themen:
- DATEV-Export (komplexe Buchhaltungsintegration)
- Mobile Push Notifications
- Advanced Analytics (Prognosen, Trends, ML)
- Mehrsprachigkeit (EN/DE)

# Phase 12: Kunden-Portal Online-Zahlung — Design

**Datum:** 2026-02-28
**Status:** Approved

---

## Ziel

Rechnungsempfänger können Rechnungen direkt im Kunden-Portal online bezahlen — per Kreditkarte, SEPA-Lastschrift, Sofort oder iDEAL. RechnungsKern erhebt automatisch eine Platform-Fee von 0,5 % über Stripe Connect Express. PayPal wird als einfacher Link-Button unterstützt (kein Platform-Cut).

---

## Architektur

```
RechnungsKern (Stripe Platform Account)
    │
    ├── Org (Stripe Connect Express Account)
    │       │
    │       └── Invoice → Portal Token → Kunde zahlt
    │               └── PaymentIntent (application_fee: 0,5%)
    │                       └── webhook: payment_intent.succeeded
    │                               └── invoice.payment_status = "paid"
    │                               └── WS notify + Push
    │
    └── PayPal → eigene paypal.me URL der Org → Button im Portal
```

### Datenfluss

1. **Einmalig (Org-Setup):** Settings → Tab "Zahlungen" → "Mit Stripe verbinden" → Stripe-hosted Express-Onboarding (~10 Min) → `stripe_connect_account_id` + `stripe_connect_onboarded=True` gespeichert
2. **Pro Zahlung:** Kunde öffnet Portal → "Online bezahlen" → `POST /api/portal/{token}/create-payment-intent` → Backend erstellt PaymentIntent auf Connected Account → Stripe Payment Element → Zahlung → Webhook → Invoice als paid + Notifications

---

## Datenmodell

### Erweiterungen `organizations`

```python
stripe_connect_account_id  String(255)  # "acct_xxx", nullable
stripe_connect_onboarded   Boolean      # default False
paypal_link                String(255)  # "https://paypal.me/...", nullable
```

### Neue Tabelle `portal_payment_intents`

```python
id                 Integer, PK
invoice_id         FK → invoices.id
share_link_id      FK → invoice_share_links.id
stripe_intent_id   String(255), unique   # "pi_xxx"
amount_cents       Integer               # Bruttobetrag in Cent
fee_cents          Integer               # 0,5% Platform-Fee
status             String(50)            # "created" | "succeeded" | "failed" | "canceled"
created_at         DateTime(tz)
updated_at         DateTime(tz)
```

---

## Backend-Endpoints

| Endpoint | Auth | Beschreibung |
|----------|------|-------------|
| `POST /api/billing/connect-onboard` | JWT | Erstellt Stripe Express Onboarding-URL |
| `GET /api/billing/connect-status` | JWT | `{onboarded: bool, account_id: str \| null}` |
| `POST /api/portal/{token}/create-payment-intent` | Token | Erstellt PaymentIntent, gibt `{client_secret, amount, currency}` |
| `GET /api/portal/{token}/payment-status` | Token | Polling: aktueller Zahlungsstatus der Rechnung |
| Webhook `payment_intent.succeeded` | Stripe-Sig | Invoice paid + WS + Push |

**Platform-Fee-Berechnung:**
```python
fee_cents = round(gross_amount_cents * 0.005)  # 0,5%
```

**Sicherheit `create-payment-intent`:**
- Token muss gültig und nicht abgelaufen sein
- Rechnung muss `payment_status in ("unpaid", "overdue")` sein
- Org muss `stripe_connect_onboarded=True` sein
- Idempotenz: Vorhandenes "created"-Intent wird zurückgegeben statt neuem

---

## Frontend

### Settings-Seite — Tab "Zahlungen"
- Status-Card: "Stripe verbunden ✓" / "Nicht verbunden"
- Button: "Mit Stripe verbinden" → `POST /api/billing/connect-onboard` → redirect
- PayPal-Link-Feld (optional, Freitext)

### Portal-Seite — Erweiterungen
- Wenn `stripe_connect_onboarded`: "Online bezahlen"-Button (prominent, primär)
- Klick → modale Stripe Payment Element Overlay
- Nach Zahlung: Erfolgs-Screen
- Wenn `paypal_link` vorhanden: "Per PayPal zahlen"-Button (sekundär, externer Link)
- Bestehender "Zahlung bestätigen" (manuell) bleibt als Fallback

### Dependencies
- `@stripe/stripe-js`
- `@stripe/react-stripe-js`

---

## Fehlerbehandlung

| Szenario | Verhalten |
|----------|-----------|
| Org nicht onboarded | "Online bezahlen"-Button unsichtbar, nur manuell + PayPal |
| Rechnung bereits bezahlt | `create-payment-intent` → 409, Portal zeigt Bezahlt-Status |
| Stripe-Fehler | Portal zeigt Fehlermeldung, kein Intent gespeichert |
| Webhook doppelt | Idempotenz via `stripe_intent_id UNIQUE` |

---

## Testing

- Backend: pytest mit Stripe-Mock (`stripe.PaymentIntent.create` gepatcht)
- Frontend: MSW für API-Mocks, kein echter Stripe-Aufruf in Tests
- Integration: Stripe Test Mode (`sk_test_...`) für manuelle E2E-Tests

---

## Nicht in Scope

- Teilzahlungen / Ratenzahlung
- PayPal Commerce Platform (Approval-Pflicht, kein Platform-Cut)
- Rückerstattungen via Portal (Phase 13)
- Stripe Connect für PayPal (manuelle Genehmigung nötig, nicht Phase 12)

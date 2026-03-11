'use client'

import React from 'react'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface InvoicePreviewProps {
  // Verkäufer
  sellerName?: string
  sellerAddress?: string
  sellerVatId?: string
  sellerEndpointId?: string
  // Käufer
  buyerName?: string
  buyerAddress?: string
  buyerVatId?: string
  buyerReference?: string
  // Rechnung
  invoiceNumber?: string
  invoiceDate?: string
  dueDate?: string
  currency?: string
  // Positionen
  lineItems?: Array<{
    description: string
    quantity: number
    unitPrice: number
    netAmount: number
  }>
  // Summen
  netAmount?: number
  taxRate?: number
  taxAmount?: number
  grossAmount?: number
  // Zahlung
  iban?: string
  bic?: string
  paymentAccountName?: string
  paymentTerms?: string
  // Logo
  logoUrl?: string | null
  // Anzeige
  scale?: number
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtCurrency(value: number | undefined, currency: string): string {
  if (value == null) return '0,00\u00a0€'
  return value.toLocaleString('de-DE', { style: 'currency', currency })
}

function fmtDate(dateStr: string | undefined): string {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function todayFormatted(): string {
  return new Date().toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function InvoicePreview(props: InvoicePreviewProps) {
  const {
    sellerName,
    sellerAddress,
    sellerVatId,
    buyerName,
    buyerAddress,
    buyerVatId,
    buyerReference,
    invoiceNumber,
    invoiceDate,
    dueDate,
    currency = 'EUR',
    lineItems,
    netAmount,
    taxRate = 19,
    taxAmount,
    grossAmount,
    iban,
    bic,
    paymentAccountName,
    logoUrl,
  } = props

  const scale = props.scale ?? 0.6
  const A4_WIDTH = 794 // px at 96 dpi

  const hasItems = lineItems && lineItems.length > 0
  const displayItems = hasItems ? lineItems : null

  const placeholderColor = '#d6d3d1' // stone-300

  return (
    <div style={{ width: A4_WIDTH * scale, overflow: 'hidden', flexShrink: 0 }}>
      <div
        style={{
          width: A4_WIDTH,
          transformOrigin: 'top left',
          transform: `scale(${scale})`,
          backgroundColor: 'white',
          border: '1px solid #e7e5e4',
          fontFamily: 'sans-serif',
          minHeight: 400,
        }}
      >
        {/* ===== Header ===== */}
        <div
          style={{
            padding: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
          }}
        >
          {/* Left: logo + seller name */}
          <div>
            {logoUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={logoUrl}
                alt="Logo"
                style={{ maxHeight: 48, maxWidth: 160, display: 'block', marginBottom: 6 }}
              />
            ) : null}
            {sellerName ? (
              <div style={{ fontSize: 18, fontWeight: 700, color: '#292524' }}>
                {sellerName}
              </div>
            ) : (
              <div style={{ fontSize: 18, fontWeight: 700, color: placeholderColor }}>
                Firmenname
              </div>
            )}
          </div>

          {/* Right: RECHNUNG + invoice info */}
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#4d7c0f', lineHeight: 1 }}>
              RECHNUNG
            </div>
            <div
              style={{
                fontSize: 13,
                marginTop: 8,
                color: invoiceNumber ? '#374151' : placeholderColor,
              }}
            >
              {invoiceNumber || 'RK-2024-001'}
            </div>
            <div
              style={{
                fontSize: 12,
                marginTop: 2,
                color: invoiceDate ? '#6b7280' : placeholderColor,
              }}
            >
              {invoiceDate ? fmtDate(invoiceDate) : todayFormatted()}
            </div>
            {dueDate && (
              <div style={{ fontSize: 12, marginTop: 2, color: '#6b7280' }}>
                Fällig: {fmtDate(dueDate)}
              </div>
            )}
          </div>
        </div>

        {/* ===== Parties ===== */}
        <div
          style={{
            backgroundColor: '#fafaf9',
            padding: '16px 24px',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 24,
          }}
        >
          {/* Von */}
          <div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: '#78716c',
                marginBottom: 6,
              }}
            >
              Von:
            </div>
            {sellerName ? (
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1c1917', marginBottom: 2 }}>
                {sellerName}
              </div>
            ) : (
              <div style={{ fontSize: 13, fontWeight: 600, color: placeholderColor, marginBottom: 2 }}>
                Firmenname GmbH
              </div>
            )}
            {sellerAddress ? (
              <div style={{ fontSize: 12, color: '#44403c', whiteSpace: 'pre-line', lineHeight: 1.5 }}>
                {sellerAddress}
              </div>
            ) : (
              <div style={{ fontSize: 12, color: placeholderColor, lineHeight: 1.5 }}>
                Musterstraße 1{'\n'}12345 Musterstadt
              </div>
            )}
            {sellerVatId && (
              <div style={{ fontSize: 11, color: '#78716c', marginTop: 3 }}>
                USt-IdNr.: {sellerVatId}
              </div>
            )}
          </div>

          {/* An */}
          <div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: '#78716c',
                marginBottom: 6,
              }}
            >
              An:
            </div>
            {buyerName ? (
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1c1917', marginBottom: 2 }}>
                {buyerName}
              </div>
            ) : (
              <div style={{ fontSize: 13, fontWeight: 600, color: placeholderColor, marginBottom: 2 }}>
                Kundenname AG
              </div>
            )}
            {buyerAddress ? (
              <div style={{ fontSize: 12, color: '#44403c', whiteSpace: 'pre-line', lineHeight: 1.5 }}>
                {buyerAddress}
              </div>
            ) : (
              <div style={{ fontSize: 12, color: placeholderColor, lineHeight: 1.5 }}>
                Kundenstraße 5{'\n'}10115 Berlin
              </div>
            )}
            {buyerVatId && (
              <div style={{ fontSize: 11, color: '#78716c', marginTop: 3 }}>
                USt-IdNr.: {buyerVatId}
              </div>
            )}
            {buyerReference && (
              <div style={{ fontSize: 11, color: '#78716c', marginTop: 2 }}>
                Leitweg-ID: {buyerReference}
              </div>
            )}
          </div>
        </div>

        {/* ===== Line items table ===== */}
        <div style={{ padding: '0 24px', marginTop: 16 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ backgroundColor: '#4d7c0f', color: '#ffffff' }}>
                <th
                  style={{
                    padding: '8px 10px',
                    textAlign: 'left',
                    fontWeight: 600,
                    fontSize: 11,
                    width: 36,
                  }}
                >
                  Pos.
                </th>
                <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, fontSize: 11 }}>
                  Beschreibung
                </th>
                <th
                  style={{
                    padding: '8px 10px',
                    textAlign: 'right',
                    fontWeight: 600,
                    fontSize: 11,
                    width: 60,
                  }}
                >
                  Menge
                </th>
                <th
                  style={{
                    padding: '8px 10px',
                    textAlign: 'right',
                    fontWeight: 600,
                    fontSize: 11,
                    width: 90,
                  }}
                >
                  Einzelpreis
                </th>
                <th
                  style={{
                    padding: '8px 10px',
                    textAlign: 'right',
                    fontWeight: 600,
                    fontSize: 11,
                    width: 90,
                  }}
                >
                  Betrag
                </th>
              </tr>
            </thead>
            <tbody>
              {displayItems ? (
                displayItems.map((item, idx) => (
                  <tr
                    key={idx}
                    style={{ backgroundColor: idx % 2 === 1 ? '#fafaf9' : '#ffffff' }}
                  >
                    <td
                      style={{
                        padding: '7px 10px',
                        color: '#a8a29e',
                        fontFamily: 'monospace',
                        fontSize: 11,
                      }}
                    >
                      {idx + 1}
                    </td>
                    <td style={{ padding: '7px 10px', color: '#1c1917' }}>
                      {item.description}
                    </td>
                    <td style={{ padding: '7px 10px', textAlign: 'right', color: '#44403c' }}>
                      {item.quantity != null
                        ? item.quantity.toLocaleString('de-DE', { maximumFractionDigits: 4 })
                        : '—'}
                    </td>
                    <td style={{ padding: '7px 10px', textAlign: 'right', color: '#44403c' }}>
                      {fmtCurrency(item.unitPrice, currency)}
                    </td>
                    <td style={{ padding: '7px 10px', textAlign: 'right', color: '#1c1917', fontWeight: 500 }}>
                      {fmtCurrency(item.netAmount, currency)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr style={{ backgroundColor: '#ffffff' }}>
                  <td style={{ padding: '7px 10px', color: placeholderColor, fontSize: 11 }}>1</td>
                  <td style={{ padding: '7px 10px', color: placeholderColor }}>Beispielleistung</td>
                  <td style={{ padding: '7px 10px', textAlign: 'right', color: placeholderColor }}>1</td>
                  <td style={{ padding: '7px 10px', textAlign: 'right', color: placeholderColor }}>
                    100,00&nbsp;€
                  </td>
                  <td style={{ padding: '7px 10px', textAlign: 'right', color: placeholderColor }}>
                    100,00&nbsp;€
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* ===== Totals ===== */}
        <div
          style={{
            padding: '16px 24px',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <div style={{ width: 240, fontSize: 13 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '4px 0',
                color: '#44403c',
              }}
            >
              <span>Nettobetrag:</span>
              <span>{fmtCurrency(netAmount, currency)}</span>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '4px 0',
                color: '#44403c',
              }}
            >
              <span>MwSt. ({taxRate}%):</span>
              <span>{fmtCurrency(taxAmount, currency)}</span>
            </div>
            <div
              style={{
                borderTop: '2px solid #4d7c0f',
                marginTop: 4,
                paddingTop: 6,
                display: 'flex',
                justifyContent: 'space-between',
                fontWeight: 700,
                fontSize: 15,
                color: '#1c1917',
              }}
            >
              <span>Gesamtbetrag:</span>
              <span>{fmtCurrency(grossAmount, currency)}</span>
            </div>
          </div>
        </div>

        {/* ===== Payment info ===== */}
        <div
          style={{
            backgroundColor: '#f7fee7',
            padding: '16px 24px',
            marginTop: 16,
          }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: '#3f3f46',
              marginBottom: 8,
            }}
          >
            Zahlungsinformationen
          </div>
          {iban || bic || paymentAccountName ? (
            <>
              {paymentAccountName && (
                <div style={{ fontSize: 12, color: '#44403c', marginBottom: 2 }}>
                  Kontoinhaber: {paymentAccountName}
                </div>
              )}
              {iban && (
                <div style={{ fontSize: 12, color: '#44403c', marginBottom: 2, fontFamily: 'monospace' }}>
                  IBAN: {iban}
                </div>
              )}
              {bic && (
                <div style={{ fontSize: 12, color: '#44403c', fontFamily: 'monospace' }}>
                  BIC: {bic}
                </div>
              )}
            </>
          ) : (
            <>
              <div style={{ fontSize: 12, color: placeholderColor, marginBottom: 2 }}>
                Kontoinhaber: Musterfirma GmbH
              </div>
              <div style={{ fontSize: 12, color: placeholderColor, marginBottom: 2, fontFamily: 'monospace' }}>
                IBAN: DE89 3704 0044 0532 0130 00
              </div>
              <div style={{ fontSize: 12, color: placeholderColor, fontFamily: 'monospace' }}>
                BIC: COBADEFFXXX
              </div>
            </>
          )}
        </div>

        {/* ===== Footer ===== */}
        <div
          style={{
            textAlign: 'center',
            padding: '12px 24px',
            fontSize: 10,
            color: '#a8a29e',
          }}
        >
          Erstellt mit RechnungsKern
        </div>
      </div>
    </div>
  )
}

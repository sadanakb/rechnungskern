"""
Quote (Angebot) PDF Generator — Generates a professional PDF for quotes.

Uses weasyprint for HTML-to-PDF conversion, same pattern as zugferd_generator.
No XML embedding (quotes don't need ZUGFeRD/XRechnung compliance).
"""
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


_QUOTE_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; color: #1a1a2e; line-height: 1.5; }}
  .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
  .brand {{ font-size: 18pt; font-weight: bold; color: #0d9488; }}
  .meta {{ text-align: right; font-size: 9pt; color: #64748b; }}
  .parties {{ display: flex; gap: 40px; margin-bottom: 25px; }}
  .party {{ flex: 1; }}
  .party h3 {{ font-size: 8pt; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; margin-bottom: 5px; }}
  .party p {{ margin: 2px 0; }}
  .quote-info {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; margin-bottom: 25px; }}
  .quote-info table {{ width: 100%; }}
  .quote-info td {{ padding: 3px 10px; }}
  .quote-info td:first-child {{ font-weight: 600; color: #334155; width: 180px; }}
  .intro-text {{ margin-bottom: 20px; padding: 10px; background: #f0fdfa; border-left: 3px solid #0d9488; }}
  table.items {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; }}
  table.items th {{ background: #0d9488; color: white; padding: 8px 12px; text-align: left; font-size: 8pt; text-transform: uppercase; letter-spacing: 0.5px; }}
  table.items th:last-child, table.items td:last-child {{ text-align: right; }}
  table.items td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; }}
  table.items tr:nth-child(even) {{ background: #f8fafc; }}
  .totals {{ float: right; width: 250px; }}
  .totals table {{ width: 100%; }}
  .totals td {{ padding: 4px 8px; }}
  .totals td:last-child {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .totals tr.total {{ font-weight: bold; font-size: 12pt; border-top: 2px solid #0d9488; }}
  .closing-text {{ clear: both; margin-top: 40px; padding: 10px; background: #f0fdfa; border-left: 3px solid #0d9488; }}
  .payment {{ clear: both; margin-top: 20px; padding: 15px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; }}
  .payment h3 {{ font-size: 9pt; color: #047857; margin-bottom: 5px; }}
  .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 8pt; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="brand">ANGEBOT</div>
    </div>
    <div class="meta">
      <strong>{quote_number}</strong><br>
      Datum: {quote_date}<br>
      {valid_until_line}
    </div>
  </div>

  <div class="parties">
    <div class="party">
      <h3>Anbieter</h3>
      <p><strong>{seller_name}</strong></p>
      <p>{seller_address_html}</p>
      {seller_vat_line}
    </div>
    <div class="party">
      <h3>Empfaenger</h3>
      <p><strong>{buyer_name}</strong></p>
      <p>{buyer_address_html}</p>
      {buyer_vat_line}
    </div>
  </div>

  {intro_text_html}

  <table class="items">
    <thead>
      <tr>
        <th>Pos.</th>
        <th>Beschreibung</th>
        <th>Menge</th>
        <th>Einzelpreis</th>
        <th>Netto</th>
      </tr>
    </thead>
    <tbody>
      {line_items_html}
    </tbody>
  </table>

  <div class="totals">
    <table>
      <tr><td>Nettobetrag</td><td>{net_amount} {currency}</td></tr>
      <tr><td>MwSt {tax_rate}%</td><td>{tax_amount} {currency}</td></tr>
      <tr class="total"><td>Gesamtbetrag</td><td>{gross_amount} {currency}</td></tr>
    </table>
  </div>

  {closing_text_html}

  {payment_html}

  <div class="footer">
    Erstellt mit RechnungsWerk &middot; Dieses Angebot ist freibleibend.
  </div>
</body>
</html>
"""


def generate_quote_pdf(quote_data: Dict, output_path: str) -> str:
    """
    Generate a PDF for a quote (Angebot).

    Args:
        quote_data: Quote field dictionary
        output_path: Where to save the PDF

    Returns:
        Path to generated PDF file
    """
    html = _render_quote_html(quote_data)
    pdf_bytes = _html_to_pdf(html)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    logger.info("Quote PDF generated: %s", output_path)
    return output_path


def _render_quote_html(data: Dict) -> str:
    """Render quote data to HTML template."""
    currency = data.get("currency", "EUR")

    # Line items HTML
    line_items = data.get("line_items") or []
    items_html = ""
    for i, item in enumerate(line_items, 1):
        qty = item.get("quantity", 1)
        price = item.get("unit_price", 0)
        net = item.get("net_amount", float(qty) * float(price))
        items_html += (
            f'<tr><td>{i}</td>'
            f'<td>{item.get("description", "Leistung")}</td>'
            f'<td>{qty}</td>'
            f'<td>{float(price):.2f} {currency}</td>'
            f'<td>{float(net):.2f} {currency}</td></tr>\n'
        )

    if not items_html:
        items_html = (
            f'<tr><td>1</td><td>Leistung</td><td>1</td>'
            f'<td>{float(data.get("net_amount", 0)):.2f} {currency}</td>'
            f'<td>{float(data.get("net_amount", 0)):.2f} {currency}</td></tr>'
        )

    # Valid until date
    valid_until = data.get("valid_until")
    valid_until_line = f"Gueltig bis: {valid_until}" if valid_until else ""

    # Seller VAT
    seller_vat = data.get("seller_vat_id")
    seller_vat_line = f"<p>USt-IdNr.: {seller_vat}</p>" if seller_vat else ""

    # Buyer VAT
    buyer_vat = data.get("buyer_vat_id")
    buyer_vat_line = f"<p>USt-IdNr.: {buyer_vat}</p>" if buyer_vat else ""

    # Intro text
    intro_text = data.get("intro_text")
    intro_text_html = f'<div class="intro-text">{intro_text}</div>' if intro_text else ""

    # Closing text
    closing_text = data.get("closing_text")
    closing_text_html = f'<div class="closing-text">{closing_text}</div>' if closing_text else ""

    # Payment
    iban = data.get("iban")
    payment_html = ""
    if iban:
        bic = data.get("bic", "")
        account_name = data.get("payment_account_name", "")
        payment_html = f"""
        <div class="payment">
          <h3>Zahlungsinformationen</h3>
          <p>IBAN: <strong>{iban}</strong></p>
          {"<p>BIC: " + bic + "</p>" if bic else ""}
          {"<p>Kontoinhaber: " + account_name + "</p>" if account_name else ""}
        </div>
        """

    # Addresses
    seller_addr = (data.get("seller_address") or "").replace("\n", "<br>")
    buyer_addr = (data.get("buyer_address") or "").replace("\n", "<br>")

    return _QUOTE_HTML_TEMPLATE.format(
        quote_number=data.get("quote_number", ""),
        quote_date=data.get("quote_date", ""),
        valid_until_line=valid_until_line,
        seller_name=data.get("seller_name", ""),
        seller_address_html=seller_addr,
        seller_vat_line=seller_vat_line,
        buyer_name=data.get("buyer_name", ""),
        buyer_address_html=buyer_addr,
        buyer_vat_line=buyer_vat_line,
        intro_text_html=intro_text_html,
        line_items_html=items_html,
        net_amount=f'{float(data.get("net_amount", 0)):.2f}',
        tax_rate=data.get("tax_rate", 19),
        tax_amount=f'{float(data.get("tax_amount", 0)):.2f}',
        gross_amount=f'{float(data.get("gross_amount", 0)):.2f}',
        currency=currency,
        closing_text_html=closing_text_html,
        payment_html=payment_html,
    )


def _html_to_pdf(html: str) -> bytes:
    """Convert HTML to PDF bytes using weasyprint."""
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except ImportError:
        logger.error("weasyprint not installed — cannot generate quote PDF")
        raise ImportError(
            "weasyprint ist nicht installiert. "
            "Installieren mit: pip install weasyprint>=62.0"
        )

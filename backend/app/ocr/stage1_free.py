"""Stufe 1: Kostenlose Extraktion mit pdfplumber + Regex. Kein API-Call nötig."""
import pdfplumber
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# --- Text-Extraktion ---

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrahiere Text aus PDF mit pdfplumber. Synchron."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:5]:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        logger.warning("pdfplumber konnte PDF nicht lesen: %s", e)
    return text.strip()


def extract_tables_from_pdf(pdf_path: str) -> list[dict]:
    """Extrahiere Tabellen aus PDF — für Rechnungspositionen."""
    line_items = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:5]:
                tables = page.extract_tables() or []
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    # Erste Zeile als Header interpretieren
                    headers = [str(h).lower().strip() if h else "" for h in table[0]]
                    # Heuristik: Ist es eine Positionstabelle?
                    has_amount = any(k in h for h in headers for k in ['betrag', 'preis', 'amount', 'netto', 'summe', 'total', 'eur', '€'])
                    has_desc = any(k in h for h in headers for k in ['beschreibung', 'leistung', 'bezeichnung', 'description', 'position', 'artikel'])
                    if has_amount or has_desc:
                        for row in table[1:]:
                            if not row or all(c is None or str(c).strip() == "" for c in row):
                                continue
                            item = _parse_table_row(headers, row)
                            if item:
                                line_items.append(item)
    except Exception as e:
        logger.debug("Tabellen-Extraktion fehlgeschlagen: %s", e)
    return line_items


def _parse_table_row(headers: list[str], row: list) -> dict | None:
    """Versuche eine Tabellenzeile als Rechnungsposition zu parsen."""
    item = {}
    for i, header in enumerate(headers):
        if i >= len(row) or row[i] is None:
            continue
        val = str(row[i]).strip()
        if not val:
            continue
        if any(k in header for k in ['beschreibung', 'leistung', 'bezeichnung', 'description', 'position', 'artikel']):
            item['description'] = val
        elif any(k in header for k in ['menge', 'qty', 'quantity', 'anzahl', 'stk']):
            item['quantity'] = _try_parse_float(val) or 1
        elif any(k in header for k in ['einzelpreis', 'preis', 'unit', 'stückpreis', 'e-preis']):
            item['unit_price'] = parse_german_amount(val)
        elif any(k in header for k in ['betrag', 'netto', 'summe', 'gesamt', 'total', 'amount']):
            item['net_amount'] = parse_german_amount(val)
    if item.get('description') and (item.get('net_amount') or item.get('unit_price')):
        return item
    return None


def _try_parse_float(val: str) -> float | None:
    try:
        return float(val.replace(',', '.').replace(' ', ''))
    except (ValueError, TypeError):
        return None


# --- Regex-Patterns für deutsche Rechnungen ---

PATTERNS = {
    'invoice_number': [
        r'Rechnungsnr\.?\s*:?\s*(\S+)',
        r'Rechnungsnummer\s*:?\s*(\S+)',
        r'Invoice\s*(?:No|Nr|Number)\.?\s*:?\s*(\S+)',
        r'Re\.?\s*-?\s*Nr\.?\s*:?\s*(\S+)',
        r'Beleg-?Nr\.?\s*:?\s*(\S+)',
    ],
    'invoice_date': [
        r'Rechnungsdatum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        r'Datum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        r'Date\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        r'Ausstellungsdatum\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
    ],
    'due_date': [
        r'Fällig(?:keit)?\s*(?:am|bis)?\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        r'Zahlungsziel\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        r'Zahlbar\s*bis\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
    ],
    'seller_vat_id': [
        r'USt\.?-?Id\.?(?:\s*-?\s*Nr\.?)?\s*:?\s*(DE\s?\d{9})',
        r'Umsatzsteuer-?Identifikationsnummer\s*:?\s*(DE\s?\d{9})',
        r'VAT\s*(?:ID|No)\.?\s*:?\s*(DE\s?\d{9})',
    ],
    'seller_tax_number': [
        r'Steuernr?\.?\s*:?\s*(\d{2,3}[/ ]\d{3}[/ ]\d{4,5})',
        r'St\.?\s*-?\s*Nr\.?\s*:?\s*(\d{2,3}[/ ]\d{3}[/ ]\d{4,5})',
        r'Tax\s*No\.?\s*:?\s*(\d{2,3}[/ ]\d{3}[/ ]\d{4,5})',
    ],
    'iban': [
        r'IBAN\s*:?\s*(DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})',
        r'(DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})',
    ],
    'bic': [
        r'BIC\s*:?\s*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)',
        r'SWIFT\s*:?\s*([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)',
    ],
    'gross_amount': [
        r'Gesamtbetrag\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Bruttobetrag\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Rechnungsbetrag\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Endbetrag\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Total\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Zahlbetrag\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ],
    'net_amount': [
        r'Nettobetrag\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Netto\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Zwischensumme\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Subtotal\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ],
    'tax_amount': [
        r'MwSt\.?\s*(?:Betrag)?\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'USt\.?\s*(?:Betrag)?\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Umsatzsteuer\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Mehrwertsteuer\s*:?\s*€?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ],
    'tax_rate': [
        r'(\d{1,2})[,.]?\d*\s*%\s*(?:MwSt|USt|Umsatzsteuer|Mehrwertsteuer)',
        r'(?:MwSt|USt|Umsatzsteuer|Mehrwertsteuer)\s*(?:Satz)?\s*:?\s*(\d{1,2})[,.]?\d*\s*%',
    ],
    'buyer_reference': [
        r'Leitweg-?ID\s*:?\s*(\S+)',
        r'Buyer\s*Reference\s*:?\s*(\S+)',
        r'Bestellnummer\s*:?\s*(\S+)',
        r'Bestell-?Nr\.?\s*:?\s*(\S+)',
    ],
    'currency': [
        r'Währung\s*:?\s*(EUR|USD|CHF|GBP)',
        r'Currency\s*:?\s*(EUR|USD|CHF|GBP)',
    ],
}

# Mindestfelder damit Stufe 1 als ausreichend gilt
IMPORTANT_FIELDS = ['invoice_number', 'invoice_date', 'gross_amount', 'seller_vat_id', 'iban']
MIN_FIELDS_FOR_SUFFICIENT = 3


def parse_german_amount(amount_str: str) -> float | None:
    """Konvertiere deutschen Betrag zu float. '1.234,56' → 1234.56, '234,56' → 234.56"""
    if not amount_str:
        return None
    try:
        cleaned = amount_str.replace(' ', '').replace('€', '').replace('EUR', '').strip()
        if ',' in cleaned and '.' in cleaned:
            # 1.234,56 → 1234.56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # 234,56 → 234.56
            cleaned = cleaned.replace(',', '.')
        # else: 1234.56 bleibt
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        return None


def parse_german_date(date_str: str) -> str | None:
    """Konvertiere deutsches Datum zu ISO. '31.12.2026' → '2026-12-31'"""
    if not date_str:
        return None
    from datetime import datetime
    for fmt in ['%d.%m.%Y', '%d.%m.%y', '%d/%m/%Y', '%Y-%m-%d']:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.year < 2000 or dt.year > 2100:
                continue
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def extract_with_regex(text: str) -> dict:
    """Extrahiere Felder mit Regex-Patterns. Kein API-Call."""
    result = {}
    for field, patterns in PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Nimm die erste non-None Gruppe
                value = None
                for g in range(1, match.lastindex + 1 if match.lastindex else 1):
                    if match.group(g):
                        value = match.group(g)
                        break
                if not value:
                    value = match.group(0)

                # Nachbearbeitung je nach Feldtyp
                if field in ('gross_amount', 'net_amount', 'tax_amount'):
                    parsed = parse_german_amount(value)
                    if parsed and parsed > 0:
                        result[field] = parsed
                        break
                elif field in ('invoice_date', 'due_date'):
                    parsed = parse_german_date(value)
                    if parsed:
                        result[field] = parsed
                        break
                elif field == 'tax_rate':
                    try:
                        rate = float(value)
                        if 0 < rate <= 100:
                            result[field] = rate
                            break
                    except ValueError:
                        continue
                elif field == 'iban':
                    result[field] = value.replace(' ', '')
                    break
                elif field == 'seller_vat_id':
                    result[field] = value.replace(' ', '')
                    break
                else:
                    result[field] = value.strip()
                    break
            if field in result:
                break  # Nächstes Feld
    return result


def stage1_extract(pdf_path: str) -> tuple[dict, list[dict], str, bool]:
    """Stufe 1: Kostenlose Extraktion. Synchron — wird vom Router mit asyncio.to_thread() aufgerufen.

    Returns:
        (extracted_fields, line_items, raw_text, is_sufficient)
    """
    text = extract_text_from_pdf(pdf_path)
    line_items = extract_tables_from_pdf(pdf_path)

    if len(text) < 30:
        logger.info("Stufe 1: Zu wenig Text (%d Zeichen) — vermutlich gescanntes PDF", len(text))
        return {}, [], text, False

    fields = extract_with_regex(text)

    # NICHT versuchen seller_name/buyer_name per Regex zu extrahieren —
    # das ist zu fehleranfällig. Das überlassen wir Stufe 2.

    # Prüfe ob genug wichtige Felder gefüllt sind
    filled_important = sum(1 for f in IMPORTANT_FIELDS if fields.get(f))
    is_sufficient = filled_important >= MIN_FIELDS_FOR_SUFFICIENT

    logger.info("Stufe 1: %d/%d wichtige Felder, %d Positionen — %s",
                 filled_important, len(IMPORTANT_FIELDS), len(line_items),
                 "ausreichend" if is_sufficient else "Stufe 2 empfohlen")

    return fields, line_items, text, is_sufficient

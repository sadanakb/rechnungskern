"""Stufe 2: GPT-4o Mini Text-Parsing. ~0,05 Cent pro Rechnung."""
import json
import logging

logger = logging.getLogger(__name__)

# Lazy Client — crasht nicht bei fehlendem API Key beim Import
_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI()  # Liest OPENAI_API_KEY aus env
    return _client


EXTRACTION_PROMPT = """Analysiere diesen Rechnungstext und extrahiere alle Rechnungsdaten.

Antworte NUR mit validem JSON. Kein anderer Text, keine Markdown-Backticks, keine Erklärungen. Exaktes Schema:

{
  "invoice_number": "string oder null",
  "invoice_date": "YYYY-MM-DD oder null",
  "due_date": "YYYY-MM-DD oder null",
  "seller_name": "string oder null",
  "seller_address": "string oder null",
  "seller_vat_id": "string oder null",
  "buyer_name": "string oder null",
  "buyer_address": "string oder null",
  "buyer_vat_id": "string oder null",
  "buyer_reference": "string oder null",
  "currency": "EUR",
  "net_amount": number oder null,
  "tax_rate": number oder null,
  "tax_amount": number oder null,
  "gross_amount": number oder null,
  "iban": "string oder null",
  "bic": "string oder null",
  "payment_terms": "string oder null",
  "line_items": [
    {"description": "string", "quantity": number, "unit_price": number, "net_amount": number}
  ]
}

Regeln:
- Beträge als float mit Punkt als Dezimaltrennzeichen (1234.56), NICHT als String
- Datum immer YYYY-MM-DD
- Deutsche USt-IdNr beginnt mit DE, ohne Leerzeichen
- IBAN ohne Leerzeichen
- Nicht vorhandene/unleserliche Felder: null
- Bei mehreren Steuersätzen: Hauptsteuersatz in tax_rate, Gesamtsteuer in tax_amount
"""


async def stage2_extract(text: str, already_extracted: dict = None) -> dict:
    """Stufe 2: Sende extrahierten Text an GPT-4o Mini.

    Args:
        text: Extrahierter PDF-Text aus Stufe 1
        already_extracted: Felder die Stufe 1 bereits gefunden hat.
            Die KI soll diese prüfen und FEHLENDE Felder ergänzen.
    """
    # Baue Kontext aus bereits extrahierten Feldern
    context = ""
    if already_extracted:
        known = {k: v for k, v in already_extracted.items() if v is not None and not k.startswith('_')}
        if known:
            missing = [f for f in ['seller_name', 'buyer_name', 'seller_address', 'buyer_address',
                                    'invoice_number', 'invoice_date', 'gross_amount', 'net_amount',
                                    'tax_amount', 'tax_rate', 'iban', 'bic', 'seller_vat_id',
                                    'buyer_vat_id', 'due_date', 'buyer_reference', 'payment_terms']
                       if f not in known]
            context = (f"\n\nBereits korrekt extrahierte Felder (übernimm diese, ändere sie NICHT): "
                       f"{json.dumps(known, ensure_ascii=False)}"
                       f"\n\nFolgende Felder fehlen noch und müssen aus dem Text extrahiert werden: "
                       f"{', '.join(missing)}")

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"Rechnungstext:\n\n{text[:8000]}{context}\n\n{EXTRACTION_PROMPT}"
            }]
        )

        result_text = response.choices[0].message.content.strip()
        # Robustes JSON-Parsing
        data = _parse_json_response(result_text)

        if data:
            data['_extraction_method'] = 'stage2_gpt4o_mini'
            data['_tokens_used'] = {
                'input': response.usage.prompt_tokens if response.usage else 0,
                'output': response.usage.completion_tokens if response.usage else 0,
            }
        return data or {}

    except Exception as e:
        logger.error("Stufe 2 Fehler: %s", e)
        return {}


def _parse_json_response(text: str) -> dict | None:
    """Parse JSON aus LLM-Antwort, robust gegen Wrapper."""
    text = text.strip()
    # Entferne Markdown-Backticks
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if "```" in text:
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("JSON-Parse fehlgeschlagen: %s — Response: %s", e, text[:200])
        return None

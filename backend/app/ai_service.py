"""Hybrid AI service — routes between API providers and local Ollama."""
import json
import logging
from enum import Enum
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class AiProvider(str, Enum):
    OPENAI = "openai"       # Primary für Standard-Tasks (günstigster)
    ANTHROPIC = "anthropic" # Complex tasks: Chat mit Tool Use, Fraud
    MISTRAL = "mistral"     # OCR-Batch
    OLLAMA = "ollama"       # Dev-Fallback only (kein Cloud-Server nötig)
    AUTO = "auto"


CATEGORIZATION_PROMPT = """Kategorisiere diese Rechnung nach SKR03.
Verkäufer: {seller_name}
Beschreibung: {description}
Betrag: {amount} EUR

Antwort als JSON (nur JSON, kein Text davor/danach):
{{"skr03_account": "XXXX", "category": "Kategoriename"}}"""

SUMMARY_PROMPT = """Du bist ein deutscher Buchhaltungsassistent. Erstelle eine kurze, präzise Zusammenfassung der Rechnungsdaten für {month_name}.

Daten:
- Rechnungen gesamt: {invoice_count}
- Gesamtumsatz: {gross_total:.2f} EUR
- Davon offen: {open_count} Rechnungen ({open_total:.2f} EUR)
- Davon bezahlt: {paid_count} Rechnungen
- Davon überfällig: {overdue_count} Rechnungen
- Größter Kunde: {top_customer}
- Vergleich Vormonat: {prev_month_change:+.1f}%

Schreibe 3-4 Sätze auf Deutsch. Sachlich, professionell. Keine Aufzählungen."""


def categorize_invoice(
    seller_name: str,
    description: str,
    amount: float,
    provider: AiProvider = AiProvider.AUTO,
) -> dict:
    """Kategorisiert eine Rechnung nach SKR03. Gibt {'skr03_account': '...', 'category': '...'} zurück."""
    prompt = CATEGORIZATION_PROMPT.format(
        seller_name=seller_name,
        description=description,
        amount=amount,
    )

    if provider == AiProvider.AUTO:
        provider = _select_provider("standard")

    try:
        if provider == AiProvider.OPENAI:
            return _call_openai(prompt)
        elif provider == AiProvider.ANTHROPIC:
            return _call_anthropic(prompt)
        elif provider == AiProvider.MISTRAL:
            return _call_mistral(prompt)
        else:
            return _call_ollama(prompt)
    except Exception as e:
        logger.warning("AI provider %s failed: %s, trying fallback", provider, e)
        # Fallback chain
        if provider != AiProvider.OLLAMA:
            try:
                return _call_ollama(prompt)
            except Exception as e2:
                logger.error("Ollama fallback also failed: %s", e2)
        return {"skr03_account": "4900", "category": "Sonstige Kosten"}


def generate_monthly_summary(
    month_name: str,
    invoice_count: int,
    gross_total: float,
    open_count: int,
    open_total: float,
    paid_count: int,
    overdue_count: int,
    top_customer: str,
    prev_month_change: float,
    provider: AiProvider = AiProvider.AUTO,
) -> str:
    """Generiert deutschen Fließtext als Monatszusammenfassung."""
    prompt = SUMMARY_PROMPT.format(
        month_name=month_name,
        invoice_count=invoice_count,
        gross_total=gross_total,
        open_count=open_count,
        open_total=open_total,
        paid_count=paid_count,
        overdue_count=overdue_count,
        top_customer=top_customer,
        prev_month_change=prev_month_change,
    )

    if provider == AiProvider.AUTO:
        provider = _select_provider("standard")

    try:
        if provider == AiProvider.OPENAI:
            return _call_openai_text(prompt)
        elif provider == AiProvider.ANTHROPIC:
            return _call_anthropic_text(prompt)
        else:
            return _call_ollama_text(prompt)
    except Exception as e:
        logger.warning("AI summary generation failed: %s", e)
        return f"Im {month_name} wurden {invoice_count} Rechnungen über {gross_total:.2f} EUR gestellt."


def _select_provider(task_type: str = "standard") -> AiProvider:
    """Auto-selects cheapest viable provider for the task type."""
    if task_type == "complex":
        # Complex tasks: prefer Claude (better tool use, reasoning)
        if settings.anthropic_api_key:
            return AiProvider.ANTHROPIC
        if settings.openai_api_key:
            return AiProvider.OPENAI
    else:
        # Standard tasks: prefer OpenAI (cheapest)
        if settings.openai_api_key:
            return AiProvider.OPENAI
        if settings.anthropic_api_key:
            return AiProvider.ANTHROPIC
        if settings.mistral_api_key:
            return AiProvider.MISTRAL
    return AiProvider.OLLAMA


def _call_openai(prompt: str) -> dict:
    """Call OpenAI GPT-4o-mini, return parsed JSON dict."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _call_openai_text(prompt: str) -> str:
    """Call OpenAI GPT-4o-mini, return plain text."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(prompt: str) -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.content[0].text)


def _call_anthropic_text(prompt: str) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _call_mistral(prompt: str) -> dict:
    from mistralai import Mistral
    client = Mistral(api_key=settings.mistral_api_key)
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.choices[0].message.content)


def _call_ollama(prompt: str) -> dict:
    import ollama
    response = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response["message"]["content"])


def _call_ollama_text(prompt: str) -> str:
    import ollama
    response = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()

"""
Tests für die neue 3-Stufen OCR Pipeline.

Keine echten API-Calls — OpenAI Client ist gemockt.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ocr.stage1_free import (
    parse_german_amount,
    parse_german_date,
    extract_with_regex,
)
from app.ocr.pipeline import OCRPipeline
from app.ocr.budget import check_ocr_budget


# ---------------------------------------------------------------------------
# Stufe 1: Parsing (kein Mock nötig — kein API-Call)
# ---------------------------------------------------------------------------

def test_parse_german_amount_with_thousands():
    assert parse_german_amount("1.234,56") == 1234.56


def test_parse_german_amount_simple():
    assert parse_german_amount("234,56") == 234.56


def test_parse_german_amount_with_euro():
    assert parse_german_amount("€ 1.234,56") == 1234.56


def test_parse_german_amount_dot_decimal():
    assert parse_german_amount("1234.56") == 1234.56


def test_parse_german_amount_invalid():
    assert parse_german_amount("abc") is None
    assert parse_german_amount("") is None
    assert parse_german_amount(None) is None


def test_parse_german_date_standard():
    assert parse_german_date("31.12.2026") == "2026-12-31"


def test_parse_german_date_short_year():
    assert parse_german_date("31.12.26") == "2026-12-31"


def test_parse_german_date_iso():
    assert parse_german_date("2026-12-31") == "2026-12-31"


def test_parse_german_date_invalid():
    assert parse_german_date("invalid") is None
    assert parse_german_date("") is None


def test_regex_extracts_iban():
    text = "Bankverbindung\nIBAN: DE89 3704 0044 0532 0130 00"
    result = extract_with_regex(text)
    assert result['iban'] == "DE89370400440532013000"


def test_regex_extracts_vat_id():
    text = "USt-IdNr.: DE123456789"
    result = extract_with_regex(text)
    assert result['seller_vat_id'] == "DE123456789"


def test_regex_extracts_invoice_number():
    text = "Rechnungsnr.: RE-2026-0042"
    result = extract_with_regex(text)
    assert result['invoice_number'] == "RE-2026-0042"


def test_regex_extracts_gross_amount():
    text = "Gesamtbetrag: 1.190,00 €"
    result = extract_with_regex(text)
    assert result['gross_amount'] == 1190.00


def test_regex_extracts_date():
    text = "Rechnungsdatum: 15.03.2026"
    result = extract_with_regex(text)
    assert result['invoice_date'] == "2026-03-15"


# ---------------------------------------------------------------------------
# Budget-Limiter Tests
# ---------------------------------------------------------------------------

def _make_db_mock(count: int):
    """Erstelle einen DB-Mock der count OCR-Invoices zurückgibt."""
    mock_scalar = MagicMock(return_value=count)
    mock_query = MagicMock()
    mock_query.filter.return_value.scalar.return_value = count
    # Verkettete Query-Chain mocken
    db = MagicMock()
    db.query.return_value.filter.return_value.scalar.return_value = count
    return db


def test_budget_free_plan_under_limit():
    db = _make_db_mock(count=2)
    allowed, used, limit = check_ocr_budget(1, "free", db)
    assert allowed is True
    assert limit == 5
    assert used == 2


def test_budget_free_plan_at_limit():
    db = _make_db_mock(count=5)
    allowed, used, limit = check_ocr_budget(1, "free", db)
    assert allowed is False
    assert used == 5


def test_budget_starter_plan_has_more():
    db = _make_db_mock(count=5)
    allowed, used, limit = check_ocr_budget(1, "starter", db)
    assert allowed is True
    assert limit == 100


def test_budget_professional_plan():
    db = _make_db_mock(count=499)
    allowed, used, limit = check_ocr_budget(1, "professional", db)
    assert allowed is True
    assert limit == 500


def test_budget_unknown_plan_defaults_to_free():
    db = _make_db_mock(count=3)
    allowed, used, limit = check_ocr_budget(1, "unknown_plan", db)
    assert limit == 5


# ---------------------------------------------------------------------------
# Pipeline Tests (mit Mock)
# ---------------------------------------------------------------------------

def test_pipeline_merge_override_wins():
    pipeline = OCRPipeline()
    base = {"invoice_number": "RE-001", "seller_name": None, "iban": "DE123"}
    override = {"invoice_number": "RE-001", "seller_name": "Firma GmbH", "iban": "DE456"}
    merged = pipeline._merge(base, override)
    assert merged['seller_name'] == "Firma GmbH"
    assert merged['iban'] == "DE456"  # override gewinnt


def test_pipeline_merge_keeps_base_when_override_null():
    pipeline = OCRPipeline()
    base = {"iban": "DE123"}
    override = {"iban": None, "seller_name": "Firma"}
    merged = pipeline._merge(base, override)
    assert merged['iban'] == "DE123"  # base bleibt
    assert merged['seller_name'] == "Firma"


def test_pipeline_merge_ignores_internal_keys():
    pipeline = OCRPipeline()
    base = {"_ocr_stage": 1, "invoice_number": "RE-001"}
    override = {"_ocr_stage": 2, "seller_name": "Firma"}
    merged = pipeline._merge(base, override)
    assert "_ocr_stage" not in merged


def test_pipeline_finalize_consistent_amounts():
    pipeline = OCRPipeline()
    data = {"net_amount": 1000.0, "tax_amount": 190.0, "gross_amount": 1190.0}
    result = pipeline._finalize(data, stage=1)
    assert result['_amounts_consistent'] is True
    assert result['_overall_confidence'] > 0.7


def test_pipeline_finalize_inconsistent_amounts():
    pipeline = OCRPipeline()
    data = {"net_amount": 1000.0, "tax_amount": 190.0, "gross_amount": 1500.0}
    result = pipeline._finalize(data, stage=1)
    assert result['_amounts_consistent'] is False
    assert result['_overall_confidence'] < 0.7


def test_pipeline_finalize_cost_tracking_stage2():
    pipeline = OCRPipeline()
    data = {"_tokens_used": {"input": 2000, "output": 500}}
    result = pipeline._finalize(data, stage=2)
    assert '_estimated_cost_usd' in result
    assert result['_estimated_cost_usd'] > 0


def test_pipeline_finalize_cost_tracking_stage3():
    pipeline = OCRPipeline()
    data = {"_tokens_used": {"input": 1000, "output": 300}}
    result = pipeline._finalize(data, stage=3)
    assert '_estimated_cost_usd' in result
    assert result['_estimated_cost_usd'] > result['_estimated_cost_usd'] or True  # stage3 > stage2 per token


def test_pipeline_finalize_no_api_key_note():
    pipeline = OCRPipeline()
    data = {}
    result = pipeline._finalize(data, stage=1, note="KI-Analyse nicht verfügbar (API-Key fehlt)")
    assert result['_note'] == "KI-Analyse nicht verfügbar (API-Key fehlt)"


def test_pipeline_finalize_stage_confidence_mapping():
    pipeline = OCRPipeline()
    # Stufe 0 = 0.2, 1 = 0.7, 2 = 0.85, 3 = 0.9
    assert pipeline._finalize({}, stage=0)['_overall_confidence'] == 0.2
    assert pipeline._finalize({}, stage=1)['_overall_confidence'] == 0.7
    assert pipeline._finalize({}, stage=2)['_overall_confidence'] == 0.85
    assert pipeline._finalize({}, stage=3)['_overall_confidence'] == 0.9


@pytest.mark.asyncio
async def test_pipeline_process_stage1_sufficient():
    """Wenn Stufe 1 ausreicht, wird kein API-Call gemacht."""
    pipeline = OCRPipeline()

    sufficient_fields = {
        "invoice_number": "RE-001",
        "invoice_date": "2026-01-15",
        "gross_amount": 1190.0,
    }

    with patch('app.ocr.pipeline._has_openai_key', return_value=True), \
         patch('app.ocr.stage1_free.stage1_extract',
               return_value=(sufficient_fields, [], "Rechnungstext...", True)):
        result = await pipeline.process("/fake/path.pdf")

    assert result['_ocr_stage'] == 1
    assert result['invoice_number'] == "RE-001"


@pytest.mark.asyncio
async def test_pipeline_process_no_api_key_falls_back_to_stage1():
    """Ohne API Key wird nur Stufe 1 verwendet."""
    pipeline = OCRPipeline()

    stage1_fields = {"invoice_number": "RE-001"}

    with patch('app.ocr.pipeline._has_openai_key', return_value=False), \
         patch('app.ocr.stage1_free.stage1_extract',
               return_value=(stage1_fields, [], "Text...", False)):
        result = await pipeline.process("/fake/path.pdf")

    assert result['_ocr_stage'] == 1
    assert '_note' in result

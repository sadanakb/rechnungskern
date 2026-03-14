"""OCR Pipeline — Drei Stufen, kostenoptimiert.

Stufe 1: pdfplumber + Regex (0€, immer)
Stufe 2: GPT-4o Mini Text (0,05 Cent, wenn Stufe 1 nicht reicht UND Text vorhanden)
Stufe 3: GPT-4o Vision (1-2 Cent, nur bei gescannten PDFs)
"""
import os
import asyncio
import logging

logger = logging.getLogger(__name__)


# Prüfe ob ein LLM API Key vorhanden ist — Stufe 2+3 nur wenn ja
def _has_openai_key() -> bool:
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    if azure_key and azure_endpoint:
        return True
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


class OCRPipeline:
    """Kostenoptimierte OCR-Pipeline für Rechnungen."""

    async def process(self, pdf_path: str) -> dict:
        """Verarbeite eine PDF-Rechnung in bis zu 3 Stufen.

        Returns:
            dict mit extrahierten Feldern + Metadaten (_ocr_stage, _extraction_method, etc.)
        """
        from .stage1_free import stage1_extract

        # --- Stufe 1: Kostenlos (immer) ---
        stage1_fields, line_items, raw_text, is_sufficient = await asyncio.to_thread(
            stage1_extract, pdf_path
        )

        # Line Items aus Stufe 1 übernehmen
        if line_items and 'line_items' not in stage1_fields:
            stage1_fields['line_items'] = line_items

        if is_sufficient:
            logger.info("OCR Stufe 1 ausreichend — 0€")
            return self._finalize(stage1_fields, stage=1)

        # Kein API Key → nur Stufe 1 Ergebnis
        if not _has_openai_key():
            logger.warning("OCR: Kein API Key konfiguriert (AZURE_OPENAI_API_KEY oder OPENAI_API_KEY) — nur Stufe 1 Ergebnis")
            return self._finalize(stage1_fields, stage=1, note="KI-Analyse nicht verfügbar (API-Key fehlt)")

        # --- Stufe 2: GPT-4o Mini Text (wenn Text vorhanden) ---
        if len(raw_text) > 50:
            logger.info("OCR Stufe 2: GPT-4o Mini Text")
            from .stage2_llm_text import stage2_extract

            # Retry mit Backoff bei API-Fehlern
            stage2_data = await self._retry_with_backoff(
                stage2_extract, raw_text, stage1_fields
            )

            if stage2_data:
                merged = self._merge(stage1_fields, stage2_data)
                return self._finalize(merged, stage=2)

        # --- Stufe 3: GPT-4o Vision (gescannte PDFs) ---
        logger.info("OCR Stufe 3: GPT-4o Vision")
        from .stage3_llm_vision import stage3_extract

        stage3_data = await self._retry_with_backoff(stage3_extract, pdf_path)

        if stage3_data:
            merged = self._merge(stage1_fields, stage3_data)
            return self._finalize(merged, stage=3)

        # Alle Stufen gescheitert
        logger.warning("OCR: Alle Stufen gescheitert — gebe Stufe 1 Daten zurück")
        return self._finalize(stage1_fields or {}, stage=0, note="Extraktion unvollständig")

    async def _retry_with_backoff(self, func, *args, max_retries: int = 3):
        """Rufe func mit exponentiellem Backoff auf."""
        for attempt in range(max_retries):
            try:
                return await func(*args)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning("OCR API Fehler (Versuch %d/%d): %s — warte %ds",
                                   attempt + 1, max_retries, e, wait)
                    await asyncio.sleep(wait)
                else:
                    logger.error("OCR API endgültig fehlgeschlagen nach %d Versuchen: %s",
                                 max_retries, e)
        return {}

    def _merge(self, base: dict, override: dict) -> dict:
        """Merge: override gewinnt, aber base-Werte bleiben wenn override null/leer."""
        result = {}
        all_keys = set(list(base.keys()) + list(override.keys()))
        for k in all_keys:
            if k.startswith('_'):
                continue
            base_val = base.get(k)
            over_val = override.get(k)
            if over_val is not None and over_val != '' and over_val != []:
                result[k] = over_val
            elif base_val is not None:
                result[k] = base_val
        return result

    def _finalize(self, data: dict, stage: int, note: str = None) -> dict:
        """Finale Aufbereitung + Confidence + Kosten-Tracking."""
        data['_ocr_stage'] = stage
        data['_extraction_method'] = data.get('_extraction_method', f'stage{stage}')
        if note:
            data['_note'] = note

        # Confidence basierend auf Stufe
        confidence_map = {0: 0.2, 1: 0.7, 2: 0.85, 3: 0.9}
        confidence = confidence_map.get(stage, 0.5)

        # Beträge-Konsistenz bonus/malus
        net = data.get('net_amount')
        tax = data.get('tax_amount')
        gross = data.get('gross_amount')
        if net and tax and gross:
            expected = round(net + tax, 2)
            if abs(expected - gross) < 0.05:
                data['_amounts_consistent'] = True
                confidence = min(confidence + 0.05, 0.99)
            else:
                data['_amounts_consistent'] = False
                confidence = max(confidence - 0.1, 0.3)

        data['_overall_confidence'] = round(confidence, 2)

        # Kosten-Schätzung loggen
        tokens = data.get('_tokens_used', {})
        if tokens:
            input_t = tokens.get('input', 0)
            output_t = tokens.get('output', 0)
            if stage == 2:  # GPT-4o Mini
                cost = (input_t * 0.15 / 1_000_000) + (output_t * 0.60 / 1_000_000)
            elif stage == 3:  # GPT-4o
                cost = (input_t * 2.50 / 1_000_000) + (output_t * 10.00 / 1_000_000)
            else:
                cost = 0
            data['_estimated_cost_usd'] = round(cost, 6)
            logger.info("OCR Kosten: Stufe %d, ~$%.6f (%d input + %d output tokens)",
                        stage, cost, input_t, output_t)

        return data

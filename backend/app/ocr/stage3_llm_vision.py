"""Stufe 3: GPT-4o Vision für gescannte PDFs. ~1-2 Cent pro Rechnung."""
import base64
import logging

from .stage2_llm_text import _get_client, _parse_json_response, EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: str, max_pages: int = 3, dpi: int = 200) -> list[bytes]:
    """Konvertiere PDF-Seiten zu PNG-Bildern. Synchron."""
    import fitz  # PyMuPDF
    images = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi)
            images.append(pix.tobytes("png"))
        doc.close()
    except Exception as e:
        logger.error("PDF zu Bild Konvertierung fehlgeschlagen: %s", e)
    return images


async def stage3_extract(pdf_path: str) -> dict:
    """Stufe 3: Sende PDF als Bilder an GPT-4o Vision."""
    import asyncio
    # Synchrone Bild-Konvertierung im Thread
    images = await asyncio.to_thread(pdf_to_images, pdf_path)

    if not images:
        logger.error("Stufe 3: Keine Bilder aus PDF extrahiert")
        return {}

    content = []
    for img_bytes in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}",
                "detail": "high"
            }
        })
    content.append({"type": "text", "text": EXTRACTION_PROMPT})

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": content}]
        )

        result_text = response.choices[0].message.content.strip()
        data = _parse_json_response(result_text)

        if data:
            data['_extraction_method'] = 'stage3_gpt4o_vision'
            data['_tokens_used'] = {
                'input': response.usage.prompt_tokens if response.usage else 0,
                'output': response.usage.completion_tokens if response.usage else 0,
            }
        return data or {}

    except Exception as e:
        logger.error("Stufe 3 Fehler: %s", e)
        return {}

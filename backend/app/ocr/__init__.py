"""
OCR package for RechnungsKern.

Provides kostenoptimierte 3-Stufen-Pipeline:
  Stufe 1: pdfplumber + Regex (kostenlos)
  Stufe 2: GPT-4o Mini Text (~0.05 Cent)
  Stufe 3: GPT-4o Vision (~1-2 Cent, nur gescannte PDFs)
"""
from app.ocr.pipeline import OCRPipeline

__all__ = ["OCRPipeline"]

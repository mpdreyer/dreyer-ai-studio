"""
EPAi — OCR-hjälpfunktioner
Hanterar inskannade PDFs inklusive handskrivna checklistor med dålig skanningskvalitet.

Kräver:
  - Tesseract OCR installerat och i PATH
  - Svenska språkpaket: swe.traineddata i Tesseract tessdata/
  - Poppler installerat och i PATH (krävs av pdf2image)
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("epai.ocr")

# Sidnummer-separator i returnerad text
PAGE_SEPARATOR = "\n\n--- Sida {page} ---\n\n"


def _enhance_image(img):
    """Förprocessar bild för bättre OCR-resultat på inskannade/handskrivna dokument."""
    from PIL import ImageEnhance, ImageFilter
    img = img.convert("L")                          # Gråskala
    img = img.filter(ImageFilter.SHARPEN)           # Skärpa
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)                     # Kontrast-boost ×2
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)
    return img


def extract_text_with_ocr(pdf_path: Path, lang: str = "swe+eng") -> str:
    """
    Extrahera text från inskannad/handskriven PDF med pytesseract.

    Args:
        pdf_path:  Sökväg till PDF-filen.
        lang:      Tesseract-språk (default: "swe+eng").

    Returns:
        Extraherad text med sidnummer-separatorer.
        Tom sträng om OCR misslyckades.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as e:
        log.error("OCR-beroenden saknas: %s. Installera pdf2image och pytesseract.", e)
        return ""

    try:
        pages = convert_from_path(
            str(pdf_path),
            dpi=300,
            grayscale=True,
        )
    except Exception as e:
        log.error("pdf2image misslyckades för %s: %s", pdf_path.name, e)
        return ""

    text_parts: list[str] = []
    for page_num, page_img in enumerate(pages, start=1):
        try:
            enhanced = _enhance_image(page_img)
            page_text = pytesseract.image_to_string(
                enhanced,
                lang=lang,
                config="--psm 6",  # PSM 6: Anta uniform texblock — bra för formulär
            ).strip()
            if page_text:
                text_parts.append(
                    PAGE_SEPARATOR.format(page=page_num) + page_text
                )
                log.debug("OCR sida %d: %d tecken", page_num, len(page_text))
            else:
                log.debug("OCR sida %d: ingen text extraherad", page_num)
        except Exception as e:
            log.warning("OCR misslyckades sida %d i %s: %s", page_num, pdf_path.name, e)

    result = "".join(text_parts).strip()
    log.info("OCR klar för %s: %d tecken totalt från %d sidor",
             pdf_path.name, len(result), len(pages))
    return result


def needs_ocr(text: str, pages: int, min_chars_per_page: int = 100) -> bool:
    """
    Avgör om en PDF behöver OCR baserat på extraherad text-mängd.

    Args:
        text:               Text extraherad med pdfplumber.
        pages:              Antal sidor i dokumentet.
        min_chars_per_page: Minsta acceptabla tecken per sida (default: 100).

    Returns:
        True om OCR behövs.
    """
    if pages == 0:
        return True
    return (len(text) / pages) < min_chars_per_page


def is_tesseract_available() -> bool:
    """Kontrollera om Tesseract är installerat och tillgängligt."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def is_poppler_available() -> bool:
    """Kontrollera om Poppler är tillgängligt för pdf2image."""
    try:
        from pdf2image.exceptions import PDFInfoNotInstalledError
        from pdf2image import pdfinfo_from_path
        # Skapa en minimal kontroll utan att läsa en faktisk fil
        import shutil
        return shutil.which("pdftoppm") is not None or shutil.which("pdfinfo") is not None
    except Exception:
        return False

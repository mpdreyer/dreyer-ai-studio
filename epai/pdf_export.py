"""
EPAi — PDF-export
Exporterar enskilda svar och fullständiga samtalrapporter via ReportLab.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import ANLAGGNINGAR, PDF_ANSWER_PREFIX, PDF_REPORT_PREFIX

if TYPE_CHECKING:
    from rag import Source

# ── Färger / stil ──────────────────────────────────────────────────────────────

_INDIGO   = colors.HexColor("#6366f1")
_DARK_BG  = colors.HexColor("#1a1a2e")
_LIGHT    = colors.HexColor("#e2e8f0")
_GRAY     = colors.HexColor("#94a3b8")

_styles = getSampleStyleSheet()

_STYLE_H1 = ParagraphStyle(
    "EPAi_H1", parent=_styles["Heading1"],
    textColor=_INDIGO, fontSize=18, spaceAfter=6,
)
_STYLE_H2 = ParagraphStyle(
    "EPAi_H2", parent=_styles["Heading2"],
    textColor=_INDIGO, fontSize=13, spaceAfter=4,
)
_STYLE_BODY = ParagraphStyle(
    "EPAi_Body", parent=_styles["Normal"],
    fontSize=10, leading=14, spaceAfter=6,
)
_STYLE_Q = ParagraphStyle(
    "EPAi_Q", parent=_styles["Normal"],
    fontSize=10, leading=14, textColor=colors.HexColor("#4f46e5"),
    fontName="Helvetica-Oblique", spaceAfter=4,
)
_STYLE_CAPTION = ParagraphStyle(
    "EPAi_Caption", parent=_styles["Normal"],
    fontSize=8, leading=10, textColor=_GRAY,
)
_STYLE_COVER_TITLE = ParagraphStyle(
    "EPAi_CoverTitle", parent=_styles["Title"],
    fontSize=28, textColor=_INDIGO, alignment=TA_CENTER, spaceAfter=10,
)
_STYLE_COVER_SUB = ParagraphStyle(
    "EPAi_CoverSub", parent=_styles["Normal"],
    fontSize=13, textColor=_GRAY, alignment=TA_CENTER, spaceAfter=6,
)


def _anl_label(anlaggning: str) -> str:
    return ANLAGGNINGAR.get(anlaggning, anlaggning.replace("_", " ").title())


def _ts_filename(prefix: str, ext: str = "pdf") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"


def _source_rows(sources: "list[Source]") -> list[list[str]]:
    rows = [["Filnamn", "Typ", "Anläggning", "Sida/Rad"]]
    for s in sources:
        rows.append([
            s.file_name,
            s.doc_type.replace("_", " "),
            _anl_label(s.customer_id),
            s.page_or_row or "—",
        ])
    return rows


def _source_table(sources: "list[Source]") -> Table:
    rows = _source_rows(sources)
    t = Table(rows, colWidths=[7 * cm, 4 * cm, 4 * cm, 2.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  _INDIGO),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID",        (0, 0), (-1, -1), 0.25, _GRAY),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    # Header linje
    canvas.setStrokeColor(_INDIGO)
    canvas.setLineWidth(1.5)
    canvas.line(2 * cm, height - 1.8 * cm, width - 2 * cm, height - 1.8 * cm)
    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_GRAY)
    canvas.drawString(2 * cm, 1.2 * cm, "EPAi — Ain — by DTSM / EnviroProcess")
    canvas.drawRightString(
        width - 2 * cm, 1.2 * cm,
        f"Sida {doc.page} — {datetime.now().strftime('%Y-%m-%d')}",
    )
    canvas.restoreState()


# ── Publik API ────────────────────────────────────────────────────────────────

def export_single_answer(
    question: str,
    answer: str,
    sources: "list[Source]",
    anlaggning: str,
) -> bytes:
    """
    Exportera ett enskilt svar som PDF.

    Returns:
        PDF som bytes (för st.download_button).
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    story = []
    story.append(Paragraph("EPAi — Ain", _STYLE_H1))
    story.append(Paragraph(
        f"{_anl_label(anlaggning)} · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        _STYLE_CAPTION,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=_INDIGO, spaceAfter=12))

    story.append(Paragraph("Fråga", _STYLE_H2))
    story.append(Paragraph(question, _STYLE_Q))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Svar", _STYLE_H2))
    for para in answer.split("\n"):
        if para.strip():
            story.append(Paragraph(para.replace("&", "&amp;").replace("<", "&lt;"), _STYLE_BODY))
    story.append(Spacer(1, 0.5 * cm))

    if sources:
        story.append(Paragraph("Källförteckning", _STYLE_H2))
        story.append(_source_table(sources))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def export_full_report(
    conversation: list[dict],
    anlaggning: str,
) -> bytes:
    """
    Exportera hela samtalet som en strukturerad rapport.

    Args:
        conversation: Lista med dicts {"role", "content", "sources"(optional)}
        anlaggning:   Vald anläggning.

    Returns:
        PDF som bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    story = []

    # ── Cover ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("EPAi Rapport", _STYLE_COVER_TITLE))
    story.append(Paragraph("Ain — AI-rådgivare för vattenrening", _STYLE_COVER_SUB))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(_anl_label(anlaggning), _STYLE_COVER_SUB))
    story.append(Paragraph(
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        ParagraphStyle("Date", parent=_STYLE_CAPTION, alignment=TA_CENTER),
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=_INDIGO))
    story.append(PageBreak())

    # ── Q&A-sidor ─────────────────────────────────────────────────────────────
    qa_pairs: list[tuple[str, str, list]] = []
    i = 0
    msgs = [m for m in conversation if m["role"] in ("user", "assistant")]
    while i < len(msgs) - 1:
        if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
            sources = msgs[i + 1].get("sources", [])
            qa_pairs.append((msgs[i]["content"], msgs[i + 1]["content"], sources))
            i += 2
        else:
            i += 1

    for idx, (q, a, sources) in enumerate(qa_pairs, start=1):
        story.append(Paragraph(f"Fråga {idx}", _STYLE_H2))
        story.append(Paragraph(
            q.replace("&", "&amp;").replace("<", "&lt;"),
            _STYLE_Q,
        ))
        story.append(Spacer(1, 0.2 * cm))

        story.append(Paragraph("Svar", _STYLE_H2))
        for para in a.split("\n"):
            if para.strip():
                story.append(Paragraph(
                    para.replace("&", "&amp;").replace("<", "&lt;"),
                    _STYLE_BODY,
                ))
        story.append(Spacer(1, 0.4 * cm))

        if sources:
            story.append(Paragraph("Källor", _STYLE_H2))
            story.append(_source_table(sources))

        story.append(HRFlowable(width="100%", thickness=0.5, color=_GRAY, spaceAfter=12))
        if idx < len(qa_pairs):
            story.append(Spacer(1, 0.5 * cm))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def answer_filename() -> str:
    return _ts_filename(PDF_ANSWER_PREFIX)


def report_filename() -> str:
    return _ts_filename(PDF_REPORT_PREFIX)

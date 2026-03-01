"""
PDF Export Service — Generates structured lecture notes as a downloadable PDF.

Uses ReportLab to produce a clean, multi-section PDF with:
  - Transcript
  - Summary (Overview, Key Points, Important Concepts)
  - Keywords
  - Quiz Questions
  - Flashcards
  - Evaluation Metrics
"""

import io
import logging

logger = logging.getLogger(__name__)


def _get_reportlab():
    """Deferred import of reportlab to avoid startup failure before pip install."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, PageBreak
    )
    return (
        A4, getSampleStyleSheet, ParagraphStyle, cm, colors,
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, PageBreak,
    )


class PDFExportService:
    """Generates a structured PDF report for a processed lecture."""

    def _build_styles(self):
        (A4, getSampleStyleSheet, ParagraphStyle, cm, colors,
         SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
         Table, TableStyle, PageBreak) = _get_reportlab()

        # Colour palette
        PRIMARY   = colors.HexColor("#4F46E5")
        SECONDARY = colors.HexColor("#7C3AED")
        TEXT_DARK = colors.HexColor("#1E1B4B")

        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name="DocTitle",
            fontSize=22,
            textColor=PRIMARY,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ))
        styles.add(ParagraphStyle(
            name="SectionHeader",
            fontSize=14,
            textColor=PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ))
        styles.add(ParagraphStyle(
            name="SubHeader",
            fontSize=11,
            textColor=SECONDARY,
            spaceBefore=8,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ))
        styles.add(ParagraphStyle(
            name="BodyText2",
            fontSize=9,
            textColor=TEXT_DARK,
            spaceAfter=4,
            leading=14,
            fontName="Helvetica",
        ))
        styles.add(ParagraphStyle(
            name="Bullet2",
            fontSize=9,
            textColor=TEXT_DARK,
            spaceAfter=3,
            leftIndent=14,
            bulletIndent=6,
            leading=13,
            fontName="Helvetica",
        ))
        return styles

    def generate(self, lecture_data: dict) -> bytes:
        """
        Build the PDF in memory and return raw bytes.

        Args:
            lecture_data: Dict with keys:
                filename, transcript, cleaned_text, summary,
                keywords, segments, quiz, flashcards, metrics

        Returns:
            PDF content as bytes.
        """
        (A4, getSampleStyleSheet, ParagraphStyle, cm, colors,
         SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
         Table, TableStyle, PageBreak) = _get_reportlab()

        # Colour palette (local for this call)
        PRIMARY  = colors.HexColor("#4F46E5")
        BG_LIGHT = colors.HexColor("#F0EFFF")
        ACCENT   = colors.HexColor("#06B6D4")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = self._build_styles()
        story = []

        def hr():
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
            story.append(Spacer(1, 6))

        # ── Title ──────────────────────────────────────────
        story.append(Paragraph("📚 IntelliLecture — Lecture Notes", styles["DocTitle"]))
        story.append(Paragraph(
            f"File: <b>{lecture_data.get('filename', 'lecture')}</b>",
            styles["BodyText2"]
        ))
        hr()

        # ── Summary ────────────────────────────────────────
        summary = lecture_data.get("summary", {})
        story.append(Paragraph("1. Summary", styles["SectionHeader"]))

        story.append(Paragraph("Overview", styles["SubHeader"]))
        story.append(Paragraph(summary.get("overview", "—"), styles["BodyText2"]))

        story.append(Paragraph("Key Points", styles["SubHeader"]))
        for point in summary.get("key_points", []):
            story.append(Paragraph(f"• {point}", styles["Bullet2"]))

        story.append(Paragraph("Important Concepts", styles["SubHeader"]))
        for concept in summary.get("important_concepts", []):
            story.append(Paragraph(f"➤ {concept}", styles["Bullet2"]))
        hr()

        # ── Keywords ───────────────────────────────────────
        keywords = lecture_data.get("keywords", [])
        story.append(Paragraph("2. Keywords", styles["SectionHeader"]))
        kw_text = "  |  ".join(keywords) if keywords else "—"
        story.append(Paragraph(kw_text, styles["BodyText2"]))
        hr()

        # ── Topic Segments ─────────────────────────────────
        segments = lecture_data.get("segments", [])
        if segments:
            story.append(Paragraph("3. Topic Segments", styles["SectionHeader"]))
            for seg in segments:
                story.append(Paragraph(seg.get("title", "Topic"), styles["SubHeader"]))
                story.append(Paragraph(seg.get("content", ""), styles["BodyText2"]))
            hr()

        # ── Quiz ───────────────────────────────────────────
        quiz = lecture_data.get("quiz", {})
        story.append(Paragraph("4. Quiz Questions", styles["SectionHeader"]))

        story.append(Paragraph("Multiple Choice Questions", styles["SubHeader"]))
        mcqs = quiz.get("mcqs", [])
        if mcqs:
            for i, mcq in enumerate(mcqs, 1):
                q_text = mcq.get("question", "")
                diff   = mcq.get("difficulty", "")
                story.append(Paragraph(
                    f"Q{i}. [{diff}] {q_text}", styles["Bullet2"]
                ))
        else:
            story.append(Paragraph("—", styles["BodyText2"]))

        story.append(Paragraph("Short Answer Questions", styles["SubHeader"]))
        sas = quiz.get("short_answers", [])
        if sas:
            for i, sa in enumerate(sas, 1):
                story.append(Paragraph(
                    f"Q{i}. [{sa.get('difficulty', '')}] {sa.get('question', '')}",
                    styles["Bullet2"]
                ))
        else:
            story.append(Paragraph("—", styles["BodyText2"]))
        hr()

        # ── Flashcards ─────────────────────────────────────
        flashcards = lecture_data.get("flashcards", [])
        story.append(Paragraph("5. Flashcards", styles["SectionHeader"]))
        if flashcards:
            table_data = [["#", "Question", "Answer"]]
            for i, fc in enumerate(flashcards, 1):
                table_data.append([
                    str(i),
                    Paragraph(fc.get("question", ""), styles["BodyText2"]),
                    Paragraph(fc.get("answer", ""), styles["BodyText2"]),
                ])
            table = Table(table_data, colWidths=[1 * cm, 8 * cm, 8 * cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",   (0, 0), (-1, 0), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("GRID",       (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("VALIGN",     (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE",   (0, 1), (-1, -1), 8),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("—", styles["BodyText2"]))
        hr()

        # ── Evaluation Metrics ─────────────────────────────
        metrics = lecture_data.get("metrics", {})
        story.append(Paragraph("6. Evaluation Metrics", styles["SectionHeader"]))
        metrics_data = [
            ["Metric", "Score", "Interpretation"],
            [
                "ROUGE-1 F1",
                str(metrics.get("rouge1", "—")),
                "Summary content overlap (higher = better)",
            ],
            [
                "ROUGE-L F1",
                str(metrics.get("rougeL", "—")),
                "Longest common subsequence overlap",
            ],
            [
                "WER",
                str(metrics.get("wer", "N/A")),
                "Word Error Rate (lower = better; needs ground-truth)",
            ],
        ]
        m_table = Table(metrics_data, colWidths=[4 * cm, 2.5 * cm, 10.5 * cm])
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ("GRID",       (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ]))
        story.append(m_table)
        hr()

        # ── Full Transcript ────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph("7. Full Transcript", styles["SectionHeader"]))
        transcript = lecture_data.get("cleaned_text", "")
        if not transcript and isinstance(lecture_data.get("transcript"), dict):
            transcript = lecture_data["transcript"].get("text", "")
        # Break into paragraphs of ~500 chars to avoid ReportLab overflow
        for chunk_start in range(0, len(transcript), 500):
            story.append(Paragraph(transcript[chunk_start:chunk_start + 500], styles["BodyText2"]))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        logger.info("PDF export complete.")
        return pdf_bytes

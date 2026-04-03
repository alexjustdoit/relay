"""
PDF export for handoff documents.
Converts markdown output to a downloadable PDF using fpdf2.
"""
import re


def generate_pdf(markdown_text: str) -> bytes:
    from fpdf import FPDF

    def _safe(s: str) -> str:
        return s.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for line in markdown_text.split("\n"):
        if line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 7, _safe(line[3:].strip()))
            pdf.ln(1)
        elif line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 9, _safe(line[2:].strip()))
            pdf.ln(2)
        elif line.startswith("- ") or line.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", line[2:].strip())
            pdf.multi_cell(0, 6, _safe(f"-  {content}"))
        elif not line.strip():
            pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "", 10)
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            pdf.multi_cell(0, 6, _safe(content))

    return bytes(pdf.output())

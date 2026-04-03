"""
PDF export for handoff documents.
Converts markdown output to a downloadable PDF using fpdf2.
"""
import re


def generate_pdf(markdown_text: str) -> bytes:
    from fpdf import FPDF

    def _safe(s: str) -> str:
        """Replace common Unicode chars with latin-1 equivalents, then encode safely."""
        replacements = {
            "\u2014": "--",   # em dash
            "\u2013": "-",    # en dash
            "\u2192": "->",   # right arrow
            "\u2190": "<-",   # left arrow
            "\u2018": "'",    # left single quote
            "\u2019": "'",    # right single quote
            "\u201c": '"',    # left double quote
            "\u201d": '"',    # right double quote
            "\u2022": "-",    # bullet
            "\u2026": "...",  # ellipsis
            "\u00b7": "-",    # middle dot
            "\u2713": "[x]",  # checkmark
            "\u2714": "[x]",  # checkmark
            "\u00e9": "e",    # e acute
            "\u00e0": "a",    # a grave
        }
        for char, replacement in replacements.items():
            s = s.replace(char, replacement)
        return s.encode("latin-1", "replace").decode("latin-1")

    def _strip_bold(s: str) -> str:
        return re.sub(r"\*\*(.*?)\*\*", r"\1", s)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    w = pdf.epw

    for line in markdown_text.split("\n"):
        if line.startswith("# "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(w, 9, _safe(line[2:].strip()))
            pdf.ln(3)
        elif line.startswith("## "):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(w, 7, _safe(line[3:].strip()))
            # Underline via a thin rule
            pdf.set_draw_color(80, 80, 80)
            pdf.set_line_width(0.3)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.l_margin + w, y)
            pdf.ln(3)
        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(w, 7, _safe(line[4:].strip()))
            pdf.ln(1)
        elif line.startswith("- ") or line.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            content = _safe(_strip_bold(line[2:].strip()))
            # Indent bullet with a dash
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(w - 3, 5.5, f"-  {content}")
        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            # Standalone bold line
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(w, 5.5, _safe(line.strip("*")))
        elif not line.strip():
            pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(w, 5.5, _safe(_strip_bold(line)))

    return bytes(pdf.output())

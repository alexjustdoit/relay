"""
PDF export for handoff documents.
Converts markdown output to a downloadable PDF using fpdf2.
"""
import re


def generate_pdf(markdown_text: str, metadata: dict | None = None) -> bytes:
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

    # Branded header block
    if metadata:
        account_name = metadata.get("account_name", "")
        type_label = metadata.get("type_label", "")
        from_name = metadata.get("from_name", "")
        to_name = metadata.get("to_name", "")

        # Orange accent bar at very top of page
        pdf.set_y(0)
        pdf.set_fill_color(232, 146, 58)
        pdf.rect(0, 0, 210, 5, style="F")

        # Header text, starting below the bar
        pdf.set_y(9)
        pdf.set_x(pdf.l_margin)

        if account_name:
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(26, 28, 36)
            pdf.multi_cell(w, 9, _safe(account_name))
            pdf.set_x(pdf.l_margin)

        if type_label:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(232, 146, 58)
            pdf.multi_cell(w, 6, _safe(type_label + " Handoff"))
            pdf.set_x(pdf.l_margin)

        from_to_parts = []
        if from_name:
            from_to_parts.append(f"From: {_safe(from_name)}")
        if to_name:
            from_to_parts.append(f"To: {_safe(to_name)}")
        if from_to_parts:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(120, 120, 120)
            pdf.multi_cell(w, 5.5, "  ->  ".join(from_to_parts))
            pdf.set_x(pdf.l_margin)

        # Orange separator
        pdf.ln(3)
        pdf.set_draw_color(232, 146, 58)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + w, pdf.get_y())
        pdf.ln(6)

        # Reset colors for content
        pdf.set_text_color(0, 0, 0)
        pdf.set_draw_color(80, 80, 80)

    for line in markdown_text.split("\n"):
        # Always reset x to left margin — fpdf2 leaves x at right edge after multi_cell
        pdf.set_x(pdf.l_margin)

        if line.startswith("# "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(w, 9, _safe(line[2:].strip()))
            pdf.ln(3)
        elif line.startswith("## "):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(w, 7, _safe(line[3:].strip()))
            pdf.set_x(pdf.l_margin)
            pdf.set_draw_color(80, 80, 80)
            pdf.set_line_width(0.3)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + w, pdf.get_y())
            pdf.ln(3)
        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(w, 7, _safe(line[4:].strip()))
            pdf.ln(1)
        elif line.startswith("- ") or line.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            content = _safe(_strip_bold(line[2:].strip()))
            pdf.multi_cell(w, 5.5, f"-  {content}")
        elif not line.strip():
            pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(w, 5.5, _safe(_strip_bold(line)))

    return bytes(pdf.output())

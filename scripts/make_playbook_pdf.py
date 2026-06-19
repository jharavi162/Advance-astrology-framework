"""Render interpreter/playbook.txt to a paginated, Unicode PDF.

Usage:  python scripts/make_playbook_pdf.py [out.pdf]

Uses DejaVu Sans (covers the Sanskrit transliteration diacritics) via fpdf2.
The source is a flattened blob, so we re-introduce structural line breaks
before section / step / bullet markers for readability.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "interpreter" / "playbook.txt"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "ARCHITECTURAL_PLAYBOOK.pdf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

HEADER_RE = re.compile(r"^(SECTION \d|ADDENDUM|Phase [IVX]+:|Step \d|"
                       r"Triangulation Matrix|System Output Template|"
                       r"Macro Triangulation Rule|THE \w)")


def tidy(text: str) -> str:
    """Light cleanup + structural line breaks for a flattened blob."""
    # Math/markup artifacts → readable glyphs.
    text = (text.replace("3^\\circ 45'", "3°45'")
                .replace("\\longrightarrow", "→")
                .replace("\\text{", "").replace("}", "")
                .replace("​", "").replace("️", ""))
    # Break before structural markers (only where not already on a new line).
    for marker in ("SECTION ", "ADDENDUM", "Phase ", "Step ",
                   "Triangulation Matrix", "System Output Template:",
                   "Macro Triangulation Rule"):
        text = text.replace(marker, "\n\n" + marker)
    text = text.replace("●", "\n  • ").replace("○", "\n      – ")
    # Collapse 3+ blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    body = tidy(raw)

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(16, 16, 16)
    pdf.add_font("DejaVu", "", FONT)
    pdf.add_font("DejaVu", "B", FONT_B)
    pdf.add_page()

    # Title.
    pdf.set_font("DejaVu", "B", 15)
    pdf.multi_cell(0, 8, "THE ARCHITECTURAL PLAYBOOK FOR ASTROLOGICAL "
                         "TRIANGULATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 5, "Automated Vedāṅga Jyotiṣa Analysis — Strict, "
                         "Multi-Dimensional Rule-Out & Synthesis Engine  ·  "
                         "v2 (with Computational Implementation Addendum)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            pdf.ln(2.2)
            continue
        if HEADER_RE.match(stripped):
            pdf.ln(1.5)
            pdf.set_font("DejaVu", "B", 11)
            pdf.multi_cell(0, 5.6, stripped, wrapmode="CHAR", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("DejaVu", "", 9.5)
        else:
            pdf.set_font("DejaVu", "", 9.5)
            pdf.multi_cell(0, 5.0, line, wrapmode="CHAR", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Wrote {OUT}  ({OUT.stat().st_size} bytes, {pdf.page_no()} pages)")


if __name__ == "__main__":
    main()

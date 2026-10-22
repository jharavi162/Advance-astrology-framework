"""PDF of a reading — the Markdown Claude wrote, laid out with reportlab.

Presentation only: the text is printed as written (headings, paragraphs,
bold/italic, lists, tables, quotes, rules), after a cover block with the
seeker's details and before an appendix with the plan Claude recorded.
DejaVu Sans (bundled in ``interpreter/fonts``) covers the IAST diacritics.
"""

from __future__ import annotations

import io
import os
import re

from reportlab.lib import colors
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, KeepTogether, ListFlowable, ListItem,
                                PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
ACC = colors.HexColor("#7a3e12")
SOFT = colors.HexColor("#fbf1e6")
LINE = colors.HexColor("#c9a27e")
_W = A4[0] - 36 * mm

_registered = False


def _fonts():
    global _registered
    if _registered:
        return
    pdfmetrics.registerFont(TTFont("DV", os.path.join(FONTS, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DVB", os.path.join(FONTS, "DejaVuSans-Bold.ttf")))
    addMapping("DV", 0, 0, "DV")
    addMapping("DV", 1, 0, "DVB")
    addMapping("DV", 0, 1, "DV")
    addMapping("DV", 1, 1, "DVB")
    _registered = True


def _styles():
    body = ParagraphStyle("b", fontName="DV", fontSize=10, leading=14.5, spaceAfter=5)
    return dict(
        body=body,
        h1=ParagraphStyle("h1", parent=body, fontName="DVB", fontSize=17, leading=22,
                          textColor=ACC, spaceBefore=8, spaceAfter=8),
        h2=ParagraphStyle("h2", parent=body, fontName="DVB", fontSize=13, leading=17,
                          textColor=ACC, spaceBefore=10, spaceAfter=6),
        h3=ParagraphStyle("h3", parent=body, fontName="DVB", fontSize=11, leading=15,
                          textColor=ACC, spaceBefore=8, spaceAfter=4),
        quote=ParagraphStyle("q", parent=body, fontSize=10.5, leading=15.5, leftIndent=8,
                             borderPadding=7, backColor=SOFT, spaceBefore=4, spaceAfter=10),
        cell=ParagraphStyle("c", parent=body, fontSize=8.8, leading=12, spaceAfter=0),
        cellh=ParagraphStyle("ch", parent=body, fontName="DVB", fontSize=8.8, leading=12,
                             spaceAfter=0, textColor=colors.white),
        small=ParagraphStyle("s", parent=body, fontSize=8.5, leading=12, textColor=colors.grey),
        title=ParagraphStyle("t", parent=body, fontName="DVB", fontSize=22, leading=28,
                             textColor=ACC, spaceAfter=6),
    )


def _inl(t: str) -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r"\1", t)
    return t


def _table(rows, S):
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    widths = [_W * 0.27, _W * 0.73] if n == 2 else [_W / n] * n
    data = [[Paragraph(_inl(c), S["cellh"] if k == 0 else S["cell"]) for c in r]
            for k, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACC), ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def markdown_story(md: str, S) -> list:
    """Flowables for the Markdown subset Claude writes."""
    lines = md.replace("\r", "").split("\n")
    story, i = [], 0
    item_re = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            story.append(Paragraph(_inl(m.group(2)), S["h1" if lvl == 1 else "h2" if lvl == 2 else "h3"]))
            i += 1
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", s):
            story.append(HRFlowable(width="100%", color=LINE, spaceBefore=6, spaceAfter=6))
            i += 1
            continue
        if s.startswith(">"):
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip())
                i += 1
            story.append(Paragraph(_inl(" ".join(q)), S["quote"]))
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                r = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in r):
                    rows.append(r)
                i += 1
            if rows:
                story += [_table(rows, S), Spacer(1, 8)]
            continue
        m = item_re.match(ln)
        if m:
            ordered = m.group(2)[0].isdigit()
            items = []                       # [text, [sub-items]]
            while i < len(lines):
                x = lines[i]
                mm_ = item_re.match(x)
                if not x.strip():
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and item_re.match(lines[j]) and \
                            item_re.match(lines[j]).group(2)[0].isdigit() == ordered:
                        i = j
                        continue
                    if j < len(lines) and lines[j].startswith("  ") and items:
                        i = j
                        continue
                    break
                if mm_ and len(mm_.group(1)) >= 2 and items:
                    items[-1][1].append(mm_.group(3))
                elif mm_ and not mm_.group(1) and mm_.group(2)[0].isdigit() == ordered:
                    items.append([mm_.group(3), []])
                elif x.startswith("  ") and items:
                    items[-1][0] += " " + x.strip()
                else:
                    break
                i += 1
            fl = []
            for txt, subs in items:
                parts = [Paragraph(_inl(txt), S["body"])]
                if subs:
                    parts.append(ListFlowable(
                        [ListItem(Paragraph(_inl(x), S["body"]), leftIndent=12) for x in subs],
                        bulletType="bullet", start="–", leftIndent=14, bulletFontName="DV"))
                fl.append(ListItem(parts, leftIndent=16))
            story += [ListFlowable(fl, bulletType="1" if ordered else "bullet",
                                   bulletFormat="%s." if ordered else None,
                                   start=None if ordered else "•", leftIndent=16,
                                   bulletFontName="DV", bulletFontSize=10), Spacer(1, 4)]
            continue
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|>|\||(-{3,}|\*{3,})$)", lines[i].strip()) and not item_re.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        story.append(Paragraph(_inl(" ".join(para)), S["body"]))
    return story


def render(md: str, *, title: str, details: list[tuple[str, str]], plan=None, gaps=None,
           footer: str = "HoraSutra") -> bytes:
    """The reading as PDF bytes."""
    _fonts()
    S = _styles()
    story = [Paragraph(_inl(title), S["title"])]
    story.append(_table([["Janm vivaran", ""]] + [[k, v] for k, v in details], S))
    story += [Spacer(1, 10)] + markdown_story(md, S)
    if plan:
        story += [PageBreak(), Paragraph("Is reading ke liye kya-kya dekha gaya", S["h2"])]
        story.append(_table([["Calculation", "Granth", "Kyon"]] +
                            [[x.get("calculation", ""), x.get("source", ""), x.get("why", "")]
                             for x in plan], S))
        if gaps:
            story.append(Spacer(1, 6))
            story.append(Paragraph(_inl("Engine mein abhi nahi: " + "; ".join(
                f"{g.get('calculation', '')} ({g.get('source', '')})" for g in gaps)), S["small"]))
    story += [Spacer(1, 12), KeepTogether([Paragraph(_inl(
        "Ye reading kundli ke sanket batati hai; ye kisi bimari ka diagnosis, kanooni ya "
        "financial salaah nahi hai."), S["small"])])]

    def foot(c, d):
        c.saveState()
        c.setFont("DV", 8)
        c.setFillColor(colors.grey)
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(d.page))
        c.drawString(18 * mm, 10 * mm, footer)
        c.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=title,
                            author="HoraSutra")
    doc.build(story, onFirstPage=foot, onLaterPages=foot)
    return buf.getvalue()

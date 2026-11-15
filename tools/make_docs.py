"""Typeset the project documentation as a PDF.

    pip install reportlab
    python tools/make_docs.py [out.pdf]

The words live in tools/docs_content.py; this file only sets them. Add an entry there after a change
worth recording and run this again.

The look follows the app: the Akadian mark drawn straight from app/icons/mark.svg, the accent orange, and
the timeline hung off a rule in the left margin with a diamond at each entry — the app's own "you are here".
"""
import re
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import docs_content as C

ROOT = Path(__file__).resolve().parent.parent
MARK = ROOT / 'app/icons/mark.svg'

W, H = letter
LEFT, RIGHT, TOP, BOT = 64, 64, 64, 64
GUTTER = 86                      # the date column
RULE_X = LEFT + GUTTER
TEXT_X = RULE_X + 20
TEXT_W = W - RIGHT - TEXT_X

INK = HexColor("#15171c")
MUTED = HexColor("#596070")
FAINT = HexColor("#8b93a3")
ACCENT = HexColor("#d2600a")
RULE = HexColor("#d4dae3")
SPINE = HexColor("#bcc5d2")   # the timeline needs more weight than a hairline to read as one line
DARK = HexColor("#16181d")
PAPER = HexColor("#f2f3f5")
GLOW = HexColor("#f0a04a")

BODY, BOLD, ITAL = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
DISPLAY = "Times-Bold"


# ---------- the mark, straight out of the app's SVG ----------
def mark_shapes():
    """[(points, 'ink'|'accent')] in viewBox coordinates, plus (x0, y0, span)."""
    svg = MARK.read_text(encoding="utf-8")
    x0, y0, w, h = (float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split())
    out = []
    for d in re.findall(r'<path[^>]*\sd="([^"]+)"', svg):
        for part in filter(None, (p.strip() for p in d.split("Z"))):
            pts = [tuple(float(v) for v in pair.split())
                   for pair in re.findall(r"[ML]\s*([-\d.]+\s+[-\d.]+)", part)]
            if len(pts) > 2:
                out.append((pts, "ink"))
    for points in re.findall(r'<polygon[^>]*\spoints="([^"]+)"', svg):
        out.append(([tuple(float(v) for v in p.split(",")) for p in points.split()], "accent"))
    return out, (x0, y0, max(w, h))


SHAPES, (VX, VY, VSPAN) = mark_shapes()


def draw_mark(c, cx, cy, span, ink, accent):
    """The mark centred on (cx, cy), spanning `span` points. SVG y grows downward, PDF y upward."""
    k = span / VSPAN
    ox, oy = cx - (VX + VSPAN / 2) * k, cy + (VY + VSPAN / 2) * k
    for pts, role in SHAPES:
        p = c.beginPath()
        for i, (x, y) in enumerate(pts):
            (p.moveTo if i == 0 else p.lineTo)(ox + x * k, oy - y * k)
        p.close()
        c.setFillColor(accent if role == "accent" else ink)
        c.drawPath(p, stroke=0, fill=1)


def diamond(c, cx, cy, r, fill):
    p = c.beginPath()
    p.moveTo(cx, cy + r)
    p.lineTo(cx + r, cy)
    p.lineTo(cx, cy - r)
    p.lineTo(cx - r, cy)
    p.close()
    c.setFillColor(fill)
    c.drawPath(p, stroke=0, fill=1)


def tracked(c, x, y, text, font, size, space, color):
    """Letterspaced text, for the small caps-and-tracking labels.

    Advanced a glyph at a time rather than through the canvas or text object, because where character
    spacing lives has moved between reportlab versions and this needs neither.
    """
    c.setFont(font, size)
    c.setFillColor(color)
    for ch in text:
        c.drawString(x, y, ch)
        x += c.stringWidth(ch, font, size) + space


def tracked_w(c, text, font, size, space):
    return c.stringWidth(text, font, size) + space * max(len(text) - 1, 0)


# ---------- the page ----------
class Doc:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=letter)
        self.c.setTitle(f"{C.TITLE} — {C.SUB}")
        self.c.setAuthor("Akadian")
        self.c.setSubject(C.SUB)
        self.page = 0
        self.y = 0
        self.rule_from = None     # top of the open timeline rule segment on this page
        self.nodes = []           # where this page's diamonds sit on that rule

    # -- text --
    def wrap(self, text, font, size, width):
        words, lines, line = text.split(), [], ""
        for word in words:
            trial = f"{line} {word}".strip()
            if self.c.stringWidth(trial, font, size) <= width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    # -- pagination --
    def room(self, need):
        if self.y - need < BOT + 8:
            self.end_page()
            self.start_page()

    def start_page(self):
        self.page += 1
        self.y = H - TOP - 10
        c = self.c
        tracked(c, LEFT, H - TOP + 14, "AKADIAN VERTEX", BODY, 6.6, 1.5, FAINT)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(LEFT, H - TOP + 6, W - RIGHT, H - TOP + 6)
        c.setFont(BODY, 7.4)
        c.setFillColor(FAINT)
        c.drawRightString(W - RIGHT, BOT - 18, str(self.page))
        self.rule_from = None
        self.nodes = []

    def end_page(self):
        self.close_rule()
        self.c.showPage()

    # -- the timeline rule --
    def open_rule(self):
        if self.rule_from is None:
            self.rule_from = self.y + 12

    def close_rule(self):
        if self.rule_from is not None and self.rule_from > self.y:
            self.c.setStrokeColor(SPINE)
            self.c.setLineWidth(1.1)
            self.c.line(RULE_X, self.rule_from, RULE_X, max(self.y, BOT + 10))
        for y in self.nodes:  # over the rule, each in its own gap
            self.c.setFillColor(HexColor("#ffffff"))
            self.c.circle(RULE_X, y, 5.4, stroke=0, fill=1)
            diamond(self.c, RULE_X, y, 3.6, ACCENT)
        self.rule_from = None
        self.nodes = []

    def save(self):
        self.close_rule()
        self.c.save()


# ---------- the pieces ----------
def cover(d):
    c = d.c
    d.page += 1
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    draw_mark(c, W / 2, H * 0.685, 156, PAPER, GLOW)

    wm = "AKADIAN"
    x = (W - tracked_w(c, wm, DISPLAY, 17, 7)) / 2
    tracked(c, x, H * 0.555, wm, DISPLAY, 17, 7, PAPER)
    wm = "VERTEX"
    x = (W - tracked_w(c, wm, DISPLAY, 17, 7)) / 2
    tracked(c, x, H * 0.555 - 24, wm, DISPLAY, 17, 7, GLOW)

    c.setStrokeColor(HexColor("#353943"))
    c.setLineWidth(0.8)
    c.line(W / 2 - 60, H * 0.455, W / 2 + 60, H * 0.455)

    c.setFillColor(PAPER)
    c.setFont(DISPLAY, 27)
    c.drawCentredString(W / 2, H * 0.385, C.SUB)

    c.setFont(BODY, 10.4)
    c.setFillColor(HexColor("#9aa0aa"))
    c.drawCentredString(W / 2, H * 0.345, "A 3D campus map for George Mason University and Virginia Tech")
    c.drawCentredString(W / 2, H * 0.345 - 16, "with indoor maps and room-level walking directions")

    diamond(c, W / 2, H * 0.245, 4, GLOW)

    lab = C.DATE.upper()
    tracked(c, (W - tracked_w(c, lab, BODY, 8, 2.4)) / 2, H * 0.195, lab, BODY, 8, 2.4, HexColor("#9aa0aa"))
    c.setFont(BODY, 8.4)
    c.setFillColor(HexColor("#6f7681"))
    c.drawCentredString(W / 2, BOT, C.REPO)
    c.showPage()


def heading(d, text, kicker=None):
    c = d.c
    d.close_rule()
    d.room(96)
    d.y -= 14
    if kicker:
        tracked(c, LEFT, d.y, kicker.upper(), BODY, 7, 2, ACCENT)
        d.y -= 15
    c.setFont(DISPLAY, 20)
    c.setFillColor(INK)
    c.drawString(LEFT, d.y, text)
    d.y -= 11
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.6)
    c.line(LEFT, d.y, LEFT + 34, d.y)
    d.y -= 24


def entry(d, date, head, sha, paras, meta):
    c = d.c
    # keep the date, the heading and the first two lines of body together
    first = d.wrap(paras[0], BODY, 9.6, TEXT_W)[:2]
    need = 20 + len(d.wrap(head, BOLD, 11.6, TEXT_W)) * 15 + len(first) * 14.2 + 14
    if d.y - need < BOT + 8:
        d.end_page()
        d.start_page()
    d.open_rule()

    top = d.y
    tracked(c, LEFT, top, date.upper(), BOLD, 8.2, 1.4, INK)
    c.setFont(BODY, 7.4)
    c.setFillColor(FAINT)
    c.drawString(LEFT, top - 12, sha)

    d.nodes.append(top + 3)  # drawn with the rule, once the page is done

    c.setFillColor(INK)
    for line in d.wrap(head, BOLD, 11.6, TEXT_W):
        c.setFont(BOLD, 11.6)
        c.drawString(TEXT_X, d.y, line)
        d.y -= 15
    d.y -= 3

    for i, p in enumerate(paras):
        for line in d.wrap(p, BODY, 9.6, TEXT_W):
            if d.y - 14.2 < BOT + 8:
                d.end_page()
                d.start_page()
                d.open_rule()
            c.setFont(BODY, 9.6)
            c.setFillColor(MUTED)
            c.drawString(TEXT_X, d.y, line)
            d.y -= 14.2
        if i < len(paras) - 1:
            d.y -= 5

    d.y -= 3
    c.setFont(BODY, 7.6)
    c.setFillColor(FAINT)
    c.drawString(TEXT_X, d.y, meta)
    d.y -= 26


def defs(d, items, label_font=BOLD, label_size=9.6):
    """A run of term-and-explanation blocks, the term set in bold on its own first line."""
    c = d.c
    for term, body in items:
        lines = d.wrap(body, BODY, 9.6, TEXT_W)
        if d.y - (16 + len(lines[:2]) * 14.2) < BOT + 8:
            d.end_page()
            d.start_page()
        diamond(c, LEFT + 4, d.y + 3, 2.6, ACCENT)
        c.setFont(label_font, label_size)
        c.setFillColor(INK)
        c.drawString(LEFT + 14, d.y, term)
        d.y -= 15
        for line in lines:
            if d.y - 14.2 < BOT + 8:
                d.end_page()
                d.start_page()
            c.setFont(BODY, 9.6)
            c.setFillColor(MUTED)
            c.drawString(LEFT + 14, d.y, line)
            d.y -= 14.2
        d.y -= 12


def build(out):
    d = Doc(out)
    cover(d)

    d.start_page()
    heading(d, "What this is", kicker="Overview")
    for p in C.INTRO:
        for line in d.wrap(p, BODY, 10, W - LEFT - RIGHT):
            d.room(15)
            d.c.setFont(BODY, 10)
            d.c.setFillColor(MUTED)
            d.c.drawString(LEFT, d.y, line)
            d.y -= 15
        d.y -= 9

    heading(d, "How it is put together", kicker="Architecture")
    defs(d, C.PARTS, label_font=BOLD, label_size=9.6)

    heading(d, "The timeline", kicker=f"{len(C.TIMELINE)} entries · 24 commits")
    for e in C.TIMELINE:
        entry(d, *e)

    heading(d, "Decisions on record", kicker="The whys that are not in the code")
    defs(d, C.DECISIONS)

    heading(d, "How it is tested", kicker="Five suites, run on every change")
    defs(d, C.TESTS)

    heading(d, "Deliberately not built", kicker="And the reasons")
    defs(d, C.NOT_BUILT)

    d.room(70)
    d.y -= 10
    d.c.setStrokeColor(RULE)
    d.c.setLineWidth(0.5)
    d.c.line(LEFT, d.y, W - RIGHT, d.y)
    d.y -= 22
    for line in d.wrap(C.CLOSING, ITAL, 9.8, W - LEFT - RIGHT - 30):
        d.c.setFont(ITAL, 9.8)
        d.c.setFillColor(MUTED)
        d.c.drawString(LEFT, d.y, line)
        d.y -= 15
    d.y -= 8
    diamond(d.c, LEFT + 3, d.y, 3, ACCENT)

    d.end_page()
    d.save()
    return d.page


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'Akadian_Vertex_documentation.pdf'
    print(f"{out} — {build(out)} pages, {out.stat().st_size // 1024} KB")

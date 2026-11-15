"""Render a campaign master (.svg) to PNG and to print-ready PDF.

Two backends read the same master file, so what you see in the PNG is what the PDF prints:

    PNG   Pillow, at any scale. 300 DPI for print pieces (scale = 300/72), 1:1 for social.
          Social art is drawn at 2x and reduced, because Pillow has no antialiasing and the
          diagonals in the floor plates would otherwise stair-step at feed-post size.
    PDF   reportlab, in CMYK, at the master's own point size. Vector, no transparency, which is
          what a print shop wants.

Fonts. Display type is Cinzel 600, the app's own wordmark face, bundled at
app/vendor/fonts/cinzel-600-latin.woff2. FreeType reads woff2, so the PNGs use the real face;
reportlab cannot register a woff2, so the PDF falls back to the best serif on the machine. The PNGs
are therefore the master for print -- see campaign/README.md.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brand
from svgdoc import parse

# ---------------------------------------------------------------- fonts
# First file that exists wins. The repo's own Cinzel leads for display; the sans candidates end in
# the Bitstream Vera faces that ship inside reportlab, so a bare machine still renders.
_VERA = Path(pdfmetrics.__file__).resolve().parent / "fonts"
WIN = Path("C:/Windows/Fonts")
MAC = Path("/System/Library/Fonts")
LIN = Path("/usr/share/fonts/truetype")

CANDIDATES = {
    "Cinzel": [brand.CINZEL, WIN / "constanb.ttf", WIN / "georgiab.ttf", WIN / "timesbd.ttf",
               MAC / "Supplemental/Georgia Bold.ttf", LIN / "dejavu/DejaVuSerif-Bold.ttf",
               _VERA / "VeraBd.ttf"],
    "Sans": [WIN / "segoeui.ttf", MAC / "Helvetica.ttc", LIN / "dejavu/DejaVuSans.ttf",
             _VERA / "Vera.ttf"],
    "Sans-Bold": [WIN / "segoeuib.ttf", MAC / "Supplemental/Arial Bold.ttf",
                  LIN / "dejavu/DejaVuSans-Bold.ttf", _VERA / "VeraBd.ttf"],
    "Sans-Black": [WIN / "seguibl.ttf", WIN / "segoeuib.ttf", MAC / "Supplemental/Arial Black.ttf",
                   LIN / "dejavu/DejaVuSans-Bold.ttf", _VERA / "VeraBd.ttf"],
}
# reportlab needs a TTF it can parse and embed; woff2 is compressed and it cannot.
PDF_SKIP_SUFFIX = {".woff2", ".woff", ".ttc"}


def _resolve(family, for_pdf):
    for p in CANDIDATES[family]:
        if p.exists() and not (for_pdf and p.suffix.lower() in PDF_SKIP_SUFFIX):
            return p
    raise RuntimeError("no font found for %r -- install a serif/sans or reinstall reportlab" % family)


def font_report():
    """What each family resolved to, so make_campaign.py can say so out loud."""
    return {fam: (_resolve(fam, False).name, _resolve(fam, True).name) for fam in CANDIDATES}


_PIL_CACHE = {}


def _pil_font(family, size):
    key = (family, round(size, 2))
    if key not in _PIL_CACHE:
        _PIL_CACHE[key] = ImageFont.truetype(str(_resolve(family, False)), max(1, round(size)))
    return _PIL_CACHE[key]


def measure(family, size, text, tracking=0.0):
    """Width of a string in user units, as the PNG renderer will set it. Layout decisions (wrapping,
    fitting a headline to a column) are made with these numbers so the art is sized by real metrics
    rather than guessed character widths."""
    f = _pil_font(family, 100)          # measure big, scale down: FreeType sizes are integers
    w = sum(f.getlength(ch) for ch in text) * size / 100.0
    return w + tracking * max(len(text) - 1, 0)


def fit_size(family, text, max_width, start, tracking_em=0.0, floor=6.0):
    """The largest size at or below `start` at which `text` fits `max_width`."""
    size = start
    while size > floor and measure(family, size, text, tracking_em * size) > max_width:
        size -= 0.5
    return size


def wrap(family, size, text, max_width, tracking=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and measure(family, size, trial, tracking) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


_PDF_REGISTERED = {}


def _pdf_font(family):
    if family not in _PDF_REGISTERED:
        path = _resolve(family, True)
        name = "cmp-" + family
        pdfmetrics.registerFont(TTFont(name, str(path)))
        _PDF_REGISTERED[family] = name
    return _PDF_REGISTERED[family]


# ---------------------------------------------------------------- colour
def cmyk(hex_):
    """A hex colour as CMYK. Three brand colours are hand-set (brand.CMYK_OVERRIDES); the rest
    convert by the usual grey-component formula, which is what a press expects for flat art."""
    h = (hex_ or "#000000").lower()
    if h in brand.CMYK_OVERRIDES:
        c, m, y, k = brand.CMYK_OVERRIDES[h]
    else:
        r, g, b = (v / 255 for v in brand.rgb(h))
        k = 1 - max(r, g, b)
        if k >= 1:
            c = m = y = 0.0
        else:
            c, m, y = ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k))
    return CMYKColor(round(c, 4), round(m, 4), round(y, 4), round(k, 4))


# ---------------------------------------------------------------- shared text metrics
def _tracked_runs(el, measure):
    """[(x, char)] for one text element, honouring letter-spacing and text-anchor.

    Letterspaced text is advanced a glyph at a time rather than handed to the backend, because
    tracking lives in a different place in every renderer and this needs none of them.
    """
    s, track = el["s"], el.get("letter-spacing") or 0.0
    widths = [measure(ch) for ch in s]
    total = sum(widths) + track * max(len(s) - 1, 0)
    anchor = el.get("text-anchor") or "start"
    x = el["x"] - (total / 2 if anchor == "middle" else total if anchor == "end" else 0)
    out = []
    for ch, w in zip(s, widths):
        out.append((x, ch))
        x += w + track
    return out


def _dash_segments(pts, pattern, width):
    """A polyline split into dashes. Pillow draws no dash pattern, so do it here and the PNG and the
    PDF agree on where the gaps fall."""
    pat = [float(v) for v in pattern.replace(",", " ").split()]
    if not pat:
        return [pts]
    pat = pat * (2 if len(pat) % 2 else 1)
    out, seg, idx, left, on = [], [], 0, pat[0], True
    cur = pts[0]
    if on:
        seg = [cur]
    for nxt in pts[1:]:
        dx, dy = nxt[0] - cur[0], nxt[1] - cur[1]
        dist = (dx * dx + dy * dy) ** 0.5
        while dist > left:
            t = left / dist if dist else 0
            mid = (cur[0] + dx * t, cur[1] + dy * t)
            if on:
                seg.append(mid)
                out.append(seg)
                seg = []
            else:
                seg = [mid]
            cur, dx, dy, dist = mid, nxt[0] - mid[0], nxt[1] - mid[1], dist - left
            on = not on
            idx = (idx + 1) % len(pat)
            left = pat[idx]
        left -= dist
        cur = nxt
        if on:
            seg.append(cur)
    if on and len(seg) > 1:
        out.append(seg)
    return out


# ---------------------------------------------------------------- PNG
def render_png(svg_path, out_path, dpi=None, supersample=1):
    w, h, els = parse(Path(svg_path).read_text(encoding="utf-8"))
    scale = (dpi / 72.0) if dpi else 1.0
    s = scale * supersample
    px = (max(1, round(w * s)), max(1, round(h * s)))
    img = Image.new("RGB", px, brand.rgb("#ffffff"))
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * s, y * s)

    def col(c):
        return brand.rgb(c) if c and c != "none" else None

    for el in els:
        t = el["t"]
        fill, stroke = col(el.get("fill")), col(el.get("stroke"))
        sw = max(1, round((el.get("stroke-width") or 0) * s)) if el.get("stroke") else 0
        if t == "rect":
            box = [P(el["x"], el["y"]), P(el["x"] + el["width"], el["y"] + el["height"])]
            if el.get("rx"):
                d.rounded_rectangle(box, radius=el["rx"] * s, fill=fill, outline=stroke, width=sw)
            else:
                d.rectangle(box, fill=fill, outline=stroke, width=sw)
        elif t in ("polygon", "path"):
            pts = [P(*p) for p in el["points"]]
            if len(pts) > 2:
                if fill:
                    d.polygon(pts, fill=fill)
                if stroke:
                    d.line(pts + [pts[0]], fill=stroke, width=sw, joint="curve")
        elif t == "polyline":
            pts = [P(*p) for p in el["points"]]
            runs = _dash_segments(pts, el["stroke-dasharray"], sw) if el.get("stroke-dasharray") else [pts]
            for run in runs:
                if len(run) > 1:
                    d.line(run, fill=stroke, width=sw, joint="curve")
                    if (el.get("stroke-linecap") or "round") == "round" and sw > 2:
                        for x, y in (run[0], run[-1]):
                            d.ellipse([x - sw / 2, y - sw / 2, x + sw / 2, y + sw / 2], fill=stroke)
        elif t == "line":
            pts = [P(el["x1"], el["y1"]), P(el["x2"], el["y2"])]
            runs = _dash_segments(pts, el["stroke-dasharray"], sw) if el.get("stroke-dasharray") else [pts]
            for run in runs:
                d.line(run, fill=stroke, width=sw)
        elif t == "circle":
            cx, cy = P(el["cx"], el["cy"])
            r = el["r"] * s
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=stroke, width=sw)
        elif t == "text":
            f = _pil_font(el["font-family"], el["font-size"] * s)
            track = (el.get("letter-spacing") or 0.0) * s
            scaled = dict(el, x=el["x"] * s, **{"letter-spacing": track})
            for x, ch in _tracked_runs(scaled, lambda c: f.getlength(c)):
                d.text((x, el["y"] * s), ch, font=f, fill=fill, anchor="ls")

    if supersample > 1:
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", dpi=(round(dpi or 72), round(dpi or 72)))
    return img.size


# ---------------------------------------------------------------- PDF
def render_pdf(svg_path, out_path):
    w, h, els = parse(Path(svg_path).read_text(encoding="utf-8"))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=(w, h))
    c.setTitle(Path(svg_path).stem)

    def Y(y):
        return h - y          # SVG y grows down, PDF y grows up

    for el in els:
        t = el["t"]
        has_fill = el.get("fill") and el["fill"] != "none"
        has_stroke = el.get("stroke") and el["stroke"] != "none"
        if has_fill:
            c.setFillColor(cmyk(el["fill"]))
        if has_stroke:
            c.setStrokeColor(cmyk(el["stroke"]))
            c.setLineWidth(el.get("stroke-width") or 1)
            c.setLineCap({"butt": 0, "round": 1, "square": 2}[el.get("stroke-linecap") or "butt"])
            c.setLineJoin({"miter": 0, "round": 1, "bevel": 2}[el.get("stroke-linejoin") or "miter"])
            c.setDash([float(v) for v in el["stroke-dasharray"].replace(",", " ").split()]
                      if el.get("stroke-dasharray") else [], 0)
        if t == "rect":
            args = (el["x"], Y(el["y"] + el["height"]), el["width"], el["height"])
            if el.get("rx"):
                c.roundRect(*args, el["rx"], stroke=int(bool(has_stroke)), fill=int(bool(has_fill)))
            else:
                c.rect(*args, stroke=int(bool(has_stroke)), fill=int(bool(has_fill)))
        elif t in ("polygon", "path"):
            p = c.beginPath()
            for i, (x, y) in enumerate(el["points"]):
                (p.moveTo if i == 0 else p.lineTo)(x, Y(y))
            p.close()
            c.drawPath(p, stroke=int(bool(has_stroke)), fill=int(bool(has_fill)))
        elif t == "polyline":
            p = c.beginPath()
            for i, (x, y) in enumerate(el["points"]):
                (p.moveTo if i == 0 else p.lineTo)(x, Y(y))
            c.drawPath(p, stroke=1, fill=0)
        elif t == "line":
            c.line(el["x1"], Y(el["y1"]), el["x2"], Y(el["y2"]))
        elif t == "circle":
            c.circle(el["cx"], Y(el["cy"]), el["r"],
                     stroke=int(bool(has_stroke)), fill=int(bool(has_fill)))
        elif t == "text":
            name = _pdf_font(el["font-family"])
            size = el["font-size"]
            c.setFont(name, size)
            for x, ch in _tracked_runs(el, lambda ch: c.stringWidth(ch, name, size)):
                c.drawString(x, Y(el["y"]), ch)
    c.showPage()
    c.save()
    return (w, h)

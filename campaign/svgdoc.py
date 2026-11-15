"""A small SVG writer and reader for the campaign masters.

The .svg files in posters/, flyers/ and social/ are the masters: they are what you open in Illustrator
or Inkscape to nudge something, and they are what the PNG and PDF renderers read. Both sides of that
round trip live here, so the subset stays honest -- if a design cannot be written by this module, it
cannot be rendered either.

The subset is deliberately flat: rect, polygon, polyline, line, circle, path (M/L/Z only) and text.
No gradients, no opacity, no transforms, no clipping. Tints are mixed in Python with brand.mix(), so
every fill is a solid colour. That keeps the PNG renderer simple and gives a printer a file with no
transparency to flatten.
"""
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

NS = "http://www.w3.org/2000/svg"


def _n(v):
    """Numbers short enough to read in a text editor."""
    return ("%.3f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def _attrs(pairs):
    return " ".join('%s="%s"' % (k, _n(v) if isinstance(v, (int, float)) else v) for k, v in pairs)


class Doc:
    """A canvas in user units. Print pieces are authored in points (72 per inch), social in pixels."""

    def __init__(self, width, height, note=""):
        self.w, self.h = float(width), float(height)
        self.note = note
        self.els = []

    # ---------------- shapes
    def rect(self, x, y, w, h, fill="none", rx=None, stroke=None, stroke_width=None):
        e = {"t": "rect", "x": x, "y": y, "width": w, "height": h, "fill": fill}
        if rx:
            e["rx"] = rx
        if stroke:
            e["stroke"], e["stroke-width"] = stroke, stroke_width or 1
        self.els.append(e)
        return self

    def polygon(self, pts, fill="none", stroke=None, stroke_width=None):
        e = {"t": "polygon", "points": list(pts), "fill": fill}
        if stroke:
            e["stroke"], e["stroke-width"] = stroke, stroke_width or 1
        self.els.append(e)
        return self

    def polyline(self, pts, stroke, stroke_width, dash=None, cap="round", join="round"):
        self.els.append({"t": "polyline", "points": list(pts), "fill": "none", "stroke": stroke,
                         "stroke-width": stroke_width, "stroke-dasharray": dash,
                         "stroke-linecap": cap, "stroke-linejoin": join})
        return self

    def line(self, x1, y1, x2, y2, stroke, stroke_width=1, dash=None, cap="butt"):
        self.els.append({"t": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": stroke,
                         "stroke-width": stroke_width, "stroke-dasharray": dash,
                         "stroke-linecap": cap})
        return self

    def circle(self, cx, cy, r, fill="none", stroke=None, stroke_width=None):
        e = {"t": "circle", "cx": cx, "cy": cy, "r": r, "fill": fill}
        if stroke:
            e["stroke"], e["stroke-width"] = stroke, stroke_width or 1
        self.els.append(e)
        return self

    def path(self, pts, fill):
        """A closed M/L/Z subpath -- what the mark is made of."""
        self.els.append({"t": "path", "points": list(pts), "fill": fill})
        return self

    def text(self, x, y, s, family, size, fill, tracking=0.0, anchor="start", weight=None):
        """`y` is the baseline. `tracking` is extra advance per glyph, in user units."""
        self.els.append({"t": "text", "x": x, "y": y, "s": s, "font-family": family,
                         "font-size": size, "fill": fill, "letter-spacing": tracking,
                         "text-anchor": anchor, "font-weight": weight})
        return self

    # ---------------- serialise
    def tostring(self):
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<svg xmlns="%s" width="%s" height="%s" viewBox="0 0 %s %s">'
               % (NS, _n(self.w), _n(self.h), _n(self.w), _n(self.h))]
        if self.note:
            out.append("<!-- %s -->" % self.note.replace("--", "-"))
        for e in self.els:
            out.append(self._el(e))
        out.append("</svg>")
        return "\n".join(out) + "\n"

    @staticmethod
    def _el(e):
        t = e["t"]
        if t == "text":
            a = [("x", e["x"]), ("y", e["y"]), ("font-family", e["font-family"]),
                 ("font-size", e["font-size"]), ("fill", e["fill"])]
            if e.get("letter-spacing"):
                a.append(("letter-spacing", e["letter-spacing"]))
            if e.get("text-anchor", "start") != "start":
                a.append(("text-anchor", e["text-anchor"]))
            if e.get("font-weight"):
                a.append(("font-weight", e["font-weight"]))
            return "<text %s>%s</text>" % (_attrs(a), escape(e["s"]))
        if t in ("polygon", "polyline"):
            pts = " ".join("%s,%s" % (_n(x), _n(y)) for x, y in e["points"])
            a = [("points", pts)] + [(k, e[k]) for k in
                                     ("fill", "stroke", "stroke-width", "stroke-dasharray",
                                      "stroke-linecap", "stroke-linejoin") if e.get(k)]
            return "<%s %s/>" % (t, _attrs(a))
        if t == "path":
            d = " ".join(("M" if i == 0 else "L") + " %s %s" % (_n(x), _n(y))
                         for i, (x, y) in enumerate(e["points"])) + " Z"
            return '<path d="%s" fill="%s"/>' % (d, e["fill"])
        keys = {"rect": ("x", "y", "width", "height", "rx", "fill", "stroke", "stroke-width"),
                "line": ("x1", "y1", "x2", "y2", "stroke", "stroke-width", "stroke-dasharray",
                         "stroke-linecap"),
                "circle": ("cx", "cy", "r", "fill", "stroke", "stroke-width")}[t]
        return "<%s %s/>" % (t, _attrs([(k, e[k]) for k in keys if e.get(k) is not None]))

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.tostring(), encoding="utf-8")
        return path


# ---------------------------------------------------------------- reading a master back
def _pts(s):
    vals = [p for p in s.replace(",", " ").split() if p]
    return [(float(vals[i]), float(vals[i + 1])) for i in range(0, len(vals) - 1, 2)]


def parse(svg_text):
    """A master file as (width, height, [element dicts]) -- the same dicts Doc builds."""
    root = ET.fromstring(svg_text)
    w, h = float(root.get("width")), float(root.get("height"))
    els = []
    for node in root:
        tag = node.tag.split("}")[-1]
        g = node.get

        def f(k, d=None, g=g):
            return float(g(k)) if g(k) is not None else d

        if tag == "rect":
            els.append({"t": "rect", "x": f("x"), "y": f("y"), "width": f("width"),
                        "height": f("height"), "rx": f("rx"), "fill": g("fill"),
                        "stroke": g("stroke"), "stroke-width": f("stroke-width")})
        elif tag in ("polygon", "polyline"):
            els.append({"t": tag, "points": _pts(g("points")), "fill": g("fill"),
                        "stroke": g("stroke"), "stroke-width": f("stroke-width"),
                        "stroke-dasharray": g("stroke-dasharray"),
                        "stroke-linecap": g("stroke-linecap"),
                        "stroke-linejoin": g("stroke-linejoin")})
        elif tag == "line":
            els.append({"t": "line", "x1": f("x1"), "y1": f("y1"), "x2": f("x2"), "y2": f("y2"),
                        "stroke": g("stroke"), "stroke-width": f("stroke-width"),
                        "stroke-dasharray": g("stroke-dasharray"),
                        "stroke-linecap": g("stroke-linecap")})
        elif tag == "circle":
            els.append({"t": "circle", "cx": f("cx"), "cy": f("cy"), "r": f("r"), "fill": g("fill"),
                        "stroke": g("stroke"), "stroke-width": f("stroke-width")})
        elif tag == "path":
            pts = [tuple(float(v) for v in m.split())
                   for m in re.findall(r"[ML]\s*([-\d.]+\s+[-\d.]+)", g("d"))]
            els.append({"t": "path", "points": pts, "fill": g("fill")})
        elif tag == "text":
            els.append({"t": "text", "x": f("x"), "y": f("y"), "s": node.text or "",
                        "font-family": g("font-family"), "font-size": f("font-size"),
                        "fill": g("fill"), "letter-spacing": f("letter-spacing", 0.0),
                        "text-anchor": g("text-anchor") or "start", "font-weight": g("font-weight")})
    return w, h, els

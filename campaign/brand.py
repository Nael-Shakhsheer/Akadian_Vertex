"""The Akadian Vertex brand, as the campaign needs it: palette, the mark, type and real campus geometry.

Nothing here is invented. The colours come from app/js/themes.js, the mark is parsed out of
app/icons/mark.svg the same way tools/make_docs.py does it, and the floor plans and counts are read
from the app's own data files at build time, so a poster can never drift from what the app ships.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK_SVG = ROOT / "app/icons/mark.svg"
CINZEL = ROOT / "app/vendor/fonts/cinzel-600-latin.woff2"
JC_DATA = ROOT / "docs/data/buildings/gmu-jc.json"
CAMPUS_DATA = ROOT / "docs/data/campus/gmu.json"

# ---------------------------------------------------------------- palette
# Straight out of app/js/themes.js. "dark" is the house look; "light" is the paper look.
DARK = {
    "bg": "#16181d", "surface": "#1c1f25", "card": "#262931", "raised": "#2d3038",
    "line": "#353943", "text": "#f2f3f5", "muted": "#9aa0aa", "accent": "#f0a04a",
}
LIGHT = {
    "bg": "#ffffff", "surface": "#f6f7f9", "card": "#ffffff", "raised": "#e9ecf1",
    "line": "#15181e", "text": "#15171c", "muted": "#596070", "accent": "#d2600a",
}

# Hand-set CMYK for the three colours that matter most in print; everything else is converted by
# formula at render time (see campaign/render.py). Documented in campaign/README.md.
#   bg      a rich black, so a large dark area does not go flat or brown on a press
#   text    knocked out to paper, so small light type on dark stays crisp instead of printing a tint
#   ink     black plate only, so small dark type cannot go fuzzy from misregistration
CMYK_OVERRIDES = {
    "#16181d": (0.60, 0.40, 0.40, 1.00),
    "#f2f3f5": (0.00, 0.00, 0.00, 0.00),
    "#15171c": (0.00, 0.00, 0.00, 0.92),
}


def rgb(hex_):
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexstr(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, round(r))), max(0, min(255, round(g))), max(0, min(255, round(b))))


def mix(a, b, t):
    """Blend two hex colours, t=0 keeps a. Used instead of opacity so every fill stays flat and
    solid — no transparency for a printer to flatten, and no alpha for the PNG renderer to composite."""
    (r1, g1, b1), (r2, g2, b2) = rgb(a), rgb(b)
    return hexstr(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


# ---------------------------------------------------------------- the mark
def mark_shapes():
    """[(points, 'ink'|'accent')] in viewBox coordinates, plus (x0, y0, span).

    The same parse tools/make_docs.py uses: the mark is pure M/L/Z subpaths plus one accent polygon,
    so it needs no curve support and never has to be redrawn by hand.
    """
    svg = MARK_SVG.read_text(encoding="utf-8")
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


def mark_polys(cx, cy, span):
    """The mark centred on (cx, cy) spanning `span` user units: [(points, role)] ready to draw."""
    k = span / VSPAN
    ox, oy = cx - (VX + VSPAN / 2) * k, cy - (VY + VSPAN / 2) * k
    return [([(ox + x * k, oy + y * k) for x, y in pts], role) for pts, role in SHAPES]


# ---------------------------------------------------------------- type
# Display is Cinzel 600, the app's own wordmark face, bundled in the repo. The PNG renderer reads the
# woff2 directly through FreeType; reportlab cannot, so the PDF falls back to the first serif it finds
# (see FONTS in campaign/render.py and the note in campaign/README.md).
FAMILY_DISPLAY = "Cinzel"
FAMILY_SANS = "Sans"
FAMILY_SANS_BOLD = "Sans-Bold"
FAMILY_SANS_BLACK = "Sans-Black"


# ---------------------------------------------------------------- real campus geometry
_JC_RAW = None


def jc_raw():
    """The Johnson Center data file, loaded once."""
    global _JC_RAW
    if _JC_RAW is None:
        _JC_RAW = json.loads(JC_DATA.read_text(encoding="utf-8"))
    return _JC_RAW


def jc_room(room_id):
    """One room by its real number, as the app has it."""
    return next((r for r in jc_raw()["rooms"] if r["id"] == room_id), None)


def jc_plan():
    """The Johnson Center's real indoor geometry and counts, read from the app's data.

    Returns a dict with the four floors (slab outline, room polygons, the walkable area) in plan
    coordinates, plus the counts the copy is allowed to quote.
    """
    d = json.loads(JC_DATA.read_text(encoding="utf-8"))

    def rings(entry):
        """A space/slab entry as [(outer, [holes])] with flat coordinate lists paired up."""
        pair = lambda flat: [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
        return pair(entry["o"]), [pair(h) for h in entry.get("h", [])]

    floors = []
    for f in d["floors"]:
        slab = [rings(s) for s in f["slab"]]
        rooms = [rings(s) for s in f["spaces"]]
        ids = {s["id"]: rings(s) for s in f["spaces"] if s.get("id")}
        floors.append({"id": f["id"], "name": f["name"], "level": f["level"],
                       "slab": slab, "rooms": rooms, "by_id": ids,
                       "walk": [rings(w) for w in f["walk"]]})

    study = [r for r in d["rooms"] if (r.get("name") or "") == "Group Study Room"]
    by_floor = {}
    for r in study:
        by_floor[r["floor"]] = by_floor.get(r["floor"], 0) + 1
    return {
        "floors": floors,
        "entrances": d["entrances"],
        "n_rooms": sum(1 for r in d["rooms"] if r.get("kind") == "room"),
        "n_study": len(study),
        "study_by_floor": by_floor,
        "study_ids": sorted(r["id"] for r in study),
    }


def campus_counts():
    """What the GMU campus layer actually holds, for any number the copy quotes."""
    d = json.loads(CAMPUS_DATA.read_text(encoding="utf-8"))
    t = d["transit"]
    return {"buildings": len(d["buildings"]), "food": len(d["food"]),
            "stops": len(t["stops"]), "lines": len(t["lines"])}


def centroid(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

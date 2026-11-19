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
# The George Mason buildings the app maps indoors, by the key the campaign uses for each.
BUILDING_DIR = ROOT / "docs/data/buildings"
BUILDINGS = {"jc": "gmu-jc.json", "research": "gmu-research.json",
             "merten": "gmu-merten.json", "hub": "gmu-hub.json"}
_RAW = {}


def building_raw(key):
    """A building's data file exactly as the app loads it, read once."""
    if key not in _RAW:
        _RAW[key] = json.loads((BUILDING_DIR / BUILDINGS[key]).read_text(encoding="utf-8"))
    return _RAW[key]


def building_room(key, room_id):
    """One room by its real number, as the app has it -- or None, so a caller can refuse to draw
    a room that does not exist."""
    return next((r for r in building_raw(key)["rooms"] if r["id"] == room_id), None)


def building_plan(key):
    """A building's floors (slab outline, room polygons, the walkable area) in plan coordinates."""
    d = building_raw(key)

    def rings(entry):
        """A space/slab entry as (outer, [holes]) with flat coordinate lists paired up."""
        pair = lambda flat: [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
        return pair(entry["o"]), [pair(h) for h in entry.get("h", [])]

    floors = [{"id": f["id"], "name": f["name"], "level": f["level"],
               "slab": [rings(x) for x in f["slab"]],
               "rooms": [rings(x) for x in f["spaces"]]} for f in d["floors"]]
    return {"key": key, "name": d["building"].get("name", key), "floors": floors,
            "entrances": d["entrances"], "mPerPx": d["mPerPx"]}


def indoor_counts():
    """What the app maps indoors at George Mason: how many buildings, how many rooms.

    Counted over every gmu-*.json the app ships, not just the ones the campaign draws, so a building
    added to the app changes these numbers -- and the build stops until the copy agrees.
    """
    files = sorted(BUILDING_DIR.glob("gmu-*.json"))
    rooms = 0
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        rooms += sum(1 for r in d["rooms"] if r.get("kind") == "room")
    named = json.loads((ROOT / "docs/data/campuses.json").read_text(encoding="utf-8"))
    gmu = next(c for c in named if c["id"] == "gmu")
    return {"buildings": len(files), "rooms": rooms, "named": gmu["indoor"]}


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

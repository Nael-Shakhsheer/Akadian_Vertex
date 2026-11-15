"""The campaign's shared furniture: themes, the logo lockup, the QR placeholder, chips, rules,
and the two pieces of real artwork -- the stacked Johnson Center floor plates and the study-room grid.

Every design in designs.py is assembled out of these, so a change to the lockup or the QR block
lands on all twenty-odd pieces at once.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brand
import render
import route
from brand import mix
from svgdoc import Doc

PT = 1.0                 # print pieces are authored in points
IN = 72.0                # points per inch

DISPLAY = brand.FAMILY_DISPLAY
SANS = brand.FAMILY_SANS
BOLD = brand.FAMILY_SANS_BOLD
BLACK = brand.FAMILY_SANS_BLACK

# The line every print piece carries. The app ships campus initials rather than anyone's marks, and
# the campaign says the same thing in words: this is a student project, not a university product.
DISCLAIMER = ("An independent student project. Not affiliated with, endorsed or sponsored by "
              "George Mason University.")


# ---------------------------------------------------------------- themes
def theme(name):
    """A palette plus the tints the layouts need, mixed flat so nothing relies on opacity."""
    if name == "dark":
        p = dict(brand.DARK)
        bg, ink = p["bg"], p["text"]
        p.update(panel=mix(bg, ink, 0.07), panel2=mix(bg, ink, 0.12), plate=mix(bg, ink, 0.13),
                 room=mix(bg, ink, 0.21), room_line=mix(bg, ink, 0.34), void=bg,
                 skirt=mix(bg, ink, 0.05), hairline=mix(bg, ink, 0.22),
                 accent_dim=mix(bg, p["accent"], 0.38), paper="#ffffff", paper_ink="#15171c")
    else:
        p = dict(brand.LIGHT)
        bg, ink = p["bg"], p["text"]
        p.update(panel=mix(bg, ink, 0.045), panel2=mix(bg, ink, 0.09), plate=mix(bg, ink, 0.05),
                 room="#ffffff", room_line=mix(bg, ink, 0.30), void=mix(bg, ink, 0.09),
                 skirt=mix(bg, ink, 0.11), hairline=mix(bg, ink, 0.18),
                 accent_dim=mix(bg, p["accent"], 0.22), paper="#ffffff", paper_ink="#15171c")
    p["name"] = name
    return p


# ---------------------------------------------------------------- type helpers
def head_size(lines, max_width, start, tracking_em=0.045):
    """The size at which the widest of these lines fits, measured as caps -- which is how it sets."""
    widest = max(lines, key=lambda t: render.measure(DISPLAY, 100, t.upper(), 100 * tracking_em))
    return render.fit_size(DISPLAY, widest.upper(), max_width, start, tracking_em)


def headline(d, x, y, lines, size, th, lead=1.06, tracking_em=0.04, anchor="start", fill=None):
    """Cinzel caps, the wordmark's own face, set as display type."""
    for i, s in enumerate(lines):
        d.text(x, y + i * size * lead, s.upper(), DISPLAY, size, fill or th["text"],
               tracking=size * tracking_em, anchor=anchor)
    return y + (len(lines) - 1) * size * lead


def paragraph(d, x, y, text, size, width, th, lead=1.42, fill=None, family=SANS, anchor="start"):
    lines = render.wrap(family, size, text, width)
    for i, s in enumerate(lines):
        d.text(x, y + i * size * lead, s, family, size, fill or th["muted"], anchor=anchor)
    return y + (len(lines) - 1) * size * lead


def label(d, x, y, s, size, th, fill=None, anchor="start", em=0.18, family=BOLD):
    """A small tracked cap line -- the app's own eyebrow style."""
    d.text(x, y, s.upper(), family, size, fill or th["muted"], tracking=size * em, anchor=anchor)


def rule(d, x, y, w, th, weight=0.75, colour=None):
    d.line(x, y, x + w, y, colour or th["hairline"], weight)


# ---------------------------------------------------------------- the lockup
def lockup(d, x, y, size, th, anchor="start", accent_vertex=True):
    """Mark + AKADIAN VERTEX, baseline-aligned, `size` being the cap height of AKADIAN.

    Returns the lockup's total width, so a layout can centre or right-align it.
    """
    gap = size * 0.52
    mark_span = size * 1.62
    big_track, small_track = size * 0.12, size * 0.40
    small = size * 0.60
    w_big = render.measure(DISPLAY, size, "AKADIAN", big_track)
    w_small = render.measure(DISPLAY, small, "VERTEX", small_track)
    total = mark_span * 0.62 + gap + w_big + size * 0.34 + w_small
    if anchor == "middle":
        x -= total / 2
    elif anchor == "end":
        x -= total
    for pts, role in brand.mark_polys(x + mark_span * 0.31, y - size * 0.40, mark_span):
        d.path(pts, th["accent"] if role == "accent" else th["text"])
    tx = x + mark_span * 0.62 + gap
    d.text(tx, y, "AKADIAN", DISPLAY, size, th["text"], tracking=big_track)
    d.text(tx + w_big + size * 0.34, y, "VERTEX", DISPLAY, small,
           th["accent"] if accent_vertex else th["text"], tracking=small_track)
    return total


def mark_tile(d, cx, cy, size, th, radius=None):
    """The mark on a dark rounded tile -- the app icon as it looks on a home screen."""
    d.rect(cx - size / 2, cy - size / 2, size, size, brand.DARK["bg"],
           rx=radius if radius is not None else size * 0.225)
    for pts, role in brand.mark_polys(cx, cy, size * 0.60):
        d.path(pts, brand.DARK["accent"] if role == "accent" else brand.DARK["text"])


# ---------------------------------------------------------------- QR placeholder
def qr_block(d, x, y, size, th, caption="Scan to open", sub="No app store. No install."):
    """A clearly marked stand-in for the real QR code.

    Always on a white panel with a quiet zone, because that is what a scanner needs and because a
    code dropped onto the dark artwork later would not read. Replace the panel's inside with the
    real code at the same box; see campaign/README.md.
    """
    pad = size * 0.085                      # the quiet zone a QR needs on all four sides
    d.rect(x, y, size, size, "#ffffff", rx=size * 0.045, stroke=th["hairline"],
           stroke_width=max(0.6, size * 0.008))
    inner, ix, iy = size - pad * 2, x + pad, y + pad
    ink = "#15171c"
    ghost = mix("#ffffff", ink, 0.17)
    # the three finder squares, so it reads as "a QR code goes here" from across a corridor
    f = inner * 0.26
    for fx, fy in ((ix, iy), (ix + inner - f, iy), (ix, iy + inner - f)):
        d.rect(fx, fy, f, f, "none", stroke=ghost, stroke_width=max(0.6, inner * 0.035))
        d.rect(fx + f * 0.30, fy + f * 0.30, f * 0.40, f * 0.40, ghost)
    d.rect(ix, iy, inner, inner, "none", stroke=ghost, stroke_width=max(0.5, inner * 0.012))
    t = inner * 0.082
    d.text(x + size / 2, iy + inner * 0.56, "QR", BLACK, t * 1.9, ghost,
           tracking=t * 0.5, anchor="middle")
    d.text(x + size / 2, iy + inner * 0.70, "PLACEHOLDER", BOLD, t * 0.92, ghost,
           tracking=t * 0.22, anchor="middle")
    if caption:
        d.text(x + size / 2, y + size + size * 0.165, caption, BOLD, size * 0.112, th["text"],
               anchor="middle")
    if sub:
        d.text(x + size / 2, y + size + size * 0.295, sub, SANS, size * 0.095, th["muted"],
               anchor="middle")
    return size + size * (0.33 if sub else 0.21 if caption else 0)


# ---------------------------------------------------------------- chips and feature rows
def chip(d, x, y, text, th, size=9, pad=None, fill=None, ink=None, border=None):
    """A rounded pill, the app's own chip row."""
    pad = pad if pad is not None else size * 0.95
    h = size * 2.25
    w = render.measure(BOLD, size, text, size * 0.04) + pad * 2
    d.rect(x, y, w, h, fill or th["panel2"], rx=h / 2, stroke=border, stroke_width=0.7 if border else None)
    d.text(x + pad, y + h * 0.66, text, BOLD, size, ink or th["text"], tracking=size * 0.04)
    return w


def feature(d, x, y, w, title, body, th, size=11, icon=None):
    """One column of the feature strip: a short accent rule, a title, two lines of plain English."""
    d.line(x, y, x + size * 2.0, y, th["accent"], max(1.4, size * 0.20))
    d.text(x, y + size * 1.85, title, BOLD, size * 1.06, th["text"])
    return paragraph(d, x, y + size * 3.25, body, size * 0.93, w, th, lead=1.38)


# ---------------------------------------------------------------- artwork: the floor stack
_PLAN = None
_ROUTE = None


def jc():
    global _PLAN
    if _PLAN is None:
        _PLAN = brand.jc_plan()
    return _PLAN


# The walk the artwork shows. 320H is a real, single group study room on the third floor (the plan
# leaves some of the suites undivided, so a room with its own four walls makes a truthful highlight),
# and entrance 0 is the north door, which gives the longest walk across the first floor.
DEST_ROOM = "320H"
DEST_ENTRANCE = 0
DEST_CAPTION = ("North entrance", "Group study room · Floor 3")


def jc_route():
    """The real walk: in the north door, across the first floor, up two floors, to room 320H."""
    global _ROUTE
    if _ROUTE is None:
        _ROUTE = route.jc_route(DEST_ROOM, from_entrance=DEST_ENTRANCE)
    return _ROUTE


class Iso:
    """Plan coordinates -> an axonometric view of the stacked floors, auto-fitted to a box."""

    def __init__(self, box, rot_deg=-24.0, squash=0.50, lift_frac=0.30, levels=4):
        self.rot = math.radians(rot_deg)
        self.squash = squash
        plan = jc()
        xs, ys = [], []
        for f in plan["floors"]:
            for outer, _ in f["slab"]:
                xs += [p[0] for p in outer]
                ys += [p[1] for p in outer]
        self.span_y = max(ys) - min(ys)
        self.lift = self.span_y * lift_frac
        pts = [self._raw(x, y, lv) for lv in range(levels) for x, y in
               ((min(xs), min(ys)), (max(xs), min(ys)), (min(xs), max(ys)), (max(xs), max(ys)))]
        px0 = min(p[0] for p in pts)
        px1 = max(p[0] for p in pts)
        py0 = min(p[1] for p in pts)
        py1 = max(p[1] for p in pts)
        bx, by, bw, bh = box
        self.s = min(bw / (px1 - px0), bh / (py1 - py0))
        self.ox = bx + (bw - (px1 - px0) * self.s) / 2 - px0 * self.s
        self.oy = by + (bh - (py1 - py0) * self.s) / 2 - py0 * self.s
        self.box = box

    def _raw(self, x, y, level):
        c, s = math.cos(self.rot), math.sin(self.rot)
        return (x * c - y * s, (x * s + y * c) * self.squash - level * self.lift)

    def __call__(self, x, y, level):
        rx, ry = self._raw(x, y, level)
        return (self.ox + rx * self.s, self.oy + ry * self.s)

    def ring(self, pts, level):
        return [self(x, y, level) for x, y in pts]


def floor_stack(d, iso, th, levels=(0, 1, 2, 3), show_route=True, show_rooms=True,
                floor_labels=True, label_size=8.0, callouts=True, thickness=0.028):
    """The Johnson Center's real floor plans, stacked. Plate, rooms, atrium voids, then the route.

    Geometry is read from docs/data/buildings/gmu-jc.json at build time; nothing here is traced or
    drawn by hand.
    """
    plan = jc()
    skirt = iso.span_y * thickness * iso.squash * iso.s
    legs, start_xy, goal_xy = jc_route() if show_route else (None, None, None)
    by_floor = {l["floor"]: l["pts"] for l in (legs or [])}
    level_of = {f["id"]: i for i, f in enumerate(plan["floors"])}
    goal_room = brand.jc_room(DEST_ROOM) if show_route else None

    # the plates, bottom up, so an upper floor overlaps the one below it
    for lv in levels:
        f = plan["floors"][lv]
        for outer, holes in f["slab"]:
            side = iso.ring(outer, lv)
            d.polygon([(x, y + skirt) for x, y in side], th["skirt"])
            d.polygon(side, th["plate"], stroke=th["hairline"], stroke_width=0.6)
            for h in holes:
                d.polygon(iso.ring(h, lv), th["void"])
        if show_rooms:
            for outer, holes in f["rooms"]:
                d.polygon(iso.ring(outer, lv), th["room"], stroke=th["room_line"], stroke_width=0.35)
                for h in holes:
                    d.polygon(iso.ring(h, lv), th["plate"])
        if goal_room is not None and level_of.get(goal_room["floor"]) == lv:
            d.polygon(iso.ring(goal_room["poly"], lv), th["accent_dim"],
                      stroke=th["accent"], stroke_width=max(0.5, iso.s * 3))
        if floor_labels:
            # hang the label off the plate's leftmost projected corner, across all its slab pieces
            proj = [p for outer, _ in f["slab"] for p in iso.ring(outer, lv)]
            lx, ly = min(proj, key=lambda p: p[0])
            label(d, lx - label_size * 1.1, ly + label_size * 0.34, f["name"], label_size, th,
                  fill=th["muted"], anchor="end", em=0.16)

    # the walk, drawn over the whole stack: an exploded view, so the path threads up through it
    if show_route and legs:
        wide = max(1.8, iso.s * 13)
        # a halo under the line, so a leg that passes over the plate above still reads as floating
        for i, leg in enumerate(legs):
            lv = level_of[leg["floor"]]
            if len(leg["pts"]) > 1:
                d.polyline(iso.ring(leg["pts"], lv), th["bg"], wide * 2.0, cap="round", join="round")
        for i, leg in enumerate(legs):
            lv = level_of[leg["floor"]]
            if len(leg["pts"]) > 1:
                d.polyline(iso.ring(leg["pts"], lv), th["accent"], wide, cap="round", join="round")
            if i + 1 < len(legs):
                nxt = legs[i + 1]
                a = iso(leg["pts"][-1][0], leg["pts"][-1][1], lv)
                b = iso(nxt["pts"][0][0], nxt["pts"][0][1], level_of[nxt["floor"]])
                d.polyline([a, b], th["accent"], wide * 0.62,
                           dash="%.1f %.1f" % (wide * 1.15, wide * 0.95), cap="round")
        sx, sy = iso(start_xy[0], start_xy[1], level_of[legs[0]["floor"]])
        gx, gy = iso(goal_xy[0], goal_xy[1], level_of[legs[-1]["floor"]])
        d.circle(sx, sy, wide * 1.05, th["bg"], stroke=th["accent"], stroke_width=wide * 0.5)
        diamond(d, gx, gy, wide * 2.1, th["accent"])
        if callouts:
            cs = max(6.5, iso.s * 34)
            label(d, sx, sy + cs * 1.75, DEST_CAPTION[0], cs, th, fill=th["text"], em=0.09)
            # the destination tag sits to the right of the marker unless that would run off the page
            tag_w = max(render.measure(BOLD, cs * 1.3, DEST_ROOM),
                        render.measure(BOLD, cs * 0.82, DEST_CAPTION[1].upper(), cs * 0.82 * 0.07))
            flip = gx + cs * 0.9 + tag_w > d.w - max(cs * 2.0, d.w * 0.045)
            tx, anchor = (gx - cs * 0.9, "end") if flip else (gx + cs * 0.9, "start")
            d.text(tx, gy - cs * 0.26, DEST_ROOM, BOLD, cs * 1.3, th["accent"], anchor=anchor)
            label(d, tx, gy + cs * 0.98, DEST_CAPTION[1], cs * 0.82, th,
                  fill=th["muted"], anchor=anchor, em=0.07)
    return legs


def diamond(d, cx, cy, r, fill):
    """The app's 'you are here' marker, the same diamond that sits inside the mark."""
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill)


# ---------------------------------------------------------------- artwork: the study-room grid
STUDY_ROWS = [("Floor 1", ["118", "119", "120"]),
              ("Floor 2", ["218", "219A", "219B", "219C", "219D", "226B", "226C", "226D"]),
              ("Floor 3", ["314", "315A", "315B", "315C", "315D", "320A", "320B", "320C",
                           "320D", "320E", "320F", "320H"])]


def study_grid(d, x, y, w, th, cols=6, gap=None, pick="320C", size=None, show_rows=True,
               max_tile=None):
    """Every group study room in the Johnson Center, by its real number, one tile each.

    The room numbers come from docs/data/buildings/gmu-jc.json -- the same 23 rooms the app routes to.
    """
    plan = jc()
    assert sum(len(ids) for _, ids in STUDY_ROWS) == plan["n_study"], "study-room list drifted from the data"
    gap = gap if gap is not None else w * 0.018
    tile = (w - gap * (cols - 1)) / cols
    if max_tile:
        tile = min(tile, max_tile)      # a cap, so the grid cannot grow taller than its slot
    size = size or tile * 0.30
    cy = y
    for floor_name, ids in STUDY_ROWS:
        if show_rows:
            label(d, x, cy, "%s · %d rooms" % (floor_name, len(ids)), size * 0.78, th, em=0.16)
            cy += size * 1.25
        for i, rid in enumerate(ids):
            col, row = i % cols, i // cols
            tx, ty = x + col * (tile + gap), cy + row * (tile * 0.74 + gap)
            hot = rid == pick
            d.rect(tx, ty, tile, tile * 0.74, th["accent"] if hot else th["panel"],
                   rx=tile * 0.10, stroke=None if hot else th["hairline"], stroke_width=0.7)
            d.text(tx + tile / 2, ty + tile * 0.47, rid, BOLD, size,
                   th["paper_ink"] if hot else th["text"], anchor="middle")
            if hot:
                diamond(d, tx + tile / 2, ty + tile * 0.62, size * 0.26, th["paper_ink"])
        rows = (len(ids) + cols - 1) // cols
        cy += rows * (tile * 0.74 + gap) + gap * 1.4
    return cy - gap * 1.4


# ---------------------------------------------------------------- artwork: offline + home screen
def phone(d, x, y, w, th, h=None, screen=None):
    """A phone outline with a dark screen, for the offline and home-screen concepts."""
    h = h or w * 2.02
    r = w * 0.135
    d.rect(x, y, w, h, th["line"] if th["name"] == "light" else mix(th["bg"], th["text"], 0.30), rx=r)
    pad = w * 0.022
    d.rect(x + pad, y + pad, w - pad * 2, h - pad * 2, screen or brand.DARK["bg"], rx=r - pad)
    d.rect(x + w * 0.36, y + pad * 2.1, w * 0.28, w * 0.055, mix(brand.DARK["bg"], "#000000", 0.5),
           rx=w * 0.028)
    return (x + pad * 2, y + w * 0.14, w - pad * 4, h - pad * 2 - w * 0.18)   # usable screen box


def no_signal(d, cx, cy, r, th, colour=None):
    """Signal arcs with a stroke through them: campus wi-fi, honestly depicted."""
    c = colour or th["muted"]
    for i in range(3):
        rr = r * (0.42 + i * 0.29)
        pts = [(cx + rr * math.cos(a), cy - rr * math.sin(a))
               for a in [math.radians(t) for t in range(28, 153, 6)]]
        d.polyline(pts, c, r * 0.11, cap="round")
    d.circle(cx, cy, r * 0.11, c)
    d.polyline([(cx - r * 0.86, cy + r * 0.52), (cx + r * 0.86, cy - r * 0.86)],
               th["accent"], r * 0.13, cap="round")


def home_grid(d, x, y, w, th, cols=4, rows=3, hot=(1, 1)):
    """A phone home screen of blank tiles with the Vertex icon dropped into one."""
    gap = w * 0.085
    tile = (w - gap * (cols - 1)) / cols
    for r in range(rows):
        for c in range(cols):
            tx, ty = x + c * (tile + gap), y + r * (tile + gap * 1.5)
            if (c, r) == hot:
                mark_tile(d, tx + tile / 2, ty + tile / 2, tile, th)
                d.rect(tx + tile / 2 - tile * 0.5, ty + tile / 2 - tile * 0.5, tile, tile, "none",
                       rx=tile * 0.225, stroke=th["accent"], stroke_width=max(0.8, tile * 0.045))
                d.text(tx + tile / 2, ty + tile + gap * 0.62, "Vertex", SANS, tile * 0.22,
                       mix(brand.DARK["bg"], brand.DARK["text"], 0.85), anchor="middle")
            else:
                d.rect(tx, ty, tile, tile, mix(brand.DARK["bg"], brand.DARK["text"], 0.09),
                       rx=tile * 0.225)
                d.rect(tx + tile * 0.18, ty + tile + gap * 0.40, tile * 0.64, tile * 0.075,
                       mix(brand.DARK["bg"], brand.DARK["text"], 0.13), rx=tile * 0.04)
    return y + rows * (tile + gap * 1.5)


def steps(d, x, y, w, items, th, size=11, lead=None):
    """Numbered steps in accent discs -- used for the add-to-home-screen pieces."""
    lead = lead or size * 3.1
    for i, (title, body) in enumerate(items):
        cy = y + i * lead
        r = size * 0.92
        d.circle(x + r, cy - size * 0.34, r, th["accent"])
        d.text(x + r, cy, str(i + 1), BLACK, size * 1.05, th["paper_ink"], anchor="middle")
        d.text(x + r * 2.9, cy - size * 0.30, title, BOLD, size * 1.02, th["text"])
        paragraph(d, x + r * 2.9, cy + size * 0.95, body, size * 0.90, w - r * 2.9, th, lead=1.34)
    return y + (len(items) - 1) * lead + size * 2


# ---------------------------------------------------------------- page furniture
def footer(d, x, y, w, th, size=7.4, url="akadian vertex · add it to your home screen"):
    """Disclaimer plus a quiet line of brand, on every printed piece.

    The disclaimer never gets dropped or truncated: if the piece is too narrow to carry the brand
    line beside it, the brand line goes and the disclaimer wraps.
    """
    rule(d, x, y - size * 1.5, w, th)
    url_w = render.measure(SANS, size, url) + size * 2 if url else 0
    if url and render.measure(SANS, size, DISCLAIMER) + url_w > w:
        url, url_w = None, 0
    lines = render.wrap(SANS, size, DISCLAIMER, w - url_w)
    for i, ln in enumerate(lines):
        d.text(x, y + size + i * size * 1.3, ln, SANS, size, th["muted"])
    if url:
        d.text(x + w, y + size, url, SANS, size, th["muted"], anchor="end")


def fineprint(d, x, y, th, size=13, text=None):
    """The independence line as plain sentence case -- it is a disclaimer, not a design element."""
    d.text(x, y, text or DISCLAIMER, SANS, size, th["muted"])


def canvas(w, h, th, note=""):
    d = Doc(w, h, note)
    d.rect(0, 0, w, h, th["bg"])
    return d


def cut_marks(d, w, h, th, lines):
    """Trim guides for the imposed flyer sheets: a hairline where the cut goes, plus ticks at the
    sheet edge so the guillotine has something to line up on."""
    for kind, at in lines:
        if kind == "h":
            d.line(0, at, w, at, th["hairline"], 0.4, dash="6 5")
            for x0, x1 in ((0, 14), (w - 14, w)):
                d.line(x0, at, x1, at, th["muted"], 0.6)
        else:
            d.line(at, 0, at, h, th["hairline"], 0.4, dash="6 5")
            for y0, y1 in ((0, 14), (h - 14, h)):
                d.line(at, y0, at, y1, th["muted"], 0.6)


def place(dst, src, dx, dy):
    """Copy one document's elements into another, shifted. How the 2-up and 4-up sheets are imposed:
    a flyer is laid out once and stamped twice or four times, so the unit and the sheet can never
    drift apart."""
    for e in src.els:
        e = dict(e)
        if e["t"] in ("polygon", "polyline", "path"):
            e["points"] = [(x + dx, y + dy) for x, y in e["points"]]
        elif e["t"] == "line":
            e["x1"] += dx
            e["x2"] += dx
            e["y1"] += dy
            e["y2"] += dy
        elif e["t"] == "circle":
            e["cx"] += dx
            e["cy"] += dy
        else:
            e["x"] += dx
            e["y"] += dy
        dst.els.append(e)
    return dst

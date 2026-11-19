"""The campaign's shared furniture: themes, the logo lockup, the QR placeholder, chips, rules,
and the real artwork -- a building's stacked floor plates with the app's own route through them,
and the app's search as it actually answers.

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
        p["plate_line"] = p["hairline"]
    else:
        # on paper the plates need real contrast: a pale grey slab, near-white rooms with a firm
        # outline and a darker edge, or the building disappears into the page
        p = dict(brand.LIGHT)
        bg, ink = p["bg"], p["text"]
        p.update(panel=mix(bg, ink, 0.045), panel2=mix(bg, ink, 0.09), plate=mix(bg, ink, 0.085),
                 room=mix(bg, ink, 0.015), room_line=mix(bg, ink, 0.36), void=mix(bg, ink, 0.16),
                 skirt=mix(bg, ink, 0.26), hairline=mix(bg, ink, 0.18),
                 accent_dim=mix(bg, p["accent"], 0.22), paper="#ffffff", paper_ink="#15171c",
                 plate_line=mix(bg, ink, 0.42))
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
class Scene:
    """One real walk through one real building: the plan, the route, and what to call each end.

    The route is computed by route.py over the app's own walk grids; a room that is not in the data,
    or one with no way to it, raises instead of being drawn.
    """

    def __init__(self, key, room, entrance, room_tag, room_sub, levels=None):
        self.key = key
        self.levels = levels      # which floors to draw (indexes); None draws them all
        self.plan = brand.building_plan(key)
        self.room_id = room
        self.room = brand.building_room(key, room)
        self.entrance = self.plan["entrances"][entrance]
        self.legs, self.start, self.goal = route.route_in(key, room, entrance)
        self.room_tag, self.room_sub = room_tag, room_sub
        self.metres = route.length_m(self.legs, key)

    @property
    def door_name(self):
        return self.entrance["name"].split(" (")[0]


_SCENES = {}


def scene(name):
    """The two walks the campaign draws, built once.

    gps  the Johnson Center, in the west door and up to the computer lab in 342 on the third floor:
         the "GPS stops at the door" pieces. The ground floor is left out -- the walk never uses it,
         and without it the door faces open space, where the GPS approach can be seen.
    find Research Hall, in the west door by the rotunda and up three floors to room 423: the "find
         your class" pieces, and the room the search-bar mock types

    Both doors were chosen because they face the viewer in the drawing; the walks are whatever the
    app's search returns from them.
    """
    if name not in _SCENES:
        if name == "gps":
            _SCENES[name] = Scene("jc", "342", 3, "342", "Room 342 \u00b7 Computer lab \u00b7 Floor 3",
                                  levels=(1, 2, 3))
        elif name == "find":
            _SCENES[name] = Scene("research", "423", 1, "423", "Room 423 \u00b7 Floor 4")
        else:
            raise KeyError(name)
    return _SCENES[name]


class Iso:
    """Plan coordinates -> an axonometric view of the stacked floors, auto-fitted to a box."""

    def __init__(self, box, sc, rot_deg=-24.0, squash=0.50, lift_frac=0.30, levels=None,
                 approach=0.0):
        self.rot = math.radians(rot_deg)
        self.squash = squash
        self.sc = sc
        floors = sc.plan["floors"]
        levels = levels if levels is not None else sc.levels
        levels = list(levels) if levels is not None else list(range(len(floors)))
        self.levels = levels
        xs, ys = [], []
        for lv in levels:
            for outer, _ in floors[lv]["slab"]:
                xs += [q[0] for q in outer]
                ys += [q[1] for q in outer]
        self.span_y = max(ys) - min(ys)
        self.span = max(max(xs) - min(xs), self.span_y)
        self.lift = self.span_y * lift_frac
        corners = [(min(xs), min(ys)), (max(xs), min(ys)), (min(xs), max(ys)), (max(xs), max(ys))]
        pts = [self._raw(x, y, i) for i in range(len(levels)) for x, y in corners]
        if approach:
            # leave room for the GPS approach drawn outside the door
            pts += [self._raw(x, y, self.level_of(sc.entrance["floor"])) for x, y in
                    [approach_point(sc, self.span * approach)]]
        px0, px1 = min(q[0] for q in pts), max(q[0] for q in pts)
        py0, py1 = min(q[1] for q in pts), max(q[1] for q in pts)
        bx, by, bw, bh = box
        self.s = min(bw / (px1 - px0), bh / (py1 - py0))
        self.ox = bx + (bw - (px1 - px0) * self.s) / 2 - px0 * self.s
        self.oy = by + (bh - (py1 - py0) * self.s) / 2 - py0 * self.s
        self.box = box

    def level_of(self, floor_id):
        """Where a floor sits in the drawn stack (0 at the bottom)."""
        ids = [self.sc.plan["floors"][lv]["id"] for lv in self.levels]
        return ids.index(floor_id)

    def _raw(self, x, y, level):
        c, s = math.cos(self.rot), math.sin(self.rot)
        return (x * c - y * s, (x * s + y * c) * self.squash - level * self.lift)

    def __call__(self, x, y, level):
        rx, ry = self._raw(x, y, level)
        return (self.ox + rx * self.s, self.oy + ry * self.s)

    def ring(self, pts, level):
        return [self(x, y, level) for x, y in pts]


def approach_point(sc, dist):
    """A point `dist` plan-units straight out from the scene's door, along the real door direction
    (the entrance's inside point to its door point, both from the app's data)."""
    (dx, dy), (sx, sy) = sc.entrance["plan"], sc.entrance["start"]
    vx, vy = dx - sx, dy - sy
    n = math.hypot(vx, vy) or 1.0
    return (dx + vx / n * dist, dy + vy / n * dist)


def callout(d, x, y, lines, th, border, gap, side="right", margin=0.0):
    """A small panel of stacked lines beside a marker at (x, y), with a short leader to it.

    `lines` is [(text, family, size, colour, tracking_em, upper)]. The panel sits on the right of the
    marker unless that would cross the page margin, in which case it goes left. It has a solid
    background, so it stays legible over the floor plates.
    """
    sets = [(t.upper() if up else t, f, z, c, z * em) for t, f, z, c, em, up in lines]
    pad = sets[0][2] * 0.7
    w = max(render.measure(f, z, t, tr) for t, f, z, c, tr in sets) + pad * 2
    h = sum(z * 1.28 for _, _, z, _, _ in sets) + pad * 1.2
    if side == "right" and x + gap + w > d.w - margin:
        side = "left"
    px = x + gap if side == "right" else x - gap - w
    py = y - h / 2
    d.line(x, y, px if side == "right" else px + w, y, border, max(0.5, sets[0][2] * 0.06))
    d.rect(px, py, w, h, th["bg"], rx=pad * 0.8, stroke=border, stroke_width=max(0.5, sets[0][2] * 0.07))
    yy = py + pad * 0.6
    for t, f, z, c, tr in sets:
        yy += z * 1.08
        d.text(px + pad, yy, t, f, z, c, tracking=tr)
        yy += z * 0.20
    return side


def floor_stack(d, iso, th, gps=True, show_rooms=True, floor_labels=True, label_size=8.0,
                callouts=True, thickness=0.028, gps_side="right", room_side="right"):
    """A building's real floor plans, stacked, with the real walk threaded through them.

    With `gps`, the walk starts outside: a white GPS dot and a dashed approach to the door, then
    the orange Vertex route on from the door to the room. The picture is the tagline -- GPS gets
    you to the building, Vertex gets you to the room. Geometry comes from docs/data/buildings/ at
    build time; nothing is traced or drawn by hand.
    """
    sc = iso.sc
    floors = sc.plan["floors"]
    skirt = iso.span_y * thickness * iso.squash * iso.s
    legs = sc.legs
    lvl = iso.level_of

    # the plates, bottom up, so an upper floor overlaps the one below it
    for i, lv in enumerate(iso.levels):
        f = floors[lv]
        for outer, holes in f["slab"]:
            side = iso.ring(outer, i)
            d.polygon([(x, y + skirt) for x, y in side], th["skirt"])
            d.polygon(side, th["plate"], stroke=th["plate_line"], stroke_width=0.6)
            for h in holes:
                d.polygon(iso.ring(h, i), th["void"])
        if show_rooms:
            for outer, holes in f["rooms"]:
                d.polygon(iso.ring(outer, i), th["room"], stroke=th["room_line"], stroke_width=0.35)
                for h in holes:
                    d.polygon(iso.ring(h, i), th["plate"])
        if sc.room["floor"] == f["id"]:
            d.polygon(iso.ring(sc.room["poly"], i), th["accent_dim"],
                      stroke=th["accent"], stroke_width=max(0.5, iso.s * 3))
        if floor_labels:
            proj = [q for outer, _ in f["slab"] for q in iso.ring(outer, i)]
            lx, ly = min(proj, key=lambda q: q[0])
            label(d, lx - label_size * 1.1, ly + label_size * 0.34, f["name"], label_size, th,
                  fill=th["muted"], anchor="end", em=0.16)

    wide = max(1.8, iso.s * 13)
    ent_lv = lvl(sc.entrance["floor"])
    door = iso(sc.entrance["plan"][0], sc.entrance["plan"][1], ent_lv)
    first = iso(sc.start[0], sc.start[1], lvl(legs[0]["floor"]))
    gx, gy = iso(sc.goal[0], sc.goal[1], lvl(legs[-1]["floor"]))
    cs = max(6.5, iso.s * 34)

    # GPS: from you, outside, to the door -- dashed, in the plain text colour
    if gps:
        out = approach_point(sc, iso.span * 0.16)
        ux, uy = iso(out[0], out[1], ent_lv)
        d.polyline([(ux, uy), door, first], th["text"], wide * 0.62,
                   dash="%.1f %.1f" % (wide * 0.9, wide * 1.1), cap="round")
        d.circle(ux, uy, wide * 3.2, mix(th["bg"], th["text"], 0.16))
        d.circle(ux, uy, wide * 1.35, th["text"], stroke=th["bg"], stroke_width=wide * 0.45)

    # Vertex: the door to the room, over the whole stack, haloed so it reads as floating
    for leg in legs:
        if len(leg["pts"]) > 1:
            d.polyline(iso.ring(leg["pts"], lvl(leg["floor"])), th["bg"], wide * 2.0,
                       cap="round", join="round")
    for i, leg in enumerate(legs):
        lv = lvl(leg["floor"])
        if len(leg["pts"]) > 1:
            d.polyline(iso.ring(leg["pts"], lv), th["accent"], wide, cap="round", join="round")
        if i + 1 < len(legs):
            nxt = legs[i + 1]
            a = iso(leg["pts"][-1][0], leg["pts"][-1][1], lv)
            b = iso(nxt["pts"][0][0], nxt["pts"][0][1], lvl(nxt["floor"]))
            d.polyline([a, b], th["accent"], wide * 0.62,
                       dash="%.1f %.1f" % (wide * 1.15, wide * 0.95), cap="round")
    d.circle(first[0], first[1], wide * 1.05, th["bg"], stroke=th["accent"], stroke_width=wide * 0.5)
    diamond(d, gx, gy, wide * 2.1, th["accent"])

    if callouts:
        margin = max(cs * 2.0, d.w * 0.045)
        if gps:
            # where GPS gives out: at you, outside, on the way to the door
            callout(d, ux, uy, [("GPS", BOLD, cs * 1.05, th["text"], 0.14, True),
                                ("gets you to the door", SANS, cs * 0.92, th["muted"], 0.0, False)],
                    th, th["hairline"], gap=wide * 4.2, side=gps_side, margin=margin)
        else:
            label(d, first[0], first[1] + cs * 1.75, sc.door_name, cs, th, fill=th["text"], em=0.09)
        callout(d, gx, gy, [("Vertex", BOLD, cs * 1.25, th["accent"], 0.14, True),
                            ("gets you to the room", SANS, cs * 0.92, th["text"], 0.0, False),
                            (sc.room_sub, BOLD, cs * 0.78, th["muted"], 0.07, True)],
                th, th["accent"], gap=wide * 3.4, side=room_side, margin=margin)
    return legs


def diamond(d, cx, cy, r, fill):
    """The app's 'you are here' marker, the same diamond that sits inside the mark."""
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill)


# ---------------------------------------------------------------- artwork: the search, as the app shows it
def magnifier(d, cx, cy, r, colour, weight):
    d.circle(cx, cy, r, "none", stroke=colour, stroke_width=weight)
    k = r * 0.72
    d.line(cx + k, cy + k, cx + k + r * 0.85, cy + k + r * 0.85, colour, weight * 1.15, cap="round")


def search_card(d, x, y, w, th, sc, query=None, size=12, ui="dark"):
    """The app's own search, typed the way a schedule reads, with the answer it gives.

    Every string matches the real interface (app/js/main.js): the room result's meta line is
    "<building> - <floor>", and the route line reads "Best entrance: <name>". The query is the
    building and room number; the app matches every word against the room's id and building name,
    so this is a search that actually works.
    """
    u = theme(ui)
    query = query or "%s %s" % (sc.plan["name"].lower(), sc.room_id)
    floor = next(f["name"] for f in sc.plan["floors"] if f["id"] == sc.room["floor"])
    pad = size * 1.15
    h_bar = size * 3.3
    # the panel the search lives on
    total_h = h_bar + size * 9.0
    d.rect(x, y, w, total_h, u["panel"], rx=size * 1.1, stroke=u["hairline"], stroke_width=max(0.6, size * 0.05))
    # the search field
    fx, fy, fw = x + pad, y + pad, w - pad * 2
    d.rect(fx, fy, fw, h_bar, u["bg"], rx=h_bar / 2, stroke=u["accent"], stroke_width=max(0.8, size * 0.11))
    magnifier(d, fx + h_bar * 0.52, fy + h_bar * 0.46, size * 0.52, u["muted"], max(0.7, size * 0.11))
    tx = fx + h_bar * 0.98
    d.text(tx, fy + h_bar * 0.64, query, SANS, size * 1.15, u["text"])
    cw = render.measure(SANS, size * 1.15, query)
    d.line(tx + cw + size * 0.25, fy + h_bar * 0.26, tx + cw + size * 0.25, fy + h_bar * 0.76,
           u["accent"], max(0.8, size * 0.1))
    # the result row
    ry = fy + h_bar + size * 1.3
    diamond(d, fx + size * 0.9, ry + size * 1.25, size * 0.55, u["accent"])
    d.text(fx + size * 2.3, ry + size * 1.1, "Room %s" % sc.room_id, BOLD, size * 1.25, u["text"])
    d.text(fx + size * 2.3, ry + size * 2.55, "%s \u00b7 %s" % (sc.plan["name"], floor), SANS, size,
           u["muted"])
    # the answer: the best door, and the button that starts the walk
    rule(d, fx, ry + size * 4.0, fw, u)
    by = ry + size * 5.9
    d.text(fx, by, "Best entrance: ", SANS, size, u["muted"])
    bw = render.measure(SANS, size, "Best entrance: ")
    d.text(fx + bw, by, sc.entrance["name"], BOLD, size, u["text"])
    gw =render.measure(BOLD, size * 1.05, "Go") + size * 2.6
    d.rect(fx + fw - gw, by - size * 1.25, gw, size * 2.3, u["accent"], rx=size * 1.15)
    d.text(fx + fw - gw / 2, by + size * 0.2, "Go", BOLD, size * 1.05,
           u["paper_ink"] if ui == "dark" else "#ffffff", anchor="middle")
    return y + total_h


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

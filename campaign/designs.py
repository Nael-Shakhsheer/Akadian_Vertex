"""Every piece of the campaign, laid out.

Each function returns a finished svgdoc.Doc. Nothing here measures by eye: headline sizes are fitted
to their column with real font metrics, text blocks flow from the one above them, and the artwork is
auto-fitted into a box, so a design survives being re-set at another size.

The campaign sells the first week of classes. Four concepts run through it:

    A  better than GPS    "GPS stops at the door. Vertex doesn't."   GPS to the door, Vertex to the room
    B  find your class    "Research Hall 423? Found it."             the app's search, typed off a schedule
    C  offline            "No bars. Still works."                    a phone with no signal, map still up
    D  no install         "No app store. Just add it."               the icon landing on a home screen

Print pieces are authored in points (72 to the inch) at trim size; social pieces in pixels.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copytext as T
import kit
import render
from kit import (BOLD, DISPLAY, SANS, fineprint, canvas, chip, diamond, feature, floor_stack, footer,
                 headline, home_grid, Iso, label, lockup, no_signal, paragraph, phone,
                 qr_block, rule, search_card, steps, theme)

LETTER = (612, 792)
TABLOID = (792, 1224)
HALF = (612, 396)
QUARTER = (306, 396)
FEED = (1080, 1080)
STORY = (1080, 1920)
BANNER = (1600, 900)


def walk_caption(name):
    """The walk the artwork draws, described from the route itself rather than guessed."""
    sc = kit.scene(name)
    floors = len({leg["floor"] for leg in sc.legs}) - 1
    return "%s to room %s: about %d m inside and %s up. The orange line is the route Vertex gives." % (
        sc.entrance["name"], sc.room_id, round(sc.metres / 5) * 5,
        {1: "one floor", 2: "two floors", 3: "three floors"}.get(floors, "%d floors" % floors))


def benefits(d, x, y, items, th, size=10.5, gap=None, width=360):
    """The short benefit list: an accent diamond, a bold lead-in, the quiet line under it.

    Each item takes exactly the height its text needs, so a longer line pushes the next item down
    instead of landing on top of it.
    """
    gap = gap if gap is not None else size * 0.95
    tx, tw = x + size * 1.35, width - size * 1.35
    cy = y
    for title, body in items:
        diamond(d, x + size * 0.34, cy - size * 0.30, size * 0.34, th["accent"])
        d.text(tx, cy, title, BOLD, size, th["text"])
        lines = render.wrap(SANS, size * 0.90, body, tw)
        for i, ln in enumerate(lines):
            d.text(tx, cy + size * 1.30 + i * size * 0.90 * 1.34, ln, SANS, size * 0.90, th["muted"])
        cy += size * 1.30 + len(lines) * size * 0.90 * 1.34 + gap
    return cy - gap


def art_box(W, M, top, bottom, label_size):
    """The box the floor stack is fitted into: inside the safe margin on both sides, with room on
    the left for the floor labels that hang off the plates."""
    left = M + label_size * 7.2
    return (left, top, W - M - left, bottom - top)


def head(d, x, y, lines, width, start, th, track=0.04, lead=1.08, fill=None):
    """Fit a headline to its column and set it; returns the last baseline."""
    size = kit.head_size(lines, width, start, track)
    return headline(d, x, y, lines, size, th, lead=lead, tracking_em=track, fill=fill), size


def bottom_band(d, W, M, y, th, qr=78, size=10.6):
    """Rule, QR, the three one-line benefits and the footer -- the same close on every Letter poster."""
    CW = W - M * 2
    rule(d, M, y, CW, th)
    qr_block(d, M, y + 16, qr, th, caption=T.SCAN, sub=T.SCAN_SUB)
    benefits(d, M + qr + 20, y + 26, T.FEATURES_SHORT, th, size=size, gap=8, width=CW - qr - 20)


# ================================================================ posters
def poster_a_letter():
    """A on US Letter, dark. The workhorse: corridors, residence halls, every corkboard on the route
    to class."""
    th = theme("dark")
    W, H = LETTER
    M = 46
    CW = W - M * 2
    d = canvas(W, H, th, "Poster A - Letter 8.5x11in - GPS stops at the door - dark")
    lockup(d, M, 68, 15, th)
    label(d, W - M, 68, T.A_KICKER, 7.6, th, anchor="end")

    y, _ = head(d, M, 146, T.A_HEAD, CW, 54, th, track=0.035)
    y = paragraph(d, M, y + 34, T.A_DECK, 11.2, 470, th, lead=1.46)

    iso = Iso(art_box(W, M, y + 14, 578, 7.2), kit.scene("gps"), approach=0.16)
    floor_stack(d, iso, th, label_size=7.2)
    d.text(M, 590, walk_caption("gps"), SANS, 8.4, th["muted"])

    bottom_band(d, W, M, 604, th)
    footer(d, M, 740, CW, th)
    return d


def poster_a_tabloid():
    """A on Tabloid, dark. Read from across the room, so the headline and the building get space."""
    th = theme("dark")
    W, H = TABLOID
    M = 60
    CW = W - M * 2
    d = canvas(W, H, th, "Poster A - Tabloid 11x17in - GPS stops at the door - dark")
    lockup(d, M, 92, 20, th)
    label(d, W - M, 92, T.A_KICKER, 10, th, anchor="end")

    y, _ = head(d, M, 210, T.A_HEAD, CW, 84, th, track=0.035)
    y = paragraph(d, M, y + 52, T.A_DECK, 16, 650, th, lead=1.46)

    iso = Iso(art_box(W, M, y + 20, 912, 9.4), kit.scene("gps"), approach=0.16)
    floor_stack(d, iso, th, label_size=9.4)
    d.text(M, 928, walk_caption("gps"), SANS, 11, th["muted"])

    x = M
    for c in T.CHIPS:
        x += chip(d, x, 946, c, th, size=10) + 9

    rule(d, M, 1004, CW, th)
    col = (CW - 132 - 40) / 3
    for i, (title, body) in enumerate(T.FEATURES):
        feature(d, M + i * (col + 20), 1036, col - 20, title, body, th, size=12)
    qr_block(d, W - M - 132, 958, 132, th, caption=T.SCAN, sub=T.SCAN_SUB)
    footer(d, M, 1150, CW, th, size=9)
    return d


def poster_b_letter():
    """B on US Letter, light. The search the app actually runs, typed the way a schedule reads.
    Cheap to photocopy; put it outside lecture halls and on department boards."""
    th = theme("light")
    W, H = LETTER
    M = 46
    CW = W - M * 2
    d = canvas(W, H, th, "Poster B - Letter 8.5x11in - find your class - light")
    lockup(d, M, 68, 15, th)
    label(d, W - M, 68, T.B_KICKER, 7.6, th, anchor="end")

    y, _ = head(d, M, 150, T.B_HEAD, CW, 58, th)
    y = paragraph(d, M, y + 34, T.B_DECK, 11.2, 470, th, lead=1.46)

    y = search_card(d, M, y + 20, CW, th, kit.scene("find"), size=11, ui="light")
    iso = Iso(art_box(W, M, y + 10, 584, 6.8), kit.scene("find"), approach=0.16)
    floor_stack(d, iso, th, label_size=6.8)

    bottom_band(d, W, M, 604, th)
    footer(d, M, 740, CW, th)
    return d


def poster_b_tabloid():
    """B on Tabloid, light."""
    th = theme("light")
    W, H = TABLOID
    M = 60
    CW = W - M * 2
    d = canvas(W, H, th, "Poster B - Tabloid 11x17in - find your class - light")
    lockup(d, M, 92, 20, th)
    label(d, W - M, 92, T.B_KICKER, 10, th, anchor="end")

    y, _ = head(d, M, 220, T.B_HEAD, CW, 96, th)
    y = paragraph(d, M, y + 52, T.B_DECK, 16, 650, th, lead=1.46)

    y = search_card(d, M, y + 30, CW, th, kit.scene("find"), size=16, ui="light")
    iso = Iso(art_box(W, M, y + 12, 926, 9), kit.scene("find"), approach=0.16)
    floor_stack(d, iso, th, label_size=9)
    d.text(M, 944, T.SCOPE, SANS, 11, th["muted"])

    rule(d, M, 1004, CW, th)
    col = (CW - 132 - 40) / 3
    for i, (title, body) in enumerate(T.FEATURES):
        feature(d, M + i * (col + 20), 1036, col - 20, title, body, th, size=12)
    qr_block(d, W - M - 132, 958, 132, th, caption=T.SCAN, sub=T.SCAN_SUB)
    footer(d, M, 1150, CW, th, size=9)
    return d


# ================================================================ flyers
def flyer_half():
    """Half a Letter sheet, landscape (8.5 x 5.5in). The table handout: don't be late, dark.

    Left, the argument; right, the search and the walk it gives.
    """
    th = theme("dark")
    W, H = HALF
    M = 30
    LW = 300
    RX, RW = 350, W - 350 - M
    d = canvas(W, H, th, "Flyer - half page 8.5x5.5in - don't be late - dark")
    lockup(d, M, 48, 12, th)
    label(d, W - M, 48, T.B_KICKER, 7.2, th, anchor="end")

    y, _ = head(d, M, 98, T.LATE_HEAD, LW, 30, th, lead=1.12)
    y = paragraph(d, M, y + 26, T.LATE_DECK, 9, LW, th, lead=1.44)
    benefits(d, M, y + 26, T.FEATURES_SHORT[:2], th, size=9, gap=6, width=LW)
    qr_block(d, M, 286, 52, th, caption=T.SCAN, sub=None)
    paragraph(d, M + 66, 300, T.D_SHORT + " Add it to your home screen.", 8.4, LW - 66, th, lead=1.4)

    y = search_card(d, RX, 66, RW, th, kit.scene("find"), size=8.2)
    iso = Iso((RX - 6, y + 4, RW + 12, 334 - (y + 4)), kit.scene("find"), approach=0.16)
    floor_stack(d, iso, th, floor_labels=False, label_size=5)
    footer(d, M, 372, W - M * 2, th, size=6.6)
    return d


def flyer_quarter():
    """A quarter of a Letter sheet, portrait (4.25 x 5.5in). Pocket handout: how to add it."""
    th = theme("dark")
    W, H = QUARTER
    M = 22
    CW = W - M * 2
    d = canvas(W, H, th, "Flyer - quarter page 4.25x5.5in - add to home screen - dark")
    lockup(d, M, 46, 10.5, th)
    y, _ = head(d, M, 92, T.D_HEAD, CW, 26, th, lead=1.1)
    y = paragraph(d, M, y + 26, T.D_DECK, 8.4, CW, th, lead=1.42)

    steps(d, M, y + 36, CW, T.D_STEPS, th, size=8.4, lead=27)
    qr_block(d, M, 276, 56, th, caption=T.SCAN, sub=None)
    paragraph(d, M + 70, 290, T.A_SHORT, 8.6, CW - 70, th, lead=1.38, fill=th["text"])
    footer(d, M, 356, CW, th, size=5.8, url=None)
    return d


def _sheet(unit_fn, cols, rows, note, base="dark"):
    """Impose a flyer onto a Letter sheet with cut guides. The unit is laid out once and stamped."""
    unit = unit_fn()
    W, H = LETTER
    th = theme(base)
    d = canvas(W, H, th, note)
    for r in range(rows):
        for c in range(cols):
            kit.place(d, unit, c * unit.w, r * unit.h)
    lines = [("v", c * unit.w) for c in range(1, cols)] + [("h", r * unit.h) for r in range(1, rows)]
    kit.cut_marks(d, W, H, th, lines)
    return d


def sheet_half_2up():
    return _sheet(flyer_half, 1, 2, "Imposed sheet - Letter - 2 half-page flyers - cut on the guide")


def sheet_quarter_4up():
    return _sheet(flyer_quarter, 2, 2, "Imposed sheet - Letter - 4 quarter-page flyers - cut on the guides")


# ================================================================ social
# Social layouts flow downward from the headline rather than sitting on fixed baselines: a headline
# that fits at a different size moves everything under it instead of landing on top of it.

def feed_gps():
    """A: Instagram feed, 1080. The building, the GPS dot outside, the route inside."""
    th = theme("dark")
    W, H = FEED
    M = 78
    d = canvas(W, H, th, "Social A - Instagram feed 1080x1080 - GPS stops at the door - dark")
    lockup(d, M, 108, 23, th)
    y, _ = head(d, M, 206, T.A_HEAD, W - M * 2, 80, th, track=0.035)
    iso = Iso(art_box(W, M, y + 40, 800, 12), kit.scene("gps"), approach=0.16)
    floor_stack(d, iso, th, label_size=12)
    qr_block(d, W - M - 104, 846, 104, th, caption=None, sub=None)
    d.text(M, 888, "GPS gets you to the building.", SANS, 27, th["muted"])
    d.text(M, 930, "Vertex gets you to the room.", BOLD, 30, th["text"])
    d.text(M, 970, T.D_SHORT, SANS, 22, th["accent"])
    fineprint(d, M, 1020, th, 13)
    return d


def banner_gps():
    """A: a wide banner for Discord and Reddit. Type left, Research Hall right -- its long plates
    were made for a wide frame."""
    th = theme("dark")
    W, H = BANNER
    M = 96
    d = canvas(W, H, th, "Social A - wide banner 1600x900 - GPS stops at the door - dark")
    lockup(d, M, 130, 27, th)
    y, _ = head(d, M, 268, T.A_HEAD, 640, 72, th, track=0.035, lead=1.1)
    y = paragraph(d, M, y + 62, T.A_DECK, 22, 620, th, lead=1.46)
    benefits(d, M, y + 58, T.FEATURES_SHORT[:2], th, size=20, gap=16, width=620)
    qr_block(d, M, 672, 104, th, caption=None, sub=None)
    d.text(M + 128, 716, T.SCAN, BOLD, 22, th["text"])
    d.text(M + 128, 748, T.D_SHORT, SANS, 18, th["muted"])
    fineprint(d, M, 834, th, 13.5)
    iso = Iso((760, 70, 800, 760), kit.scene("find"), approach=0.16)
    floor_stack(d, iso, th, label_size=12)
    return d


def feed_findclass():
    """B: Instagram feed, 1080, light. The search, then the walk it gives."""
    th = theme("light")
    W, H = FEED
    M = 78
    d = canvas(W, H, th, "Social B - Instagram feed 1080x1080 - find your class - light")
    lockup(d, M, 108, 23, th)
    y, _ = head(d, M, 222, T.B_HEAD, W - M * 2, 92, th)
    y = search_card(d, M, y + 46, W - M * 2, th, kit.scene("find"), size=18, ui="light")
    iso = Iso(art_box(W, M, y + 10, 824, 11), kit.scene("find"), approach=0.16)
    floor_stack(d, iso, th, label_size=11)
    qr_block(d, W - M - 104, 852, 104, th, caption=None, sub=None)
    d.text(M, 896, "Type the room off your schedule.", SANS, 26, th["muted"])
    d.text(M, 940, T.B_SHORT, BOLD, 28, th["text"])
    fineprint(d, M, 1020, th, 13)
    return d


def story_findclass():
    """B: a 9:16 story, light. Built for a thumb, in the week everyone is lost."""
    th = theme("light")
    W, H = STORY
    M = 86
    d = canvas(W, H, th, "Social B - story 1080x1920 - find your class - light")
    lockup(d, M, 330, 26, th)
    label(d, M, 400, "Never get lost finding a class", 20, th, fill=th["accent"], em=0.14)
    y, _ = head(d, M, 500, T.B_STORY_HEAD, W - M * 2, 86, th, lead=1.12)
    y = paragraph(d, M, y + 70, T.B_DECK, 26, W - M * 2, th, lead=1.46)
    y = search_card(d, M, y + 48, W - M * 2, th, kit.scene("find"), size=22, ui="light")
    iso = Iso(art_box(W, M, y + 14, 1420, 12), kit.scene("find"), approach=0.16)
    floor_stack(d, iso, th, label_size=12)
    qr_block(d, M, 1450, 150, th, caption=None, sub=None)
    d.text(M + 190, 1500, T.SCAN, BOLD, 32, th["text"])
    d.text(M + 190, 1542, T.A_SHORT.split(". ")[0] + ".", SANS, 24, th["muted"])
    d.text(M + 190, 1578, T.A_SHORT.split(". ")[1], BOLD, 24, th["accent"])
    fineprint(d, M, 1648, th, 15)
    return d


def story_offline():
    """C: a 9:16 story, dark. The phone has no signal and the map is still there."""
    th = theme("dark")
    W, H = STORY
    M = 86
    d = canvas(W, H, th, "Social C - story 1080x1920 - offline - dark")
    lockup(d, M, 330, 26, th)
    y, _ = head(d, M, 480, T.C_HEAD, W - M * 2, 108, th, track=0.045)
    paragraph(d, M, y + 78, T.C_DECK, 26, W - M * 2, th, lead=1.46)

    sx, sy, sw, sh = phone(d, 132, 800, 404, th, h=640)
    iso = Iso((sx - 30, sy + 40, sw + 60, sh - 186), kit.scene("gps"), rot_deg=-20, lift_frac=0.26)
    floor_stack(d, iso, th, gps=False, floor_labels=False, callouts=False)
    d.rect(sx + 16, sy + sh - 104, sw - 32, 72, kit.mix(th["bg"], th["text"], 0.11), rx=15)
    d.text(sx + 38, sy + sh - 68, "Offline · showing the saved map", BOLD, 20, th["text"])
    d.text(sx + 38, sy + sh - 44, "Your route is still here", SANS, 17, th["muted"])

    no_signal(d, 800, 940, 96, th)
    label(d, 800, 1082, "No signal", 22, th, fill=th["text"], anchor="middle", em=0.08)
    d.text(800, 1116, "2.5s and it stops waiting", SANS, 18, th["muted"], anchor="middle")
    qr_block(d, 710, 1160, 180, th, caption=T.SCAN, sub=None)

    benefits(d, M, 1498, [T.FEATURES[0], T.FEATURE_CAMPUS], th, size=22, gap=22, width=W - M * 2)
    fineprint(d, M, 1650, th, 15)
    return d


def banner_offline():
    """C: wide banner, dark. The same idea sized for a Discord header."""
    th = theme("dark")
    W, H = BANNER
    M = 96
    d = canvas(W, H, th, "Social C - wide banner 1600x900 - offline - dark")
    lockup(d, M, 130, 27, th)
    y, _ = head(d, M, 300, T.C_HEAD, 740, 94, th, track=0.045)
    y = paragraph(d, M, y + 72, T.C_DECK, 23, 700, th, lead=1.46)
    benefits(d, M, y + 58, [T.FEATURES_SHORT[2]], th, size=21, width=700)
    qr_block(d, M, 660, 104, th, caption=None, sub=None)
    fineprint(d, M, 834, th, 13.5)

    sx, sy, sw, sh = phone(d, 1010, 130, 330, th, h=650)
    iso = Iso((sx - 26, sy + 30, sw + 52, sh - 150), kit.scene("gps"), rot_deg=-20, lift_frac=0.26)
    floor_stack(d, iso, th, gps=False, floor_labels=False, callouts=False)
    d.rect(sx + 13, sy + sh - 88, sw - 26, 60, kit.mix(th["bg"], th["text"], 0.11), rx=13)
    d.text(sx + 30, sy + sh - 59, "Offline · saved map", BOLD, 17, th["text"])
    d.text(sx + 30, sy + sh - 38, "Your route is still here", SANS, 15, th["muted"])
    no_signal(d, 1452, 292, 84, th)
    return d


def feed_homescreen():
    """D: Instagram feed, 1080, dark. The icon arriving on a home screen."""
    th = theme("dark")
    W, H = FEED
    M = 78
    d = canvas(W, H, th, "Social D - Instagram feed 1080x1080 - no install - dark")
    lockup(d, M, 108, 23, th)
    y, _ = head(d, M, 218, T.D_HEAD, 600, 72, th)
    y = paragraph(d, M, y + 62, T.D_DECK, 23, 540, th, lead=1.46)
    steps(d, M, y + 74, 610, T.D_STEPS, th, size=21, lead=80)
    sx, sy, sw, sh = phone(d, 712, 250, 290, th, h=560)
    home_grid(d, sx + 26, sy + 56, sw - 52, th, cols=3, rows=3, hot=(1, 1))
    qr_block(d, M, 846, 104, th, caption=None, sub=None)
    d.text(M + 128, 890, "Add it before your first class.", BOLD, 24, th["text"])
    d.text(M + 128, 926, T.A_SHORT, SANS, 20, th["muted"])
    fineprint(d, M, 1016, th, 13)
    return d


def story_homescreen():
    """D: a 9:16 story, dark. Three steps, big enough to follow while standing in a queue."""
    th = theme("dark")
    W, H = STORY
    M = 86
    d = canvas(W, H, th, "Social D - story 1080x1920 - no install - dark")
    lockup(d, M, 330, 26, th)
    y, _ = head(d, M, 480, T.D_HEAD, W - M * 2, 104, th)
    paragraph(d, M, y + 78, T.D_DECK, 26, W - M * 2, th, lead=1.46)

    sx, sy, sw, sh = phone(d, 330, 770, 420, th, h=540)
    home_grid(d, sx + 40, sy + 60, sw - 80, th, cols=3, rows=3, hot=(1, 1))

    steps(d, M, 1384, W - M * 2 - 240, T.D_STEPS, th, size=24, lead=90)
    qr_block(d, W - M - 170, 1366, 170, th, caption=T.SCAN, sub=None)
    fineprint(d, M, 1660, th, 15)
    return d


# ================================================================ the set
PIECES = [
    # (folder, name, builder, render spec)
    ("posters", "poster-a-gps-letter", poster_a_letter, {"dpi": 300, "pdf": True}),
    ("posters", "poster-a-gps-tabloid", poster_a_tabloid, {"dpi": 300, "pdf": True}),
    ("posters", "poster-b-findclass-letter", poster_b_letter, {"dpi": 300, "pdf": True}),
    ("posters", "poster-b-findclass-tabloid", poster_b_tabloid, {"dpi": 300, "pdf": True}),
    ("flyers", "flyer-findclass-half", flyer_half, {"dpi": 300, "pdf": True}),
    ("flyers", "flyer-install-quarter", flyer_quarter, {"dpi": 300, "pdf": True}),
    ("flyers", "sheet-half-2up-letter", sheet_half_2up, {"dpi": 300, "pdf": True}),
    ("flyers", "sheet-quarter-4up-letter", sheet_quarter_4up, {"dpi": 300, "pdf": True}),
    ("social", "a-gps-feed-1080", feed_gps, {"dpi": None, "supersample": 2}),
    ("social", "a-gps-banner-1600x900", banner_gps, {"dpi": None, "supersample": 2}),
    ("social", "b-findclass-feed-1080", feed_findclass, {"dpi": None, "supersample": 2}),
    ("social", "b-findclass-story-1080x1920", story_findclass, {"dpi": None, "supersample": 2}),
    ("social", "c-offline-story-1080x1920", story_offline, {"dpi": None, "supersample": 2}),
    ("social", "c-offline-banner-1600x900", banner_offline, {"dpi": None, "supersample": 2}),
    ("social", "d-install-feed-1080", feed_homescreen, {"dpi": None, "supersample": 2}),
    ("social", "d-install-story-1080x1920", story_homescreen, {"dpi": None, "supersample": 2}),
]

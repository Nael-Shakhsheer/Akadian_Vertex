"""Every piece of the campaign, laid out.

Each function returns a finished svgdoc.Doc. Nothing here measures by eye: headline sizes are fitted
to their column with real font metrics, and the artwork is auto-fitted into a box, so the same design
survives being re-set at another size.

Four concepts run through the set:

    A  indoor routing     "Find the room, not the building."   the stacked Johnson Center plates
    B  study rooms        "Where is a free study room?"        all 23 rooms, by their real numbers
    C  offline            "No bars. Still works."              a phone with no signal, map still up
    D  no install         "No app store. Just add it."         the icon landing on a home screen

Print pieces are authored in points (72 to the inch) at trim size; social pieces in pixels.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copytext as T
import kit
import render
import route
from kit import (BOLD, DISPLAY, SANS, fineprint, canvas, chip, diamond, feature, floor_stack, footer,
                 headline, home_grid, Iso, label, lockup, no_signal, paragraph, phone,
                 qr_block, rule, steps, study_grid, theme)

LETTER = (612, 792)
TABLOID = (792, 1224)
HALF = (612, 396)
QUARTER = (306, 396)
FEED = (1080, 1080)
STORY = (1080, 1920)
BANNER = (1600, 900)


def walk_caption():
    """The length of the walk the artwork draws, measured from the route itself."""
    legs, _, _ = kit.jc_route()
    return "About %d m and two floors up — Vertex counts the turns so you do not have to." % (
        round(route.length_m(legs) / 10) * 10)


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


# ================================================================ posters
def poster_a_letter():
    """Concept A on US Letter, dark. The workhorse: corridor walls, corkboards, residence halls."""
    th = theme("dark")
    W, H = LETTER
    M = 46
    CW = W - M * 2
    d = canvas(W, H, th, "Poster A - Letter 8.5x11in - indoor routing - dark")

    lockup(d, M, 68, 15, th)
    label(d, W - M, 68, T.A_KICKER, 8.2, th, anchor="end")

    size = kit.head_size(T.A_HEAD, CW, 50, 0.045)
    headline(d, M, 150, T.A_HEAD, size, th, lead=1.08, tracking_em=0.045)
    paragraph(d, M, 234, T.A_DECK, 11.4, 446, th, lead=1.46)

    iso = Iso((14, 248, W - 28, 318))
    floor_stack(d, iso, th, label_size=7.4)
    d.text(M, 588, walk_caption(), SANS, 9.2, th["muted"])

    rule(d, M, 608, CW, th)
    qr_block(d, M, 624, 78, th, caption=T.SCAN, sub=T.SCAN_SUB)
    benefits(d, M + 98, 634, T.FEATURES_SHORT, th, size=10.6, gap=8, width=CW - 98)
    footer(d, M, 740, CW, th)
    return d


def poster_a_tabloid():
    """Concept A on Tabloid, dark. Read from further away, so the headline and the plates get room."""
    th = theme("dark")
    W, H = TABLOID
    M = 60
    CW = W - M * 2
    d = canvas(W, H, th, "Poster A - Tabloid 11x17in - indoor routing - dark")

    lockup(d, M, 92, 20, th)
    label(d, W - M, 92, T.A_KICKER, 10.5, th, anchor="end")

    size = kit.head_size(T.A_HEAD, CW, 92, 0.045)
    headline(d, M, 226, T.A_HEAD, size, th, lead=1.08, tracking_em=0.045)
    paragraph(d, M, 338, T.A_DECK, 16.5, 646, th, lead=1.46)

    iso = Iso((28, 400, W - 56, 486))
    floor_stack(d, iso, th, label_size=9.4)
    d.text(M, 924, walk_caption(), SANS, 12, th["muted"])

    x = M
    for c in T.CHIPS:
        x += chip(d, x, 948, c, th, size=10) + 9

    rule(d, M, 1004, CW, th)
    col = (CW - 132 - 40) / 3
    for i, (title, body) in enumerate(T.FEATURES):
        feature(d, M + i * (col + 20), 1036, col - 20, title, body, th, size=12)
    qr_block(d, W - M - 132, 958, 132, th, caption=T.SCAN, sub=T.SCAN_SUB)
    footer(d, M, 1150, CW, th, size=9)
    return d


def poster_b_letter():
    """Concept B on US Letter, light. Cheap to photocopy, aimed at the Johnson Center itself."""
    th = theme("light")
    W, H = LETTER
    M = 46
    CW = W - M * 2
    d = canvas(W, H, th, "Poster B - Letter 8.5x11in - study rooms - light")

    lockup(d, M, 68, 15, th)
    label(d, W - M, 68, T.B_KICKER, 8.2, th, anchor="end")

    size = kit.head_size(T.B_HEAD, CW, 54, 0.04)
    headline(d, M, 158, T.B_HEAD, size, th, lead=1.08, tracking_em=0.04)
    paragraph(d, M, 240, T.B_DECK, 11.4, 446, th, lead=1.46)

    d.text(M, 286, "Every group study room in the building, by its real number. The one in orange "
                   "is on the third floor.", SANS, 9.2, th["muted"])
    study_grid(d, M, 320, CW, th, cols=8, pick=kit.DEST_ROOM, size=15)

    rule(d, M, 608, CW, th)
    qr_block(d, M, 624, 78, th, caption=T.SCAN, sub=T.SCAN_SUB)
    benefits(d, M + 98, 634, T.FEATURES_SHORT, th, size=10.6, gap=8, width=CW - 98)
    footer(d, M, 740, CW, th)
    return d


def poster_b_tabloid():
    """Concept B on Tabloid, light. The same idea with the grid big enough to read across a lobby."""
    th = theme("light")
    W, H = TABLOID
    M = 60
    CW = W - M * 2
    d = canvas(W, H, th, "Poster B - Tabloid 11x17in - study rooms - light")

    lockup(d, M, 92, 20, th)
    label(d, W - M, 92, T.B_KICKER, 10.5, th, anchor="end")

    size = kit.head_size(T.B_HEAD, CW, 92, 0.04)
    headline(d, M, 240, T.B_HEAD, size, th, lead=1.08, tracking_em=0.04)
    paragraph(d, M, 352, T.B_DECK, 16.5, 646, th, lead=1.46)

    d.text(M, 414, "Every group study room in the building, by its real number. The one in orange "
                   "is on the third floor.", SANS, 12, th["muted"])
    study_grid(d, M, 466, CW, th, cols=8, pick=kit.DEST_ROOM, size=22)

    rule(d, M, 1004, CW, th)
    col = (CW - 132 - 40) / 3
    for i, (title, body) in enumerate(T.FEATURES):
        feature(d, M + i * (col + 20), 1036, col - 20, title, body, th, size=12)
    qr_block(d, W - M - 132, 958, 132, th, caption=T.SCAN, sub=T.SCAN_SUB)
    footer(d, M, 1150, CW, th, size=9)
    return d


# ================================================================ flyers
def flyer_half():
    """Half a Letter sheet, landscape (8.5 x 5.5in). Table handout: the study-room hook, dark.

    Two columns: the argument on the left, all 23 rooms on the right, so it works face-up on a table
    as well as in a hand.
    """
    th = theme("dark")
    W, H = HALF
    M = 30
    LW = 296                                   # the left column
    RX, RW = 342, W - 342 - M                  # the right column
    d = canvas(W, H, th, "Flyer - half page 8.5x5.5in - study rooms - dark")

    lockup(d, M, 48, 12, th)
    label(d, W - M, 48, T.B_KICKER, 7.2, th, anchor="end")

    size = kit.head_size(T.B_HEAD, LW, 30, 0.04)
    headline(d, M, 100, T.B_HEAD, size, th, lead=1.1, tracking_em=0.04)
    paragraph(d, M, 160, T.B_DECK, 8.8, LW, th, lead=1.44)

    benefits(d, M, 210, T.FEATURES_SHORT, th, size=9, gap=6, width=LW)
    qr_block(d, M, 296, 50, th, caption=T.SCAN, sub=None)
    paragraph(d, M + 64, 316, T.D_SHORT + " Vertex is a web page you add to your home screen.",
              8.4, LW - 64, th, lead=1.4)

    study_grid(d, RX, 76, RW, th, cols=6, pick=kit.DEST_ROOM, size=11)
    paragraph(d, RX, 300, "The one in orange is 320H, on the third floor. Vertex walks you to it "
                          "from whichever door you came in.", 8.4, RW, th, lead=1.4)
    footer(d, M, 372, W - M * 2, th, size=6.6)
    return d


def flyer_quarter():
    """A quarter of a Letter sheet, portrait (4.25 x 5.5in). Pocket handout: how to install it."""
    th = theme("dark")
    W, H = QUARTER
    M = 22
    CW = W - M * 2
    d = canvas(W, H, th, "Flyer - quarter page 4.25x5.5in - add to home screen - dark")

    lockup(d, M, 46, 10.5, th)
    size = kit.head_size(T.D_HEAD, CW, 26, 0.04)
    headline(d, M, 92, T.D_HEAD, size, th, lead=1.1, tracking_em=0.04)
    paragraph(d, M, 146, T.D_DECK, 8.4, CW, th, lead=1.42)

    steps(d, M, 206, CW, T.D_STEPS, th, size=8.4, lead=27)
    qr_block(d, M, 276, 56, th, caption=T.SCAN, sub=None)
    paragraph(d, M + 70, 294, T.A_SHORT + " Vertex takes you to the room, indoors, floor by floor.",
              8.2, CW - 70, th, lead=1.4)
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

def feed_floors():
    """A: Instagram feed, 1080. The plates do the talking; the type stays out of their way."""
    th = theme("dark")
    W, H = FEED
    M = 78
    d = canvas(W, H, th, "Social A - Instagram feed 1080x1080 - indoor routing - dark")
    lockup(d, M, 108, 23, th)
    size = kit.head_size(T.A_HEAD, W - M * 2, 76, 0.04)
    y = headline(d, M, 206, T.A_HEAD, size, th, lead=1.08, tracking_em=0.04)
    iso = Iso((40, y + 44, W - 80, 772 - y), lift_frac=0.26)
    floor_stack(d, iso, th, label_size=12.5)
    qr_block(d, W - M - 104, 836, 104, th, caption=None, sub=None)
    d.text(M, 880, T.A_SHORT, SANS, 25, th["muted"])
    d.text(M, 924, T.B_SHORT, BOLD, 26, th["text"])
    d.text(M, 962, T.D_SHORT, SANS, 23, th["accent"])
    fineprint(d, M, 1016, th, 13)
    return d


def banner_floors():
    """A: a wide banner for Discord and Reddit. Type left, plates right."""
    th = theme("dark")
    W, H = BANNER
    M = 96
    d = canvas(W, H, th, "Social A - wide banner 1600x900 - indoor routing - dark")
    lockup(d, M, 132, 27, th)
    size = kit.head_size(T.A_HEAD, 700, 72, 0.04)
    y = headline(d, M, 276, T.A_HEAD, size, th, lead=1.1, tracking_em=0.04)
    y = paragraph(d, M, y + 66, T.A_DECK, 23, 650, th, lead=1.46)
    benefits(d, M, y + 62, T.FEATURES[1:], th, size=20, gap=18, width=640)
    qr_block(d, M, 668, 112, th, caption=None, sub=None)
    fineprint(d, M, 832, th, 13.5)
    iso = Iso((790, 80, 620, 740), lift_frac=0.28)
    floor_stack(d, iso, th, label_size=13)
    return d


def feed_studyrooms():
    """B: Instagram feed, 1080, light. All 23 room numbers at once."""
    th = theme("light")
    W, H = FEED
    M = 78
    d = canvas(W, H, th, "Social B - Instagram feed 1080x1080 - study rooms - light")
    lockup(d, M, 108, 23, th)
    size = kit.head_size(T.B_HEAD, W - M * 2, 84, 0.04)
    y = headline(d, M, 230, T.B_HEAD, size, th, lead=1.08, tracking_em=0.04)
    study_grid(d, M, y + 58, W - M * 2, th, cols=8, pick=kit.DEST_ROOM, size=22, max_tile=78)
    qr_block(d, W - M - 104, 836, 104, th, caption=None, sub=None)
    d.text(M, 884, T.B_DECK.split(". ")[0] + ".", SANS, 24, th["muted"])
    d.text(M, 926, "Vertex walks you to the door.", BOLD, 26, th["text"])
    d.text(M, 964, T.D_SHORT, SANS, 23, th["accent"])
    fineprint(d, M, 1016, th, 13)
    return d


def story_studyrooms():
    """B: a 9:16 story, light. Built for a thumb: one question, the answer, a code."""
    th = theme("light")
    W, H = STORY
    M = 86
    d = canvas(W, H, th, "Social B - story 1080x1920 - study rooms - light")
    lockup(d, M, 340, 26, th)
    size = kit.head_size(T.B_HEAD, W - M * 2, 96, 0.04)
    y = headline(d, M, 500, T.B_HEAD, size, th, lead=1.1, tracking_em=0.04)
    y = paragraph(d, M, y + 84, T.B_DECK, 26, W - M * 2, th, lead=1.46)
    study_grid(d, M, y + 76, W - M * 2, th, cols=6, pick=kit.DEST_ROOM, size=26, max_tile=115)
    qr_block(d, M, 1452, 150, th, caption=None, sub=None)
    d.text(M + 190, 1500, T.SCAN, BOLD, 32, th["text"])
    d.text(M + 190, 1544, "Vertex walks you to the door.", SANS, 25, th["muted"])
    d.text(M + 190, 1582, T.D_SHORT, SANS, 23, th["accent"])
    fineprint(d, M, 1648, th, 15)
    return d


def story_offline():
    """C: a 9:16 story, dark. The phone has no signal and the map is still there."""
    th = theme("dark")
    W, H = STORY
    M = 86
    d = canvas(W, H, th, "Social C - story 1080x1920 - offline - dark")
    lockup(d, M, 330, 26, th)
    size = kit.head_size(T.C_HEAD, W - M * 2, 108, 0.045)
    y = headline(d, M, 480, T.C_HEAD, size, th, lead=1.08, tracking_em=0.045)
    paragraph(d, M, y + 78, T.C_DECK, 26, W - M * 2, th, lead=1.46)

    sx, sy, sw, sh = phone(d, 132, 800, 404, th, h=640)
    iso = Iso((sx - 34, sy + 48, sw + 68, sh - 196), rot_deg=-20, lift_frac=0.24)
    floor_stack(d, iso, th, levels=(1, 2, 3), floor_labels=False, callouts=False)
    d.rect(sx + 16, sy + sh - 104, sw - 32, 72, kit.mix(th["bg"], th["text"], 0.11), rx=15)
    d.text(sx + 38, sy + sh - 68, "Offline \u00b7 showing the saved map", BOLD, 20, th["text"])
    d.text(sx + 38, sy + sh - 44, "Last loaded on campus wi-fi", SANS, 17, th["muted"])

    no_signal(d, 800, 940, 96, th)
    label(d, 800, 1082, "No signal", 22, th, fill=th["text"], anchor="middle", em=0.08)
    d.text(800, 1116, "2.5s and it stops waiting", SANS, 18, th["muted"], anchor="middle")
    qr_block(d, 710, 1160, 180, th, caption=T.SCAN, sub=None)

    benefits(d, M, 1498, [T.FEATURES[2], T.FEATURE_CAMPUS], th, size=22, gap=22, width=W - M * 2)
    fineprint(d, M, 1634, th, 15)
    return d


def banner_offline():
    """C: wide banner, dark. The same idea sized for a Discord header."""
    th = theme("dark")
    W, H = BANNER
    M = 96
    d = canvas(W, H, th, "Social C - wide banner 1600x900 - offline - dark")
    lockup(d, M, 130, 27, th)
    size = kit.head_size(T.C_HEAD, 740, 90, 0.045)
    y = headline(d, M, 290, T.C_HEAD, size, th, lead=1.08, tracking_em=0.045)
    y = paragraph(d, M, y + 72, T.C_DECK, 23, 700, th, lead=1.46)
    benefits(d, M, y + 58, [T.FEATURES[2]], th, size=21, width=700)
    qr_block(d, M, 650, 112, th, caption=None, sub=None)
    fineprint(d, M, 834, th, 13.5)

    sx, sy, sw, sh = phone(d, 1010, 130, 330, th, h=650)
    iso = Iso((sx - 28, sy + 36, sw + 56, sh - 166), rot_deg=-20, lift_frac=0.24)
    floor_stack(d, iso, th, levels=(1, 2, 3), floor_labels=False, callouts=False)
    d.rect(sx + 13, sy + sh - 88, sw - 26, 60, kit.mix(th["bg"], th["text"], 0.11), rx=13)
    d.text(sx + 30, sy + sh - 59, "Offline \u00b7 saved map", BOLD, 17, th["text"])
    d.text(sx + 30, sy + sh - 38, "Still routes you indoors", SANS, 15, th["muted"])
    no_signal(d, 1452, 292, 84, th)
    return d


def feed_homescreen():
    """D: Instagram feed, 1080, dark. The icon arriving on a home screen."""
    th = theme("dark")
    W, H = FEED
    M = 78
    d = canvas(W, H, th, "Social D - Instagram feed 1080x1080 - no install - dark")
    lockup(d, M, 108, 23, th)
    size = kit.head_size(T.D_HEAD, 600, 72, 0.04)
    y = headline(d, M, 218, T.D_HEAD, size, th, lead=1.08, tracking_em=0.04)
    y = paragraph(d, M, y + 62, T.D_DECK, 23, 540, th, lead=1.46)
    steps(d, M, y + 74, 520, T.D_STEPS, th, size=21, lead=70)
    sx, sy, sw, sh = phone(d, 712, 250, 290, th, h=560)
    home_grid(d, sx + 26, sy + 56, sw - 52, th, cols=3, rows=3, hot=(1, 1))
    qr_block(d, M, 846, 104, th, caption=None, sub=None)
    d.text(M + 128, 890, T.D_SHORT, BOLD, 24, th["text"])
    d.text(M + 128, 926, "Open the link and keep it on your home screen.", SANS, 21, th["muted"])
    fineprint(d, M, 1016, th, 13)
    return d


def story_homescreen():
    """D: a 9:16 story, dark. Three steps, big enough to follow while standing in a queue."""
    th = theme("dark")
    W, H = STORY
    M = 86
    d = canvas(W, H, th, "Social D - story 1080x1920 - no install - dark")
    lockup(d, M, 330, 26, th)
    size = kit.head_size(T.D_HEAD, W - M * 2, 104, 0.04)
    y = headline(d, M, 480, T.D_HEAD, size, th, lead=1.08, tracking_em=0.04)
    paragraph(d, M, y + 78, T.D_DECK, 26, W - M * 2, th, lead=1.46)

    sx, sy, sw, sh = phone(d, 320, 790, 440, th, h=580)
    home_grid(d, sx + 40, sy + 62, sw - 80, th, cols=3, rows=3, hot=(1, 1))

    steps(d, M, 1440, W - M * 2 - 250, T.D_STEPS, th, size=26, lead=80)
    qr_block(d, W - M - 170, 1402, 170, th, caption=T.SCAN, sub=None)
    fineprint(d, M, 1660, th, 15)
    return d


# ================================================================ the set
PIECES = [
    # (folder, name, builder, render spec)
    ("posters", "poster-a-indoor-letter", poster_a_letter, {"dpi": 300, "pdf": True}),
    ("posters", "poster-a-indoor-tabloid", poster_a_tabloid, {"dpi": 300, "pdf": True}),
    ("posters", "poster-b-studyrooms-letter", poster_b_letter, {"dpi": 300, "pdf": True}),
    ("posters", "poster-b-studyrooms-tabloid", poster_b_tabloid, {"dpi": 300, "pdf": True}),
    ("flyers", "flyer-studyrooms-half", flyer_half, {"dpi": 300, "pdf": True}),
    ("flyers", "flyer-install-quarter", flyer_quarter, {"dpi": 300, "pdf": True}),
    ("flyers", "sheet-half-2up-letter", sheet_half_2up, {"dpi": 300, "pdf": True}),
    ("flyers", "sheet-quarter-4up-letter", sheet_quarter_4up, {"dpi": 300, "pdf": True}),
    ("social", "a-indoor-feed-1080", feed_floors, {"dpi": None, "supersample": 2}),
    ("social", "a-indoor-banner-1600x900", banner_floors, {"dpi": None, "supersample": 2}),
    ("social", "b-studyrooms-feed-1080", feed_studyrooms, {"dpi": None, "supersample": 2}),
    ("social", "b-studyrooms-story-1080x1920", story_studyrooms, {"dpi": None, "supersample": 2}),
    ("social", "c-offline-story-1080x1920", story_offline, {"dpi": None, "supersample": 2}),
    ("social", "c-offline-banner-1600x900", banner_offline, {"dpi": None, "supersample": 2}),
    ("social", "d-install-feed-1080", feed_homescreen, {"dpi": None, "supersample": 2}),
    ("social", "d-install-story-1080x1920", story_homescreen, {"dpi": None, "supersample": 2}),
]

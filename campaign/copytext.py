"""Every word that appears on a piece of artwork.

campaign/copy.md is the document a human edits and reads; this module is the same words in a form
the layouts can set. make_campaign.py checks at build time that every string in on_artwork() still
appears verbatim in copy.md, so the two can never drift apart -- change the words in both, or the
build fails.

The campaign sells one moment: the first week of classes, when nobody knows where anything is.

Rules this copy is written under:
  - no university logo, wordmark or name used as an endorsement; "for George Mason" is descriptive
    only, and every printed piece carries the independence line in kit.DISCLAIMER
  - no invented numbers. Every figure below is read out of the app's own data at build time and
    checked in make_campaign.py. There are no users yet, so there are no usage numbers, quotes or
    awards anywhere.
  - no claim the app cannot back. Vertex uses GPS outdoors; indoors it routes from the door you
    came in by, because GPS does not work inside (app/js/main.js says so in its first two lines).
    So the copy says GPS gets you to the building and Vertex gets you to the room -- which is the
    better line anyway -- and never that the phone knows where you are inside a building.
"""

# ---------------------------------------------------------------- A: better than GPS
A_HEAD = ["GPS stops at the door.", "Vertex doesn't."]
A_DECK = ("Vertex uses live GPS to walk you across campus and pick the best door. Then it keeps "
          "going where GPS can't: up the right stairs, down the right hallway, to the room on "
          "your schedule.")
A_KICKER = "Live GPS · 3D campus · turn-by-turn inside"
A_SHORT = "GPS gets you to the building. Vertex gets you to the room."

# ---------------------------------------------------------------- B: find your class
B_HEAD = ["Research Hall 423?", "Found it."]
B_DECK = ("Type the building and room number off your schedule. Vertex finds it, picks the best "
          "door, and walks you there, floor by floor. Your first week, minus the wandering.")
B_KICKER = "First week of classes"
B_SHORT = "Walk in like you've been here for years."
B_STORY_HEAD = ["Walk in like you've", "been here for years."]

# ---------------------------------------------------------------- B, the handout: don't be late
LATE_HEAD = ["Don't be the one", "walking in at 9:07."]
LATE_DECK = ("Type the room off your schedule. Vertex walks you there on live GPS, picks the best "
             "door, and takes you inside, floor by floor, to the room.")

# ---------------------------------------------------------------- C: offline
C_HEAD = ["No bars.", "Still works."]
C_DECK = ("Campus wi-fi doesn't fail, it hangs, usually in a stairwell four minutes before class. "
          "Vertex gives the network 2.5 seconds, then uses the map already on your phone.")
C_KICKER = "Built for bad campus wi-fi"
C_SHORT = "The map is already on your phone."

# ---------------------------------------------------------------- D: no install
D_HEAD = ["No app store.", "Just add it."]
D_DECK = ("Vertex is a website that works like an app. Add it to your home screen before your "
          "first class: no download, no account, and it opens full-screen.")
D_KICKER = "No install · no account · no download"
D_SHORT = "No app store. No account. No download."
D_STEPS = [("Open the link", "Scan the code, or type the address into your phone's browser."),
           ("Add to Home Screen", "In Safari, tap Share. In Chrome, tap the three dots."),
           ("Open it like an app", "Full-screen, no browser bar, and it still works on bad wi-fi.")]

# ---------------------------------------------------------------- what it does
FEATURES = [
    ("Live GPS outside",
     "Watch yourself move on a 3D map of campus, and get walked to the best door for your room."),
    ("Turn-by-turn inside",
     "Research Hall, Merten Hall, the Johnson Center and The HUB, mapped room by room: 633 rooms."),
    ("Works on bad wi-fi",
     "A map you have opened stays on your phone, so a dead stairwell can't strand you."),
]
# The same three, cut to one short line each: a poster is read in three seconds, not thirty.
FEATURES_SHORT = [
    ("Live GPS outside", "Walks you to the best door for your room."),
    ("Turn-by-turn inside", "Research Hall, Merten, the JC and The HUB."),
    ("Nothing to install", "No app store, no account. Add it to your home screen."),
]
FEATURE_CAMPUS = ("All of campus",
                  "163 buildings, 25 places to eat, and 7 CUE routes across 26 stops.")
# Where the indoor promise stops, said plainly wherever a piece promises "to the room".
SCOPE = ("Room by room inside Research Hall, Merten Hall, the Johnson Center and The HUB. "
         "Right to the door of every other building on campus.")

# ---------------------------------------------------------------- small furniture
SCAN = "Scan to open"
SCAN_SUB = "No app store. No install."
CHIPS = ["Research Hall", "Merten Hall", "Johnson Center", "The HUB"]
SIGNOFF = "Akadian Vertex · a 3D campus map for George Mason students"


def on_artwork():
    """Every string the artwork sets that must also appear, word for word, in copy.md."""
    heads = [A_HEAD, B_HEAD, B_STORY_HEAD, LATE_HEAD, C_HEAD, D_HEAD]
    singles = [A_DECK, A_KICKER, A_SHORT, B_DECK, B_KICKER, B_SHORT, LATE_DECK, C_DECK, C_KICKER,
               C_SHORT, D_DECK, D_KICKER, D_SHORT, SCOPE, SIGNOFF, *FEATURE_CAMPUS]
    pairs = [t for pair in FEATURES + FEATURES_SHORT for t in pair]
    return [" ".join(h) for h in heads] + singles + pairs


def numbers_claimed():
    """Every figure the copy states, so make_campaign.py can check it against the app's data."""
    return {"indoor_buildings": 4, "indoor_rooms": 633, "campus_buildings": 163, "food": 25,
            "cue_routes": 7, "cue_stops": 26, "net_timeout_ms": 2500, "rsch_floors": 4,
            "rsch_room_423_floor": "fourth"}

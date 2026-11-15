"""Every word that appears on a piece of artwork.

campaign/copy.md is the document a human edits and reads; this module is the same words in a form
the layouts can set. make_campaign.py checks at build time that each string here still appears
verbatim in copy.md, so the two can never drift apart -- change the words in both, or the build fails.

Rules this copy is written under:
  - no university logo, wordmark or name used as an endorsement; "for George Mason" is descriptive
    only, and every printed piece carries the independence line in kit.DISCLAIMER
  - no invented numbers. Every figure below is read out of the app's own data at build time and
    checked in make_campaign.py: 23 group study rooms, 320 rooms, 4 indoor buildings, 163 campus
    buildings, 25 food spots, 7 CUE routes, 26 stops, and the 2.5 second network deadline in
    app/sw.js. There are no users yet, so there are no usage numbers, quotes or awards anywhere.
"""

# ---------------------------------------------------------------- concept A: indoor routing
A_HEAD = ["Find the room,", "not the building."]
A_DECK = ("Indoor, room-level walking directions through the Johnson Center: four floors, "
          "320 rooms, and the walk from the front door to the door you actually want.")
A_KICKER = "3D campus maps · indoor directions"
A_SHORT = "Every other campus map stops at the front door."

# ---------------------------------------------------------------- concept B: study rooms
B_HEAD = ["Where is a free", "study room?"]
B_DECK = ("The Johnson Center has 23 group study rooms across three floors. Vertex knows where "
          "every one of them is, and walks you to the door.")
B_KICKER = "23 group study rooms · Johnson Center"
B_SHORT = "23 group study rooms. Vertex walks you to one."

# ---------------------------------------------------------------- concept C: offline
C_HEAD = ["No bars.", "Still works."]
C_DECK = ("Campus wi-fi does not fail, it hangs. Vertex gives the network 2.5 seconds, then draws "
          "the map already sitting on your phone.")
C_KICKER = "Built for bad campus wi-fi"
C_SHORT = "The map is already on your phone."

# ---------------------------------------------------------------- concept D: no install
D_HEAD = ["No app store.", "Just add it."]
D_DECK = ("Vertex is a web page, not a download. Open the link, add it to your home screen, and it "
          "opens full-screen like any other app.")
D_KICKER = "No install · no account · no download"
D_SHORT = "No app store. No account. No download."
D_STEPS = [("Open the link", "Scan the code, or type the address into your phone's browser."),
           ("Add to Home Screen", "In Safari, tap Share. In Chrome, tap the three dots."),
           ("Open it like an app", "Full-screen, no browser bar, and it still works on bad wi-fi.")]

# ---------------------------------------------------------------- the three things it does
FEATURES = [
    ("Room-level indoors",
     "Four buildings mapped floor by floor: the Johnson Center, Research Hall, Merten Hall and The HUB."),
    ("Works on bad wi-fi",
     "A map you have opened stays on your phone, so a dead spot in a stairwell does not strand you."),
    ("Nothing to install",
     "No app store and no account. Open the link and add it to your home screen."),
]
# The same three, cut to one short line each: a poster is read in three seconds, not thirty.
FEATURES_SHORT = [
    ("Room-level indoors", "Johnson Center, Research Hall, Merten Hall, The HUB."),
    ("Works on bad wi-fi", "A map you have opened stays on your phone."),
    ("Nothing to install", "No app store, no account. Add it to your home screen."),
]
FEATURE_CAMPUS = ("The rest of campus too",
                  "163 buildings, 25 places to eat, and 7 CUE routes across 26 stops.")

# ---------------------------------------------------------------- small furniture
SCAN = "Scan to open"
SCAN_SUB = "No app store. No install."
CHIPS = ["Johnson Center", "Research Hall", "Merten Hall", "The HUB"]
SIGNOFF = "Akadian Vertex · a 3D campus map for George Mason students"


def numbers_claimed():
    """Every figure the copy states, so make_campaign.py can check it against the app's data."""
    return {"study_rooms": 23, "jc_rooms": 320, "jc_floors": 4, "indoor_buildings": 4,
            "campus_buildings": 163, "food": 25, "cue_routes": 7, "cue_stops": 26,
            "net_timeout_ms": 2500}

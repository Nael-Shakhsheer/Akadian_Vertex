# The words of the document, kept apart from the typesetting.

TITLE = "Akadian Vertex"
SUB = "Project documentation and timeline"
DATE = "14 November 2026"
REPO = "github.com/Nael-Shakhsheer/Akadian_Vertex"

INTRO = [
    "Akadian Vertex is a 3D campus map for George Mason University and Virginia Tech, with indoor maps "
    "and room-level walking directions. You search for a building, a room, a bus stop, a food spot or a "
    "parking lot, and it walks you there — across the campus, and then through the building, floor by "
    "floor.",
    "This document is the record of how it was built: every change in order, with what each one was for, "
    "and the decisions and constraints behind them that the code itself does not explain. It covers the "
    "work from the first commit on 24 October 2026 to the present — 24 commits in all.",
]

# (date, heading, hash, [paragraphs], meta)
TIMELINE = [
    ("24 Oct", "The first build", "2885caa", [
        "Akadian Maps began as a whole system rather than a prototype: a public web app, and a private "
        "map engine behind it.",
        "The app drew the GMU campus in 3D with MapLibre, the Johnson Center's interior in Three.js, "
        "walking directions to a named room, and layers for buses, food and parking — installable to a "
        "phone as a progressive web app. The engine held the encrypted vault, an admin studio, the "
        "schematic pipeline that turns published floor plans into routable maps, the OpenStreetMap "
        "compilers for campus, transit, food and walking paths, and a read-only public API that served "
        "the compiled result.",
    ], "76 files, 204,539 lines"),

    ("25 Oct", "Three more buildings, and the first performance pass", "e9b96aa", [
        "Research Hall (floors 1–4), Merten Hall and The HUB joined the Johnson Center, and the app "
        "stopped assuming a single indoor building: search spanned all of them, and each got its own "
        "routing worker and 3D view, reachable by link.",
        "The engine learned to place a plan by fitting its outline to the OpenStreetMap footprint, for "
        "buildings with fewer than two tagged entrances, and to read four-digit room numbers. Indoor "
        "routing moved into a Web Worker, so choosing a room no longer froze the interface; the 3D views "
        "became lazy-loaded, and the pixel ratio was capped on phones.",
    ], "40 files, +7,902"),

    ("25 Oct", "Five saved places", "8950935", [
        "The home screen's generic list of popular places gave way to five slots the user fills "
        "themselves, with one-tap directions. A room in any building, a building, a bus stop or a food "
        "spot can be saved. Like recents and the parked car, they stay on the device and are never sent "
        "anywhere.",
    ], "4 files, +89"),

    ("26 Oct", "A static build, so it could be carried around", "049ace2", [
        "A new export script copies the app and the published maps into docs/, with the tiles and fonts "
        "unpacked and the data location baked in, so the whole thing runs from GitHub Pages with no "
        "Python anywhere. Every path in the app became relative, so one build serves both the engine and "
        "Pages at a subpath.",
    ], "101 files, +61,420"),

    ("27 Oct", "An honest location", "1ff81df", [
        "Off campus, the app used to drop a made-up position beside the Johnson Center and stop watching "
        "GPS — which looked like a working location and was not one. It now shows no location at all, "
        "says how far from campus you are, lets you tap a starting point instead, and keeps watching, so "
        "real GPS takes over the moment you arrive. Leaving campus hides the marker again.",
        "The location dot became a breathing diamond with a diamond ripple, still when the device asks "
        "for reduced motion.",
    ], "6 files, +68 − 26"),

    ("27 Oct", "Akadian Vertex", "f5852fa", [
        "The rebrand that named the product. The mark is Cinzel's letter A with its crossbar replaced by "
        "the orange “you are here” diamond — the map's own symbol doing the work of a letter — beside an "
        "AKADIAN / VERTEX wordmark. It went into the header, the loading screen, the app icons and the "
        "favicon.",
        "Cinzel is bundled under the SIL Open Font License, so the app still loads nothing from outside "
        "its own server.",
    ], "22 files, +234"),

    ("27 Oct", "CUE bus times", "d687265", [
        "The engine reads CUE's published GTFS timetable, matches its stops to the campus stops and "
        "builds the result into the campus layer, so bus times work offline and on Pages. A stop lists "
        "the next buses per line and direction; tapping a line shows the rest of that trip stop by stop, "
        "earlier and later buses, and the line's hours from that stop.",
        "Times follow the feed's own time zone and handle trips running past midnight and calendar "
        "exceptions. It is the timetable, not live vehicle positions, and the app says so.",
    ], "20 files, +873"),

    ("28 Oct", "Turn-by-turn navigation", "32c4e09", [
        "The route preview gained a Start button, and with it the behaviour people expect from the big "
        "map apps: the sheet drops away, the map follows you in close and tilted, facing your compass "
        "heading. A banner shows the next turn with a live distance countdown and the turn after it; a "
        "bottom bar shows time left, distance, arrival time and a spoken-directions toggle that is "
        "remembered. Turns are spoken ahead of time and again at the turn, the screen stays awake, and "
        "the route is recomputed every few metres, so walking off it reroutes.",
        "Rooms tapped in the 3D view stopped rerouting instantly and opened a card instead — the room "
        "outlined on its floor, with directions from here, a route from the entrance, save and share.",
    ], "11 files, +768"),

    ("2 Nov", "Virginia Tech", "ad79d9c", [
        "A second campus, and a first screen to choose between them. Virginia Tech came from "
        "OpenStreetMap — 3D buildings, lots, fields, Blacksburg Transit, food and walking routes — with "
        "Torgersen Hall floors 1–3 redrawn from Virginia Tech Computer Science's public CAD plans into "
        "the engine's own convention: 219 rooms, stairs and lifts, five tagged entrances.",
        "The router gained a rule that paid off on both campuses: never snap into a tiny sealed pocket, "
        "and route to the nearest reachable spot when a room is sealed off in the drawing. That also "
        "fixed three Johnson Center rooms that had never been reachable.",
    ], "77 files, +5,391"),

    ("2 Nov", "The two lines of work brought together", "27d0510", [
        "The rebrand, bus times and navigation mode merged with the campus picker and Virginia Tech: the "
        "picker took the Vertex mark, navigation kept the campus in its links, and the offline cache "
        "moved on a version.",
    ], "merge"),

    ("4 Nov", "Map-first, the way the big maps do it", "9238925", [
        "The home screen stopped being a screen in front of the map and became the map. A floating "
        "search bar sits over it with category chips beneath; the search list opens over the map only "
        "when the bar is tapped. Places open in a bottom sheet that drags between peek, half and full, "
        "and becomes a side panel on a wide screen. The map's framing and controls keep clear of both.",
    ], "11 files, +730 − 130"),

    ("14 Nov", "Appearance, settings, search, and the study rooms", "d4dd31c", [
        "The app learned to look how the user wants. A base (dark or white) and an accent now run "
        "through the whole of it — interface, wordmark, map cartography, route and the 3D views — chosen "
        "in a new settings screen and kept on the device, so it survives closing the app. Standard is "
        "dark with warm orange; Light is a white base with near-black outlines and a more vibrant "
        "orange, which a pale background needs to hold its contrast; Custom takes any base with orange, "
        "red, green, blue, gold or purple. An inline script applies the choice before the first paint, "
        "so the wrong base never flashes. The Layers category colours stay fixed, because there they are "
        "a legend.",
        "The indoor view kept its original orange with the glow turned down — outlines muted to a "
        "fraction of their strength, bloom from 0.75 to 0.3, floor fills lifted — so rooms read as "
        "surfaces rather than as circuitry. The route and its destination keep the full accent, so the "
        "thing you are following is the only thing that glows.",
        "Search became usable the way people actually type: initials (JC, MTC), entrances, lifts and "
        "stairwells are findable, equally good matches are ordered by distance and show it, the matching "
        "text is highlighted, and the arrow keys walk the list. Searching a building's own name no "
        "longer buries it under its own room numbers.",
        "All 23 bookable Johnson Center study rooms were named, taken from Student Centers' own "
        "reservation system. They had been drawn on GMU's floor plans all along and only lacked names, "
        "so search could never find them; the rebuild changed names only, and moved no geometry.",
        "Routing gained diagonal and bidirectional settings, and in testing them a real bug surfaced: a "
        "room costs more to enter than to leave, so the grid is directed, and the search that spreads "
        "out from the goal to choose the best entrance had been pricing those steps the wrong way round.",
    ], "25 files, +1,739 − 272"),

    ("14 Nov", "The home screen on an iPhone", "4108194", [
        "Settings gained a Home screen section that walks you through adding the app to an iPhone: the "
        "three taps by name, a warning if you are not in Safari (the only browser iOS allows this from), "
        "and a button that opens the share sheet, where Add to Home Screen lives. A website cannot "
        "install itself on iOS, so handing over to that sheet is as far as the platform goes. Android "
        "and desktop Chrome install in one tap, and the section reports when the app is already running "
        "from the home screen.",
        "A new tool generates the assets from the mark itself — which is pure polygons, so no font or "
        "SVG library is needed: icons at 120, 152, 167 and 180 px, and a launch image for every current "
        "iPhone and iPad size in both orientations, 38 in all. Without one of exactly the right size, "
        "iOS shows a blank screen while the app starts.",
    ], "94 files, +491"),

    ("14 Nov", "One app, and a switcher that reads as one piece", "5442702", [
        "Per-place home-screen icons were dropped: adding the app adds the app, and individual places no "
        "longer get icons of their own.",
        "Change campus became the campus monogram ringed by two arrows that cycle, and spin on hover, "
        "living only in the search bar. The two arcs and their heads are exact 180-degree rotations of "
        "each other about the centre, and each head's tip lands on its own arc's radius, so the badge "
        "sits in a true circle instead of looking off-centre.",
    ], "7 files, +73 − 123"),

    ("14 Nov", "The Vertex website, and a shorter README", "0ede73c", [
        "A small site for the product published alongside the app on Pages, linked back to Akadian, and "
        "a README cut back from a build manual to a product overview.",
    ], "4 commits, 13 files"),

    ("14 Nov", "What the phone showed", "5ab5cf4", [
        "The first round of fixes from carrying it around campus rather than looking at it on a desk.",
        "Light became what the app starts as. On a light base the interior outlines turned from black to "
        "the accent taken deeper, so a floor plan stays in the app's colour instead of reading like a "
        "photocopy. One tap now picks a building and routes to it, and two taps open its inside — "
        "tapping a mapped building used to jump straight indoors, which left no way to get directions to "
        "the Johnson Center without searching for it.",
        "Bus routes had been drifting off their roads, because the offset is measured in screen pixels: a "
        "fixed offset spreads the lines apart as you zoom out and bunches them as you zoom in, and the "
        "glow was not offset at all, so it never sat under its own line. The spacing now grows with the "
        "roads.",
        "Parking lots took the letter they are signed by (Lot A to A, Merten Hall Lot to MH) and became "
        "destinations in their own right. Stops, food spots and parking badges lifted off the map with a "
        "shadow beneath them and began to bob out of step with each other, so they read as objects "
        "standing on the campus; reduced motion keeps the lift and drops the movement.",
    ], "10 files, +388 − 54"),

    ("14 Nov", "The double tap, and icons drawn rather than typed", "d9c883a", [
        "The double tap relied on the map's own double-click event, which a phone does not reliably "
        "send. The second tap is now spotted in the ordinary click stream — same building, within 400 ms "
        "and 30 px — and while a first tap is pending the map's own double-tap zoom is switched off, so "
        "the two gestures cannot both fire.",
        "The settings gear and the back arrow still sat right of centre. Two causes: the gear path was "
        "hand-written and its shape sat 0.6 units right of the middle of its box, and the arrows and "
        "crosses were text glyphs, whose side bearings differ from font to font. All nine are drawn now, "
        "from paths symmetric about the centre, so they land in the middle whatever font the device has.",
    ], "6 files, +76 − 34"),

    ("14 Nov", "A seamless row, and the accent reaching further", "646622d", [
        "The category chips showed a rectangle over the map: a scroller clips whatever leaves its "
        "padding box, so each chip's shadow was being sliced into a straight line across the row. The "
        "row now carries room for the shadow and takes the space back with a matching negative margin, "
        "so it sits exactly where it did and scrolls edge to edge. Floating shadows had also been picked "
        "for the dark base and were running at about 53% black on white; they follow the base now.",
        "The chosen colour reached the walking route and the you-are-here sprite. The route's bright core "
        "and the focus halo had been fixed values, and a repaint changed the route's halo but not the "
        "line itself, so a route already on screen kept its old colour.",
    ], "4 files, +50 − 36"),

    ("14 Nov", "The car too", "eada251", [
        "The parked-car marker had kept a fixed orange — the glow, the pad, and the body, cabin and "
        "headlight of the little 3D model. All of them come from the accent now, with the cabin and "
        "headlight mixed towards white so the model still reads as a car rather than a coloured blob, "
        "and a car already on the map changes colour without a reload. Tail lights stay red and tyres "
        "stay dark: those are what they are, not theming.",
    ], "4 files, +38 − 10"),

    ("14 Nov", "The performance audit", "b4d56c1", [
        "A pass over the whole app for smoothness, with no change to how anything behaves. The marker "
        "bob was the one real find: every frame it wrote thirteen paint properties and marked the map "
        "dirty, so the map redrew about thirty times a second for as long as the app was open — behind "
        "the search sheet, behind settings, and while a building's inside was on screen, where the map "
        "cannot be seen at all. It now idles unless the map is really visible.",
        "Measured and deliberately left alone: parsing the campus and all four building maps costs "
        "5.9 ms; the worst search keystroke is 3.7 ms; frame pacing on the map is a locked 60 fps with "
        "no long tasks; Three.js stays unloaded until a room is picked; both 3D views already idle when "
        "off screen; and rebuilding the walking-step list is too cheap to be worth guarding.",
    ], "4 files, +24 − 4"),

    ("14 Nov", "A deadline on the network", "96dd78e", [
        "The app fetches its own files and map data network first, so a change is always picked up, with "
        "the cache as the fallback when a fetch fails. On campus wi-fi it often does not fail: an "
        "associated network with no throughput leaves the request hanging, and the app sat there waiting "
        "with a perfectly good copy already on the device.",
        "The network now gets 2.5 seconds to answer. Past that a cached copy is served and the request "
        "is left running, so it still refreshes the cache for the next launch. Nothing is served stale "
        "while the network works, and with nothing cached the request is waited out as before rather "
        "than failing at the deadline.",
    ], "3 files, +80 − 4"),
]

PARTS = [
    ("app/", "The public web app. Vanilla ES modules with no build step: MapLibre GL JS for the 3D "
     "campus, Three.js (lazy-loaded) for interiors, a Web Worker for indoor routing, and a service "
     "worker for offline use."),
    ("engine/", "The private map engine. An encrypted vault, an admin studio, the schematic pipeline "
     "that turns published floor plans into routable maps, the OpenStreetMap compilers for campus, "
     "transit, food and walking paths, and a read-only public API."),
    ("tools/", "The scripts that produce data and assets: campus seeds, floor-plan preparation and OCR, "
     "the Virginia Tech CAD conversion, the iOS icons and launch images, and the static export."),
    ("tests/", "Five suites, run on every change."),
    ("docs/", "The static build served from GitHub Pages, and the product website."),
]

DECISIONS = [
    ("No university logos.", "The campus badge uses the campus's initials as a monogram. The GMU and "
     "Virginia Tech marks are their trademarks and are not ours to ship."),
    ("No invented map data.", "Nothing is placed on a map that is not in a published source. When study "
     "rooms were wanted, the rooms were found in Student Centers' own reservation system rather than "
     "estimated, and the rebuild moved no geometry — it only added names to rooms already drawn."),
    ("No true iOS widget, and the reason said plainly.", "Home-screen widgets on iOS require a native "
     "app built with WidgetKit. No web API exposes them, so a progressive web app cannot provide one at "
     "any effort. What was achievable — a real app icon, per-device launch images, full-screen launch "
     "and a guided setup — was built instead."),
    ("Everything personal stays on the device.", "Saved places, history, the appearance choice and the "
     "parked car live in local storage and are never sent anywhere. Off campus the app shows no location "
     "rather than a plausible guess."),
    ("Bidirectional routing is off by default.", "Over 455 real routes both searches return paths of "
     "identical cost, but the bidirectional search expands about 31% more cells on these maps. It is "
     "available as a setting, and the correctness bug it exposed in entrance choice was fixed for both."),
    ("Bus times are the timetable, not live positions.", "The engine compiles the published GTFS feed, "
     "which works offline; the app does not claim to know where a bus is."),
    ("Reduced motion is honoured throughout.", "The breathing location diamond, the bobbing markers and "
     "the spinning campus arrows all settle when the device asks for less motion — keeping the lift and "
     "the shadow, dropping the movement."),
]

TESTS = [
    ("test_router.mjs", "455 real routes across both campuses, checking that the one-way and "
     "bidirectional searches agree to the cent."),
    ("test_sw.mjs", "The service worker's fetch handler, driven with the worker globals stubbed: the "
     "network deadline, the cache fallback, the deep-link shell and the cache-first assets."),
    ("test_buses.mjs", "Next departures, trip expansion and midnight rollover against the compiled "
     "timetable."),
    ("test_parking.mjs", "The parked-car store and its recovery."),
    ("test_schedule.py", "The GTFS reader: time zones, trips past midnight and calendar exceptions."),
]

NOT_BUILT = [
    ("A native iOS widget.", "Impossible for a web app, for the reason given above."),
    ("Splitting the walkable grid out of the building files.", "Considered during the performance audit "
     "and dropped: it saves about 24 KB gzipped on the Johnson Center, which does not justify a second "
     "request and a second code path."),
    ("Deferring the walking graph.", "The one payload item large enough to matter — 133 KB of GMU's "
     "181 KB campus file, 266 KB of Virginia Tech's 338 KB — but it is needed as soon as anyone asks for "
     "directions, which is immediately. Left alone."),
    ("A fully cache-first service worker.", "It would have made launches instant on a weak signal at the "
     "cost of occasionally running yesterday's code. The bounded network deadline gets most of the "
     "benefit and keeps the guarantee."),
]

CLOSING = ("As of 14 November 2026 the app covers two campuses, five mapped buildings and the rooms "
           "inside them, with 24 commits behind it and five test suites passing.")

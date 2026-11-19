# Akadian Vertex — app audit, 18 November 2026

Scope: user-friendliness, smoothness, the GPS system, the map data, and a search for public records of building
interiors that could become new indoor maps. Everything below was measured on the live GitHub Pages build or
computed from the published data, unless it says otherwise. Each finding carries a status that is updated as the
fixes land.

Severity: **High** — wrong or blocked for many people · **Medium** — degraded experience · **Low** — polish.

---

## 1. User-friendliness and accessibility

Automated sweep at phone size (375 × 812) of the home map, search, a route card, the indoor view and Settings:
every control has an accessible name, and no body text fails contrast. The failures are concentrated.

| # | Finding | Severity | Status |
|---|---|---|---|
| U1 | **The primary button fails contrast in the default Light theme.** White on the light-mode orange `#d2600a` is 3.88:1; WCAG AA needs 4.5:1 for text this size. It is the Start button, and every other filled button. | High | Fixed |
| U2 | Small orange text fails the same way at 3.88:1 — the room tag in the indoor view, "Route", the VERTEX wordmark. Lines and shapes in that orange are fine (they need 3:1). | Medium | Fixed |
| U3 | Touch targets under Apple's 44 pt minimum: map zoom and compass 29 px, the Legend toggle 30 px tall, the "Use my location" link 19 px, the History "Clear" link 19 px, the sheet's close button 34 px, Save/Share 33 px, Back to map 31 px, chips 36 px, Settings and Back 40 px. | Medium | Fixed |
| U4 | Unnamed buildings — 64 of 163 at GMU, 189 of 422 at Virginia Tech — all read as "Building". OpenStreetMap has no names for them (re-checked today for VT's nine largest), but it does say what they are. | Low | Fixed |
| U5 | Healthy: search costs at most 4 ms per keystroke on desktop (≈20 ms on a phone); its empty state explains what to try; the indoor view opens in ~330 ms because the 3D code is fetched as soon as a room is chosen. | — | — |

## 2. Smoothness and loading

| # | Finding | Severity | Status |
|---|---|---|---|
| S1 | **Startup is one long chain.** `maplibre-gl.js` (209 KB) blocks; `main.js` only asks for the campus file once it runs; the building files are only asked for once the campus file has arrived; and the map — and so its tiles and fonts — is only created once every building file is in. At GMU that is ≈ 860 KB fetched in four waves; at 2 Mb/s, about 3.3 s before the map appears. | High | Fixed |
| S2 | The same chain on a repeat launch over "connected but dead" campus wi-fi: each wave can wait the service worker's full 2.5 s network deadline before using its cached copy — up to ~10 s before the map. | High | Fixed (by S1) |
| S3 | JavaScript modules are discovered in two rounds (main.js, then its imports): one extra round trip. | Medium | Fixed |
| S4 | One 65 ms main-thread stall during pan and zoom. Frame rate could not be measured reliably here — the test browser throttles animation when its window isn't on screen — so no fps figure is claimed. | Low | Noted |
| S5 | Healthy: the service worker is registered and controlling on GitHub Pages; Pages gzips the tiles in transit (a 90 KB tile travels as 59 KB); GMU's bus timetable is valid to 2050. | — | — |
| S6 | Correction to 16 November: "the map's `ready` never resolves" was very likely an artefact of testing in a hidden browser pane, where animation frames stop and MapLibre never fires `load`. The change made then (settle on `style.load`) is harmless and still more robust; it was not a production fault. | — | — |

## 3. GPS

The 16–18 November work fixed the timeout that killed location, the silent iPhone refusal, and the hang with no
answer. Read with fresh eyes, three gaps remain.

| # | Finding | Severity | Status |
|---|---|---|---|
| G1 | **No accuracy filtering.** The quick Wi‑Fi fix (up to a minute old, accuracy often hundreds of metres) can arrive *after* a precise GPS fix and drag the dot away. | High | Fixed |
| G2 | **The automatic hand-over indoors ignores accuracy.** It fires when the fix's centre is within 20 m of the door — a ±150 m fix that happens to centre there switches you inside. | High | Fixed |
| G3 | The map shows a dot but no accuracy circle, so ±5 m and ±500 m look the same. | Medium | Fixed |
| G4 | No recovery after switching apps. iOS pauses location for a home-screen app in the background and often does not resume it, so the dot freezes where you left. | Medium | Fixed |

## 4. Map data

| # | Finding | Severity | Status |
|---|---|---|---|
| M1 | Healthy: the walking network is a single connected piece on both campuses (3,803 and 9,834 nodes), so no route is ever forced onto a straight line by an island. | — | — |
| M2 | **Virginia Tech has 78 bus stops and no bus times.** Blacksburg Transit publishes its timetable (GTFS) through Virginia DRPT's open-data clearinghouse, but the official server dropped every download attempted today, and the mirror's copy expired on 31 July 2026. Transitland shows the current feed covers only 17 Oct – 20 Nov 2026 — so bus times there need a scheduled refresh, not a one-off import. | Medium | See §6 |
| M3 | `tests/test_router.mjs` prints its comparison inverted ("−27% fewer cells" where bidirectional expands 27% more). | Low | Fixed |

## 5. Public records of building interiors

| Building | Source | What it has | Verdict |
|---|---|---|---|
| **Fenwick Library** (GMU) | GMU Libraries, floor maps 1–5 | Every floor, numbered study and instruction rooms, stairs, lifts, restrooms, both entrances, a directory naming the rooms; identical framing on all five sheets | **Built** — see §6 |
| **Exploratory Hall** (GMU) | OpenStreetMap indoor tagging (ODbL) | 51 named rooms on levels 0–4, three entrances; no corridors, doors, stairs or lifts mapped | Partial: rooms and floors are known, a route between floors is not |
| Data & Decision Sciences (VT) | VT Computer Science space plans, floors 1–4 | Clean colour-coded plans with a scale bar, but no room numbers | Possible; rooms could only be called "Classroom" or "Lab" |
| Gilbert Street Building (VT) | same | Floors 3–4 only | Too partial to route |
| ICAB1 | same | Innovation Campus, Alexandria | Not on either campus |
| Virginia Tech, generally | OpenStreetMap | Negligible indoor tagging (two features with a level) | — |

Nothing here was copied into the repository: like the existing GMU and VT sources, the plans are fetched by a
script and only the compiled map (room outlines and labels) is published.

## 6. Outcomes

- **U1–U4, S1–S3, G1–G4, M3: fixed** in commit 5fd3183, each re-measured afterwards with the same check that
  found it (contrast and tap-area sweep at phone size; stubbed-location tests for the GPS filter, accuracy
  circle and resume; the campus file now requested once, by the preload; basemap tiles all loading).
- **Fenwick Library: built.** `tools/gmu_fenwick.py` redraws GMU Libraries' five floor maps in the engine's
  convention; room numbers by OCR with hand fixes checked against each sheet; stairs, lifts and restrooms found
  with each sheet's own legend pictograms; zones named from each floor's directory. 150 rooms, 42 stair/lift
  links. Placed by fitting its outline to OpenStreetMap's footprint (overlap IoU 0.89). Every room and
  restroom routes from the entrances, normally and step-free (180/180). The rebuilt campus layer differs from
  the live one in exactly one field — Fenwick's indoor link. It adds 90 KB (gzipped) to GMU's startup, which
  now downloads alongside the tiles rather than before them.
- **Fixed on the way:** `seed_gmu.py --campus-only` dropped GMU's picker card; it no longer does.
- **M2, Virginia Tech bus times: blocked.** Every download from Blacksburg Transit's server arrived truncated,
  and the only intact copy expired in July. Shipping stale times would be worse than none. Needs a scheduled
  refresh from a machine that can reach the feed.
- **Torgersen Hall, found by the same every-room check and fixed:** the third floor published five rooms that
  aren't rooms there. 2150 and 2150B are second-floor numbers printed on the floor above (the upper part of a
  double-height space, entered on floor 2), and no route could reach them; 0000, 1000 and 6005 were OCR reading
  linework as numbers, and showed up in search as rooms. The Torgersen tool now keeps only numbers that start
  with their floor's digit, which drops exactly those five; the rebuild changes nothing else (checked against
  a rebuild of the untouched source, identical to within 2.5e-9).
- **New test:** `tests/test_reach.mjs` routes to every room and restroom in every published building from its
  entrances, on foot and step-free, through the app's own router — 1,068 of 1,068 today.
- **Not done:** Exploratory Hall (OSM rooms without corridors or stairs) and the Data & Decision Sciences plans
  (no room numbers) — see §5.

# The Akadian Map Engine

Everything private lives here: the floor plans, the schematics, the OCR, the room geometry before it is
published, and the usage counts. The engine turns published floor plans and OpenStreetMap data into the
compiled maps the app reads, and serves them.

This is the step-by-step guide to all of it. Read "How it is shaped" first; after that the sections stand
alone.

---

## How it is shaped

The engine runs **two servers from one process**:

| | Admin studio | Public server |
|---|---|---|
| Listens on | `127.0.0.1` only | every interface |
| Default port | 8081 | 8080 |
| Needs the passphrase | yes | no |
| Can | import plans, edit, build, publish, read usage | serve published maps and the app, count usage |
| Cannot | — | see a schematic, a draft, or anything unpublished |

The split is the whole security model. The public server has no code path that reaches an unpublished
file, and the admin server is not reachable from another machine. **Never expose port 8081.** If you need
the studio from elsewhere, tunnel it:

```bash
ssh -N -L 8081:127.0.0.1:8081 you@your-server
```

Then open `http://127.0.0.1:8081` on your own machine.

Private data is encrypted at rest with a key derived from your passphrase (scrypt). The key only ever
exists in the running process's memory. **There is no recovery.** Lose the passphrase and the schematics
are gone; published maps are unaffected.

---

## Before you start

Python 3.11 or newer.

```bash
pip install -r engine/requirements.txt
```

That pulls in OpenCV, PyMuPDF and an OCR model, so it is a few hundred megabytes and takes a while. You
only need it on the machine that *builds* maps. A machine that only serves them needs `fastapi`,
`uvicorn` and `cryptography`.

---

## First run

```bash
python -m engine serve
```

It prints both URLs. Open the admin one and you will be asked to create a passphrase — at least 12
characters. This is the moment that creates the vault, so choose it properly and put it in a password
manager now, not later.

Options:

```bash
python -m engine serve --home engine_data --public-port 8080 --admin-port 8081
```

`--home` is where everything is kept. The default is `engine_data/` next to the repo. Back **that** up.

---

## Quick start: the demo campuses

If you just want a working map, skip the studio and use the seed scripts.

**George Mason.** The floor plans belong to GMU, so they are not in the repository; fetch them first.

```bash
python tools/fetch_gmu_sources.py
python tools/seed_gmu.py --publish-only
```

`--publish-only` writes the public map files without needing the vault. Drop the flag and it also imports
the Johnson Center as an editable project, which does need your passphrase.

Rebuilding only the campus layer — buildings, paths, buses, food, parking — needs no PDFs at all:

```bash
python tools/seed_gmu.py --campus-only
```

**Virginia Tech.**

```bash
python tools/fetch_vt_sources.py
python tools/vt_buildings.py prepare
python tools/seed_vt.py --publish-only
```

Then open the public server. Both campuses appear in the picker.

---

## Adding a campus from scratch

1. **Find the boundary.** On [openstreetmap.org](https://www.openstreetmap.org), find the campus
   boundary and note its **way id** from the URL.
2. **Create it.** Studio → Campuses → New campus. Give it a short lowercase id (`gmu`, `vt`), a name and
   that way id. The id is permanent: it appears in every link as `?campus=<id>`.
3. **Set the hints** (optional but worth it). Hints tell the compiler things OSM does not:
   - `dorms`, `athletics` — building names to categorise
   - `levels` — floor counts for buildings OSM does not give a height for
   - `gtfs` — URLs of published bus timetables to compile in
4. **Fetch.** Campus → Fetch. This downloads the OpenStreetMap extract and any timetables. It is the
   slowest step and it hits a public API, so do not loop it.
5. **Download the basemap.** Campus → Basemap. This pulls vector tiles for the area and the font glyphs,
   so the map works offline and does not depend on anyone else's tile server at demo time.
6. **Publish.** Campus → Publish. This compiles the layer and writes
   `published/campus/<id>.json`, which is what the app reads.

Re-publish whenever you change hints, or after publishing a new indoor map that should link in.

---

## Adding a building from scratch

This is the long one. The engine takes a floor plan drawing and produces a routable indoor map: room
outlines, room numbers, walkable floor, stairs and lifts, and doors tied to real coordinates.

### 1. Create the project

Studio → Buildings → New building. You need:

- **ID** — lowercase, permanent (`gmu-jc`)
- **Name** — what people see
- **Campus ID** — the campus it belongs to
- **OSM way id** — the building's footprint in OpenStreetMap, if it has one. Supply it: it is what lets
  the engine place the plan in the real world.

### 2. Upload each floor

Floors tab → add a floor. Per floor:

- **ID** — `l1`, `l2`, `lower`
- **Level** — the storey number as an integer. This orders the floors and drives stair links. Use
  negative numbers for basements.
- **Room prefix** — the letter or digits room numbers start with on this floor
- **Digits** — how many digits a room number has (3 by default; some buildings use 4, like `1201A`)

PDF or image, up to 60 MB. On upload the engine renders the plan and runs OCR **on this machine** — no
drawing is sent anywhere — and pulls out candidate room labels.

The command-line equivalent, useful for a batch:

```bash
python tools/prepare_building.py research-hall Research-1:1 Research-2:2
python tools/prepare_building.py merten-hall Merten-1:1:4   # 4-digit room numbers
```

### 3. Align the floors

Floors must sit on top of each other or stairs will not line up. Mark one floor as the **reference**,
then for each other floor use **Auto-align**, which reports a confidence. Check it on the overlay and
nudge the offset by hand if the confidence is low. This is worth getting right; everything vertical
depends on it.

### 4. Fix the labels

Plan editor tab. OCR will get some room numbers wrong, invent a few from stray text, and miss others.
Here you correct them, delete the ones that are not rooms, and mark **voids** — courtyards, atria and
anything else that is drawn but is not floor.

This is the step that takes real time, and it is the one that decides whether search finds a room.

### 5. Place the entrances

Entrances tab. Each entrance needs a point on the plan **and** a real latitude and longitude, because
that is the join between the outdoor route and the indoor one. If the building is in OpenStreetMap with
tagged entrance nodes, the engine offers them and you copy the coordinates across.

A building needs at least one. With fewer than two, the engine falls back to fitting the plan outline to
the OSM footprint to work out where it is.

### 6. Link the floors

Stairs and lifts that connect floors. The builder finds most of them from the drawings; add anything it
missed as an extra link, naming the label on each floor.

### 7. Build

Build & publish tab → Build. This runs the whole pipeline: room shapes, the walkable grid, stair and lift
links, and the routing graph. The report tells you, per floor, how many labelled rooms and room shapes
came out and **how many separate walkable components** there are.

Watch that last number. More than one component means part of the floor cannot be walked to from the
rest — usually a doorway the drawing closed off. One component per floor is what you want.

The build produces a *draft*. Nothing is public yet.

### 8. Publish

Build & publish → Publish. This writes `published/buildings/<id>.json`.

Then go to the campus and **publish it again**, so the campus layer links to the new indoor map. A campus
only links buildings that are actually published, so this order matters.

---

## Usage counts

The public server keeps anonymous tallies so there is evidence of how much the app is used. Studio →
Usage shows them, with a range picker and a CSV download.

**What is counted:** app opens, launches from the home screen, searches, places opened, routes, turn-by-turn
starts, arrivals, indoor views (and which building), study-room routes, bus times, parking, saved cars.

**What is not, and cannot be reconstructed:** who anyone is, where they went, which room, what order they
did things in, or what time of day. There is no identifier of any kind, and the finest resolution kept is
one UTC day. See `engine/usage.py`.

Two honest limits to keep in mind when you quote these numbers:

- An **open is an open, not a user.** Nothing distinguishes one device from another, so you cannot derive
  a user count from this and must not present one.
- Anything can post to the collect endpoint. There is a rate limit per address, but treat the figures as
  a floor on real interest rather than an audited number, and say so.

Counting only happens when the app is served **by the engine**, which sets the endpoint the app posts to.
The static GitHub Pages build has no server, so it counts nothing. If you want numbers, serve the app from
the engine. Users can also switch it off in the app's settings, and a device sending Do Not Track is never
counted.

Counts are in `<home>/usage/<YYYY-MM>.json` as plain counters. They are not encrypted, because the public
server runs without the passphrase and there is nothing personal in them.

```bash
curl -o usage.csv http://127.0.0.1:8081/api/usage.csv   # with an admin session cookie
```

---

## The static build

For a demo with no server — GitHub Pages, a USB stick, any static host:

```bash
python tools/export_static.py            # writes docs/
python tools/export_static.py --out dist
```

Everything the app does runs in the browser, so the static copy behaves the same: search, routing, 3D,
GPS, parking, saved places. Only *published* maps are copied — exactly what the public server would hand
to anyone. Schematics, renders, OCR and the vault are never touched, and the studio is not included.

The one thing it cannot do is count usage.

---

## Running it for other people

- Put a reverse proxy (Caddy, nginx) in front of the public port and give it HTTPS. The app needs a
  secure context for geolocation and the service worker, so **plain HTTP will not work** anywhere except
  `localhost`.
- Bind the public server to a local interface and let the proxy reach it, or leave it on `0.0.0.0` behind
  a firewall. Either way, only 8080 is ever exposed.
- Keep 8081 on loopback. Use the SSH tunnel above.
- Run it under systemd or similar so it restarts. There is no state in memory that matters except the
  unlocked vault, and the public server does not need it.
- After a restart the vault is locked. The public server keeps serving published maps regardless; you
  only need to unlock to edit or to read usage.

---

## Backups, and the passphrase

Back up the whole engine home. It holds:

| Path | What | If you lose it |
|---|---|---|
| `vault.json` | the salt and passphrase check | everything encrypted is unreadable |
| `projects/<id>/` | project settings and encrypted schematics | re-import and re-label the building |
| `campuses/<id>/` | campus settings and the OSM extract | re-fetch from OpenStreetMap |
| `published/` | the compiled public maps | rebuild and re-publish |
| `usage/` | the anonymous counts | gone, and not reconstructible |

The passphrase is not in any of them. Store it separately. A backup without it recovers the published
maps and the usage counts, and nothing else.

---

## Troubleshooting

**"Engine is locked" in the studio.** The process restarted. Unlock it again.

**Auto-align confidence is low.** The two plans are drawn at different scales or crops. Check the overlay
and set the offset by hand.

**A room will not route.** Build and look at the walkable components for that floor. More than one means
the drawing seals part of it off. The router already refuses to snap into a tiny sealed pocket and will
route to the nearest reachable spot instead, but the real fix is in the plan editor.

**A building does not appear indoors on the campus.** Publish the building, then publish the campus. The
campus only links maps that exist at the time it is compiled.

**A timetable did not download.** Some transit sites refuse scripted downloads. The fetch logs it and
carries on without that feed; save the GTFS zip by hand and point the hint at a local copy.

**No usage numbers.** You are serving the static build, or the day has not flushed yet (counts are held
in memory for up to 20 seconds), or everyone has it switched off.

---

## On disk

```
<engine home>/
  vault.json                            passphrase check + KDF salt
  projects/<building-id>/
    settings.enc                        floors, labels, entrances, links
    blobs/*.enc                         schematics, renders, OCR, drafts, debug overlays
  campuses/<campus-id>/settings.enc     campus settings + the OSM extract
  published/
    campus/<id>.json                    PUBLIC: the compiled campus layer
    buildings/<id>.json                 PUBLIC: the compiled indoor map
    tiles/<campus-id>/z/x/y.pbf         PUBLIC: basemap tiles
    fonts/<stack>/<range>.pbf           PUBLIC: glyphs
  usage/<YYYY-MM>.json                  anonymous day counters
```

Only `published/` is ever served. Everything else stays on the machine.

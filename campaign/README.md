# Akadian Vertex — spring launch campaign

Print and social artwork for the first week of spring semester, January 2027. It sells one moment:
nobody knows where their classes are, and the only tool anyone has is a maps app that drops them at
the front of a building. The line the whole set hangs on:

> **GPS gets you to the building. Vertex gets you to the room.**

Everything here is generated from the app itself: the logo is parsed out of `app/icons/mark.svg`,
the palette comes from `app/js/themes.js`, the buildings are the real floor plans from
`docs/data/buildings/`, and the orange route drawn through them is computed at build time by a
Python port of the app's own router. No figure appears on a piece that the build has not checked
against the data first.

```bash
python campaign/make_campaign.py
```

That writes every `.svg` master and renders the PNG and PDF beside it — sixteen pieces, about ten
seconds. Other ways to run it:

```bash
python campaign/make_campaign.py --render
```

```bash
python campaign/make_campaign.py --check
```

```bash
python campaign/make_campaign.py --qr
```

```bash
python campaign/make_campaign.py posters social
```

`--render` rebuilds PNG and PDF from the `.svg` files **without rewriting them**, which is what you
want after hand-editing a master in Illustrator or Inkscape. `--check` runs the fact, claim and
trademark checks and stops. `--qr` prints the exact box the real QR code goes in, for every piece. A
bare word argument filters to pieces whose path contains it.

Requires `pillow` and `reportlab` (already used by `tools/make_docs.py`). Nothing else.

---

## The four concepts

| | Concept | Headline | Where it runs |
| --- | --- | --- | --- |
| **A** | Better than GPS | *GPS stops at the door. Vertex doesn't.* | Both dark posters, feed post, wide banner |
| **B** | Find your class | *Research Hall 423? Found it.* — and on the handout, *Don't be the one walking in at 9:07.* | Both light posters, half-page flyer, feed post, story (*Walk in like you've been here for years.*) |
| **C** | Offline | *No bars. Still works.* | Story, wide banner |
| **D** | No install | *No app store. Just add it.* | Quarter-page flyer, feed post, story |

A and B lead. A makes the promise — Vertex keeps going where GPS gives up — and draws it: a white
GPS dot outside the building, a dashed approach to the door, then the orange Vertex route inside, up
the stairs, to the room. B makes it personal: the app's real search, typed the way a schedule reads,
and the answer it really gives. C and D answer the next two questions a student asks: *will it work
in here*, and *do I have to install something*.

### What the campaign deliberately does not say

**That the phone knows where you are inside a building.** It does not: Vertex uses GPS outdoors, and
indoors it routes from the door you walk in (`app/js/main.js`, first two lines — GPS does not work
reliably inside). So the pieces sell "better than GPS" the true way: GPS gets you to the door, Vertex
gets you to the room. `make_campaign.py` fails the build if any artwork claims indoor positioning.

**That it finds any room on campus.** Room-by-room directions exist in four buildings — Research
Hall, Merten Hall, the Johnson Center and The HUB, 633 rooms. Every other building, Vertex gets you
to the door. Every piece that promises "the room" names the four or carries that scope line.

The full wording, five social captions, the r/gmu post and the two sentences for a professor are in
[copy.md](copy.md).

---

## What each file is

Every piece exists three ways: `.svg` is the editable master, `.png` is the render you actually
print or upload, `.pdf` is vector and CMYK for a print shop.

### `posters/`

| File | Trim size | Theme | Print on | Where it goes |
| --- | --- | --- | --- | --- |
| `poster-a-gps-letter` | 8.5 × 11 in | dark | 100 lb / 270 gsm satin or matte cover | corridors, residence halls, the walk between parking and class |
| `poster-a-gps-tabloid` | 11 × 17 in | dark | 100 lb satin cover | building lobbies and stair landings, anywhere read from across a room |
| `poster-b-findclass-letter` | 8.5 × 11 in | light | 80 lb text is fine; 100 lb cover is better | outside lecture halls, department boards, Research Hall and Merten |
| `poster-b-findclass-tabloid` | 11 × 17 in | light | 100 lb cover | the main entrances of Research Hall, Merten Hall, the JC and The HUB |

Put **A** where people are walking *to* class and **B** where they arrive *at* a building and
realise they do not know the room — inside the front doors is the best spot on campus for it.

### `flyers/`

| File | Size | What it is |
| --- | --- | --- |
| `flyer-findclass-half` | 8.5 × 5.5 in, landscape | one half-page flyer: *Don't be the one walking in at 9:07.* The search, the route, a code |
| `flyer-install-quarter` | 4.25 × 5.5 in, portrait | one quarter-page flyer, concept D. The three steps to add it to a home screen |
| `sheet-half-2up-letter` | 8.5 × 11 in | **print this one.** Two half-page flyers on a Letter sheet, with a cut guide across the middle |
| `sheet-quarter-4up-letter` | 8.5 × 11 in | **print this one.** Four quarter-page flyers on a Letter sheet, with cut guides |

Print the imposed sheets, not the single units — the units exist so the design can be edited once.
Cut on the dashed lines; the tick marks at the sheet edges are there to line a guillotine up on.
Nothing important sits within 0.3 in of a cut. 80 lb text paper, single-sided.

### `social/`

PNG only, at native pixel size, no PDF.

| File | Size | Concept | Use |
| --- | --- | --- | --- |
| `a-gps-feed-1080` | 1080 × 1080 | A | Instagram feed |
| `a-gps-banner-1600x900` | 1600 × 900 | A | Discord, Reddit, a link preview |
| `b-findclass-feed-1080` | 1080 × 1080 | B | Instagram feed |
| `b-findclass-story-1080x1920` | 1080 × 1920 | B | Instagram and TikTok story |
| `c-offline-story-1080x1920` | 1080 × 1920 | C | Instagram and TikTok story |
| `c-offline-banner-1600x900` | 1600 × 900 | C | Discord server banner |
| `d-install-feed-1080` | 1080 × 1080 | D | Instagram feed |
| `d-install-story-1080x1920` | 1080 × 1920 | D | Instagram and TikTok story |

Stories keep everything between 300 px and 1670 px from the top, clear of the app's own interface.

---

## The two buildings in the artwork

| Scene | Building | Walk | Used on |
| --- | --- | --- | --- |
| `gps` | Johnson Center (ground floor left out — the walk never uses it) | West entrance → room 342, the computer lab on Floor 3 | A posters, A feed, the offline phones |
| `find` | Research Hall | West entrance (by the rotunda) → room 423 on Floor 4 | B posters, B feed and story, the half flyer, the A banner |

Both doors were picked because they face the viewer in the drawing, so the GPS approach outside is
visible. The walks are whatever the app's search returns from those doors; the captions' distances
and floor counts are measured from them. To change a walk, edit `scene()` in `kit.py` — a room that
is not in the data, or one with no route to it, stops the build rather than being drawn anyway.

---

## The QR code

**Every piece carries a placeholder, not a code.** A white rounded square with three finder marks
and the word PLACEHOLDER. The target URL is not decided yet, so nothing here points anywhere.

To drop the real one in:

1. Decide the URL. Use one you control and can repoint later — a short link or your own domain
   beats a bare GitHub Pages URL, because posters outlive a hosting decision.
2. Generate the code: error correction **M**, black on white, no logo in the middle, no colour.
   Do not use a generator that proxies through a tracking domain that could expire.
3. Run `python campaign/make_campaign.py --qr`. It prints, for every piece, the placeholder's box in
   points, inches and PNG pixels.
4. Place the code inside that box, in the same spot, leaving the quiet zone: the placeholder's white
   panel is 8.5% larger than the code on every side, and that margin is part of the code working.
   Keep the white panel. A QR on the dark artwork will not scan.
5. Re-render and test-scan the actual printed sheet, in the light it will hang in, on at least two
   phones — one iPhone, one Android.

Sizes as built: 1.08 in on the Letter posters, 1.83 in on the Tabloids, 0.72 in on the half-page
flyer, 0.78 in on the quarter. A code scans from roughly ten times its own width, so the Letter
posters want a wall people can walk up to; use the Tabloid where they cannot.

---

## Printing notes

**Colour.** The PDFs are CMYK, built for a press. Three colours are hand-set rather than converted:
the dark base `#16181d` prints as a rich black (60/40/40/100) so a large dark area does not go flat
or brown; light type on dark knocks out to paper rather than printing a pale tint; dark type on
light prints on the black plate only, so small text cannot go fuzzy from misregistration. Everything
else converts by the standard formula. The accent orange `#f0a04a` is inside CMYK gamut and prints
slightly duller than it looks on screen — that is expected.

**Which file to hand over.** The PNGs are 300 DPI and carry the real Cinzel wordmark, so they are the
safe thing to print from anywhere, including a campus printer. The PDFs are vector and CMYK, which a
print shop will prefer, but reportlab cannot embed a woff2, so the display face falls back to
whatever serif the build found (it says which, at the top of its output). If you need vector *and*
Cinzel, install Cinzel from `app/vendor/fonts/` and export the `.svg` master from Illustrator or
Inkscape instead.

**Bleed.** Every piece is laid out at trim size with the background running to the edge. Nothing
important sits within 0.5 in of a poster's edge or 0.3 in of a flyer's cut, so you can print
borderless, or at 100% and let a printer's own margin eat the edge. If a shop insists on bleed,
scale to 101.5% and centre.

**Toner.** The dark pieces cover a Letter sheet in near-solid ink. On a laser printer that is slow,
expensive and often streaky. Use the light B poster for anything you are running off yourself, and
send the dark ones to a shop.

---

## Posting schedule

**T** is the first day of spring classes. Check the official academic calendar for the exact date —
it is mid-January 2027 — and count back from it. The whole campaign peaks on T and the two days
after it: that is when people are actually lost.

| When | Do |
| --- | --- |
| **T−14** | Decide the URL and generate the QR code. Drop it into the masters and re-render. |
| **T−12** | Print. Test-scan a real printed poster on two phones before the full run. Suggested first run: 15 × Tabloid A, 15 × Tabloid B, 40 × Letter B, 20 × Letter A, 50 sheets of the 4-up quarter flyer (200 flyers), 30 sheets of the 2-up half (60 flyers). |
| **T−10** | Check where posting is allowed. Most boards need a stamp or a date; some buildings limit posters per board. Ask rather than have them pulled down. |
| **T−7** | Posters go up. **Tabloid B inside the main doors of Research Hall, Merten Hall, the JC and The HUB** — the exact spot where someone realises they do not know the room. Letter B outside lecture halls. A posters on the walks between buildings, in residence halls and by the bus stops. |
| **T−7, evening** | The r/gmu post (see [copy.md](copy.md)). Sunday evening gets the most reach. Answer every comment that day. |
| **T−6** | Instagram: feed post A (`a-gps-feed-1080`) with caption 1. Drop `a-gps-banner-1600x900` into the GMU Discord servers and any class or club GroupMe you are actually in — as yourself, with a sentence, not as an advert. |
| **T−4** | Instagram: feed post B (`b-findclass-feed-1080`) with caption 2. People are looking at their schedules now. |
| **T−2** | Feed post D (`d-install-feed-1080`) with caption 5: *add it before your first class*. Story C the same evening, as people arrive back on campus and meet the wi-fi again. |
| **T−1, evening** | Story B (`b-findclass-story-1080x1920`) with caption 3 — the night before, when people check where tomorrow's classes are. Email the two sentences to any professor who might read them out. |
| **T, morning** | The big day. Story D at 7:30 a.m. Half-page flyers handed out outside Research Hall and the JC from 8:30 to 10:30, the first class changeovers. Re-share story B at 11:45 for the afternoon classes. |
| **T+1 … T+3** | Still the first week, still lost. Quarter-page flyers on JC tables. Walk the poster route and replace what has come down — expect to lose a third in the first week. |
| **T+5 … T+10** | Add/drop: people switch into new sections in new rooms. Repost B. |
| **Next semester** | Run it again, with real usage numbers by then. That is a different campaign, and a much easier one. |

Two things worth holding to. **Post as a person, not a brand** — a student who built something gets
read; a product account gets scrolled past. And **nothing in this campaign claims a number it does
not have, or a feature the app does not have.**

---

## How it is built

| File | What it does |
| --- | --- |
| `make_campaign.py` | the build. Checks the claims, writes the masters, renders, checks for university marks and indoor-positioning claims, lists stale files |
| `designs.py` | every piece, laid out. One function per piece, and the list of them at the bottom |
| `kit.py` | shared furniture: themes, the logo lockup, the QR placeholder, the floor stack with the GPS approach, the search card, the phone |
| `brand.py` | palette, the mark parsed from `app/icons/mark.svg`, and the building and campus data the copy quotes |
| `copytext.py` | every word that appears on artwork, checked against `copy.md` at build time |
| `route.py` | a Python port of `app/js/router.js`, so the routes in the art are real ones |
| `svgdoc.py` | writes and reads the SVG subset the masters use |
| `render.py` | SVG → PNG (Pillow) and SVG → CMYK PDF (reportlab) |

What the build refuses to let through:

- **a figure that drifts.** Every number in the copy — 633 rooms, 4 buildings, 163 buildings, the
  2.5-second deadline, room 423 being on the fourth floor — is compared against the app's data. If
  the app maps a fifth building, the build fails until the copy says so.
- **a drawn walk that does not exist.** The rooms and routes are looked up and routed at build time.
- **copy that has drifted from `copy.md`.** Every on-artwork string must appear in both.
- **a claim of indoor positioning.** Phrases like *indoor GPS* or *knows where you are inside*.
- **a university mark.** *Mason* may appear only in the independence line or in the descriptive
  phrase *for George Mason*.

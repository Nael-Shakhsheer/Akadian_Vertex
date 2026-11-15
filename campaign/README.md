# Akadian Vertex — spring launch campaign

Print and social artwork for the start of spring semester, January 2027. Everything here is
generated from the app itself: the logo is parsed out of `app/icons/mark.svg`, the palette comes from
`app/js/themes.js`, the Johnson Center floor plates are the real plans from
`docs/data/buildings/gmu-jc.json`, and the walking route drawn across them is computed at build time
by a Python port of the app's own router. No figure appears on a poster that the build has not
checked against the data first.

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
want after hand-editing a master in Illustrator or Inkscape. `--check` runs the fact and trademark
checks and stops. `--qr` prints the exact box the real QR code goes in, for every piece. A bare word
argument filters to pieces whose path contains it.

Requires `pillow` and `reportlab` (already used by `tools/make_docs.py`). Nothing else.

---

## The four concepts

| | Concept | Line | Where it runs |
| --- | --- | --- | --- |
| **A** | Indoor routing | *Find the room, not the building.* | Both posters, feed post, wide banner |
| **B** | Study rooms | *Where is a free study room?* | Both posters, half-page flyer, feed post, story |
| **C** | Offline | *No bars. Still works.* | Story, wide banner |
| **D** | No install | *No app store. Just add it.* | Quarter-page flyer, feed post, story |

A and B lead because they are the two things nothing else on campus does: directions to a room
rather than a building, and a map that survives the wi-fi. C and D answer the two objections a
student raises in the next breath — *will it work in here* and *do I have to install something*.

The full wording, the social captions, the r/gmu post and the two sentences for a professor are in
[copy.md](copy.md).

---

## What each file is

Every piece exists three ways: `.svg` is the editable master, `.png` is the render you actually
print or upload, `.pdf` is vector and CMYK for a print shop.

### `posters/`

| File | Trim size | Theme | Print on | Where it goes |
| --- | --- | --- | --- | --- |
| `poster-a-indoor-letter` | 8.5 × 11 in | dark | 100 lb / 270 gsm satin or matte cover | corridor walls, residence hall boards, lift lobbies |
| `poster-a-indoor-tabloid` | 11 × 17 in | dark | 100 lb satin cover | the Johnson Center itself — atrium boards, stair landings, anywhere read from across a room |
| `poster-b-studyrooms-letter` | 8.5 × 11 in | light | 80 lb text is fine; 100 lb cover is better | corkboards, outside study rooms, library and department boards |
| `poster-b-studyrooms-tabloid` | 11 × 17 in | light | 100 lb cover | JC second and third floors, where the study rooms actually are |

The dark posters are the better-looking pair and the ones to pay for. The light B poster is the one
to photocopy by the hundred — it costs almost nothing in toner and it carries the sharpest hook.

### `flyers/`

| File | Size | What it is |
| --- | --- | --- |
| `flyer-studyrooms-half` | 8.5 × 5.5 in, landscape | one half-page flyer, concept B. Table handout |
| `flyer-install-quarter` | 4.25 × 5.5 in, portrait | one quarter-page flyer, concept D. Pocket handout, the three steps to add it to a home screen |
| `sheet-half-2up-letter` | 8.5 × 11 in | **print this one.** Two half-page flyers on a Letter sheet, with a cut guide across the middle |
| `sheet-quarter-4up-letter` | 8.5 × 11 in | **print this one.** Four quarter-page flyers on a Letter sheet, with cut guides |

Print the imposed sheets, not the single units — the units exist so the design can be edited once.
Cut on the dashed lines; the tick marks at the sheet edges are there to line a guillotine up on.
Nothing important sits within 0.3 in of a cut. 80 lb text paper, printed double-sided only if you
have something for the back (there is no back design; a blank back is correct).

### `social/`

PNG only, at native pixel size, no PDF.

| File | Size | Concept | Use |
| --- | --- | --- | --- |
| `a-indoor-feed-1080` | 1080 × 1080 | A | Instagram feed |
| `a-indoor-banner-1600x900` | 1600 × 900 | A | Discord, Reddit, a link preview |
| `b-studyrooms-feed-1080` | 1080 × 1080 | B | Instagram feed |
| `b-studyrooms-story-1080x1920` | 1080 × 1920 | B | Instagram and TikTok story |
| `c-offline-story-1080x1920` | 1080 × 1920 | C | Instagram and TikTok story |
| `c-offline-banner-1600x900` | 1600 × 900 | C | Discord server banner |
| `d-install-feed-1080` | 1080 × 1080 | D | Instagram feed |
| `d-install-story-1080x1920` | 1080 × 1920 | D | Instagram and TikTok story |

Stories keep everything between 300 px and 1660 px from the top, clear of the app's own interface.

---

## The QR code

**Every piece carries a placeholder, not a code.** A white rounded square with three finder marks
and the word PLACEHOLDER. The target URL is not decided yet, so nothing here points anywhere.

To drop the real one in:

1. Decide the URL. Use one you control and can repoint later — a short link or your own domain
   beats a bare GitHub Pages URL, because posters outlive a hosting decision.
2. Generate the code: error correction **M**, black on white, no logo in the middle, no colour.
   Any generator will do. Do not use one that proxies through a tracking domain that could expire.
3. Run `python campaign/make_campaign.py --qr`. It prints, for every piece, the placeholder's box in
   points, inches and in PNG pixels.
4. Place the code inside that box, in the same spot, leaving the quiet zone: the placeholder's white
   panel is 8.5% larger than the code on every side, and that margin is part of the code working.
   Keep the white panel. A QR on the dark artwork will not scan.
5. Re-render and test-scan the actual printed sheet, in the light it will hang in, on at least two
   phones — one iPhone, one Android.

Sizes as built: 1.08 in on the Letter posters, 1.83 in on the Tabloids, 0.69 in on the half-page
flyer, 0.78 in on the quarter. A code scans from roughly ten times its own width, so the Letter
posters want a wall people can walk up to; use the Tabloid where they cannot.

---

## Printing notes

**Colour.** The PDFs are CMYK, built for a press. Three colours are hand-set rather than converted:
the dark base `#16181d` prints as a rich black (60/40/40/100) so a large dark area does not go flat
or brown; light type on dark knocks out to paper rather than printing a pale tint; dark type on
light prints on the black plate only, so small text cannot go fuzzy from misregistration. Everything
else converts by the standard formula. The accent orange `#f0a04a` is inside CMYK gamut and prints
slightly duller than it looks on screen — that is expected, and no substitute is needed.

**Which file to hand over.** The PNGs are 300 DPI and carry the real Cinzel wordmark, so they are the
safe thing to print from anywhere, including a campus printer. The PDFs are vector and CMYK, which a
print shop will prefer, but reportlab cannot embed a woff2, so the display face falls back to
whatever serif the build found (it says which, at the top of its output). If you need vector *and*
Cinzel, install Cinzel from `app/vendor/fonts/` and export the `.svg` master from Illustrator or
Inkscape instead.

**Bleed.** Every piece is laid out at trim size with the background running to the edge. Nothing
important sits within 0.5 in of a poster's edge or 0.3 in of a flyer's cut, so you can print
borderless, or print at 100% and let a printer's own margin eat the edge, without losing anything.
If a shop insists on bleed, scale to 101.5% and centre.

**Toner.** The dark pieces cover a Letter sheet in near-solid ink. On a laser printer that is slow,
expensive and often streaky. Use the light B poster for anything you are running off yourself, and
send the dark ones to a shop.

---

## Posting schedule

**T** is the first day of spring classes. Check the official academic calendar for the exact date —
it is mid-January 2027 — and count back from it. Everything before T−7 is preparation.

| When | Do |
| --- | --- |
| **T−14** | Decide the URL and generate the QR code. Drop it into the masters and re-render. |
| **T−12** | Print. Test-scan a real printed poster on two phones before committing to the full run. Suggested first run: 15 × Tabloid A, 40 × Letter B, 10 × Letter A, 50 sheets of the 4-up quarter flyer (200 flyers), 20 sheets of the 2-up half (40 flyers). |
| **T−10** | Check where posting is actually allowed. Most boards need a stamp or a date; some buildings have a limit per board. Ask rather than find out by having them pulled down. |
| **T−7** | Posters go up. The Johnson Center first and heaviest — atrium, all four floors, both stair landings, outside the study rooms on 2 and 3. Then Research Hall, Merten Hall and The HUB, then residence hall boards. |
| **T−7, evening** | The r/gmu post (see [copy.md](copy.md)). Sunday evening or Monday morning gets the most reach. Answer every comment that day. |
| **T−6** | Instagram: feed post A (`a-indoor-feed-1080`) with caption 1, and story A. |
| **T−5** | Drop `a-indoor-banner-1600x900` into the GMU Discord servers and any class or club GroupMe you are actually in. Post it as yourself, with a sentence, not as an advert. |
| **T−4** | Instagram: feed post B (`b-studyrooms-feed-1080`) with caption 2, and story B. This is the strongest single post of the campaign. |
| **T−2** | Story C, the offline one. People are arriving on campus and meeting the wi-fi again. |
| **T−1** | Email the two sentences to any professor who might read them out. Ask, do not assume. |
| **T** | First day. Hand out quarter-page flyers at the Johnson Center over lunch. Story D in the morning, when people are standing in queues with their phones out. |
| **T+1 … T+3** | Half-page flyers on JC tables. Walk the poster route and replace what has come down — expect to lose a third in the first week. |
| **T+5** | Feed post D with caption 4. By now people have seen the posters; this one closes the loop on how to keep it. |
| **T+10** | Syllabus week is over and the first real assignments land. Repost B, the study-room post — demand for a study room peaks now, not in week one. |
| **Midterms, then finals** | B again, both times, with the posters refreshed in the JC. This is the moment the product is most obviously useful; do not save the budget for the launch and have nothing left. |

Two things worth holding to. **Post as a person, not a brand** — a student who built something gets
read; a product account gets scrolled past. And **nothing in this campaign claims a number it does
not have.** When there are real usage figures, that is a new campaign and a much easier one.

---

## How it is built

| File | What it does |
| --- | --- |
| `make_campaign.py` | the build. Checks the claims, writes the masters, renders, checks for university marks |
| `designs.py` | every piece, laid out. One function per piece, and the list of them at the bottom |
| `kit.py` | shared furniture: themes, the logo lockup, the QR placeholder, the floor stack, the room grid, the phone |
| `brand.py` | palette, the mark parsed from `app/icons/mark.svg`, and the campus data the copy quotes |
| `copytext.py` | every word that appears on artwork, checked against `copy.md` at build time |
| `route.py` | a Python port of `app/js/router.js`, so the route on the posters is a real one |
| `svgdoc.py` | writes and reads the SVG subset the masters use |
| `render.py` | SVG → PNG (Pillow) and SVG → CMYK PDF (reportlab) |

Three things the build refuses to let through:

- **a figure that drifts.** Every number in the copy is compared against the app's data. If the
  Johnson Center gains a study room, the build fails until the copy is corrected.
- **copy that has drifted from `copy.md`.** Headlines and decks must appear in both, word for word.
- **a university mark.** The word *Mason* may only appear inside the independence line or in the
  descriptive phrase *for George Mason*; anywhere else fails the build.

### The two rules in the artwork

**No university logo, wordmark or implied endorsement.** The app ships campus initials as a monogram
for exactly this reason, and the campaign holds the same line. Every printed piece carries, at the
foot: *An independent student project. Not affiliated with, endorsed or sponsored by George Mason
University.*

**Nothing invented.** There are no users yet, so there are no counts, ratings, quotes or awards
anywhere in this campaign. The numbers that do appear — 23 group study rooms, 320 rooms over four
floors, 163 buildings, 25 places to eat, 7 CUE routes, 26 stops, the 2.5-second network deadline —
are all read from the app at build time. The walk shown on the posters is the route the app's own
search returns from the Johnson Center's north entrance to group study room 320H, and the "about
150 m" caption is measured from that route rather than guessed.

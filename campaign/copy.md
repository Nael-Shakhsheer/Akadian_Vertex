# Akadian Vertex — launch campaign copy

Everything the campaign says, in one place. The artwork pulls the short strings from
`campaign/copytext.py`, and `make_campaign.py` fails the build if a headline or a deck here stops
matching what the posters set — so edit both, or edit here and run the build to find out where it
broke.

## The two rules this copy is written under

**No university marks, no implied endorsement.** The app ships campus initials as a monogram because
George Mason's logos and wordmarks are not ours to use, and the campaign holds the same line. The
university's name appears only descriptively — *a campus map for George Mason students* — never as a
badge, never in a logo, never in a way that suggests the university made this or blessed it. Every
printed piece carries, in small type at the foot:

> An independent student project. Not affiliated with, endorsed or sponsored by George Mason
> University.

**No invented numbers.** There are no users yet, so there are no download counts, no star ratings, no
testimonials and no awards anywhere in this campaign. Every figure that does appear is read out of
the app's own data at build time and checked before a single pixel is drawn:

| Claim | Where it comes from |
| --- | --- |
| 23 group study rooms | `docs/data/buildings/gmu-jc.json` — rooms named *Group Study Room*: 3 on Floor 1, 8 on Floor 2, 12 on Floor 3 |
| 320 rooms, 4 floors in the Johnson Center | the same file |
| 4 buildings mapped indoors | `docs/data/campuses.json` — Johnson Center, Research Hall, Merten Hall, The HUB |
| 163 buildings, 25 places to eat, 7 CUE routes, 26 stops | `docs/data/campus/gmu.json` |
| the 2.5-second network deadline | `NET_TIMEOUT` in `app/sw.js` |
| "about 150 m and two floors up" | measured from the route the artwork draws, computed at build time |

The walk on the posters is not an illustration. It is the route the app's own search returns — the
same grids, costs and stair links as `app/js/router.js` — from the Johnson Center's north entrance to
group study room 320H on the third floor.

---

## Poster headlines

**A · Indoor routing** (the lead concept — dark, Letter and Tabloid, and the feed post and banner)

> Find the room, not the building.

Deck: *Indoor, room-level walking directions through the Johnson Center: four floors, 320 rooms, and
the walk from the front door to the door you actually want.*

Kicker: *3D campus maps · indoor directions*
Pull line: *Every other campus map stops at the front door.*

**B · Study rooms** (light, Letter and Tabloid, the half-page flyer, a feed post and a story)

> Where is a free study room?

Deck: *The Johnson Center has 23 group study rooms across three floors. Vertex knows where every one
of them is, and walks you to the door.*

Kicker: *23 group study rooms · Johnson Center*
Pull line: *23 group study rooms. Vertex walks you to one.*

**C · Offline** (dark, a story and a banner)

> No bars. Still works.

Deck: *Campus wi-fi does not fail, it hangs. Vertex gives the network 2.5 seconds, then draws the map
already sitting on your phone.*

Kicker: *Built for bad campus wi-fi*
Pull line: *The map is already on your phone.*

**D · No install** (dark, the quarter-page flyer, a feed post and a story)

> No app store. Just add it.

Deck: *Vertex is a web page, not a download. Open the link, add it to your home screen, and it opens
full-screen like any other app.*

Kicker: *No install · no account · no download*
Pull line: *No app store. No account. No download.*

### The three things it does, everywhere

- **Room-level indoors** — Four buildings mapped floor by floor: the Johnson Center, Research Hall, Merten Hall and The HUB.
- **Works on bad wi-fi** — A map you have opened stays on your phone, so a dead spot in a stairwell does not strand you.
- **Nothing to install** — No app store and no account. Open the link and add it to your home screen.
- **The rest of campus too** — 163 buildings, 25 places to eat, and 7 CUE routes across 26 stops.

Cut to one line each, for posters and anywhere else read at a glance:

- **Room-level indoors** — Johnson Center, Research Hall, Merten Hall, The HUB.
- **Works on bad wi-fi** — A map you have opened stays on your phone.
- **Nothing to install** — No app store, no account. Add it to your home screen.

Sign-off line: *Akadian Vertex · a 3D campus map for George Mason students*

---

## Social captions

Four variants. One per concept, so a week of posts does not read like the same sentence four times.
Each is written to stand on its own if the image never loads.

### 1 — Indoor routing (pairs with `a-indoor-feed-1080` or `a-indoor-banner-1600x900`)

> Campus maps are great right up until you are inside the building.
>
> Akadian Vertex maps the Johnson Center floor by floor — all four levels, 320 rooms — and gives you
> walking directions to the actual door. Front entrance to third-floor study room, turn by turn.
>
> It is a web page. No app store, no account. Link in bio.
>
> #GeorgeMason #GMU #Mason2031 #PatriotLife #FairfaxVA #CampusLife #StudentBuilt #WebDev

### 2 — Study rooms (pairs with `b-studyrooms-feed-1080` or `b-studyrooms-story-1080x1920`)

> There are 23 group study rooms in the JC. Three on the first floor, eight on the second, twelve on
> the third.
>
> Knowing that is the easy part. Vertex is the part that walks you to one — indoors, floor by floor,
> to the right door.
>
> Opens in your browser. Add it to your home screen and it behaves like an app.
>
> #GeorgeMason #GMU #JohnsonCenter #StudySpot #FinalsPrep #MasonNation #CampusMap

### 3 — Offline (pairs with `c-offline-story-1080x1920` or `c-offline-banner-1600x900`)

> Campus wi-fi does not fail. It hangs — one bar, nothing loading, and you are standing in a stairwell
> guessing.
>
> Vertex gives the network two and a half seconds. After that it draws the map it already has on your
> phone and gets on with it.
>
> Built for the wi-fi we actually have.
>
> #GMU #GeorgeMason #CampusWifi #PWA #OfflineFirst #StudentBuilt #MasonNation

### 4 — No install (pairs with `d-install-feed-1080` or `d-install-story-1080x1920`)

> No app store. No account. No 180 MB download for a map.
>
> Open the link, hit Add to Home Screen, and Akadian Vertex sits on your phone like any other app —
> full-screen, and it still works when the wi-fi gives up.
>
> 3D campus map, indoor directions to the room, CUE routes and somewhere to eat.
>
> #GeorgeMason #GMU #PatriotLife #AddToHomeScreen #WebApp #CampusLife #SpringSemester

**On hashtags.** Keep the first three or four — they are the ones GMU students actually browse. The
rest are padding and can go. Do not use any tag that reads as an official university account or
programme.

---

## Reddit — r/gmu

Post as yourself, not as a brand. Flair it as a project or a resource if the subreddit has one, and
read the self-promotion rules before posting. Reply to every comment for the first day.

**Title:** I built a 3D campus map that gives you walking directions to the room, not just the building

**Body:**

> I am a student here and I got tired of campus maps that drop you at a front door and wish you luck.
> So over the last few weeks I built Akadian Vertex: a 3D map of campus where the Johnson Center,
> Research Hall, Merten Hall and The HUB are mapped indoors, floor by floor, and you can ask for
> directions to an actual room number and get a walking route that goes in the door, down the right
> corridor and up the right stairs.
>
> The JC is the one I have put the most into — four floors, 320 rooms, including all 23 group study
> rooms. Search a room, and it routes you there from whichever entrance you are closest to.
>
> Two things that might matter more than the 3D:
>
> - It works on bad wi-fi. It is a progressive web app: it gives the network 2.5 seconds, then falls
>   back to the copy of the map already on your phone.
> - There is nothing to install. It is a web page. Open it, Add to Home Screen, and it opens
>   full-screen like an app. No account, no app store.
>
> Also on there: 163 buildings across campus, 25 places to eat, and the CUE routes and stops.
>
> It is not official and it is not affiliated with the university — it is just mine, and it is free.
> The floor plans came from public sources and OpenStreetMap, so if a room is wrong or missing, tell
> me and I will fix it. Virginia Tech has Torgersen Hall mapped too, but Mason is where the work has
> gone.
>
> Link: [URL]
>
> Happy to answer anything about how the indoor routing works.

---

## For a professor to read out in class

Two sentences, no jargon, nothing for them to vouch for:

> One of your classmates has built a free 3D campus map called Akadian Vertex that gives walking
> directions to a specific room inside the Johnson Center and three other buildings, and it works
> offline on campus wi-fi.
>
> It is a web page rather than an app — there is a poster outside with a code on it, or you can add
> it to your home screen in a couple of taps.

**If you are the one asking:** email the professor the two sentences, say plainly that it is your own
project and not a university one, and offer to drop it if they would rather not. A professor who
reads this out is lending you their credibility; make it easy for them to say no.

---

## Words to avoid

- *Official*, *the campus app*, *partnered with*, *approved* — none of these are true.
- The university's logo, seal, wordmark, or colours used as if they were ours.
- *Trusted by students*, *everyone is using it*, star ratings, download counts — there is no usage
  data yet. Sell what it does, not an audience it does not have.
- *Never lose your way again*, *revolutionary*, *game-changing*. The product is specific; the copy
  should be too.

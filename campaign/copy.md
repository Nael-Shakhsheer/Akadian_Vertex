# Akadian Vertex — launch campaign copy

Everything the campaign says, in one place. The artwork pulls its strings from
`campaign/copytext.py`, and `make_campaign.py` fails the build if any of them stops appearing here
word for word — so edit both, or edit here and run the build to find out where it broke.

## What we are selling

**The first week of classes.** Nobody knows where anything is, everyone is a little late, and the
only tool anyone has is a maps app that drops them at the front of a building and says *you have
arrived*. Vertex is the thing that keeps going.

The line the whole campaign hangs on:

> GPS gets you to the building. Vertex gets you to the room.

## The three rules this copy is written under

**Only claim what the app does.** Vertex uses live GPS outdoors: you see yourself on a 3D map of
campus and it walks you to the best door for your room. Indoors, GPS does not work, so the app does
not pretend — it routes you from the door you walk in, up the stairs and down the hallway to the
room (`app/js/main.js` says so in its first two lines). So the copy says Vertex is *better than GPS
because it keeps going where GPS can't*, which is true and is the stronger line anyway. It never
says the phone knows where you are inside a building, and the build fails if any artwork does.

**Be honest about the edge.** Room-by-room directions exist inside four buildings. Every other
building on campus, Vertex gets you to the door. Wherever a piece promises "to the room", it either
names the four buildings or carries the scope line:

> Room by room inside Research Hall, Merten Hall, the Johnson Center and The HUB. Right to the door of every other building on campus.

**No university marks, no invented numbers.** The app ships campus initials as a monogram because
George Mason's logos and wordmarks are not ours to use. The university's name appears only
descriptively, and every printed piece carries, at the foot:

> An independent student project. Not affiliated with, endorsed or sponsored by George Mason
> University.

There are no users yet, so there are no download counts, ratings, quotes or awards anywhere. Every
figure that does appear is read out of the app's own data at build time:

| Claim | Where it comes from |
| --- | --- |
| 4 buildings mapped inside, 633 rooms | every `docs/data/buildings/gmu-*.json` the app ships |
| Research Hall, Merten Hall, the Johnson Center, The HUB | `docs/data/campuses.json` |
| Research Hall 423, on the fourth floor | `docs/data/buildings/gmu-research.json` |
| 163 buildings, 25 places to eat, 7 CUE routes, 26 stops | `docs/data/campus/gmu.json` |
| the 2.5-second network deadline | `NET_TIMEOUT` in `app/sw.js` |
| the distances and floor counts in the route captions | measured from the route the artwork draws, at build time |

The orange routes on the posters are not illustrations. They are what the app's own search returns —
a port of `app/js/router.js` over the same walk grids, costs and stair links — from Research Hall's
west door to room 423, and from the Johnson Center's west door to the computer lab in 342.

---

## Headlines

**A · Better than GPS** — the lead. Dark. Both posters, the feed post and the wide banner.

> GPS stops at the door. Vertex doesn't.

Deck: *Vertex uses live GPS to walk you across campus and pick the best door. Then it keeps going
where GPS can't: up the right stairs, down the right hallway, to the room on your schedule.*

Kicker: *Live GPS · 3D campus · turn-by-turn inside*
Tagline: *GPS gets you to the building. Vertex gets you to the room.*

**B · Find your class** — the first-week hook. Light. Both posters, the feed post and the story.

> Research Hall 423? Found it.

Deck: *Type the building and room number off your schedule. Vertex finds it, picks the best door,
and walks you there, floor by floor. Your first week, minus the wandering.*

Kicker: *First week of classes*
Pull line, and the story's headline: *Walk in like you've been here for years.*

The search in the artwork is the real one. The app matches every word you type against a room's
number and its building's name, so *research hall 423* — the way it reads on a schedule — finds it.
The result shows *Room 423*, *Research Hall · Floor 4* and *Best entrance:* with the door's name,
exactly as the app does.

**B, on the handout** — the half-page flyer.

> Don't be the one walking in at 9:07.

Deck: *Type the room off your schedule. Vertex walks you there on live GPS, picks the best door, and
takes you inside, floor by floor, to the room.*

**C · Offline** — dark. A story and a banner.

> No bars. Still works.

Deck: *Campus wi-fi doesn't fail, it hangs, usually in a stairwell four minutes before class. Vertex
gives the network 2.5 seconds, then uses the map already on your phone.*

Kicker: *Built for bad campus wi-fi*
Pull line: *The map is already on your phone.*

**D · No install** — dark. The quarter-page flyer, a feed post and a story.

> No app store. Just add it.

Deck: *Vertex is a website that works like an app. Add it to your home screen before your first
class: no download, no account, and it opens full-screen.*

Kicker: *No install · no account · no download*
Pull line: *No app store. No account. No download.*

### What it does, everywhere

- **Live GPS outside** — Watch yourself move on a 3D map of campus, and get walked to the best door for your room.
- **Turn-by-turn inside** — Research Hall, Merten Hall, the Johnson Center and The HUB, mapped room by room: 633 rooms.
- **Works on bad wi-fi** — A map you have opened stays on your phone, so a dead stairwell can't strand you.
- **All of campus** — 163 buildings, 25 places to eat, and 7 CUE routes across 26 stops.

Cut to one line each, for posters and anywhere else read at a glance:

- **Live GPS outside** — Walks you to the best door for your room.
- **Turn-by-turn inside** — Research Hall, Merten, the JC and The HUB.
- **Nothing to install** — No app store, no account. Add it to your home screen.

Sign-off line: *Akadian Vertex · a 3D campus map for George Mason students*

---

## Social captions

Five variants, one per angle, so a week of posts never reads like the same sentence twice. Each
stands on its own if the image never loads. Written to sound like a student, because one wrote it.

### 1 — GPS stops at the door (pairs with `a-gps-feed-1080` or `a-gps-banner-1600x900`)

> Your maps app: "You have arrived."
> You: outside Research Hall, class in four minutes, no idea where 423 is.
>
> Vertex picks up where GPS gives out. Live GPS across campus, the best door for your room, then
> turn-by-turn inside — up the stairs, down the hall, to the actual room.
>
> Free. No app store. Link in bio.
>
> #GMU #GeorgeMason #MasonNation #FirstWeek #SpringSemester #CollegeLife #CampusMap

### 2 — Found it (pairs with `b-findclass-feed-1080`)

> Syllabus week checklist:
> ☐ buy the textbook you'll never open
> ☐ find Research Hall 423
>
> We can help with one of those. Type the room off your schedule and Vertex walks you there, floor
> by floor.
>
> #GMU #GeorgeMason #SyllabusWeek #FirstDayOfClasses #Freshman #TransferStudent #CollegeLife

### 3 — Walk in like you've been here for years (pairs with `b-findclass-story-1080x1920`)

> 9:00 class. 9:07 and you're on the wrong floor of the right building.
>
> Not this semester. GPS to the door, turn-by-turn to the room. Never get lost finding a class
> again.
>
> #GMU #GeorgeMason #SpringSemester #FirstWeek #MasonNation

### 4 — No bars (pairs with `c-offline-story-1080x1920` or `c-offline-banner-1600x900`)

> One bar. Nothing loading. Stairwell. Class in four minutes.
>
> Vertex gives campus wi-fi two and a half seconds, then just uses the map already on your phone.
> Built for the wi-fi we actually have.
>
> #GMU #GeorgeMason #CampusWifi #CollegeLife #StudentBuilt

### 5 — Just add it (pairs with `d-install-feed-1080` or `d-install-story-1080x1920`)

> No app store. No account. No download.
>
> Open the link, hit Add to Home Screen, and Vertex sits on your phone like any other app. Do it
> before your first class and thank yourself at 8:58.
>
> #GMU #GeorgeMason #FirstWeek #AddToHomeScreen #CollegeHacks

**On hashtags.** Keep the first three or four — they are the ones GMU students actually browse. The
rest are padding. Never use a tag that reads as an official university account or programme.

---

## Reddit — r/gmu

Post as yourself, not as a brand. Flair it as a project or a resource if the subreddit has one, and
read the self-promotion rules first. Post it the weekend before classes start, and answer every
comment that day.

**Title:** I made a campus map that gets you to the actual room, not just the building — might help
the first week

**Body:**

> Every semester I watch people (me included) stand outside Research Hall at 8:58 with a maps app
> that says "you have arrived" and no idea where their room is. GPS gets you to the building and
> then gives up.
>
> So I built Akadian Vertex. You type the room off your schedule — "research hall 423" works — and it
> walks you there on live GPS, picks the best door for that room, and then gives you turn-by-turn
> directions inside: which stairs, which floor, which hallway, which door.
>
> To be straight about what it does and does not do:
>
> - Room-by-room directions work inside Research Hall, Merten Hall, the Johnson Center and The HUB
>   (633 rooms). Every other building on campus, it gets you to the door. More buildings as I map
>   them.
> - It does not pretend to track you indoors — GPS does not work in there. Outside it uses your
>   location; inside it routes from the door you came in by, floor by floor.
> - It works on bad wi-fi. It is a progressive web app: it gives the network 2.5 seconds, then uses
>   the copy of the map already on your phone.
> - There is nothing to install. It is a website. Open it, Add to Home Screen, and it opens
>   full-screen like an app. No account, no app store.
>
> Also on there: 163 buildings, 25 places to eat, and the CUE routes and stops.
>
> It is not official and not affiliated with the university — it is mine and it is free. The floor
> plans came from public sources, so if a room is wrong or missing, tell me and I will fix it.
>
> Link: [URL]

---

## For a professor to read out in class

Two sentences, no jargon, nothing for them to vouch for:

> One of your classmates has built a free campus map called Akadian Vertex that takes you to a
> specific room, not just the building — handy this week if you are still finding your classes.
>
> It is a website rather than an app; there is a code on the posters around campus, or you can add
> it to your home screen in a couple of taps.

**If you are the one asking:** email the professor the two sentences, say plainly that it is your own
project and not a university one, and offer to drop it if they would rather not.

---

## Words to avoid

- **Indoor GPS**, *knows where you are inside*, *tracks you through the building* — the app does
  not do indoor positioning, and the build rejects artwork that says so. Say *turn-by-turn inside*
  or *floor by floor from the door*.
- **Any room on campus** — rooms are mapped in four buildings. Say *every building, and every room
  in four of them*, or name the four.
- *Official*, *the campus app*, *partnered with*, *approved* — none of these are true.
- The university's logo, seal, wordmark, or colours used as if they were ours.
- *Trusted by students*, *everyone is using it*, ratings, download counts — there is no usage data
  yet. Sell what it does, not an audience it does not have.

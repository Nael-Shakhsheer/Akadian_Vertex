"""Fenwick Library's indoor map, from GMU Libraries' published floor maps (floors 1-5).

    python tools/fetch_gmu_sources.py        # downloads the five maps (they belong to GMU; not stored here)
    python tools/gmu_fenwick.py prepare      # redraw them in the engine's convention + read room numbers
    python tools/gmu_fenwick.py check        # build and print a report, without publishing

These are wayfinding maps, not architectural plans: flat colour per kind of space, white for the way around,
slate for staff and service areas, black text. That makes them easy to read by colour. Each map is redrawn in
the engine's convention -- walls dark, corridors gray, rooms white -- and built by the same pipeline as every
other building, so routing, search and the 3D view need nothing special.

What the maps don't show is doors. Every coloured space is a closed block, so a route to a study room ends in
the corridor beside it, which for a library is the useful answer. Stairs, lifts and restrooms are found with the
pictograms from each sheet's own key and opened onto the corridor they face; the service lift (staff only) is
left out. Room numbers are read with OCR and corrected by hand in FIX, the same way as every other GMU building,
and the lettered zones take their names from each floor's own directory. Nothing is placed that the maps don't
show.
"""
import json, re, sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.pipeline import ingest, build as builder  # noqa: E402

FEN = ROOT / "data/gmu/fenwick-library"
CROP = (180, 40, 840, 775)    # the building's part of every sheet (x0, y0, x1, y1); the key and directory are left out
K = 3                         # upscale: the sheets are 840 px wide, the engine's constants assume ~250 dpi renders
CORRIDOR, SERVICE, WALL, ROOM, OUTSIDE = 215, 175, 0, 255, 255

FLOORS = [  # id, name, level, sheet
    ("first", "Floor 1", 1, 1), ("second", "Floor 2", 2, 2), ("third", "Floor 3", 3, 3),
    ("fourth", "Floor 4", 4, 4), ("fifth", "Floor 5", 5, 5),
]
# Each floor's own directory: zone letter -> (name, room number when it has one). "Study Room" is the blue.
ZONES = {
    1: {"A": ("Tower Book Stacks", None), "B": ("Compact Shelving", None), "C": ("Instruction Room", "1014A"),
        "D": ("Access Services", "1300"), "E": ("Fenwick Gallery", None)},
    2: {"A": ("Special Collections Research Center", "2400"), "B": ("University Dissertation and Thesis Services", "2005"),
        "C": ("Writing Center Tutoring", "2303"), "D": ("Main Reading Room", "2001"), "E": ("Data Services", "2608"),
        "F": ("Subject Librarians", None), "G": ("Special Collections and Archives", "2500"),
        "H": ("Special Collections and Archives Exhibition", None)},
    3: {"A": ("Tower Book Stacks AC–GR", None), "B": ("Compact Shelving GT–JZ", None), "C": ("Preservation Lab", "3009"),
        "D": ("Technical Services", "3300"), "E": ("Seminar Room", "3001"), "F": ("Reading Room", "3403"),
        "G": ("Presentation Practice Room", "3102")},
    4: {"A": ("Tower Book Stacks K–PN", None), "B": ("Compact Shelving PQ–Q", None), "C": ("Administration", "4300"),
        "D": ("Mason Publishing Group", "4315"), "E": ("Instruction Room", "4010"), "F": ("Seminar Room", "4008")},
    5: {"A": ("Tower Book Stacks QA–ZA & Thesis/Dissertations", None), "B": ("Systems Group", "5300"),
        "C": ("Digital Lab", "5001"), "D": ("Faculty Collaborative Research Center", "5003"),
        "E": ("Virtual Library of Virginia (VIVA) at George Mason", "5100")},
}
STUDY = {1: "Study Room", 2: "Study Room", 3: "Study Room", 4: "Study Room", 5: "Graduate Study Room"}
# Numbers in a zone's own directory line that name individual rooms inside it.
NUMBERED = {1: {"1014A": "Instruction Room", "1014B": "Instruction Room"},
            2: {"2303": "Writing Center Tutoring", "2304": "Writing Center Tutoring",
                **{f"22{i:02d}": "Subject Librarians" for i in range(1, 13)}},  # "Subject Librarians 2201-2212"
            3: {"3102": "Presentation Practice Room", "3111": "Presentation Practice Room"},
            5: {"5001": "Digital Lab"}}  # its zone letter didn't read; the number did once added in FIX
# OCR corrections, checked against the sheets: misread -> right id; "+id": (x, y) in sheet pixels for a number
# OCR missed; "-id" drops a reading that isn't a room number on the map.
FIX = {
    1: {"1301": "1701", "1209": "1204", "1310": "1300", "+1707": (336, 175), "+1706": (356, 175), "+1014A": (601, 184)},
    # renames first, then additions: an added number must not be renamed by a later entry
    2: {"2302": "2303", "2307": "2304", "2230": "2210", "2206": "2205", "-2026": None,
        "+2206": (379, 687), "+2207": (359, 687), "+2209": (324, 654)},
    3: {"3105": "3106", "3100": "3104", "+3105": (474, 669), "+3706": (411, 181), "+3705": (433, 181),
        "+3607": (389, 618), "+3608": (411, 618)},
    4: {"4039": "4009", "4814": "4614", "4109": "4104", "+4708": (326, 181), "+4707": (346, 181),
        "+4706": (411, 181), "+4705": (434, 181), "+4701": (470, 358), "+4003": (599, 623)},
    5: {"5680": "5609", "+5607": (381, 623), "+5608": (402, 623), "+5001": (520, 475)},
}
# What the pictograms and letters missed, read off the sheets: a restroom the matcher passed over, and a zone drawn
# as two blocks with its letter in only one. Sheet pixels.
EXTRA = {
    1: {"restroom": [(458, 658)], "zone": [("B", 374, 96)]},
    2: {"restroom": [(505, 272), (505, 299), (265, 507)], "zone": [("H", 620, 361)]},
    3: {"restroom": [(265, 294)]},
    4: {"restroom": [(264, 259), (505, 297)]},
    5: {"restroom": [(251, 506)]},
}
# Where the map marks the way in, sheet pixels on Floor 1.
ENTRANCES = [("first", "North entrance", (196, 689)), ("first", "South entrance", (627, 740))]

# ---------------------------------------------------------------------------------------------------------------
C_WHITE, C_BLACK, C_SERVICE, C_GREY, C_COLOUR = 1, 2, 3, 4, 5


def sheet(n):
    p = FEN / f"source/floor-maps/fenwick-floor{n}.jpg"
    im = cv2.imread(str(p))
    if im is None:
        raise SystemExit("Fenwick's floor maps aren't downloaded yet. Run:  python tools/fetch_gmu_sources.py")
    return im


def classify(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s, v = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    cls = np.full(v.shape, C_COLOUR, np.uint8)
    cls[(s < 45) & (v >= 228)] = C_WHITE
    cls[(s < 45) & (v >= 150) & (v < 228)] = C_GREY        # restrooms, the gray blocks
    cls[(v < 150) & (s < 110)] = C_SERVICE                 # slate: staff and service
    cls[v < 60] = C_BLACK                                  # text, outlines, pictograms
    return cls, hsv


def redraw(n):
    """One sheet -> (plan at sheet resolution in the engine's values, room-id map, classes)."""
    x0, y0, x1, y1 = CROP
    crop = cv2.medianBlur(sheet(n)[y0:y1, x0:x1], 3)
    cls, hsv = classify(crop)
    h, w = cls.shape
    # The maps have no continuous outer wall -- just blocks with door gaps -- so the envelope comes from closing
    # everything drawn hard enough to bridge a corridor's mouth, then filling it in.
    drawn = (cls != C_WHITE).astype(np.uint8)
    sealed = cv2.morphologyEx(drawn, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35)))
    ff = sealed * 255
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (1, 1), 128)
    inside = cv2.morphologyEx((ff != 128).astype(np.uint8), cv2.MORPH_OPEN, np.ones((15, 15), np.uint8)) > 0
    # rooms: coloured and gray blocks, split by colour, with their numbers and pictograms filled in
    hue = (hsv[..., 0].astype(int) // 12) * 4 + np.minimum(hsv[..., 1].astype(int) // 64, 3)
    key = np.where(cls == C_COLOUR, hue + 10, np.where(cls == C_GREY, 1, 0)).astype(np.int32)
    room_id = np.zeros((h, w), np.int32)
    nid = 0
    for k in np.unique(key):
        if k == 0:
            continue
        m = cv2.morphologyEx((key == k).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # JPEG fringes
        cnt, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
        for i in range(1, cnt):
            if st[i, cv2.CC_STAT_AREA] < 40:
                continue
            cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            filled = np.zeros((h, w), np.uint8)
            cv2.drawContours(filled, cs, -1, 1, -1)
            nid += 1
            room_id[(filled > 0) & (room_id == 0) & inside] = nid
    rooms = room_id > 0
    plan = np.full((h, w), CORRIDOR, np.uint8)
    plan[cls == C_SERVICE] = SERVICE
    black = (cls == C_BLACK) & ~rooms
    cnt, lab, st, _ = cv2.connectedComponentsWithStats(black.astype(np.uint8), connectivity=8)
    for i in range(1, cnt):  # words and pictograms lying in the open stay walkable
        if max(st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]) <= 45 and st[i, cv2.CC_STAT_AREA] <= 900:
            black[lab == i] = False
    plan[black] = WALL
    plan[rooms] = ROOM
    edge = cv2.morphologyEx(room_id.astype(np.float32), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    plan[edge & (rooms | (plan == CORRIDOR))] = WALL
    plan[~inside] = OUTSIDE
    return plan, room_id, cls


# ---- pictograms, matched against each sheet's own key ----------------------------------------------------------
KEY_ROWS = {"elevator": 260, "service": 283, "stair": 306, "women": 329, "men": 352}


def pictograms(n, cls=None):
    """Stairs, lifts (as pairs: a lift lobby) and restrooms, in sheet pixels. Matched on the glyph alone, since
    the building draws them on green and slate where the key draws them on white, and at several sizes."""
    key = cv2.cvtColor(sheet(1), cv2.COLOR_BGR2GRAY)
    dark = lambda g: (g < 100).astype(np.float32)
    tpl = {k: key[y + 2:y + 13, 42:53] for k, y in KEY_ROWS.items()}
    x0, y0, x1, y1 = CROP
    g = dark(cv2.cvtColor(sheet(n), cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1])
    if cls is None:
        cls = redraw(n)[2]
    def grey_round(x, y, r=12):  # restrooms are drawn on gray blocks; other pictograms aren't
        sx, sy = int(x - x0), int(y - y0)
        return (cls[max(0, sy - r):sy + r, max(0, sx - r):sx + r] == C_GREY).mean()
    found = {"stair": [], "lift": [], "restroom": []}
    for s in (1.0, 1.15, 1.3, 1.45):
        r = {k: cv2.matchTemplate(g, dark(cv2.resize(t, None, fx=s, fy=s)), cv2.TM_CCOEFF_NORMED) for k, t in tpl.items()}
        half = int(11 * s) // 2
        lift = np.maximum(r["elevator"], r["service"]); loo = np.maximum(r["women"], r["men"])
        for kind, score, rivals, th in (("stair", r["stair"], (lift, loo), 0.62),
                                        ("lift", lift, (r["stair"],), 0.60),   # lifts are judged against stairs only
                                        ("restroom", loo, (r["stair"], lift), 0.62)):
            ys, xs = np.nonzero((score >= th) & (score >= np.maximum.reduce(rivals)))
            found[kind] += [(float(score[y, x]), int(x + half + x0), int(y + half + y0)) for x, y in zip(xs, ys)]
    def one_each(hits, gap=9):
        kept = []
        for h in sorted(hits, reverse=True):
            if all(abs(h[1] - a) > gap or abs(h[2] - b) > gap for _, a, b in kept):
                kept.append(h)
        return [(x, y) for _, x, y in kept]
    stairs = one_each(found["stair"])
    restrooms = [(x, y) for x, y in one_each(found["restroom"]) if grey_round(x, y) >= 0.25]
    # a lift lobby draws its lifts side by side; a lone match is the staff service lift or a false hit on an edge
    lifts = one_each(found["lift"])
    lobbies, used = [], set()
    for i, (xa, ya) in enumerate(lifts):
        for j, (xb, yb) in enumerate(lifts):
            if j > i and i not in used and j not in used and 14 <= abs(xa - xb) <= 28 and abs(ya - yb) <= 5:
                lobbies.append(((xa + xb) / 2, (ya + yb) / 2)); used |= {i, j}
    return stairs, lobbies, restrooms


# ---- reading the numbers -----------------------------------------------------------------------------------------
def read_text(n):
    x0, y0, x1, y1 = CROP
    big = cv2.resize(sheet(n)[y0:y1, x0:x1], None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    res, _ = ingest._ocr_engine()(big, box_thresh=0.3, text_score=0.3)
    out = []
    for box, txt, score in res or []:
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        out.append({"text": txt.strip(), "x": round(sum(xs) / 4, 1), "y": round(sum(ys) / 4, 1),
                    "w": round(max(xs) - min(xs), 1), "h": round(max(ys) - min(ys), 1), "score": round(float(score), 2)})
    return out  # plan pixels (crop x K)


def to_plan(x, y):
    return round((x - CROP[0]) * K), round((y - CROP[1]) * K)


def floor_labels(n, plan, room_id, ocr, stairs, lobbies, restrooms):
    """Labels in plan pixels, before the floor's offset."""
    zones, study, numbered, fix = ZONES.get(n, {}), STUDY[n], NUMBERED.get(n, {}), FIX.get(n, {})
    at = lambda x, y: region_at(room_id, x, y)
    def mostly_service(x, y, r=9):  # the number's own glyphs are white: judge it by what surrounds it
        sx, sy = int(x / K), int(y / K)
        return (plan[max(0, sy - r):sy + r, max(0, sx - r):sx + r] == SERVICE).mean() > 0.5
    labels, by_region = {}, {}
    nums = {}
    for it in ocr:
        t = it["text"].upper().replace("O", "0")
        if re.fullmatch(r"\d{4}[A-Z]?", t) and int(t[0]) == n:
            nums[t] = (it["x"], it["y"])
    for k, v in fix.items():
        if k.startswith("+"):
            nums[k[1:]] = to_plan(*v)
        elif k.startswith("-"):
            nums.pop(k[1:], None)
        elif k in nums:
            nums[v] = nums.pop(k)
    for rid, (x, y) in nums.items():
        if mostly_service(x, y):
            continue  # "Building Service and Support": not a place to send anyone
        name = numbered.get(rid)
        labels[rid] = {"id": rid, "kind": "room", "x": round(x), "y": round(y)}
        reg = at(x, y)
        if reg:
            by_region.setdefault(reg, []).append(rid)
        if name:
            labels[rid]["name"] = name
    # lettered zones: big single letters, named from this floor's directory
    seen = {}
    for it in ocr:
        t = it["text"].strip()
        if not (re.fullmatch(r"[A-H]", t) and it["h"] >= 18 * K * 0.8 and t in zones):
            continue
        name, number = zones[t]
        x, y, reg = it["x"], it["y"], at(it["x"], it["y"])
        if number and number in labels:  # the zone's own number is printed in it: name that label
            labels[number]["name"] = name
            continue
        seen[t] = seen.get(t, 0) + 1
        zid = number or (f"{n}{t}" if seen[t] == 1 else f"{n}{t}-{seen[t]}")
        labels[zid] = {"id": zid, "kind": "room", "x": round(x), "y": round(y), "name": name, "area": number is None}
        for other in by_region.get(reg, []):  # a number inside a lettered zone belongs to that zone's name
            labels[other].setdefault("name", name)
    for rid, l in labels.items():  # the blue is study rooms
        l.setdefault("name", study if _is_blue(n, room_id, l["x"], l["y"]) else None)
        if l["name"] is None:
            l.pop("name")
    for i, (x, y) in enumerate(sorted(stairs), 1):
        labels[f"STAIR{i}"] = dict(zip(("x", "y"), _box_centre(room_id, *to_plan(x, y))), id=f"STAIR{i}", kind="stair")
    for i, (x, y) in enumerate(sorted(lobbies), 1):
        labels[f"ELEV{i}"] = dict(zip(("x", "y"), _box_centre(room_id, *to_plan(x, y))), id=f"ELEV{i}", kind="elevator")
    restrooms = list(restrooms) + list(EXTRA.get(n, {}).get("restroom", []))
    for letter, x, y in EXTRA.get(n, {}).get("zone", []):
        name, number = zones[letter]
        seen[letter] = seen.get(letter, 0) + 1
        zid = f"{n}{letter}" if seen[letter] == 1 else f"{n}{letter}-{seen[letter]}"
        px, py = to_plan(x, y)
        labels[zid] = {"id": zid, "kind": "room", "x": px, "y": py, "name": name, "area": True}
    for i, (x, y) in enumerate(sorted(restrooms), 1):
        px, py = to_plan(x, y)
        labels[f"RESTROOM{i}"] = {"id": f"RESTROOM{i}", "kind": "restroom", "x": px, "y": py}
    return sorted(labels.values(), key=lambda l: (l["kind"], l["id"]))


def region_at(room_id, x, y, r=6):
    """The room a label belongs to: the most common one within a few pixels, since a number often sits on its
    box's edge, right on the outline."""
    sx, sy = int(x / K), int(y / K)
    win = room_id[max(0, sy - r):sy + r + 1, max(0, sx - r):sx + r + 1]
    ids, counts = np.unique(win[win > 0], return_counts=True)
    return int(ids[np.argmax(counts)]) if len(ids) else 0


def _is_blue(n, room_id, x, y):
    """Is the room this label sits in the study-room blue? Taken from the room's own colour, not the number's
    (white) glyphs."""
    rid = region_at(room_id, x, y)
    if not rid:
        return False
    x0, y0, x1, y1 = CROP
    hsv = cv2.cvtColor(sheet(n)[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)[room_id == rid]
    hsv = hsv[hsv[:, 1] > 120]  # drop the glyphs
    return len(hsv) > 10 and 95 <= np.median(hsv[:, 0]) <= 112


def _box_centre(room_id, px, py):
    """Stairs and lifts are labelled at the middle of the box they're drawn in -- the same place on every floor --
    rather than at the pictogram, which sits on either side of its box from sheet to sheet."""
    sx, sy = int(px / K), int(py / K)
    rid = room_id[min(room_id.shape[0] - 1, sy), min(room_id.shape[1] - 1, sx)]
    if not rid:
        return px, py
    ys, xs = np.nonzero(room_id == rid)
    if len(xs) > 4000:  # not a stair box but a whole zone: keep the pictogram's place
        return px, py
    return round(xs.mean() * K), round(ys.mean() * K)


def open_connectors(plan_big, room_id, labels):
    """Stairs and lifts are drawn as closed boxes; open each onto the corridor it faces so routes can use it."""
    for l in labels:
        if l["kind"] not in ("stair", "elevator"):
            continue
        rid = room_id[min(room_id.shape[0] - 1, int(l["y"] / K)), min(room_id.shape[1] - 1, int(l["x"] / K))]
        if not rid:
            continue
        box = cv2.resize((room_id == rid).astype(np.uint8), (plan_big.shape[1], plan_big.shape[0]), interpolation=cv2.INTER_NEAREST)
        if box.sum() > 4000 * K * K:
            continue
        ring = cv2.dilate(box, np.ones((3 * K + 1, 3 * K + 1), np.uint8)) > 0
        plan_big[(box > 0)] = CORRIDOR
        plan_big[ring & (plan_big == WALL)] = CORRIDOR
    return plan_big


def align(ref, im):
    """Offset of a floor against Floor 1: the sheets are drawn in nearly the same frame, but not quite."""
    a = cv2.GaussianBlur((ref < 200).astype(np.float32), (0, 0), 4)
    b = cv2.GaussianBlur((im < 200).astype(np.float32), (0, 0), 4)
    warp = np.eye(2, 3, dtype=np.float32)
    cc, warp = cv2.findTransformECC(a, b, warp, cv2.MOTION_TRANSLATION,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), None, 5)
    return [round(float(warp[0, 2]), 1), round(float(warp[1, 2]), 1)], round(float(cc), 3)


def prepare(verbose=True):
    (FEN / "plans").mkdir(parents=True, exist_ok=True)
    (FEN / "ocr").mkdir(parents=True, exist_ok=True)
    plans, report = {}, {}
    for fid, name, lv, n in FLOORS:
        plan, room_id, _cls = redraw(n)
        ocr = read_text(n)
        stairs, lobbies, restrooms = pictograms(n, _cls)
        labels = floor_labels(n, plan, room_id, ocr, stairs, lobbies, restrooms)
        big = cv2.resize(plan, None, fx=K, fy=K, interpolation=cv2.INTER_NEAREST)
        big = open_connectors(big, room_id, labels)
        plans[fid] = big
        cv2.imwrite(str(FEN / f"plans/fenwick-floor{n}.png"), big)
        (FEN / f"ocr/fenwick-floor{n}.ocr.json").write_text(json.dumps(ocr, indent=1, ensure_ascii=False), encoding="utf-8")
        (FEN / f"ocr/fenwick-floor{n}.labels.json").write_text(json.dumps(labels, indent=1, ensure_ascii=False), encoding="utf-8")
        kinds = {}
        for l in labels:
            kinds[l["kind"]] = kinds.get(l["kind"], 0) + 1
        report[fid] = kinds
        if verbose:
            print(f"{name}: {big.shape[1]}x{big.shape[0]} px, {kinds}")
    offsets = {"first": [0.0, 0.0]}
    for fid, *_ in FLOORS[1:]:
        offsets[fid], cc = align(plans["first"], plans[fid])
        if verbose:
            print(f"  {fid} offset {offsets[fid]} (correlation {cc})")
    (FEN / "ocr/offsets.json").write_text(json.dumps(offsets, indent=1), encoding="utf-8")
    return report


# ---- the project and the build -----------------------------------------------------------------------------------
def project():
    way = json.loads((FEN / "osm/building.json").read_text())["elements"][0]
    offsets = json.loads((FEN / "ocr/offsets.json").read_text())
    floors = [{"id": fid, "name": name, "level": lv, "prefix": "", "offset": offsets[fid], "reference": fid == "first",
               "exclude": [], "processed": True} for fid, name, lv, _ in FLOORS]
    labels = {fid: [{k: v for k, v in l.items() if k != "area"}
                    for l in json.loads((FEN / f"ocr/fenwick-floor{n}.labels.json").read_text(encoding="utf-8"))]
              for fid, _, _, n in FLOORS}
    entrances = [{"name": nm, "floor": f, "x": to_plan(x, y)[0], "y": to_plan(x, y)[1]} for f, nm, (x, y) in ENTRANCES]
    return {"id": "gmu-fenwick", "name": "Fenwick Library", "campus": "gmu", "osm_way": way["id"],
            "floors": floors, "labels": labels, "voids": {}, "entrances": entrances, "extra_links": [],
            "footprint": [[p["lat"], p["lon"]] for p in way["geometry"]]}


def build(log=lambda m: None):
    images = {fid: cv2.imread(str(FEN / f"plans/fenwick-floor{n}.png"), cv2.IMREAD_GRAYSCALE) for fid, _, _, n in FLOORS}
    if any(v is None for v in images.values()):
        raise SystemExit("Fenwick's plans aren't prepared yet. Run:  python tools/gmu_fenwick.py prepare")
    p = project()
    ocr = {fid: json.loads((FEN / f"ocr/fenwick-floor{n}.ocr.json").read_text(encoding="utf-8")) for fid, _, _, n in FLOORS}
    out, debug, report = builder.build(p, images, ocr, log=log)
    report["blocked"] = keep_main_network(out)
    areas = {(fid, l["id"]) for fid, _, _, n in FLOORS
             for l in json.loads((FEN / f"ocr/fenwick-floor{n}.labels.json").read_text(encoding="utf-8")) if l.get("area")}
    for r in out["rooms"]:  # a lettered zone is an area of the library, not a numbered room
        if (r["floor"], r["id"]) in areas:
            r["area"] = True
    return p, images, out, debug, report


def keep_main_network(out):
    """Keep only each floor's main walkable network on the routing grid.

    With no doors on the maps, every room is a closed box. The engine counts a room's inside as walkable but
    discouraged, so a destination would snap to a cell inside the box -- which nothing can reach -- and the route
    would fail. Blocking every cell off the main network (sealed room interiors, and stray islands like the
    roof areas drawn in white) makes a room's nearest reachable cell the corridor beside it, which is where a
    route to a room on these maps should end. No door is invented; the rooms keep their outlines for display.
    Returns how many cells were blocked per floor."""
    g = out["grid"]
    starts = {(e["floor"], tuple(e["start"])) for e in out["entrances"]}
    lifts = [(r["floor"], r["label"]) for r in out["rooms"] if r["kind"] == "elevator"]
    blocked = {}
    for fl in out["floors"]:
        cells = np.zeros(g["w"] * g["h"], np.uint8)
        pos = 0
        for i in range(0, len(fl["grid"]), 2):
            cells[pos:pos + fl["grid"][i + 1]] = fl["grid"][i]
            pos += fl["grid"][i + 1]
        cells = cells.reshape(g["h"], g["w"])
        # 4-way, on purpose: the router never cuts a corner between two walls, so a pocket that touches the
        # network only diagonally can't be walked into, even though an 8-way test would call it connected
        n, lab = cv2.connectedComponents((cells > 0).astype(np.uint8), connectivity=4)
        at = lambda x, y: lab[min(g["h"] - 1, int((y - g["y0"]) / g["cell"])), min(g["w"] - 1, int((x - g["x0"]) / g["cell"]))]
        # the network the lifts (and, on the ground floor, the entrances) stand on; failing that, the largest
        anchors = [at(*pt) for f, pt in lifts if f == fl["id"]] + [at(*pt) for f, pt in starts if f == fl["id"]]
        anchors = [a for a in anchors if a]
        main = np.bincount(anchors).argmax() if anchors else 1 + int(np.argmax(np.bincount(lab.ravel())[1:]))
        off = (cells > 0) & (lab != main)
        blocked[fl["id"]] = int(off.sum())
        cells[off] = 0
        fl["grid"] = builder.rle([int(v) for v in cells.ravel()])
    return blocked


def publish(store):
    p, images, out, debug, report = build()
    store.publish("buildings", p["id"], out)
    print(f"{p['name']}: {report['rooms']} rooms, {report['links']} links, georef {report['georef']}")
    return p


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["check"]:
        p, images, out, debug, report = build(log=print)
        print(json.dumps({k: v for k, v in report.items() if k != "floors"}, indent=1))
        for fid, d in debug.items():
            (FEN / f"plans/debug-{fid}.png").write_bytes(d)
    else:
        print(__doc__)

"""The route the app would actually walk, computed from the app's own data.

A poster that shows a route ought to show a real one. This is a small Python port of the search in
app/js/router.js -- the same run-length-encoded walk grids (0 blocked, 1 corridor, 2 inside a room),
the same costs, the same stair and lift links between floors -- run over
docs/data/buildings/gmu-jc.json. What the artwork draws is what Vertex would tell you to walk.

Kept deliberately simple next to the app: plain Dijkstra rather than the app's bidirectional A*, and
no step-free option, because this runs once at build time over one building.
"""
import heapq
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brand

ROOM_COST = 4          # walking through rooms instead of corridors is discouraged
STAIR_COST = 45        # per floor, in cell units
ELEVATOR_COST = 70     # waiting + riding
DX = (1, -1, 0, 0, 1, 1, -1, -1)
DY = (0, 0, 1, -1, 1, -1, 1, -1)
DL = (1, 1, 1, 1, math.sqrt(2), math.sqrt(2), math.sqrt(2), math.sqrt(2))


def decode_rle(runs, n):
    out = bytearray(n)
    p = 0
    for i in range(0, len(runs), 2):
        v, c = runs[i], runs[i + 1]
        if v:
            out[p:p + c] = bytes([v]) * c
        p += c
    return out


class Plan:
    """The building's stacked walk grids, ready to search."""

    def __init__(self, data):
        self.d = data
        g = data["grid"]
        self.w, self.h, self.cell, self.x0, self.y0 = g["w"], g["h"], g["cell"], g["x0"], g["y0"]
        self.per = self.w * self.h
        self.order = [f["id"] for f in data["floors"]]
        self.cells = b"".join(bytes(decode_rle(f["grid"], self.per)) for f in data["floors"])
        # stairs and lifts: the id of a vertical core -> the cell it sits in, per floor
        self.node_cell = {}
        for r in data["rooms"]:
            if r["kind"] in ("stair", "elevator"):
                self.node_cell[(r["floor"], r["id"])] = self.to_cell(r["floor"], *brand.centroid(r["poly"]))
        self.links = {}
        for l in data["links"]:
            a, b = self.node_cell.get(tuple(l["a"])), self.node_cell.get(tuple(l["b"]))
            if a is None or b is None:
                continue
            cost = STAIR_COST if l["kind"] == "stair" else ELEVATOR_COST
            self.links.setdefault(a, []).append((b, cost))
            self.links.setdefault(b, []).append((a, cost))

    # ---------------- coordinates
    def to_cell(self, floor, x, y):
        cx = round((x - self.x0) / self.cell - 0.5)
        cy = round((y - self.y0) / self.cell - 0.5)
        cx, cy = max(0, min(self.w - 1, cx)), max(0, min(self.h - 1, cy))
        return self.order.index(floor) * self.per + cy * self.w + cx

    def to_plan(self, idx):
        f, r = divmod(idx, self.per)
        cy, cx = divmod(r, self.w)
        return self.order[f], self.x0 + (cx + 0.5) * self.cell, self.y0 + (cy + 0.5) * self.cell

    def nearest_open(self, idx, radius=40):
        """The closest cell that is not blocked -- an entrance mat or a room centroid can land on a wall."""
        if self.cells[idx]:
            return idx
        f, r = divmod(idx, self.per)
        cy, cx = divmod(r, self.w)
        for d in range(1, radius):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.w and 0 <= y < self.h:
                        j = f * self.per + y * self.w + x
                        if self.cells[j]:
                            return j
        return idx

    # ---------------- search
    def walk(self, start, goal):
        """Cell indices from start to goal, or None. Dijkstra; a move is priced by the cell it enters."""
        start, goal = self.nearest_open(start), self.nearest_open(goal)
        dist = {start: 0.0}
        prev = {}
        q = [(0.0, start)]
        cells, w, h, per = self.cells, self.w, self.h, self.per
        while q:
            dcur, cur = heapq.heappop(q)
            if cur == goal:
                break
            if dcur > dist.get(cur, 1e18):
                continue
            base = cur - cur % per
            r = cur % per
            x, y = r % w, (r - r % w) // w
            for k in range(8):
                X, Y = x + DX[k], y + DY[k]
                if X < 0 or Y < 0 or X >= w or Y >= h:
                    continue
                ni = base + Y * w + X
                c = cells[ni]
                if not c:
                    continue
                if k >= 4 and (not cells[base + y * w + X] or not cells[base + Y * w + x]):
                    continue    # no cutting a corner through a wall
                nd = dcur + DL[k] * (ROOM_COST if c == 2 else 1)
                if nd < dist.get(ni, 1e18):
                    dist[ni], prev[ni] = nd, cur
                    heapq.heappush(q, (nd, ni))
            for ni, cost in self.links.get(cur, ()):
                nd = dcur + cost
                if nd < dist.get(ni, 1e18):
                    dist[ni], prev[ni] = nd, cur
                    heapq.heappush(q, (nd, ni))
        if goal not in prev and goal != start:
            return None
        path, cur = [], goal
        while cur != start:
            path.append(cur)
            cur = prev[cur]
        path.append(start)
        path.reverse()
        return path

    def legs(self, path):
        """The cell path split into per-floor polylines in plan coordinates, each simplified."""
        out = []
        for idx in path:
            floor, x, y = self.to_plan(idx)
            if not out or out[-1]["floor"] != floor:
                out.append({"floor": floor, "pts": []})
            out[-1]["pts"].append((x, y))
        for leg in out:
            leg["pts"] = simplify(leg["pts"], 4.0)
        return out


def simplify(pts, eps):
    """Ramer-Douglas-Peucker, so a grid path draws as a few clean strides instead of a staircase."""
    if len(pts) < 3:
        return list(pts)
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy) or 1.0
    worst, at = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / n
        if d > worst:
            worst, at = d, i
    if worst <= eps:
        return [pts[0], pts[-1]]
    return simplify(pts[:at + 1], eps)[:-1] + simplify(pts[at:], eps)


def length_m(legs):
    """How far the walk actually is, on the flat, in metres -- so a caption can say so truthfully."""
    per_px = brand.jc_raw()["mPerPx"]
    total = 0.0
    for leg in legs:
        for a, b in zip(leg["pts"], leg["pts"][1:]):
            total += math.dist(a, b)
    return total * per_px


def jc_route(to_room="218", from_entrance=0):
    """Walk in the front door of the Johnson Center and up to a real group study room.

    Returns (legs, start_plan_point, goal_plan_point) in plan coordinates.
    """
    import json
    data = json.loads(brand.JC_DATA.read_text(encoding="utf-8"))
    p = Plan(data)
    ent = data["entrances"][from_entrance]
    room = next(r for r in data["rooms"] if r["id"] == to_room)
    start_xy = tuple(ent["start"])
    goal_xy = brand.centroid(room["poly"])
    path = p.walk(p.to_cell(ent["floor"], *start_xy), p.to_cell(room["floor"], *goal_xy))
    if not path:
        return None, start_xy, goal_xy
    return p.legs(path), start_xy, goal_xy

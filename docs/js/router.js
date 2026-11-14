// Best-first search (A*) over the stacked floor grids. Cells: 0 blocked, 1 corridor, 2 inside a room
// (allowed, but costs more). Floors are joined only at stairs and elevators (data.links).
//
// Settings, per call:
//   diagonal       8 neighbours (default) or 4. Diagonals never cut a blocked corner.
//   bidirectional  search out from the start and the goal at once and meet in the middle, instead of only from
//                  the start. Both return a shortest path (same cost to the cent, see tests/test_router.mjs):
//                  the heuristic below is consistent, so a frontier whose best f has reached the best meeting
//                  cost cannot improve on it. It is OFF by default because it loses here: measured over 385
//                  routes in the Johnson Center it expands ~31% MORE cells than the one-way search. The
//                  straight-line heuristic already aims one frontier almost at the goal, so a second frontier
//                  mostly duplicates it and overshoots before they meet. It is kept for buildings with weaker
//                  heuristics (long detours, many floors), where the balance can go the other way.
//
// The heuristic is straight-line (Euclidean) distance in cells, plus 0.9 x STAIR_COST per floor still to change.
// Every move of length L costs at least L and every floor change at least STAIR_COST, so it never overestimates
// and the path returned is a true shortest path.


const ROOM_COST = 4;          // walking through rooms instead of corridors is discouraged
const STAIR_COST = 45;        // per floor, in cell units (~10 m of walking)
const ELEVATOR_COST = 70;     // waiting + riding
const MIN_AREA = 300;         // cells (~12 m²): smaller sealed pockets (between stair treads, inside wall
                              // drawings) are never used as a start, goal or stair landing
const NEAR_M = 15;            // a room the plan seals off (no drawn door) is routed to its nearest reachable spot
// 8 neighbours: straight moves first (k < 4), then diagonals
const DX = [1, -1, 0, 0, 1, 1, -1, -1], DY = [0, 0, 1, -1, 1, -1, 1, -1];
const DL = [1, 1, 1, 1, Math.SQRT2, Math.SQRT2, Math.SQRT2, Math.SQRT2];

export class Router {
  constructor(b) {
    this.b = b;
    const { w, h } = b.grid;
    this.w = w; this.h = h; this.per = w * h;
    this.n = this.per * b.floors.length;
    this.cells = new Uint8Array(this.n);
    b.floors.forEach((f, i) => this.cells.set(f.cells, i * this.per));
    this.labelAreas();
    this.g = new Float64Array(this.n);
    this.from = new Int32Array(this.n);
    this.seen = new Uint32Array(this.n); // generation stamps so we don't clear arrays per search
    this.closed = new Uint32Array(this.n);
    this.gen = 0;
    this.links = [];
    for (const l of b.links) {
      const ra = b.roomByKey.get(`${l.a[0]}:${l.a[1]}`);
      const rb = b.roomByKey.get(`${l.b[0]}:${l.b[1]}`);
      if (!ra || !rb) continue;
      this.links.push({ kind: l.kind, a: this.snap(ra.floor, ra.label), b: this.snap(rb.floor, rb.label), ra, rb });
    }
    this.stats = { expanded: 0, ms: 0, mode: '' }; // what the last search cost, for the routing benchmark
    this.linkAt = new Map();
    this.hasLink = new Uint8Array(this.n);
    for (const l of this.links) {
      push(this.linkAt, l.a, [l.b, l]);
      push(this.linkAt, l.b, [l.a, l]);
      this.hasLink[l.a] = this.hasLink[l.b] = 1;
    }
  }

  // Connected open areas per floor (same 8-neighbour moves as the search), so snapping can skip tiny pockets.
  labelAreas() {
    const { w, h, per } = this;
    this.area = new Int32Array(this.n).fill(-1);
    this.areaSize = [];
    const stack = new Int32Array(this.n);
    for (let s = 0; s < this.n; s++) {
      if (!this.cells[s] || this.area[s] >= 0) continue;
      const id = this.areaSize.length, base = s - (s % per);
      let top = 0, size = 0;
      stack[top++] = s; this.area[s] = id;
      while (top) {
        const c = stack[--top], r = c - base, x = r % w, y = (r / w) | 0;
        size++;
        for (let k = 0; k < 8; k++) {
          const X = x + DX[k], Y = y + DY[k];
          if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
          const j = base + Y * w + X;
          if (this.cells[j] && this.area[j] < 0) { this.area[j] = id; stack[top++] = j; }
        }
      }
      this.areaSize.push(size);
    }
  }

  // Nearest open cell to a plan point on a floor (in an area big enough to walk around in).
  snap(fid, [x, y]) {
    const fi = this.b.floorIndex[fid];
    const cx = Math.round((x - this.b.grid.x0) / this.b.grid.cell - 0.5);
    const cy = Math.round((y - this.b.grid.y0) / this.b.grid.cell - 0.5);
    for (let r = 0; r < 40; r++) {
      let best = -1, bd = Infinity;
      for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
        const X = cx + dx, Y = cy + dy;
        if (X < 0 || Y < 0 || X >= this.w || Y >= this.h) continue;
        const i = fi * this.per + Y * this.w + X;
        if (this.cells[i] && this.areaSize[this.area[i]] >= MIN_AREA && dx * dx + dy * dy < bd) { bd = dx * dx + dy * dy; best = i; }
      }
      if (best >= 0) return best;
    }
    return fi * this.per + cy * this.w + cx;
  }

  cellToPlan(i) {
    const f = Math.floor(i / this.per), r = i % this.per;
    const { x0, y0, cell } = this.b.grid;
    return { floor: this.b.floors[f].id, x: x0 + ((r % this.w) + 0.5) * cell, y: y0 + (Math.floor(r / this.w) + 0.5) * cell };
  }

  // Other open areas on the goal's floor within NEAR_M, nearest first (one cell each): where to send you if
  // the room itself can't be reached (its door isn't drawn, or a drawn railing seals it).
  nearbyGoals(goal) {
    const { w, h, per } = this;
    const fi = Math.floor(goal / per), r = goal % per, gx = r % w, gy = (r / w) | 0;
    const maxR = Math.ceil(NEAR_M / (this.b.mPerPx * this.b.grid.cell));
    const found = new Map();
    for (let rad = 1; rad <= maxR; rad++) {
      for (let dy = -rad; dy <= rad; dy++) for (let dx = -rad; dx <= rad; dx++) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== rad) continue;
        const X = gx + dx, Y = gy + dy;
        if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
        const i = fi * per + Y * w + X, a = this.area[i];
        if (!this.cells[i] || a === this.area[goal] || this.areaSize[a] < MIN_AREA) continue;
        const d = dx * dx + dy * dy;
        if (!found.has(a) || d < found.get(a)[1]) found.set(a, [i, d]);
      }
      if (found.size >= 3) break;
    }
    return [...found.values()].sort((a, c) => a[1] - c[1]).map(([i]) => i);
  }

  route(start, goal, opts = {}) {
    const legs = this.routeTo(start, goal, opts);
    if (legs) return legs;
    for (const near of this.nearbyGoals(goal)) {
      const l = this.routeTo(start, near, opts);
      if (l) return l;
    }
    return null;
  }

  /** Straight-line distance in cells to cell `to`, plus the floors still to change. */
  heuristic(to) {
    const { w, per } = this;
    const tx = to % per % w, ty = Math.floor(to % per / w), tf = Math.floor(to / per);
    return (i) => {
      const r = i % per, dx = r % w - tx, dy = ((r / w) | 0) - ty; // (Math.hypot is slow in hot loops)
      return Math.sqrt(dx * dx + dy * dy) + Math.abs(((i / per) | 0) - tf) * STAIR_COST * 0.9;
    };
  }

  routeTo(start, goal, { stepFree = false, diagonal = true, bidirectional = false } = {}) {
    const clock = typeof performance !== 'undefined' ? performance : Date;
    const t0 = clock.now();
    const cells = bidirectional && start !== goal
      ? this.searchBoth(start, goal, stepFree, diagonal)
      : this.searchOne(start, goal, stepFree, diagonal);
    this.stats = {
      expanded: this.expanded, ms: clock.now() - t0,
      mode: `${bidirectional ? 'bidirectional' : 'one-way'}, ${diagonal ? '8' : '4'}-way`,
    };
    return cells && this.toLegs(cells);
  }

  // One-way A*: grow out from the start until the goal comes off the queue.
  searchOne(start, goal, stepFree, diagonal) {
    const gen = this.search(start, this.heuristic(goal), (cur) => cur === goal, stepFree, diagonal);
    if (this.seen[goal] !== gen) return null;
    const cells = [];
    for (let i = goal; i !== -1; i = this.from[i]) cells.push(i);
    return cells.reverse();
  }

  /**
   * Routes from every start to one goal in a single search: it grows outward from the goal until every
   * start is reached. (Path costs are symmetric apart from the first/last cell, which doesn't matter here.)
   * Returns an array of legs (or null) per start.
   */
  routeMany(starts, goal, opts = {}) {
    const all = this.routeManyTo(starts, goal, opts);
    if (all.some(Boolean)) return all;
    for (const near of this.nearbyGoals(goal)) {
      const res = this.routeManyTo(starts, near, opts);
      if (res.some(Boolean)) return res;
    }
    return all;
  }

  routeManyTo(starts, goal, { stepFree = false, diagonal = true } = {}) {
    const want = new Set(starts);
    // one spread outward from the goal reaches every entrance, which beats running an A* per entrance;
    // it prices steps in reverse so each total matches the walk in from that entrance
    const gen = this.search(goal, () => 0, (cur) => want.delete(cur) && want.size === 0, stepFree, diagonal, true);
    return starts.map((s) => {
      if (this.seen[s] !== gen) return null;
      const cellsPath = [];
      for (let i = s; i !== -1; i = this.from[i]) cellsPath.push(i); // from[] already points toward the goal
      return this.toLegs(cellsPath);
    });
  }

  // Best-first search over the stacked grids (A* with a heuristic, Dijkstra with heur = 0).
  search(source, heur, done, stepFree, diagonal = true, reverse = false) {
    const { w, h, per, cells, g, from, seen, closed, hasLink } = this;
    const gen = ++this.gen;
    const dirs = diagonal ? 8 : 4;
    this.expanded = 0;
    const heap = new Heap();
    g[source] = 0; from[source] = -1; seen[source] = gen;
    heap.push(source, heur(source));
    while (heap.size) {
      const cur = heap.pop();
      if (closed[cur] === gen) continue; // a stale queue entry: this cell was already finished
      closed[cur] = gen;
      this.expanded++;
      if (done(cur)) break;
      const gc = g[cur];
      const r = cur % per, x = r % w, y = (r - x) / w, base = cur - r;
      const here = cells[cur];
      for (let k = 0; k < dirs; k++) {
        const X = x + DX[k], Y = y + DY[k];
        if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
        const ni = base + Y * w + X;
        const c = cells[ni];
        if (!c || closed[ni] === gen) continue;
        if (k >= 4 && (!cells[base + y * w + X] || !cells[base + Y * w + x])) continue; // no corner cutting
        const ng = gc + DL[k] * ((reverse ? here : c) === 2 ? ROOM_COST : 1);
        if (seen[ni] !== gen || ng < g[ni]) {
          seen[ni] = gen; g[ni] = ng; from[ni] = cur;
          heap.push(ni, ng + heur(ni));
        }
      }
      const ls = hasLink[cur] ? this.linkAt.get(cur) : null; // only ~70 cells are stairs/elevators
      if (ls) for (const [ni, l] of ls) {
        if (stepFree && l.kind === 'stair') continue;
        const floors = Math.abs(Math.floor(ni / per) - Math.floor(cur / per));
        const ng = gc + floors * (l.kind === 'stair' ? STAIR_COST : ELEVATOR_COST);
        if (seen[ni] !== gen || ng < g[ni]) {
          seen[ni] = gen; g[ni] = ng; from[ni] = cur;
          heap.push(ni, ng + heur(ni));
        }
      }
    }
    return gen;
  }

  // Scratch arrays for the search that grows out from the goal. Allocated on first use: a one-way search
  // never needs them, and on a big building they are a few megabytes.
  backArrays() {
    if (!this.gB) {
      this.gB = new Float64Array(this.n);
      this.fromB = new Int32Array(this.n);
      this.seenB = new Uint32Array(this.n);
      this.closedB = new Uint32Array(this.n);
    }
    return this;
  }

  /**
   * Bidirectional A*: one search grows out from the start, the other from the goal, and they meet.
   * Expanding the side whose best f is smaller keeps the two frontiers balanced.
   * Stopping rule: once a frontier's best f has reached the best meeting cost found, nothing cheaper can
   * come through it (the heuristic is consistent), so the meeting path is a shortest path.
   */
  searchBoth(start, goal, stepFree, diagonal) {
    const { g, from, seen, closed, w, h, per, cells, hasLink } = this.backArrays();
    const { gB, fromB, seenB, closedB } = this;
    const gen = ++this.gen;
    const dirs = diagonal ? 8 : 4;
    const hF = this.heuristic(goal), hB = this.heuristic(start);
    this.expanded = 0;

    const heapF = new Heap(), heapB = new Heap();
    g[start] = 0; from[start] = -1; seen[start] = gen; heapF.push(start, hF(start));
    gB[goal] = 0; fromB[goal] = -1; seenB[goal] = gen; heapB.push(goal, hB(goal));

    let best = Infinity, meet = -1;
    while (heapF.size && heapB.size) {
      if (heapF.top >= best || heapB.top >= best) break; // neither side can still improve on `best`
      const forward = heapF.top <= heapB.top;
      const heap = forward ? heapF : heapB;
      const cur = heap.pop();
      const mine = forward ? closed : closedB;
      if (mine[cur] === gen) continue; // a stale queue entry: already finished
      mine[cur] = gen;
      this.expanded++;
      // the other side may already have reached this cell: finishing it here gives a complete path
      if ((forward ? seenB : seen)[cur] === gen) {
        const join = (forward ? g : gB)[cur] + (forward ? gB : g)[cur];
        if (join < best) { best = join; meet = cur; }
      }
      // relax one neighbour, whichever direction we are going in
      const G = forward ? g : gB, F = forward ? from : fromB, S = forward ? seen : seenB;
      const oG = forward ? gB : g, oS = forward ? seenB : seen;
      const h = forward ? hF : hB;
      const gc = G[cur];
      // the same steps as moves(), written out: this is the hot loop, and a generator allocates on every step
      const r = cur % per, x = r % w, y = (r - x) / w, base = cur - r;
      const here = cells[cur];
      for (let k = 0; k < dirs; k++) {
        const X = x + DX[k], Y = y + DY[k];
        if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
        const ni = base + Y * w + X;
        const c = cells[ni];
        if (!c || mine[ni] === gen) continue;
        if (k >= 4 && (!cells[base + y * w + X] || !cells[base + Y * w + x])) continue; // no corner cutting
        const ng = gc + DL[k] * ((forward ? c : here) === 2 ? ROOM_COST : 1);
        if (S[ni] !== gen || ng < G[ni]) {
          S[ni] = gen; G[ni] = ng; F[ni] = cur;
          heap.push(ni, ng + h(ni));
        }
        // checked whether or not we improved it: the other side may have reached it since we last looked
        if (oS[ni] === gen && G[ni] + oG[ni] < best) { best = G[ni] + oG[ni]; meet = ni; }
      }
      const ls = hasLink[cur] ? this.linkAt.get(cur) : null;
      if (ls) for (const [ni, l] of ls) {
        if (stepFree && l.kind === 'stair') continue;
        if (mine[ni] === gen) continue;
        const ng = gc + Math.abs(Math.floor(ni / per) - Math.floor(cur / per)) * (l.kind === 'stair' ? STAIR_COST : ELEVATOR_COST);
        if (S[ni] !== gen || ng < G[ni]) {
          S[ni] = gen; G[ni] = ng; F[ni] = cur;
          heap.push(ni, ng + h(ni));
        }
        if (oS[ni] === gen && G[ni] + oG[ni] < best) { best = G[ni] + oG[ni]; meet = ni; }
      }
    }
    if (meet < 0) return null;
    const path = [];
    for (let i = meet; i !== -1; i = from[i]) path.push(i);
    path.reverse();
    for (let i = fromB[meet]; i !== -1; i = fromB[i]) path.push(i); // on toward the goal
    return path;
  }

  /**
   * Every step out of a cell as [neighbour, cost]: the 4 or 8 grid moves, then any stairs or lift.
   * A move is priced by the cell it ENTERS, so the grid is directed: stepping into a room costs ROOM_COST and
   * stepping back out of it costs 1. A search running outward from the goal has to price each edge the way the
   * walker will travel it, which is what `reverse` does; without it the totals come out slightly wrong.
   */
  *moves(cur, stepFree, diagonal, reverse = false) {
    const { w, h, per, cells } = this;
    const r = cur % per, x = r % w, y = (r - x) / w, base = cur - r;
    const dirs = diagonal ? 8 : 4;
    const here = cells[cur];
    for (let k = 0; k < dirs; k++) {
      const X = x + DX[k], Y = y + DY[k];
      if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
      const ni = base + Y * w + X;
      const c = cells[ni];
      if (!c) continue;
      if (k >= 4 && (!cells[base + y * w + X] || !cells[base + Y * w + x])) continue; // no corner cutting
      yield [ni, DL[k] * ((reverse ? here : c) === 2 ? ROOM_COST : 1)];
    }
    const ls = this.hasLink[cur] ? this.linkAt.get(cur) : null; // only ~70 cells are stairs/lifts
    if (ls) for (const [ni, l] of ls) {
      if (stepFree && l.kind === 'stair') continue;
      const floors = Math.abs(Math.floor(ni / per) - Math.floor(cur / per));
      yield [ni, floors * (l.kind === 'stair' ? STAIR_COST : ELEVATOR_COST)];
    }
  }

  // Split a cell path into per-floor polylines joined by vertical transitions.
  toLegs(path) {
    const legs = [];
    let cur = null;
    for (let k = 0; k < path.length; k++) {
      const p = this.cellToPlan(path[k]);
      if (!cur || cur.floor !== p.floor) {
        if (cur) {
          const link = (this.linkAt.get(path[k - 1]) || []).find(([ni]) => ni === path[k])?.[1];
          legs.push({ transition: true, kind: link?.kind || 'stair', from: cur.floor, to: p.floor, at: cur.pts.at(-1) });
        }
        cur = { floor: p.floor, pts: [] };
        legs.push(cur);
      }
      cur.pts.push([p.x, p.y]);
    }
    for (const l of legs) if (l.pts) {
      l.pts = simplify(l.pts, 4);
      l.meters = polyLen(l.pts) * this.b.mPerPx;
    }
    return legs;
  }
}

function push(map, k, v) { (map.get(k) || map.set(k, []).get(k)).push(v); }

export function polyLen(pts) {
  let s = 0;
  for (let i = 1; i < pts.length; i++) s += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return s;
}

// Douglas–Peucker
export function simplify(pts, eps) {
  if (pts.length < 3) return pts;
  const keep = new Uint8Array(pts.length); keep[0] = keep[pts.length - 1] = 1;
  const stack = [[0, pts.length - 1]];
  while (stack.length) {
    const [a, b] = stack.pop();
    let md = 0, mi = -1;
    const [ax, ay] = pts[a], [bx, by] = pts[b];
    const L = Math.hypot(bx - ax, by - ay) || 1;
    for (let i = a + 1; i < b; i++) {
      const d = Math.abs((bx - ax) * (ay - pts[i][1]) - (ax - pts[i][0]) * (by - ay)) / L;
      if (d > md) { md = d; mi = i; }
    }
    if (md > eps) { keep[mi] = 1; stack.push([a, mi], [mi, b]); }
  }
  return pts.filter((_, i) => keep[i]);
}

class Heap {
  constructor() { this.ids = []; this.ks = []; }
  get size() { return this.ids.length; }
  get top() { return this.ids.length ? this.ks[0] : Infinity; }
  push(id, k) {
    const { ids, ks } = this;
    let i = ids.length; ids.push(id); ks.push(k);
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (ks[p] <= k) break;
      ids[i] = ids[p]; ks[i] = ks[p]; i = p;
    }
    ids[i] = id; ks[i] = k;
  }
  pop() {
    const { ids, ks } = this;
    const top = ids[0], lid = ids.pop(), lk = ks.pop();
    if (ids.length) {
      let i = 0;
      for (;;) {
        let c = 2 * i + 1;
        if (c >= ids.length) break;
        if (c + 1 < ids.length && ks[c + 1] < ks[c]) c++;
        if (ks[c] >= lk) break;
        ids[i] = ids[c]; ks[i] = ks[c]; i = c;
      }
      ids[i] = lid; ks[i] = lk;
    }
    return top;
  }
}

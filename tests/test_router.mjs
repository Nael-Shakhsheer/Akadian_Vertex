// Indoor routing: the bidirectional search must find paths of exactly the same cost as the one-way search,
// with and without diagonals, and step-free must never use stairs.  Run: node tests/test_router.mjs
//
// Cost is the invariant, not the drawn polyline: equal-cost paths can run through different cells, and
// Douglas-Peucker then smooths them slightly differently.
import { readFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';

const { Router } = await import(new URL('../app/js/router.js', import.meta.url));
const { decodeRle } = await import(new URL('../app/js/building.js', import.meta.url));

const root = new URL('..', import.meta.url);
const file = ['docs/data/buildings/gmu-jc.json', 'engine_data/published/buildings/gmu-jc.json']
  .map((p) => new URL(p, root)).find((u) => existsSync(u));
assert.ok(file, 'no published Johnson Center map to test against');

const b = JSON.parse(readFileSync(file, 'utf8'));
b.mPerPx = b.mPerPx || Math.hypot(b.building.transform[0], b.building.transform[3]);
const { w, h } = b.grid;
for (const f of b.floors) { f.cells = decodeRle(f.grid, w * h); delete f.grid; }
b.floorIndex = Object.fromEntries(b.floors.map((f, i) => [f.id, i]));
b.roomByKey = new Map(b.rooms.map((r) => [`${r.floor}:${r.id}`, r]));

const router = new Router(b);

/** What the walk along this cell path actually costs, priced the way the walker travels it. */
function cost(cells, { stepFree = false, diagonal = true } = {}) {
  let total = 0;
  for (let i = 1; i < cells.length; i++) {
    let step = null;
    for (const [ni, c] of router.moves(cells[i - 1], stepFree, diagonal)) if (ni === cells[i]) step = Math.min(step ?? c, c);
    assert.ok(step !== null, `step ${i} of the path is not a legal move`);
    total += step;
  }
  return total;
}

// a spread of real destinations: every named room, plus the restrooms
const targets = b.rooms.filter((r) => (r.kind === 'room' && r.name) || r.kind === 'restroom');
assert.ok(targets.length > 20, `expected plenty of rooms, got ${targets.length}`);
const entrances = b.entrances.map((e) => router.snap(e.floor, e.start));

let checked = 0, oneCells = 0, biCells = 0, oneMs = 0, biMs = 0;
for (const room of targets) {
  const goal = router.snap(room.floor, room.label);
  for (const start of entrances) {
    const one = router.searchOne(start, goal, false, true);
    const oneStats = { expanded: router.expanded };
    const t0 = performance.now(); router.searchOne(start, goal, false, true); oneMs += performance.now() - t0;
    const t1 = performance.now(); const two = router.searchBoth(start, goal, false, true); biMs += performance.now() - t1;
    const twoStats = { expanded: router.expanded };

    assert.equal(!!one, !!two, `the two searches disagree on whether ${room.id} can be reached`);
    if (!one) continue;
    assert.ok(Math.abs(cost(one) - cost(two)) < 1e-6,
      `${room.id}: one-way costs ${cost(one).toFixed(3)}, bidirectional ${cost(two).toFixed(3)}`);
    assert.equal(one[0], start, 'the path must start where we asked');
    assert.equal(two[0], start, 'the bidirectional path must start where we asked');
    assert.equal(two.at(-1), goal, 'the bidirectional path must end on the goal');
    checked++;
    oneCells += oneStats.expanded; biCells += twoStats.expanded;
  }
}
assert.ok(checked > 100, `expected to check many routes, checked ${checked}`);

// 4-way: a legal path, never cheaper than the 8-way one, and the two searches still agree
for (const room of targets.slice(0, 25)) {
  const goal = router.snap(room.floor, room.label);
  const start = entrances[0];
  const eight = router.searchOne(start, goal, false, true);
  const four = router.searchOne(start, goal, false, false);
  if (!eight || !four) continue;
  assert.ok(cost(four, { diagonal: false }) >= cost(eight) - 1e-6,
    `${room.id}: the 4-way path came out cheaper than the 8-way one`);
  const fourBi = router.searchBoth(start, goal, false, false);
  assert.ok(Math.abs(cost(four, { diagonal: false }) - cost(fourBi, { diagonal: false })) < 1e-6,
    `${room.id}: 4-way one-way and bidirectional disagree`);
}

// step-free never takes a stair link
assert.ok(router.links.some((l) => l.kind === 'stair'), 'expected the Johnson Center to have stairs');
let stepFreeChecked = 0;
for (const room of targets.filter((r) => r.floor !== 'first').slice(0, 15)) {
  const legs = router.route(entrances[0], router.snap(room.floor, room.label), { stepFree: true });
  if (!legs) continue;
  assert.ok(legs.every((l) => !l.transition || l.kind === 'elevator'), `${room.id}: step-free route still uses stairs`);
  stepFreeChecked++;
}
assert.ok(stepFreeChecked > 5, 'expected step-free routes to other floors');

// the public API still returns usable legs
const legs = router.route(entrances[0], router.snap(targets[0].floor, targets[0].label));
assert.ok(legs?.length && legs.some((l) => l.pts?.length), 'route() should return drawable legs');
assert.ok(router.stats.mode.includes('one-way'), 'route() defaults to the one-way search: it expands fewer cells here');

console.log(`router: ok — ${checked} routes, both searches agree to the cent`);
console.log(`  one-way        ${oneCells.toLocaleString()} cells expanded, ${oneMs.toFixed(0)} ms`);
console.log(`  bidirectional  ${biCells.toLocaleString()} cells expanded, ${biMs.toFixed(0)} ms`
  + `  (${(100 - (biCells / oneCells) * 100).toFixed(0)}% fewer cells, ${(100 - (biMs / oneMs) * 100).toFixed(0)}% less time)`);

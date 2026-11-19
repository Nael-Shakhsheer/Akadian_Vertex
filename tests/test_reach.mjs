// Every room and restroom in every published building can be reached from its entrances -- walking, and
// step-free -- through the same Router.route() the app's routing worker calls.
//
//     node tests/test_reach.mjs
//
// This is the check that found Fenwick Library's sealed rooms (its maps draw no doors) and three phantom
// rooms in Torgersen Hall that OCR had read off the linework, so it covers every building, not one.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';

const { Router } = await import(new URL('../app/js/router.js', import.meta.url));
const { decodeRle } = await import(new URL('../app/js/building.js', import.meta.url));

const root = new URL('..', import.meta.url);
const dir = ['docs/data/buildings/', 'engine_data/published/buildings/'].map((p) => new URL(p, root)).find((u) => existsSync(u));
assert.ok(dir, 'no published buildings to test against');
const files = readdirSync(dir).filter((f) => f.endsWith('.json')).sort();
assert.ok(files.length, 'no published buildings to test against');

let total = 0;
const t0 = performance.now();
for (const file of files) {
  const b = JSON.parse(readFileSync(new URL(file, dir), 'utf8'));
  b.mPerPx = b.mPerPx || Math.hypot(b.building.transform[0], b.building.transform[3]);
  const { w, h } = b.grid;
  for (const f of b.floors) { f.cells = decodeRle(f.grid, w * h); delete f.grid; }
  b.floorIndex = Object.fromEntries(b.floors.map((f, i) => [f.id, i]));
  b.roomByKey = new Map(b.rooms.map((r) => [`${r.floor}:${r.id}`, r]));
  const router = new Router(b);
  const starts = b.entrances.map((e) => router.snap(e.floor, e.start));
  assert.ok(starts.length, `${file}: no entrances`);

  const unreachable = [], unreachableStepFree = [];
  const targets = b.rooms.filter((r) => r.kind === 'room' || r.kind === 'restroom');
  for (const r of targets) {
    const goal = router.snap(r.floor, r.label);
    if (!starts.some((s) => router.route(s, goal, { stepFree: false }))) unreachable.push(`${r.floor}:${r.id}`);
    if (!starts.some((s) => router.route(s, goal, { stepFree: true }))) unreachableStepFree.push(`${r.floor}:${r.id}`);
  }
  assert.deepEqual(unreachable, [], `${file}: rooms no route reaches`);
  assert.deepEqual(unreachableStepFree, [], `${file}: rooms no step-free route reaches`);
  total += targets.length;
}
console.log(`reach: ok — ${total} rooms and restrooms in ${files.length} buildings, all reachable on foot and step-free `
  + `(${((performance.now() - t0) / 1000).toFixed(0)} s)`);

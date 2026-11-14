// The service worker's fetch handler, driven in a stubbed worker.
//
// What is being pinned down is the network deadline: on campus wi-fi a request can hang for a long time before
// it fails, and the app should not sit there when a good copy is already on the device. A real service worker
// needs a browser, so the script is run here with `self`, `caches` and `fetch` stubbed, and the handler is
// called the way the browser would call it.
//
//     node tests/test_sw.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(path.join(root, 'app/sw.js'), 'utf8');

function worker({ net, cacheHas }) {
  const listeners = {};
  const waits = [];
  const self_ = { addEventListener: (k, f) => (listeners[k] = f), skipWaiting() {}, clients: { claim() {} } };
  const caches = { match: async (r) => (cacheHas(String(r.url ?? r)) ? { body: 'cached' } : undefined), open: async () => ({ put() {} }) };
  const fetch_ = (req) => net(req);
  const Response_ = { error: () => ({ body: 'neterror' }) };
  new Function('self', 'caches', 'fetch', 'Response', 'location', src)
    (self_, caches, fetch_, Response_, { origin: 'https://x.test' });
  return {
    get: (url, mode = 'same-origin') => new Promise((done, fail) => {
      const req = { url, method: 'GET', mode };
      listeners.fetch({ request: req, respondWith: (p) => Promise.resolve(p).then(done, fail), waitUntil: (p) => waits.push(p) });
    }),
    waits,
  };
}
const slow = (ms, body) => new Promise((r) => setTimeout(r, ms, { ok: true, body, clone: () => ({}) }));
const U = 'https://x.test/data/gmu.json';

// 1. network answers in time -> fresh, even with a cached copy on hand
let w = worker({ net: () => slow(10, 'fresh'), cacheHas: () => true });
assert.equal((await w.get(U)).body, 'fresh');

// 2. network stalls past the deadline -> the cached copy, and the request is kept alive to refresh it
let finished = false;
w = worker({ net: () => slow(4000, 'fresh').then((r) => ((finished = true), r)), cacheHas: () => true });
let t = Date.now();
assert.equal((await w.get(U)).body, 'cached');
assert.ok(Date.now() - t >= 2400 && Date.now() - t < 3200, `served at ${Date.now() - t}ms`);
assert.equal(w.waits.length, 1, 'the stalled request is handed to waitUntil');
await w.waits[0];
assert.ok(finished, 'it finishes in the background and refreshes the cache');

// 3. offline with a cached copy -> cache, immediately, no waiting out the deadline
w = worker({ net: () => Promise.reject(new Error('offline')), cacheHas: () => true });
t = Date.now();
assert.equal((await w.get(U)).body, 'cached');
assert.ok(Date.now() - t < 500, 'a failure is not made to wait for the timer');

// 4. nothing cached -> wait for the network however long it takes, rather than failing at the deadline
w = worker({ net: () => slow(3500, 'fresh'), cacheHas: () => false });
assert.equal((await w.get(U)).body, 'fresh');

// 5. nothing cached, offline, a deep link -> the cached shell
w = worker({ net: () => Promise.reject(new Error('offline')), cacheHas: (u) => u.endsWith('./') });
assert.equal((await w.get('https://x.test/?to=344', 'navigate')).body, 'cached');

// 6. long-lived assets stay cache-first and never touch the network
w = worker({ net: () => { throw new Error('should not be fetched'); }, cacheHas: () => true });
assert.equal((await w.get('https://x.test/vendor/maplibre.js')).body, 'cached');

console.log('sw: 6 cases ok');

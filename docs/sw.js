// Offline support: the app keeps working on campus with a weak signal.
// App files and map data: network first (always fresh), cache as fallback — but not at any cost. Campus wi-fi
//   is often associated with no throughput, where a request waits a long time before it finally fails, and the
//   app would sit there with a perfectly good copy already on the device. So the network gets NET_TIMEOUT to
//   answer; past that, a cached copy is served and the request is left to finish and refresh the cache for
//   next time. Nothing is served stale while the network is working.
// Libraries, map tiles, fonts and icons: cache first (they never change for a given URL).
// Paths are relative to where the app is served (/ on the engine, /<repo>/ on GitHub Pages).
const CACHE = 'akadian-v8'; // v8: home-screen icons and launch images
const SHELL = ['./', 'style.css', 'manifest.webmanifest', 'icons/icon-192.png'];
const LONG_LIVED = ['/vendor/', '/tiles/', '/fonts/', '/icons/', '/splash/'];
const NET_TIMEOUT = 2500; // ms: comfortable for a working connection, short enough not to stall a launch

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

function keep(req, res) {
  if (res.ok) {
    const copy = res.clone();
    caches.open(CACHE).then((c) => c.put(req, copy));
  }
  return res;
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (LONG_LIVED.some((p) => url.pathname.includes(p))) {
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((res) => keep(req, res))));
    return;
  }
  e.respondWith(fresh(e, req));
});

/** The network, given a deadline; past it a cached copy wins and the request refreshes the cache behind us. */
async function fresh(e, req) {
  const network = fetch(req).then((res) => keep(req, res));
  const cached = await caches.match(req);
  if (!cached) {
    // nothing better to offer, so wait it out; deep links (?to=344 …) all share the page, so fall back to it
    try {
      return await network;
    } catch {
      return (req.mode === 'navigate' && await caches.match('./')) || Response.error();
    }
  }
  let timer;
  try {
    return await Promise.race([network, new Promise((_, slow) => { timer = setTimeout(slow, NET_TIMEOUT, new Error('slow')); })]);
  } catch {
    e.waitUntil(network.catch(() => {})); // let it finish: that is what makes the next launch current
    return cached;
  } finally {
    clearTimeout(timer);
  }
}

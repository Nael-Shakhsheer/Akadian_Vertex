// How much the app gets used — and nothing about who used it.
//
// This keeps a handful of counters in memory and, when you leave the page, posts the tallies. That is the
// whole of it: no identifier, no cookie, no clock time, no position, no route, nothing naming a room, and
// no order of events. The server keeps a per-day total and can tell how many searches happened on a given
// day; it cannot tell that two of them were the same person, or that anyone went anywhere.
//
// It stays switched off unless the page is served by the engine, which sets window.AKADIAN_USAGE. The
// static GitHub Pages build has no server to count with, so it quietly counts nothing. Settings has an
// off switch, and a device asking not to be tracked is taken at its word.
//
// Why bother: the case for the app being made official rests on showing it is used, and nobody can produce
// that number afterwards. Counting has to be in place before the people are.
const ENDPOINT = typeof window !== 'undefined' ? window.AKADIAN_USAGE : null;
export const KEY = 'akadian:usage';

const dnt = () => navigator.doNotTrack === '1' || window.doNotTrack === '1';
export const usageOn = () => {
  try { return localStorage.getItem(KEY) !== 'off'; } catch { return true; }
};
export function setUsage(on) {
  try { localStorage.setItem(KEY, on ? 'on' : 'off'); } catch {}
  if (!on) { events = {}; buildings = {}; }
}

let campus = '';
let events = {};
let buildings = {};
let timer = null;

const live = () => Boolean(ENDPOINT) && usageOn() && !dnt();

/** Note that something happened once. Unknown names are dropped by the server, not silently kept here. */
export function count(name) {
  if (!live()) return;
  events[name] = (events[name] || 0) + 1;
  schedule();
}

/** Note that a building's inside was opened. The id is a building, never a room. */
export function countBuilding(id) {
  if (!live() || !id) return;
  buildings[id] = (buildings[id] || 0) + 1;
  count('indoor');
}

export function setCampus(id) {
  campus = id || '';
}

// Most visits end by the tab being hidden, which is the reliable moment to send. The timer is only for a
// page left open all day and then killed, where that moment never arrives.
function schedule() {
  if (timer === null) timer = setTimeout(send, 60000);
}

function send() {
  clearTimeout(timer);
  timer = null;
  if (!live()) return;
  const body = { campus, events, buildings };
  if (!Object.keys(events).length && !Object.keys(buildings).length) return;
  events = {};
  buildings = {};
  try {
    // text/plain keeps this a "simple" request: no preflight, so it also works when the app is served
    // from somewhere other than the engine. The server parses the body as JSON whatever the type says.
    const blob = new Blob([JSON.stringify(body)], { type: 'text/plain;charset=UTF-8' });
    if (!navigator.sendBeacon?.(ENDPOINT, blob)) {
      fetch(ENDPOINT, { method: 'POST', body: blob, keepalive: true, mode: 'no-cors' }).catch(() => {});
    }
  } catch {}
}

/** Call once at boot, after the campus is known. */
export function startUsage(campusId) {
  setCampus(campusId);
  if (!live()) return;
  count('open');
  if (matchMedia('(display-mode: standalone)').matches || navigator.standalone === true) count('standalone');
  if (!navigator.onLine) count('offline');
  document.addEventListener('visibilitychange', () => { if (document.hidden) send(); });
  addEventListener('pagehide', send); // pagehide is a window event; visibilitychange is the document's
}

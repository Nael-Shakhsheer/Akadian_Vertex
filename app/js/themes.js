// Appearance: a base (dark or light) and an accent, applied to the whole app — interface, map route, the 3D
// views and the wordmark. Kept free of Three.js so the picker and the no-flash boot script cost nothing before
// the 3D bundle loads. The choice is stored on the device, so it survives closing the app.
//
//   standard  the house look: dark base, warm orange
//   light     white base, black outlines, a more vibrant orange to hold up against the paper
//   custom    any base with any accent

export const ACCENTS = {
  orange: { label: 'Orange', dark: '#f0a04a', light: '#d2600a' },
  red: { label: 'Red', dark: '#ff6b6b', light: '#c62828' },
  green: { label: 'Green', dark: '#4ade80', light: '#15803d' },
  blue: { label: 'Blue', dark: '#60a5fa', light: '#1d4ed8' },
  gold: { label: 'Gold', dark: '#fbbf24', light: '#a16207' },
  purple: { label: 'Purple', dark: '#c084fc', light: '#7c3aed' },
};
export const MODES = {
  standard: { label: 'Standard', hint: 'Dark, warm orange', base: 'dark', accent: 'orange' },
  light: { label: 'Light', hint: 'White, black outlines', base: 'light', accent: 'orange' },
  custom: { label: 'Custom', hint: 'Pick a base and a colour' },
};
export const KEY = 'akadian:appearance';
export const DEFAULTS = { mode: 'light', base: 'light', accent: 'orange' }; // light is what the app starts as

// ---------- colour helpers ----------
const clamp = (n) => Math.max(0, Math.min(255, Math.round(n)));
export const hexOf = (c) => (typeof c === 'number' ? `#${c.toString(16).padStart(6, '0')}` : c);
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const toHex = (r, g, b) => `#${[r, g, b].map((v) => clamp(v).toString(16).padStart(2, '0')).join('')}`;
/** Blend two hex colours; t = 0 keeps a, t = 1 gives b. */
export function mix(a, b, t) {
  const [r1, g1, b1] = rgb(a), [r2, g2, b2] = rgb(b);
  return toHex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t);
}
const int = (h) => parseInt(h.slice(1), 16);

// ---------- what is set ----------
export function loadAppearance() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY));
    if (saved && MODES[saved.mode]) {
      return { ...DEFAULTS, ...saved, ...(saved.mode === 'custom' ? {} : MODES[saved.mode]) };
    }
  } catch {}
  return { ...DEFAULTS, ...MODES.light };
}
export function saveAppearance(next) {
  const merged = { ...loadAppearance(), ...next };
  const settled = merged.mode === 'custom' ? merged : { ...merged, ...MODES[merged.mode] };
  try {
    localStorage.setItem(KEY, JSON.stringify({ mode: settled.mode, base: settled.base, accent: settled.accent }));
  } catch {}
  return settled;
}
/** The appearance as concrete values: which base, and the accent hex for that base. */
export function resolved(a = loadAppearance()) {
  const accent = ACCENTS[a.accent] ? a.accent : 'orange';
  const base = a.base === 'light' ? 'light' : 'dark';
  return { mode: a.mode, base, accent, hex: ACCENTS[accent][base] };
}

// ---------- the interface ----------
// Surfaces per base. The light base uses a near-black line so panels and rooms read as outlined, not shaded.
const SURFACES = {
  dark: {
    '--bg': '#16181d', '--surface': '#1c1f25', '--card': '#262931', '--input': '#1d2027', '--raised': '#2d3038',
    '--line': '#353943', '--text': '#f2f3f5', '--muted': '#9aa0aa',
    '--glass-1': '#1c1f25cc', '--glass-2': '#1c1f25e6', '--glass-3': '#1c1f25f2', '--shadow': '#000000aa',
  },
  light: {
    '--bg': '#ffffff', '--surface': '#f6f7f9', '--card': '#ffffff', '--input': '#f1f3f6', '--raised': '#e9ecf1',
    '--line': '#15181e', '--text': '#15171c', '--muted': '#596070',
    '--glass-1': '#ffffffcc', '--glass-2': '#ffffffe8', '--glass-3': '#fffffff5', '--shadow': '#0000002e',
  },
};

/** Paint the chosen appearance onto the document. Safe to call before the app starts. */
export function applyAppearance(a = loadAppearance()) {
  const r = resolved(a);
  const root = document.documentElement;
  root.dataset.base = r.base;
  root.dataset.accent = r.accent;
  for (const [k, v] of Object.entries(SURFACES[r.base])) root.style.setProperty(k, v);
  root.style.setProperty('--accent', r.hex);
  root.style.setProperty('--accent-hi', r.base === 'dark' ? mix(r.hex, '#ffffff', 0.3) : mix(r.hex, '#000000', 0.2));
  root.style.setProperty('--on-accent', r.base === 'dark' ? '#1b1d22' : '#ffffff');
  root.style.setProperty('color-scheme', r.base);
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', SURFACES[r.base]['--bg']);
  applyTheme(a);
  return r;
}

// ---------- the 3D views ----------
// Structure stays neutral and the accent is kept for the route and its destination, so the thing you follow is
// the only thing that glows. Outline strength is tuned per base: a light base gets flat black lines and no bloom,
// because glow on a pale background just smears.
export function indoorPalette(a = loadAppearance()) {
  const r = resolved(a);
  if (r.base === 'light') {
    return {
      base: 'light', light: true, accentHex: r.hex,
      bg: 0xf4f6f9, grid: [0xd8dde5, 0xe8ecf1], slab: 0xdfe4ea, walk: 0xf8fafc, room: 0xe9edf2, shaft: 0xc7ced8,
      // outlines are the accent taken deeper rather than black: still dark enough to read on pale slabs, but
      // the whole plan stays in the app's colour instead of looking like a photocopy
      line: int(mix(r.hex, '#6b2800', 0.4)), accent: int(r.hex), hover: int(mix(r.hex, '#000000', 0.25)),
      bloom: [0, 0.4, 1], hemi: 0.95, sun: 0.45, edgeK: 1, roomK: 1, roomEdge: 0.95,
    };
  }
  return {
    base: 'dark', light: false, accentHex: r.hex,
    bg: 0x16181d, grid: [0x2a2d34, 0x1e2026], slab: 0x1f2228, walk: 0x363c47, room: 0x2d323c, shaft: 0x15171b,
    // the outline colour is the accent pulled most of the way to grey: present, but no longer glowing circuitry
    line: int(mix(r.hex, '#55585f', 0.5)), accent: int(r.hex), hover: int(mix(r.hex, '#ffffff', 0.45)),
    bloom: [0.3, 0.5, 0.78], hemi: 1.5, sun: 1.15, edgeK: 1.15, roomK: 0.42, roomEdge: 0.45,
  };
}

// A live object the 3D views read while they build: swap it and rebuild to re-skin the scene.
export const THEME = {};
export function applyTheme(a = loadAppearance()) {
  Object.assign(THEME, indoorPalette(a));
  return THEME;
}
applyTheme();

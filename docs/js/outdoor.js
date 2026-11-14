// Outdoor map: the campus in 3D (extruded building shells), everything around it flat 2D.
// Uses MapLibre GL (global `maplibregl`) over darkened OpenStreetMap raster tiles.

// The accent comes from the appearance the app booted with (js/themes.js sets it on <html>).
const cssVar = (name, fallback) =>
  (getComputedStyle(document.documentElement).getPropertyValue(name) || '').trim() || fallback;
const BASE = document.documentElement.dataset.base === 'light' ? 'light' : 'dark';
const ACCENT = cssVar('--accent', '#f0a04a');
const NEUTRAL = BASE === 'light' ? '#c3c8d2' : '#2b2f37';

// Basemap cartography per base. The campus itself is drawn from our own data on top of this; these are the
// surroundings, which stay quiet either way.
const MAP = {
  dark: {
    bg: '#15171c', wood: '#18201b', grass: '#171c19', park: '#171e1a', landuse: '#181a1f',
    water: '#0f1b26', waterway: '#13283a', bldg: '#1d2026', bldgEdge: '#262a31',
    path: '#2a2e36', minor: '#292d35', mid: '#30343d', major: '#383d48', rail: '#2a2d34',
    label: '#9aa0aa', bldgLabel: '#e9ebef', halo: '#16181d', sky: '#16181d', horizon: '#22252c', lightColor: '#ffffff', lightIntensity: 0.32,
  },
  light: {
    bg: '#eef1f5', wood: '#dfe9dc', grass: '#e6eee2', park: '#e3ede4', landuse: '#e9ebef',
    water: '#c7dcef', waterway: '#9fc2de', bldg: '#dcdfe6', bldgEdge: '#b9bec8',
    path: '#d2d6de', minor: '#ffffff', mid: '#ffffff', major: '#ffffff', rail: '#c6cad2',
    label: '#4a5160', bldgLabel: '#2a2f3a', halo: '#ffffff', sky: '#dce4ee', horizon: '#eef1f5', lightColor: '#ffffff', lightIntensity: 0.55,
  },
}[BASE];

// Color filter categories. Buildings and flat areas (lots, fields) share them.
export const CATEGORIES = [
  { id: 'academic', label: 'Academic', color: '#f0a04a' },
  { id: 'dorm', label: 'Residence halls', color: '#a98bff' },
  { id: 'parking', label: 'Parking', color: '#4da3ff' },
  { id: 'athletics', label: 'Arena & athletics', color: '#ff5f6d' },
  { id: 'fields', label: 'Sports fields', color: '#3fcf7f' },
  { id: 'transit', label: 'Bus & shuttle', color: '#2dd4bf' },
  { id: 'food', label: 'Food & coffee', color: '#ff7ab6' },
];
const TRANSIT = '#2dd4bf';
const PARK_COLOR = CATEGORIES.find((c) => c.id === 'parking').color;
// A marker's shadow: soft, small, and always on the ground.
const SHADOW = { 'circle-color': '#000000', 'circle-blur': 0.9, 'circle-opacity': 0.22 };
// Every marker that floats, with the paint property that moves it and a phase so the families bob out of step.
const FLOATERS = [
  ['park-shadow', 'circle-translate', 4.2, true], ['park-badge', 'circle-translate', 4.2], ['park-letter', 'text-translate', 4.2],
  ['area-names', 'text-translate', 4.2],
  ['stop-shadow', 'circle-translate', 0, true], ['stops', 'icon-translate', 0], ['stop-names', 'text-translate', 0],
  ['food-group-shadow', 'circle-translate', 2.1, true], ['food-group', 'icon-translate', 2.1], ['food-group-count', 'text-translate', 2.1],
  ['food-shadow', 'circle-translate', 2.1, true], ['food', 'icon-translate', 2.1], ['food-names', 'text-translate', 2.1],
];
const FOOD = '#ff7ab6';
// Widths and the side-by-side spacing of bus routes, all growing with the roads they follow so the lines stay
// on the road at every zoom. `slot` on each line is its place in the bundle: ..., -1, 0, 1, ...
// A zoom expression has to be the whole value, so the per-line multiply goes inside each stop rather than
// around the interpolate — MapLibre rejects the other way round and drops the entire style.
const TRANSIT_W = ['interpolate', ['exponential', 1.6], ['zoom'], 13, 0.8, 16, 1.8, 18, 3.2];
const TRANSIT_W_FOCUS = ['interpolate', ['exponential', 1.6], ['zoom'], 13, 1.8, 16, 3.8, 18, 6.6];
const TRANSIT_GLOW_W = ['interpolate', ['exponential', 1.6], ['zoom'], 13, 1.6, 16, 4, 18, 9];
const TRANSIT_BLUR = ['interpolate', ['linear'], ['zoom'], 13, 1.5, 18, 6];
const slotAt = (px) => ['*', ['get', 'slot'], px];
const SLOT_OFFSET = ['interpolate', ['exponential', 1.6], ['zoom'],
  13, slotAt(1.1), 16, slotAt(2.2), 18, slotAt(3.8)];

/**
 * The letter a parking lot is known by, for its badge: "Lot A" -> A, "Parking Lot R" -> R, "PV Lot" -> PV,
 * "Merten Hall Lot" -> MH, "Roberts Lot" -> RO. Anything longer is cut to two letters, which is all that fits.
 */
export function parkingTag(name) {
  const words = String(name || '').split(/[^A-Za-z0-9]+/)
    .filter((w) => w && !/^(lot|parking|for|and|the|of|deck|garage)$/i.test(w));
  if (!words.length) return 'P';
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

const POINT_LAYERS = { transit: ['transit-glow', 'transit-line', 'stops', 'stop-names'], food: ['food', 'food-names', 'food-group', 'food-group-count'] };
const FOOD_SPLIT_ZOOM = 18.3; // a building with several spots shows one icon until you zoom in this far

export class OutdoorMap {
  constructor(container, campus, { campusId, data, onBuildingClick, onBuildingOpen, onAreaClick, onMapClick, onStopClick, onFoodClick, stopNote } = {}) {
    const base = new URL(data, location.href).href.replace(/\/$/, ''); // MapLibre wants absolute URLs
    this.campus = campus;
    this.enabled = new Set(CATEGORIES.map((c) => c.id));
    const fc = {
      type: 'FeatureCollection',
      features: campus.buildings.map((b, i) => ({
        type: 'Feature', id: i,
        properties: { i, name: b.name || '', h: b.h, indoor: b.indoor ? 1 : 0, cat: b.cat },
        geometry: { type: 'Polygon', coordinates: [b.ring, ...b.holes] },
      })),
    };
    const areas = {
      type: 'FeatureCollection',
      features: (campus.areas || []).map((a, i) => ({
        type: 'Feature', id: i, properties: { i, name: a.name, cat: a.cat },
        geometry: { type: 'Polygon', coordinates: [a.ring, ...a.holes] },
      })),
    };
    this.buildingsFC = fc;
    const center = centroid(campus.boundary);

    this.map = new maplibregl.Map({
      container,
      center,
      zoom: 16.2,
      pitch: 58,
      bearing: -28,
      maxPitch: 75,
      minZoom: 12,
      maxBounds: campus.bounds ? [[campus.bounds[0], campus.bounds[1]], [campus.bounds[2], campus.bounds[3]]] : undefined,
      attributionControl: { compact: true },
      style: {
        version: 8,
        // fonts and tiles are served by our own engine (downloaded once for the campus area)
        glyphs: `${base}/fonts/{fontstack}/{range}.pbf`,
        light: { anchor: 'viewport', color: MAP.lightColor, intensity: MAP.lightIntensity, position: [1.3, 200, 35] },
        sky: { 'sky-color': MAP.sky, 'horizon-color': MAP.horizon, 'fog-color': MAP.sky, 'sky-horizon-blend': 0.6, 'horizon-fog-blend': 0.7, 'fog-ground-blend': 0.85, 'atmosphere-blend': 0 },
        sources: {
          // vector basemap: we style every layer ourselves, so the world outside campus stays quiet and flat
          omt: { type: 'vector', tiles: [`${base}/tiles/${campusId}/{z}/{x}/{y}.pbf`], minzoom: 10, maxzoom: 14,
            bounds: campus.bounds, attribution: '© OpenMapTiles · © OpenStreetMap contributors' },
          campus: { type: 'geojson', data: { type: 'Feature', geometry: { type: 'Polygon', coordinates: [campus.boundary] } } },
          buildings: { type: 'geojson', data: fc },
          areas: { type: 'geojson', data: areas },
          labels: { type: 'geojson', data: labelPoints(campus) },
          route: { type: 'geojson', data: empty() },
          points: { type: 'geojson', data: empty() },
          focus: { type: 'geojson', data: empty() },
          transitLines: { type: 'geojson', data: transitLines(campus) },
          stops: { type: 'geojson', data: stopPoints(campus) },
          food: { type: 'geojson', data: foodPoints(campus) },
          foodGroups: { type: 'geojson', data: foodGroups(campus) },
          car: { type: 'geojson', data: empty() },
        },
        layers: [
          ...basemapLayers(),
          { id: 'campus-fill', type: 'fill', source: 'campus', paint: { 'fill-color': ACCENT, 'fill-opacity': 0.035 } },
          { id: 'campus-line', type: 'line', source: 'campus', paint: { 'line-color': ACCENT, 'line-width': 1.2, 'line-opacity': 0.4, 'line-dasharray': [2, 3] } },
          // flat areas: parking lots and sports fields, tinted by category
          { id: 'area-fill', type: 'fill', source: 'areas', paint: { 'fill-color': this.catColor(NEUTRAL), 'fill-opacity': this.areaOpacity() } },
          { id: 'area-glow', type: 'line', source: 'areas', paint: { 'line-color': this.catColor(NEUTRAL), 'line-width': 5, 'line-blur': 4, 'line-opacity': this.areaLineOpacity(0.35) } },
          { id: 'area-edge', type: 'line', source: 'areas', paint: { 'line-color': this.catColor(NEUTRAL), 'line-width': 1.2, 'line-opacity': this.areaLineOpacity(0.9) } },
          // bus and shuttle routes, in each line's own color
          // Bus routes run side by side along the same roads. line-offset is in screen pixels, so a fixed
          // offset slides the lines off the road as you zoom: SLOT_OFFSET grows with the roads instead, and the
          // glow carries the same offset so it sits under its own line rather than on the centreline.
          { id: 'transit-glow', type: 'line', source: 'transitLines', layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': ['get', 'colour'], 'line-width': TRANSIT_GLOW_W, 'line-blur': TRANSIT_BLUR,
              'line-opacity': 0.25, 'line-offset': SLOT_OFFSET } },
          { id: 'transit-line', type: 'line', source: 'transitLines', layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': ['get', 'colour'], 'line-width': TRANSIT_W, 'line-opacity': 0.75,
              'line-offset': SLOT_OFFSET } },
          // glowing footprints under the 3D shells
          { id: 'bld-glow', type: 'line', source: 'buildings', paint: { 'line-color': this.catColor('#6b6f78'), 'line-width': 6, 'line-blur': 5, 'line-opacity': 0.35 } },
          { id: 'bld-edge', type: 'line', source: 'buildings', paint: { 'line-color': this.catColor('#6b6f78'), 'line-width': 1.2, 'line-opacity': 0.9 } },
          { id: 'bld-3d', type: 'fill-extrusion', source: 'buildings', paint: {
            'fill-extrusion-height': ['get', 'h'],
            'fill-extrusion-base': 0,
            'fill-extrusion-color': this.extrusionColor(),
            'fill-extrusion-opacity': 0.9,
            'fill-extrusion-vertical-gradient': true } },
          // your parked car: a small glowing 3D model at its spot (and deck level)
          { id: 'car-glow', type: 'circle', source: 'car', filter: ['==', ['get', 'part'], 'glow'],
            paint: { 'circle-color': '#f0a04a', 'circle-blur': 1, 'circle-opacity': 0.55,
              'circle-radius': ['interpolate', ['exponential', 2], ['zoom'], 14, 6, 17, 16, 20, 110] } },
          { id: 'car-pad', type: 'fill-extrusion', source: 'car', filter: ['==', ['get', 'part'], 'pad'],
            paint: { 'fill-extrusion-color': '#ff9a2e', 'fill-extrusion-base': ['get', 'base'], 'fill-extrusion-height': ['get', 'top'],
              'fill-extrusion-opacity': 0.45 } },
          { id: 'car-3d', type: 'fill-extrusion', source: 'car', filter: ['all', ['!=', ['get', 'part'], 'glow'], ['!=', ['get', 'part'], 'pad']],
            paint: { 'fill-extrusion-color': ['match', ['get', 'part'], 'body', '#ff9426', 'cabin', '#ffc47a', 'light', '#fff4e0', '#141518'],
              'fill-extrusion-base': ['get', 'base'], 'fill-extrusion-height': ['get', 'top'], 'fill-extrusion-opacity': 1,
              'fill-extrusion-vertical-gradient': false } },
          // the deck your car is in turns to glass so the car shows through (drawn after the car on purpose)
          { id: 'bld-ghost', type: 'fill-extrusion', source: 'buildings', filter: ['==', ['get', 'i'], -1],
            paint: { 'fill-extrusion-height': ['get', 'h'], 'fill-extrusion-base': 0, 'fill-extrusion-color': '#4da3ff',
              'fill-extrusion-opacity': 0.2, 'fill-extrusion-vertical-gradient': true } },
          { id: 'route-glow', type: 'line', source: 'route', layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': ACCENT, 'line-width': ['interpolate', ['linear'], ['zoom'], 15, 10, 19, 22], 'line-blur': 8, 'line-opacity': 0.5 } },
          { id: 'route', type: 'line', source: 'route', layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': '#ffd29a', 'line-width': ['interpolate', ['linear'], ['zoom'], 15, 3, 19, 6] } },
          { id: 'pts-halo', type: 'circle', source: 'points', paint: {
            'circle-radius': ['case', ['==', ['get', 'kind'], 'best'], 13, 0], 'circle-color': ACCENT, 'circle-opacity': 0.25, 'circle-blur': 0.6 } },
          { id: 'pts', type: 'circle', source: 'points', paint: {
            'circle-radius': ['case', ['==', ['get', 'kind'], 'best'], 6.5, 4.5],
            'circle-color': ['case', ['==', ['get', 'kind'], 'best'], ACCENT, '#262931'],
            'circle-stroke-color': ACCENT, 'circle-stroke-width': 2 } },
          // Markers hover above the map and bob (see floatMarkers). These are the shadows they cast, drawn at
          // the real position so the thing above them still reads as standing at that spot.
          { id: 'park-shadow', type: 'circle', source: 'labels', minzoom: 14.5, filter: ['==', ['get', 'type'], 'parking'],
            paint: { ...SHADOW, 'circle-radius': ['interpolate', ['linear'], ['zoom'], 14.5, 3, 17, 5, 19, 6.5] } },
          { id: 'stop-shadow', type: 'circle', source: 'stops',
            paint: { ...SHADOW, 'circle-radius': ['interpolate', ['linear'], ['zoom'], 13, 2, 16, 3.5, 19, 5] } },
          { id: 'food-group-shadow', type: 'circle', source: 'foodGroups', maxzoom: FOOD_SPLIT_ZOOM,
            paint: { ...SHADOW, 'circle-radius': ['interpolate', ['linear'], ['zoom'], 14, 2.5, 17, 4] } },
          { id: 'food-shadow', type: 'circle', source: 'food',
            filter: ['any', ['!', ['get', 'grouped']], ['>=', ['zoom'], FOOD_SPLIT_ZOOM]],
            paint: { ...SHADOW, 'circle-radius': ['interpolate', ['linear'], ['zoom'], 14, 2, 16, 3, 19, 4.5] } },
          // bus / shuttle stops (icons drawn in code, see addStopIcons)
          { id: 'stops', type: 'symbol', source: 'stops',
            layout: { 'icon-image': ['case', ['get', 'shuttle'], 'stop-shuttle', 'stop-bus'],
              'icon-size': ['interpolate', ['linear'], ['zoom'], 13, 0.32, 16, 0.5, 19, 0.75],
              'icon-allow-overlap': true, 'icon-ignore-placement': true, 'symbol-sort-key': ['case', ['get', 'shuttle'], 0, 1] } },
          { id: 'stop-names', type: 'symbol', source: 'stops', minzoom: 16.5,
            filter: ['any', ['get', 'shuttle'], ['>=', ['get', 'nlines'], 3]],
            layout: { 'text-field': ['get', 'short'], 'text-font': ['Noto Sans Bold'], 'text-size': 11, 'text-offset': [0, 1.6], 'text-anchor': 'top', 'text-max-width': 10 },
            paint: { 'text-color': TRANSIT, 'text-halo-color': MAP.halo, 'text-halo-width': 1.4 } },
          // food & coffee (spots that share a building are grouped until you zoom in)
          { id: 'food-group', type: 'symbol', source: 'foodGroups', maxzoom: FOOD_SPLIT_ZOOM,
            layout: { 'icon-image': 'food-meal', 'icon-size': ['interpolate', ['linear'], ['zoom'], 14, 0.36, 17, 0.55],
              'icon-allow-overlap': true, 'icon-ignore-placement': true } },
          { id: 'food-group-count', type: 'symbol', source: 'foodGroups', maxzoom: FOOD_SPLIT_ZOOM, minzoom: 15,
            layout: { 'text-field': ['to-string', ['get', 'count']], 'text-font': ['Noto Sans Bold'], 'text-size': 10,
              'text-offset': [1.1, -1.1], 'text-allow-overlap': true },
            paint: { 'text-color': '#16181d', 'text-halo-color': '#ffd1e6', 'text-halo-width': 4 } },
          { id: 'food', type: 'symbol', source: 'food',
            filter: ['any', ['!', ['get', 'grouped']], ['>=', ['zoom'], FOOD_SPLIT_ZOOM]],
            layout: { 'icon-image': ['case', ['get', 'cafe'], 'food-cafe', 'food-meal'],
              'icon-size': ['interpolate', ['linear'], ['zoom'], 14, 0.3, 16, 0.42, 19, 0.65],
              'icon-allow-overlap': true, 'icon-ignore-placement': true } },
          { id: 'food-names', type: 'symbol', source: 'food', minzoom: 17.2,
            filter: ['any', ['!', ['get', 'grouped']], ['>=', ['zoom'], FOOD_SPLIT_ZOOM]],
            layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Bold'], 'text-size': 11, 'text-offset': [0, 1.4], 'text-anchor': 'top', 'text-padding': 2 },
            paint: { 'text-color': FOOD, 'text-halo-color': MAP.halo, 'text-halo-width': 1.4 } },
          // the step you tapped in the directions
          { id: 'focus-halo', type: 'circle', source: 'focus', paint: { 'circle-radius': 18, 'circle-color': '#ffd29a', 'circle-opacity': 0.25, 'circle-blur': 0.5 } },
          { id: 'focus', type: 'circle', source: 'focus', paint: { 'circle-radius': 6, 'circle-color': '#ffffff', 'circle-stroke-color': ACCENT, 'circle-stroke-width': 3 } },
          // names fade in as you zoom: big buildings first, lots and small buildings when you're close
          { id: 'bld-names', type: 'symbol', source: 'labels', minzoom: 16, filter: ['==', ['get', 'type'], 'building'],
            layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Bold'], 'text-size': ['interpolate', ['linear'], ['zoom'], 16, 10.5, 19, 13.5],
              'text-max-width': 8, 'text-padding': 4, 'symbol-sort-key': ['-', 0, ['get', 'size']], 'text-variable-anchor': ['center', 'top', 'bottom'] },
            paint: { 'text-color': MAP.bldgLabel, 'text-halo-color': MAP.halo, 'text-halo-width': 1.4,
              'text-opacity': ['interpolate', ['linear'], ['zoom'], 16, ['case', ['>', ['get', 'size'], 2500], 1, 0], 17, 1] } },
          // Parking lots carry a badge with the letter they are signed by, so you can pick one out without
          // zooming in far enough for the full name.
          { id: 'park-badge', type: 'circle', source: 'labels', minzoom: 14.5, filter: ['==', ['get', 'type'], 'parking'],
            paint: {
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 14.5, 7, 17, 12, 19, 15],
              'circle-color': PARK_COLOR, 'circle-stroke-width': 1.6, 'circle-stroke-color': MAP.halo,
              'circle-opacity': ['interpolate', ['linear'], ['zoom'], 14.5, 0, 15.2, 0.92],
              'circle-stroke-opacity': ['interpolate', ['linear'], ['zoom'], 14.5, 0, 15.2, 1],
            } },
          { id: 'park-letter', type: 'symbol', source: 'labels', minzoom: 14.5, filter: ['==', ['get', 'type'], 'parking'],
            layout: {
              'text-field': ['get', 'tag'], 'text-font': ['Noto Sans Bold'], 'text-allow-overlap': true,
              'text-size': ['interpolate', ['linear'], ['zoom'], 14.5, 9, 17, 13, 19, 16],
            },
            paint: { 'text-color': '#ffffff', 'text-opacity': ['interpolate', ['linear'], ['zoom'], 14.5, 0, 15.2, 1] } },
          { id: 'area-names', type: 'symbol', source: 'labels', minzoom: 17, filter: ['==', ['get', 'type'], 'area'],
            layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Regular'], 'text-size': 11, 'text-padding': 4,
              'text-offset': [0, 1.5], 'text-anchor': 'top' },
            paint: { 'text-color': this.catColor(MAP.label), 'text-halo-color': MAP.halo, 'text-halo-width': 1.3,
              'text-opacity': ['interpolate', ['linear'], ['zoom'], 17, 0, 17.6, 1] } },
        ],
      },
    });
    this.map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-left');
    const el = document.createElement('div');
    el.className = 'me-dot';
    el.innerHTML = '<b class="me-heading" hidden></b><i></i>'; // heading pointer + diamond; MapLibre moves the element itself
    this.me = new maplibregl.Marker({ element: el });
    this.heading = null;
    this.map.on('rotate', () => this.drawHeading());
    // navigation: the camera follows you until you move the map yourself
    for (const ev of ['dragstart', 'rotatestart', 'pitchstart', 'zoomstart']) {
      this.map.on(ev, (e) => { if (e.originalEvent && this.following) { this.following = false; this.onFollowLost?.(); } });
    }
    this.popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12, className: 'bld-popup' });

    this.hoverId = null;
    for (const layer of ['bld-3d', 'bld-ghost']) {
      this.map.on('mousemove', layer, (e) => {
        const f = e.features[0];
        this.setHover(f.id);
        this.map.getCanvas().style.cursor = 'pointer';
        const b = campus.buildings[f.id];
        this.popup.setLngLat(e.lngLat).setHTML(`<b>${b.name || 'Building'}</b>${b.indoor ? '<small>3D indoor map available</small>' : ''}`).addTo(this.map);
      });
      this.map.on('mouseleave', layer, () => { this.setHover(null); this.map.getCanvas().style.cursor = ''; this.popup.remove(); });
    }
    this.map.on('mousemove', 'area-fill', (e) => {
      if (this.hoverId !== null) return; // a building is on top
      const f = e.features[0];
      if (!this.enabled.has(f.properties.cat)) return;
      const label = CATEGORIES.find((c) => c.id === f.properties.cat)?.label;
      this.popup.setLngLat(e.lngLat).setHTML(`<b>${f.properties.name}</b><small>${label}</small>`).addTo(this.map);
    });
    this.map.on('mouseleave', 'area-fill', () => { if (this.hoverId === null) this.popup.remove(); });
    for (const layer of ['park-badge', 'park-letter']) {
      this.map.on('mouseenter', layer, () => { this.map.getCanvas().style.cursor = 'pointer'; });
      this.map.on('mouseleave', layer, () => { this.map.getCanvas().style.cursor = ''; });
    }
    this.map.on('styleimagemissing', (e) => { addStopIcons(this.map, e.id); addFoodIcons(this.map, e.id); });

    // food: hover for a quick look, click for a card with "Go here"
    const foodHtml = (f, full) => `<b>${f.name}</b>
      <small>${[f.kind, f.cuisine].filter(Boolean).join(' · ')}</small>
      ${f.building ? `<small>In ${f.building}${f.level !== null && f.level !== undefined ? `, ${f.level === 0 ? 'Ground floor' : `Floor ${f.level}`}` : ''}</small>` : ''}
      ${full && f.hours ? `<small class="hours">${f.hours.replace(/;\s*/g, '<br>')}</small>` : ''}
      ${full ? '<button class="btn primary sm walk-here">Go here</button>' : ''}`;
    this.map.on('mousemove', 'food', (e) => {
      if (this.stopPopup.isOpen()) return;
      this.map.getCanvas().style.cursor = 'pointer';
      const f = campus.food[e.features[0].properties.i];
      this.popup.setLngLat([f.lon, f.lat]).setHTML(foodHtml(f, false)).addTo(this.map);
    });
    this.map.on('mouseleave', 'food', () => { this.map.getCanvas().style.cursor = ''; this.popup.remove(); });
    this.map.on('mousemove', 'food-group', (e) => {
      const g = e.features[0].properties;
      this.map.getCanvas().style.cursor = 'zoom-in';
      this.popup.setLngLat(e.features[0].geometry.coordinates)
        .setHTML(`<b>${g.building}</b><small>${JSON.parse(g.names).join(' · ')}</small>`).addTo(this.map);
    });
    this.map.on('mouseleave', 'food-group', () => { this.map.getCanvas().style.cursor = ''; this.popup.remove(); });
    this.map.on('click', 'food-group', (e) => {
      this.popup.remove();
      this.map.easeTo({ center: e.features[0].geometry.coordinates, zoom: FOOD_SPLIT_ZOOM + 0.4, duration: 800 });
      this.stopClicked = true;
    });
    this.map.on('click', 'food', (e) => {
      const f = campus.food[e.features[0].properties.i];
      this.popup.remove();
      this.stopPopup.setLngLat([f.lon, f.lat]).setHTML(foodHtml(f, true)).addTo(this.map);
      this.stopPopup.getElement().querySelector('.walk-here').onclick = () => { this.stopPopup.remove(); onFoodClick?.(f); };
      this.stopClicked = true;
    });

    // stops: hover shows the lines; click opens a card with "Walk here"
    this.stopPopup = new maplibregl.Popup({ closeButton: true, closeOnClick: true, offset: 16, className: 'bld-popup stop-popup', maxWidth: '280px' });
    const stopHtml = (s, full) => {
      const lines = s.lines.map((ref) => {
        const l = campus.transit.lines[ref];
        return `<span class="line-chip" style="--lc:${l?.colour || TRANSIT}">${l?.name || ref}</span>`;
      }).join('');
      const nets = s.networks.filter((n) => !s.lines.length || n === 'Mason Shuttles' || n === 'Fairfax Connector');
      return `<b>${s.name}</b>${lines ? `<div class="chips-row">${lines}</div>` : ''}
        ${nets.length ? `<small>${nets.join(' · ')}</small>` : ''}
        ${stopNote?.(s) ? `<small class="next-bus">${stopNote(s)}</small>` : ''}
        ${full ? `<small>${[s.shelter && 'Shelter', s.bays > 1 && `${s.bays} bays`].filter(Boolean).join(' · ')}</small>
        <button class="btn primary sm walk-here">${stopNote?.(s) ? 'Bus times & walk here' : 'Walk here'}</button>` : ''}`;
    };
    this.map.on('mousemove', 'stops', (e) => {
      if (this.stopPopup.isOpen()) return;
      this.map.getCanvas().style.cursor = 'pointer';
      const s = campus.transit.stops[e.features[0].properties.i];
      this.popup.setLngLat([s.lon, s.lat]).setHTML(stopHtml(s, false)).addTo(this.map);
    });
    this.map.on('mouseleave', 'stops', () => { this.map.getCanvas().style.cursor = ''; this.popup.remove(); });
    this.map.on('click', 'stops', (e) => {
      const s = campus.transit.stops[e.features[0].properties.i];
      this.popup.remove();
      this.stopPopup.setLngLat([s.lon, s.lat]).setHTML(stopHtml(s, true)).addTo(this.map);
      this.stopPopup.getElement().querySelector('.walk-here').onclick = () => { this.stopPopup.remove(); onStopClick?.(s); };
      this.stopClicked = true;
    });
    this.buildFilterBar(container);
    // One tap picks a building (directions to it); two taps open its inside. The single-tap action waits
    // out the double-tap window, so one gesture never fires both. Taps on anything else act at once.
    // The second tap is spotted here rather than through the map's `dblclick`, which a phone does not reliably
    // fire. While a building's tap is pending, the map's own double-tap zoom is switched off so the two
    // gestures cannot both happen; it goes straight back on afterwards.
    this.tapTimer = null;
    this.lastTap = { id: null, at: 0, x: 0, y: 0 };
    const endTap = () => {
      clearTimeout(this.tapTimer);
      this.tapTimer = null;
      this.map.doubleClickZoom.enable();
    };
    this.map.on('click', (e) => {
      if (this.stopClicked) { this.stopClicked = false; return; } // a stop handled this tap
      const f = this.map.queryRenderedFeatures(e.point, { layers: ['bld-3d', 'bld-ghost'] })[0];
      const bld = f ? campus.buildings[f.id] : null;
      const fallthrough = () => onMapClick?.([e.lngLat.lat, e.lngLat.lng], bld);
      if (bld && onBuildingClick) {
        const now = performance.now();
        const again = this.lastTap.id === f.id && now - this.lastTap.at < 400
          && Math.hypot(e.point.x - this.lastTap.x, e.point.y - this.lastTap.y) < 30;
        this.lastTap = { id: f.id, at: now, x: e.point.x, y: e.point.y };
        if (again && onBuildingOpen) {
          endTap();
          this.lastTap.id = null; // a third tap starts over
          onBuildingOpen(bld);
          return;
        }
        clearTimeout(this.tapTimer);
        this.map.doubleClickZoom.disable();
        this.tapTimer = setTimeout(() => {
          endTap();
          // the handler returns false to let the tap through (demo mode: tap anywhere to set your start)
          if (onBuildingClick(bld) === false) fallthrough();
        }, 300);
        return;
      }
      const lot = onAreaClick && this.map.queryRenderedFeatures(e.point, { layers: ['park-badge', 'park-letter', 'area-fill'] })
        .find((x) => x.properties.cat === 'parking' && x.properties.i !== undefined);
      if (lot && onAreaClick(campus.areas[lot.properties.i]) !== false) return;
      fallthrough();
    });
    // a mouse still sends dblclick, and stopping it here keeps the map from zooming under the open building
    this.map.on('dblclick', (e) => {
      if (this.map.queryRenderedFeatures(e.point, { layers: ['bld-3d', 'bld-ghost'] })[0]) e.preventDefault();
    });
    this.ready = new Promise((r) => this.map.on('load', r));
    this.ready.then(() => this.floatMarkers());
  }

  // ----- color filters -----
  // category -> its color when enabled, otherwise the fallback
  catColor(fallback) {
    const m = ['match', ['get', 'cat']];
    for (const c of CATEGORIES) m.push(c.id, this.enabled.has(c.id) ? c.color : fallback);
    m.push(fallback);
    return m;
  }
  extrusionColor() {
    return ['case',
      ['boolean', ['feature-state', 'selected'], false], '#ffe6c4',
      ['boolean', ['feature-state', 'hover'], false], '#d8dbe2',
      this.catColor(NEUTRAL)];
  }
  areaOpacity() {
    // parking is the highlight: a stronger fill than fields
    const m = ['match', ['get', 'cat']];
    for (const c of CATEGORIES) m.push(c.id, this.enabled.has(c.id) ? (c.id === 'parking' ? 0.45 : 0.3) : 0.06);
    m.push(0.06);
    return m;
  }
  areaLineOpacity(on) {
    const m = ['match', ['get', 'cat']];
    for (const c of CATEGORIES) m.push(c.id, this.enabled.has(c.id) ? on : 0.12);
    m.push(0.12);
    return m;
  }
  applyFilters() {
    const set = (layer, prop, v) => this.map.getLayer(layer) && this.map.setPaintProperty(layer, prop, v);
    set('area-fill', 'fill-color', this.catColor(NEUTRAL));
    set('area-fill', 'fill-opacity', this.areaOpacity());
    set('area-glow', 'line-color', this.catColor(NEUTRAL));
    set('area-glow', 'line-opacity', this.areaLineOpacity(0.35));
    set('area-edge', 'line-color', this.catColor(NEUTRAL));
    set('area-edge', 'line-opacity', this.areaLineOpacity(0.9));
    set('bld-glow', 'line-color', this.catColor('#6b6f78'));
    set('bld-edge', 'line-color', this.catColor('#6b6f78'));
    set('bld-3d', 'fill-extrusion-color', this.extrusionColor());
    set('area-names', 'text-color', this.catColor(MAP.label));
    for (const [cat, ids] of Object.entries(POINT_LAYERS)) {
      for (const id of ids) if (this.map.getLayer(id)) this.map.setLayoutProperty(id, 'visibility', this.enabled.has(cat) ? 'visible' : 'none');
    }
  }
  buildFilterBar(container) {
    const bar = document.createElement('div');
    bar.className = 'cat-filter';
    // collapsible so it doesn't cover the map on phones; remembers your choice on this device
    const KEY = 'akadian:layers-open';
    let open;
    try { open = localStorage.getItem(KEY); } catch {}
    open = open === null || open === undefined ? innerWidth >= 700 : open === '1';
    bar.classList.toggle('collapsed', !open);
    const toggle = document.createElement('button');
    toggle.className = 'layers-toggle';
    toggle.setAttribute('aria-expanded', open);
    toggle.innerHTML = '<span>Layers</span><span class="chev" aria-hidden="true">▾</span>';
    toggle.onclick = () => {
      const now = bar.classList.toggle('collapsed');
      toggle.setAttribute('aria-expanded', !now);
      try { localStorage.setItem(KEY, now ? '0' : '1'); } catch {}
    };
    bar.append(toggle);
    for (const c of CATEGORIES) {
      const btn = document.createElement('button');
      btn.className = 'on';
      btn.style.setProperty('--c', c.color);
      btn.innerHTML = `<i></i>${c.label}`;
      btn.title = `Show ${c.label.toLowerCase()} in color`;
      btn.setAttribute('aria-pressed', 'true');
      btn.onclick = () => {
        this.enabled.has(c.id) ? this.enabled.delete(c.id) : this.enabled.add(c.id);
        btn.classList.toggle('on', this.enabled.has(c.id));
        btn.setAttribute('aria-pressed', this.enabled.has(c.id));
        this.applyFilters();
      };
      bar.append(btn);
    }
    container.append(bar);
  }

  setHover(id) {
    if (this.hoverId !== null) this.map.setFeatureState({ source: 'buildings', id: this.hoverId }, { hover: false });
    this.hoverId = id;
    if (id !== null) this.map.setFeatureState({ source: 'buildings', id }, { hover: true });
  }

  select(building) {
    if (this.selectedId !== undefined) this.map.setFeatureState({ source: 'buildings', id: this.selectedId }, { selected: false });
    this.selectedId = building ? this.campus.buildings.indexOf(building) : undefined;
    if (this.selectedId !== undefined && this.selectedId >= 0) this.map.setFeatureState({ source: 'buildings', id: this.selectedId }, { selected: true });
  }

  // your saved parking spot (stored on the device by the app), drawn as a small 3D car
  setCar(spot, { heading = 0, onClick } = {}) {
    this.map.getSource('car')?.setData(spot ? carModel(spot, heading) : empty());
    this.onCarClick = onClick;
    // which deck (if any) holds the car: draw it as glass instead of solid
    const deck = spot?.deck ? this.campus.buildings.findIndex((b) => b.cat === 'parking' && b.name === spot.lot) : -1;
    if (this.map.getLayer('bld-ghost')) {
      this.map.setFilter('bld-3d', ['!=', ['get', 'i'], deck]);
      this.map.setFilter('bld-ghost', ['==', ['get', 'i'], deck]);
    }
    if (!this.carHooked) {
      this.carHooked = true;
      this.map.on('click', 'car-3d', () => { this.stopClicked = true; this.onCarClick?.(); });
      this.map.on('mouseenter', 'car-3d', () => (this.map.getCanvas().style.cursor = 'pointer'));
      this.map.on('mouseleave', 'car-3d', () => (this.map.getCanvas().style.cursor = ''));
    }
  }

  setUser(ll) { // null hides you
    if (!ll) return void this.me.remove();
    this.me.setLngLat([ll[1], ll[0]]).addTo(this.map);
  }

  // points: [{lat, lon, kind: 'best'|'entrance'}]
  setPoints(points) {
    this.map.getSource('points')?.setData({
      type: 'FeatureCollection',
      features: points.map((p) => ({ type: 'Feature', properties: { kind: p.kind }, geometry: { type: 'Point', coordinates: [p.lon, p.lat] } })),
    });
  }

  // one bus line stands out (its timetable is open); null shows them all evenly again
  focusLine(ref) {
    if (!this.map.isStyleLoaded() || !this.map.getLayer('transit-line')) return; // the next render after ready applies it
    const on = (a, b) => (ref ? ['case', ['==', ['get', 'ref'], ref], a, b] : a);
    this.map.setPaintProperty('transit-line', 'line-opacity', on(1, 0.12));
    this.map.setPaintProperty('transit-glow', 'line-opacity', on(0.55, 0.05));
    this.map.setPaintProperty('transit-line', 'line-width', ref ? TRANSIT_W_FOCUS : TRANSIT_W);
  }

  /**
   * Lift the markers off the map and let them bob, with their shadows tightening underneath, so a stop or a
   * lot reads as an object standing at that spot rather than a sticker painted on it. The three families bob
   * out of step with each other. Reduced motion gets the lift and the shadow but no movement.
   */
  floatMarkers() {
    const anchor = (id, prop) => this.map.getLayer(id) && this.map.setPaintProperty(id, `${prop}-anchor`, 'viewport');
    for (const [id, prop] of FLOATERS) anchor(id, prop);

    const still = matchMedia('(prefers-reduced-motion: reduce)');
    const LIFT = 9, BOB = 3.4;
    const place = (now) => {
      for (const [id, prop, phase, isShadow] of FLOATERS) {
        if (!this.map.getLayer(id)) continue;
        const rise = LIFT + (still.matches ? 0 : BOB * Math.sin(now / 620 + phase));
        if (isShadow) {
          // the shadow stays on the ground and only shrinks away as the marker climbs
          this.map.setPaintProperty(id, 'circle-opacity', 0.26 - 0.1 * ((rise - LIFT + BOB) / (2 * BOB || 1)));
        } else {
          this.map.setPaintProperty(id, prop, [0, -rise]);
        }
      }
    };
    place(0);
    if (still.matches) return;
    let last = 0;
    const tick = (now) => {
      this.floatRaf = requestAnimationFrame(tick);
      if (document.hidden || now - last < 33) return; // ~30fps: it is a slow bob, not an animation reel
      last = now;
      place(now);
    };
    this.floatRaf = requestAnimationFrame(tick);
  }

  /** Repaint the accent-coloured layers after the accent changes (no reload needed). */
  setAccent(hex) {
    if (!this.map.isStyleLoaded()) return;
    const set = (layer, prop, v) => this.map.getLayer(layer) && this.map.setPaintProperty(layer, prop, v);
    set('campus-fill', 'fill-color', hex);
    set('campus-line', 'line-color', hex);
    set('route-glow', 'line-color', hex);
    set('focus-halo', 'circle-color', hex);
  }

  setRoute(lls) {
    this.map.getSource('route')?.setData(lls ? { type: 'Feature', geometry: { type: 'LineString', coordinates: lls.map(([a, b]) => [b, a]) } } : empty());
  }

  // Which way you're facing (degrees from north), drawn as a pointer on your marker; null hides it.
  setHeading(deg) {
    this.heading = deg;
    this.drawHeading();
  }
  drawHeading() {
    const b = this.me.getElement().querySelector('.me-heading');
    b.hidden = this.heading == null;
    if (this.heading != null) b.style.transform = `rotate(${this.heading - this.map.getBearing()}deg)`;
  }

  // Navigation camera: close, tilted, facing `bearing`, with you low on the screen (padding keeps the banner clear).
  follow([lat, lon], bearing, { padding, instant = false } = {}) {
    this.following = true;
    this.map.easeTo({ center: [lon, lat], bearing: bearing ?? this.map.getBearing(), pitch: 60, zoom: 18.6,
      padding: padding || { top: 0, bottom: 0, left: 0, right: 0 }, duration: instant || REDUCED() ? 0 : 900 });
  }
  stopFollowing() {
    this.following = false;
    this.map.easeTo({ padding: { top: 0, bottom: 0, left: 0, right: 0 }, duration: 0 });
  }

  // The parts of the map covered by the search bar and the card (px per side): routes and places are framed in the rest.
  setInset(inset) { this.inset = inset; }
  pad(extra = 0) {
    const i = this.inset || { top: 0, bottom: 0, left: 0, right: 0 };
    const c = this.map.getContainer();
    // never pad more than the map has room for (fitBounds refuses)
    const v = Math.max(0, Math.min(i.top + i.bottom + 2 * extra, c.clientHeight - 80) - 2 * extra);
    const k = i.top + i.bottom ? v / (i.top + i.bottom) : 0;
    const h = Math.max(0, Math.min(i.left + i.right + 2 * extra, c.clientWidth - 80) - 2 * extra);
    const kh = i.left + i.right ? h / (i.left + i.right) : 0;
    return { top: extra + i.top * k, bottom: extra + i.bottom * k, left: extra + i.left * kh, right: extra + i.right * kh };
  }

  center([lat, lon]) {
    this.map.easeTo({ center: [lon, lat], zoom: Math.max(this.map.getZoom(), 17.3), padding: this.pad(), duration: 700 });
  }

  // fly to one step of the walking directions (null clears the marker)
  focus(ll) {
    this.map.getSource('focus')?.setData(ll ? { type: 'Feature', geometry: { type: 'Point', coordinates: [ll[1], ll[0]] } } : empty());
    if (ll) this.map.easeTo({ center: [ll[1], ll[0]], zoom: 18.2, padding: this.pad(), duration: 900 });
  }

  fit(lls) {
    const b = new maplibregl.LngLatBounds();
    for (const [lat, lon] of lls) b.extend([lon, lat]);
    this.following = false;
    const c = this.map.getContainer();
    const extra = Math.min(60, c.clientWidth / 8, c.clientHeight / 8);
    this.map.fitBounds(b, { padding: this.pad(extra), maxZoom: 17.5, pitch: 58, bearing: -28, duration: REDUCED() ? 0 : 1200 });
  }

  resize() { this.map.resize(); }
}

function empty() { return { type: 'FeatureCollection', features: [] }; }
const REDUCED = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// A low-poly car as extruded boxes: body, cabin, wheels, lights. Same proportions as the 3D building view.
const CAR_SCALE = 1.3, DECK_LEVEL_M = 3.8;
function carModel(spot, heading) {
  const s = CAR_SCALE;
  const base = spot.deck && spot.level ? (Number(spot.level) - 1) * DECK_LEVEL_M + 0.3 : 0;
  const a = (heading * Math.PI) / 180, ca = Math.cos(a), sa = Math.sin(a);
  const kx = 111320 * Math.cos((spot.lat * Math.PI) / 180), ky = 110540;
  // box in car coordinates (x forward, y left), metres -> lon/lat ring
  const box = (x0, x1, y0, y1) => {
    const pts = [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]].map(([x, y]) => {
      const e = (x * ca - y * sa) * s, n = (x * sa + y * ca) * s;
      return [spot.lon + e / kx, spot.lat + n / ky];
    });
    return { type: 'Polygon', coordinates: [pts] };
  };
  const part = (name, geom, b, t) => ({ type: 'Feature', properties: { part: name, base: base + b * s, top: base + t * s }, geometry: geom });
  const f = [
    part('body', box(-2.2, 2.2, -0.9, 0.9), 0.34, 1.06),
    part('cabin', box(-1.5, 0.9, -0.78, 0.78), 1.06, 1.68),
    part('light', box(2.12, 2.22, -0.8, -0.4), 0.74, 0.9),
    part('light', box(2.12, 2.22, 0.4, 0.8), 0.74, 0.9),
  ];
  for (const [x, y] of [[1.35, 0.86], [1.35, -0.86], [-1.35, 0.86], [-1.35, -0.86]]) {
    f.push(part('wheel', box(x - 0.36, x + 0.36, y - 0.13, y + 0.13), 0, 0.72));
  }
  // a thin glowing pad on the car's own level (the ground glow can't reach up into a deck)
  f.push(part('pad', box(-3.6, 3.6, -2.4, 2.4), 0, 0.04));
  f.push({ type: 'Feature', properties: { part: 'glow' }, geometry: { type: 'Point', coordinates: [spot.lon, spot.lat] } });
  return { type: 'FeatureCollection', features: f };
}

// Lines sharing a street are nudged apart a little so each color stays visible.
function transitLines(campus) {
  const lines = Object.entries(campus.transit?.lines || {});
  return {
    type: 'FeatureCollection',
    features: lines.map(([ref, l], i) => ({
      type: 'Feature', properties: { ref, name: l.name, colour: l.colour, slot: i - (lines.length - 1) / 2 },
      geometry: { type: 'MultiLineString', coordinates: l.paths },
    })),
  };
}

function stopPoints(campus) {
  return {
    type: 'FeatureCollection',
    features: (campus.transit?.stops || []).map((s, i) => ({
      type: 'Feature',
      properties: { i, shuttle: s.shuttle, nlines: s.lines.length, short: s.shuttle ? s.name.split(' (')[0] : s.lines.join(' · ') },
      geometry: { type: 'Point', coordinates: [s.lon, s.lat] },
    })),
  };
}

const groupedBuildings = (campus) => {
  const n = {};
  for (const f of campus.food || []) if (f.building) n[f.building] = (n[f.building] || 0) + 1;
  return new Set(Object.keys(n).filter((b) => n[b] >= 3));
};

function foodPoints(campus) {
  const grouped = groupedBuildings(campus);
  return {
    type: 'FeatureCollection',
    features: (campus.food || []).map((f, i) => ({
      type: 'Feature', properties: { i, name: f.name, cafe: /café|coffee/i.test(`${f.kind} ${f.cuisine}`), grouped: grouped.has(f.building) },
      geometry: { type: 'Point', coordinates: [f.lon, f.lat] },
    })),
  };
}

function foodGroups(campus) {
  const features = [];
  for (const b of groupedBuildings(campus)) {
    const spots = campus.food.filter((f) => f.building === b);
    const lon = spots.reduce((s, f) => s + f.lon, 0) / spots.length, lat = spots.reduce((s, f) => s + f.lat, 0) / spots.length;
    features.push({ type: 'Feature', properties: { building: b, count: spots.length, names: JSON.stringify(spots.map((f) => f.name)) },
      geometry: { type: 'Point', coordinates: [lon, lat] } });
  }
  return { type: 'FeatureCollection', features };
}

// Fork & knife / coffee cup pictograms, drawn on a canvas like the bus icon.
function addFoodIcons(map, id) {
  if (id !== 'food-meal' && id !== 'food-cafe') return;
  const S = 64, c = document.createElement('canvas');
  c.width = c.height = S;
  const g = c.getContext('2d');
  g.beginPath(); g.arc(S / 2, S / 2, S / 2 - 3, 0, Math.PI * 2);
  g.fillStyle = FOOD; g.fill();
  g.lineWidth = 4; g.strokeStyle = MAP.halo; g.stroke();
  g.fillStyle = g.strokeStyle = '#3a0f22';
  g.lineCap = 'round';
  if (id === 'food-meal') {
    g.lineWidth = 3.5; // fork: three tines and a handle
    for (const x of [19, 24, 29]) { g.beginPath(); g.moveTo(x, 16); g.lineTo(x, 27); g.stroke(); }
    g.beginPath(); g.moveTo(19, 27); g.quadraticCurveTo(24, 33, 29, 27); g.stroke();
    g.beginPath(); g.moveTo(24, 30); g.lineTo(24, 48); g.stroke();
    g.beginPath(); g.moveTo(40, 48); g.lineTo(40, 16); g.quadraticCurveTo(47, 22, 45, 34); g.lineTo(40, 34); g.stroke(); // knife
  } else {
    roundRect(g, 18, 22, 22, 22, 5); g.fill(); // cup
    g.lineWidth = 3.5; g.beginPath(); g.arc(42, 32, 5, -Math.PI / 2, Math.PI / 2); g.stroke(); // handle
    g.lineWidth = 2.5; for (const x of [24, 31]) { g.beginPath(); g.moveTo(x, 18); g.quadraticCurveTo(x + 3, 14, x, 10); g.stroke(); } // steam
  }
  map.addImage(id, g.getImageData(0, 0, S, S), { pixelRatio: 1 });
}

// Bus pictogram drawn on a canvas: no icon files or sprite sheet to host.
function addStopIcons(map, id) {
  if (id !== 'stop-bus' && id !== 'stop-shuttle') return;
  const S = 64, c = document.createElement('canvas');
  c.width = c.height = S;
  const g = c.getContext('2d');
  g.beginPath(); g.arc(S / 2, S / 2, S / 2 - 3, 0, Math.PI * 2);
  g.fillStyle = TRANSIT; g.fill();
  g.lineWidth = 4; g.strokeStyle = id === 'stop-shuttle' ? ACCENT : MAP.halo; g.stroke();
  // bus body, windscreen, wheels
  g.fillStyle = '#10302c';
  roundRect(g, 18, 15, 28, 30, 6); g.fill();
  g.fillStyle = '#e8fffb';
  roundRect(g, 22, 20, 20, 10, 2); g.fill();
  g.fillRect(22, 36, 5, 3); g.fillRect(37, 36, 5, 3);
  g.fillStyle = '#10302c';
  g.fillRect(21, 45, 6, 5); g.fillRect(37, 45, 6, 5);
  map.addImage(id, g.getImageData(0, 0, S, S), { pixelRatio: 1 });
}
function roundRect(g, x, y, w, h, r) {
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
}

// Dark, label-light basemap (OpenMapTiles schema). Road names only appear at street-level zoom.
function basemapLayers() {
  const z = (stops) => ['interpolate', ['exponential', 1.6], ['zoom'], ...stops];
  const road = (id, classes, color, widths, extra = {}) => ({
    id, type: 'line', source: 'omt', 'source-layer': 'transportation',
    filter: ['all', ['in', ['get', 'class'], ['literal', classes]], ['!=', ['get', 'brunnel'], 'tunnel']],
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': color, 'line-width': z(widths), ...extra },
  });
  const name = ['coalesce', ['get', 'name:en'], ['get', 'name']];
  return [
    { id: 'bg', type: 'background', paint: { 'background-color': MAP.bg } },
    { id: 'landcover', type: 'fill', source: 'omt', 'source-layer': 'landcover',
      filter: ['in', ['get', 'class'], ['literal', ['grass', 'wood', 'farmland', 'wetland']]],
      paint: { 'fill-color': ['match', ['get', 'class'], 'wood', MAP.wood, MAP.grass], 'fill-opacity': 0.9 } },
    { id: 'park', type: 'fill', source: 'omt', 'source-layer': 'park', paint: { 'fill-color': MAP.park, 'fill-opacity': 0.8 } },
    { id: 'landuse', type: 'fill', source: 'omt', 'source-layer': 'landuse',
      filter: ['in', ['get', 'class'], ['literal', ['residential', 'commercial', 'industrial', 'retail']]],
      paint: { 'fill-color': MAP.landuse } },
    { id: 'water', type: 'fill', source: 'omt', 'source-layer': 'water', paint: { 'fill-color': MAP.water } },
    { id: 'waterway', type: 'line', source: 'omt', 'source-layer': 'waterway', paint: { 'line-color': MAP.waterway, 'line-width': 1.2 } },
    // flat buildings everywhere (the campus gets its own 3D shells on top)
    { id: 'omt-building', type: 'fill', source: 'omt', 'source-layer': 'building', minzoom: 14,
      paint: { 'fill-color': MAP.bldg, 'fill-outline-color': MAP.bldgEdge, 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 14, 0, 15.5, 1] } },
    road('paths', ['path', 'track'], MAP.path, [15, 0.5, 18, 2.2], { 'line-dasharray': [1.5, 1.5] }),
    road('minor', ['minor', 'service'], MAP.minor, [13, 0.4, 18, 7]),
    road('mid', ['tertiary', 'secondary'], MAP.mid, [10, 0.6, 18, 13]),
    road('major', ['primary', 'trunk', 'motorway'], MAP.major, [8, 0.8, 18, 18]),
    { id: 'rail', type: 'line', source: 'omt', 'source-layer': 'transportation', filter: ['==', ['get', 'class'], 'rail'],
      paint: { 'line-color': MAP.rail, 'line-width': 1, 'line-dasharray': [3, 3] } },
    // road names: only once you're zoomed in; main roads at 16, campus streets at 17, footpaths never
    ...[['road-names', ['primary', 'secondary', 'tertiary', 'trunk'], 16], ['street-names', ['minor', 'service'], 17]].map(([id, classes, zmin]) => ({
      id, type: 'symbol', source: 'omt', 'source-layer': 'transportation_name', minzoom: zmin,
      filter: ['in', ['get', 'class'], ['literal', classes]],
      layout: { 'symbol-placement': 'line', 'text-field': name, 'text-font': ['Noto Sans Regular'], 'text-size': 11, 'text-letter-spacing': 0.04 },
      paint: { 'text-color': '#7d838d', 'text-halo-color': '#15171c', 'text-halo-width': 1.2,
        'text-opacity': ['interpolate', ['linear'], ['zoom'], zmin, 0, zmin + 0.6, 1] },
    })),
    // town names only when zoomed far out
    { id: 'places', type: 'symbol', source: 'omt', 'source-layer': 'place', maxzoom: 14,
      filter: ['in', ['get', 'class'], ['literal', ['city', 'town', 'village']]],
      layout: { 'text-field': name, 'text-font': ['Noto Sans Regular'], 'text-size': 12 },
      paint: { 'text-color': '#8a909a', 'text-halo-color': '#15171c', 'text-halo-width': 1.2 } },
  ];
}

// One label point per named building / lot, at the middle of its outline.
function labelPoints(campus) {
  const mid = (ring) => {
    let x = 0, y = 0;
    for (const [lon, lat] of ring.slice(0, -1)) { x += lon; y += lat; }
    const n = Math.max(1, ring.length - 1);
    return [x / n, y / n];
  };
  const area = (ring) => {
    let a = 0;
    for (let i = 1; i < ring.length; i++) a += ring[i - 1][0] * ring[i][1] - ring[i][0] * ring[i - 1][1];
    return Math.abs(a / 2) * 111320 * 86700; // ≈ m² at this latitude
  };
  const seen = new Set();
  const features = [];
  for (const b of campus.buildings) {
    if (!b.name || seen.has(b.name)) continue;
    seen.add(b.name);
    features.push({ type: 'Feature', properties: { type: 'building', name: b.name, size: area(b.ring), cat: b.cat }, geometry: { type: 'Point', coordinates: mid(b.ring) } });
  }
  // every lot gets a lettered badge; the ones with a real name also get that name once you are zoomed in
  (campus.areas || []).forEach((a, i) => {
    if (a.cat !== 'parking') return;
    const at = { type: 'Point', coordinates: mid(a.ring) };
    features.push({ type: 'Feature', properties: { type: 'parking', i, name: a.name, tag: parkingTag(a.name), cat: a.cat }, geometry: at });
    if (a.name && a.name !== 'Parking') {
      features.push({ type: 'Feature', properties: { type: 'area', i, name: a.name, cat: a.cat }, geometry: at });
    }
  });
  return { type: 'FeatureCollection', features };
}
function centroid(ring) {
  let x = 0, y = 0;
  for (const [lon, lat] of ring) { x += lon; y += lat; }
  return [x / ring.length, y / ring.length];
}

// Nearest vertex of a building ring to a point (used as the walking target for buildings without indoor maps).
export function nearestOnRing(ring, [lat, lon]) {
  let best = ring[0], bd = Infinity;
  for (const p of ring) {
    const d = (p[0] - lon) ** 2 + (p[1] - lat) ** 2;
    if (d < bd) { bd = d; best = p; }
  }
  return [best[1], best[0]];
}

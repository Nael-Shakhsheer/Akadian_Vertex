const $ = (selector) => document.querySelector(selector);
const canvas = $('#model-canvas');
const ctx = canvas.getContext('2d');
const models = window.vertexModels;
const campusSelect = $('#campus-select');
const buildingSelect = $('#building-select');
const floorControls = $('#floor-controls');
const appURL = 'https://nael-shakhsheer.github.io/Akadian_Vertex/';
const palette = getComputedStyle(document.documentElement);
const accent = palette.getPropertyValue('--accent').trim();
const accentHover = palette.getPropertyValue('--accent-hi').trim();
const lineColor = palette.getPropertyValue('--line').trim();
// Vertex's light theme colors for building geometry.
const modelColors = {
  grid: '#d8dde5',
  fineGrid: '#e8ecf1',
  slab: '#dfe4ea',
  walk: '#f8fafc',
  room: '#e9edf2',
  shaft: '#c7ced8',
  highlight: '#fbece0'
};
const keys = Object.keys(models);
const home = { yaw: -.55, pitch: .60, zoom: 1, x: 0, y: 0 };
let camera = { ...home };
let model, selectedFloor = -1, selectedRoom = null, hover = null;
let width = 0, height = 0, pixelRatio = 1, frame = 0;
let surfaces = [];
let modelSpan, lift;
const pointers = new Map();
let gesture = null;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function chooseCampus() {
  const campus = campusSelect.value;
  buildingSelect.replaceChildren(...keys.filter(key => models[key].campus === campus)
    .map(key => new Option(models[key].name, key)));
  $('#campus-link').href = appURL + '?campus=' + campus;
  chooseBuilding();
}

function chooseBuilding() {
  const source = models[buildingSelect.value];
  model = {
    ...source,
    floors: source.floors.map(floor => ({
      ...floor,
      slabPath: new Path2D(floor.slab),
      walkPath: new Path2D(floor.walk),
      rooms: floor.spaces.filter(([path]) => path).map(([path, id, kind]) => ({ path: new Path2D(path), id, kind }))
    }))
  };
  const [x0, y0, x1, y1] = source.bounds;
  modelSpan = Math.hypot(x1 - x0, y1 - y0);
  lift = modelSpan * .082;
  $('#model-heading').textContent = model.name;
  camera = { ...home };
  hover = null;
  floorControls.replaceChildren();
  [-1, ...model.floors.map((_, index) => index).reverse()].forEach(index => {
    const floor = model.floors[index];
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.floor = index;
    button.textContent = floor ? (floor.level === 0 ? 'G' : 'L' + floor.level) : 'All';
    button.title = floor?.name ?? 'All floors';
    button.setAttribute('aria-label', button.title);
    floorControls.append(button);
  });
  focusFloor(-1);
}

function focusFloor(index, room = null) {
  selectedFloor = index;
  selectedRoom = room;
  const floor = model.floors[index];
  const caption = floor ? floor.name + (room ? ' · ' + roomName(room) : '') : 'All floors · ' + model.floors.length + ' levels';
  $('#model-caption').textContent = caption;
  $('#model-status').textContent = model.name + ', ' + caption;
  for (const button of floorControls.children) button.setAttribute('aria-pressed', +button.dataset.floor === index);
  schedule();
}

function roomName(room) {
  if (!room.id) return room.kind === 'shaft' ? 'Mapped shaft' : 'Mapped space';
  return room.kind === 'room' ? 'Room ' + room.id : String(room.id);
}

function schedule() {
  if (!frame) frame = requestAnimationFrame(draw);
}

function draw() {
  frame = 0;
  if (!width || !height || !model) return;
  ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const [x0, y0, x1, y1] = model.bounds;
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  const scale = Math.min(width * (width < 500 ? .76 : .84), height * 1.30) / modelSpan * camera.zoom;
  const c = Math.cos(camera.yaw), s = Math.sin(camera.yaw);
  const pitch = Math.sin(camera.pitch), rise = Math.cos(camera.pitch);
  const a = scale * c, b = scale * s * pitch, d = scale * c * pitch, u = -scale * s;
  const floorCount = model.floors.length;
  const middle = (floorCount - 1) / 2;
  const screenX = width * .49 + camera.x, screenY = height * .51 + camera.y;
  const matrix = z => new DOMMatrix([a, b, u, d, screenX - a * cx - u * cy, screenY - b * cx - d * cy - z * scale * rise]);
  function apply(transform) {
    ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    ctx.transform(transform.a, transform.b, transform.c, transform.d, transform.e, transform.f);
  }
  function paint(path, fill, stroke, pixels = 1) {
    if (fill) { ctx.fillStyle = fill; ctx.fill(path, 'evenodd'); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = pixels / scale; ctx.stroke(path); }
  }

  // Project an architectural grid in the same coordinate system as the floors.
  apply(matrix(-lift * (middle + .45)));
  const unit = modelSpan / 16;
  const span = unit * 26;
  const grid = new Path2D();
  const fineGrid = new Path2D();
  for (let i = -26; i <= 26; i++) {
    const lines = i % 4 === 0 ? grid : fineGrid;
    lines.moveTo(cx + i * unit, cy - span); lines.lineTo(cx + i * unit, cy + span);
    lines.moveTo(cx - span, cy + i * unit); lines.lineTo(cx + span, cy + i * unit);
  }
  paint(fineGrid, null, modelColors.fineGrid, .65);
  paint(grid, null, modelColors.grid, .8);
  surfaces = [];
  model.floors.forEach((floor, index) => {
    const z = (index - middle) * lift;
    const isSelected = selectedFloor === index;
    const stroke = isSelected ? accent : lineColor;
    ctx.globalAlpha = selectedFloor === -1 || isSelected ? 1 : index > selectedFloor ? .18 : .38;
    apply(matrix(z - modelSpan * .014));
    paint(floor.slabPath, modelColors.shaft, stroke, .9);
    const top = matrix(z);
    apply(top);
    paint(floor.slabPath, modelColors.slab, stroke, 1.2);
    paint(floor.walkPath, modelColors.walk);
    floor.rooms.forEach(room => {
      const highlighted = room === selectedRoom || (hover?.room === room && hover.index === index);
      const fill = room.kind === 'shaft' ? modelColors.shaft : modelColors.room;
      paint(room.path, highlighted ? modelColors.highlight : fill, highlighted ? accentHover : stroke, highlighted ? 1.8 : .63);
    });
    surfaces.push({ floor, index, inverse: top.inverse() });
  });
  ctx.globalAlpha = 1;
  ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
}

function locate(event) {
  const box = canvas.getBoundingClientRect();
  return { x: event.clientX - box.left, y: event.clientY - box.top };
}

function hit(point) {
  // A focused floor gets first pick so the ghosted floors don't block its rooms.
  ctx.save();
  ctx.resetTransform();
  const ordered = surfaces.slice().reverse();
  if (selectedFloor >= 0 && surfaces[selectedFloor]) {
    ordered.splice(surfaces.length - 1 - selectedFloor, 1);
    ordered.unshift(surfaces[selectedFloor]);
  }
  for (const { floor, index, inverse } of ordered) {
    const { x, y } = inverse.transformPoint(point);
    if (!ctx.isPointInPath(floor.slabPath, x, y, 'evenodd')) continue;
    const room = floor.rooms.find(item => ctx.isPointInPath(item.path, x, y, 'evenodd')) ?? null;
    ctx.restore();
    return { index, room };
  }
  ctx.restore();
  return null;
}

function orbit(dx, dy) {
  camera.yaw -= dx;
  camera.pitch = clamp(camera.pitch + dy, .20, 1.49);
}
function pan(dx, dy) { camera.x += dx; camera.y += dy; }
function zoom(factor) { camera.zoom = clamp(camera.zoom * factor, .55, 4); }
function adjust(action) {
  const commands = { left: () => orbit(-.21, 0), right: () => orbit(.21, 0), in: () => zoom(1.2), out: () => zoom(1 / 1.2), reset: () => { camera = { ...home }; } };
  commands[action]?.();
  hover = null;
  schedule();
}

canvas.addEventListener('pointerdown', event => {
  if (![0, 1, 2].includes(event.button)) return;
  canvas.setPointerCapture(event.pointerId);
  const point = locate(event);
  if (!pointers.size) gesture = { start: point, moved: false, pan: event.shiftKey || event.button !== 0 };
  else if (gesture) gesture.moved = true;
  pointers.set(event.pointerId, point);
});
canvas.addEventListener('pointermove', event => {
  const point = locate(event);
  if (!pointers.has(event.pointerId)) {
    if (pointers.size) return;
    const next = hit(point);
    if (next?.room !== hover?.room || next?.index !== hover?.index) {
      hover = next;
      canvas.classList.toggle('pickable', Boolean(next));
      schedule();
    }
    return;
  }
  const old = pointers.get(event.pointerId);
  if (pointers.size === 2) {
    const other = [...pointers.entries()].find(([id]) => id !== event.pointerId)[1];
    const before = Math.hypot(old.x - other.x, old.y - other.y);
    const after = Math.hypot(point.x - other.x, point.y - other.y);
    if (before > 5 && after > 5) zoom(after / before);
    pan((point.x - old.x) / 2, (point.y - old.y) / 2);
  } else if (pointers.size === 1) {
    if (!gesture.moved && Math.hypot(point.x - gesture.start.x, point.y - gesture.start.y) > 5) gesture.moved = true;
    if (gesture.moved) {
      if (gesture.pan) pan(point.x - old.x, point.y - old.y);
      else orbit((point.x - old.x) * .009, (point.y - old.y) * .007);
    }
  }
  pointers.set(event.pointerId, point);
  if (gesture.moved) {
    hover = null;
    canvas.classList.add('dragging');
    schedule();
  }
});
function release(event) {
  if (!pointers.delete(event.pointerId)) return;
  if (!pointers.size) {
    canvas.classList.remove('dragging');
    if (event.type === 'pointerup' && event.button === 0 && !gesture.moved && !gesture.pan) {
      const found = hit(locate(event));
      if (found) focusFloor(found.index, found.room);
    }
    gesture = null;
  }
}
for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(type, release);
canvas.addEventListener('pointerleave', () => { hover = null; canvas.classList.remove('pickable'); schedule(); });
canvas.addEventListener('contextmenu', event => event.preventDefault());
canvas.addEventListener('wheel', event => {
  if (document.activeElement !== canvas || event.ctrlKey) return;
  event.preventDefault();
  zoom(Math.exp(-clamp(event.deltaY, -150, 150) * .003));
  schedule();
}, { passive: false });
canvas.addEventListener('keydown', event => {
  const direction = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
  if (direction) {
    event.preventDefault();
    if (event.shiftKey) pan(direction[0] * 20, direction[1] * 20);
    else orbit(direction[0] * .14, direction[1] * .10);
    schedule();
  } else {
    const action = { '+': 'in', '=': 'in', '-': 'out', Home: 'reset' }[event.key];
    if (action) { event.preventDefault(); adjust(action); }
  }
});

new ResizeObserver(([entry]) => {
  width = entry.contentRect.width;
  height = entry.contentRect.height;
  pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  schedule();
}).observe(canvas);
campusSelect.addEventListener('change', chooseCampus);
buildingSelect.addEventListener('change', chooseBuilding);
floorControls.addEventListener('click', event => {
  const button = event.target.closest('button[data-floor]');
  if (button) { hover = null; focusFloor(+button.dataset.floor); }
});
$('.camera-controls').addEventListener('click', event => {
  const action = event.target.closest('button')?.dataset.camera;
  if (action) adjust(action);
});
chooseCampus();

const scenarios = {
  first: ['CAMPUS → BUILDING → ROOM', 'Find your first class.', 'Look up your classroom before you leave and see the entrance, floor, and route in one place.'],
  new: ['EXPLORE → DISCOVER → GET ORIENTED', 'Make campus feel familiar.', 'See where the libraries, study rooms, bus stops, restrooms, and cafés are as you settle in.'],
  everyday: ['SEARCH → CHECK NEARBY → GO', 'Make the next stop easier.', 'Look up a spot between classes, check what’s nearby, or find a building you haven’t visited yet.']
};
$('.scenario-controls').addEventListener('click', event => {
  const button = event.target.closest('button[data-case]');
  if (!button) return;
  for (const other of $('.scenario-controls').children) other.setAttribute('aria-pressed', other === button);
  const [route, title, copy] = scenarios[button.dataset.case];
  $('#case-route').textContent = route;
  $('#case-title').textContent = title;
  $('#case-copy').textContent = copy;
});

const menu = $('.menu-toggle');
const nav = $('#site-nav');
function setMenu(open) {
  menu.setAttribute('aria-expanded', open);
  nav.classList.toggle('open', open);
}
menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
nav.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });

$('#partner-form').addEventListener('submit', event => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.currentTarget));
  const subject = encodeURIComponent('Campus business partnership — ' + values.business);
  const body = encodeURIComponent("Hi Akadian Vertex,\n\nI'd like to learn about campus advertising.\n\nName: " + values.name + '\nBusiness: ' + values.business + '\nEmail: ' + values.email + '\nCampus: ' + values.campus + '\n\n' + values.message);
  $('#form-status').textContent = 'Your draft is ready. Add the Akadian Vertex contact email before sending.';
  window.location.href = 'mailto:?subject=' + subject + '&body=' + body;
});

const story = $('.story');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
if (!reduced.matches && 'IntersectionObserver' in window) {
  const reveal = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) { entry.target.classList.add('seen'); reveal.unobserve(entry.target); }
  }), { rootMargin: '0px 0px -8% 0px' });
  document.documentElement.classList.add('with-motion');
  document.querySelectorAll('.reveal').forEach(section => reveal.observe(section));
}
function drawProgress() {
  const rect = story.getBoundingClientRect();
  const percent = clamp((window.innerHeight * .70 - rect.top) / rect.height, 0, 1) * 100;
  story.style.setProperty('--progress', percent + '%');
}
let scrollFrame = 0;
window.addEventListener('scroll', () => {
  if (!scrollFrame) scrollFrame = requestAnimationFrame(() => { scrollFrame = 0; drawProgress(); });
}, { passive: true });
window.addEventListener('resize', drawProgress);
drawProgress();

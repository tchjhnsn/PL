/** Decided stage viewer: survey → land → foundation → frame → openings → patterns. */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const [plan, names, report, processStages, survey] = await Promise.all([
  fetch("data/plan-model.json").then((r) => r.json()),
  fetch("data/pattern-names.json").then((r) => r.json()),
  fetch("data/pass-report.json").then((r) => r.json()),
  fetch("data/process-stages.json").then((r) => r.json()),
  fetch("data/seed-district-survey.json").then((r) => r.json()),
]);

const canvas = document.getElementById("view");
const inspector = document.getElementById("inspector");
const patternList = document.getElementById("pattern-list");
const stageList = document.getElementById("stage-list");
const stageNote = document.getElementById("stage-note");
const patternsSection = document.getElementById("patterns-section");
const hud = document.getElementById("hud");

const statusByPattern = new Map(
  (report.instances || []).map((i) => [i.pattern, i.status]),
);

const STAGE_ORDER = ["survey", "land", "foundation", "frame", "openings", "patterns"];

const HEIGHT = {
  void: 0.08,
  path: 0.12,
  land: 0.04,
  foundation: 0.35,
  room: 2.7,
  solid: 3.2,
};

const BASE = {
  void: 0x3a4a42,
  path: 0x8a7d68,
  land: 0x5a6e58,
  foundation: 0x8a8478,
  room: 0xd8cbb4,
  solid: 0xcfc0a8,
};

const ROOF = 0x4a3f36;
const WINDOW = 0x6a9ab8;
const DOOR = 0x3d5c4a;
const FOCUS = 0xc9a227;
const DIM = 0x3a423c;

const HOUSE_WALL = {
  "house-b": 0xd2c4ae,
  "house-c": 0xc8b9a0,
  "house-d": 0xdbcbb2,
  workshop: 0xa89078,
};

let mode = "district";
let focusPattern = null;
let selectedId = null;
/** Highest unlocked Decided stage index (default: land = survey + land). */
let stageIndex = 1;

const placeMeshes = new Map();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x243028);
scene.fog = new THREE.Fog(0x243028, 120, 220);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 400);
camera.position.set(48, 55, 72);

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  preserveDrawingBuffer: true,
  alpha: false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x243028, 1);
renderer.shadowMap.enabled = true;

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.target.set(45, 0, -35);
controls.maxPolarAngle = Math.PI * 0.49;
controls.minDistance = 8;
controls.maxDistance = 180;

scene.add(new THREE.AmbientLight(0xb8c4bc, 0.55));
const sun = new THREE.DirectionalLight(0xfff2dd, 1.05);
sun.position.set(40, 60, 20);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
scene.add(sun);
scene.add(new THREE.HemisphereLight(0xc5d8e8, 0x3a4038, 0.35));

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(200, 200),
  new THREE.MeshStandardMaterial({ color: 0x243028, roughness: 1 }),
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.02;
ground.receiveShadow = true;
scene.add(ground);

const grid = new THREE.GridHelper(120, 24, 0x4a564e, 0x2f3832);
grid.position.set(45, 0.01, -35);
scene.add(grid);

const world = new THREE.Group();
scene.add(world);

function ringToShape(ring) {
  const shape = new THREE.Shape();
  ring.forEach(([x, y], i) => {
    if (i === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  });
  shape.closePath();
  return shape;
}

function placeHeight(place) {
  if (typeof place.height_m === "number" && place.height_m > 0) {
    return place.height_m;
  }
  if (place.kind === "room" && place.enclosure_hw) {
    return Math.max(2.4, Math.min(3.4, 2.2 + place.enclosure_hw));
  }
  return HEIGHT[place.kind] ?? 1;
}

function placeElevation(place) {
  return typeof place.floor_elevation_m === "number" ? place.floor_elevation_m : 0;
}

function placeColor(place) {
  if (focusPattern != null) {
    const hit = (place.patterns || []).includes(focusPattern);
    return hit ? FOCUS : DIM;
  }
  if (selectedId === place.id) return 0xe8dcc0;
  if (HOUSE_WALL[place.id]) return HOUSE_WALL[place.id];
  if (place.component === "building" || place.kind === "solid") return BASE.solid;
  return BASE[place.kind] ?? 0x888888;
}

function isBuildingShell(place) {
  return (
    place.kind === "solid" ||
    place.kind === "room" ||
    place.component === "building" ||
    place.component === "massing" ||
    (place.roles || []).includes("building")
  );
}

function placeStageId(place) {
  if (place.stage) return place.stage;
  if (place.kind === "land") return "land";
  if (place.kind === "foundation") return "foundation";
  if (place.kind === "room" || place.kind === "solid") return "frame";
  return "land";
}

function stageAllowed(stageId) {
  return STAGE_ORDER.indexOf(stageId) <= stageIndex;
}

function currentStage() {
  return processStages.stages[stageIndex] || processStages.stages[0];
}

function unlockedPredicates() {
  const set = new Set();
  for (let i = 0; i <= stageIndex; i++) {
    const st = processStages.stages[i];
    for (const u of st.unlocks || []) set.add(u);
  }
  return set;
}

function applyColors() {
  for (const [id, mesh] of placeMeshes) {
    const place = plan.places.find((p) => p.id === id);
    if (!place) continue;
    mesh.material.color.setHex(placeColor(place));
    mesh.material.opacity = focusPattern != null && !(place.patterns || []).includes(focusPattern)
      ? 0.35
      : place.kind === "void"
        ? 0.85
        : 0.95;
    mesh.material.transparent = true;
  }
}

function clearWorld() {
  while (world.children.length) {
    const c = world.children.pop();
    c.traverse?.((o) => {
      o.geometry?.dispose?.();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
        else o.material.dispose?.();
      }
    });
  }
  placeMeshes.clear();
}

const HOUSE_A_IDS = new Set([
  "a-court",
  "path-approach",
  "a-hall",
  "a-living",
  "a-bedroom",
  "a-balcony",
  "green-shared",
]);

function houseFocus(place) {
  return HOUSE_A_IDS.has(place.id) || String(place.id).startsWith("a-");
}

function buildPlaces() {
  const places = plan.places.filter((p) => {
    if (mode === "house") {
      const ok = houseFocus(p) || p.id === "lot-a" || p.id === "found-a";
      if (!ok) return false;
    }
    return stageAllowed(placeStageId(p));
  });

  for (const place of places) {
    if (!place.ring || place.ring.length < 3) continue;
    const shape = ringToShape(place.ring);
    const depth = placeHeight(place);
    const elev = placeElevation(place);
    const wallColor = placeColor(place);
    const isBalcony = (place.roles || []).includes("balcony") || place.component === "balcony";

    // Continuous shell from grade through elevated floors (no floating storey).
    const shellBottom = isBalcony ? elev : 0;
    const shellHeight = isBalcony ? depth : elev + depth;
    const geom = new THREE.ExtrudeGeometry(shape, {
      depth: Math.max(shellHeight, 0.08),
      bevelEnabled: false,
    });
    geom.rotateX(-Math.PI / 2);

    const mat = new THREE.MeshStandardMaterial({
      color: wallColor,
      roughness: place.kind === "solid" ? 0.85 : 0.72,
      metalness: 0.02,
      transparent: place.kind === "void" && !isBalcony,
      opacity: place.kind === "void" && !isBalcony ? 0.85 : 1,
    });
    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.y = shellBottom;
    mesh.userData.placeId = place.id;
    mesh.castShadow = isBuildingShell(place) || isBalcony;
    mesh.receiveShadow = true;
    world.add(mesh);
    placeMeshes.set(place.id, mesh);

    if (isBuildingShell(place) || isBalcony) {
      const edges = new THREE.EdgesGeometry(geom);
      const line = new THREE.LineSegments(
        edges,
        new THREE.LineBasicMaterial({ color: 0x2a2620, transparent: true, opacity: 0.45 }),
      );
      line.position.y = shellBottom;
      line.userData.placeId = place.id;
      world.add(line);
    }

    if (isBalcony && elev > 0.05) {
      addBalconyPosts(place, elev);
    }

    if (isBuildingShell(place) && !isBalcony && stageAllowed("frame")) {
      if (stageAllowed("openings") || place.kind === "room") {
        addGableRoof(place, elev + depth);
      }
      if (stageAllowed("openings")) {
        addFacadeOpenings(place, elev, depth + elev);
      }
    }
  }
}

function addBalconyPosts(place, elev) {
  const ring = place.ring || [];
  for (const [x, y] of ring) {
    const post = new THREE.Mesh(
      new THREE.BoxGeometry(0.2, elev, 0.2),
      new THREE.MeshStandardMaterial({ color: 0x5a5048, roughness: 0.85 }),
    );
    post.position.set(x, elev / 2, -y);
    post.castShadow = true;
    post.userData.placeId = place.id;
    world.add(post);
  }
  // Simple deck slab edge
  const xs = ring.map((p) => p[0]);
  const ys = ring.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const rail = new THREE.Mesh(
    new THREE.BoxGeometry(Math.max(...xs) - Math.min(...xs), 0.9, 0.08),
    new THREE.MeshStandardMaterial({ color: 0x6a756e, roughness: 0.7 }),
  );
  rail.position.set(cx, elev + 0.45, -Math.max(...ys));
  rail.userData.placeId = place.id;
  world.add(rail);
}

function ringBounds(ring) {
  const xs = ring.map((p) => p[0]);
  const ys = ring.map((p) => p[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
    w: Math.max(...xs) - Math.min(...xs),
    d: Math.max(...ys) - Math.min(...ys),
  };
}

function addGableRoof(place, topY) {
  const b = ringBounds(place.ring);
  if (b.w < 1 || b.d < 1) return;
  const ridgeAlongX = b.w >= b.d;
  const roofH = Math.min(2.4, Math.max(1.1, Math.min(b.w, b.d) * 0.28));
  const over = 0.35;
  const cx = (b.minX + b.maxX) / 2;
  const cy = (b.minY + b.maxY) / 2;
  const mat = new THREE.MeshStandardMaterial({
    color: ROOF,
    roughness: 0.92,
    metalness: 0.05,
    side: THREE.DoubleSide,
  });

  if (ridgeAlongX) {
    // Ridge parallel to X; slope in ±Z (plan Y)
    const hw = b.w / 2 + over;
    const hd = b.d / 2 + over;
    const left = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(cx - hw, topY, -(cy - hd)),
      new THREE.Vector3(cx + hw, topY, -(cy - hd)),
      new THREE.Vector3(cx + hw, topY + roofH, -cy),
      new THREE.Vector3(cx - hw, topY + roofH, -cy),
    ]);
    left.setIndex([0, 1, 2, 0, 2, 3]);
    left.computeVertexNormals();
    const right = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(cx - hw, topY, -(cy + hd)),
      new THREE.Vector3(cx + hw, topY, -(cy + hd)),
      new THREE.Vector3(cx + hw, topY + roofH, -cy),
      new THREE.Vector3(cx - hw, topY + roofH, -cy),
    ]);
    right.setIndex([0, 2, 1, 0, 3, 2]);
    right.computeVertexNormals();
    for (const g of [left, right]) {
      const mesh = new THREE.Mesh(g, mat);
      mesh.userData.placeId = place.id;
      mesh.castShadow = true;
      world.add(mesh);
    }
  } else {
    const hw = b.w / 2 + over;
    const hd = b.d / 2 + over;
    const front = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(cx - hw, topY, -(cy - hd)),
      new THREE.Vector3(cx - hw, topY, -(cy + hd)),
      new THREE.Vector3(cx, topY + roofH, -(cy + hd)),
      new THREE.Vector3(cx, topY + roofH, -(cy - hd)),
    ]);
    front.setIndex([0, 1, 2, 0, 2, 3]);
    front.computeVertexNormals();
    const back = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(cx + hw, topY, -(cy - hd)),
      new THREE.Vector3(cx + hw, topY, -(cy + hd)),
      new THREE.Vector3(cx, topY + roofH, -(cy + hd)),
      new THREE.Vector3(cx, topY + roofH, -(cy - hd)),
    ]);
    back.setIndex([0, 2, 1, 0, 3, 2]);
    back.computeVertexNormals();
    for (const g of [front, back]) {
      const mesh = new THREE.Mesh(g, mat);
      mesh.userData.placeId = place.id;
      mesh.castShadow = true;
      world.add(mesh);
    }
  }
}

function addFacadeOpenings(place, elev, totalHeight) {
  // Catalog openings already drawn for House A; synthesize a facade for neighbor shells.
  if (place.id.startsWith("a-")) return;
  const ring = place.ring;
  const n = ring.length;
  let best = null;
  for (let i = 0; i < n; i++) {
    const a = ring[i];
    const b = ring[(i + 1) % n];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    // Prefer south edges (constant plan Y, run +X) — equator face when north is +Y.
    const southish = b[0] >= a[0] && Math.abs(a[1] - b[1]) < 1e-6;
    const score = len + (southish ? 20 : 0);
    if (!best || score > best.score) best = { a, b, len, score, southish };
  }
  if (!best || best.len < 4) return;

  const { a, b, len } = best;
  const dx = (b[0] - a[0]) / len;
  const dy = (b[1] - a[1]) / len;
  // Outward normal (left of edge for CCW rings in plan)
  const nx = -dy;
  const ny = dx;
  const levels = totalHeight > 5 ? [1.2, 4.2] : [1.4];
  const winMat = new THREE.MeshStandardMaterial({
    color: WINDOW,
    roughness: 0.35,
    metalness: 0.15,
    emissive: 0x1a3040,
    emissiveIntensity: 0.15,
  });
  const doorMat = new THREE.MeshStandardMaterial({ color: DOOR, roughness: 0.7 });

  // Door near mid of primary facade
  const doorT = 0.35;
  const door = new THREE.Mesh(new THREE.BoxGeometry(1.0, 2.1, 0.16), doorMat);
  door.position.set(
    a[0] + dx * len * doorT + nx * 0.12,
    elev + 1.05,
    -(a[1] + dy * len * doorT + ny * 0.12),
  );
  door.rotation.y = Math.atan2(nx, ny);
  door.userData.placeId = place.id;
  world.add(door);

  for (const sill of levels) {
    if (sill + 1.2 > totalHeight - 0.4) continue;
    for (let t = 0.15; t <= 0.85; t += 0.18) {
      if (Math.abs(t - doorT) < 0.12 && sill < 2.5) continue;
      const win = new THREE.Mesh(new THREE.BoxGeometry(1.3, 1.15, 0.14), winMat);
      win.position.set(
        a[0] + dx * len * t + nx * 0.12,
        elev + sill + 0.55,
        -(a[1] + dy * len * t + ny * 0.12),
      );
      win.rotation.y = Math.atan2(nx, ny);
      win.userData.placeId = place.id;
      world.add(win);
    }
  }
}

function buildNorthIndicator() {
  const origin = new THREE.Vector3(4, 0.2, -4);
  const tip = new THREE.Vector3(4, 0.2, -14);
  const geom = new THREE.BufferGeometry().setFromPoints([origin, tip]);
  world.add(new THREE.Line(geom, new THREE.LineBasicMaterial({ color: 0xe8dcc0 })));
  const label = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: makeTextTexture("N"),
      depthTest: false,
      transparent: true,
    }),
  );
  label.position.set(4, 1.0, -15);
  label.scale.set(3, 3, 1);
  world.add(label);
}

function buildSurveyOverlays() {
  if (!stageAllowed("survey")) return;
  // Sun sector toward south (−Z) for northern-hemisphere seed
  const sunMat = new THREE.MeshBasicMaterial({
    color: 0xe8c56a,
    transparent: true,
    opacity: 0.18,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const wedge = new THREE.CircleGeometry(28, 32, Math.PI * 0.15, Math.PI * 0.7);
  const sun = new THREE.Mesh(wedge, sunMat);
  sun.rotation.x = -Math.PI / 2;
  sun.position.set(30, 0.03, -18);
  world.add(sun);

  for (const c of survey.contours || []) {
    if (!c.ring || c.ring.length < 3) continue;
    const pts = c.ring.map(([x, y]) => new THREE.Vector3(x, 0.06 + (c.elevation_m || 0) * 0.01, -y));
    pts.push(pts[0].clone());
    const geom = new THREE.BufferGeometry().setFromPoints(pts);
    world.add(
      new THREE.Line(
        geom,
        new THREE.LineBasicMaterial({ color: 0x9ab09a, transparent: true, opacity: 0.7 }),
      ),
    );
  }

  // Grade plane tint within survey extent
  const ex = survey.extent || plan.extent;
  if (ex) {
    const w = ex.max_x - ex.min_x;
    const d = ex.max_y - ex.min_y;
    const plane = new THREE.Mesh(
      new THREE.PlaneGeometry(w, d),
      new THREE.MeshStandardMaterial({
        color: 0x3a4a3c,
        roughness: 1,
        transparent: true,
        opacity: 0.55,
      }),
    );
    plane.rotation.x = -Math.PI / 2;
    plane.position.set((ex.min_x + ex.max_x) / 2, 0.005, -(ex.min_y + ex.max_y) / 2);
    plane.receiveShadow = true;
    world.add(plane);
  }
}

function buildInteractions() {
  if (!stageAllowed("foundation")) return;
  const mat = new THREE.LineBasicMaterial({ color: 0xa8c4ff, transparent: true, opacity: 0.55 });
  for (const ix of plan.interactions || []) {
    if (ix.kind !== "sit-on" && ix.kind !== "clearance") continue;
    const a = plan.places.find((p) => p.id === ix.a);
    const b = plan.places.find((p) => p.id === ix.b);
    if (!a?.ring || !b?.ring) continue;
    if (!stageAllowed(placeStageId(a)) || !stageAllowed(placeStageId(b))) continue;
    const ca = ringBounds(a.ring);
    const cb = ringBounds(b.ring);
    const p0 = new THREE.Vector3((ca.minX + ca.maxX) / 2, 0.5, -(ca.minY + ca.maxY) / 2);
    const p1 = new THREE.Vector3((cb.minX + cb.maxX) / 2, 0.5, -(cb.minY + cb.maxY) / 2);
    world.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([p0, p1]), mat));
  }
}

function makeTextTexture(text) {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, 64, 64);
  ctx.fillStyle = "#e8dcc0";
  ctx.font = "bold 42px serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, 32, 34);
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

function buildNetwork() {
  const edges = plan.network?.edges || plan.network || [];
  if (!Array.isArray(edges)) return;
  const mat = new THREE.LineBasicMaterial({ color: 0x6ecf9a, transparent: true, opacity: 0.85 });

  for (const e of edges) {
    const pts = e.centerline || e.path || e.polyline;
    if (!pts || pts.length < 2) continue;
    if (mode === "house") {
      // keep district flow visible but faint when zoomed conceptually
    }
    const vectors = pts.map(([x, y]) => new THREE.Vector3(x, 0.25, -y));
    const geom = new THREE.BufferGeometry().setFromPoints(vectors);
    world.add(new THREE.Line(geom, mat));
  }
}

function buildOpenings() {
  if (!stageAllowed("openings")) return;
  const openings = plan.openings || [];
  for (const o of openings) {
    const parent = o.parent || o.host || "";
    if (mode === "house" && parent && !HOUSE_A_IDS.has(parent) && !String(parent).startsWith("a-")) {
      continue;
    }
    const x = o.x ?? (o.at && o.at[0]) ?? 0;
    const y = o.y ?? (o.at && o.at[1]) ?? 0;
    const isDoor = (o.component || o.kind || "").includes("door") || o.swing != null;
    const w = o.width || (isDoor ? 0.9 : 1.2);
    const geom = new THREE.BoxGeometry(w, isDoor ? 2.1 : 1.2, 0.18);
    const mat = new THREE.MeshStandardMaterial({
      color: isDoor ? 0x1c4333 : 0x2f5f7a,
      roughness: 0.5,
    });
    const host = plan.places.find((p) => p.id === parent);
    const elev = host ? placeElevation(host) : 0;
    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.set(x, elev + (isDoor ? 1.05 : 1.5), -y);
    const angle = o.wall_angle ?? o.angle_deg;
    if (angle != null) mesh.rotation.y = (-angle * Math.PI) / 180;
    mesh.userData.placeId = parent || o.id;
    world.add(mesh);
  }
}

function rebuild() {
  clearWorld();
  buildSurveyOverlays();
  buildPlaces();
  if (stageAllowed("land")) buildNetwork();
  buildOpenings();
  buildInteractions();
  buildNorthIndicator();
  frameCamera();
  applyColors();
  const st = currentStage();
  const unlocks = [...unlockedPredicates()].join(", ") || "—";
  hud.textContent = `${st.name} · unlocks ${unlocks} · drag to orbit`;
  if (patternsSection) {
    patternsSection.style.display = stageAllowed("patterns") ? "" : "none";
  }
  if (stageNote) {
    stageNote.textContent = st.note || st.webgl || "";
  }
}

function renderStages() {
  if (!stageList) return;
  stageList.innerHTML = "";
  processStages.stages.forEach((st, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip" + (i === stageIndex ? " is-active" : "");
    btn.textContent = st.name;
    btn.dataset.stage = st.id;
    btn.setAttribute("aria-pressed", i === stageIndex ? "true" : "false");
    btn.title = `${st.mode}: requires ${(st.requires || []).join(", ") || "—"}`;
    btn.addEventListener("click", () => {
      stageIndex = i;
      if (!stageAllowed("patterns")) focusPattern = null;
      renderStages();
      renderPatterns();
      rebuild();
    });
    stageList.appendChild(btn);
  });
}

function frameCamera() {
  const box = new THREE.Box3().setFromObject(world);
  if (box.isEmpty()) return;
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const span = Math.max(size.x, size.z, 20);
  controls.target.copy(center);
  camera.position.set(center.x + span * 0.55, span * 0.7, center.z + span * 0.75);
  controls.update();
}

function statusLabel(status) {
  if (status === "satisfied") return "satisfied";
  if (status === "violated") return "violated";
  if (status === "needs_judgment") return "needs judgment";
  return "—";
}

function renderPatterns() {
  const nums = [...new Set(plan.places.flatMap((p) => p.patterns || []))].sort((a, b) => a - b);
  patternList.innerHTML = "";

  const clear = document.createElement("button");
  clear.type = "button";
  clear.className = "pattern-card" + (focusPattern == null ? " is-active" : "");
  clear.innerHTML = `<strong>All places</strong><span class="status">no filter</span>`;
  clear.addEventListener("click", () => {
    focusPattern = null;
    applyColors();
    renderPatterns();
  });
  patternList.appendChild(clear);

  for (const n of nums) {
    const status = statusByPattern.get(n) || "neutral";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pattern-card" + (focusPattern === n ? " is-active" : "");
    const title = names[String(n)] || names[n] || `Pattern ${n}`;
    btn.innerHTML =
      `<strong><span class="status-dot ${status}"></span>${n} ${title}</strong>` +
      `<span class="status">${statusLabel(status)}</span>`;
    btn.addEventListener("click", () => {
      focusPattern = n;
      applyColors();
      renderPatterns();
      showPattern(n);
    });
    patternList.appendChild(btn);
  }
}

function measuredLines(evidence) {
  const rows = evidence?.measured || [];
  if (!rows.length) return "";
  return `<p class="soft">measured</p><ul class="soft">${rows
    .map((row) => {
      const name = row.name ?? row[0];
      const value = row.value ?? row[1];
      return `<li><code>${name}</code> = ${value}</li>`;
    })
    .join("")}</ul>`;
}

function showPattern(n) {
  const status = statusByPattern.get(n);
  const inst = (report.instances || []).find((i) => i.pattern === n);
  const related = plan.places.filter((p) => (p.patterns || []).includes(n));
  inspector.innerHTML = `
    <p><strong>${n} ${names[String(n)] || ""}</strong></p>
    <p class="soft"><span class="status-dot ${status || "neutral"}"></span>${statusLabel(status)}</p>
    ${inst?.evidence?.question ? `<p class="soft">${inst.evidence.question}</p>` : ""}
    ${inst?.evidence?.check ? `<p class="soft">check: <code>${inst.evidence.check}</code></p>` : ""}
    ${measuredLines(inst?.evidence)}
    <p class="soft">${related.length} place(s) tagged</p>
    <ul class="soft">${related
      .slice(0, 8)
      .map((p) => `<li>${p.label || p.id}${typeof p.floor_elevation_m === "number" ? ` @ ${p.floor_elevation_m} m` : ""}</li>`)
      .join("")}</ul>
  `;
}

function showPlace(id) {
  const place = plan.places.find((p) => p.id === id);
  if (!place) return;
  selectedId = id;
  applyColors();
  const pats = (place.patterns || [])
    .map((n) => {
      const st = statusByPattern.get(n) || "neutral";
      return `<li><span class="status-dot ${st}"></span>${n} ${names[String(n)] || ""} — ${statusLabel(st)}</li>`;
    })
    .join("");
  const elev = placeElevation(place);
  const h = placeHeight(place);
  const links = (plan.interactions || [])
    .filter((ix) => ix.a === place.id || ix.b === place.id)
    .map((ix) => `<li><code>${ix.kind}</code> ${ix.a} ↔ ${ix.b}${ix.min_m != null ? ` ≥ ${ix.min_m} m` : ""}</li>`)
    .join("");
  inspector.innerHTML = `
    <p><strong>${place.label || place.id}</strong></p>
    <p class="soft">${place.kind} · ${place.component || "—"} · stage ${placeStageId(place)}</p>
    <p class="soft">floor ${elev.toFixed(1)} m · height ${h.toFixed(1)} m</p>
    ${place.role ? `<p class="soft">${place.role}</p>` : ""}
    ${links ? `<p class="soft">interactions</p><ul class="soft">${links}</ul>` : ""}
    <p class="soft">patterns</p>
    <ul class="soft">${pats || "<li>none</li>"}</ul>
  `;
}

function onPointer(event) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects([...placeMeshes.values()], false);
  if (hits.length) {
    const id = hits[0].object.userData.placeId;
    if (id) showPlace(id);
  }
}

canvas.addEventListener("pointerdown", (e) => {
  canvas.dataset.downX = String(e.clientX);
  canvas.dataset.downY = String(e.clientY);
});
canvas.addEventListener("pointerup", (e) => {
  const dx = Math.abs(e.clientX - Number(canvas.dataset.downX || 0));
  const dy = Math.abs(e.clientY - Number(canvas.dataset.downY || 0));
  if (dx < 4 && dy < 4) onPointer(e);
});

document.querySelectorAll("[data-mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    mode = btn.dataset.mode;
    document.querySelectorAll("[data-mode]").forEach((b) => b.classList.toggle("is-active", b === btn));
    rebuild();
  });
});

function resize() {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (w < 1 || h < 1) return;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h, false);
}

window.addEventListener("resize", resize);

function tick() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

renderStages();
rebuild();
renderPatterns();
resize();
tick();

window.__plWebgl = {
  placeCount: () => placeMeshes.size,
  stage: () => currentStage().id,
  stageIndex: () => stageIndex,
  camera: () => ({
    pos: camera.position.toArray(),
    target: controls.target.toArray(),
  }),
  worldChildren: () => world.children.length,
};

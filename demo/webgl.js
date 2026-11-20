/** Entry-level WebGL viewer: SpatialStructure → Three.js extrusions + pattern focus. */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const [plan, names, report] = await Promise.all([
  fetch("data/plan-model.json").then((r) => r.json()),
  fetch("data/pattern-names.json").then((r) => r.json()),
  fetch("data/pass-report.json").then((r) => r.json()),
]);

const canvas = document.getElementById("view");
const inspector = document.getElementById("inspector");
const patternList = document.getElementById("pattern-list");
const hud = document.getElementById("hud");

const statusByPattern = new Map(
  (report.instances || []).map((i) => [i.pattern, i.status]),
);

const HEIGHT = {
  void: 0.08,
  path: 0.12,
  room: 2.7,
  solid: 3.2,
};

const BASE = {
  void: 0x3a4a42,
  path: 0x8a7d68,
  room: 0xd4c4a8,
  solid: 0x2a2e2c,
};

const FOCUS = 0xc9a227;
const DIM = 0x3a423c;

let mode = "district";
let focusPattern = null;
let selectedId = null;

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
  return BASE[place.kind] ?? 0x888888;
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
  const places = plan.places.filter((p) => (mode === "house" ? houseFocus(p) : true));

  for (const place of places) {
    if (!place.ring || place.ring.length < 3) continue;
    const shape = ringToShape(place.ring);
    const depth = placeHeight(place);
    const geom = new THREE.ExtrudeGeometry(shape, {
      depth,
      bevelEnabled: false,
    });
    // Plan XY → Three XZ (Y up): rotate so plan Y becomes −Z
    geom.rotateX(-Math.PI / 2);

    const mat = new THREE.MeshStandardMaterial({
      color: placeColor(place),
      roughness: place.kind === "solid" ? 0.9 : 0.7,
      metalness: 0.02,
      transparent: true,
      opacity: place.kind === "void" ? 0.85 : 0.95,
    });
    const elev = placeElevation(place);
    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.y = elev;
    mesh.userData.placeId = place.id;
    mesh.castShadow = place.kind === "room" || place.kind === "solid" || elev > 0;
    mesh.receiveShadow = true;
    world.add(mesh);
    placeMeshes.set(place.id, mesh);

    // Soft outline for rooms and elevated voids (balconies)
    if (place.kind === "room" || place.kind === "solid" || elev > 0) {
      const edges = new THREE.EdgesGeometry(geom);
      const line = new THREE.LineSegments(
        edges,
        new THREE.LineBasicMaterial({ color: 0x1a1814, transparent: true, opacity: 0.55 }),
      );
      line.position.y = elev;
      line.userData.placeId = place.id;
      world.add(line);
    }
  }
}

function buildNorthIndicator() {
  const frame = plan.frame || {};
  // frame.north is "up" meaning +plan Y → Three −Z
  const origin = new THREE.Vector3(4, 0.15, -4);
  const tip = new THREE.Vector3(4, 0.15, -12);
  const geom = new THREE.BufferGeometry().setFromPoints([origin, tip]);
  world.add(new THREE.Line(geom, new THREE.LineBasicMaterial({ color: 0xe8dcc0 })));
  const label = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: makeTextTexture("N"),
      depthTest: false,
      transparent: true,
    }),
  );
  label.position.set(4, 0.8, -13);
  label.scale.set(3, 3, 1);
  world.add(label);
  void frame;
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
  buildPlaces();
  buildNetwork();
  buildOpenings();
  buildNorthIndicator();
  frameCamera();
  applyColors();
  hud.textContent =
    mode === "house"
      ? "House A · N arrow · drag to orbit · scroll to zoom"
      : "District · N arrow · drag to orbit · scroll to zoom";
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
  inspector.innerHTML = `
    <p><strong>${place.label || place.id}</strong></p>
    <p class="soft">${place.kind} · ${place.component || "—"}</p>
    <p class="soft">floor ${elev.toFixed(1)} m · height ${h.toFixed(1)} m</p>
    ${place.role ? `<p class="soft">${place.role}</p>` : ""}
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

rebuild();
renderPatterns();
resize();
tick();

// Debug for smoke checks
window.__plWebgl = {
  placeCount: () => placeMeshes.size,
  camera: () => ({
    pos: camera.position.toArray(),
    target: controls.target.toArray(),
  }),
  worldChildren: () => world.children.length,
};

/** Decided stage viewer: survey → land → foundation → frame → openings → patterns. */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { Sky } from "three/addons/objects/Sky.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

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
  land: 0x6b7d5e,
  foundation: 0x8a8478,
  room: 0xd8cbb4,
  solid: 0xcfc0a8,
};

const COVER = {
  grass: 0x4f7a45,
  gravel: 0x9a9080,
  mulch: 0x6b5344,
  water: 0x234e56,
  pond: 0x234e56,
  pavement: 0x6a6c68,
};

const ROOF = 0x6a5344;
const WINDOW = 0x9ec4d4;
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

const extent = plan.extent || { min_x: 0, min_y: 0, max_x: 90, max_y: 70 };
const siteCenter = new THREE.Vector3(
  (extent.min_x + extent.max_x) / 2,
  0,
  -((extent.min_y + extent.max_y) / 2),
);
const siteSpan = Math.max(extent.max_x - extent.min_x, extent.max_y - extent.min_y, 40);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xc5d6ea);
scene.fog = new THREE.Fog(0xd5e3f0, 220, 560);

const camera = new THREE.PerspectiveCamera(52, 1, 0.35, 480);
camera.position.set(siteCenter.x + 64, 9, siteCenter.z + 100);

const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  preserveDrawingBuffer: true,
  alpha: false,
  powerPreference: "high-performance",
});
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.88;
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1.5 : 2));
renderer.setClearColor(0xd7e2d4, 1);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.target.copy(siteCenter);
controls.maxPolarAngle = Math.PI * 0.49;
controls.minDistance = 6;
controls.maxDistance = 160;

const sun = new THREE.DirectionalLight(0xfff1d6, 2.65);
sun.castShadow = true;
sun.shadow.mapSize.set(isMobile ? 1024 : 2048, isMobile ? 1024 : 2048);
sun.shadow.bias = -0.00022;
sun.shadow.normalBias = 0.018;
sun.shadow.radius = 1.25;
const shadowHalf = siteSpan * 0.72;
sun.shadow.camera.left = -shadowHalf;
sun.shadow.camera.right = shadowHalf;
sun.shadow.camera.top = shadowHalf;
sun.shadow.camera.bottom = -shadowHalf;
sun.shadow.camera.near = 8;
sun.shadow.camera.far = siteSpan * 3.2;
sun.shadow.camera.updateProjectionMatrix();
scene.add(sun);
scene.add(sun.target);

const hemi = new THREE.HemisphereLight(0xb9cfee, 0x4e6240, 0.22);
scene.add(hemi);

/** 0 = high midday, 1 = low sunset (matches archviz sun control intent). */
let sunTime = 0.28;
let bloomEnabled = !isMobile;
const sky = new Sky();
sky.scale.setScalar(450000);
sky.frustumCulled = false;
sky.material.fog = false;
sky.material.depthWrite = false;
sky.material.fragmentShader = sky.material.fragmentShader.replace(
  "gl_FragColor = vec4( retColor, 1.0 );",
  "gl_FragColor = vec4( retColor * 0.22, 1.0 );",
);
sky.name = "sky";
scene.add(sky);
const pmrem = new THREE.PMREMGenerator(renderer);
let envRenderTarget = null;

applySunTime(sunTime);

const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);
const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(1, 1),
  isMobile ? 0.08 : 0.18,
  0.42,
  0.82,
);
bloomPass.enabled = bloomEnabled;
composer.addPass(bloomPass);
composer.addPass(new OutputPass());

const grassMap = makeTiledTexture(paintGrass, 0.16);
const gravelMap = makeTiledTexture(paintGravel, 0.22);
const asphaltMap = makeTiledTexture(paintAsphalt, 0.2);
const plasterMap = makeTiledTexture(paintPlaster, 0.35);
const groundMap = grassMap.clone();
groundMap.repeat.set(36, 36);
groundMap.needsUpdate = true;

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(Math.max(220, siteSpan * 2.4), Math.max(220, siteSpan * 2.4)),
  new THREE.MeshStandardMaterial({
    color: 0xffffff,
    map: groundMap,
    roughness: 0.96,
    metalness: 0,
    envMapIntensity: 0.35,
  }),
);
ground.name = "site-ground";
ground.rotation.x = -Math.PI / 2;
ground.position.set(siteCenter.x, -0.04, siteCenter.z);
ground.receiveShadow = true;
scene.add(ground);

const world = new THREE.Group();
scene.add(world);

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function clampByte(value) {
  return Math.max(0, Math.min(255, value));
}

function paintGrass(ctx, size, rnd) {
  ctx.fillStyle = "#4a6a38";
  ctx.fillRect(0, 0, size, size);
  const img = ctx.getImageData(0, 0, size, size);
  const data = img.data;
  for (let i = 0; i < data.length; i += 4) {
    const lift = (rnd() - 0.5) * 30;
    data[i] = clampByte(data[i] + lift * 0.55);
    data[i + 1] = clampByte(data[i + 1] + lift);
    data[i + 2] = clampByte(data[i + 2] + lift * 0.32);
  }
  ctx.putImageData(img, 0, 0);
  ctx.strokeStyle = "rgba(42, 64, 34, 0.38)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 640; i += 1) {
    const x = rnd() * size;
    const y = rnd() * size;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + (rnd() - 0.5) * 2.4, y - 3 - rnd() * 5);
    ctx.stroke();
  }
  ctx.fillStyle = "rgba(176, 184, 118, 0.2)";
  for (let i = 0; i < 160; i += 1) {
    ctx.fillRect(rnd() * size, rnd() * size, 2, 1);
  }
}

function paintGravel(ctx, size, rnd) {
  ctx.fillStyle = "#8c8274";
  ctx.fillRect(0, 0, size, size);
  const pebbles = ["#6f675c", "#a39684", "#7d7264", "#c2b5a2", "#5e574e"];
  for (let i = 0; i < 460; i += 1) {
    ctx.fillStyle = pebbles[Math.floor(rnd() * pebbles.length)];
    ctx.beginPath();
    const radius = 1.1 + rnd() * 3.1;
    ctx.ellipse(
      rnd() * size,
      rnd() * size,
      radius,
      radius * (0.65 + rnd() * 0.45),
      rnd() * Math.PI,
      0,
      Math.PI * 2,
    );
    ctx.fill();
  }
}

function paintAsphalt(ctx, size, rnd) {
  ctx.fillStyle = "#5c5e5a";
  ctx.fillRect(0, 0, size, size);
  const img = ctx.getImageData(0, 0, size, size);
  const data = img.data;
  for (let i = 0; i < data.length; i += 4) {
    const lift = (rnd() - 0.5) * 16;
    data[i] = clampByte(data[i] + lift);
    data[i + 1] = clampByte(data[i + 1] + lift);
    data[i + 2] = clampByte(data[i + 2] + lift);
  }
  ctx.putImageData(img, 0, 0);
  ctx.strokeStyle = "rgba(36, 38, 36, 0.35)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 24; i += 1) {
    ctx.beginPath();
    ctx.moveTo(rnd() * size, rnd() * size);
    ctx.lineTo(rnd() * size, rnd() * size);
    ctx.stroke();
  }
}

function paintPlaster(ctx, size, rnd) {
  ctx.fillStyle = "#d9cebc";
  ctx.fillRect(0, 0, size, size);
  const img = ctx.getImageData(0, 0, size, size);
  const data = img.data;
  for (let i = 0; i < data.length; i += 4) {
    const lift = (rnd() - 0.5) * 14;
    data[i] = clampByte(data[i] + lift);
    data[i + 1] = clampByte(data[i + 1] + lift * 0.92);
    data[i + 2] = clampByte(data[i + 2] + lift * 0.78);
  }
  ctx.putImageData(img, 0, 0);
  ctx.fillStyle = "rgba(120, 110, 95, 0.08)";
  for (let i = 0; i < 80; i += 1) {
    ctx.fillRect(rnd() * size, rnd() * size, 6 + rnd() * 18, 1);
  }
}

function makeTiledTexture(paint, repeat) {
  const size = 256;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  paint(ctx, size, mulberry32(0x51eed + repeat * 1000));
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  texture.repeat.set(repeat, repeat);
  texture.needsUpdate = true;
  return texture;
}

function applySunTime(t) {
  sunTime = Math.max(0, Math.min(1, t));
  // Midday ~48° elevation; sunset ~6°. Azimuth drifts west as the day ends.
  const elevation = THREE.MathUtils.lerp(48, 6, sunTime);
  const azimuth = THREE.MathUtils.lerp(18, 78, sunTime);
  const sunPos = new THREE.Vector3().setFromSphericalCoords(
    1,
    THREE.MathUtils.degToRad(90 - elevation),
    THREE.MathUtils.degToRad(azimuth),
  );
  const uniforms = sky.material.uniforms;
  uniforms.turbidity.value = THREE.MathUtils.lerp(2.2, 6.5, sunTime);
  uniforms.rayleigh.value = THREE.MathUtils.lerp(2.6, 1.4, sunTime);
  uniforms.mieCoefficient.value = THREE.MathUtils.lerp(0.0014, 0.0045, sunTime);
  uniforms.mieDirectionalG.value = THREE.MathUtils.lerp(0.72, 0.88, sunTime);
  uniforms.sunPosition.value.copy(sunPos);

  const skyScene = new THREE.Scene();
  skyScene.add(sky);
  const prevTone = renderer.toneMapping;
  const prevExposure = renderer.toneMappingExposure;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.toneMappingExposure = 1;
  if (envRenderTarget) envRenderTarget.dispose();
  envRenderTarget = pmrem.fromScene(skyScene, 0, 0.1, 100);
  renderer.toneMapping = prevTone;
  renderer.toneMappingExposure = prevExposure;
  skyScene.remove(sky);
  scene.add(sky);
  scene.environment = envRenderTarget.texture;
  scene.environmentIntensity = THREE.MathUtils.lerp(0.34, 0.48, sunTime);
  scene.fog.color.set(sunTime < 0.55 ? 0xd5e3f0 : 0xe8c9a8);
  scene.background = new THREE.Color(sunTime < 0.55 ? 0x8eb6dc : 0xc48a58);

  const warm = new THREE.Color().setHSL(0.1, 0.35 + sunTime * 0.35, 0.88);
  sun.color.copy(warm);
  sun.intensity = THREE.MathUtils.lerp(2.65, 1.55, sunTime);
  hemi.intensity = THREE.MathUtils.lerp(0.22, 0.12, sunTime);
  renderer.toneMappingExposure = THREE.MathUtils.lerp(0.88, 1.05, sunTime);

  const aim = siteCenter.clone();
  aim.y = 1.2;
  sun.position.copy(aim).add(sunPos.clone().multiplyScalar(siteSpan * 1.15));
  sun.target.position.copy(aim);
  sun.target.updateMatrixWorld();
  renderer.shadowMap.needsUpdate = true;
  const sunInput = document.getElementById("sun-time");
  const sunLabelEl = document.getElementById("sun-time-label");
  if (sunInput) sunInput.value = String(Math.round(sunTime * 100));
  if (sunLabelEl) sunLabelEl.textContent = sunLabel(sunTime);
}

function glassMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0xb8d4e4,
    metalness: 0,
    roughness: 0.05,
    transmission: 0.82,
    thickness: 0.35,
    ior: 1.45,
    envMapIntensity: 1.4,
    transparent: true,
    opacity: 1,
    depthWrite: false,
  });
}

function waterMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0x1a3f48,
    metalness: 0.05,
    roughness: 0.08,
    transmission: 0.55,
    thickness: 1.2,
    ior: 1.33,
    envMapIntensity: 1.6,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
  });
}

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
  const roles = place.roles || [];
  if (roles.includes("balcony") || place.component === "balcony") return 0xb8c4a8;
  if (roles.includes("pond") || place.component === "pond" || roles.includes("water")) {
    return COVER.pond;
  }
  if (roles.includes("gravel")) return COVER.gravel;
  if (roles.includes("grass") || roles.includes("green")) return COVER.grass;
  if (HOUSE_WALL[place.id]) return HOUSE_WALL[place.id];
  if (place.component === "building" || place.kind === "solid") return BASE.solid;
  if (place.kind === "land") return 0x7a8f6a;
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

function surfaceKind(place) {
  const roles = place.roles || [];
  if (roles.includes("balcony") || place.component === "balcony") return null;
  if (roles.includes("pond") || roles.includes("water") || place.component === "pond") return "pond";
  if (roles.includes("gravel")) return "gravel";
  if (roles.includes("grass") || roles.includes("green") || roles.includes("ground-cover")) return "grass";
  if (place.kind === "land") return "grass";
  if (place.kind === "path") return "gravel";
  if (place.kind === "foundation") return "concrete";
  if (place.kind === "void") return "asphalt";
  return null;
}

function surfaceTint(place) {
  if (focusPattern != null) {
    return (place.patterns || []).includes(focusPattern) ? 0xffffff : DIM;
  }
  if (selectedId === place.id) return 0xfff1d4;
  return 0xffffff;
}

function makePlaceMaterial(place) {
  const kind = surfaceKind(place);
  if (kind === "grass" || kind === "gravel" || kind === "asphalt") {
    const map = kind === "grass" ? grassMap : kind === "gravel" ? gravelMap : asphaltMap;
    return new THREE.MeshStandardMaterial({
      color: 0xffffff,
      map,
      roughness: kind === "asphalt" ? 0.92 : 0.96,
      metalness: kind === "asphalt" ? 0.04 : 0,
      envMapIntensity: 0.4,
    });
  }
  if (kind === "pond") {
    return waterMaterial();
  }
  if (kind === "concrete") {
    return new THREE.MeshStandardMaterial({
      color: 0x9a9286,
      roughness: 0.92,
      metalness: 0.03,
      envMapIntensity: 0.35,
    });
  }
  if (isBuildingShell(place) || place.kind === "room") {
    return new THREE.MeshStandardMaterial({
      color: placeColor(place),
      map: plasterMap,
      roughness: 0.78,
      metalness: 0.02,
      envMapIntensity: 0.55,
    });
  }
  return new THREE.MeshStandardMaterial({
    color: placeColor(place),
    roughness: place.kind === "solid" ? 0.82 : 0.74,
    metalness: 0.02,
    envMapIntensity: 0.5,
  });
}

function applyColors() {
  for (const [id, mesh] of placeMeshes) {
    const place = plan.places.find((p) => p.id === id);
    if (!place) continue;
    const surface = mesh.userData.surface;
    const textured = surface === "grass" || surface === "gravel" || surface === "asphalt";
    const watery = surface === "pond";
    const plastered = mesh.material.map === plasterMap;
    if (!watery) {
      mesh.material.color.setHex(textured || plastered ? surfaceTint(place) : placeColor(place));
    }
    const dimmed = focusPattern != null && !(place.patterns || []).includes(focusPattern);
    if (dimmed) {
      mesh.material.opacity = watery ? 0.35 : 0.4;
      mesh.material.transparent = true;
      mesh.material.depthWrite = false;
    } else if (watery) {
      mesh.material.opacity = 0.92;
      mesh.material.transparent = true;
      mesh.material.depthWrite = false;
    } else {
      mesh.material.opacity = 1;
      mesh.material.transparent = false;
      mesh.material.depthWrite = true;
    }
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
    const isBalcony = (place.roles || []).includes("balcony") || place.component === "balcony";

    // Continuous shell from grade through elevated floors (no floating storey).
    const shellBottom = isBalcony ? elev : 0;
    const shellHeight = isBalcony ? depth : elev + depth;
    const geom = new THREE.ExtrudeGeometry(shape, {
      depth: Math.max(shellHeight, 0.08),
      bevelEnabled: false,
    });
    geom.rotateX(-Math.PI / 2);

    const mat = makePlaceMaterial(place);
    const mesh = new THREE.Mesh(geom, mat);
    mesh.userData.surface = surfaceKind(place);
    // Slight Y bias so cover layers stack without z-fighting when coplanar.
    const yBias =
      place.component === "pond"
        ? 0.06
        : (place.roles || []).includes("gravel")
          ? 0.03
          : (place.roles || []).includes("grass") || (place.roles || []).includes("green")
            ? 0.02
            : place.kind === "land"
              ? 0.01
              : 0;
    mesh.position.y = shellBottom + yBias;
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
    roughness: 0.9,
    metalness: 0.04,
    envMapIntensity: 0.32,
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
  const winMat = glassMaterial();
  const doorMat = new THREE.MeshStandardMaterial({ color: DOOR, roughness: 0.72, envMapIntensity: 0.3 });

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

function buildTrees() {
  if (!stageAllowed("survey")) return;
  const trees = plan.trees || [];
  if (!trees.length) return;
  const dummy = new THREE.Object3D();
  const trunkGeo = new THREE.CylinderGeometry(1, 1.12, 1, 6);
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x6b4f38, roughness: 0.92 });
  const trunks = new THREE.InstancedMesh(trunkGeo, trunkMat, trees.length);
  trunks.castShadow = true;
  trunks.receiveShadow = false;
  trunks.frustumCulled = false;
  trunks.name = "tree-trunks";
  trees.forEach((tree, index) => {
    const evergreen = (tree.form || "") === "evergreen";
    const height = evergreen ? 2.35 : 1.85;
    const radius = tree.trunk || 0.28;
    dummy.position.set(tree.x, height / 2, -tree.y);
    dummy.scale.set(radius, height, radius);
    dummy.rotation.set(0, 0, 0);
    dummy.updateMatrix();
    trunks.setMatrixAt(index, dummy.matrix);
  });
  trunks.instanceMatrix.needsUpdate = true;
  world.add(trunks);

  const evergreen = trees.filter((tree) => (tree.form || "") === "evergreen");
  const deciduous = trees.filter((tree) => (tree.form || "") !== "evergreen");
  const pineLayers = [
    { lift: 0.35, radius: 1.05, height: 1.25, color: 0x2c5538 },
    { lift: 0.95, radius: 0.78, height: 1.05, color: 0x3d6a44 },
    { lift: 1.5, radius: 0.46, height: 0.82, color: 0x4d7a4e },
  ];
  for (const layer of pineLayers) {
    addTreeLayer(evergreen, dummy, {
      geometry: new THREE.ConeGeometry(1, 1, 7),
      color: layer.color,
      flatShading: false,
      place(tree, index) {
        const canopy = Math.max(0.75, (tree.canopy || 3) * 0.42);
        dummy.position.set(tree.x, 2.35 + layer.lift * canopy, -tree.y);
        dummy.scale.set(canopy * layer.radius, canopy * layer.height, canopy * layer.radius);
        dummy.rotation.set(0, index * 0.45, 0);
      },
    });
  }
  addTreeLayer(deciduous, dummy, {
    geometry: new THREE.IcosahedronGeometry(1, 1),
    color: 0x4e7338,
    flatShading: true,
    place(tree) {
      const canopy = Math.max(0.8, (tree.canopy || 3) * 0.48);
      dummy.position.set(tree.x, 1.85 + canopy * 0.72, -tree.y);
      dummy.scale.set(canopy, canopy * 0.82, canopy);
      dummy.rotation.set(0, 0, 0);
    },
  });
  addTreeLayer(deciduous, dummy, {
    geometry: new THREE.IcosahedronGeometry(1, 0),
    color: 0x3f6234,
    flatShading: true,
    place(tree, index) {
      const canopy = Math.max(0.8, (tree.canopy || 3) * 0.48);
      dummy.position.set(tree.x + canopy * 0.35, 1.85 + canopy * 0.95, -tree.y - canopy * 0.15);
      dummy.scale.set(canopy * 0.62, canopy * 0.5, canopy * 0.62);
      dummy.rotation.set(0.2, index, 0.1);
    },
  });
  buildUnderstory(trees, dummy);
}

function addTreeLayer(trees, dummy, spec) {
  if (!trees.length) return;
  const material = new THREE.MeshStandardMaterial({
    color: spec.color,
    roughness: 0.88,
    metalness: 0,
    flatShading: spec.flatShading,
    envMapIntensity: 0.35,
  });
  const mesh = new THREE.InstancedMesh(spec.geometry, material, trees.length);
  mesh.castShadow = true;
  mesh.receiveShadow = false;
  mesh.frustumCulled = false;
  trees.forEach((tree, index) => {
    spec.place(tree, index);
    dummy.updateMatrix();
    mesh.setMatrixAt(index, dummy.matrix);
  });
  mesh.instanceMatrix.needsUpdate = true;
  world.add(mesh);
}

/** Shrubs and ground clumps around authored trees — denser planting without a purchased mesh. */
function buildUnderstory(trees, dummy) {
  if (!trees.length) return;
  const rnd = mulberry32(0xc0ffee);
  const shrubs = [];
  for (const tree of trees) {
    const canopy = Math.max(0.8, (tree.canopy || 3) * 0.45);
    const count = (tree.form || "") === "evergreen" ? 3 : 5;
    for (let i = 0; i < count; i += 1) {
      const ang = rnd() * Math.PI * 2;
      const dist = canopy * (0.55 + rnd() * 0.85);
      shrubs.push({
        x: tree.x + Math.cos(ang) * dist,
        y: tree.y + Math.sin(ang) * dist,
        s: 0.35 + rnd() * 0.55,
        hue: rnd(),
      });
    }
  }
  // Extra clumps on shared green / grass cover places.
  for (const place of plan.places || []) {
    const roles = place.roles || [];
    if (!(roles.includes("grass") || roles.includes("green") || place.id === "green-shared")) continue;
    if (!place.ring || place.ring.length < 3) continue;
    const b = ringBounds(place.ring);
    for (let i = 0; i < 8; i += 1) {
      shrubs.push({
        x: b.minX + rnd() * b.w,
        y: b.minY + rnd() * b.d,
        s: 0.28 + rnd() * 0.4,
        hue: rnd(),
      });
    }
  }
  const bushMat = new THREE.MeshStandardMaterial({
    color: 0x3a5c34,
    roughness: 0.92,
    metalness: 0,
    flatShading: true,
    envMapIntensity: 0.3,
  });
  const bush = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), bushMat, shrubs.length);
  bush.castShadow = true;
  bush.receiveShadow = true;
  bush.frustumCulled = false;
  bush.name = "understory";
  shrubs.forEach((s, index) => {
    dummy.position.set(s.x, s.s * 0.55, -s.y);
    dummy.scale.set(s.s * (0.9 + s.hue * 0.3), s.s * 0.7, s.s);
    dummy.rotation.set(0.1, index * 0.7, 0.05);
    dummy.updateMatrix();
    bush.setMatrixAt(index, dummy.matrix);
  });
  bush.instanceMatrix.needsUpdate = true;
  world.add(bush);
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
  const mat = new THREE.LineBasicMaterial({ color: 0x6d7c74, transparent: true, opacity: 0.42 });

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

/** Garden / court enclosure vs building shell vs balcony rail. */
function wallKind(wall) {
  const id = wall.id || "";
  if (id.includes("court") || id === "w-house-w" || id.includes("house-e-court")) return "garden";
  if (id.includes("balc")) return "rail";
  return "building";
}

function wallHeightM(wall) {
  const kind = wallKind(wall);
  if (kind === "garden") return 1.35;
  if (kind === "rail") return 1.0;
  return 2.7;
}

function distPointToSegment(px, py, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy;
  if (len2 < 1e-12) return Math.hypot(px - ax, py - ay);
  let t = ((px - ax) * dx + (py - ay) * dy) / len2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function paramOnSegment(px, py, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy;
  if (len2 < 1e-12) return 0;
  return Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2));
}

function openingsOnWall(wall) {
  const [ax, ay] = wall.a;
  const [bx, by] = wall.b;
  const tol = Math.max(0.35, (wall.thickness || 0.2) + 0.25);
  const hits = [];
  for (const o of plan.openings || []) {
    const x = o.x ?? (o.at && o.at[0]);
    const y = o.y ?? (o.at && o.at[1]);
    if (x == null || y == null) continue;
    if (distPointToSegment(x, y, ax, ay, bx, by) > tol) continue;
    const width = o.width || 1.0;
    const t = paramOnSegment(x, y, ax, ay, bx, by);
    hits.push({ opening: o, t, width });
  }
  hits.sort((a, b) => a.t - b.t);
  return hits;
}

function buildWalls() {
  if (!stageAllowed("frame")) return;
  const walls = plan.walls || [];
  if (!walls.length) return;
  const gardenMat = new THREE.MeshStandardMaterial({
    color: 0x6a6258,
    roughness: 0.9,
    metalness: 0.02,
    envMapIntensity: 0.35,
  });
  const buildingMat = new THREE.MeshStandardMaterial({
    color: 0xcfc4b0,
    map: plasterMap,
    roughness: 0.82,
    metalness: 0.02,
    envMapIntensity: 0.45,
  });
  const railMat = new THREE.MeshStandardMaterial({
    color: 0x6a756e,
    roughness: 0.75,
    metalness: 0.05,
    envMapIntensity: 0.3,
  });

  for (const wall of walls) {
    if (mode === "house") {
      // Keep House A court + shell walls; skip neighbor-only later if needed.
      const id = wall.id || "";
      if (id.startsWith("w-") && !id.includes("court") && !id.includes("hall") && !id.includes("liv")
        && !id.includes("bed") && !id.includes("balc") && !id.includes("house-w")
        && !id.includes("house-e-court")) {
        // still show all seed walls in house mode — they belong to House A
      }
    }
    const [ax, ay] = wall.a;
    const [bx, by] = wall.b;
    const len = Math.hypot(bx - ax, by - ay);
    if (len < 0.2) continue;
    const height = wallHeightM(wall);
    const thick = wall.thickness || 0.2;
    const kind = wallKind(wall);
    const mat = kind === "garden" ? gardenMat : kind === "rail" ? railMat : buildingMat;
    const dx = (bx - ax) / len;
    const dy = (by - ay) / len;
    const angle = Math.atan2(-(by - ay), bx - ax); // plan Y → −Z
    const gaps = stageAllowed("openings") ? openingsOnWall(wall) : [];
    const spans = [];
    let cursor = 0;
    for (const g of gaps) {
      const half = (g.width + 0.08) / (2 * len);
      const t0 = Math.max(0, g.t - half);
      const t1 = Math.min(1, g.t + half);
      if (t0 > cursor + 0.01 / len) spans.push([cursor, t0]);
      cursor = Math.max(cursor, t1);
    }
    if (cursor < 1 - 0.01 / len) spans.push([cursor, 1]);
    if (!spans.length && !gaps.length) spans.push([0, 1]);

    for (const [t0, t1] of spans) {
      const segLen = (t1 - t0) * len;
      if (segLen < 0.08) continue;
      const mx = ax + dx * len * ((t0 + t1) / 2);
      const my = ay + dy * len * ((t0 + t1) / 2);
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(segLen, height, thick),
        mat,
      );
      mesh.position.set(mx, height / 2, -my);
      mesh.rotation.y = -angle;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.name = wall.id || "wall";
      mesh.userData.wallId = wall.id;
      world.add(mesh);
    }
  }
}

function isGateOpening(o, wall) {
  if (!wall) return false;
  if ((o.id || "").includes("approach") || (o.label || "").toLowerCase().includes("gate")) return true;
  return wallKind(wall) === "garden";
}

function hostWallForOpening(o) {
  const x = o.x ?? (o.at && o.at[0]);
  const y = o.y ?? (o.at && o.at[1]);
  if (x == null || y == null) return null;
  let best = null;
  for (const wall of plan.walls || []) {
    const [ax, ay] = wall.a;
    const [bx, by] = wall.b;
    const d = distPointToSegment(x, y, ax, ay, bx, by);
    const tol = Math.max(0.35, (wall.thickness || 0.2) + 0.25);
    if (d <= tol && (!best || d < best.d)) best = { wall, d };
  }
  return best?.wall || null;
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
    const wall = hostWallForOpening(o);
    const gate = isDoor && isGateOpening(o, wall);
    const leafH = gate ? 1.1 : isDoor ? 2.1 : 1.2;
    const thick = wall ? Math.max(0.12, (wall.thickness || 0.2) * 0.85) : 0.18;
    const geom = new THREE.BoxGeometry(w, leafH, thick);
    const mat = isDoor
      ? new THREE.MeshStandardMaterial({
          color: gate ? 0x4a4036 : 0x1c4333,
          roughness: 0.72,
          metalness: 0.02,
          envMapIntensity: 0.3,
        })
      : glassMaterial();
    const host = plan.places.find((p) => p.id === parent);
    const elev = host ? placeElevation(host) : 0;
    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.set(x, elev + leafH / 2, -y);
    const angle = o.wall_angle ?? o.angle_deg;
    if (angle != null) mesh.rotation.y = (-angle * Math.PI) / 180;
    mesh.userData.placeId = parent || o.id;
    mesh.userData.openingId = o.id;
    mesh.castShadow = true;
    world.add(mesh);

    if (gate && wall) {
      const postH = wallHeightM(wall);
      const postMat = new THREE.MeshStandardMaterial({
        color: 0x5a544c,
        roughness: 0.88,
        metalness: 0.02,
      });
      const [ax, ay] = wall.a;
      const [bx, by] = wall.b;
      const len = Math.hypot(bx - ax, by - ay) || 1;
      const dx = (bx - ax) / len;
      const dy = (by - ay) / len;
      for (const side of [-1, 1]) {
        const px = x + dx * side * (w / 2 + 0.08);
        const py = y + dy * side * (w / 2 + 0.08);
        const post = new THREE.Mesh(
          new THREE.BoxGeometry(0.22, postH, Math.max(0.22, (wall.thickness || 0.2) + 0.06)),
          postMat,
        );
        post.position.set(px, postH / 2, -py);
        post.rotation.y = (-(angle ?? 0) * Math.PI) / 180;
        post.castShadow = true;
        post.userData.placeId = parent || o.id;
        world.add(post);
      }
    }
  }
}

function rebuild() {
  clearWorld();
  buildSurveyOverlays();
  buildPlaces();
  buildWalls();
  buildTrees();
  if (stageAllowed("land")) buildNetwork();
  buildOpenings();
  buildInteractions();
  buildNorthIndicator();
  frameCamera();
  applyColors();
  renderer.shadowMap.needsUpdate = true;
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
  const eye = Math.max(8, span * 0.2);
  controls.target.set(center.x, Math.min(4, eye * 0.35), center.z);
  camera.position.set(center.x + span * 0.62, eye, center.z + span * 0.95);
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
  composer.setSize(w, h);
  bloomPass.resolution.set(w, h);
}

window.addEventListener("resize", resize);

function sunLabel(t) {
  if (t < 0.35) return "midday";
  if (t < 0.6) return "afternoon";
  if (t < 0.82) return "golden hour";
  return "sunset";
}

function wireLookControls() {
  const sunInput = document.getElementById("sun-time");
  const sunLabelEl = document.getElementById("sun-time-label");
  const bloomInput = document.getElementById("bloom-toggle");
  if (sunInput) {
    sunInput.value = String(Math.round(sunTime * 100));
    if (sunLabelEl) sunLabelEl.textContent = sunLabel(sunTime);
    sunInput.addEventListener("input", () => {
      const t = Number(sunInput.value) / 100;
      applySunTime(t);
      if (sunLabelEl) sunLabelEl.textContent = sunLabel(t);
    });
  }
  if (bloomInput) {
    bloomInput.checked = bloomEnabled;
    bloomInput.addEventListener("change", () => {
      bloomEnabled = bloomInput.checked;
      bloomPass.enabled = bloomEnabled;
    });
  }
}

function tick() {
  controls.update();
  if (bloomEnabled) composer.render();
  else renderer.render(scene, camera);
}

renderStages();
rebuild();
renderPatterns();
wireLookControls();
resize();
renderer.setAnimationLoop(tick);

window.__plWebgl = {
  placeCount: () => placeMeshes.size,
  stage: () => currentStage().id,
  stageIndex: () => stageIndex,
  sunTime: () => sunTime,
  bloom: () => bloomEnabled,
  setSunTime: (t) => applySunTime(t),
  camera: () => ({
    pos: camera.position.toArray(),
    target: controls.target.toArray(),
  }),
  worldChildren: () => world.children.length,
};

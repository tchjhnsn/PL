/** Geometry-aware plan renderer: network flow + measures + symbology. */

const plan = await fetch("data/plan-model.json").then((r) => r.json());

const svg = document.getElementById("plan");
const patternList = document.getElementById("pattern-list");
const inspector = document.getElementById("inspector");
const sheetTitle = document.getElementById("sheet-title");
const scaleLabel = document.getElementById("scale-label");
const flowList = document.getElementById("flow-list");
const measureList = document.getElementById("measure-list");

const NS = "http://www.w3.org/2000/svg";
let view = "district";
let activePattern = null;
let selectedId = null;

const placeById = new Map(plan.places.map((p) => [p.id, p]));
const openingById = new Map(plan.openings.map((o) => [o.id, o]));
const edgeById = new Map(plan.network.edges.map((e) => [e.id, e]));
const measureById = new Map(plan.measures.map((m) => [m.id, m]));
const nodeById = new Map(plan.network.nodes.map((n) => [n.id, n]));

const HIER_WIDTH = { arterial: 1.1, local: 0.7, lane: 0.5, approach: 0.34, path: 0.2 };

function metresLabel(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(1)} m` : "";
}

function feetLabel(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `~${Math.round(n / 0.3048)} ft` : "";
}

function el(name, attrs = {}, children = []) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    node.setAttribute(k, String(v));
  }
  for (const child of children) {
    if (typeof child === "string") node.appendChild(document.createTextNode(child));
    else if (child) node.appendChild(child);
  }
  return node;
}

function ringPoints(ring) {
  return ring.map(([x, y]) => `${x},${-y}`).join(" ");
}

function centroid(ring) {
  let x = 0;
  let y = 0;
  for (const [px, py] of ring) {
    x += px;
    y += py;
  }
  return [x / ring.length, y / ring.length];
}

function wallAngles(angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { cos: Math.cos(rad), sin: Math.sin(rad) };
}

function patternIdSet(row) {
  const ids = new Set(row.feature_ids || []);
  const diagram = row.diagram || {};
  for (const key of ["zones", "openings", "measures", "edges"]) {
    for (const item of diagram[key] || []) ids.add(item);
  }
  return ids;
}

function hotClass(id) {
  const selected = selectedId === id ? "is-selected" : "";
  if (!activePattern) return selected ? `${selected} is-hot` : "";
  const row = plan.patterns.find((p) => p.number === activePattern);
  if (!row) return selected;
  const on = patternIdSet(row).has(id);
  if (selected) return on ? "is-selected is-hot" : "is-selected";
  return on ? "is-hot" : "is-dim";
}

function drawDoor(g, door, hot) {
  const { cos, sin } = wallAngles(door.wall_angle);
  const w = door.width;
  const hx = door.x - cos * (w / 2);
  const hy = door.y - sin * (w / 2);
  const ox = door.x + cos * (w / 2);
  const oy = door.y + sin * (w / 2);
  const s = door.swing === "ccw" ? 1 : -1;
  const px = -sin * s;
  const py = cos * s;
  const lx = hx + px * w;
  const ly = hy + py * w;
  const group = el("g", { class: `hit door ${hot}`, "data-id": door.id, "data-kind": "opening" });
  group.appendChild(
    el("line", {
      x1: hx,
      y1: -hy,
      x2: ox,
      y2: -oy,
      class: "door-gap",
      "stroke-width": 0.35,
      stroke: "#fbfaf6",
    }),
  );
  const sweep = door.swing === "ccw" ? 0 : 1;
  group.appendChild(
    el("path", {
      d: `M ${hx} ${-hy} A ${w} ${w} 0 0 ${sweep} ${lx} ${-ly} L ${hx} ${-hy}`,
      class: "door-swing",
    }),
  );
  group.appendChild(el("line", { x1: hx, y1: -hy, x2: lx, y2: -ly, class: "door-leaf" }));
  g.appendChild(group);
}

function drawWindow(g, win, hot) {
  const { cos, sin } = wallAngles(win.wall_angle);
  const w = win.width;
  const x1 = win.x - cos * (w / 2);
  const y1 = win.y - sin * (w / 2);
  const x2 = win.x + cos * (w / 2);
  const y2 = win.y + sin * (w / 2);
  const nx = -sin * 0.25;
  const ny = cos * 0.25;
  const group = el("g", { class: `hit window ${hot}`, "data-id": win.id, "data-kind": "opening" });
  group.appendChild(
    el("line", { x1, y1: -y1, x2, y2: -y2, class: "window-glass", "stroke-width": 0.4 }),
  );
  group.appendChild(
    el("line", {
      x1: x1 + nx,
      y1: -(y1 + ny),
      x2: x1 - nx,
      y2: -(y1 - ny),
      class: "window-tick",
    }),
  );
  group.appendChild(
    el("line", {
      x1: x2 + nx,
      y1: -(y2 + ny),
      x2: x2 - nx,
      y2: -(y2 - ny),
      class: "window-tick",
    }),
  );
  g.appendChild(group);
}

function drawTree(g, tree, hot) {
  const evergreen = tree.form === "evergreen";
  const group = el("g", {
    class: `hit tree ${evergreen ? "evergreen" : ""} ${hot}`,
    "data-id": tree.id,
    "data-kind": "tree",
  });
  const r = tree.canopy;
  if (evergreen) {
    // Needle canopy: layered triangles (plan symbology for pine/evergreen).
    const tips = [
      [tree.x, tree.y + r],
      [tree.x - r * 0.75, tree.y - r * 0.35],
      [tree.x + r * 0.75, tree.y - r * 0.35],
    ];
    group.appendChild(
      el("polygon", {
        points: tips.map(([x, y]) => `${x},${-y}`).join(" "),
        class: "tree-canopy evergreen",
      }),
    );
    const mid = [
      [tree.x, tree.y + r * 0.45],
      [tree.x - r * 0.95, tree.y - r * 0.55],
      [tree.x + r * 0.95, tree.y - r * 0.55],
    ];
    group.appendChild(
      el("polygon", {
        points: mid.map(([x, y]) => `${x},${-y}`).join(" "),
        class: "tree-canopy evergreen",
      }),
    );
  } else {
    const lobes = [];
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const rr = r * (0.82 + 0.18 * Math.sin(i * 2.1 + tree.x));
      lobes.push([tree.x + Math.cos(a) * rr, tree.y + Math.sin(a) * rr]);
    }
    group.appendChild(
      el("polygon", { points: lobes.map(([x, y]) => `${x},${-y}`).join(" "), class: "tree-canopy" }),
    );
  }
  group.appendChild(el("circle", { cx: tree.x, cy: -tree.y, r: tree.trunk, class: "tree-trunk" }));
  g.appendChild(group);
}

function edgePoints(edge) {
  if (edge.polyline && edge.polyline.length >= 2) return edge.polyline;
  const a = nodeById.get(edge.a);
  const b = nodeById.get(edge.b);
  if (!a || !b) return null;
  return [
    [a.x, a.y],
    [b.x, b.y],
  ];
}

function pathD(pts) {
  return pts.map(([x, y], i) => `${i ? "L" : "M"} ${x} ${-y}`).join(" ");
}

function shortenEnd(pts, dist) {
  if (pts.length < 2 || dist <= 0) return pts;
  const out = pts.map((p) => [p[0], p[1]]);
  const a = out[out.length - 2];
  const b = out[out.length - 1];
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy);
  if (len <= dist + 0.05) return out;
  out[out.length - 1] = [b[0] - (dx / len) * dist, b[1] - (dy / len) * dist];
  return out;
}

function flowChevron(from, to, size) {
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  const px = -uy * size * 0.42;
  const py = ux * size * 0.42;
  const bx = to[0] - ux * size;
  const by = to[1] - uy * size;
  return `M ${bx + px} ${-(by + py)} L ${to[0]} ${-to[1]} L ${bx - px} ${-(by - py)} Z`;
}

function drawEdge(g, edge, hot) {
  const poly = edgePoints(edge);
  if (!poly) return;
  const head =
    edge.hierarchy === "arterial" ? 1.7 : edge.hierarchy === "lane" || edge.hierarchy === "local" ? 1.25 : 0.9;
  const shaft = edge.directed ? shortenEnd(poly, head * 0.85) : poly;
  const group = el("g", {
    class: `hit edge mode-${edge.mode || "shared"} ${hot}`,
    "data-id": edge.id,
    "data-kind": "edge",
  });
  group.appendChild(el("path", { d: pathD(poly), class: "flow-hit", "stroke-width": 2.2 }));
  group.appendChild(
    el("path", {
      d: pathD(shaft),
      class: "centerline",
      "stroke-width": HIER_WIDTH[edge.hierarchy] || 0.28,
    }),
  );
  if (edge.directed) {
    const prev = poly[poly.length - 2];
    const tip = poly[poly.length - 1];
    group.appendChild(el("path", { d: flowChevron(prev, tip, head), class: "flow-head" }));
  }
  g.appendChild(group);
}

function textAngle(ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = -(by - ay);
  let deg = (Math.atan2(dy, dx) * 180) / Math.PI;
  if (deg > 90) deg -= 180;
  if (deg < -90) deg += 180;
  return Math.round(deg * 10) / 10;
}

function drawMeasure(g, m, hot) {
  const [x1, y1] = m.a;
  const [x2, y2] = m.b;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const span = Math.hypot(dx, dy) || 1;
  let nx = -dy / span;
  let ny = dx / span;
  const place = m.of ? placeById.get(m.of) : null;
  if (place?.ring) {
    const [cx, cy] = centroid(place.ring);
    const dot = ((x1 + x2) / 2 - cx) * nx + ((y1 + y2) / 2 - cy) * ny;
    if (dot < -0.05) {
      nx = -nx;
      ny = -ny;
    }
  }
  const off = span < 4 ? 0.9 : 1.45;
  const over = 0.38;
  const ax = x1 + nx * off;
  const ay = y1 + ny * off;
  const bx = x2 + nx * off;
  const by = y2 + ny * off;
  const group = el("g", {
    class: `hit measure ${hot}`,
    "data-id": m.id,
    "data-kind": "measure",
  });
  group.appendChild(
    el("line", { x1: ax, y1: -ay, x2: bx, y2: -by, class: "flow-hit", "stroke-width": 2.2 }),
  );
  group.appendChild(
    el("line", {
      x1,
      y1: -y1,
      x2: x1 + nx * (off + over),
      y2: -(y1 + ny * (off + over)),
      class: "dim-ext",
    }),
  );
  group.appendChild(
    el("line", {
      x1: x2,
      y1: -y2,
      x2: x2 + nx * (off + over),
      y2: -(y2 + ny * (off + over)),
      class: "dim-ext",
    }),
  );
  group.appendChild(el("line", { x1: ax, y1: -ay, x2: bx, y2: -by, class: "dim-line" }));
  const ux = dx / span;
  const uy = dy / span;
  for (const [px, py] of [
    [ax, ay],
    [bx, by],
  ]) {
    const tx = (ux - nx) * 0.34;
    const ty = (uy - ny) * 0.34;
    group.appendChild(
      el("line", {
        x1: px - tx,
        y1: -(py - ty),
        x2: px + tx,
        y2: -(py + ty),
        class: "dim-tick",
      }),
    );
  }
  const short = span < 4.5;
  const t = short ? 0.5 : 0.62;
  const lx = ax + (bx - ax) * t + nx * (short ? 0.95 : 0.28);
  const ly = ay + (by - ay) * t + ny * (short ? 0.95 : 0.28);
  const deg = short ? 0 : textAngle(ax, ay, bx, by);
  group.appendChild(
    el(
      "text",
      {
        x: lx,
        y: -ly,
        class: "dim-label",
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        transform: deg ? `rotate(${deg} ${lx} ${-ly})` : null,
      },
      [metresLabel(m.value_m)],
    ),
  );
  g.appendChild(group);
}

function drawDiagram(g, row) {
  const d = row.diagram || {};
  const layer = el("g", { class: "diagram-layer" });
  for (const zid of d.zones || []) {
    const z = placeById.get(zid);
    if (!z) continue;
    layer.appendChild(el("polygon", { points: ringPoints(z.ring), class: "diagram-zone" }));
  }
  for (const arrow of d.arrows || []) {
    const [x1, y1] = arrow.from;
    const [x2, y2] = arrow.to;
    layer.appendChild(el("line", { x1, y1: -y1, x2, y2: -y2, class: "diagram-arrow" }));
    if (arrow.label) {
      layer.appendChild(
        el(
          "text",
          {
            x: (x1 + x2) / 2 + 0.5,
            y: -((y1 + y2) / 2) - 0.4,
            class: "diagram-label",
          },
          [arrow.label],
        ),
      );
    }
  }
  for (const ray of d.rays || []) {
    const [x, y] = ray.at;
    const [dx, dy] = ray.dir;
    layer.appendChild(
      el("line", {
        x1: x,
        y1: -y,
        x2: x + dx * 4,
        y2: -(y + dy * 4),
        class: "diagram-ray",
      }),
    );
  }
  for (const m of d.markers || []) {
    layer.appendChild(el("circle", { cx: m.at[0], cy: -m.at[1], r: 0.7, class: "selected-ring" }));
    layer.appendChild(
      el("text", { x: m.at[0], y: -m.at[1] - 1.2, class: "diagram-label", "text-anchor": "middle" }, [
        m.label,
      ]),
    );
  }
  for (const oid of d.openings || []) {
    const o = openingById.get(oid);
    if (o) layer.appendChild(el("circle", { cx: o.x, cy: -o.y, r: 0.9, class: "selected-ring" }));
  }
  for (const lab of d.labels || []) {
    layer.appendChild(
      el(
        "text",
        { x: lab.at[0], y: -lab.at[1], class: "diagram-label", "text-anchor": "middle" },
        [lab.text],
      ),
    );
  }
  for (const dim of d.dims || []) {
    const [x1, y1] = dim.a;
    const [x2, y2] = dim.b;
    layer.appendChild(el("line", { x1, y1: -y1, x2, y2: -y2, class: "diagram-dim" }));
    if (dim.label) {
      layer.appendChild(
        el(
          "text",
          {
            x: (x1 + x2) / 2,
            y: -((y1 + y2) / 2) - 0.5,
            class: "diagram-label",
            "text-anchor": "middle",
          },
          [dim.label],
        ),
      );
    }
  }
  g.appendChild(layer);
}

function listClass(id) {
  const hot = hotClass(id);
  return [selectedId === id ? "is-active" : "", hot.includes("is-hot") ? "is-related" : ""]
    .filter(Boolean)
    .join(" ");
}

function renderSideLists() {
  if (flowList) {
    flowList.replaceChildren();
    for (const e of plan.network.edges) {
      const li = document.createElement("li");
      li.className = listClass(e.id);
      li.innerHTML = `<button type="button" data-id="${e.id}" data-kind="edge"><strong>${e.label || e.id}</strong><span>${e.directed ? "→" : "↔"} ${e.mode} · ${e.hierarchy} · ${metresLabel(e.width_m)}</span></button>`;
      flowList.appendChild(li);
    }
    flowList.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => select(btn.dataset.id, "edge"));
    });
  }
  if (measureList) {
    measureList.replaceChildren();
    for (const m of plan.measures) {
      const li = document.createElement("li");
      li.className = listClass(m.id);
      li.innerHTML = `<button type="button" data-id="${m.id}" data-kind="measure"><strong>${m.label}</strong><span>${metresLabel(m.value_m)} · ${feetLabel(m.value_m)} · ${m.kind}</span></button>`;
      measureList.appendChild(li);
    }
    measureList.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => select(btn.dataset.id, "measure"));
    });
  }
}

function showInspector(id, kind) {
  if (!id) {
    inspector.innerHTML = '<p class="soft">Click a place, opening, flow edge, or dimension.</p>';
    return;
  }
  if (kind === "edge" || edgeById.has(id)) {
    const e = edgeById.get(id);
    if (!e) return;
    inspector.innerHTML = `
      <span class="tag">edge</span>
      <h3>${e.label || e.id}</h3>
      <p><strong>Mode</strong> ${e.mode}</p>
      <p><strong>Hierarchy</strong> ${e.hierarchy}</p>
      <p><strong>Width</strong> ${metresLabel(e.width_m)}</p>
      <p><strong>Flow</strong> ${e.directed ? "directed →" : "two-way ↔"}</p>`;
    return;
  }
  if (kind === "measure" || measureById.has(id)) {
    const m = measureById.get(id);
    if (!m) return;
    const ofPlace = m.of ? placeById.get(m.of) : null;
    inspector.innerHTML = `
      <span class="tag">measure</span>
      <h3>${m.label}</h3>
      <p><strong>Value</strong> ${metresLabel(m.value_m)} · ${feetLabel(m.value_m)}</p>
      <p><strong>Kind</strong> ${m.kind}</p>
      <p><strong>Of</strong> ${ofPlace?.label || m.of || "—"}</p>
      <p class="soft">Patterns: ${(m.patterns || []).join(", ") || "—"}</p>`;
    return;
  }
  if (openingById.has(id)) {
    const o = openingById.get(id);
    inspector.innerHTML = `
      <span class="tag">${o.component}</span>
      <h3>${o.label}</h3>
      <p>${o.role || ""}</p>
      ${o.facing ? `<p><strong>Facing</strong> ${o.facing}</p>` : ""}
      <p><strong>Width</strong> ${o.width} m</p>`;
    return;
  }
  const p = placeById.get(id);
  if (p) {
    inspector.innerHTML = `
      <span class="tag">${p.kind} · ${p.component}</span>
      <h3>${p.label}</h3>
      <p>${p.role || ""}</p>
      ${p.height_m ? `<p><strong>Ceiling</strong> ${p.height_m} m</p>` : ""}
      ${p.enclosure_hw != null ? `<p><strong>Enclosure H:W</strong> ${p.enclosure_hw}</p>` : ""}
      <p class="soft">Roles: ${(p.roles || []).join(", ")}</p>`;
    return;
  }
  const t = plan.trees.find((x) => x.id === id);
  if (t) {
    inspector.innerHTML = `
      <span class="tag">tree</span>
      <h3>${t.label}</h3>
      <p>${t.role}</p>
      <p><strong>Canopy</strong> ${t.canopy} m</p>`;
  }
}

function select(id, kind) {
  selectedId = id;
  showInspector(id, kind);
  render();
  renderSideLists();
}

function render() {
  const ext = plan.extent;
  let minX = ext.min_x;
  let minY = ext.min_y;
  let maxX = ext.max_x;
  let maxY = ext.max_y;
  if (view === "house") {
    minX = 15;
    minY = 10;
    maxX = 52;
    maxY = 40;
    sheetTitle.textContent = "House A — floor plan + approach";
    scaleLabel.textContent = "100";
  } else if (view === "figure") {
    sheetTitle.textContent = "Figure–ground";
    scaleLabel.textContent = "250";
  } else {
    sheetTitle.textContent = plan.title;
    scaleLabel.textContent = "250";
  }
  const pad = 2;
  svg.setAttribute(
    "viewBox",
    `${minX - pad} ${-(maxY + pad)} ${maxX - minX + pad * 2} ${maxY - minY + pad * 2}`,
  );
  svg.replaceChildren();
  svg.appendChild(
    el("defs", {}, [
      el(
        "marker",
        {
          id: "flowhead",
          markerWidth: 4,
          markerHeight: 4,
          refX: 3.5,
          refY: 2,
          orient: "auto",
        },
        [el("path", { d: "M0,0 L4,2 L0,4 Z", fill: "#1c4333" })],
      ),
      el(
        "marker",
        {
          id: "arrowhead",
          markerWidth: 5,
          markerHeight: 5,
          refX: 4,
          refY: 2.5,
          orient: "auto",
        },
        [el("path", { d: "M0,0 L5,2.5 L0,5 Z", fill: "#1c4333" })],
      ),
    ]),
  );

  const root = el("g", { id: "drawing" });

  const figureMode = view === "figure";
  const kindRank = { land: 0, void: 1, path: 2, foundation: 3, solid: 4, room: 5 };
  const places = [...plan.places].sort(
    (a, b) => (kindRank[a.kind] ?? 9) - (kindRank[b.kind] ?? 9),
  );

  for (const p of places) {
    if (!p.ring) continue;
    // In figure–ground, skip children of the right-of-way so the void stays one piece.
    if (figureMode && (p.id === "carriageway-main" || p.id === "sidewalk-main-n")) continue;
    let cls = "room-fill";
    if (figureMode) {
      cls = p.kind === "solid" || p.kind === "room" ? "fg-solid" : "fg-void";
    } else if (p.component === "pond" || p.roles?.includes("pond") || p.roles?.includes("water"))
      cls = "pond-fill";
    else if (p.roles?.includes("gravel") || p.component === "ground-cover") cls = "gravel-fill";
    else if (p.kind === "land" && (p.roles?.includes("lot") || p.roles?.includes("parcel")))
      cls = "land-fill";
    else if (p.kind === "foundation") cls = "foundation-fill";
    else if (p.kind === "void" && p.component === "street") cls = "street-fill";
    else if (p.component === "sidewalk" || p.roles?.includes("sidewalk")) cls = "sidewalk-fill";
    else if (p.component === "carriageway" || p.roles?.includes("carriageway")) cls = "street-fill";
    else if (
      p.kind === "void" &&
      (p.component === "court" || p.component === "balcony" || p.roles?.includes("green"))
    )
      cls = p.component === "balcony" ? "balcony-fill" : "green-fill";
    else if (p.kind === "path") cls = "path-fill";
    else if (p.kind === "solid") cls = "mass-fill";
    else if (p.roles?.includes("living")) cls = "room-fill living";
    else if (p.roles?.includes("private")) cls = "room-fill private";
    root.appendChild(
      el("polygon", {
        points: ringPoints(p.ring),
        class: `hit ${cls} ${hotClass(p.id)}`,
        "data-id": p.id,
        "data-kind": "place",
      }),
    );
    if (!figureMode && p.label) {
      const [cx, cy] = centroid(p.ring);
      root.appendChild(
        el(
          "text",
          { x: cx, y: -cy, class: p.kind === "solid" ? "label label-on-mass" : "label" },
          [p.label],
        ),
      );
    }
  }

  if (!figureMode) {
    for (const wall of plan.walls || []) {
      root.appendChild(
        el("line", {
          x1: wall.a[0],
          y1: -wall.a[1],
          x2: wall.b[0],
          y2: -wall.b[1],
          class: "wall-line",
          "stroke-width": wall.thickness,
        }),
      );
    }
  }

  for (const e of plan.network.edges) drawEdge(root, e, hotClass(e.id));

  if (!figureMode) {
    for (const o of plan.openings || []) {
      if (o.component === "door") drawDoor(root, o, hotClass(o.id));
      else drawWindow(root, o, hotClass(o.id));
    }
    for (const t of plan.trees || []) {
      if (view === "house" && t.x > 52) continue;
      drawTree(root, t, hotClass(t.id));
    }
  }

  for (const m of plan.measures) drawMeasure(root, m, hotClass(m.id));

  if (activePattern != null) {
    const row = plan.patterns.find((p) => p.number === activePattern);
    if (row) drawDiagram(root, row);
  }

  root.appendChild(
    el("text", { x: maxX - 3, y: -(maxY - 2), class: "north-mark", "text-anchor": "end" }, [
      "N ↑",
    ]),
  );
  svg.appendChild(root);
  renderSideLists();
}

function activatePattern(number) {
  activePattern = number === activePattern ? null : number;
  document.querySelectorAll(".pattern-card").forEach((card) => {
    card.classList.toggle("is-active", Number(card.dataset.number) === activePattern);
  });
  if (activePattern != null) {
    const row = plan.patterns.find((p) => p.number === activePattern);
    inspector.innerHTML = `
      <span class="tag">pattern · ${row.kind}</span>
      <h3>${row.number} ${row.name}</h3>
      <p>${row.look_for}</p>
      <p class="soft">Diagram + related edges/measures highlighted.</p>`;
    if ([107, 110, 112, 127, 128, 130, 159, 167, 180, 190].includes(activePattern)) {
      view = "house";
      document.querySelectorAll(".chip").forEach((c) => {
        c.classList.toggle("is-active", c.dataset.view === "house");
      });
    }
  } else showInspector(null);
  render();
}

plan.patterns.forEach((p) => {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "pattern-card";
  btn.dataset.number = String(p.number);
  btn.innerHTML = `<span class="num">${p.number}</span><span class="name">${p.name}</span><span class="kind ${p.kind === "judgment" ? "judge" : ""}">${p.kind}</span>`;
  btn.addEventListener("click", () => activatePattern(p.number));
  patternList.appendChild(btn);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    view = chip.dataset.view;
    document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("is-active", c === chip));
    render();
  });
});

svg.addEventListener("click", (ev) => {
  const hit = ev.target.closest("[data-id]");
  if (!hit) {
    selectedId = null;
    if (!activePattern) showInspector(null);
    render();
    return;
  }
  select(hit.getAttribute("data-id"), hit.getAttribute("data-kind"));
});

render();

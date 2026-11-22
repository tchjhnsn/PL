/** One-hop browser for data/concept-graph.json (copied from the design graph). */

const RELS = ["depends_on", "parent_of", "sibling_of", "maps_to", "specializes", "renders_as"];

const REL_COLOR = {
  depends_on: "#1c4333",
  parent_of: "#2f5f7a",
  sibling_of: "#8a8478",
  maps_to: "#6a5a40",
  specializes: "#5d7a52",
  renders_as: "#8a6a20",
};

const DIR_GLYPH = { out: "→", in: "←", both: "↔" };
const DIR_RANK = { out: 0, in: 1, both: 2 };

const nodeList = document.getElementById("node-list");
const search = document.getElementById("search");
const detail = document.getElementById("detail");
const relations = document.getElementById("relations");
const svg = document.getElementById("graph-svg");
const sheetTitle = document.getElementById("sheet-title");
const edgeCount = document.getElementById("edge-count");
const statsEl = document.getElementById("stats");
const filtersEl = document.getElementById("status-filters");
const layerSelect = document.getElementById("layer");
const listCount = document.getElementById("list-count");
const legend = document.getElementById("rel-legend");

let graph = null;
let byId = new Map();
let selected = null;
let statusFilter = new Set(["have", "partial", "todo", "placeholder"]);
let drawnKey = "";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) node.append(child);
  return node;
}

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value != null) node.setAttribute(key, value);
  }
  return node;
}

function statusTitle(status) {
  return graph.status_legend?.[status] || status;
}

function hops(id) {
  const groups = Object.fromEntries(RELS.map((rel) => [rel, []]));
  const seenSibling = new Set();
  const seen = new Set();
  for (const edge of graph.edges) {
    if (!groups[edge.rel]) continue;
    let other = null;
    let dir = null;
    if (edge.from === id) {
      other = edge.to;
      dir = "out";
    } else if (edge.to === id) {
      other = edge.from;
      dir = "in";
    } else {
      continue;
    }
    if (edge.rel === "sibling_of") {
      if (seenSibling.has(other)) continue;
      seenSibling.add(other);
      dir = "both";
    }
    const key = `${edge.rel}|${other}|${dir}`;
    if (seen.has(key)) continue;
    seen.add(key);
    groups[edge.rel].push({ id: other, dir });
  }
  for (const rel of RELS) {
    groups[rel].sort((a, b) => {
      const byDir = DIR_RANK[a.dir] - DIR_RANK[b.dir];
      if (byDir) return byDir;
      const an = byId.get(a.id)?.name || a.id;
      const bn = byId.get(b.id)?.name || b.id;
      return an.localeCompare(bn);
    });
  }
  return groups;
}

function layerOrder() {
  const seen = [];
  for (const node of graph.nodes) {
    if (!seen.includes(node.layer)) seen.push(node.layer);
  }
  return seen;
}

function matchesQuery(node, query) {
  if (!query) return true;
  const hay = [node.id, node.name, node.note, node.kind, node.layer, ...(node.sources || [])]
    .join(" ")
    .toLowerCase();
  return hay.includes(query);
}

function visibleNodes() {
  const query = search.value.trim().toLowerCase();
  const layer = layerSelect.value;
  return graph.nodes.filter((node) => {
    if (!statusFilter.has(node.status)) return false;
    if (layer !== "all" && node.layer !== layer) return false;
    return matchesQuery(node, query);
  });
}

function renderList() {
  const rows = visibleNodes();
  const scroll = nodeList.scrollTop;
  nodeList.replaceChildren();
  listCount.textContent = rows.length === graph.nodes.length
    ? `${graph.nodes.length} concepts`
    : `${rows.length} of ${graph.nodes.length}`;
  if (!rows.length) {
    nodeList.append(el("li", { class: "empty", text: "No concepts match." }));
    return;
  }
  let lastLayer = "";
  for (const node of rows) {
    if (node.layer !== lastLayer) {
      lastLayer = node.layer;
      nodeList.append(el("li", { class: "layer-label", text: node.layer }));
    }
    const button = el("button", { type: "button", "data-id": node.id });
    if (node.id === selected) button.classList.add("is-active");
    button.append(
      el("span", { class: "nid", text: node.id }),
      el("span", { class: `badge ${node.status}`, text: node.status, title: statusTitle(node.status) }),
      el("span", { class: "nname", text: node.name }),
    );
    button.addEventListener("click", () => select(node.id));
    nodeList.append(el("li", {}, [button]));
  }
  nodeList.scrollTop = scroll;
}

function renderDetail(id) {
  const node = byId.get(id);
  detail.replaceChildren();
  relations.replaceChildren();
  if (!node) {
    detail.append(el("p", { class: "soft", text: "Unknown concept." }));
    return;
  }
  sheetTitle.textContent = `${node.name}`;
  const head = el("div", { class: "detail-head" });
  head.append(
    el("span", { class: `badge ${node.status}`, text: node.status, title: statusTitle(node.status) }),
    el("span", { class: "tag", text: `${node.kind} · ${node.layer}` }),
  );
  detail.append(
    head,
    el("h3", { text: node.name }),
    el("p", { class: "detail-id", text: node.id }),
  );
  if (node.note) detail.append(el("p", { text: node.note }));
  const sources = node.sources || [];
  const sourceRow = el("div", { class: "src-tags" });
  sourceRow.append(el("span", { class: "src-label", text: "Sources" }));
  if (!sources.length) sourceRow.append(el("span", { class: "src-label", text: "—" }));
  for (const source of sources) {
    sourceRow.append(el("span", { class: "tag", text: source }));
  }
  detail.append(sourceRow);

  const groups = hops(id);
  let any = false;
  for (const rel of RELS) {
    const items = groups[rel];
    if (!items.length) continue;
    any = true;
    const block = el("div", { class: "rel-block" });
    const heading = el("h3");
    const swatch = el("span", { class: "rel-swatch" });
    swatch.style.background = REL_COLOR[rel];
    if (rel === "sibling_of") swatch.classList.add("is-dash");
    heading.append(swatch, document.createTextNode(rel));
    const list = el("ul");
    for (const hop of items) {
      const other = byId.get(hop.id);
      const button = el("button", { type: "button" });
      const name = other?.name || hop.id;
      button.append(
        el("span", { class: "rel-dir", text: DIR_GLYPH[hop.dir] }),
        el("span", { class: "rel-name", text: name }),
        el("span", { class: "rel-id", text: hop.id }),
      );
      if (other) {
        button.append(el("span", {
          class: `badge ${other.status}`,
          text: other.status,
          title: statusTitle(other.status),
        }));
      }
      button.addEventListener("click", () => select(hop.id));
      list.append(el("li", {}, [button]));
    }
    block.append(heading, list);
    relations.append(block);
  }
  if (!any) {
    relations.append(el("p", { class: "soft", text: "No recorded neighbors." }));
  }
  return groups;
}

function shortName(node) {
  const name = node?.name || "";
  return name.length > 22 ? `${name.slice(0, 20)}…` : name;
}

function labelPlacement(point, text) {
  const width = Math.min(170, Math.max(36, text.length * 6.15));
  const cos = Math.cos(point.angle);
  const sin = Math.sin(point.angle);
  let anchor = "middle";
  let x = point.x;
  let y = point.y + 4;
  if (cos > 0.35) {
    anchor = "start";
    x = point.x + 14;
  } else if (cos < -0.35) {
    anchor = "end";
    x = point.x - 14;
  } else if (sin < 0) {
    y = point.y - 16;
  } else {
    y = point.y + 20;
  }
  const left = anchor === "start" ? x : anchor === "end" ? x - width : x - width / 2;
  return { x, y, anchor, box: { x: left, y: y - 11, w: width, h: 14 } };
}

function boxesOverlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function placeNeighbors(id, groups, width, height) {
  const cx = width / 2;
  const cy = height / 2;
  const ordered = [];
  const seen = new Set();
  for (const rel of RELS) {
    for (const hop of groups[rel]) {
      if (seen.has(hop.id)) continue;
      seen.add(hop.id);
      ordered.push(hop.id);
    }
  }
  const maxR = Math.max(78, Math.min(width / 2 - 158, height / 2 - 36));
  const pos = new Map([[id, { x: cx, y: cy }]]);
  ordered.forEach((nid, index) => {
    const angle = -Math.PI / 2 + ((index + 0.5) / Math.max(ordered.length, 1)) * Math.PI * 2;
    pos.set(nid, {
      x: cx + Math.cos(angle) * maxR,
      y: cy + Math.sin(angle) * maxR,
      angle,
      r: maxR,
    });
  });
  for (let iter = 0; iter < 28 && ordered.length > 1; iter += 1) {
    let moved = false;
    for (let i = 0; i < ordered.length; i += 1) {
      for (let j = i + 1; j < ordered.length; j += 1) {
        const a = pos.get(ordered[i]);
        const b = pos.get(ordered[j]);
        const boxA = labelPlacement(a, shortName(byId.get(ordered[i]))).box;
        const boxB = labelPlacement(b, shortName(byId.get(ordered[j]))).box;
        if (!boxesOverlap(boxA, boxB)) continue;
        const delta = Math.atan2(Math.sin(b.angle - a.angle), Math.cos(b.angle - a.angle));
        b.angle += delta === 0 ? 0.1 : Math.sign(delta) * 0.07;
        b.r = Math.min(maxR, b.r + 4);
        b.x = cx + Math.cos(b.angle) * b.r;
        b.y = cy + Math.sin(b.angle) * b.r;
        moved = true;
      }
    }
    if (!moved) break;
  }
  return pos;
}

function rectExit(cx, cy, halfW, halfH, x, y) {
  const dx = x - cx;
  const dy = y - cy;
  const scale = Math.min(
    halfW / Math.max(Math.abs(dx), 0.001),
    halfH / Math.max(Math.abs(dy), 0.001),
  );
  return { x: cx + dx * scale, y: cy + dy * scale };
}

function pullToward(from, to, distance) {
  const dx = from.x - to.x;
  const dy = from.y - to.y;
  const len = Math.hypot(dx, dy) || 1;
  return { x: to.x + (dx / len) * distance, y: to.y + (dy / len) * distance };
}

function edgePath(x1, y1, x2, y2, slot, slots) {
  if (slots < 2) return `M ${x1} ${y1} L ${x2} ${y2}`;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const off = (slot - (slots - 1) / 2) * 16;
  const mx = (x1 + x2) / 2 + (-dy / len) * off;
  const my = (y1 + y2) / 2 + (dx / len) * off;
  return `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
}

function draw(id) {
  const rect = svg.getBoundingClientRect();
  const width = Math.max(320, Math.round(rect.width));
  const height = Math.max(300, Math.round(rect.height));
  const key = `${id}:${width}x${height}`;
  if (key === drawnKey && svg.childElementCount) return;
  drawnKey = key;

  const node = byId.get(id);
  const groups = hops(id);
  const pos = placeNeighbors(id, groups, width, height);
  const edges = [];
  for (const rel of RELS) {
    for (const hop of groups[rel]) edges.push({ ...hop, rel });
  }
  const byOther = new Map();
  for (const edge of edges) {
    if (!byOther.has(edge.id)) byOther.set(edge.id, []);
    byOther.get(edge.id).push(edge);
  }

  const name = node?.name || id;
  const pillW = Math.min(250, Math.max(132, name.length * 7.1 + 28, id.length * 6.6 + 24));
  const pillH = 46;
  const center = pos.get(id);

  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("aria-label", `Neighborhood of ${name}`);
  svg.replaceChildren();

  const defs = svgEl("defs");
  for (const rel of RELS) {
    if (rel === "sibling_of") continue;
    const marker = svgEl("marker", {
      id: `arrow-${rel}`,
      viewBox: "0 0 10 10",
      refX: "8.5",
      refY: "5",
      markerWidth: "8",
      markerHeight: "8",
      orient: "auto",
    });
    marker.append(svgEl("path", { d: "M 0 1.3 L 9 5 L 0 8.7 Z", fill: REL_COLOR[rel] }));
    defs.append(marker);
  }
  svg.append(defs);

  if (!edges.length) {
    const note = svgEl("text", {
      x: width / 2,
      y: center.y + pillH / 2 + 28,
      "text-anchor": "middle",
      class: "g-note",
    });
    note.textContent = "No neighbors";
    svg.append(note);
  }

  for (const [otherId, bundle] of byOther) {
    const other = pos.get(otherId);
    if (!other) continue;
    bundle.forEach((edge, slot) => {
      const atCenter = rectExit(center.x, center.y, pillW / 2, pillH / 2, other.x, other.y);
      const atOther = pullToward(center, other, 12);
      const inbound = edge.dir === "in";
      const start = inbound ? atOther : atCenter;
      const end = inbound ? atCenter : atOther;
      const path = svgEl("path", {
        d: edgePath(start.x, start.y, end.x, end.y, slot, bundle.length),
        class: `g-edge ${edge.rel}`,
        fill: "none",
        stroke: REL_COLOR[edge.rel],
      });
      if (edge.dir !== "both") path.setAttribute("marker-end", `url(#arrow-${edge.rel})`);
      const title = svgEl("title");
      const otherName = byId.get(otherId)?.name || otherId;
      title.textContent = edge.dir === "in"
        ? `${otherName} ${edge.rel} ${name}`
        : `${name} ${edge.rel} ${otherName}`;
      path.append(title);
      svg.append(path);
    });
  }

  for (const [nid, point] of pos) {
    if (nid === id) continue;
    const concept = byId.get(nid);
    const text = shortName(concept);
    const place = labelPlacement(point, text);
    const group = svgEl("g", { class: "g-hit", role: "button", tabindex: "0" });
    group.setAttribute("aria-label", `${concept?.name || nid}, ${concept?.status || ""}`);
    const dot = svgEl("circle", {
      cx: point.x,
      cy: point.y,
      r: "6.5",
      class: `g-dot ${concept?.status || "todo"}`,
    });
    const label = svgEl("text", {
      x: place.x,
      y: place.y,
      "text-anchor": place.anchor,
      class: "g-label",
    });
    label.textContent = text;
    const title = svgEl("title");
    title.textContent = `${concept?.name || nid} (${nid})`;
    group.append(title, dot, label);
    group.addEventListener("click", () => select(nid));
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        select(nid);
      }
    });
    svg.append(group);
  }

  const pill = svgEl("g", { class: "g-center" });
  pill.append(svgEl("rect", {
    x: center.x - pillW / 2,
    y: center.y - pillH / 2,
    width: pillW,
    height: pillH,
    rx: "4",
    class: "g-pill",
  }));
  const centerName = svgEl("text", {
    x: center.x,
    y: center.y - 4,
    "text-anchor": "middle",
    class: "g-center-name",
  });
  centerName.textContent = name.length > 32 ? `${name.slice(0, 30)}…` : name;
  const centerId = svgEl("text", {
    x: center.x,
    y: center.y + 14,
    "text-anchor": "middle",
    class: "g-center-id",
  });
  centerId.textContent = id;
  pill.append(centerName, centerId);
  svg.append(pill);

  const neighborCount = pos.size - 1;
  edgeCount.textContent = `${neighborCount} neighbor${neighborCount === 1 ? "" : "s"} · ${edges.length} edges`;
}

function revealActive() {
  const active = nodeList.querySelector("li button.is-active");
  if (!active) return;
  const li = active.closest("li");
  const listRect = nodeList.getBoundingClientRect();
  const itemRect = li.getBoundingClientRect();
  const top = nodeList.scrollTop + (itemRect.top - listRect.top);
  const bottom = top + itemRect.height;
  const viewBottom = nodeList.scrollTop + nodeList.clientHeight;
  if (top < nodeList.scrollTop) nodeList.scrollTop = Math.max(0, top - 8);
  else if (bottom > viewBottom) nodeList.scrollTop = bottom - nodeList.clientHeight + 8;
}

function select(id) {
  if (!byId.has(id)) return;
  selected = id;
  drawnKey = "";
  renderDetail(id);
  renderList();
  const paint = () => {
    revealActive();
    const rect = svg.getBoundingClientRect();
    if (rect.width < 40 || rect.height < 40) return;
    draw(id);
  };
  requestAnimationFrame(() => {
    paint();
    requestAnimationFrame(revealActive);
  });
}

function renderLegend() {
  legend.replaceChildren();
  for (const rel of RELS) {
    const swatch = el("span", { class: "rel-swatch" });
    swatch.style.background = REL_COLOR[rel];
    if (rel === "sibling_of") swatch.classList.add("is-dash");
    legend.append(el("div", {}, [swatch, document.createTextNode(rel)]));
  }
  for (const status of ["have", "partial", "todo", "placeholder"]) {
    legend.append(el("div", {}, [
      el("span", { class: `status-dot ${status}`, title: statusTitle(status) }),
      document.createTextNode(status),
    ]));
  }
}

function renderFilters() {
  filtersEl.replaceChildren();
  for (const status of ["have", "partial", "todo", "placeholder"]) {
    const button = el("button", {
      type: "button",
      class: "chip is-active",
      text: status,
      title: statusTitle(status),
    });
    button.addEventListener("click", () => {
      if (statusFilter.has(status) && statusFilter.size > 1) statusFilter.delete(status);
      else statusFilter.add(status);
      button.classList.toggle("is-active", statusFilter.has(status));
      renderList();
    });
    filtersEl.append(button);
  }
  layerSelect.replaceChildren(el("option", { value: "all", text: "All layers" }));
  for (const layer of layerOrder()) {
    layerSelect.append(el("option", { value: layer, text: layer }));
  }
}

function showLoadError(message) {
  detail.replaceChildren(el("p", { text: message }));
  listCount.textContent = "Graph unavailable";
}

async function main() {
  let response;
  try {
    response = await fetch("data/concept-graph.json");
    if (!response.ok) throw new Error(`${response.status}`);
    graph = await response.json();
  } catch {
    showLoadError("Could not load data/concept-graph.json. From the repo root run python3 demo/serve.py and open http://127.0.0.1:8765/concepts.html.");
    return;
  }
  byId = new Map(graph.nodes.map((node) => [node.id, node]));
  const nodes = graph.stats?.nodes ?? graph.nodes.length;
  const edges = graph.stats?.edges ?? graph.edges.length;
  const have = graph.stats?.by_status?.have ?? graph.nodes.filter((node) => node.status === "have").length;
  statsEl.textContent = `${nodes} nodes · ${edges} edges · ${have} have`;
  renderFilters();
  renderLegend();
  search.addEventListener("input", renderList);
  layerSelect.addEventListener("change", renderList);
  new ResizeObserver(() => {
    if (!selected) return;
    const rect = svg.getBoundingClientRect();
    if (rect.width < 40 || rect.height < 40) return;
    draw(selected);
  }).observe(svg);
  const start = byId.has("I10.place") ? "I10.place" : graph.nodes[0]?.id;
  if (start) select(start);
  else renderList();
}

main();

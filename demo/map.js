/**
 * MapLibre city surface over district.geojson (U20).
 * Figure–ground first: buildings solid, streets/courts void — not a rainbow probe.
 */
const ORIGIN = { lon: -75.1636, lat: 39.9522 };

function fillColor() {
  return [
    "case",
    ["==", ["get", "component"], "pond"],
    "#4a7a9a",
    ["any", ["==", ["get", "kind"], "solid"], ["==", ["get", "component"], "massing"]],
    "#2a2a28",
    ["==", ["get", "component"], "street"],
    "#5c5c58",
    ["==", ["get", "component"], "carriageway"],
    "#4a4a48",
    ["any", ["==", ["get", "component"], "sidewalk"], ["==", ["get", "kind"], "path"]],
    "#c9b896",
    ["any", ["==", ["get", "component"], "court"], ["==", ["get", "kind"], "void"]],
    "#6f9a6a",
    ["any", ["==", ["get", "component"], "parcel"], ["==", ["get", "component"], "block"]],
    "#8a9a7a",
    ["==", ["get", "component"], "district"],
    "#00000000",
    ["==", ["get", "kind"], "foundation"],
    "#9a9286",
    "#a8b09a",
  ];
}

function opacity() {
  return [
    "case",
    ["==", ["get", "component"], "district"],
    0,
    ["any", ["==", ["get", "kind"], "solid"], ["==", ["get", "component"], "massing"]],
    0.92,
    ["==", ["get", "component"], "street"],
    0.85,
    0.55,
  ];
}

const geo = await fetch("data/district.geojson").then((r) => r.json());

const map = new maplibregl.Map({
  container: "map",
  style: {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {},
    layers: [
      {
        id: "bg",
        type: "background",
        paint: { "background-color": "#d8d2c4" },
      },
    ],
  },
  center: [ORIGIN.lon, ORIGIN.lat],
  zoom: 16.2,
  attributionControl: { compact: true },
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");

map.on("load", () => {
  map.addSource("district", { type: "geojson", data: geo });

  map.addLayer({
    id: "places-fill",
    type: "fill",
    source: "district",
    filter: ["==", ["geometry-type"], "Polygon"],
    paint: {
      "fill-color": fillColor(),
      "fill-opacity": opacity(),
    },
  });

  map.addLayer({
    id: "places-line",
    type: "line",
    source: "district",
    filter: ["==", ["geometry-type"], "Polygon"],
    paint: {
      "line-color": "#2a2a28",
      "line-width": 0.6,
      "line-opacity": 0.35,
    },
  });

  map.addLayer({
    id: "network-line",
    type: "line",
    source: "district",
    filter: ["==", ["geometry-type"], "LineString"],
    paint: {
      "line-color": [
        "match",
        ["get", "hierarchy"],
        "arterial",
        "#1a1a18",
        "local",
        "#3a3a36",
        "lane",
        "#5a5a54",
        "#7a6a4a",
      ],
      "line-width": [
        "match",
        ["get", "hierarchy"],
        "arterial",
        3.2,
        "local",
        2.2,
        "lane",
        1.8,
        1.2,
      ],
      "line-opacity": 0.9,
    },
  });

  const bounds = new maplibregl.LngLatBounds();
  for (const f of geo.features || []) {
    const g = f.geometry;
    if (!g) continue;
    if (g.type === "Polygon") {
      for (const ring of g.coordinates) {
        for (const c of ring) bounds.extend(c);
      }
    } else if (g.type === "LineString") {
      for (const c of g.coordinates) bounds.extend(c);
    }
  }
  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, { padding: 48, maxZoom: 17.5, duration: 0 });
  }
});

const sel = document.getElementById("sel");
map.on("click", "places-fill", (e) => {
  const f = e.features && e.features[0];
  if (!f || !sel) return;
  const p = f.properties || {};
  sel.textContent = `${p.label || p.id || "—"} · ${p.component || "—"} · ${p.kind || "—"}`;
});

map.on("mouseenter", "places-fill", () => {
  map.getCanvas().style.cursor = "pointer";
});
map.on("mouseleave", "places-fill", () => {
  map.getCanvas().style.cursor = "";
});

window.__plMap = { map, featureCount: () => (geo.features || []).length };

---
name: pl-applied-research
description: Long-running applied research loop for the Pattern Language city. Use when expanding the metropolis, finding skills, codifying kits, or improving lint — research → library object → stamp → lint → verify → ship.
---

# Applied research loop (PL)

## What we are building for

A **formal pattern language for buildings and towns** that city developers can run: catalog → SpatialStructure mid-layer → checks → Decided/WebGL + MapLibre. Consumers: 70x7 city development, Idionautics. Cite pattern **numbers and names only**.

## Loop (do not wait for babysitting)

1. **Find tools** — search/install skills (Three.js, UX, architecture, P-Stack). Prefer `.agents/skills/`.
2. **Codify an object** — add a stampable kit under `src/pattern_language/kits/` (frontage lot, street section, block face…).
3. **Compose** — `demo/build_district.py` stamps kits; no one-off anonymous geometry.
4. **Lint** — `scripts/lint_spatial.py` + pytest; rules hold; exceptions only when documented.
5. **Verify** — MapLibre + WebGL readable; screenshot when house/street claims change.
6. **Ship** — draft PR; continue.

## Anti-patterns

- Hand-authoring the Nth lot without a kit.
- Breaking PL into generic procedural city soup.
- Process jargon in product chrome.
- Stopping to ask permission for the next obvious city cell.

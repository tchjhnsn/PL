# U24 — Urban typology ontology + component library

## Goal

Codify researched urban design typologies into a formal ontology and bind them to the stampable kit library — so the city grows from named types, not anonymous boxes.

## Contract

- `schema/ontology/urban-typologies.json` + `.schema.json` validate
- Layers: fabric, transect, street, block, plot, building, open_space, program
- Components declare `implements` typology ids; three kits already `implemented`
- `pattern_language.urban_typology` loads + checks refs
- `pattern_language.kits.registry` resolves implemented kits
- No catalog / Lean / `pl` / MCP change
- Cite pattern numbers/names only

## Acceptance

```bash
uv run pytest tests/test_urban_typology.py tests/test_kits.py
python3 -c "from pattern_language.kits.registry import library_summary; print(library_summary())"
```

## Non-goals

Implementing `comp.street-section` / `comp.block-face` in this unit (planned entries only).
Mesh GLB packs (borrow later via `mesh_hint`).

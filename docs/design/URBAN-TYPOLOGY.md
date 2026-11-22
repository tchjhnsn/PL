# Urban design typology ontology

Formal typologies for Seed City: research → ontology → stampable component library.

Machine document: [`schema/ontology/urban-typologies.json`](../../schema/ontology/urban-typologies.json)  
Schema: [`schema/ontology/urban-typologies.schema.json`](../../schema/ontology/urban-typologies.schema.json)  
Loader: `pattern_language.urban_typology` · kit registry: `pattern_language.kits.registry`

## Research basis (what we borrowed)

| Tradition | What we take | What we do not take |
|---|---|---|
| **Conzen** town-plan analysis | Street / plot / building as plan elements; plan units as tissue | Historical map archaeology as runtime |
| **Muratori–Caniggia** | Building type generates tissue; street as plot series | Full typological process history |
| **Kropf** | Clear hierarchy: buildings in plots in street pattern | Competing hierarchy debates |
| **Urban Taxonomy / Fleischmann et al.** | Coherent vs incoherent fabric; dense / interconnected clusters | Clustering pipeline as a dependency |
| **Building Types Online** | Morphological types: block edge, infill, entire block, solitary, slab | Program taxonomy as morphology |
| **Duany Transect / SmartCode** | T3–T5 intensity + thoroughfare character (road / street / avenue / boulevard / lane) | Full zoning code |
| **CityGML / CityJSON** | Thematic class mapping for interchange | CityGML as authoring UI |
| **Pattern Language** | Pattern **numbers and names only** on types | Book text |

## Layers (ontology)

```text
fabric / transect
    └─ street  (ROW, carriageway, sidewalk)
    └─ block
         └─ plot  (frontage, corner)
              └─ building morphology  (edge, infill, solitary, slab)
              └─ program            (living, shop, school, civic…)
    └─ open_space  (court, green finger, playground, fringe)
```

**Morphology ≠ program.** A school can be solitary or block-edge; a frontage plot can be living or shop.

## Component library (status)

| Component | Kit | Status |
|---|---|---|
| `comp.frontage-lot` | `stamp_frontage_lot` | implemented |
| `comp.program-place` | `stamp_program_place` | implemented |
| `comp.city-fabric` | `generate_city_fabric` | implemented |
| `comp.street-section` | — | planned |
| `comp.block-face` | — | planned |
| `comp.corner-shop` | — | planned |

Implemented kits stay the **semantic** library. Mesh kits (storefront bay GLBs, etc.) attach later via `mesh_hint` — SpatialStructure remains source of truth.

## How to use

```python
from pattern_language.urban_typology import get_type, components_for_type, load_urban_typologies
from pattern_language.kits.registry import resolve_kit, library_summary

load_urban_typologies()  # schema + internal refs
get_type("ut.open.green-finger")["patterns"]  # [3, 60, 67]
resolve_kit("comp.frontage-lot")  # stamp_frontage_lot
library_summary()
```

## Product rules

1. Stamp places through kits that declare `implements` typology ids.
2. Neighborhood scale keeps seed tissue (`ut.fabric.coherent-dense` / T4); City scale adds metro fabric — do not delete the neighborhood.
3. Cite pattern numbers/names only on types and places.
4. Next kit to implement: `comp.street-section` (carriageway + sidewalks as first-class types).

## Commands

```bash
uv run pytest tests/test_urban_typology.py
python3 -c "from pattern_language.kits.registry import library_summary; print(library_summary())"
```

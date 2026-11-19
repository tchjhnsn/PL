# U3 synthesis

## Decision

Base: candidate A (two houses: `pass-house.ifc` / `fail-house.ifc` carrying all ten computed pass/fail witnesses).

Graft from B:
- Frozen `Topology` / `Zone` / `Opening` / `Adjacency` types with no IFC leakage past `topology.py`
- `read_ifc` / `write_ifc` import IfcOpenShell inside the function body
- Sibling `.expected.json` + `make_fixtures.py --check` comparing graphs, not STEP bytes

## Why A

- Laziness Protocol: twenty nearly-duplicate houses do not change the U3 done-when (readback of zones, adjacency, orientations, heights).
- Shared houses still give U4 a pass path and a fail path for every computed check, as long as witnesses do not cancel.
- Judged patterns 110 and 180 get no house (both sketches agree).

## Reopen B when

A shared fail house cannot hold non-cancelling witnesses, or U4 needs distinct fixture paths per pattern for clarity in reports.

## Implement

`docs/design/u3-sketch-a.md` for fixture shape and witness table; B's type/import boundary and expected-JSON check.

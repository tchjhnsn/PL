# U6 synthesis

## Decision

Base: candidate B (thin stdio adapter; validate args/results against existing schemas; tools only call catalog/sequence/checker/step).

Graft from A: do not add `mcp/__init__.py` (keep the `mcp` name for the SDK package); in-memory or stdio client test both acceptable if each tool is called.

## Why B

- Boundary Discipline: JSON Schema at the MCP edge, trust types inside
- Laziness: no new domain logic in the server

## Implement

`docs/design/u6-sketch-b.md` + A package-naming note.

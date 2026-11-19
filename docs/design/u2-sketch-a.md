# U2 candidate A — minimal Lean signature

U2 adds the language laws and a generated building instantiation. It is done when `lake build` passes, `decide` proves that numeric order is a valid sequence for the twelve seed patterns, and CI fails when the generated file differs from `scripts/catalog_to_lean.py`.

The signature is the structure in `DESIGN.full.md` §2.6. `Pattern` stays a field. The seed is a finite inductive outside that structure. Geometry, project languages, and a general existence proof stay out of this unit.

Cite pattern numbers only in Lean. The generator copies numbers and `smaller` links. It leaves names, summaries, forces, and conditions in the JSON.

These signatures elaborate on `leanprover/lean4:v4.33.1` with `lake-manifest.json` `packages` empty. `omega`, `Subrelation.wf`, `InvImage.wf`, `List.all_eq_true`, and `List.idxOf?` are Init.

## Usage

Regenerate the seed, from the repo root:

```bash
uv run python scripts/catalog_to_lean.py
```

Check the committed file without writing:

```bash
uv run python scripts/catalog_to_lean.py --check
```

`--check` exits 0 when `lean/PatternLanguage/Instantiations/Buildings.lean` equals the render of `load_catalog`. It exits 1, and does not write, when the file differs or the catalog is not ok. A missing file is stale.

An optional positional `root` defaults to the parent of `scripts/`, the same default as `scripts/validate_catalog.py`.

After a successful write, from `lean/`:

```bash
lake build
```

The seed facts are `PatternLanguage.Instantiations.Buildings.numericOrder_ok`, proved by `decide`, and `numericOrder_valid`, the same fact at type `ValidSequence`.

## Call sites

| Caller | What it does |
|---|---|
| `scripts/catalog_to_lean.py` | Calls `load_catalog`. On `catalog.ok`, renders `Buildings.lean` and writes it, or compares it under `--check`. |
| `lean/PatternLanguage/Instantiations/Buildings.lean` | Generated. Imports `PatternLanguage.Language` and `PatternLanguage.Sequence`. |
| `tests/test_catalog_to_lean.py` | Asserts `render(load_catalog(repo))` equals the committed file, and that `--check` exits 0. |
| `tests/test_boundaries.py` | The CI test expects the `--check` step. The Mathlib scan already walks every file under `lean/` except `.lake`. |
| `.github/workflows/ci.yml` | Runs `--check` after `validate_catalog.py` and before `lean-action`. |
| U5 sequencer | Later caller of `ValidSequence` and `Preserving`. U2 does not add it. |

`load_catalog` is the only read of the catalog. The script scans through that call. `gate.py` stays as it is. There is no `pl` command and no `[project.scripts]` entry.

`lake build` is the proof check. Pytest compares text and does not invoke `lake`.

## Data shapes

### Scale

```lean
inductive Scale
  | town
  | building
  | construction
deriving DecidableEq, Repr
```

`[D]` Order: town is larger than building, building larger than construction. `rank` encodes that, and `≤` on `Scale` follows rank.

| Constructor | rank |
|---|---|
| `town` | 2 |
| `building` | 1 |
| `construction` | 0 |

`a ≤ b` means `a.rank ≤ b.rank`. So `building ≤ town`, and `town ≤ building` is false. `scale_mono` uses this order: a smaller-pattern at town scale cannot complete a building-scale pattern.

`instance : LE Scale` and `instance (a b : Scale) : Decidable (a ≤ b)` live in `Language.lean`.

### Language

```lean
structure Language where
  Pattern : Type
  scale : Pattern → Scale
  smaller : Pattern → Pattern → Prop
  scale_mono : ∀ p q, smaller q p → scale q ≤ scale p
  acyclic : WellFounded (fun q p => smaller q p)
```

| Field | Tag | Meaning |
|---|---|---|
| `Pattern` | [P] | Carrier chosen by the instantiation. |
| `scale` | [D] | Scale of each pattern. |
| `smaller` | [D] | `smaller q p`: q is one of the smaller patterns that help complete p. |
| `scale_mono` | [S] | The link never goes up in scale. False when some pattern lists a larger-scale pattern among its smaller ones. |
| `acyclic` | [S] | The link graph has no cycle. False when two patterns each help complete the other, directly or through a chain. |

`smaller q p` is the JSON fact "`q` is in `p.smaller`". The `larger` arrays stay in the JSON. U1 already checks that the seed inverse holds. Lean has one relation.

### How a finite edge list fills the two proofs

`decide` closes a closed decidable goal. It does not invent a `Decidable` instance for `∀ p q : Pat, …`. The catalog-sized obligations are `List.all` facts. Hand-written lemmas turn those Booleans into the structure fields.

```lean
def edgeIncreases {α : Type} (number : α → Nat) (edges : List (α × α)) : Bool :=
  edges.all fun (q, p) => decide (number p < number q)

def edgeScaleMono {α : Type} (scale : α → Scale) (edges : List (α × α)) : Bool :=
  edges.all fun (q, p) => decide (scale q ≤ scale p)

def patternNumberBound : Nat := 253

theorem scaleMono_of_edges {α : Type} (scale : α → Scale) (edges : List (α × α))
    (h : edgeScaleMono scale edges = true) :
    ∀ p q, (q, p) ∈ edges → scale q ≤ scale p :=
  fun p q hmem => of_decide_eq_true ((List.all_eq_true).mp h (q, p) hmem)

theorem acyclicOfIncreasingNumber {α : Type} (number : α → Nat) (bound : Nat)
    (edges : List (α × α))
    (hBound : ∀ a, number a ≤ bound)
    (hInc : edgeIncreases number edges = true) :
    WellFounded (fun q p => (q, p) ∈ edges)
```

`patternNumberBound` is the maximum in `schema/catalog.schema.json`.

`acyclicOfIncreasingNumber` is `Subrelation.wf`. The well-founded relation is `InvImage (· < ·) (fun a => bound - number a)`, whose well-foundedness is `InvImage.wf` of `Nat.lt_wfRel`. An edge `(q, p)` steps to a greater `number`, so `bound - number` falls. The subtraction step is:

```lean
private theorem sub_lt_of_lt {b p q : Nat} (hp : p ≤ b) (hq : q ≤ b) (hlt : p < q) :
    b - q < b - p := by omega
```

`hBound` is the remaining forall over the carrier. On the seed it is `number_le`, one generated line: `cases p <;> decide`. That case split is what `decide` cannot do by itself on an inductive.

### Seed instantiation

`Pat` has twelve constructors, `p105` through `p190`, in numeric order: 105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190.

| Def | Source |
|---|---|
| `number` | `Pattern.number`, one arm per constructor |
| `scaleOf` | `Pattern.scale`, one arm per constructor. The seed is `building` on every arm. |
| `smallerEdges : List (Pat × Pat)` | `(q, p)` for each `q` in `p.smaller`, patterns in numeric order, targets in stored order |
| `numericOrder` | the twelve constructors sorted by `number` |

Seed edges `(q, p)`:

| p | q |
|---|---|
| 105 | 106, 107, 128 |
| 106 | 167 |
| 107 | 128, 159, 190 |
| 110 | 112, 130 |
| 112 | 130 |
| 127 | 130 |
| 128 | 159 |
| 159 | 180 |

130, 167, 180, and 190 contribute no pairs.

```lean
def language : Language where
  Pattern := Pat
  scale := scaleOf
  smaller q p := (q, p) ∈ smallerEdges
  scale_mono := scaleMono_of_edges scaleOf smallerEdges (by decide)
  acyclic := acyclicOfIncreasingNumber number patternNumberBound smallerEdges
    number_le (by decide)

instance : BEq language.Pattern := inferInstanceAs (BEq Pat)
```

The `BEq` instance is required because `Pattern` is a field. Instance search does not look through `Pattern := Pat`. The instance has to be declared before `ValidSequence language …` is checked. A `letI` inside the proof is too late.

`number_le` is `∀ p, number p ≤ patternNumberBound`, proved by `cases p <;> decide`.

### Sequence

```lean
def indexBefore {α : Type} [BEq α] (order : List α) (earlier later : α) : Bool :=
  match order.idxOf? earlier, order.idxOf? later with
  | some i, some j => decide (i < j)
  | _, _ => false

def orderOk {α : Type} [BEq α] (order : List α) (edges : List (α × α)) : Bool :=
  edges.all fun (q, p) => indexBefore order p q

def ValidSequence (L : Language) [BEq L.Pattern] (s : List L.Pattern) : Prop :=
  ∀ q p, L.smaller q p → indexBefore s p q = true
```

`[D]` `ValidSequence`: every smaller pattern appears after the pattern it completes. `indexBefore s p q` is true when both occur in `s` and the first index of `p` is less than the first index of `q`. A missing endpoint makes it false.

```lean
theorem numericOrder_ok : orderOk numericOrder smallerEdges = true := by
  decide

theorem numericOrder_valid : ValidSequence language numericOrder := by
  intro q p h
  exact (List.all_eq_true).mp numericOrder_ok (q, p) h
```

`numericOrder_ok` is the `decide` proof. `numericOrder_valid` is that fact at `ValidSequence`. `lake build` fails when a smaller-target is absent from the list or does not sit strictly after its source. On this seed every stored smaller-target is greater than its source, so both theorems close.

A downward smaller-link still generates. `decide` is what rejects it. U1 already prints that link as a back-edge.

### Preservation

Satisfaction is abstract. `Design` is a parameter. This unit has no IFC, no centers, and no building `sat`.

```lean
structure Satisfaction (L : Language) where
  Design : Type
  sat : Design → L.Pattern → Prop

def Preserving (S : Satisfaction L) (sel : List L.Pattern) (d d' : S.Design) : Prop :=
  ∀ p, p ∈ sel → S.sat d p → S.sat d' p

def Adds (S : Satisfaction L) (p : L.Pattern) (d d' : S.Design) : Prop :=
  ¬ S.sat d p ∧ S.sat d' p
```

| Name | Tag | Meaning |
|---|---|---|
| `Design` | [P] | Whatever a later unit checks. |
| `sat` | [D] | `sat d p` means pattern p holds of design d. |
| `Preserving` | [D] | Patterns in `sel` that hold in `d` hold in `d'`. False when one of them held before and fails after. |
| `Adds` | [D] | `p` failed before and holds after. False when `p` already held or still fails. |

`Preserving.refl` and `Preserving.trans` are the two lemmas.

A run is the reflexive-transitive closure on a fixed list:

```lean
inductive Run {L : Language} (S : Satisfaction L) (sel : List L.Pattern) :
    S.Design → S.Design → Prop where
  | refl (d : S.Design) : Run S sel d d
  | step {d mid final : S.Design}
      (r : Run S sel d mid) (h : Preserving S sel mid final) : Run S sel d final

theorem Run.preserving {L : Language} (S : Satisfaction L) (sel : List L.Pattern)
    {d d' : S.Design} (r : Run S sel d d') : Preserving S sel d d' := by
  induction r with
  | refl => exact Preserving.refl S sel d
  | step _ h ih => exact Preserving.trans ih h
```

The `refl` alternative binds no name. `d` is the index still in scope. Constructor results repeat `Run S sel …`.

Adding runs down the sequence. The list being preserved is the whole sequence, the same list the design writes as `S`.

```lean
structure Adding (S : Satisfaction L) (sel : List L.Pattern) (p : L.Pattern)
    (d d' : S.Design) : Prop where
  preserving : Preserving S sel d d'
  adds : Adds S p d d'

def Applies (S : Satisfaction L) (sel : List L.Pattern) :
    List L.Pattern → S.Design → S.Design → Prop
  | [], d, d' => d = d'
  | p :: ps, d, d' => ∃ mid, Adding S sel p d mid ∧ Applies S sel ps mid d'

theorem sequence_satisfied {L : Language} (S : Satisfaction L) (seq : List L.Pattern)
    {d d' : S.Design} (h : Applies S seq seq d d') :
    ∀ p, p ∈ seq → S.sat d' p
```

`Applies.preserving` is the chain lemma: a list of `Adding` steps is `Preserving` on `sel`, by induction and `Preserving.trans`. `Applies.satisfied` is the induction that each head holds at its `mid` and stays held because later steps preserve `sel` and the head is a member. `sequence_satisfied` is that lemma with `sel` and `rest` the same list.

`Preservation.lean` imports `Language` only. It does not import `Sequence`.

### What this unit leaves for later

`Selection` and `DownClosed` are the project language. `projects/` is empty, so U2 has no selection value. The seed sequence is the whole catalog in numeric order. U5 is the sequencer, and that is where a selection becomes data.

The existence theorem, "a finite acyclic selection has a valid sequence," needs an enumeration of `Pattern`. The signature's `Pattern` is an arbitrary type and carries no list. The unit check is `decide` on this seed, which has its own list.

`Instantiations/Software.lean` is U8.

## Module map

```text
lean/PatternLanguage/Language.lean                         Scale, Language, the two lemmas
lean/PatternLanguage/Sequence.lean                         indexBefore, orderOk, ValidSequence
lean/PatternLanguage/Preservation.lean                    Satisfaction, Run, Applies
lean/PatternLanguage/Instantiations/Buildings.lean        generated seed
scripts/catalog_to_lean.py                                 render and --check
tests/test_catalog_to_lean.py                              committed file matches render
.github/workflows/ci.yml                                   one step
README.md                                                  U2 paragraph
AGENTS.md                                                  Lean row and U2 section
docs/design/DESIGN.md                                      short U2 pointer after U1
```

`lean/lakefile.lean` stays. The glob `.submodules PatternLanguage` builds every new module, including `Preservation.lean`, which nothing imports. `lean/lake-manifest.json` stays `"packages": []`. `lean/lean-toolchain` stays `leanprover/lean4:v4.33.1`.

`catalog.py`, `gate.py`, the twelve JSON files, and the five schemas stay. The generator reads them.

Docs the implementer updates, in place:

- `README.md` — `catalog_to_lean.py`, the `--check` command, and `lake build` on the generated seed. Keep the number-and-name citation rule.
- `AGENTS.md` — `lean/` holds `Language`, `Sequence`, `Preservation`, and generated `Instantiations/Buildings.lean`. The empty-namespace sentence becomes the U0 history. The Mathlib ban stays.
- `docs/design/DESIGN.md` — a U2 section after U1: the laws live in `lean/PatternLanguage/`; the seed file is generated; `decide` proves numeric order; CI checks the file is current.

## Signatures

`scripts/catalog_to_lean.py`:

```python
def render(catalog: Catalog) -> str: ...

def main(argv: list[str] | None = None) -> int: ...
```

`render` reads `catalog.patterns` in numeric order even though `load_catalog` already sorts. For each pattern it emits one `Pat` constructor, one `number` arm, and one `scaleOf` arm (`town`, `building`, or `construction`). `smallerEdges` is the concatenation, over that same order, of `(q, p)` for `q` in `pattern.smaller`. `main` calls `load_catalog` and returns 1 without writing when the load raises `CatalogLoadError` or `catalog.ok` is false. Missing targets go to stderr as `missing target: <source> <field> <target>`, the validate script's line. Back-edges are not printed here.

The generated file starts with:

```lean
-- Generated by scripts/catalog_to_lean.py. Do not edit.
import PatternLanguage.Language
import PatternLanguage.Sequence

namespace PatternLanguage.Instantiations.Buildings
```

and ends with `end PatternLanguage.Instantiations.Buildings` plus a final newline. Constructors and edges are one per line. The render is byte-stable.

`Language.lean`, `Sequence.lean`, and `Preservation.lean` use `namespace PatternLanguage`. Their public names are `Scale`, `Language`, `patternNumberBound`, `scaleMono_of_edges`, `acyclicOfIncreasingNumber`, `indexBefore`, `orderOk`, `ValidSequence`, `Satisfaction`, `Preserving`, `Run`, `Adds`, `Adding`, `Applies`, and `sequence_satisfied`.

`catalog_to_lean.py` imports `load_catalog` and `CatalogLoadError`. It does not import `ifcopenshell` or `bpy`.

## Rationale

The unit check is a proof about twelve concrete edges, plus the signature those edges inhabit.

- The structure matches §2.6 field for field, including `WellFounded (fun q p => smaller q p)` and `smaller q p` for "q helps complete p". A Boolean adjacency matrix on the structure would be a different signature.
- `Pattern` stays a field. The generated file supplies one `BEq` instance so `idxOf?` works on `language.Pattern`.
- Edges are a `List (Pat × Pat)` because `List.all_eq_true` turns one `by decide` into `∀` over the list. A match on all constructor pairs is the same fact, larger, and no easier for `decide`.
- `acyclic` is the measure `253 - number`. Every schema number is at most 253, and every seed edge increases `number`, so the measure falls along `smaller`. That is `Subrelation.wf` and `InvImage.wf` of `Nat.lt_wfRel`. `omega` is used once, on three `Nat`s, inside `sub_lt_of_lt`.
- `scale_mono` is the same list fact for `≤` on `Scale`. The seed is `building` on every pattern, so each edge is `building ≤ building`. The comparison still runs, and a later town-scale target fails `decide`.
- `ValidSequence` is the index comparison on that list. `numericOrder_ok` is `by decide`. `numericOrder_valid` applies `List.all_eq_true`. Together they are "numeric order is a valid sequence, proved by `decide`."
- Preservation is the §2.6 paragraph: reflexive, transitive, and a run of preserving steps that each add one pattern ends with every pattern of the sequence satisfied. The proofs are induction on `Run` and on `List`. They quantify over `Prop` membership and need no `DecidableEq`.
- The generator owns the seed file. Hand-written lemmas own the laws. A hand edit of an edge fails `--check`. A regenerated downward edge fails `decide` inside `lake build`.
- `larger` is not a second Lean relation. One link has one direction.
- No Mathlib, no new Lake package, no `pl` command, no edit to `gate.py`, no project file.

## CI impact

`.github/workflows/ci.yml` gains one step after `uv run python scripts/validate_catalog.py` and before `leanprover/lean-action`:

```yaml
- run: uv run python scripts/catalog_to_lean.py --check
```

`lean-action` stays `lake-package-directory: lean`, `build: true`, `test: false`, `lint: false`, `use-mathlib-cache: false`. `uv.lock` stays. The manifest stays empty.

| Check | U2 result |
|---|---|
| `catalog_to_lean.py --check` | Exit 0. Stdout empty. Exit 1 and stderr `stale: lean/PatternLanguage/Instantiations/Buildings.lean` when the committed file differs. |
| `lake build` | Builds `Language`, `Sequence`, `Preservation`, and `Instantiations.Buildings`, including both `by decide` goals. |
| `uv run pytest` | `test_catalog_to_lean.py` asserts the committed file equals `render`. `test_lean_has_no_mathlib` still requires `packages == []` and no `Mathlib` string under `lean/`. |
| `validate_catalog.py` | Unchanged. `back-edges: 0` and `ok: 12 records`. |

`tests/test_boundaries.py` `test_ci_workflow_covers_gate_and_lean` gains:

```python
assert "uv run python scripts/catalog_to_lean.py --check" in workflow
```

`tests/test_catalog_to_lean.py` on the repo:

- `render(load_catalog(repo_root))` equals the committed `Buildings.lean` text
- the text contains `theorem numericOrder_ok` and `by decide`
- the text contains `(.p106, .p105)` and `(.p180, .p159)`
- the text contains `p105` and does not contain `South`

`--check` on the repo exits 0 with empty stdout and empty stderr. `test_u0_has_no_pl_command` stays.

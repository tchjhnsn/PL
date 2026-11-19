namespace PatternLanguage

/-- [D] Town is larger than building, and building is larger than construction. -/
inductive Scale
  | town
  | building
  | construction
deriving DecidableEq, Repr

/-- Rank of a scale. Town is 2, building is 1, construction is 0. -/
def Scale.rank : Scale → Nat
  | .town => 2
  | .building => 1
  | .construction => 0

instance : LE Scale where
  le a b := a.rank ≤ b.rank

instance (a b : Scale) : Decidable (a ≤ b) :=
  inferInstanceAs (Decidable (a.rank ≤ b.rank))

structure Language where
  /-- [P] Carrier chosen by the instantiation. -/
  Pattern : Type
  /-- [D] Scale of each pattern. -/
  scale : Pattern → Scale
  /-- [D] `smaller q p`: q is one of the smaller patterns that help complete p. -/
  smaller : Pattern → Pattern → Prop
  /-- [S] The link never goes up in scale. False when some pattern lists a
      larger-scale pattern among its smaller ones. -/
  scale_mono : ∀ p q, smaller q p → scale q ≤ scale p
  /-- [S] The link graph has no cycle. False when two patterns each help complete
      the other, directly or through a chain. -/
  acyclic : WellFounded (fun q p => smaller q p)

def edgeIncreases {α : Type} (number : α → Nat) (edges : List (α × α)) : Bool :=
  edges.all fun (q, p) => decide (number p < number q)

def edgeScaleMono {α : Type} (scale : α → Scale) (edges : List (α × α)) : Bool :=
  edges.all fun (q, p) => decide (scale q ≤ scale p)

def patternNumberBound : Nat := 253

theorem scaleMono_of_edges {α : Type} (scale : α → Scale) (edges : List (α × α))
    (h : edgeScaleMono scale edges = true) :
    ∀ p q, (q, p) ∈ edges → scale q ≤ scale p :=
  fun p q hmem => of_decide_eq_true ((List.all_eq_true).mp h (q, p) hmem)

private theorem sub_lt_of_lt {b p q : Nat} (hp : p ≤ b) (hq : q ≤ b) (hlt : p < q) :
    b - q < b - p := by omega

theorem acyclicOfIncreasingNumber {α : Type} (number : α → Nat) (bound : Nat)
    (edges : List (α × α))
    (hBound : ∀ a, number a ≤ bound)
    (hInc : edgeIncreases number edges = true) :
    WellFounded (fun q p => (q, p) ∈ edges) := by
  refine Subrelation.wf ?_ (InvImage.wf (fun a => bound - number a) Nat.lt_wfRel.wf)
  intro q p hmem
  exact sub_lt_of_lt (hBound p) (hBound q)
    (of_decide_eq_true ((List.all_eq_true).mp hInc (q, p) hmem))

end PatternLanguage

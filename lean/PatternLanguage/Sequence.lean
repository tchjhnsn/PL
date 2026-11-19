import PatternLanguage.Language

namespace PatternLanguage

def indexBefore {α : Type} [BEq α] (order : List α) (earlier later : α) : Bool :=
  match order.idxOf? earlier, order.idxOf? later with
  | some i, some j => decide (i < j)
  | _, _ => false

def orderOk {α : Type} [BEq α] (order : List α) (edges : List (α × α)) : Bool :=
  edges.all fun (q, p) => indexBefore order p q

/-- [D] Every smaller pattern appears after the pattern it completes. -/
def ValidSequence (L : Language) [BEq L.Pattern] (s : List L.Pattern) : Prop :=
  ∀ q p, L.smaller q p → indexBefore s p q = true

end PatternLanguage

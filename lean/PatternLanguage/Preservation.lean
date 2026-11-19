import PatternLanguage.Language

namespace PatternLanguage

structure Satisfaction (L : Language) where
  /-- [P] Whatever a later unit checks. -/
  Design : Type
  /-- [D] `sat d p` means pattern p holds of design d. -/
  sat : Design → L.Pattern → Prop

/-- [D] Patterns in `sel` that hold in `d` hold in `d'`.
False when one of them held before and fails after. -/
def Preserving {L : Language} (S : Satisfaction L) (sel : List L.Pattern)
    (d d' : S.Design) : Prop :=
  ∀ p, p ∈ sel → S.sat d p → S.sat d' p

theorem Preserving.refl {L : Language} (S : Satisfaction L) (sel : List L.Pattern)
    (d : S.Design) : Preserving S sel d d :=
  fun _ _ h => h

theorem Preserving.trans {L : Language} {S : Satisfaction L} {sel : List L.Pattern}
    {d mid final : S.Design} (h₁ : Preserving S sel d mid) (h₂ : Preserving S sel mid final) :
    Preserving S sel d final :=
  fun p hp hsat => h₂ p hp (h₁ p hp hsat)

/-- [D] `p` failed before and holds after.
False when `p` already held or still fails. -/
def Adds {L : Language} (S : Satisfaction L) (p : L.Pattern) (d d' : S.Design) : Prop :=
  ¬ S.sat d p ∧ S.sat d' p

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

structure Adding {L : Language} (S : Satisfaction L) (sel : List L.Pattern) (p : L.Pattern)
    (d d' : S.Design) : Prop where
  preserving : Preserving S sel d d'
  adds : Adds S p d d'

def Applies {L : Language} (S : Satisfaction L) (sel : List L.Pattern) :
    List L.Pattern → S.Design → S.Design → Prop
  | [], d, d' => d = d'
  | p :: ps, d, d' => ∃ mid, Adding S sel p d mid ∧ Applies S sel ps mid d'

theorem Applies.preserving {L : Language} (S : Satisfaction L) (sel : List L.Pattern)
    (rest : List L.Pattern) {d d' : S.Design} (h : Applies S sel rest d d') :
    Preserving S sel d d' := by
  induction rest generalizing d d' with
  | nil =>
    simp only [Applies] at h
    subst h
    exact Preserving.refl S sel d
  | cons _ _ ih =>
    simp only [Applies] at h
    obtain ⟨_mid, hadd, happ⟩ := h
    exact Preserving.trans hadd.preserving (ih happ)

theorem Applies.satisfied {L : Language} (S : Satisfaction L) (sel : List L.Pattern)
    (rest : List L.Pattern) {d d' : S.Design} (h : Applies S sel rest d d')
    (hsub : ∀ p, p ∈ rest → p ∈ sel) :
    ∀ p, p ∈ rest → S.sat d' p := by
  induction rest generalizing d d' with
  | nil =>
    intro p hp
    cases hp
  | cons q qs ih =>
    simp only [Applies] at h
    obtain ⟨mid, hadd, happ⟩ := h
    intro p hp
    have hpres : Preserving S sel mid d' := Applies.preserving S sel qs happ
    have hq : S.sat d' q := hpres q (hsub q List.mem_cons_self) hadd.adds.right
    rcases List.mem_cons.mp hp with rfl | hmem
    · exact hq
    · exact ih happ (fun r hr => hsub r (List.mem_cons_of_mem q hr)) p hmem

theorem sequence_satisfied {L : Language} (S : Satisfaction L) (seq : List L.Pattern)
    {d d' : S.Design} (h : Applies S seq seq d d') :
    ∀ p, p ∈ seq → S.sat d' p :=
  Applies.satisfied S seq seq h fun _ hp => hp

end PatternLanguage

import Lean

/-!
Original small examples accompanying the review. The physicalIndex expression
illustrates the tape convention in OAI.Combinatorics.MatroidCounting.CommonBases,
commit fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb. These declarations are independent
of the release library. They establish the finite arithmetic interfaces studied
in the paper; no declaration here imports or certifies the release endpoints.
-/

namespace InterfaceExamples

def physicalIndex (start m : Nat) (i : Fin m) : Nat :=
  start + 3 * (m - 1 - i.val) + 1

theorem physicalIndex_injective (start m : Nat) (i j : Fin m)
    (h : physicalIndex start m i = physicalIndex start m j) : i = j := by
  apply Fin.ext
  have hi := i.isLt
  have hj := j.isLt
  simp only [physicalIndex] at h
  omega

theorem physicalIndex_lt (start m B : Nat) (i : Fin m)
    (hB : start + 3 * m + 1 ≤ B) : physicalIndex start m i < B := by
  have hi := i.isLt
  simp only [physicalIndex]
  omega

def moment : Nat → (Nat → Nat) → (Nat → Nat) → Nat
  | 0, _, _ => 0
  | n + 1, counts, observable =>
      moment n counts observable + observable n * counts n

theorem moment_indicator (n : Nat) (counts : Nat → Nat) (j : Nat) :
    moment n counts (fun i => if i = j then 1 else 0) =
      if j < n then counts j else 0 := by
  induction n with
  | zero => simp [moment]
  | succ n ih =>
    by_cases h : j = n
    · subst j
      simp [moment, ih]
    · by_cases hj : j < n
      · have hjs : j < n + 1 := by omega
        simp [moment, ih, Ne.symm h, hj, hjs]
      · have hjs : ¬j < n + 1 := by omega
        simp [moment, ih, Ne.symm h, hj, hjs]

theorem all_observables_determine_counts (n : Nat) (counts other : Nat → Nat)
    (h : ∀ observable, moment n counts observable = moment n other observable)
    (j : Nat) (hj : j < n) : counts j = other j := by
  have witness := h (fun i => if i = j then 1 else 0)
  simpa [moment_indicator, hj] using witness

def flatCounts (_ : Nat) : Nat := 1
def concentratedCounts (i : Nat) : Nat := if i = 1 then 3 else 0

example : moment 3 flatCounts (fun _ => 1) =
    moment 3 concentratedCounts (fun _ => 1) := by decide

example : moment 3 flatCounts id = moment 3 concentratedCounts id := by decide

example : moment 3 flatCounts (fun i => if i = 0 then 1 else 0) ≠
    moment 3 concentratedCounts (fun i => if i = 0 then 1 else 0) := by decide

#print axioms physicalIndex_injective
#print axioms physicalIndex_lt
#print axioms moment_indicator
#print axioms all_observables_determine_counts

end InterfaceExamples

import OAI.Analysis.TraceCone.IdealTransport

/-!
An explanatory reuse of the actual upstream additive ideal correspondence.
The OAI modules are compiled without changing their source bytes.
-/

namespace ReviewReuse

open OAI.TraceConeClassification

universe u v w

variable {A : Type u} [NonUnitalCStarAlgebra A] [PartialOrder A] [StarOrderedRing A]
    {B : Type v} [NonUnitalCStarAlgebra B] [PartialOrder B] [StarOrderedRing B]
    {C : Type w} [NonUnitalCStarAlgebra C] [PartialOrder C] [StarOrderedRing C]

theorem compositeAdditive (e : ExtendedTrace A ≃ ExtendedTrace B)
    (f : ExtendedTrace B ≃ ExtendedTrace C)
    (he : ∀ x y, e (x.add y) = (e x).add (e y))
    (hf : ∀ x y, f (x.add y) = (f x).add (f y)) :
    ∀ x y, (e.trans f) (x.add y) = ((e.trans f) x).add ((e.trans f) y) := by
  intro x y
  change f (e (x.add y)) = (f (e x)).add (f (e y))
  rw [he, hf]

/-- Ideal transport composes using only additive equivalences of trace cones. -/
theorem additiveIdealTransport_comp (e : ExtendedTrace A ≃ ExtendedTrace B)
    (f : ExtendedTrace B ≃ ExtendedTrace C)
    (he : ∀ x y, e (x.add y) = (e x).add (e y))
    (hf : ∀ x y, f (x.add y) = (f x).add (f y))
    (I : ClosedIdeal A) :
    closedIdealOrderEquivOfAdditive (e.trans f) (compositeAdditive e f he hf) I =
      closedIdealOrderEquivOfAdditive f hf (closedIdealOrderEquivOfAdditive e he I) := by
  apply ClosedIdeal.weight_injective
  change (closedIdealEquivOfAdditive (e.trans f) _ I).weight =
    (closedIdealEquivOfAdditive f hf (closedIdealEquivOfAdditive e he I)).weight
  rw [closedIdealEquivOfAdditive_weight, closedIdealEquivOfAdditive_weight,
      closedIdealEquivOfAdditive_weight]
  rfl

#print axioms additiveIdealTransport_comp

end ReviewReuse

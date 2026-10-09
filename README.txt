PROOF ARCHITECTURE IN THE OPENAI LEAN LIBRARY
Representation, Locality, and Semantic Transport

Robin Gounder, Vaionex Corporation, robin@gounder.com
9 October 2026

This separate review studies six concrete mathematical interfaces in the
OpenAI Lean collection. Its contribution is source-level comparative analysis,
a preservation framework, and elementary explanatory examples. It distinguishes
established proof methods from their specific composition in the selected cases.
The tactic profile is a second central finding. The review relates the measured
differences from Mathlib to the division of proof work in compiler cost bounds,
analytic cancellation, and exact numerical certificates. Frequencies describe
written methods; source tracing explains their role in completed constructions.

READ
lean-proof-architecture.pdf: compiled manuscript.
main.tex and the other top-level .tex files: complete LaTeX source.
references.bib: cited references.
research/*/findings.*: case studies with declaration locations and scope.
research/discrete/evidence.json: 92 source excerpt records.
research/corpus-inventory.json: complete-tree totals and curated source hashes.
research/source/openai-math/: byte-identical selected upstream source files.
audit/citation-verification.json: primary bibliography records and DOI evidence.
audit/cross-review-*.json: internal reviews across case authors.
audit/full-manuscript-review.json: internal reader and novelty assessment.
audit/review-resolution.json: disposition of the initial review findings.
audit/publication-review-oct8.txt: mathematical category review and audit fixes.
audit/reading-flow-review-v1.1.1.txt: earlier reading-flow and organization review.
audit/depth-revision-review-2026-10-08.txt: earlier depth and verification review.
audit/paragraph-review-2026-10-08.txt: earlier paragraph-by-paragraph mathematical review.
audit/style-clarity-review-2026-10-09.json: style, notation, and evidence review for v1.6.0.
audit/release-audit-2026-10-09.txt: final reviewer-style category audit for v1.6.1.
research/method-survey/report.txt: current exploratory method-distribution report.
research/method-survey/comparison.png: module-balanced comparison chart.
research/method-survey/comparison.csv: pooled, balanced, and domain-adjusted rates.
figures/method-shift.pdf, .png and .svg: differences from the Mathlib baseline;
aligned marker pairs, no connectors or point-value annotations.
research/method-survey/shift-comparison.csv: exact rates and percentage-point shifts.
audit/publication-review-oct8.json: machine-readable revision/recheck record.
Edition 1.6.1: 35 pages, 47 references, 546 curated source
artifacts plus 800 separately sampled OpenAI modules, five compiled elementary
Lean lemmas, and a compiled corollary importing three unchanged upstream
trace-cone modules. The manuscript cites release v1.6.1 of this reproduction
repository. Earlier publication records remain in publication.json.
results/: original Lean compiler output and exact finite example results.

REPRODUCE
From this folder, with Python 3.11 or later:
  python reproduce/verify_sources.py
  python reproduce/verify_depth_evidence.py
  python reproduce/verify_method_profile.py
  python reproduce/audit_completeness.py
  python reproduce/verify_examples.py
  python reproduce/assemble_references.py
  python reproduce/build.py
  python reproduce/verify_manuscript.py
  python reproduce/package_review.py

The original Lean examples require elan and the exact toolchain:
  elan toolchain install leanprover/lean4:v4.34.1
The examples import only Lean, with no external package dependency.

For the actual upstream reuse experiment, prepare a separate pinned Mathlib
checkout in an empty sibling directory (Git, Lake, and network required):
  python reproduce/prepare_upstream_reuse.py ../mathlib-reuse
  python reproduce/verify_upstream_reuse.py ../mathlib-reuse
The experiment compiles Basic, FiniteIdeal, IdealTransport, and UpstreamReuse.
Its axiom report is [propext, Classical.choice, Quot.sound]. See README.md.

The exploratory method survey compares 800 uniformly sampled OpenAI modules
with 8,070 mathematical Mathlib modules at the pinned dependency revision.
Its verifier checks sample membership, all sampled source bytes, extraction
fixtures, the 40-body manual validation cohort, and retained summary counts.
To regenerate the full source profile using the same Mathlib checkout:
  python reproduce/profile_lean_methods.py ../mathlib-reuse
  python reproduce/verify_method_profile.py
  python reproduce/audit_completeness.py
  python reproduce/summarize_method_profile.py
The joint analysis retains 69 cell weights and rates, bootstrap intervals,
and a generated Table 3. Its module/body measure reconciles against a direct
calculation. Arithmetic remains +22.8 pp after joint subject/length controls;
tactic mode and local claims become +10.4 and +5.8 pp.
Add --plot to the final command to regenerate PNG/SVG/PDF comparison charts,
including the embedded shift figure
(optional matplotlib dependency). The survey reads source without elaboration.
Its categories overlap; module-balanced and pooled rates have different units.
The retained data include the exploratory design, complete path population,
800 source blobs, feature definitions, CSV tables, bootstrap summaries, and
the initial manual inspection with corrected extraction classifications.

The manuscript build requires pdfLaTeX, BibTeX, and the packages in main.tex.
Python packages: requests, bibtexparser, pypdf. The optional render_review.py
also uses Pillow and Poppler's pdftoppm. Retained DOI metadata makes bibliography
assembly offline unless a new DOI is added. build.py uses a temporary directory.

All six cases were studied by static declaration/dependency analysis. The
trace-cone interface additionally has the targeted compilation and reuse
experiment above. The other five cases and Comparator were not compiled in
that experiment. The complete corpus inventory was obtained by git ls-tree
-r HEAD at the stated commit. The package retains each selected endpoint's
transitive OAI import closure; evidence ledgers record the deeper reading.

SOURCE AND RIGHTS
OpenAI corpus revision: fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb.
The separate Comparator and Mathlib revisions are recorded in their research
manifests. Original upstream licenses remain applicable; see THIRD-PARTY.txt.
Original reproduction scripts and Lean examples are MIT licensed (LICENSE-CODE).
Copyright Robin Gounder. A manuscript reuse license has not been selected.

Public source repository: https://github.com/Kohze/lean-proof-architecture-review.
SSRN submission identifiers are recorded separately when available. Internal cross-review is distinct from external peer review.

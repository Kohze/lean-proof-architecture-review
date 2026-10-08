PROOF ARCHITECTURE IN THE OPENAI LEAN LIBRARY
Representation, Locality, and Semantic Transport

Robin Gounder, Vaionex Corporation, robin@gounder.com
8 October 2026

This separate review studies six concrete mathematical interfaces in the
OpenAI Lean collection. Its contribution is source-level comparative analysis,
a preservation framework, and elementary explanatory examples. It distinguishes
established proof methods from their specific composition in the selected cases.

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
audit/publication-review-oct8.txt: latest category review and audit fixes.
audit/publication-review-oct8.json: machine-readable revision/recheck record.
Current edition v1.1.0: 23 pages, 38 references, 168 retained source files,
five compiled original Lean lemmas, and an exact 640/1024 success fixture.
results/: original Lean compiler output and exact finite example results.

REPRODUCE
From this folder, with Python 3.11 or later:
  python reproduce/verify_sources.py
  python reproduce/verify_examples.py
  python reproduce/assemble_references.py
  python reproduce/build.py
  python reproduce/verify_manuscript.py
  python reproduce/package_review.py

The original Lean examples require elan and the exact toolchain:
  elan toolchain install leanprover/lean4:v4.34.1
The examples import only Lean, with no external package dependency.

The manuscript build requires pdfLaTeX, BibTeX, and the packages in main.tex.
Python packages: requests, bibtexparser, pypdf. The optional render_review.py
also uses Pillow and Poppler's pdftoppm. Retained DOI metadata makes bibliography
assembly offline unless a new DOI is added. build.py uses a temporary directory.

The source cases were studied by static declaration/dependency analysis.
Executable verification records concern the review's original small examples;
they are not build logs for the upstream headline theorems. The complete corpus
inventory was obtained by git ls-tree -r HEAD at the stated commit. The curated
source set is the material retained for reproducible case inspection.

SOURCE AND RIGHTS
OpenAI corpus revision: fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb.
The separate Comparator and Mathlib revisions are recorded in their research
manifests. Original upstream licenses remain applicable; see THIRD-PARTY.txt.
Original reproduction scripts and Lean examples are MIT licensed (LICENSE-CODE).
Copyright Robin Gounder. A manuscript reuse license has not been selected.

Public source repository: https://github.com/Kohze/lean-proof-architecture-review.
SSRN submission identifiers are recorded separately when available. Internal cross-review is distinct from external peer review.

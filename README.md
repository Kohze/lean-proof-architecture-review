# Proof Architecture in the OpenAI Lean Library

**Representation, Locality, and Semantic Transport**  
Robin Gounder · Vaionex Corporation · 8 October 2026

[Read the manuscript](lean-proof-architecture.pdf) · [Citation metadata](CITATION.cff) · [Reproduction instructions](#reproduce)

This source-driven review examines six mathematical interfaces in the OpenAI Lean collection: common-base counting, graph switch chains, the symmetric Mahler inequality, the complete Crouzeix bound, extended trace cones, and marked character-variety constructions. It studies the preservation theorems that connect representations and make the next mathematical operation possible. Original elementary examples explain tape-index arithmetic, normalized finite laws, and the composition of sampling loss with exact physical-tape success counts.

**Audited source edition v1.1.0:** a 23-page manuscript with 38 references (26 scholarly works and 12 source or software records). The package includes internal source, citation, reader, and visual audits. Internal review is distinct from external peer review.

Repository: [Kohze/lean-proof-architecture-review](https://github.com/Kohze/lean-proof-architecture-review).

The [publication review](audit/publication-review-oct8.txt) gives category ratings, resolved findings, and the scope of the verification. Five original Lean lemmas compile with Lean 4.34.1; exhaustive finite checks include a tight 640/1024 successful-tape example.

## Contents

| Location | Contents |
| --- | --- |
| `lean-proof-architecture.pdf` | Compiled manuscript |
| `main.tex`, other top-level `.tex` files, `references.bib` | Complete manuscript source |
| `reproduce/` | Original Lean examples and Python reproduction tools |
| `results/` | Original example compiler output and exact finite checks |
| `research/corpus-inventory.json` | Corpus revision, inventory method, and curated-source hashes |
| `research/source/openai-math/` | Selected upstream files with their original paths and licenses |
| `research/*/findings.*`, `research/discrete/evidence.json` | Source locations and case evidence |
| `research/bibliography/` | Retained publisher DOI metadata |
| `audit/` | Build, source-integrity, citation, and internal review records |

The reviewed OpenAI corpus is pinned to commit [`fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb`](https://github.com/openai/math/tree/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb). The package retains 168 curated files from that revision. Separate Mathlib and Comparator revisions are recorded in the research manifests. The curated source set supports inspection; it is not a complete upstream checkout.

## Reproduce

Run these commands from the folder containing `main.tex` and `reproduce/`, with Python 3.11 or later:

```sh
python -m pip install -r requirements.txt
python reproduce/verify_sources.py
```

The original Lean examples require [elan](https://github.com/leanprover/elan) and the exact toolchain below. They import only Lean and have no Mathlib dependency.

```sh
elan toolchain install leanprover/lean4:v4.34.1
python reproduce/verify_examples.py
```

`verify_examples.py` compiles `InterfaceExamples.lean`, checks the five reported axiom lists, and runs the exhaustive finite Python examples. The verification records describe these original explanatory examples. The six upstream case studies were reviewed through static source analysis; the workflow does not compile their headline theorems or run Comparator on them.

For the manuscript, install pdfLaTeX, BibTeX, and the packages named in `main.tex`. On Ubuntu, the workflow uses `texlive-latex-base`, `texlive-latex-extra`, `texlive-fonts-recommended`, and `lmodern`.

```sh
python reproduce/assemble_references.py
python reproduce/build.py
python reproduce/verify_manuscript.py
```

Retained DOI metadata allows bibliography assembly without new metadata requests for the existing references. `build.py` uses a temporary build directory and copies the PDF and logs back into this folder. `verify_manuscript.py` checks citation coverage, duplicate labels, retained DOI/title identities, LaTeX diagnostics, and PDF structure. It checks the rebuilt PDF's content and structure; byte-identical PDFs across TeX installations are not required. Keep `README.txt`, which is checked by that script.

The GitHub workflow runs these curated-source, original-example, bibliography, and PDF checks on pushes and pull requests. It uploads fresh verification records and the rebuilt PDF as workflow artifacts. A successful run has the scope described above.

To create a source archive and a separate PDF copy:

```sh
python reproduce/package_review.py
```

In a standalone checkout, these appear under `output/releases/` and `output/pdf/`. Optional page images and contact sheets require Pillow and Poppler's `pdftoppm`:

```sh
python -m pip install Pillow
python reproduce/render_review.py
```

The renderer writes to `tmp/pdfs/lean-proof-architecture/` in a standalone checkout. When the manuscript folder is nested immediately under a folder named `papers`, these two tools retain the original workspace output layout instead. Research extraction scripts retain the original discovery-workspace paths and are not part of the portable reproduction commands above.

## Cite

Use the scholarly `preferred-citation` in [CITATION.cff](CITATION.cff), or:

```bibtex
@article{gounder2026leanproofarchitecture,
  author = {Gounder, Robin},
  title = {Proof Architecture in the OpenAI Lean Library: Representation, Locality, and Semantic Transport},
  year = {2026},
  note = {Manuscript, 8 October 2026},
  url = {https://github.com/Kohze/lean-proof-architecture-review}
}
```

## Rights and attribution

Original reproduction scripts, Lean examples, and their associated documentation are MIT licensed under [LICENSE-CODE](LICENSE-CODE). This code license does not license the manuscript. The manuscript is copyright © 2026 Robin Gounder; a manuscript reuse license has not been selected.

Curated OpenAI files retain the upstream Apache License 2.0 and included license texts. Other reference materials retain their respective rights. See [THIRD-PARTY.txt](THIRD-PARTY.txt).

The manuscript's dedicated disclosure states that OpenAI Codex agents contributed substantially to source discovery, literature synthesis, and mathematical exposition.

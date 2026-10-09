# Proof Architecture in the OpenAI Lean Library

**Representation, Locality, and Semantic Transport**  
Robin Gounder · Vaionex Corporation · 8 October 2026

[Read the manuscript](lean-proof-architecture.pdf) · [Citation metadata](CITATION.cff) · [Reproduction instructions](#reproduce)

This source-driven review examines six mathematical interfaces in the OpenAI Lean collection: common-base counting, graph switch chains, the symmetric Mahler inequality, the complete Crouzeix bound, extended trace cones, and marked character-variety constructions. It studies the preservation theorems that connect representations and make the next mathematical operation possible. Original elementary examples explain tape-index arithmetic, normalized finite laws, and the composition of sampling loss with exact physical-tape success counts.

Its second central finding is a measured difference in proof-writing practice relative to Mathlib. The survey and case studies connect greater use of tactic blocks, arithmetic discharge, and intermediate claims to the division of proof work: mathematical interfaces organize the obligations that established Lean tactics resolve. Compiler cost bounds and the Crouzeix scalar cancellation provide concrete source-traced examples. The comparison describes completed proof constructions and library profiles; testing effects on completion rates or development effort requires matched tasks and outcome measurements.

The [paragraph and mathematical review](audit/paragraph-review-2026-10-08.txt) records checks and changes for all 161 original manuscript blocks, with additional entries for the new mathematical and statistical analysis. Earlier audits remain records of their respective editions.

**Edition 1.6.0, 9 October 2026:** a 35-page manuscript with 47 references (32 scholarly works and 15 source or software records). The [style and clarity review](audit/style-clarity-review-2026-10-09.json) records the revised captions, Lean listings, notation, and Figure 1. A new discussion distinguishes proof generation, simplification, and explanation, and frames possible automation advantages as testable workflow hypotheses. The edition includes the previously local joint subject/length analysis, detailed source evidence, and reproduction data. Earlier audits and the public v1.1.1 release document earlier editions.

The [method-survey report](research/method-survey/report.txt), [comparison chart](research/method-survey/comparison.png), and [data table](research/method-survey/comparison.csv) explain the method distribution. Module-balanced rates give equal weight to each proof-bearing module; pooled rates expose the concentration of exact numerical certificates. These lexical measurements describe the use of established Lean devices. The six case studies supply the mathematical interpretation.

Figure 1 in the manuscript displays [differences from the Mathlib baseline](figures/method-shift.png) in percentage points. Hollow markers show the full comparison; filled markers show the shared-domain comparison with a standardized Mathlib baseline. The [figure data](research/method-survey/shift-comparison.csv) retain the absolute rates and both differences. The two markers for each feature share the same height; they are separate estimates relative to the zero baseline, with no connecting lines or value annotations. Vector [PDF](figures/method-shift.pdf) and [SVG](figures/method-shift.svg) versions are included for reuse. Table 3 adds the [joint subject/length comparison](research/method-survey/joint-comparison.csv); its [cell-level record](research/method-survey/joint-standardization.json) preserves weights, conditional rates, and bootstrap intervals. The arithmetic/algebra difference remains +22.8 percentage points, while tactic mode and local claims become +10.4 and +5.8 points. Length can itself reflect proof style, so this is a descriptive comparison.

Reproduction repository: [Kohze/lean-proof-architecture-review](https://github.com/Kohze/lean-proof-architecture-review). The manuscript cites the versioned [v1.6.0 reproduction edition](https://github.com/Kohze/lean-proof-architecture-review/releases/tag/v1.6.0).

The [depth revision review](audit/depth-revision-review-2026-10-08.txt) records the earlier depth analysis and verification scope. The [mathematical publication review](audit/publication-review-oct8.txt) and [reading-flow review](audit/reading-flow-review-v1.1.1.txt) document earlier editions. Five elementary Lean lemmas compile with Lean 4.34.1; exhaustive finite checks include a tight 640/1024 successful-tape example. A separate experiment compiles three unchanged upstream trace-cone modules and the ideal-transport composition corollary.

## Contents

| Location | Contents |
| --- | --- |
| `lean-proof-architecture.pdf` | Compiled manuscript |
| `figures/` | Embedded vector shift figure and reusable PDF, SVG, and PNG versions |
| `main.tex`, other top-level `.tex` files, `references.bib` | Complete manuscript source |
| `reproduce/` | Original Lean examples and Python reproduction tools |
| `results/` | Original example compiler output and exact finite checks |
| `research/corpus-inventory.json` | Corpus revision, inventory method, and curated-source hashes |
| `research/source/openai-math/` | Selected upstream files with their original paths and licenses |
| `research/*/findings.*`, `research/discrete/evidence.json` | Source locations and case evidence |
| `research/depth/` | Six transitive OAI import closures and 21 additional proof-body evidence records |
| `research/method-survey/` | Population, 800 sampled source modules, extracted-body tables, summaries, chart, and manual validation |
| `research/bibliography/` | Retained publisher DOI metadata |
| `audit/` | Build, source-integrity, citation, and internal review records |

The reviewed OpenAI corpus is pinned to commit [`fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb`](https://github.com/openai/math/tree/fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb). The package retains 546 source artifacts from that revision, including all 518 unique OAI modules in the six selected endpoint import closures. Separate Mathlib and Comparator revisions are recorded in the research manifests. Retention makes dependencies available for inspection; the evidence ledgers identify the passages analyzed in depth.

## Reproduce

Run these commands from the folder containing `main.tex` and `reproduce/`, with Python 3.11 or later:

```sh
python -m pip install -r requirements.txt
python reproduce/verify_sources.py
python reproduce/verify_depth_evidence.py
python reproduce/verify_method_profile.py
python reproduce/audit_completeness.py
```

The original Lean examples require [elan](https://github.com/leanprover/elan) and the exact toolchain below. They import only Lean and have no Mathlib dependency.

```sh
elan toolchain install leanprover/lean4:v4.34.1
python reproduce/verify_examples.py
```

`verify_examples.py` compiles `InterfaceExamples.lean`, checks the five reported axiom lists, and runs the exhaustive finite Python examples. `verify_depth_evidence.py` checks the 21 detailed evidence spans and every pinned OpenAI source hyperlink in the manuscript against retained files and valid line ranges. The mathematical interpretations in the ledgers come from source reading.

The upstream reuse experiment requires a separate Mathlib checkout, Git, Lake, and network access to prepare the targeted dependency cache. From this manuscript folder, choose an empty sibling directory for the checkout:

```sh
python reproduce/prepare_upstream_reuse.py ../mathlib-reuse
python reproduce/verify_upstream_reuse.py ../mathlib-reuse
```

The preparation script fetches Mathlib revision `d13f23b723b8a846827a245b89c10fc7d3f11612` and downloads the cache for the imports used by the three OAI modules. The verification script copies their unchanged source bytes, compiles `Basic`, `FiniteIdeal`, and `IdealTransport`, then compiles `UpstreamReuse.lean`. Its axiom report is `[propext, Classical.choice, Quot.sound]`. The logs and hashes are retained under `results/upstream-reuse-*`. This experiment checks one concrete reuse interface; the other five case studies use static source analysis. Comparator is described from its source.

The corpus survey reads source without elaboration. Its retained population list and seed reproduce sample membership, and the verifier checks all 800 sampled source blobs, the extraction fixtures, 40 manually inspected cases, and pooled and module-balanced count reconciliation. To regenerate the full profile, use the same pinned Mathlib checkout:

```sh
python reproduce/profile_lean_methods.py ../mathlib-reuse
python reproduce/verify_method_profile.py
python reproduce/audit_completeness.py
python reproduce/summarize_method_profile.py
```

`audit_completeness.py` regenerates the joint cell data, intervals, manuscript table, and directory-family sensitivity checks from the retained proof table. It also reconciles the cell formula against a direct module/body calculation. The final command generates the report, original CSV comparisons, and absolute-rate table from `summary.json`. Add `--plot` to regenerate the PNG, SVG, and PDF charts, including the embedded shift figure, after installing `matplotlib`. The retained figure is a build input, so building the manuscript itself does not require Matplotlib. The initial manual inspection and corrected classifications are retained separately. Features overlap, and module balancing was added as an exploratory sensitivity analysis after observing large certificate batches. Domain and length comparisons are descriptive controls rather than comparisons of identical mathematical tasks.

For the manuscript, install pdfLaTeX, BibTeX, and the packages named in `main.tex`. On Ubuntu, the workflow uses `texlive-latex-base`, `texlive-latex-extra`, `texlive-fonts-recommended`, and `lmodern`.

```sh
python reproduce/assemble_references.py
python reproduce/build.py
python reproduce/verify_manuscript.py
```

Retained DOI metadata allows bibliography assembly without new metadata requests for the existing references. `build.py` uses a temporary build directory and copies the PDF and logs back into this folder. `verify_manuscript.py` checks citation coverage, duplicate labels, retained DOI/title identities, LaTeX diagnostics, and PDF structure. It checks the rebuilt PDF's content and structure; byte-identical PDFs across TeX installations are not required. Keep `README.txt`, which is checked by that script.

The GitHub workflow runs the curated-source, evidence-locator, method-survey, joint-standardization, elementary-example, bibliography, and PDF checks on pushes and pull requests. It uploads fresh verification records and the rebuilt PDF as workflow artifacts. Full survey regeneration and the optional Mathlib reuse experiment have separate commands and retained local evidence.

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
  note = {Manuscript, 9 October 2026; edition 1.6.0},
  url = {https://github.com/Kohze/lean-proof-architecture-review}
}
```

## Rights and attribution

Original reproduction scripts, Lean examples, and their associated documentation are MIT licensed under [LICENSE-CODE](LICENSE-CODE). This code license does not license the manuscript. The manuscript is copyright © 2026 Robin Gounder; a manuscript reuse license has not been selected.

Curated OpenAI files retain the upstream Apache License 2.0 and included license texts. Other reference materials retain their respective rights. See [THIRD-PARTY.txt](THIRD-PARTY.txt).

The manuscript's dedicated disclosure states that OpenAI Codex agents contributed substantially to source discovery, literature synthesis, and mathematical exposition.

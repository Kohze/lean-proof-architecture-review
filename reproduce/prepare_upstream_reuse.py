"""Prepare a separate pinned Mathlib checkout and its targeted dependency cache.

Usage: python reproduce/prepare_upstream_reuse.py <empty-directory-or-pinned-checkout>
Requires Git, elan/Lean 4.34.1, Lake, and network access. Existing checkouts
must already be at the recorded revision and have no tracked modifications.
"""
from pathlib import Path
import subprocess
import sys

REV = 'd13f23b723b8a846827a245b89c10fc7d3f11612'
TARGETS = [
    'Mathlib/Analysis/CStarAlgebra/ContinuousFunctionalCalculus/Order.lean',
    'Mathlib/Analysis/SpecificLimits/Basic.lean',
    'Mathlib/Topology/Semicontinuity/Basic.lean',
    'Mathlib/Tactic/FunProp.lean',
    'Mathlib/Tactic/Linarith.lean',
    'Mathlib/Tactic/Positivity.lean',
    'Mathlib/Tactic/NoncommRing.lean',
    'Mathlib/Analysis/CStarAlgebra/ApproximateUnit.lean',
    'Mathlib/Analysis/CStarAlgebra/ContinuousFunctionalCalculus/Range.lean',
]


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Pass an empty directory or a checkout at the pinned Mathlib revision.')
    target = Path(sys.argv[1]).resolve()
    target.mkdir(parents=True, exist_ok=True)
    if not (target / '.git').exists():
        assert not any(target.iterdir()), 'A new checkout requires an empty directory.'
        for command in [
            ['git', 'init'],
            ['git', 'remote', 'add', 'origin', 'https://github.com/leanprover-community/mathlib4.git'],
            ['git', 'fetch', '--depth', '1', 'origin', REV],
            ['git', '-c', 'core.longpaths=true', 'checkout', '--detach', REV],
        ]:
            subprocess.run(command, cwd=target, check=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=target, text=True).strip()
    assert revision == REV, revision
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=target, check=True)
    assert (target / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
    subprocess.run(['lake', 'exe', 'cache', 'get', *TARGETS], cwd=target, check=True)
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=target, check=True)
    print(f'Pinned Mathlib and targeted dependencies ready: {target}')


if __name__ == '__main__':
    main()

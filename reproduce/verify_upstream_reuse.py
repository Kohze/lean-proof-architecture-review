"""Compile a real OAI interface and its compositional reuse in pinned Mathlib.

Pass the path to a Mathlib checkout at the recorded revision with its targeted
cache populated. This script adds only untracked OAI source and the example;
it does not alter Mathlib's tracked files or the upstream OAI source bytes.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

PAPER = Path(__file__).resolve().parents[1]
REV = 'd13f23b723b8a846827a245b89c10fc7d3f11612'
OAI = 'fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb'


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Pass the prepared pinned Mathlib checkout directory.')
    checkout = Path(sys.argv[1]).resolve()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    assert revision == REV, revision
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=checkout, check=True)
    assert (checkout / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.34.1'
    records, logs, sources = [], [], {}
    source = PAPER / 'research/source/openai-math/lean'
    env = dict(os.environ)
    env['LEAN_PATH'] = str(checkout) + os.pathsep + env.get('LEAN_PATH', '')
    for module in ['Basic', 'FiniteIdeal', 'IdealTransport']:
        rel = Path('OAI/Analysis/TraceCone') / (module + '.lean')
        target = checkout / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / rel, target)
        sources[rel.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        command = ['lake', 'env', 'lean', '-DautoImplicit=false', '-o',
                   str(rel.with_suffix('.olean')), str(rel)]
        run = subprocess.run(command, cwd=checkout, env=env, capture_output=True)
        text = (run.stdout + run.stderr).decode('utf-8', errors='replace')
        logs.append('COMMAND: ' + ' '.join(command) + '\n' + text)
        records.append({'module': rel.as_posix(), 'exit_code': run.returncode})
        print(module, 'exit', run.returncode, flush=True)
        if run.returncode:
            print(text)
            break
    else:
        shutil.copy2(PAPER / 'reproduce/UpstreamReuse.lean', checkout / 'UpstreamReuse.lean')
        command = ['lake', 'env', 'lean', '-DautoImplicit=false', 'UpstreamReuse.lean']
        run = subprocess.run(command, cwd=checkout, env=env, capture_output=True)
        text = (run.stdout + run.stderr).decode('utf-8', errors='replace')
        logs.append('COMMAND: ' + ' '.join(command) + '\n' + text)
        records.append({'module': 'UpstreamReuse.lean', 'exit_code': run.returncode})
        print(text, flush=True)
    results = PAPER / 'results'
    (results / 'upstream-reuse-compiler.log').write_text('\n'.join(logs), encoding='utf-8')
    success = len(records) == 4 and all(r['exit_code'] == 0 for r in records)
    axioms = [line for line in '\n'.join(logs).splitlines() if 'depends on axioms:' in line]
    if success:
        assert 'warning:' not in '\n'.join(logs), 'Compiler warnings require review.'
        assert len(axioms) == 1 and 'sorryAx' not in axioms[0]
        assert axioms[0].endswith('[propext, Classical.choice, Quot.sound]'), axioms
    report = {'status': 'passed' if success else 'failed', 'oai_commit': OAI,
              'mathlib_revision': REV, 'toolchain': 'leanprover/lean4:v4.34.1',
              'commands': records, 'unmodified_upstream_source_sha256': sources,
              'example_sha256': hashlib.sha256((PAPER / 'reproduce/UpstreamReuse.lean').read_bytes()).hexdigest(),
              'reported_axioms': axioms,
              'scope': 'Three TraceCone modules plus one compositional corollary; other five cases and Comparator were not compiled by this experiment.'}
    (results / 'upstream-reuse-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if not success:
        raise SystemExit(1)
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=checkout, check=True)


if __name__ == '__main__':
    main()

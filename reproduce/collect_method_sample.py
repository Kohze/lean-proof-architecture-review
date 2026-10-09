"""Retain a deterministic probability sample of the OAI mathematical source.

Usage: python reproduce/collect_method_sample.py <complete-git-tree.json>
The supplied inventory must have the reviewed commit and complete tree.
Sample membership is fixed by SHA-256 ranking of seed + NUL + path.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import sys
import time
import requests

PAPER = Path(__file__).resolve().parents[1]
OUT = PAPER / 'research/method-survey'
COMMIT = 'fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb'
SEED = 'lean-method-profile-2026-10-08-v1'
SAMPLE_SIZE = 800


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    tree_path = Path(sys.argv[1]).resolve()
    tree = json.loads(tree_path.read_text(encoding='utf-8'))
    assert tree['commit'] == COMMIT and tree['truncated'] is False
    population = sorted((e['path'], e['sha']) for e in tree['tree']
                        if e['type'] == 'blob' and e['path'].startswith('lean/OAI/')
                        and e['path'].endswith('.lean'))
    assert len(population) == 122457
    ranked = sorted(population, key=lambda e: sha256((SEED + '\0' + e[0]).encode()))
    selected = ranked[:SAMPLE_SIZE]
    OUT.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['path', 'git_blob_sha1'])
    writer.writerows(population)
    population_data = stream.getvalue().encode('utf-8')
    (OUT / 'population.csv.gz').write_bytes(gzip.compress(population_data, mtime=0))
    plan = {
        'date': '2026-10-08', 'oai_commit': COMMIT,
        'mathlib_commit': 'd13f23b723b8a846827a245b89c10fc7d3f11612',
        'population': 'All tracked .lean blobs strictly under lean/OAI/, excluding challenges, build files and the umbrella import file.',
        'population_modules': len(population), 'unique_population_blobs': len({sha for _, sha in population}),
        'inventory_sha256': sha256(tree_path.read_bytes()), 'population_csv_sha256': sha256(population_data),
        'selection': 'Lowest SHA-256 ranks of UTF-8(seed + NUL + path); no selection on observed contents.',
        'seed': SEED, 'sample_size': SAMPLE_SIZE, 'replacement': False,
        'unit': 'Source module sampled with equal probability; theorem/lemma bodies nested within modules.',
        'primary_features': ['Proof mode: top-level by / term with nested by / term only',
                             'Rewrite and simplification tokens', 'Arithmetic and algebra automation tokens',
                             'Search automation tokens', 'Case splitting and induction tokens',
                             'Extensionality and congruence tokens', 'Local claims or calculation chains',
                             'Finite decision tokens', 'Restricted simplification: simp/simpa only',
                             'Proof-body nonempty line counts', 'Named theorem/lemma bodies per source module'],
        'baseline': 'Tracked Mathlib/*.lean mathematical modules at the recorded dependency revision; exclude infrastructure roots Tactic, Lean, Util, Testing and umbrella files.',
        'controls': ['Raw baseline', 'Reweight common top-level mathematical domains to sampled OAI proof-body shares',
                     'Compare proof-length bands within the same common-domain cohorts'],
        'uncertainty': 'Bootstrap OAI source modules as clusters; named proof bodies are not treated as independent trials.',
        'interpretation': 'Lexical source features, not an elaborated tactic trace, proof-time profile, semantic method classification or novelty detector.',
        'selected_paths': [p for p, _ in selected],
    }
    # This is written before fetching or profiling any sampled contents.
    (OUT / 'design.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    curated = PAPER / 'research/source/openai-math'

    def retain(entry):
        path, blob = entry
        destination = OUT / 'source' / path
        if destination.exists():
            data = destination.read_bytes()
        elif (curated / path).exists():
            data = (curated / path).read_bytes()
        else:
            for attempt in range(4):
                try:
                    response = requests.get(f'https://raw.githubusercontent.com/openai/math/{COMMIT}/{path}', timeout=35)
                    response.raise_for_status()
                    data = response.content
                    break
                except requests.RequestException:
                    if attempt == 3:
                        raise
                    time.sleep(1 + attempt)
        actual_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert actual_blob == blob, path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(data)
        return {'path': path, 'domain': path.split('/')[2], 'git_blob_sha1': blob,
                'sha256': sha256(data), 'bytes': len(data),
                'rank': sha256((SEED + '\0' + path).encode()),
                'archived_path': destination.relative_to(PAPER).as_posix()}

    records = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        pending = [executor.submit(retain, entry) for entry in selected]
        for future in as_completed(pending):
            records.append(future.result())
            if len(records) % 80 == 0:
                print(f'Byte-verified sampled modules: {len(records)}/{SAMPLE_SIZE}', flush=True)
    records.sort(key=lambda r: r['rank'])
    manifest = {'commit': COMMIT, 'seed': SEED, 'files': records,
                'source_bytes': sum(r['bytes'] for r in records),
                'status': 'All selected files retained and verified against pinned Git blob identities.'}
    (OUT / 'sample-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sampled_modules': len(records), 'source_bytes': manifest['source_bytes']}), flush=True)


if __name__ == '__main__':
    main()

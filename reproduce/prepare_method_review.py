"""Retain a stratified boundary/feature review set for human source inspection."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import sys

PAPER = Path(__file__).resolve().parents[1]
OUT = PAPER / 'research/method-survey'


def main():
    mathlib = Path(sys.argv[1]).resolve()
    proofs = list(csv.DictReader(io.StringIO(gzip.decompress((OUT / 'proofs.csv.gz').read_bytes()).decode())))
    manifest = {e['path']: e for e in json.loads((OUT / 'sample-manifest.json').read_text())['files']}
    features = list(json.loads((OUT / 'summary.json').read_text())['features'])
    groups = [
        ('short_tactic', lambda p: p['mode'] == 'tactic' and int(p['body_lines']) <= 3),
        ('medium_tactic', lambda p: p['mode'] == 'tactic' and 4 <= int(p['body_lines']) <= 10),
        ('long_tactic', lambda p: p['mode'] == 'tactic' and int(p['body_lines']) >= 11),
        ('term', lambda p: p['mode'] == 'term_only'),
        ('mixed_term', lambda p: p['mode'] == 'term_with_tactic'),
    ]
    cases = []
    for corpus in ['OAI', 'Mathlib']:
        used_files = set()
        for group, predicate in groups:
            candidates = [p for p in proofs if p['corpus'] == corpus and predicate(p)]
            candidates.sort(key=lambda p: hashlib.sha256(('review-v1\0' + p['path'] + '\0' + p['line']).encode()).hexdigest())
            chosen = []
            for p in candidates:
                if p['path'] not in used_files:
                    chosen.append(p); used_files.add(p['path'])
                if len(chosen) == 4:
                    break
            assert len(chosen) == 4
            for p in chosen:
                source = PAPER / manifest[p['path']]['archived_path'] if corpus == 'OAI' else mathlib / p['path']
                lines = source.read_text(encoding='utf-8-sig').splitlines()
                first, last = int(p['line']), int(p['end_line'])
                selected_lines = list(range(first, min(last + 4, len(lines) + 1)))
                if len(selected_lines) > 28:
                    selected_lines = selected_lines[:16] + selected_lines[-9:]
                excerpt = []
                previous = None
                for n in selected_lines:
                    if previous is not None and n > previous + 1:
                        excerpt.append('... middle omitted ...')
                    line = lines[n - 1]
                    if len(line) > 260:
                        line = line[:150] + ' ... [long line abbreviated] ... ' + line[-100:]
                    excerpt.append(f'{n}: {line}')
                    previous = n
                cases.append({'id': f'{corpus}-{len(cases)+1:02}', 'stratum': group, **p,
                              'features_present': [k for k in features if p[k] == '1'], 'excerpt': '\n'.join(excerpt)})
    (OUT / 'manual-review-inputs.json').write_text(json.dumps({'selection': 'Four different source modules per proof-mode/length stratum and corpus; review validation set, not an estimator of corpus prevalence.', 'cases': cases}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Retained {len(cases)} source-inspection cases.')


if __name__ == '__main__':
    main()

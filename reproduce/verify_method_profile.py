"""Test proof extraction edge cases and reconcile all retained profile counts."""
import csv
import gzip
import hashlib
import io
import json
import collections
from pathlib import Path
from profile_lean_methods import FEATURES, mask_noncode, profile_source

PAPER = Path(__file__).resolve().parents[1]
OUT = PAPER / 'research/method-survey'


def check_fixture(source, names, modes, lengths=None):
    _, proofs, _ = profile_source(source.encode(), 'fixture', 'fixture.lean', 'Test')
    assert [p['name'] for p in proofs] == names
    assert [p['mode'] for p in proofs] == modes
    if lengths is not None:
        assert [p['body_lines'] for p in proofs] == lengths
    return proofs


def fixtures():
    masked = mask_noncode('x /- outer /- simp -/ aesop -/ y\n-- decide\n"rw" z')
    assert 'simp' not in masked and 'aesop' not in masked and 'decide' not in masked and 'rw' not in masked
    ps = check_fixture('theorem one : True := by\n  exact True.intro\n@[simp]\ntheorem two : True := True.intro\n#check two\n',
                       ['one', 'two'], ['tactic', 'term_only'], [2, 1])
    assert not ps[0]['rewrite_simplify']
    check_fixture('theorem defaultArg (x : Nat := 1) : True := by trivial\n', ['defaultArg'], ['tactic'], [1])
    check_fixture('theorem typeLets : let n := 1; let m := n; n = m := by rfl\n', ['typeLets'], ['tactic'], [1])
    check_fixture('theorem nestedTypeLet : let n := (let m := 1; m); n = n := by rfl\n', ['nestedTypeLet'], ['tactic'], [1])
    check_fixture('omit [Foo α] in theorem scoped : True := by trivial\nvariable (p) in protected lemma zero_le : True := True.intro\n',
                  ['scoped', 'zero_le'], ['tactic', 'term_only'])
    check_fixture('@[simp] private theorem attr : True := by trivial\n', ['attr'], ['tactic'])
    ps = check_fixture('theorem nested : True := id (by exact True.intro)\ntheorem fields : True := Object.simp\n',
                       ['nested', 'fields'], ['term_with_tactic', 'term_only'])
    assert not ps[1]['rewrite_simplify']
    ps = check_fixture('theorem restricted : True := by\n  simpa only [true_and]\ntheorem finite : 2 = 2 := by decide +kernel\n',
                       ['restricted', 'finite'], ['tactic', 'tactic'])
    assert ps[0]['restricted_simplification'] and ps[1]['finite_decision'] and ps[1]['kernel_decision_flag']
    check_fixture('theorem quotes : True := by\n  let s := r#"aesop -- /- decide"#\n  exact True.intro\n', ['quotes'], ['tactic'])
    fs, ps, xs = profile_source(b'theorem eqn : Nat -> Nat\n  | 0 => 0\n  | n+1 => n\n', 'fixture', 'f.lean', 'Test')
    assert fs['named_proof_declarations'] == 1 and not ps and len(xs) == 1
    return 11


def main():
    ntests = fixtures()
    summary = json.loads((OUT / 'summary.json').read_text(encoding='utf-8'))
    file_data = (OUT / 'files.csv').read_bytes()
    proof_data = gzip.decompress((OUT / 'proofs.csv.gz').read_bytes())
    assert hashlib.sha256(file_data).hexdigest() == summary['artifact_sha256']['files.csv']
    assert hashlib.sha256(proof_data).hexdigest() == summary['artifact_sha256']['proofs.csv_uncompressed']
    files = list(csv.DictReader(io.StringIO(file_data.decode())))
    proofs = list(csv.DictReader(io.StringIO(proof_data.decode())))
    design = json.loads((OUT / 'design.json').read_text(encoding='utf-8'))
    population_data = gzip.decompress((OUT / 'population.csv.gz').read_bytes())
    assert hashlib.sha256(population_data).hexdigest() == design['population_csv_sha256']
    population = list(csv.DictReader(io.StringIO(population_data.decode())))
    selected = sorted(population, key=lambda e: hashlib.sha256(
        (design['seed'] + '\0' + e['path']).encode()).hexdigest())[:design['sample_size']]
    manifest = json.loads((OUT / 'sample-manifest.json').read_text(encoding='utf-8'))
    assert [e['path'] for e in selected] == design['selected_paths'] == [e['path'] for e in manifest['files']]
    for entry in manifest['files']:
        data = (PAPER / entry['archived_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['git_blob_sha1']
    for c in ['OAI', 'Mathlib']:
        fs = [f for f in files if f['corpus'] == c]
        ps = [p for p in proofs if p['corpus'] == c]
        assert len(fs) == summary['source_file_counts'][c]
        assert len(ps) == summary['proof_body_counts'][c] == sum(int(f['extracted_proofs']) for f in fs)
        for k in FEATURES:
            expected = 100 * sum(int(p[k]) for p in ps) / len(ps)
            assert abs(expected - summary['feature_rates_percent'][c][k]) < 1e-10
        assert abs(sum(v['percent'] for v in summary['proof_modes'][c].values()) - 100) < 1e-10
        assert all(int(p['line']) <= int(p['body_line']) <= int(p['end_line']) for p in ps)
        groups = collections.defaultdict(list)
        for p in ps:
            groups[p['path']].append(p)
        assert len(groups) == summary['module_balanced'][c]['proof_bearing_modules']
        for k in FEATURES:
            expected = 100 * sum(sum(int(p[k]) for p in group) / len(group)
                                 for group in groups.values()) / len(groups)
            assert abs(expected - summary['module_balanced'][c]['rates_percent'][k]) < 1e-9
    manual = json.loads((OUT / 'manual-validation.json').read_text(encoding='utf-8'))
    index = {(p['corpus'], p['path'], p['name'], int(p['line'])): p for p in proofs}
    for case in manual['cases']:
        row = index[(case['corpus'], case['path'], case['name'], case['line'])]
        for k, expected in case['expected'].items():
            actual = row[k] if k == 'mode' else int(row[k])
            assert actual == expected, (case['id'], k, actual, expected)
    report = {'status': 'passed', 'synthetic_edge_case_checks': ntests,
              'sampled_source_blobs_verified': len(manifest['files']),
              'population_modules': len(population), 'hash_rank_membership_verified': True,
              'manually_inspected_bodies': len(manual['cases']),
              'initial_manual_validation_errors_corrected': len(manual['corrections']),
              'source_file_counts': summary['source_file_counts'], 'extracted_body_counts': summary['proof_body_counts'],
              'scope': 'Lexer/boundary fixtures, retained CSV hashes and count reconciliation; source reading remains necessary for mathematical interpretation.'}
    (PAPER / 'audit/method-survey-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

"""Measure lexical proof-body features in sampled OAI and pinned Mathlib source.

Usage: python reproduce/profile_lean_methods.py <pinned-Mathlib-checkout>
This is source analysis, not elaboration, a tactic trace or a novelty test.
"""
from pathlib import Path
import bisect
import collections
import csv
import gzip
import hashlib
import io
import json
import math
import random
import re
import statistics
import subprocess
import sys

PAPER = Path(__file__).resolve().parents[1]
OUT = PAPER / 'research/method-survey'
REV = 'd13f23b723b8a846827a245b89c10fc7d3f11612'
EXCLUDED_ROOTS = {'Tactic', 'Lean', 'Util', 'Testing'}
FEATURES = {
    'rewrite_simplify': ['rw', 'rwa', 'simp', 'simpa', 'simp_all', 'simp_rw', 'dsimp', 'erw', 'nth_rw', 'conv'],
    'arithmetic_algebra': ['omega', 'linarith', 'nlinarith', 'ring', 'ring_nf', 'norm_num', 'positivity', 'field_simp', 'linear_combination', 'simp_arith', 'abel', 'noncomm_ring'],
    'search_automation': ['aesop', 'tauto', 'grind', 'solve_by_elim', 'exact?', 'apply?', 'library_search'],
    'cases_induction': ['cases', 'cases\'', 'rcases', 'rintro', 'by_cases', 'by_contra', 'split', 'split_ifs', 'induction', 'induction\'', 'fun_induction', 'interval_cases', 'fin_cases'],
    'extensionality_congruence': ['ext', 'ext1', 'funext', 'congr', 'congr!', 'congrm', 'convert', 'convert!'],
    'local_claims_calc': ['have', 'suffices', 'obtain', 'calc'],
    'finite_decision': ['decide', 'native_decide'],
    'restricted_simplification': [],
    'explicit_classical': ['classical'],
    'kernel_decision_flag': [],
    'native_decision': [],
}
PATTERNS = {
    k: re.compile(r'(?<![\w.\'!?])(?:' + '|'.join(re.escape(w) for w in sorted(v, key=len, reverse=True)) + r')(?![\w.\'!?])')
    for k, v in FEATURES.items() if v
}
PATTERNS['restricted_simplification'] = re.compile(r'(?<![\w.\'])\b(?:simp|simpa|simp_all)\s+only\b')
PATTERNS['kernel_decision_flag'] = re.compile(r'(?<![\w.\'])\bdecide\s+\+kernel\b')
PATTERNS['native_decision'] = re.compile(r'(?<![\w.\'])(?:native_decide\b|decide\s+\+native\b)')
COMMANDS = ('theorem|lemma|def|abbrev|opaque|instance|structure|class|inductive|coinductive|example|axiom|constant|constants|axioms|variable|variables|universe|universes|section|namespace|end|open|export|attribute|notation|infix|infixl|infixr|prefix|postfix|syntax|macro|macro_rules|elab|elab_rules|set_option|initialize|builtin_initialize|declare_syntax_cat|include|omit|mutual')
COMMAND_RE = re.compile(r'^(?P<indent>[ \t]*)(?:(?:include|omit|set_option|open|attribute|variable|variables)\b[^\n]*?\bin[ \t]+)*(?:@\[[^\n]*\][ \t]*)*(?:(?:private|protected|noncomputable|unsafe|partial|public|scoped|local|nonrec)\s+)*(?P<kind>' + COMMANDS + r')\b(?:\s+(?P<name>[\w.\'«»]+))?')
TOKEN = re.compile(r'(?<![\w.\'])\bby\b')
MARKERS = re.compile(r'/-|--|"')
BLOCK_MARKERS = re.compile(r'/-|-/')
BOOTSTRAPS = 1500


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blank(text):
    return re.sub(r'[^\n]', ' ', text)


def mask_noncode(text):
    """Preserve offsets/newlines while removing nested comments and strings."""
    chunks, position = [], 0
    while match := MARKERS.search(text, position):
        start = match.start()
        chunks.append(text[position:start])
        marker = match.group()
        if marker == '--':
            stop = text.find('\n', match.end())
            stop = len(text) if stop < 0 else stop
        elif marker == '/-':
            level, stop = 1, match.end()
            while level:
                nested = BLOCK_MARKERS.search(text, stop)
                assert nested, 'Unclosed block comment.'
                level += 1 if nested.group() == '/-' else -1
                stop = nested.end()
        else:
            # Raw strings have r followed by zero or more hashes before the quote.
            raw = re.search(r'(?<![\w])r(#{0,})$', text[:start])
            if raw:
                terminator = '"' + raw.group(1)
                closing = text.find(terminator, match.end())
                assert closing >= 0, 'Unclosed raw string.'
                stop = closing + len(terminator)
            else:
                stop = match.end()
                while stop < len(text):
                    if text[stop] == '\\':
                        stop += 2
                    elif text[stop] == '"':
                        stop += 1
                        break
                    else:
                        stop += 1
                else:
                    raise AssertionError('Unclosed string.')
        chunks.append(blank(text[start:stop]))
        position = stop
    chunks.append(text[position:])
    masked = ''.join(chunks)
    assert len(masked) == len(text) and masked.count('\n') == text.count('\n')
    return masked


def body_offset(block):
    depth, pending_bindings = 0, 0
    for match in re.finditer(r'«[^»]*»|:=|(?<![\w.\'])\b(?:let|letI|have)\b|[()\[\]{}⦃⦄⟨⟩]', block):
        token = match.group()
        if token.startswith('«'):
            continue
        if depth == 0 and token in {'let', 'letI', 'have'}:
            pending_bindings += 1
        if token == ':=' and depth == 0:
            if pending_bindings:
                pending_bindings -= 1
            else:
                return match.end()
        if token in '([{⦃⟨':
            depth += 1
        elif token in ')]}⦄⟩':
            depth -= 1
    return None


def profile_source(data, corpus, path, domain):
    text = data.decode('utf-8-sig')
    code = mask_noncode(text)
    lines = code.splitlines(keepends=True)
    offsets, offset = [], 0
    commands = []
    for number, line in enumerate(lines):
        offsets.append(offset)
        if match := COMMAND_RE.match(line):
            indent = len(match['indent'].expandtabs(4))
            commands.append((offset, number + 1, indent, match['kind'], match['name'] or ''))
        elif line.lstrip().startswith(('@[', '#', 'assert_not_exists', 'suppress_compilation')):
            indent = len(line) - len(line.lstrip())
            commands.append((offset, number + 1, indent, 'attribute_block', ''))
        offset += len(line)
    proofs, excluded = [], []
    detected = {(line, kind, name) for _, line, _, kind, name in commands if kind in {'theorem', 'lemma'}}
    unrecognized = []
    for candidate in re.finditer(r'(?<![\w.])\b(theorem|lemma)\s+([\w.\'«»]+)', code):
        candidate_line = bisect.bisect_right(offsets, candidate.start())
        if (candidate_line, candidate[1], candidate[2]) not in detected:
            unrecognized.append({'corpus': corpus, 'path': path, 'line': candidate_line,
                                 'name': candidate[2], 'reason': 'Named declaration token outside recognized command start.'})
    for index, (start, line, indent, kind, name) in enumerate(commands):
        if kind not in {'theorem', 'lemma'}:
            continue
        stop = len(code)
        for following in commands[index + 1:]:
            if following[2] <= indent:
                stop = following[0]
                break
        block = code[start:stop]
        relative = body_offset(block)
        if relative is None:
            excluded.append({'corpus': corpus, 'path': path, 'name': name, 'line': line,
                             'reason': 'No outer := body found (e.g. equation-style declaration).',
                             'excerpt': text[start:min(stop, start + 600)]})
            continue
        body_start = start + relative
        body = code[body_start:stop].rstrip()
        if not body.strip():
            excluded.append({'corpus': corpus, 'path': path, 'name': name, 'line': line,
                             'reason': 'Empty extracted body.'})
            continue
        mode = ('tactic' if re.match(r'\s*\(*\s*by\b', body) else
                'term_with_tactic' if TOKEN.search(body) else 'term_only')
        proof = {'corpus': corpus, 'path': path, 'domain': domain, 'kind': kind, 'name': name,
                 'line': line, 'body_line': bisect.bisect_right(offsets, body_start),
                 'end_line': bisect.bisect_right(offsets, body_start + len(body) - 1),
                 'mode': mode, 'body_lines': sum(bool(s.strip()) for s in body.splitlines())}
        feature_body = re.sub(r'«[^»]*»', lambda m: blank(m.group()), body)
        proof.update({key: int(bool(pattern.search(feature_body))) for key, pattern in PATTERNS.items()})
        proofs.append(proof)
    imports = re.findall(r'^\s*(?:(?:public|meta)\s+)*import\s+([\w.]+)', code, re.M)
    record = {'corpus': corpus, 'path': path, 'domain': domain, 'sha256': digest(data),
              'bytes': len(data), 'source_lines': len(lines),
              'code_lines': sum(bool(s.strip()) for s in lines), 'imports': len(imports),
              'broad_mathlib_import': int('Mathlib' in imports),
              'oai_import': int(any(s.startswith('OAI.') for s in imports)),
              'named_proof_declarations': sum(c[3] in {'theorem', 'lemma'} for c in commands),
              'extracted_proofs': len(proofs), 'unextracted_proofs': len(excluded)}
    record['unrecognized_named_declaration_tokens'] = len(unrecognized)
    excluded.extend(unrecognized)
    return record, proofs, excluded


def csv_bytes(rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def quantile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def rates(proofs):
    return {feature: 100 * sum(p[feature] for p in proofs) / len(proofs) for feature in FEATURES}


def band(length):
    return '1-3' if length <= 3 else '4-10' if length <= 10 else '11-30' if length <= 30 else '31+'


def main():
    checkout = Path(sys.argv[1]).resolve()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip() == REV
    subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=checkout, check=True)
    design = json.loads((OUT / 'design.json').read_text())
    population_data = gzip.decompress((OUT / 'population.csv.gz').read_bytes())
    assert digest(population_data) == design['population_csv_sha256']
    population = list(csv.DictReader(io.StringIO(population_data.decode())))
    selected = sorted(population, key=lambda e: digest((design['seed'] + '\0' + e['path']).encode()))[:design['sample_size']]
    manifest = json.loads((OUT / 'sample-manifest.json').read_text())
    assert [e['path'] for e in selected] == [e['path'] for e in manifest['files']] == design['selected_paths']
    files, proofs, excluded = [], [], []
    for entry in manifest['files']:
        data = (PAPER / entry['archived_path']).read_bytes()
        assert digest(data) == entry['sha256']
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['git_blob_sha1']
        f, p, x = profile_source(data, 'OAI', entry['path'], entry['domain'])
        f['git_blob_sha1'] = entry['git_blob_sha1']
        files.append(f); proofs.extend(p); excluded.extend(x)
    print(f'OAI sample profiled: {len(files)} modules, {len(proofs)} bodies', flush=True)
    git_entries = subprocess.check_output(['git', 'ls-tree', '-r', '-z', 'HEAD', '--', 'Mathlib'], cwd=checkout).decode().split('\0')
    git_blobs = {entry.split('\t', 1)[1]: entry.split('\t', 1)[0].split()[2] for entry in git_entries if entry}
    tracked = list(git_blobs)
    baseline = sorted(path for path in tracked if path.endswith('.lean') and len(Path(path).parts) > 2
                      and Path(path).parts[1] not in EXCLUDED_ROOTS)
    for index, path in enumerate(baseline):
        data = (checkout / path).read_bytes()
        expected = git_blobs[path]
        blob = lambda value: hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest()
        if blob(data) != expected:
            data = data.replace(b'\r\n', b'\n')
        assert blob(data) == expected, path
        f, p, x = profile_source(data, 'Mathlib', path, Path(path).parts[1])
        f['git_blob_sha1'] = expected
        files.append(f); proofs.extend(p); excluded.extend(x)
        if (index + 1) % 1500 == 0:
            print(f'Mathlib modules profiled: {index + 1}/{len(baseline)}', flush=True)
    file_data, proof_data = csv_bytes(files), csv_bytes(proofs)
    (OUT / 'files.csv').write_bytes(file_data)
    (OUT / 'proofs.csv.gz').write_bytes(gzip.compress(proof_data, mtime=0))
    (OUT / 'extraction-exclusions.json').write_text(json.dumps(excluded, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    summary = {'oai_commit': design['oai_commit'], 'mathlib_commit': REV,
               'unit': 'Extracted named theorem/lemma body; multiple lexical features may occur in one body.',
               'extraction': 'Nested comments and quoted strings masked; declarations found at source-command starts; outer := identified outside bracketed binders/types; body ends at the next command at no greater indentation.',
               'features': FEATURES, 'source_file_counts': {}, 'proof_body_counts': {},
               'file_summary': {}, 'proof_modes': {}, 'feature_rates_percent': {},
               'proof_length_nonempty_lines': {}, 'coverage': {}}
    by_corpus = {}
    for corpus in ['OAI', 'Mathlib']:
        fs = [f for f in files if f['corpus'] == corpus]
        ps = [p for p in proofs if p['corpus'] == corpus]
        by_corpus[corpus] = ps
        summary['source_file_counts'][corpus] = len(fs)
        summary['proof_body_counts'][corpus] = len(ps)
        summary['file_summary'][corpus] = {
            'median_source_lines': statistics.median(f['source_lines'] for f in fs),
            'median_extracted_proofs': statistics.median(f['extracted_proofs'] for f in fs),
            'median_imports': statistics.median(f['imports'] for f in fs),
            'broad_mathlib_import_percent': 100 * sum(f['broad_mathlib_import'] for f in fs) / len(fs),
            'oai_import_percent': 100 * sum(f['oai_import'] for f in fs) / len(fs),
            'zero_named_proof_files': sum(f['named_proof_declarations'] == 0 for f in fs),
        }
        counts = collections.Counter(p['mode'] for p in ps)
        summary['proof_modes'][corpus] = {k: {'count': counts[k], 'percent': 100 * counts[k] / len(ps)}
                                          for k in ['tactic', 'term_with_tactic', 'term_only']}
        summary['feature_rates_percent'][corpus] = rates(ps)
        lengths = [p['body_lines'] for p in ps]
        summary['proof_length_nonempty_lines'][corpus] = {
            'median': statistics.median(lengths), 'q25': quantile(lengths, .25), 'q75': quantile(lengths, .75),
            'p90': quantile(lengths, .90), 'p99': quantile(lengths, .99), 'max': max(lengths),
            'bands': dict(collections.Counter(band(v) for v in lengths))}
        total = sum(f['named_proof_declarations'] for f in fs)
        summary['coverage'][corpus] = {'named_declarations_detected': total, 'bodies_extracted': len(ps),
                                       'unextracted': total - len(ps), 'percent_extracted': 100 * len(ps) / total,
                                       'unrecognized_named_declaration_tokens': sum(f['unrecognized_named_declaration_tokens'] for f in fs)}
    # Equal-probability module sampling requires cluster uncertainty, not a
    # binomial interval treating every named body as an independent sample.
    clustered = collections.defaultdict(list)
    for p in by_corpus['OAI']:
        clustered[p['path']].append(p)
    vectors = []
    metric_names = list(FEATURES) + ['mode_tactic', 'mode_term_with_tactic', 'mode_term_only']
    for f in [f for f in files if f['corpus'] == 'OAI']:
        ps = clustered[f['path']]
        vectors.append([len(ps)] + [sum(p[k] for p in ps) for k in FEATURES]
                       + [sum(p['mode'] == mode for p in ps) for mode in ['tactic', 'term_with_tactic', 'term_only']])
    rng = random.Random(764982)
    bootstrap = {k: [] for k in metric_names}
    for _ in range(BOOTSTRAPS):
        totals = [0] * (len(metric_names) + 1)
        for _ in vectors:
            vector = vectors[rng.randrange(len(vectors))]
            for i, value in enumerate(vector):
                totals[i] += value
        for i, key in enumerate(metric_names, 1):
            bootstrap[key].append(100 * totals[i] / totals[0])
    summary['oai_95_percent_module_bootstrap_intervals'] = {
        k: [quantile(v, .025), quantile(v, .975)] for k, v in bootstrap.items()}
    summary['bootstrap'] = {'replicates': BOOTSTRAPS, 'seed': 764982, 'unit': '800 source modules, including files with zero named proofs',
                            'scope': 'Percentile cluster bootstrap; exploratory descriptive uncertainty, without a finite-population correction.'}
    # An exploratory sensitivity analysis gives equal weight to each module
    # with an extracted named body, then equal weight to its bodies. It avoids
    # allowing large batches of numerical certificates to dominate the view
    # of a typical source module. This is a different estimand from pooling.
    module_profiles = {}
    for corpus in ['OAI', 'Mathlib']:
        groups = collections.defaultdict(list)
        for p in by_corpus[corpus]:
            groups[p['path']].append(p)
        module_profiles[corpus] = [dict(path=path, domain=ps[0]['domain'], proofs=len(ps),
            **{k: sum(p[k] for p in ps) / len(ps) for k in FEATURES},
            **{'mode_' + mode: sum(p['mode'] == mode for p in ps) / len(ps)
               for mode in ['tactic', 'term_with_tactic', 'term_only']}) for path, ps in groups.items()]
    balanced = {c: {'proof_bearing_modules': len(vs),
                   'rates_percent': {k: 100 * statistics.mean(v[k] for v in vs) for k in metric_names}}
                for c, vs in module_profiles.items()}
    rng = random.Random(764983)
    draws = {k: [] for k in metric_names}
    vs = module_profiles['OAI']
    for _ in range(BOOTSTRAPS):
        weights = collections.Counter(rng.randrange(len(vs)) for _ in vs)
        for k in metric_names:
            draws[k].append(100 * sum(n * vs[i][k] for i, n in weights.items()) / len(vs))
    balanced['oai_95_percent_module_bootstrap_intervals'] = {k: [quantile(v, .025), quantile(v, .975)] for k, v in draws.items()}
    balanced['estimand'] = 'Choose a proof-bearing module uniformly, then one extracted named body uniformly within it.'
    balanced['analysis_status'] = 'Exploratory sensitivity analysis added after observing certificate-batch concentration; not the original pooled estimand.'
    summary['module_balanced'] = balanced
    ordered = sorted(module_profiles['OAI'], key=lambda v: v['proofs'], reverse=True)
    summary['concentration'] = {
        'largest_module_body_share_percent': 100 * ordered[0]['proofs'] / len(by_corpus['OAI']),
        'top_10_module_body_share_percent': 100 * sum(v['proofs'] for v in ordered[:10]) / len(by_corpus['OAI']),
        'top_modules': [{'path': v['path'], 'bodies': v['proofs'], 'finite_decision_percent': 100*v['finite_decision']} for v in ordered[:10]],
    }
    summary['without_finite_decision_bodies'] = {
        c: {'bodies': len(ps := [p for p in by_corpus[c] if not p['finite_decision']]), 'rates_percent': rates(ps)}
        for c in ['OAI', 'Mathlib']}
    # Standardize the census to the OAI sample's proof-body domain shares.
    domains = sorted({p['domain'] for p in by_corpus['OAI']} & {p['domain'] for p in by_corpus['Mathlib']})
    common = {c: [p for p in ps if p['domain'] in domains] for c, ps in by_corpus.items()}
    domain_counts = collections.Counter(p['domain'] for p in common['OAI'])
    domain_rates = {d: rates([p for p in common['Mathlib'] if p['domain'] == d]) for d in domains}
    standardized = {k: sum(domain_counts[d] * domain_rates[d][k] for d in domains) / len(common['OAI']) for k in FEATURES}
    summary['common_domain_control'] = {'domains': domains, 'oai_bodies': len(common['OAI']),
        'oai_coverage_percent': 100 * len(common['OAI']) / len(by_corpus['OAI']),
        'mathlib_bodies': len(common['Mathlib']), 'oai_domain_body_counts': dict(domain_counts),
        'oai_rates_percent': rates(common['OAI']), 'mathlib_domain_standardized_rates_percent': standardized}
    common_modules = {c: [v for v in module_profiles[c] if v['domain'] in domains] for c in ['OAI', 'Mathlib']}
    module_domains = collections.Counter(v['domain'] for v in common_modules['OAI'])
    baseline_domain_means = {d: {k: statistics.mean(v[k] for v in common_modules['Mathlib'] if v['domain'] == d)
                                for k in metric_names} for d in domains}
    summary['common_domain_module_balanced_control'] = {
        'domains': domains, 'oai_proof_bearing_modules': len(common_modules['OAI']),
        'oai_module_coverage_percent': 100 * len(common_modules['OAI']) / len(module_profiles['OAI']),
        'oai_rates_percent': {k: 100 * statistics.mean(v[k] for v in common_modules['OAI']) for k in metric_names},
        'mathlib_domain_standardized_rates_percent': {k: 100 * sum(module_domains[d] * baseline_domain_means[d][k] for d in domains) / len(common_modules['OAI']) for k in metric_names},
        'domain_module_counts': dict(module_domains),
    }
    summary['length_band_controls'] = {}
    for length_band in ['1-3', '4-10', '11-30', '31+']:
        summary['length_band_controls'][length_band] = {}
        band_groups = {}
        for c in ['OAI', 'Mathlib']:
            ps = [p for p in common[c] if band(p['body_lines']) == length_band]
            band_groups[c] = ps
            summary['length_band_controls'][length_band][c] = {'bodies': len(ps), 'rates_percent': rates(ps)}
        available = sorted({p['domain'] for p in band_groups['OAI']} & {p['domain'] for p in band_groups['Mathlib']})
        oai_band = [p for p in band_groups['OAI'] if p['domain'] in available]
        dc = collections.Counter(p['domain'] for p in oai_band)
        br = {d: rates([p for p in band_groups['Mathlib'] if p['domain'] == d]) for d in available}
        summary['length_band_controls'][length_band]['domain_standardized'] = {
            'oai_bodies': len(oai_band), 'oai_rates_percent': rates(oai_band),
            'mathlib_rates_percent': {k: sum(dc[d] * br[d][k] for d in available) / len(oai_band) for k in FEATURES}}
    summary['domain_details'] = {}
    for d in domains:
        summary['domain_details'][d] = {
            c: {'modules': sum(f['corpus'] == c and f['domain'] == d for f in files),
                'bodies': len(ps := [p for p in by_corpus[c] if p['domain'] == d]),
                'rates_percent': rates(ps)} for c in ['OAI', 'Mathlib']}
    summary['artifact_sha256'] = {'files.csv': digest(file_data), 'proofs.csv_uncompressed': digest(proof_data),
                                  'population.csv_uncompressed': digest(population_data)}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ['source_file_counts', 'proof_body_counts', 'file_summary', 'proof_modes', 'feature_rates_percent', 'coverage']}, indent=2), flush=True)


if __name__ == '__main__':
    main()

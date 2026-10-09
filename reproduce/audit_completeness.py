"""Explore robustness gaps using the retained proof-method data.

This analysis retains the original survey and generates a separate joint
comparison and manuscript table. Directory family labels are proxies.
Joint standardization is descriptive: proof length may itself reflect style.
Run: python reproduce/audit_completeness.py
"""
from pathlib import Path
import collections
import csv
import gzip
import hashlib
import io
import json
import math
import random
import statistics

PAPER = Path(__file__).resolve().parents[1]
SURVEY = PAPER / 'research/method-survey'
FEATURES = ['mode_tactic', 'local_claims_calc', 'arithmetic_algebra',
            'restricted_simplification', 'finite_decision']


def value(row, feature):
    return int(row['mode'] == 'tactic') if feature == 'mode_tactic' else int(row[feature])


def rate(rows, feature):
    return 100 * statistics.mean(value(row, feature) for row in rows)


def band(row):
    size = int(row['body_lines'])
    return '1-3' if size <= 3 else '4-10' if size <= 10 else '11-30' if size <= 30 else '31+'


def quantile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def main():
    summary_bytes = (SURVEY / 'summary.json').read_bytes()
    summary = json.loads(summary_bytes)
    raw = gzip.decompress((SURVEY / 'proofs.csv.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == summary['artifact_sha256']['proofs.csv_uncompressed']
    modules = {corpus: collections.defaultdict(list) for corpus in ['OAI', 'Mathlib']}
    for row in csv.DictReader(raw.decode('utf-8').splitlines()):
        modules[row['corpus']][row['path']].append(row)
    rates = {corpus: {path: {feature: rate(rows, feature) for feature in FEATURES}
                     for path, rows in paths.items()} for corpus, paths in modules.items()}
    base = {corpus: {feature: statistics.mean(row[feature] for row in paths.values())
                    for feature in FEATURES} for corpus, paths in rates.items()}
    for corpus in modules:
        assert len(modules[corpus]) == summary['module_balanced'][corpus]['proof_bearing_modules']
        for feature in FEATURES[1:]:
            assert abs(base[corpus][feature] - summary['module_balanced'][corpus]['rates_percent'][feature]) < 1e-9

    families = collections.defaultdict(list)
    for path in modules['OAI']:
        families['/'.join(path.split('/')[2:4])].append(path)
    family_counts = sorted([{'family': family, 'modules': len(paths),
                             'proofs': sum(len(modules['OAI'][path]) for path in paths)}
                            for family, paths in families.items()], key=lambda row: row['modules'], reverse=True)
    family_equal = {feature: statistics.mean(statistics.mean(rates['OAI'][path][feature] for path in paths)
                                            for paths in families.values()) for feature in FEATURES}
    exclusions = {feature: [statistics.mean(row[feature] for path, row in rates['OAI'].items()
                                           if path not in paths) for paths in families.values()]
                  for feature in FEATURES}
    certificate_paths = {path for path in modules['OAI']
                         if any(part.lower() in {'certificate', 'certificates', 'numerics'} for part in path.split('/'))}
    noncertificate = {feature: statistics.mean(row[feature] for path, row in rates['OAI'].items()
                                              if path not in certificate_paths) for feature in FEATURES}

    strata = {corpus: collections.defaultdict(dict) for corpus in modules}
    for corpus, paths in modules.items():
        for path, rows in paths.items():
            groups = collections.defaultdict(list)
            for row in rows:
                groups[band(row)].append(row)
            domain = path.split('/')[2 if corpus == 'OAI' else 1]
            for length_band, subset in groups.items():
                strata[corpus][domain, length_band][path] = subset
    common_set = set(strata['OAI']) & set(strata['Mathlib'])
    common = sorted(common_set)
    weights = {cell: sum(len(rows) / len(modules['OAI'][path])
                         for path, rows in strata['OAI'][cell].items()) / len(modules['OAI']) for cell in common}
    coverage = sum(weights.values())
    cell_rates = {corpus: {cell: {feature:
        sum(len(rows) / len(modules[corpus][path]) * rate(rows, feature)
            for path, rows in strata[corpus][cell].items()) /
        sum(len(rows) / len(modules[corpus][path]) for path, rows in strata[corpus][cell].items())
        for feature in FEATURES} for cell in common} for corpus in modules}
    joint = {corpus: {feature: sum(weights[cell] * cell_rates[corpus][cell][feature]
                                   for cell in common) / coverage for feature in FEATURES} for corpus in modules}
    figure = json.loads((SURVEY / 'shift-figure.json').read_text(encoding='utf-8'))
    for row in figure['data']:
        if row['feature'] in FEATURES:
            assert abs(joint['OAI'][row['feature']] - row['oai_common_domains_percent']) < 1e-9

    # Bootstrap uniformly sampled OAI modules. Keep the Mathlib census cell
    # means fixed; OAI stratum weights and the matched coverage vary each draw.
    vectors = []
    for path, rows in modules['OAI'].items():
        domain = path.split('/')[2]
        matched = [row for row in rows if (domain, band(row)) in common_set]
        mass = len(matched) / len(rows)
        differences = [sum(100 * value(row, feature) - cell_rates['Mathlib'][domain, band(row)][feature]
                           for row in matched) / len(rows) for feature in FEATURES]
        vectors.append((mass, differences))
    # Reconcile the cell formula with a separate uniform-module/body sum.
    total_mass = sum(row[0] for row in vectors)
    assert abs(total_mass / len(vectors) - coverage) < 1e-12
    for index, feature in enumerate(FEATURES):
        direct_difference = sum(row[1][index] for row in vectors) / total_mass
        assert abs(direct_difference - (joint['OAI'][feature] - joint['Mathlib'][feature])) < 1e-9
    rng = random.Random(764984)
    replicates = [[] for _ in FEATURES]
    for _ in range(1500):
        sample = rng.choices(vectors, k=len(vectors))
        total_mass = sum(row[0] for row in sample)
        for index in range(len(FEATURES)):
            replicates[index].append(sum(row[1][index] for row in sample) / total_mass)
    intervals = {feature: [quantile(replicates[index], .025), quantile(replicates[index], .975)]
                 for index, feature in enumerate(FEATURES)}
    result = {
        'definition': 'Exploratory sensitivity audit of retained lexical data; not matched tasks or a causal estimate.',
        'survey_summary_sha256': hashlib.sha256(summary_bytes).hexdigest(),
        'sampled_oai_families': len(families), 'largest_sampled_families': family_counts[:10],
        'largest_family_share_of_proof_bearing_modules_percent': 100 * family_counts[0]['modules'] / len(modules['OAI']),
        'module_balanced_raw_rates': base, 'equal_family_weight_oai_rates': family_equal,
        'leave_one_family_out_oai_rate_ranges': {feature: {'minimum_oai_rate': min(values), 'maximum_oai_rate': max(values)}
                                                for feature, values in exclusions.items()},
        'certificate_directory_proxy_excluded_modules': len(certificate_paths),
        'oai_rates_after_certificate_directory_proxy_exclusion': noncertificate,
        'joint_domain_length_standardization': {
            'unit': 'Uniform proof-bearing module then uniform body; Mathlib cell means reweighted to OAI domain/length probabilities.',
            'common_cell_count': len(common), 'oai_module_body_probability_coverage_percent': 100 * coverage,
            'rates_percent': joint, 'differences_pp': {feature: joint['OAI'][feature] - joint['Mathlib'][feature] for feature in FEATURES},
            'oai_module_bootstrap_95_percent_intervals_pp': intervals,
            'bootstrap': {'replicates': 1500, 'seed': 764984, 'baseline': 'Fixed retained Mathlib census cell means.'},
            'scope': 'Coarse subject/length cells; length may itself reflect proof style. Conditional on extraction and fixed baseline; no task-difficulty, declaration-role or author-provenance matching.'}}
    output = PAPER / 'audit/completeness-sensitivity-2026-10-08.json'
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    joint_record = result['joint_domain_length_standardization'] | {
        'source_summary_sha256': result['survey_summary_sha256'],
        'proofs_csv_uncompressed_sha256': hashlib.sha256(raw).hexdigest(),
        'length_bands': ['1-3', '4-10', '11-30', '31+'],
        'features': FEATURES,
        'cell_weights': [{'domain': cell[0], 'length_band': cell[1],
                         'normalized_oai_weight': weights[cell] / coverage,
                         'oai_modules_contributing': len(strata['OAI'][cell]),
                         'mathlib_modules_contributing': len(strata['Mathlib'][cell]),
                         'oai_conditional_rates_percent': cell_rates['OAI'][cell],
                         'mathlib_conditional_rates_percent': cell_rates['Mathlib'][cell]}
                        for cell in common]}
    (SURVEY / 'joint-standardization.json').write_text(json.dumps(joint_record, indent=2) + '\n', encoding='utf-8', newline='\n')
    subject = {row['feature']: row['common_domain_difference_pp'] for row in figure['data']}
    labels = {'mode_tactic': 'Outer tactic block', 'local_claims_calc': 'Local claims or calculation chains',
              'arithmetic_algebra': 'Arithmetic or algebra tactics',
              'restricted_simplification': 'Restricted simplification', 'finite_decision': 'Finite decision'}
    comparison = [{'feature': feature, 'subject_only_difference_pp': subject[feature],
                   'joint_difference_pp': result['joint_domain_length_standardization']['differences_pp'][feature],
                   'joint_bootstrap_lower_pp': intervals[feature][0], 'joint_bootstrap_upper_pp': intervals[feature][1]}
                  for feature in FEATURES]
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(comparison[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(comparison)
    (SURVEY / 'joint-comparison.csv').write_text(buffer.getvalue(), encoding='utf-8', newline='\n')
    table = [r'\begin{table}[H]', r'\centering\small',
             r'\caption{OpenAI minus Mathlib differences in percentage points, with subject-only and joint subject/length standardization. Both use the module/body sampling measure. The 95\% percentile-bootstrap intervals resample OpenAI modules with Mathlib cell means fixed. The joint comparison covers 69 cells and 93.75\% of the OpenAI measure.}',
             r'\label{tab:joint-profile}', r'\setlength{\tabcolsep}{4pt}',
             r'\renewcommand{\arraystretch}{1.18}', r'\begin{tabular}{@{}p{6.0cm}rrr@{}}',
             r'\toprule', r'Written feature & Subject only & Subject + length & 95\% joint interval \\', r'\midrule']
    for row in comparison:
        table.append(f"{labels[row['feature']]} & {row['subject_only_difference_pp']:+.1f} & {row['joint_difference_pp']:+.1f} & {row['joint_bootstrap_lower_pp']:.1f}--{row['joint_bootstrap_upper_pp']:.1f}" + r' \\[5pt]')
    table += [r'\bottomrule', r'\end{tabular}', r'\end{table}', '']
    (PAPER / 'method-profile-joint-table.tex').write_text('\n'.join(table), encoding='utf-8', newline='\n')
    print(json.dumps({'output': str(output), 'joint_differences_pp': result['joint_domain_length_standardization']['differences_pp'],
                      'bootstrap_intervals_pp': intervals, 'sampled_directory_families': len(families)}))


if __name__ == '__main__':
    main()

"""Retain and verify the exact source spans behind the deeper case analysis."""
from pathlib import Path
import hashlib
import json
import re

PAPER = Path(__file__).resolve().parents[1]
COMMIT = 'fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb'
PREFIX = 'lean/OAI/'
CLAIMS = [
    ('compiler_fold', 'Combinatorics/MatroidCounting/CommonBases.lean', 16855, 16904,
     'evalFold_charge', 'Safety bounds intermediate encodings; the fold charge is bounded by list length times the body and encoding costs.'),
    ('compiler_polynomial', 'Combinatorics/MatroidCounting/CommonBases.lean', 17079, 17092,
     'evaluate_polynomial', 'Structural polynomial charge follows from the Safe invariant.'),
    ('compiler_poly_safe', 'Combinatorics/MatroidCounting/CommonBases.lean', 17689, 17706,
     'PolySafe', 'Polynomial width certificates compose by polynomial substitution.'),
    ('compiler_attributes', 'Combinatorics/MatroidCounting/CommonBases.lean', 22444, 22466,
     'attrSafe_compose', 'Attribute composition enlarges the width parameter and uses monotonicity to preserve numerical predicates.'),
    ('estimator_attributes', 'Combinatorics/MatroidCounting/CommonBases.lean', 24280, 24308,
     'attr_estimate', 'Exponentiation has a numerical exponent bound; estimator attributes bound three parameter fields.'),
    ('slice_two_blocks', 'Probability/SwitchChain/SliceOperatorComparison.lean', 96, 156,
     'operator_comparison_nontrivial', 'A two-block coefficient decomposition compares the flag Gram operator with the swap generator, with boundary cases separate.'),
    ('slice_isometry', 'Probability/SwitchChain/SliceReindexedComparison.lean', 49, 79,
     'reindexed_projection_energy_le_swap_sum', 'A linear isometry preserves projection norms and conjugates label swaps.'),
    ('graph_restriction_budget', 'Probability/SwitchChain/PairEqualityBudget.lean', 150, 270,
     'sum_assignmentRestriction_norm_sq', 'Division by assignment-space cardinality gives the exact global restriction identity and lifts the local energy budget.'),
    ('unordered_budget', 'Probability/SwitchChain/PairEqualityBudgetUnordered.lean', 23, 54,
     'pair_projection_budget', 'The conversion from ordered labels to unordered partner pairs contributes the same factor one-half to both sides.'),
    ('continuous_wedge', 'Analysis/Mahler/ContinuousWedge.lean', 19, 107,
     'continuousWedgeCLM', 'Finite-dimensionality promotes the algebraic wedge to a continuous bilinear operator; regularity follows by composition.'),
    ('real_form_pullback', 'Analysis/Mahler/ExactFormCoordinates.lean', 33, 96,
     'extDeriv_fluxPullback', 'Real-part projection and fixed linear pullback commute with exterior differentiation at differentiability points.'),
    ('oriented_flux_bridge', 'Analysis/Mahler/ExactSphereFluxBridge.lean', 11, 67,
     'sphereFlux_eq_coordinateFlux', 'The positive orthonormal frame has volume +1; density equality and sphere measure preservation identify the real and complex-form fluxes.'),
    ('compiler_arithmetic_close', 'Combinatorics/MatroidCounting/CommonBases.lean', 16905, 16907,
     'omega', 'The fold induction hypothesis carries safety and width bounds; restricted simplification expands the shared product before linear arithmetic closes the cost inequality.'),
    ('crouzeix_arithmetic_close', 'Analysis/DirectCrouzeix/DomainCore.lean', 111, 117,
     'nlinarith', 'Positive denominators and the strictly positive energy witness permit the scalar cancellation yielding gamma squared at most four.'),
    ('faber_coefficients', 'Analysis/DirectCrouzeix/FaberCalculus.lean', 94, 163,
     'algebraGenerating_coefficient', 'A finite geometric expansion removes a higher-order Taylor remainder before antianalytic Fourier coefficient transport.'),
    ('boundary_germs', 'Analysis/DirectCrouzeix/Continuation.lean', 31, 111,
     'patch_boundary_germs', 'The identity theorem makes chosen boundary extensions locally equal, preserving analytic and side data.'),
    ('inverse_collar', 'Analysis/DirectCrouzeix/ConformalCollar.lean', 129, 238,
     'inverse_riemann_collar', 'Compactness, local invertibility and a disk thickening construct an analytic inverse on a disk of radius greater than one.'),
    ('exterior_map', 'Analysis/DirectCrouzeix/ExteriorMapping.lean', 148, 214,
     'exists_expLevel_exterior', 'The inverted exponential domain and inverse collar supply the exterior Laurent map used by the analytic bound.'),
    ('trace_filter_extension', 'Analysis/TraceCone/IdealTransport.lean', 238, 257,
     'PreservesCanonicalConvergence.net', 'Image filters extend carrier-indexed convergence preservation to arbitrary indexing types.'),
    ('atomic_coordinates', 'AlgebraicGeometry/CharacterVarieties/Cutting/AtomicFrames.lean', 179, 227,
     'split_equiv_eq', 'Common atom labels and injectivity produce equality of splitting coordinate maps, then framed compatibility.'),
    ('inherited_coordinates', 'AlgebraicGeometry/CharacterVarieties/Frames/InheritedSeams.lean', 117, 155,
     'markedInherited_seamHolds', 'Inherited seam compatibility consumes grades, both frame identities, both word transports and the old seam equation.'),
]


def main():
    inventory = json.loads((PAPER / 'research/corpus-inventory.json').read_text(encoding='utf-8'))
    assert inventory['commit'] == COMMIT
    indexed = {e['path']: e for e in inventory['selected_files']}
    closure_record = json.loads((PAPER / 'research/depth/import-closures.json').read_text(encoding='utf-8'))
    assert closure_record['commit'] == COMMIT
    closure_counts, all_modules = {}, set()
    for case, closure in closure_record['closures'].items():
        seen, external, stack = set(), set(), [closure['seed']]
        while stack:
            path = stack.pop()
            if path in seen:
                continue
            seen.add(path)
            assert path in indexed, (case, path)
            source = (PAPER / indexed[path]['archived_path']).read_text(encoding='utf-8')
            for module in re.findall(r'^import ([A-Za-z0-9_.]+)\s*$', source, re.M):
                if module.startswith('OAI.'):
                    stack.append('lean/' + module.replace('.', '/') + '.lean')
                else:
                    external.add(module)
        assert sorted(seen) == closure['files'], case
        assert len(seen) == closure['oai_module_count'], case
        assert sorted(external) == closure['external_imports'], case
        closure_counts[case] = len(seen)
        all_modules.update(seen)
    assert len(closure_counts) == 6
    records = []
    for key, suffix, first, last, declaration, interpretation in CLAIMS:
        path = PREFIX + suffix
        entry = indexed[path]
        data = (PAPER / entry['archived_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        lines = data.decode('utf-8').splitlines()
        assert 1 <= first <= last <= len(lines)
        excerpt = '\n'.join(lines[first - 1:last])
        assert declaration in excerpt
        records.append({'id': key, 'path': path, 'lines': [first, last],
                        'declaration': declaration, 'interpretation': interpretation,
                        'sha256': entry['sha256'], 'git_blob_sha1': entry['git_blob_sha1'],
                        'url': f'https://github.com/openai/math/blob/{COMMIT}/{path}#L{first}-L{last}',
                        'excerpt': excerpt})
    # Every immutable OAI source hyperlink in the manuscript must be retained.
    source_index = dict(indexed)
    survey_manifest = PAPER / 'research/method-survey/sample-manifest.json'
    if survey_manifest.exists():
        survey = json.loads(survey_manifest.read_text(encoding='utf-8'))
        for entry in survey['files']:
            if entry['path'] in source_index:
                assert source_index[entry['path']]['sha256'] == entry['sha256']
            else:
                source_index[entry['path']] = entry
    url_pattern = rf'https://github\.com/openai/math/blob/{COMMIT}/([^}}\s#]+)(?:#L(\d+)-L(\d+))?'
    links = []
    for file in PAPER.glob('*.tex'):
        tex = file.read_text(encoding='utf-8').replace(r'\#', '#')
        for path, first, last in re.findall(url_pattern, tex):
            assert path in source_index, (file.name, path)
            if first:
                data = (PAPER / source_index[path]['archived_path']).read_bytes()
                assert hashlib.sha256(data).hexdigest() == source_index[path]['sha256']
                line_count = len(data.decode('utf-8').splitlines())
                assert 1 <= int(first) <= int(last) <= line_count, (file.name, path, first, last)
            links.append({'tex': file.name, 'path': path, 'lines': [first, last]})
    report = {'commit': COMMIT, 'method': 'Targeted static proof-body reading; automated source identity, declaration and line-range checks.',
              'records': records, 'manuscript_pinned_source_links_checked': len(links),
              'verified_oai_closure_counts': closure_counts, 'unique_oai_closure_modules': len(all_modules)}
    (PAPER / 'research/depth/evidence.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (PAPER / 'audit/depth-evidence-verification.json').write_text(json.dumps({
        'commit': COMMIT, 'case_evidence_records': len(records), 'source_links_checked': len(links),
        'verified_oai_closure_counts': closure_counts, 'unique_oai_closure_modules': len(all_modules),
        'status': 'passed', 'scope': 'Byte identity and source locators; mathematical interpretations are the recorded static reading.'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case_evidence_records': len(records), 'source_links_checked': len(links)}))


if __name__ == '__main__':
    main()

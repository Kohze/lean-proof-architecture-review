"""Assemble primary-source references and retain publisher DOI evidence."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import html
import json
import re
import requests

PAPER = Path(__file__).resolve().parents[1]
COMMIT = 'fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb'

EXTRA = [
 ('Perfectoid2020','10.1145/3372885.3373830','https://arxiv.org/abs/1910.12320',
  'Sophisticated mathematical objects and reusable foundations in Lean.'),
 ('Schemes2021','10.1080/10586458.2021.1983489','https://arxiv.org/abs/2101.02602',
  'Alternative formal representations of schemes illustrate design choices.'),
 ('CertiCrypt2009','10.1145/1480881.1480894','https://software.imdea.org/~szanella/Zanella.2009.POPL.pdf',
  'Established observational-equivalence and probabilistic-program proof methodology.'),
 ('EasyCrypt2011','10.1007/978-3-642-22792-9_5','https://software.imdea.org/~szanella/Zanella.2011.CRYPTO.pdf',
  'Established computer-aided game-based cryptographic proofs.'),
 ('CakeML2014','10.1145/2535838.2535841','https://www.cl.cam.ac.uk/~mom22/popl14.pdf',
  'Verified compilation is an established method.'),
 ('Leroy2009','10.1145/1538788.1538814','https://xavierleroy.org/publi/compcert-CACM.pdf',
  'Compiler semantic preservation is an established independent proof obligation.'),
 ('ElliottRobertSantiago2011','10.1353/ajm.2011.0027','https://arxiv.org/abs/0805.3122',
  'Sections 3.1--3.2 contain ideal weights/idempotents, cut-sensitive convergence, and scalar-zero/infinity limits; these are classical mathematical antecedents of the reviewed formal architecture.'),
 ('CrouzeixPalencia2017','10.1137/17M1116672','https://arxiv.org/abs/1702.00668',
  'Established complete spectral-set bound 1+sqrt(2), used as an architecture comparator.'),
 ('BagnallStewartBanerjee2023','10.1145/3591220','https://arxiv.org/abs/2211.06747v3',
  'Zar is a Coq-verified compiler from probabilistic programs through choice-fix and interaction trees to random-bit samplers, with equidistribution correctness. This is a close baseline for the counting compiler; the reviewed OAI specification additionally tracks its own width, value-attribute and every-tape resource guarantees.')]

def crossref(doi):
    target = PAPER / 'research/bibliography' / (re.sub(r'[^a-zA-Z0-9]+','_',doi)+'.json')
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8'))
    r = requests.get('https://doi.org/'+doi,
                     headers={'Accept':'application/vnd.citationstyles.csl+json'}, timeout=45)
    r.raise_for_status()
    data = r.json()
    if 'message' in data:
        data = data['message']
    for field in ('title','container-title'):
        if isinstance(data.get(field),str):
            data[field] = [data[field]]
    assert data['DOI'].lower() == doi.lower()
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return data

def clean(value):
    value = html.unescape(re.sub('<[^>]+>','',str(value)))
    return value.replace('–','--').replace('—','---').replace('&',r'\&')

def main():
    base = json.loads((PAPER/'research/architecture/references.json').read_text(encoding='utf-8'))
    refs = base['references'] + base['additional_primary_software_sources']
    companions = PAPER/'research/companion-reviews.json'
    if companions.exists():
        refs += json.loads(companions.read_text(encoding='utf-8'))['references']
    additional = PAPER/'research/analysis/additional-prior-references.json'
    if additional.exists():
        extra_data = json.loads(additional.read_text(encoding='utf-8'))
        refs += extra_data['references']
    editorial = PAPER/'research/style-review/references.json'
    if editorial.exists():
        refs += json.loads(editorial.read_text(encoding='utf-8'))['references']
    for ref in refs:
        ref.setdefault('type', 'misc')
        ref.setdefault('year', 2026)
        if ref['key'] == 'HalesEtAl2017':
            ref['primary_url'] = ref['arxiv_url']
        if ref['key'] == 'CohenMahboubi2012':
            ref['printed_doi_variant'] = ref['doi']
            ref['doi'] = '10.2168/LMCS-8(1:2)2012'
            ref['doi_normalization_note'] = 'The journal prints 1:02; its resolving DOI and official project bibliography use 1:2.'
    # arXiv and SSRN identifiers describe preprints, not publisher-verified
    # journal articles. Retain their primary records without reclassifying them.
    dois = [r['doi'] for r in refs if r.get('doi') and not r['doi'].startswith(('10.48550/','10.2139/'))]
    dois += [x[1] for x in EXTRA]
    with ThreadPoolExecutor(max_workers=3) as executor:
        metadata = dict(zip(dois, executor.map(crossref,dois)))
    for key,doi,url,claim in EXTRA:
        data = metadata[doi]
        title = clean(data['title'][0])
        authors = [a.get('given','')+' '+a.get('family','') for a in data.get('author',[])]
        year = data.get('published-print',data.get('published',data.get('issued')))['date-parts'][0][0]
        refs.append({'key':key,'type':'article' if data['type']=='journal-article' else 'inproceedings',
                     'title':title, 'authors':authors,'year':year,
                     'venue':clean(data.get('container-title',[''])[0]),
                     'volume':data.get('volume'), 'pages':data.get('page'),
                     'doi':doi,'primary_url':url,'claim_supported':claim})
    for ref in refs:
        if ref['key'] == 'CakeML2014':
            ref['title'] = 'CakeML: A Verified Implementation of ML'
        if ref['key'] == 'EasyCrypt2011':
            ref['venue'] = 'Advances in Cryptology -- CRYPTO 2011'
            ref['series'] = 'Lecture Notes in Computer Science'
            ref['volume'] = '6841'
    artifacts = [
      ('OAIRepository','Mathematics manuscripts and supporting proof artifacts','README.md'),
      ('OAICatalog','Formalization catalogue','lean/formalization.yaml'),
      ('OAIComparator','Comparator verification configurations and instructions','lean/ComparatorChallenges/README.md'),
      ('OAICommonBases','Lean source for common-base approximate counting','lean/OAI/Combinatorics/MatroidCounting/CommonBases.lean'),
      ('OAISwitch','Lean source for switch-chain mixing','lean/OAI/Probability/SwitchChain/Main.lean'),
      ('OAIMahler','Lean source for the symmetric Mahler theorem','lean/OAI/Analysis/Mahler/MainTheorem.lean'),
      ('OAICrouzeix','Lean source for the complete Crouzeix bound','lean/OAI/Analysis/DirectCrouzeix/CompleteBound.lean'),
      ('OAITraceIdeals','Lean source for trace and ideal transport','lean/OAI/Analysis/TraceCone/IdealTransport.lean'),
      ('OAIAllSeams','Lean source for produced all-seams compatibility','lean/OAI/AlgebraicGeometry/CharacterVarieties/Seams/ProducedSolution.lean')]
    inventory = PAPER/'research/corpus-inventory.json'
    if inventory.exists():
        tree = json.loads(inventory.read_text(encoding='utf-8'))
        paths = {r['path']:r['git_blob_sha1'] for r in tree['selected_files']}
    else:
        tree = json.loads((PAPER.parents[1]/'tmp/lean-study/complete-git-tree.json').read_text(encoding='utf-8'))
        paths = {r['path']:r['sha'] for r in tree['tree']}
    for key,title,path in artifacts:
        assert path in paths, f'Invalid primary artifact path: {path}'
        refs.append({'key':key,'type':'misc','title':title,'authors':['OpenAI'],'year':2026,
                     'primary_url':f'https://github.com/openai/math/blob/{COMMIT}/{path}',
                     'note':'Repository artifact; accessed 8 October 2026',
                     'git_blob_sha1':paths[path], 'claim_supported':'Source-level case analysis; see research evidence ledger.'})
    refs.append({'key':'MathlibForms','type':'misc','title':'Differential forms: Mathlib source',
                 'authors':['The mathlib Community'],'year':2026,
                 'primary_url':'https://github.com/leanprover-community/mathlib4/blob/d13f23b723b8a846827a245b89c10fc7d3f11612/Mathlib/Analysis/Calculus/DifferentialForm/Basic.lean',
                 'note':'Pinned dependency source; accessed 8 October 2026',
                 'claim_supported':'Continuous alternating maps, Frechet exterior derivative, and d squared under smoothness.'})
    refs.extend([
        {'key':'LeanDecideSource','type':'misc',
         'title':'Tactic syntax and decision-procedure documentation: Lean 4.34.1 source',
         'authors':['The Lean developers'],'year':2026,
         'primary_url':'https://github.com/leanprover/lean4/blob/v4.34.1/src/Init/Tactics.lean',
         'note':'Version-pinned source, lines 1411--1430; accessed 8 October 2026',
         'claim_supported':'The documented semantics of decide +kernel in the reviewed Lean toolchain.'},
        {'key':'MathlibStyle','type':'misc','title':'Library Style Guidelines',
         'authors':['The mathlib Community'],'year':2026,
         'primary_url':'https://leanprover-community.github.io/contribute/style.html',
         'note':'Living contributor documentation; accessed 8 October 2026',
         'claim_supported':'Term and tactic styles, explicit local claims, and the context-dependent tradeoffs of squeezing simp calls.'}
    ])
    bib = []
    for ref in refs:
        doi = ref.get('doi')
        if doi in metadata:
            data = metadata[doi]
            ref['publisher_metadata_title'] = data['title'][0]
            ref['publisher_metadata_verified'] = True
            # Metadata title differences are retained for explicit human review.
        authors = ' and '.join('{'+a+'}' if a in ('OpenAI','The mathlib Community','Lean FRO','The Lean developers') else a for a in ref.get('authors',[]))
        fields = {'title':'{'+clean(ref['title'])+'}', 'author':authors, 'year':ref['year']}
        if ref.get('venue'):
            fields['journal' if ref['type']=='article' else 'booktitle'] = ref['venue']
        for key in ('volume','pages','doi','note'):
            if ref.get(key): fields[key] = clean(ref[key])
        for key in ('number','series','institution','eprint'):
            if ref.get(key): fields[key] = clean(ref[key])
        # plainnat omits the DOI field for misc entries. Print SSRN identifiers
        # through its standard howpublished field as well as retaining doi.
        if ref['type'] == 'misc' and ref.get('doi','').startswith('10.2139/'):
            fields['howpublished'] = r'\doi{' + ref['doi'] + '}'
        fields['url'] = ref['primary_url']
        bib.append('@'+ref['type']+'{'+ref['key']+',\n'+',\n'.join('  '+k+' = {'+str(v)+'}' for k,v in fields.items())+'\n}')
    rendered = '\n\n'.join(bib)+'\n'
    target = PAPER/'references.bib'
    if not target.exists() or target.read_text(encoding='utf-8') != rendered:
        target.write_text(rendered,encoding='utf-8',newline='\n')
    audit = PAPER/'audit'
    audit.mkdir(parents=True,exist_ok=True)
    (audit/'citation-verification.json').write_text(json.dumps({'date':'2026-10-09',
        'method':'Primary literature records plus retained DOI publisher metadata, and pinned Git-tree artifacts.',
        'references':refs,'reference_count':len(refs)},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'references':len(refs), 'crossref_records':len(metadata),
                      'metadata_title_pairs':[(r['key'],r['title'],r.get('publisher_metadata_title')) for r in refs if r.get('publisher_metadata_verified')]},ensure_ascii=True))

if __name__ == '__main__':
    main()

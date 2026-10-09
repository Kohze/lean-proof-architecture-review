"""Check citation coverage, publisher identities, PDF structure, and build logs."""
from pathlib import Path
import hashlib,json,re,unicodedata,textwrap
import bibtexparser
from pypdf import PdfReader

PAPER=Path(__file__).resolve().parents[1]

def normalized(text):
    text=unicodedata.normalize('NFKD',text).casefold()
    return re.sub(r'[^a-z0-9]','',text)

def main():
    texfiles=sorted(PAPER.glob('*.tex'))
    tex='\n'.join(p.read_text(encoding='utf-8') for p in texfiles)
    bibliography=bibtexparser.loads((PAPER/'references.bib').read_text(encoding='utf-8')).entries
    keys=[r['ID'] for r in bibliography]
    assert len(keys)==len(set(keys))
    cited={key.strip() for group in re.findall(r'\\cite\w*\{([^}]+)\}',tex) for key in group.split(',')}
    assert cited==set(keys), {'missing':sorted(cited-set(keys)),'unused':sorted(set(keys)-cited)}
    assert len(cited)>25
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert len(labels)==len(set(labels))
    refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex)
    assert set(refs)<=set(labels)
    # Literal proof excerpts must agree with the retained upstream lines.
    discussion=(PAPER/'discussion.tex').read_text(encoding='utf-8')
    excerpts=re.findall(r'\\begin\{lstlisting\}(?:\[[^\n]*\])?\n([\s\S]*?)\n\\end\{lstlisting\}',discussion)
    source_spans=[('Combinatorics/MatroidCounting/CommonBases.lean',16905,16907),
                  ('Analysis/DirectCrouzeix/DomainCore.lean',111,117)]
    assert len(excerpts)==len(source_spans)
    for excerpt,(path,first,last) in zip(excerpts,source_spans):
        source=(PAPER/'research/source/openai-math/lean/OAI'/path).read_text(encoding='utf-8').splitlines()
        assert excerpt==textwrap.dedent('\n'.join(source[first-1:last])),path
    disclosure='OpenAI Codex agents contributed substantially to source discovery, literature synthesis, and mathematical exposition.'
    assert tex.count(disclosure)==1
    assert 'Codex' not in (PAPER/'abstract.tex').read_text(encoding='utf-8')
    log=(PAPER/'audit/latex-final.log').read_text(encoding='utf-8')
    problems=[line for line in log.splitlines() if re.search(r'Overfull|undefined|Warning:|ignored error|Missing character|^!',line)]
    assert not problems,problems
    rendered=(PAPER/'audit/references-rendered.bbl').read_text(encoding='utf-8')
    assert rendered.count('\\bibitem')==len(cited)
    records=json.loads((PAPER/'audit/citation-verification.json').read_text(encoding='utf-8'))['references']
    metadata_checks=[]
    for record in records:
        doi=record.get('doi')
        if doi and not doi.startswith('10.48550/'):
            cache=PAPER/'research/bibliography'/(re.sub(r'[^a-zA-Z0-9]+','_',doi)+'.json')
            data=json.loads(cache.read_text(encoding='utf-8'))
            assert data['DOI'].casefold()==doi.casefold()
            titles=data['title']
            if isinstance(titles,str):titles=[titles]
            subtitle=data.get('subtitle',[])
            if isinstance(subtitle,str):subtitle=[subtitle]
            candidates=titles+[title+': '+sub for title in titles for sub in subtitle]
            assert normalized(record['title']) in [normalized(title) for title in candidates],(record['key'],candidates)
            metadata_checks.append({'key':record['key'],'doi':doi,'title_identity':True,
                                    'recorded_title':record['title'],'publisher_titles':candidates})
    pdfpath=PAPER/'lean-proof-architecture.pdf'
    reader=PdfReader(pdfpath)
    text='\n'.join(page.extract_text() for page in reader.pages)
    assert len(reader.pages)>10
    assert 'Robin Gounder' in text and 'Vaionex Corporation' in text
    assert 'Generative AI disclosure' in text
    assert 'OpenAI Codex' not in reader.pages[0].extract_text()
    assert all(len(page.extract_text().strip())>100 for page in reader.pages)
    assert (PAPER/'README.txt').is_file()
    for script in re.findall(r'python (reproduce/\S+\.py)',(PAPER/'README.txt').read_text(encoding='utf-8')):
        assert (PAPER/script).is_file(),script
    companions=[r for r in records if r.get('reference_category')=='companion_manuscript']
    scholarly=[r for r in records if r.get('doi') or r.get('type')=='techreport' or r in companions]
    preprints=[r for r in scholarly if r.get('doi','').startswith(('10.48550/','10.2139/')) or r in companions]
    technical=[r for r in scholarly if r.get('type')=='techreport']
    summary={'pages':len(reader.pages),'cited_references':len(cited),
             'scholarly_references':len(scholarly),'published_scholarly_references_with_doi':len(metadata_checks),
             'preprints':len(preprints),'technical_reports':len(technical),
             'companion_manuscript_references':len(companions),
             'source_and_software_references':len(cited)-len(scholarly),
             'unused_reference_keys':[],'missing_citation_keys':[], 'latex_problems':[],
             'doi_title_checks':metadata_checks,'disclosure_confined_to_dedicated_section':True, 'literal_upstream_lean_excerpts_checked':len(excerpts),
             'review_type':'Source-driven comparative narrative review with an exploratory corpus survey and original explanatory examples.',
             'novelty_scope':'Comparative synthesis and original descriptive corpus analysis; the elementary propositions are not presented as new theorems.',
             'pdf_sha256':hashlib.sha256(pdfpath.read_bytes()).hexdigest(),
             'tex_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in texfiles}}
    (PAPER/'audit/final-audit.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('doi_title_checks','tex_hashes')}))

if __name__=='__main__':main()

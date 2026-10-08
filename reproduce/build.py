"""Build the review in a disposable directory, then copy a stable PDF."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

PAPER = Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix='lean-proof-review-') as temporary:
        build = Path(temporary)
        for source in [*PAPER.glob('*.tex'), PAPER/'references.bib']:
            shutil.copy2(source,build/source.name)
        commands = [['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],
                    ['bibtex','main'],
                    ['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],
                    ['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex']]
        records=[]
        audit = PAPER/'audit'
        audit.mkdir(exist_ok=True)
        for index, command in enumerate(commands):
            run = subprocess.run(command,cwd=build,capture_output=True)
            (audit/f'build-pass-{index+1}.log').write_bytes(run.stdout+run.stderr)
            records.append({'command':command,'exit_code':run.returncode})
            if run.returncode:
                print((run.stdout+run.stderr).decode('utf-8',errors='replace')[-6000:])
                raise SystemExit(run.returncode)
        log=(build/'main.log').read_text(encoding='utf-8',errors='replace')
        # Pagination-sensitive references can need another pass after restructuring.
        for _ in range(2):
            if not re.search(r'Label\(s\) may have changed|Rerun to get cross-references right',log):
                break
            command=['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex']
            run=subprocess.run(command,cwd=build,capture_output=True)
            (audit/f'build-pass-{len(records)+1}.log').write_bytes(run.stdout+run.stderr)
            records.append({'command':command,'exit_code':run.returncode})
            if run.returncode:
                print((run.stdout+run.stderr).decode('utf-8',errors='replace')[-6000:])
                raise SystemExit(run.returncode)
            log=(build/'main.log').read_text(encoding='utf-8',errors='replace')
        (audit/'latex-final.log').write_text(log,encoding='utf-8')
        (audit/'bibliography-build.log').write_bytes((build/'main.blg').read_bytes())
        shutil.copy2(build/'main.bbl',audit/'references-rendered.bbl')
        warnings = [line for line in log.splitlines() if re.search(r'Overfull|undefined|LaTeX Warning|Package .*Warning',line)]
        target = PAPER/'lean-proof-architecture.pdf'
        shutil.copy2(build/'main.pdf',target)
        try:
            from pypdf import PdfReader
            pages=len(PdfReader(target).pages)
        except ImportError:
            pages=None
        record={'commands':records,'pages':pages,'warnings':warnings,
                'pdf_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        (audit/'build.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(record))

if __name__=='__main__': main()

"""Create a self-contained review archive and record its exact contents."""
from pathlib import Path
import hashlib,json,shutil,zipfile

PAPER=Path(__file__).resolve().parents[1]
WORKSPACE=PAPER.parents[1] if PAPER.parent.name=='papers' else PAPER

def files():
    for path in sorted(PAPER.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(PAPER)
        if relative.parts[0] in ('.git','output','tmp','build','dist'):continue
        if relative.parts[0].startswith('.venv') or relative.parts[0] in ('venv','.pytest_cache','.mypy_cache','.ruff_cache'):continue
        if '__pycache__' in relative.parts:continue
        if relative.parts[:3]==('research','architecture','source'):continue
        if relative.as_posix() in ('audit/artifact-manifest.json','audit/package.json'):continue
        yield path,relative

def main():
    manifest=[]
    for path,relative in files():
        manifest.append({'path':relative.as_posix(),'bytes':path.stat().st_size,
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest_path=PAPER/'audit/artifact-manifest.json'
    manifest_path.write_text(json.dumps({'files':manifest,'scope':'Self-contained manuscript package; self-referential package records excluded.'},indent=2)+'\n',encoding='utf-8')
    destination=WORKSPACE/'output/releases'
    destination.mkdir(parents=True,exist_ok=True)
    target=destination/'lean-proof-architecture-review.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for entry in manifest:
            archive.write(PAPER/entry['path'],'lean-proof-architecture/'+entry['path'])
        archive.write(manifest_path,'lean-proof-architecture/audit/artifact-manifest.json')
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for entry in manifest:
            data=archive.read('lean-proof-architecture/'+entry['path'])
            assert hashlib.sha256(data).hexdigest()==entry['sha256']
    pdfout=WORKSPACE/'output/pdf'
    pdfout.mkdir(parents=True,exist_ok=True)
    shutil.copy2(PAPER/'lean-proof-architecture.pdf',pdfout/'lean-proof-architecture.pdf')
    record={'archive':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'files_in_archive':len(manifest)+1,'bytes':target.stat().st_size,
            'status':'Local package; no external submission or publication performed.'}
    (PAPER/'audit/package.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()

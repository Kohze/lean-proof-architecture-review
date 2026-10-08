"""Rehash curated external sources against the pinned Git inventory."""
from pathlib import Path
import hashlib,json

PAPER=Path(__file__).resolve().parents[1]

def main():
    inventory=json.loads((PAPER/'research/corpus-inventory.json').read_text(encoding='utf-8'))
    records=[]
    for entry in inventory['selected_files']:
        source=PAPER/entry['archived_path']
        data=source.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        sha=hashlib.sha256(data).hexdigest()
        assert blob==entry['git_blob_sha1'],source
        assert sha==entry['sha256'],source
        records.append({'path':entry['path'],'git_blob_sha1':blob,'sha256':sha})
    record={'commit':inventory['commit'],'source_files_verified':len(records),
            'scope':'Byte identity of curated sources; independent of proof compilation.',
            'files':records}
    (PAPER/'audit/source-integrity.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_files_verified':len(records),'commit':inventory['commit']}))

if __name__=='__main__':main()

"""Compile the original examples with the corpus toolchain and retain evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PAPER=Path(__file__).resolve().parents[1]
TOOLCHAIN='leanprover/lean4:v4.34.1'

def main():
    results=PAPER/'results'
    results.mkdir(exist_ok=True)
    version=subprocess.run(['lean','+'+TOOLCHAIN,'--version'],capture_output=True,check=True)
    command=['lean','+'+TOOLCHAIN,str(PAPER/'reproduce/InterfaceExamples.lean')]
    run=subprocess.run(command,capture_output=True)
    (results/'lean-compiler.log').write_bytes(run.stdout+run.stderr)
    output=run.stdout.decode('utf-8',errors='replace')
    expected=['physicalIndex_injective','physicalIndex_lt','moment_indicator',
              'all_observables_determine_counts','normalized_observables_determine_counts']
    axioms={}
    for name in expected:
        matching=[line for line in output.splitlines() if "'InterfaceExamples."+name+"' depends on axioms:" in line]
        assert len(matching)==1, (name,matching)
        assert matching[0].endswith('[propext, Quot.sound]'),matching[0]
        axioms[name]=['propext','Quot.sound']
    assert run.returncode==0
    assert 'warning:' not in output and 'sorryAx' not in output
    run_python=subprocess.run([sys.executable,str(PAPER/'reproduce/check_examples.py')],capture_output=True,check=True)
    record={'command':command,'toolchain':TOOLCHAIN,'version':version.stdout.decode().strip(),
            'exit_code':run.returncode,'reported_axioms':axioms,
            'lean_source_sha256':hashlib.sha256((PAPER/'reproduce/InterfaceExamples.lean').read_bytes()).hexdigest(),
            'finite_check_exit_code':run_python.returncode,
            'scope':'Original review examples; source-corpus endpoints were studied statically.'}
    (results/'verification.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()

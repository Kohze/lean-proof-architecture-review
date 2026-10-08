"""Exact finite checks of the review's own worked examples; no external libraries."""
from collections import Counter
from itertools import product
from pathlib import Path
from fractions import Fraction
import json

PAPER = Path(__file__).resolve().parents[1]

def main():
    fibers = []
    for m in range(5):
        for start in range(3):
            B = start + 3*m + 1
            positions = [start + 3*(m-1-i) + 1 for i in range(m)]
            assert len(set(positions)) == m and all(i < B for i in positions)
            counts = Counter(tuple(tape[i] for i in positions)
                             for tape in product((0,1), repeat=B))
            assert len(counts) == 2**m
            assert set(counts.values()) == {2**(B-m)}
            fibers.append({'m':m, 'start':start, 'B':B, 'positions':positions,
                           'output_words':len(counts), 'fiber_cardinality':2**(B-m)})
    matrices = list(product((0,1), repeat=4))
    table = []
    for r in range(3):
        row = []
        for c in range(3):
            count = sum(a+b+c0+d==2 and a+b==r and a+c0==c
                        for a,b,c0,d in matrices)
            assert count == 2 - int(r!=1) - int(c!=1)
            row.append(count)
        table.append(row)
    assert table == [[0,1,0],[1,2,1],[0,1,0]]
    six=[(a+b,a+c) for a,b,c,d in matrices if a+b+c+d==2]
    mean_left=Fraction(sum(r!=1 for r,c in six),len(six))
    mean_right=Fraction(sum(c!=1 for r,c in six),len(six))
    joint=Fraction(sum(r!=1 and c!=1 for r,c in six),len(six))
    covariance=joint-mean_left*mean_right
    assert (mean_left,mean_right,joint,covariance)==(Fraction(1,3),Fraction(1,3),0,Fraction(-1,9))
    # A tight compositional example: a lost a-outcome is explicit failure,
    # and the actual fixed tape projection supplies the bounded word law.
    ideal={'a':Fraction(6,8),'b':Fraction(2,8)}
    bounded=('a',)*5+('b',)*2+(None,)
    bounded_mass={x:Fraction(bounded.count(x),len(bounded)) for x in ideal}
    indicator_losses=[sum(ideal[x]-bounded_mass[x] for x,on in zip(ideal,mask) if on)
                      for mask in product((False,True),repeat=len(ideal))]
    eta=max(indicator_losses)
    assert eta==Fraction(1,8)
    m,B,start=3,10,0
    positions=[start+3*(m-1-i)+1 for i in range(m)]
    actual=Counter(bounded[sum(tape[pos] << i for i,pos in enumerate(positions))]
                   for tape in product((0,1),repeat=B))
    delta0=1-ideal['a']
    assert actual==Counter({'a':640,'b':256,None:128})
    assert Fraction(actual['a'],2**B)==1-delta0-eta==Fraction(5,8)
    result = {'status':'passed', 'method':'exhaustive finite enumeration',
              'physical_tape_fibers':fibers, 'two_by_two_binary_total_two_counts':table,
              'binary_matrices_enumerated':len(matrices),
              'uniform_total_two_flag_example':{'matrices':len(six),
                'left_mean':str(mean_left),'right_mean':str(mean_right),
                'joint_mean':str(joint),'covariance':str(covariance)},
              'composed_success_budget_example':{
                'ideal_event_probability':str(ideal['a']),
                'bounded_event_probability':str(bounded_mass['a']),
                'maximum_indicator_loss':str(eta),'ideal_failure_budget':str(delta0),
                'word_bits':m,'tape_bits':B,'positions':positions,
                'successful_tapes':actual['a'],'all_tapes':2**B,
                'failure_tapes':actual[None],
                'scope':'Original tight finite fixture, not a run of the upstream rejection sampler.'},
              'scope':'Finite examples of general arguments explained in the review.'}
    target = PAPER / 'results/worked-examples.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Passed: 15 tape-fiber checks, all 16 binary matrices, and the tight 640/1024 success-budget example.')

if __name__ == '__main__':
    main()

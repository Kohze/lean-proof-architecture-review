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
    result = {'status':'passed', 'method':'exhaustive finite enumeration',
              'physical_tape_fibers':fibers, 'two_by_two_binary_total_two_counts':table,
              'binary_matrices_enumerated':len(matrices),
              'uniform_total_two_flag_example':{'matrices':len(six),
                'left_mean':str(mean_left),'right_mean':str(mean_right),
                'joint_mean':str(joint),'covariance':str(covariance)},
              'scope':'Finite examples of general arguments explained in the review.'}
    target = PAPER / 'results/worked-examples.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Passed: 15 exact tape-fiber checks and all 16 binary 2-by-2 matrices.')

if __name__ == '__main__':
    main()

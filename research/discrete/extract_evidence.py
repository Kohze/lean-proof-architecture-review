from pathlib import Path
import json,hashlib,re
COMMIT='fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb'
ROOT=Path('tmp/lean-study/source')
OUT=Path('papers/lean-proof-architecture/research/discrete')
tree=json.loads(Path('tmp/lean-study/complete-git-tree.json').read_text(encoding='utf-8'))
index={x['path']:x['sha'] for x in tree['tree'] if x['type']=='blob'}
CB='lean/OAI/Combinatorics/MatroidCounting/CommonBases.lean'
SW='lean/OAI/Probability/SwitchChain/'
specs=[
 ('cb.target',CB,'common_bases_fpras'),('cb.statement',CB,'MainTheorem'),
 ('cb.oracle',CB,'ExactOracles'),('cb.count',CB,'commonBaseCount'),
 ('cb.instructions',CB,'Instruction'),('cb.step',CB,'machineStep'),
 ('cb.resource',CB,'resourceBound'),('cb.paired',CB,'pairedMatroid'),
 ('cb.transversal',CB,'transversal'),('cb.base_equiv',CB,'transversal_isBase_iff'),
 ('cb.deficiency',CB,'subsetDeficiency_zero'),('cb.count_transfer',CB,'zeroDeficiency_eq_commonBaseCount'),
 ('cb.partition_transfer',CB,'plainPartition_eq_subsets'),('cb.contamination',CB,'paired_partition_contamination'),
 ('cb.tree',CB,'DrawTree'),('cb.tree_run',CB,'run',9304),('cb.tree_lower',CB,'run_lower'),
 ('cb.oracle_rank',CB,'rankOracle'),('cb.oracle_rank_correct',CB,'rankOracle_correct'),
 ('cb.oracle_weight',CB,'oracleAnneal'),('cb.guard',CB,'oracleGuard'),
 ('cb.oracle_semantics',CB,'oracleDeficiency_eq'),('cb.reindex',CB,'Reindexed'),
 ('cb.reindex_expectation',CB,'Reindexed.expectation'),('cb.walk',CB,'canonicalMetropolis'),
 ('cb.algorithm_tree',CB,'canonicalAlgorithmTree'),('cb.canonical_correct',CB,'canonical_bounded_fair_experiment'),
 ('cb.bounded',CB,'Bounded'),('cb.types',CB,'DataType'),('cb.values',CB,'Value'),
 ('cb.encode',CB,'encode',16289),('cb.expression',CB,'Expression'),('cb.compile',CB,'compile'),
 ('cb.evaluate',CB,'evaluate'),('cb.compile_correct',CB,'compile_correct'),
 ('cb.run',CB,'run',16625),('cb.safe',CB,'Safe'),('cb.effect',CB,'Effect'),
 ('cb.bank_eval',CB,'bankEval'),('cb.realizes',CB,'Realizes'),('cb.realizes_law',CB,'RealizesLaw'),
 ('cb.proposal',CB,'proposal'),('cb.proposal_source',CB,'proposal_source'),
 ('cb.walk_code',CB,'stepCode'),('cb.walk_source',CB,'stepCode_source'),
 ('cb.algorithm_code',CB,'algorithmCode'),('cb.algorithm_source',CB,'algorithmCode_source'),
 ('cb.preamble',CB,'preambleCode'),('cb.postamble',CB,'postambleCode'),
 ('cb.compile_bound',CB,'compile_safe_bound'),('cb.compile_majorant',CB,'compile_majorant'),
 ('cb.uniform_safe',CB,'frozen_uniform_safe'),('cb.physical',CB,'physicalWord'),
 ('cb.physical_injective',CB,'physicalPosition_injective'),('cb.physical_law',CB,'physicalWord_law'),
 ('cb.program',CB,'fprasBlock'),('cb.output_certificate',CB,'OutputCertificate'),
 ('cb.certificate_exists',CB,'output_certificate'),('cb.machine_transfer',CB,'frozen_machine'),
 ('cb.accuracy_transfer',CB,'physical_accuracy'),
 ('sw.target',SW+'Main.lean','switch_chain_main'),
 ('sw.graphs',SW+'Definitions.lean','GraphState'),('sw.proposals',SW+'Definitions.lean','SwitchProposal'),
 ('sw.cell',SW+'DisjointEncoding.lean','SameCell'),
 ('sw.cell_injective',SW+'DisjointEncoding.lean','graph_eq_of_cell_coordinates'),
 ('sw.degree_feasible',SW+'DisjointCoordinateFeasibility.lean','coordinate_degrees_iff'),
 ('sw.margin',SW+'DisjointCellCounting.lean','MarginData'),
 ('sw.joint',SW+'DisjointCellCounting.lean','JointData'),
 ('sw.coordinate_equiv',SW+'DisjointCellCounting.lean','coordinatesEquiv'),
 ('sw.count_transfer',SW+'DisjointCellCounting.lean','sum_degreeCell_joint'),
 ('sw.cross',SW+'CrossMatrix.lean','Matrix'),('sw.cross_count',SW+'CrossMatrix.lean','count'),
 ('sw.count_two',SW+'CrossMatrix.lean','count_two'),
 ('sw.count_real',SW+'CrossMatrix.lean','count_two_real'),
 ('sw.product',SW+'CrossIndependent.lean','count_eq_independent_product'),
 ('sw.cross_cell',SW+'CrossCellMoments.lean','Cell'),
 ('sw.conditional_span',SW+'CrossCellMoments.lean','conditionalRight_two_span'),
 ('sw.affine',SW+'CrossCellAffineComposition.lean','expectation_first_second_affine'),
 ('sw.state_equiv',SW+'DisjointCrossCellEquiv.lean','stateCellCrossEquiv'),
 ('sw.pullback',SW+'DisjointCrossCellEquiv.lean','expectation_ker_pullback'),
 ('sw.restriction',SW+'DisjointGraphAffine.lean','crossCellRestriction'),
 ('sw.graph_affine',SW+'DisjointGraphAffine.lean','right_left_expectation_cell_affine'),
 ('sw.flag_correspondence',SW+'DisjointEqualityFlags.lean','stateLeftFlag_eq_observable'),
 ('sw.observable',SW+'PairEqualityProjection.lean','observable'),
 ('sw.equality_space',SW+'PairEqualityProjection.lean','equalitySpace'),
 ('sw.affine_image',SW+'PairAffineInteraction.lean','AffineFlagImage'),
 ('sw.error_projection',SW+'PairAffineInteraction.lean','fluctuation_mem_of_affineFlagImage'),
 ('sw.interaction',SW+'PairActualAffine.lean','actual_named_interaction'),
 ('sw.interaction_general',SW+'ProjectionRangeInteraction.lean','interaction_of_correlated_error_ranges'),
 ('sw.budget',SW+'PairEqualityBudgetUnordered.lean','pair_projection_budget'),
 ('sw.assembly',SW+'PairDisjointAssembly.lean','disjoint_sum_nonneg_of_named_interaction_budget'),
 ('sw.spectral',SW+'LocalGapEndgame.lean','spectralGap_of_triples_and_disjoint'),
]
cache={}; evidence=[]
def lines(path):
 if path not in cache: cache[path]=(ROOT/path).read_text(encoding='utf-8').splitlines()
 return cache[path]
decl=re.compile(r'^(?:noncomputable\s+)?(?:def|abbrev|lemma|theorem|inductive|structure)\s+')
for spec in specs:
 ident,path,name,*preferred=spec
 ls=lines(path)
 pat=re.compile(r'^(?:@\[[^\]]+\]\s*)?(?:noncomputable\s+)?(?:def|abbrev|lemma|theorem|inductive|structure)\s+'+re.escape(name)+r'(?=[\s:{(]|$)')
 hits=[i for i,l in enumerate(ls) if pat.match(l)]
 if preferred: hits=sorted(hits,key=lambda i:abs(i+1-preferred[0]))
 if not hits: raise ValueError((ident,name))
 start=hits[0]; end=next((i for i in range(start+1,len(ls)) if decl.match(ls[i]) or re.match(r'^@\[.*\]\s+(?:lemma|theorem)',ls[i])),len(ls))
 excerpt_end=min(end,start+12)
 evidence.append({'id':ident,'path':path,'declaration':name,'start_line':start+1,'end_line':end,
  'git_blob_sha1':index[path],'url':f'https://github.com/openai/math/blob/{COMMIT}/{path}#L{start+1}-L{end}',
  'excerpt_start_line':start+1,'excerpt_end_line':excerpt_end,'excerpt':'\n'.join(ls[start:excerpt_end])})
manifest=[]
for path in sorted(cache):
 data=(ROOT/path).read_bytes(); blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 assert blob==index[path],(path,blob,index[path])
 manifest.append({'path':path,'bytes':len(data),'lines':len(cache[path]),'git_blob_sha1':blob,
   'sha256':hashlib.sha256(data).hexdigest(),'imports':[l[7:] for l in cache[path] if l.startswith('import ')]})
(OUT/'evidence.json').write_text(json.dumps({'commit':COMMIT,'verification':'Pinned raw source bytes independently match the complete Git tree blob IDs. Source inspection only; no Lean build, kernel audit, or execution benchmark was run by this research agent.','evidence':evidence},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'source-manifest.json').write_text(json.dumps({'commit':COMMIT,'files':manifest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'evidence_records':len(evidence),'source_files':len(manifest),'verified_git_blob_ids':len(manifest)}))

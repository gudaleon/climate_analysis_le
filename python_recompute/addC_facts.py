"""Addendum C: build the facts layers on out_addC/idx (London on Branch P, everything else identical to
the main layer) with facts.build at its default ROUND=6, for both observation layers."""
import sys, pickle
sys.path.insert(0, 'code')
import facts
for branch, tag in (('AUTHORS_v4', 'AUTHORS_v4'), ('H1_reviewed', 'H1_reviewed')):
    F = facts.build(branch, idxdir='out_addC/idx')
    pickle.dump(F, open(f'out_addC/facts_P_{tag}.pkl', 'wb'))
    print('built', tag, flush=True)

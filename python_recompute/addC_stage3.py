"""Addendum C, Stage 3: the matched-granularity contrast between the two post hoc methods, extended to
the third station, London. The matched level is exactly the one Addendum B's Stage 3 stated before
computing: one output per index per method component, at the aggregation level at which each method
speaks about an index at a station.
- Bounding method: (i) the v7 envelope classification of the observed H->P change (bounded / unbounded /
  sign_reversal), and (ii) the Table C1 pooled Overall Shift label for the index (executed pooling,
  observations included in H and P as the code ran; the models-only label is recorded as a secondary line).
- Arrow method: for each printed contrast (H->P, H->N, H->F), the pair (sign of the pooled-ensemble median
  change; majority direction of the ten models' median changes, where a direction held by more than half of
  the models with a defined change is the majority and anything else is 'split').
An output changes when any of its components differs between the branches.
Primary layer V4 (authors' homogenised observations); the H1 layer is computed for the bounding
classification as a robustness check. Fergus and Harrow rows are recomputed from Addendum A's and
Addendum B's saved facts objects by the same code, as a machinery check against Addendum B's table."""
import sys, pickle, numpy as np
import pandas as pd
sys.path.insert(0, 'code')
from analysis import MODELS
from cdx import INDICES
from v7branch import c1 as c1tab

def load(p): return pickle.load(open(p, 'rb'))
CASES = {}
for lay, t, fS, hP, lP in (('V4', 'out/facts_AUTHORS_v4.pkl', 'out_addA/facts_S_AUTHORS_v4.pkl', 'out_addB/facts_P_AUTHORS_v4.pkl', 'out_addC/facts_P_AUTHORS_v4.pkl'),
                           ('H1', 'out/facts_H1_reviewed.pkl', 'out_addA/facts_S_H1_reviewed.pkl', 'out_addB/facts_P_H1_reviewed.pkl', 'out_addC/facts_P_H1_reviewed.pkl')):
    FT = load(t)
    CASES[(lay, 'Fergus', 'T')] = FT; CASES[(lay, 'Fergus', 'S')] = load(fS)
    CASES[(lay, 'Harrow', 'T')] = FT; CASES[(lay, 'Harrow', 'P')] = load(hP)
    CASES[(lay, 'London', 'T')] = FT; CASES[(lay, 'London', 'P')] = load(lP)

def sgn(d):
    if d is None or (isinstance(d, float) and np.isnan(d)): return 'n/a'
    return '–' if abs(d) < 1e-9 else ('↑' if d > 0 else '↓')

def outputs(F, st):
    """All matched-level outputs for one station on one branch/layer (addB_stage3.outputs, unchanged)."""
    pc = F['pc'][F['pc'].station == st]
    env = F['env'][F['env'].station == st].set_index('index')
    c1e = c1tab(F, include_obs=True).set_index(['station', 'index']).label
    c1m = c1tab(F, include_obs=False).set_index(['station', 'index']).label
    out = {}
    for ix in INDICES:
        out[(ix, 'env')] = env.loc[ix, 'cv7']
        out[(ix, 'c1')] = c1e.loc[(st, ix)]
        out[(ix, 'c1m')] = c1m.loc[(st, ix)]
        for comp in 'PNF':
            ens = pc[(pc['index'] == ix) & (pc.source == 'ENS') & (pc.comp == comp)].delta.iloc[0]
            md = pc[(pc['index'] == ix) & (pc.source.isin(MODELS)) & (pc.comp == comp)].delta.values
            signs = [sgn(d) for d in md if not (isinstance(d, float) and np.isnan(d))]
            maj = 'split'
            for s in ('↑', '↓', '–'):
                if signs.count(s) > len(signs) / 2: maj = s
            out[(ix, f'arr_{comp}')] = f'{sgn(ens)}|{maj}'
    return out

rows = []
for lay in ('V4', 'H1'):
    for st, other in (('Fergus', 'S'), ('Harrow', 'P'), ('London', 'P')):
        A = outputs(CASES[(lay, st, 'T')], st); B = outputs(CASES[(lay, st, other)], st)
        for k in A:
            rows.append(dict(layer=lay, station=st, index=k[0], output=k[1], T=A[k], other=B[k], changed=A[k] != B[k]))
d = pd.DataFrame(rows)
d.to_csv('out_addC/stage3_matched.csv', index=False)
for (lay, st), g in d.groupby(['layer', 'station']):
    env = g[g.output == 'env']; c1 = g[g.output == 'c1']; c1m = g[g.output == 'c1m']; arr = g[g.output.str.startswith('arr')]
    btouch = len(set(env[env.changed]['index']) | set(c1[c1.changed]['index']))
    print(f"{lay} {st}: envelope classifications changed {int(env.changed.sum())}/44; "
          f"C1 labels (executed pooling) changed {int(c1.changed.sum())}/44; C1 labels (models-only) changed {int(c1m.changed.sum())}/44; "
          f"bounding outputs changed {int(env.changed.sum()) + int(c1.changed.sum())}/88 over {btouch} indices; "
          f"arrow index-contrast outputs changed {int(arr.changed.sum())}/132 over {arr[arr.changed]['index'].nunique()} indices")
    for name, gg in (('env', env), ('c1', c1), ('c1m', c1m), ('arrow', arr)):
        ch = gg[gg.changed]
        if len(ch): print('  ', name, 'changes:', '; '.join(f"{r['index']} {r['output']}: {r['T']} -> {r['other']}" for r in ch.to_dict('records')))

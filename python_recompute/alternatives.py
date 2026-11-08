import sys, pickle, json, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from analysis import *
from cdx import INDICES, TEMP
from v7branch import skill_change
R = {}
F = pickle.load(open('out/facts_AUTHORS_v4.pkl', 'rb'))
e = F['env']
# 1. envelope permutation null: permute observed changes across stations within index (keeps units), and across indices within
#    station using standardised changes (obs / model-range scale)
rng = np.random.default_rng(1)
o = e.pivot(index='index', columns='station', values='obs'); lo = e.pivot(index='index', columns='station', values='lo'); hi = e.pivot(index='index', columns='station', values='hi')
null1 = []
for _ in range(5000):
    perm = o.apply(lambda r: pd.Series(rng.permutation(r.values), index=r.index), axis=1)
    null1.append(int(((perm >= lo - 1e-9) & (perm <= hi + 1e-9)).values.sum()))
R['null_perm_stations'] = dict(mean=float(np.mean(null1)), p95=float(np.percentile(null1, 95)), p_ge_115=float(np.mean(np.array(null1) >= 115)))
# null 2: observed change replaced by an independent draw: sign-flip of observed change (direction independent of models)
null2 = []
for _ in range(5000):
    s = rng.choice([-1, 1], size=o.shape)
    null2.append(int(((o * s >= lo - 1e-9) & (o * s <= hi + 1e-9)).values.sum()))
R['null_signflip'] = dict(mean=float(np.mean(null2)), p95=float(np.percentile(null2, 95)), p_ge_115=float(np.mean(np.array(null2) >= 115)))
# null 3: across indices within station, standardised by model-envelope centre/width
z = (o - (lo + hi) / 2) / ((hi - lo) / 2).replace(0, np.nan)
R['share_obs_zero_and_range_includes_zero'] = int(((o.abs() < 1e-9) & (lo <= 0) & (hi >= 0)).values.sum())
null3 = []
for _ in range(5000):
    zz = z.apply(lambda c: pd.Series(rng.permutation(c.values), index=c.index), axis=0)
    null3.append(int((zz.abs() <= 1 + 1e-9).values.sum()))
R['null_perm_indices_standardised'] = dict(mean=float(np.nanmean(null3)), p95=float(np.percentile(null3, 95)))
# 2. leave-one-model-out
loo = {}
for m in MODELS:
    keep = [x for x in MODELS if x != m]
    ee = envelope(F['pc'], keep)
    cc = F['pc'][F['pc'].source.isin(keep)]
    cons = consensus_k(F['pc'], keep) if 'consensus_k' in globals() else None
    loo[m] = dict(within=int(ee.within.sum()), rev613=int((ee.c613 == 'reversal').sum()), signrev_v7=int((ee.cv7 == 'sign_reversal').sum()))
R['leave_one_out'] = loo
# consensus with 9 models: >=8 of 9 and >=7 of 9 (same 80% share ~ 7.2)
def cons9(pc, keep, thr):
    out = {}
    for st in ST:
        for comp in 'NF':
            s = pc[(pc.station == st) & (pc.comp == comp) & pc.source.isin(keep)]
            g = s.groupby('index').apply(lambda d: max(((d.delta > 0) & (d.p < 0.05)).sum(), ((d.delta < 0) & (d.p < 0.05)).sum()) >= thr)
            out[f'{st}_{comp}'] = int(g.sum())
    return out
R['consensus_loo_range'] = {}
for thr in (8, 7):
    vals = {m: cons9(F['pc'], [x for x in MODELS if x != m], thr) for m in MODELS}
    R['consensus_loo_range'][f'>={thr}of9'] = {k: [min(v[k] for v in vals.values()), max(v[k] for v in vals.values())] for k in vals['ACCESS']}
# 3. reversal definitions cross-applied: counts under each
R['reversal_defs'] = dict(r613_median=int((e.c613 == 'reversal').sum()), v7_entire_interval=int((e.cv7 == 'sign_reversal').sum()),
                          opposite_every_model=int(e.opposite_all.sum()),
                          r613_list=e[e.c613 == 'reversal'][['station', 'index']].values.tolist(),
                          v7_list=e[e.cv7 == 'sign_reversal'][['station', 'index']].values.tolist(),
                          magnitude_613=e[e.c613 == 'magnitude'][['station', 'index']].values.tolist())
# 4. Wilcoxon variants: pass counts and refs
D = F['D']
var = {}
for name, kw in {'printed(asym,cc)': dict(), 'asym,no_cc': dict(correct=False), 'exact(scipy)': dict(exact=True)}.items():
    mp = model_performance(D, **kw)
    pcn = pass_counts(mp)
    rf = ref_models(mp)
    var[name] = dict(refs={k: v['temp_ref'] for k, v in rf.items() if isinstance(v, dict) and 'temp_ref' in v}, precip_ref=rf['precip_ref'],
                     precip_sum=rf['precip_sum'], temp_scores={k: v['temp_scores'] for k, v in rf.items() if isinstance(v, dict) and 'temp_scores' in v},
                     nan_cells=int(mp.p.isna().sum()))
    rfn = ref_models(mp, nan_pass=True)
    var[name]['refs_nan_as_pass'] = {k: v['temp_ref'] for k, v in rfn.items() if isinstance(v, dict) and 'temp_ref' in v}
    var[name]['temp_scores_nan_as_pass'] = {k: v['temp_scores'] for k, v in rfn.items() if isinstance(v, dict) and 'temp_scores' in v}
    sc, _ = skill_change(dict(F, mp=mp))
    var[name]['skill_vs_change'] = sc['>=10of20']
R['wilcox_variants'] = var
json.dump(R, open('out/alternatives.json', 'w'), indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x))
print(json.dumps({k: R[k] for k in ['null_perm_stations', 'null_signflip', 'null_perm_indices_standardised', 'leave_one_out', 'consensus_loo_range', 'reversal_defs']}, indent=0, default=str)[:4000])
for k, v in var.items():
    print(k, v['refs'], v['refs_nan_as_pass'], v['precip_ref'], v['nan_cells'], {kk: (vv['misjudged'], round(vv['fisher_p'], 3)) for kk, vv in [('s', v['skill_vs_change'])]})

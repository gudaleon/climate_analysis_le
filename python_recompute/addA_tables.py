"""Addendum A: Branch T vs Branch S tables for Fergus (items 1, 2, 3, 5 of the brief). Primary layer V4 (authors'
homogenised v4 observations; my indices and statistics); Pass-1 layer H1 (my own homogenisation) as a check."""
import sys, pickle, json, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from analysis import MODELS, PER, per
from cdx import INDICES, TEMP
from v7branch import skill_change, c1 as c1tab, d1 as d1tab
LAY = sys.argv[1] if len(sys.argv) > 1 else 'AUTHORS_v4'
T = pickle.load(open(f'out/facts_{LAY}.pkl', 'rb')); S = pickle.load(open(f'out_addA/facts_S_{LAY}.pkl', 'rb'))
ST = 'Fergus'; R = {}
UNITS = {}
# ---------- 1. annual values: per model x period medians, and annual cell diffs
rows = []; cells = []
for ix in INDICES:
    for m in MODELS:
        a, b = T['D'][(ST, m)][ix], S['D'][(ST, m)][ix]
        d = (b - a).dropna()
        cells.append(dict(index=ix, model=m, n_diff=int((d.abs() > 1e-9).sum()), mean_SminusT=d.mean(), maxabs=d.abs().max(),
                          nan_mismatch=int((a.isna() != b.isna()).sum())))
        for p in PER:
            rows.append(dict(index=ix, model=m, period=p, T=np.median(per(T['D'][(ST, m)], p, ix)) if len(per(T['D'][(ST, m)], p, ix)) else np.nan,
                             S=np.median(per(S['D'][(ST, m)], p, ix)) if len(per(S['D'][(ST, m)], p, ix)) else np.nan))
mm = pd.DataFrame(rows); mm['d'] = mm['S'] - mm['T']
cd = pd.DataFrame(cells)
pt = T['pmed'][T['pmed'].station == ST].set_index('index'); ps = S['pmed'][S['pmed'].station == ST].set_index('index')
pm = pd.DataFrame({f'{k}_{p}': (pt if k == 'T' else ps)[f'pooled_{p}'] for p in PER for k in 'TS'})
for p in PER: pm[f'd_{p}'] = pm[f'S_{p}'] - pm[f'T_{p}']
# model spread of period medians (per branch) for item 5
for p in PER:
    for k, F in (('T', pt), ('S', ps)):
        pm[f'spread{k}_{p}'] = F[f'maxmodel_{p}'] - F[f'minmodel_{p}']
mm.to_csv(f'out_addA/fergus_model_period_medians_{LAY}.csv', index=False); cd.to_csv(f'out_addA/fergus_annual_cell_diffs_{LAY}.csv', index=False)
pm.to_csv(f'out_addA/fergus_pooled_period_medians_{LAY}.csv')
# ---------- 2. Test 1
def t1(F):
    mp = F['mp'][F['mp'].station == ST].copy(); mp['ok'] = mp.p >= 0.05
    pc = mp.groupby(['model', 'group', 'period']).ok.sum().unstack(['group', 'period'])
    both = mp[mp.group == 'T'].groupby(['model', 'index']).ok.all().groupby('model').sum()
    out = pd.DataFrame({'T_H': pc[('T', 'H')], 'T_P': pc[('T', 'P')], 'P_H': pc[('P', 'H')], 'P_P': pc[('P', 'P')]})
    out['T_tot'] = out.T_H + out.T_P; out['P_tot'] = out.P_H + out.P_P; out['both_T'] = both; out['all_tot'] = out.T_tot + out.P_tot
    out['nan_cells'] = mp.groupby('model').p.apply(lambda s: int(s.isna().sum()))
    return out.loc[MODELS]
t1T, t1S = t1(T), t1(S)
def basinP(F):
    mp = F['mp'].copy(); mp['ok'] = mp.p >= 0.05
    return mp[mp.group == 'P'].groupby(['model', 'station']).ok.sum().unstack()
bT, bS = basinP(T), basinP(S)
# ---------- 3. change layer
def chlayer(F):
    e = F['env'][F['env'].station == ST].set_index('index')
    pc = F['pc'][F['pc'].station == ST]
    return e, pc
eT, pcT = chlayer(T); eS, pcS = chlayer(S)
arr = []
for ix in INDICES:
    for src in ['OBS'] + MODELS + ['ENS']:
        for comp in (['P'] if src == 'OBS' else ['P', 'N', 'F']):
            a = pcT[(pcT['index'] == ix) & (pcT.source == src) & (pcT.comp == comp)].iloc[0]
            b = pcS[(pcS['index'] == ix) & (pcS.source == src) & (pcS.comp == comp)].iloc[0]
            f = lambda r: ('n/a' if np.isnan(r.delta) else ('–' if abs(r.delta) < 1e-9 else ('↑' if r.delta > 0 else '↓'))) + ('*' if (not np.isnan(r.delta) and abs(r.delta) > 1e-9 and r.p < 0.05) else '')
            arr.append(dict(index=ix, source=src, comp=comp, T=f(a), S=f(b), dT=a.delta, dS=b.delta, pT=a.p, pS=b.p))
arr = pd.DataFrame(arr); arr.to_csv(f'out_addA/fergus_arrows_{LAY}.csv', index=False)
cT = T['cons'][T['cons'].station == ST].set_index(['comp', 'index']); cS = S['cons'][S['cons'].station == ST].set_index(['comp', 'index'])
prT = T['proj'][T['proj'].station == ST].set_index(['comp', 'index']); prS = S['proj'][S['proj'].station == ST].set_index(['comp', 'index'])
# ---------- aggregates
agg = {}
for k, F in (('T', T), ('S', S)):
    e = F['env']; c = F['cons']
    sc = skill_change(F)[0]['>=10of20']
    agg[k] = dict(bounded=int(e.within.sum()), per_station=e.groupby('station').within.sum().to_dict(),
                  c613=e.c613.value_counts().to_dict(), cv7=e.cv7.value_counts().to_dict(),
                  bounded_all3=int(e.groupby('index').within.all().sum()),
                  fergus_T=int(e[(e.station == ST) & (e.group == 'T')].within.sum()), fergus_P=int(e[(e.station == ST) & (e.group == 'P')].within.sum()),
                  cons={f'{st}_{cp}_{g}': int(len(c[(c.station == st) & (c.comp == cp) & (c.group == g) & c.strong])) for st in ['London', 'Fergus', 'Harrow'] for cp in 'NF' for g in 'TP'},
                  skill=dict(a=sc['a'], b=sc['b'], c=sc['c'], d=sc['d'], misjudged=sc['misjudged'], fisher=sc['fisher_p']),
                  d1=d1tab(F)[['group', 'coh_HP', 'coh_N', 'coh_F', 'bounded', 'sign_rev', 'conf']].to_dict('records'),
                  refs={'Fergus_T': F['refs']['Fergus'], 'precip_sum': F['refs']['precip_sum'], 'precip_ref': F['refs']['precip_ref']})
c1T = c1tab(T)[lambda d: d.station == ST].set_index('index'); c1S = c1tab(S)[lambda d: d.station == ST].set_index('index')
pickle.dump(dict(mm=mm, cd=cd, pm=pm, t1T=t1T, t1S=t1S, bT=bT, bS=bS, eT=eT, eS=eS, arr=arr, cT=cT, cS=cS, prT=prT, prS=prS, agg=agg,
                 c1T=c1T, c1S=c1S, pcT=pcT, pcS=pcS), open(f'out_addA/tables_{LAY}.pkl', 'wb'))
print('indices with any annual model cell difference:', int((cd.groupby('index').n_diff.sum() > 0).sum()), 'of 44')
print(t1T.to_string()); print(t1S.to_string())
print('basin P T', bT.sum(1).to_dict()); print('basin P S', bS.sum(1).to_dict())
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ('d1', 'refs')} for k, v in agg.items()}, indent=0, default=str))
x = eT[['obs', 'lo', 'hi', 'c613', 'cv7']].join(eS[['lo', 'hi', 'c613', 'cv7']], rsuffix='_S')
print(x[(x.c613 != x.c613_S) | (x.cv7 != x.cv7_S)].to_string())
ch = arr[arr['T'] != arr['S']]; print('arrow/shading cells changed:', len(ch), 'of', len(arr)); print(ch.to_string())

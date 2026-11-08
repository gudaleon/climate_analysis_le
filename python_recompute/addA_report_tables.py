"""Addendum A: render the Branch T / Branch S Markdown tables from the saved addendum outputs (no hand transcription)."""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from cdx import INDICES, TEMP
from analysis import MODELS
U = dict(PRCPTOT='mm', R10mm='days', R20mm='days', RX1day='mm', RX3day='mm', RX5day='mm', SDII='mm/day', R95p='mm', R95pTOT='%', R99p='mm',
         R99pTOT='%', CDD='days', CWD='days', CSDI6='days', CSDI3='days', WSDI6='days', WSDI3='days', FD='days', ID='days', SU='days', TR='days',
         TNn='°C', TNx='°C', TXx='°C', TXn='°C', TXm='°C', TMm='°C', TNm='°C', TN10p='% days', TN90p='% days', TX10p='% days', TX90p='% days',
         DTR='°C', DTRgt15='days', TXb3TNb3='events', TXge30='days', TXgt50p='% days', GDDgrow10='°C·day', TNltm20='days', GSL='days',
         CWA='°C²', CWF='days', HWA='°C²', HWF='days')
X = pickle.load(open('out_addA/tables_AUTHORS_v4.pkl', 'rb')); H = pickle.load(open('out_addA/tables_H1_reviewed.pkl', 'rb'))
f = lambda v, d=2: 'NA' if v is None or (isinstance(v, float) and np.isnan(v)) else (f'{v:+.{d}f}' if d < 0 else f'{v:.{d}f}')
sg = lambda v, d=2: 'NA' if np.isnan(v) else f'{v:+.{d}f}'
out = []
w = out.append
# ---- 1a
cd = X['cd'].groupby('index').agg(n=('n_diff', 'sum'), mean=('mean_SminusT', 'mean'), mx=('maxabs', 'max'), nanm=('nan_mismatch', 'sum'))
pm = X['pm']
w('| Index | Unit | Annual model-year cells differing (of 1,510) | Mean S−T over all model-years | Max \\|S−T\\| in one model-year | Pooled median H: T / S (Δ) | P: T / S (Δ) | N: T / S (Δ) | F: T / S (Δ) |')
w('|---|---|---|---|---|---|---|---|---|')
for ix in INDICES:
    c = cd.loc[ix]; r = pm.loc[ix]
    cells = ' | '.join(f"{r[f'T_{p}']:.2f} / {r[f'S_{p}']:.2f} ({sg(r[f'd_{p}'])})" for p in 'HPNF')
    w(f"| {ix} | {U[ix]} | {int(c.n)}{' (+%d NA-pattern)' % c.nanm if c.nanm else ''} | {sg(c['mean'], 3)} | {c.mx:.2f} | {cells} |")
T1A = '\n'.join(out); out.clear()
# ---- 1b per model period medians (appendix)
mm = X['mm']
w('| Index (unit) | Model | H: T / S (Δ) | P: T / S (Δ) | N: T / S (Δ) | F: T / S (Δ) |'); w('|---|---|---|---|---|---|')
for ix in INDICES:
    for m in MODELS:
        g = mm[(mm['index'] == ix) & (mm.model == m)].set_index('period')
        w(f"| {ix} ({U[ix]}) | {m} | " + ' | '.join(f"{f(g.loc[p, 'T'])} / {f(g.loc[p, 'S'])} ({sg(g.loc[p, 'd'])})" for p in 'HPNF') + ' |')
T1B = '\n'.join(out); out.clear()
# ---- 2 Test 1
t, s = X['t1T'], X['t1S']
w('| Model | Temp H (of 31) T / S | Temp P T / S | **Temp total (of 62) T / S** | Temp both-period indices T / S | Precip H (of 13) T / S | Precip P T / S | **Precip total (of 26) T / S** | All (of 88) T / S |')
w('|---|---|---|---|---|---|---|---|---|')
for m in MODELS:
    a, b = t.loc[m], s.loc[m]
    w(f"| {m} | {a.T_H} / {b.T_H} | {a.T_P} / {b.T_P} | **{a.T_tot} / {b.T_tot}** ({b.T_tot - a.T_tot:+d}) | {a.both_T} / {b.both_T} | {a.P_H} / {b.P_H} | {a.P_P} / {b.P_P} | **{a.P_tot} / {b.P_tot}** ({b.P_tot - a.P_tot:+d}) | {a.all_tot} / {b.all_tot} |")
T2 = '\n'.join(out); out.clear()
def rank(sr):
    o = sr.sort_values(ascending=False); r = o.rank(method='min', ascending=False).astype(int)
    return ', '.join(f'{m} {v} (#{r[m]})' for m, v in o.items())
RK = dict(tT=rank(t.T_tot), tS=rank(s.T_tot), pT=rank(t.P_tot), pS=rank(s.P_tot),
          bT=rank(X['bT'].sum(axis=1)), bS=rank(X['bS'].sum(axis=1)))
# ---- 3a envelope
eT, eS = X['eT'], X['eS']
w('| Index | Unit | Observed Δ (H→P) | T: model Δ range | T: bounding (v7) | T: 6.13 class | S: model Δ range | S: bounding (v7) | S: 6.13 class | Changes? |')
w('|---|---|---|---|---|---|---|---|---|---|')
nm = dict(bounded='Bounded', unbounded='Unbounded (magnitude offset)', sign_reversal='Sign reversal', within='within', magnitude='magnitude', reversal='directional reversal')
for ix in INDICES:
    a, b = eT.loc[ix], eS.loc[ix]; chg = (a.cv7 != b.cv7) or (a.c613 != b.c613)
    w(f"| {ix} | {U[ix]} | {sg(a.obs)} | [{sg(a.lo)}, {sg(a.hi)}] | {nm[a.cv7]} | {nm[a.c613]} | [{sg(b.lo)}, {sg(b.hi)}] | {nm[b.cv7]} | {nm[b.c613]} | {'**yes**' if chg else 'no'} |")
T3A = '\n'.join(out); out.clear()
# ---- 3b arrows
ar = X['arr']; ch = ar[ar['T'] != ar['S']].copy()
CN = {'P': 'Table B (H→P)', 'N': 'Table C (H→N)', 'F': 'Table C (H→F)'}
w('| Index (unit) | Source | Comparison | T symbol | S symbol | Kind | T: Δ median, p | S: Δ median, p |'); w('|---|---|---|---|---|---|---|---|')
for r in ch.itertuples():
    kind = 'shading only' if r.T.rstrip('*') == r.S.rstrip('*') else 'direction'
    w(f"| {r.index} ({U[r.index]}) | {r.source} | {CN[r.comp]} | {r.T} | {r.S} | {kind} | {sg(r.dT)}, {r.pT:.3f} | {sg(r.dS)}, {r.pS:.3f} |")
T3B = '\n'.join(out); out.clear()
# ---- consensus per index changes
cT, cS = X['cT'], X['cS']
j = cT[['up', 'down', 'strong']].join(cS[['up', 'down', 'strong']], rsuffix='_S')
j = j[(j.up != j.up_S) | (j.down != j.down_S) | (j.strong != j.strong_S)]
w('| Horizon | Index | T: models ↑* / ↓* | T consensus (≥8/10) | S: models ↑* / ↓* | S consensus |'); w('|---|---|---|---|---|---|')
for (cp, ix), r in j.iterrows():
    w(f"| {'Near (H→N)' if cp == 'N' else 'Far (H→F)'} | {ix} | {r.up} / {r.down} | {'yes' if r.strong else 'no'} | {r.up_S} / {r.down_S} | {'yes' if r.strong_S else 'no'} |")
T3C = '\n'.join(out); out.clear()
# ---- projections (ensemble median change and range) changes
prT, prS = X['prT'], X['prS']
w('| Horizon | Index (unit) | T: ensemble-median Δ [model min, max] | S: ensemble-median Δ [model min, max] | S−T in median |'); w('|---|---|---|---|---|')
for cp in 'NF':
    for ix in INDICES:
        a, b = prT.loc[(cp, ix)], prS.loc[(cp, ix)]
        w(f"| {cp} | {ix} ({U[ix]}) | {sg(a.ens_median)} [{sg(a.lo)}, {sg(a.hi)}] | {sg(b.ens_median)} [{sg(b.lo)}, {sg(b.hi)}] | {sg(b.ens_median - a.ens_median)} |")
T3D = '\n'.join(out); out.clear()
# ---- C1 label changes and D1
c1 = X['c1T'][['label']].join(X['c1S'][['label']], rsuffix='_S')
C1CH = c1[c1.label != c1.label_S]
d1T = pd.DataFrame(X['agg']['T']['d1']).set_index('group'); d1S = pd.DataFrame(X['agg']['S']['d1']).set_index('group')
w('| Process group | T: coherence H→P / N / F (%) | T: bounded % | T: confidence | S: coherence H→P / N / F (%) | S: bounded % | S: confidence |'); w('|---|---|---|---|---|---|---|')
for g in d1T.index:
    a, b = d1T.loc[g], d1S.loc[g]
    w(f"| {g} | {a.coh_HP} / {a.coh_N} / {a.coh_F} | {a.bounded} | {a.conf} | {b.coh_HP} / {b.coh_N} / {b.coh_F} | {b.bounded} | {b.conf} |")
TD1 = '\n'.join(out); out.clear()
# ---- spread
sp = pd.read_csv('out_addA/fergus_cell_vs_spread.csv', index_col=0)
pickle.dump(dict(T1A=T1A, T1B=T1B, T2=T2, RK=RK, T3A=T3A, T3B=T3B, T3C=T3C, T3D=T3D, C1CH=C1CH, TD1=TD1, sp=sp, X=X, H=H, ch=ch), open('out_addA/report_parts.pkl', 'wb'))
print(RK); print(C1CH); print(len(ch))

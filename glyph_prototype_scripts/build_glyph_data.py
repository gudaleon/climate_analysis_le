"""Compute per-cell channel data for the glyph prototype from the verified recompute layer.
Sources: executor_runs/wu_claude/out/facts_AUTHORS_v4.pkl (pc, proj) and out/tables_613.json (printed arrows).
Annual tables in out/idx/ are used only for the independent hand-checks at the end."""
import pickle, json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path.home()/"workspace/jeremy_wu_redteam/executor_runs/wu_claude/code"))
from cdx import INDICES, PREC, TEMP
from analysis import wilcox, per, MODELS, PER

BASE = pathlib.Path.home()/"workspace/jeremy_wu_redteam/executor_runs/wu_claude/out"
OUT  = pathlib.Path.home()/"workspace/jeremy_wu_redteam/figures_glyph_prototype"
STATIONS = ['London','Fergus','Harrow']
CAP = 5.0

F = pickle.load(open(BASE/"facts_AUTHORS_v4.pkl",'rb'))
pc, proj = F['pc'], F['proj']
tabs = json.load(open(BASE/"tables_613.json"))
tabmap = {'London': tabs['T5_London'], 'Fergus': tabs['C1_Fergus'], 'Harrow': tabs['C2_Harrow']}

def sgn(x):
    return '–' if x == 0 else ('↑' if x > 0 else '↓')

rows = []
for st in STATIONS:
    pf = proj[(proj.station==st)&(proj.comp=='F')].set_index('index')
    ef = pc[(pc.station==st)&(pc.source=='ENS')&(pc.comp=='F')].set_index('index')
    for ix in INDICES:
        d_all = pc[(pc.station==st)&(pc['index']==ix)&(pc.source.isin(MODELS))&(pc.comp=='F')].delta.values.astype(float)
        d = d_all[~np.isnan(d_all)]
        med = float(np.median(d))                      # median of the models' changes (= proj.ens_median)
        assert abs(med - float(pf.loc[ix,'ens_median'])) < 1e-9, (st, ix, med, pf.loc[ix,'ens_median'])
        q1, q3 = np.quantile(d, [0.25, 0.75]); iqr = float(q3-q1)
        ratio = abs(med)/iqr if iqr > 0 else (0.0 if med == 0 else float('inf'))
        if med != 0:
            agree = int((np.sign(d) == np.sign(med)).sum())
        else:
            agree = int((d == 0).sum())                # flat cells: models with exactly no change
        p = float(ef.loc[ix,'p']); pooled = float(ef.loc[ix,'delta'])
        printed = tabmap[st][ix][21] if ix in tabmap[st] else None   # ENS, Far Future column of the 22-column printed arrow tables
        rows.append(dict(station=st, index=ix, family=('Precipitation' if ix in PREC else 'Temperature'),
            n_models_defined=int(len(d)), median_change=med, q1_change=float(q1), q3_change=float(q3), iqr_change=iqr,
            relative_magnitude=(ratio if np.isfinite(ratio) else np.nan), relative_magnitude_capped=float(min(ratio, CAP)) if np.isfinite(ratio) else CAP,
            ratio_at_cap=bool(ratio > CAP), agreement=agree, direction=sgn(med),
            pooled_ensemble_change=pooled, pooled_arrow=sgn(pooled), wilcoxon_p=p, significant=bool(p < 0.05),
            printed_arrow=printed, direction_agrees_with_printed=(None if printed is None else sgn(med) == printed)))
df = pd.DataFrame(rows)
df.to_csv(OUT/"glyph_channel_data_far_future.csv", index=False)
print(f"cells {len(df)}; capped {int(df.ratio_at_cap.sum())}; sig {int(df.significant.sum())}")
dis = df[df.direction_agrees_with_printed == False]
print(f"direction vs printed: agree {int((df.direction_agrees_with_printed==True).sum())}, disagree {len(dis)}, missing printed {int(df.printed_arrow.isna().sum())}")
print(dis[['station','index','median_change','pooled_ensemble_change','direction','printed_arrow']].to_string())

# ---- Independent hand-checks straight from the annual index tables (out/idx) ----
def load(st, m):
    return pd.read_csv(BASE/f"idx/{st}_{m}_annual.csv", index_col=0).round(6)
print("\nHAND CHECKS (recomputed from out/idx annual tables):")
for st, ix in [('London','TXm'), ('Fergus','CWD'), ('Harrow','R95p')]:
    deltas, hall, fall = [], [], []
    for m in MODELS:
        dfm = load(st, m)
        h = per(dfm,'H',ix); f = per(dfm,'F',ix)
        deltas.append(float(np.median(f)-np.median(h))); hall.append(h); fall.append(f)
    deltas = np.array(deltas); med = float(np.median(deltas))
    q1,q3 = np.quantile(deltas,[.25,.75]); iqr = float(q3-q1)
    agree = int((np.sign(deltas)==np.sign(med)).sum()) if med!=0 else int((deltas==0).sum())
    p = wilcox(np.concatenate(hall), np.concatenate(fall))
    saved = df[(df.station==st)&(df['index']==ix)].iloc[0]
    ok = (abs(med-saved.median_change)<1e-9 and abs(iqr-saved.iqr_change)<1e-9 and agree==saved.agreement
          and abs(p-saved.wilcoxon_p) < 1e-9*max(1,abs(p)))
    print(f"{st} {ix}: per-model changes {np.round(deltas,4).tolist()}")
    print(f"  median {med:.6f} (saved {saved.median_change:.6f}); IQR {iqr:.6f} (saved {saved.iqr_change:.6f}); "
          f"ratio {abs(med)/iqr if iqr>0 else 0:.4f}; agreement {agree} (saved {saved.agreement}); "
          f"Wilcoxon p {p:.6g} (saved {saved.wilcoxon_p:.6g}); direction {sgn(med)}; MATCH {ok}")

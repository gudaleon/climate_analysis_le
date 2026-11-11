"""Assemble the unified diagnostic table (one row per station-and-index case,
Historical-to-Present contrast) from the verified artefacts on disk only.

Nothing is recomputed from raw series here. The inputs are:
  - figures_error_framework/plotted_data.csv, Panel A: the observed change, the
    ten-model range, the signed margin, the 6.13 bounding class and the
    perturbation / H1-layer flip record for all 132 cases (itself extracted from
    the envelope frames of the Claude route's addendum outputs and cross-checked
    against the pass-2 bounding comparison).
  - executor_runs/wu_claude/out/facts_AUTHORS_v4.pkl, frames pc and env: the
    per-source period-change table (comp 'P' = Present against Historical) whose
    rows carry each model's change, the observed change, and the pooled ensemble
    change with its Wilcoxon rank-sum p-value; and the envelope frame, whose
    cv7 column carries the v7 bounding class.

Derived here, by arithmetic on those artefact values only: the sign of the
median of the ten model changes, the sign of the pooled ensemble change, the
model agreement count, and the observed change's rank among the eleven values
(the ten model changes plus itself), as a midrank so that ties share a rank.
"""
import pickle, pathlib
import numpy as np, pandas as pd

BASE = pathlib.Path.home() / "workspace/jeremy_wu_redteam"
OUT = BASE / "unified_diagnostic"
MODELS = ['ACCESS', 'BCC', 'CanESM', 'CNRM', 'EC', 'GFDL', 'INM', 'MIROC', 'MRI', 'NorESM']
STATIONS = ['London', 'Fergus', 'Harrow']
ADDENDUM = {'Fergus': 'Addendum A', 'Harrow': 'Addendum B', 'London': 'Addendum C'}
CLS613 = {'within': 'within range', 'magnitude': 'magnitude offset', 'reversal': 'directional reversal'}
CV7 = {'bounded': 'Bounded', 'unbounded': 'Unbounded', 'sign_reversal': 'Sign Reversal'}

def sgn(x):
    return '–' if x == 0 else ('↑' if x > 0 else '↓')

def sgn3(x):
    return 0 if x == 0 else (1 if x > 0 else -1)

# --- error-framework Panel A: margins, 6.13 class, flip record ------------------
D = pd.read_csv(BASE / "figures_error_framework/plotted_data.csv")
A = D[D.panel == 'A'].set_index(['station', 'index'])
assert len(A) == 132

# --- facts frames: per-source changes (comp P), envelope v7 class ---------------
F = pickle.load(open(BASE / "executor_runs/wu_claude/out/facts_AUTHORS_v4.pkl", 'rb'))
pc = F['pc']; env = F['env'].set_index(['station', 'index'])
p = pc[pc.comp == 'P']
piv = p.pivot_table(index=['station', 'index'], columns='source', values='delta')
ens = p[p.source == 'ENS'].set_index(['station', 'index'])

rows = []
for (st, ix), a in A.iterrows():
    d = piv.loc[(st, ix), MODELS].values.astype(float)
    assert np.isfinite(d).all(), (st, ix)
    obs = float(piv.loc[(st, ix), 'OBS'])
    med = float(np.median(d))
    pooled = float(ens.loc[(st, ix), 'delta'])
    pw = float(ens.loc[(st, ix), 'p'])
    if med != 0:
        agree = int((np.sign(d) == np.sign(med)).sum())
    else:
        agree = int((d == 0).sum())
    rank = 1.0 + float((d < obs).sum()) + 0.5 * float((d == obs).sum())
    flips = []
    if isinstance(a.flip_sources, str) and a.flip_sources:
        for part in a.flip_sources.split('; '):
            if part.endswith('grid-cell perturbation'):
                flips.append(f"{part} ({ADDENDUM[st]})")
            else:
                flips.append(part)
    rows.append(dict(
        station=st, index=ix, process_family=a.family,
        obs_change=round(obs, 6),
        model_range_lo=round(float(a.range_lo), 6), model_range_hi=round(float(a.range_hi), 6),
        bounding_class_613=CLS613[str(a.class_613_T)],
        bounding_class_v7=CV7[str(env.loc[(st, ix), 'cv7'])],
        signed_margin=round(float(a.margin_norm), 6),
        obs_rank_among_11=rank,
        median_model_change=round(med, 6), arrow_median_sign=sgn(med),
        pooled_ensemble_change=round(pooled, 6), arrow_pooled_sign=sgn(pooled),
        sign_disagreement=bool(sgn3(med) != sgn3(pooled)),
        pooled_wilcoxon_p=pw,
        model_agreement_count=agree,
        perturbation_flip='; '.join(flips),
        source=("figures_error_framework/plotted_data.csv (Panel A: observed change, model range, "
                "signed margin, 6.13 class, flip record); executor_runs/wu_claude/out/"
                "facts_AUTHORS_v4.pkl (frame pc, comp P: model, observed and pooled changes and "
                "pooled Wilcoxon p; frame env: v7 class)"),
    ))

U = pd.DataFrame(rows)
order = {s: i for i, s in enumerate(STATIONS)}
U['_o'] = U.station.map(order)
U = U.sort_values(['_o', 'index']).drop(columns='_o').reset_index(drop=True)
# keep the thesis's station order but the index order of Panel A within a station:
A_order = list(A.reset_index().groupby('station', sort=False).index)
U = U.set_index(['station', 'index']).loc[A.reset_index().set_index(['station', 'index']).index].reset_index()
U.to_csv(OUT / "unified_cases.csv", index=False)

print(f"rows: {len(U)}")
print("bounding_class_613:", U.bounding_class_613.value_counts().to_dict())
print("bounding_class_v7:", U.bounding_class_v7.value_counts().to_dict())
print("flipped cases:", int((U.perturbation_flip != '').sum()))
print(U[U.perturbation_flip != ''][['station', 'index', 'perturbation_flip']].to_string(index=False))
print("sign disagreements:", int(U.sign_disagreement.sum()))
print(U[U.sign_disagreement][['station', 'index', 'median_model_change', 'pooled_ensemble_change']].to_string(index=False))
print("rank distribution:", sorted(U.obs_rank_among_11.unique()))
print("rank 1 or 11 rows:", int(U.obs_rank_among_11.isin([1.0, 11.0]).sum()),
      "| outside-range rows:", int((U.signed_margin < 0).sum()))

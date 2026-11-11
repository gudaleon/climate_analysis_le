"""Verify unified_cases.csv against the source artefacts by an independent path.

Three seed rows are recomputed field by field with explicit loops over the
facts frames (executor_runs/wu_claude/out/facts_AUTHORS_v4.pkl), taking the
observed change and range from the envelope frame rather than from the error
framework's plotted data, and compared with the delivered table. Global checks
then reconcile the table against the published record: 115 of 132 cases within
range on the thesis cells (both class schemes), nine flipped cases in the error
framework's count, and the rank bridge itself (a case is outside the model
range exactly when its rank among the eleven values is 1 or 11).
"""
import pickle, pathlib
import numpy as np, pandas as pd

BASE = pathlib.Path.home() / "workspace/jeremy_wu_redteam"
MODELS = ['ACCESS', 'BCC', 'CanESM', 'CNRM', 'EC', 'GFDL', 'INM', 'MIROC', 'MRI', 'NorESM']
U = pd.read_csv(BASE / "unified_diagnostic/unified_cases.csv").set_index(['station', 'index'])
F = pickle.load(open(BASE / "executor_runs/wu_claude/out/facts_AUTHORS_v4.pkl", 'rb'))
pc, env = F['pc'], F['env'].set_index(['station', 'index'])
SEEDS = [('London', 'PRCPTOT'), ('Fergus', 'CWD'), ('Harrow', 'CWA')]

def seed_check(st, ix):
    sub = pc[(pc.station == st) & (pc['index'] == ix) & (pc.comp == 'P')]
    d = np.array([float(sub[sub.source == m].delta.iloc[0]) for m in MODELS])
    obs = float(sub[sub.source == 'OBS'].delta.iloc[0])
    pooled = float(sub[sub.source == 'ENS'].delta.iloc[0])
    pw = float(sub[sub.source == 'ENS'].p.iloc[0])
    e = env.loc[(st, ix)]
    lo, hi = float(e.lo), float(e.hi)
    width = hi - lo
    margin = (min(obs - lo, hi - obs) / width) if width > 0 else 0.0
    med = float(np.median(d))
    rank = 1.0 + float((d < obs).sum()) + 0.5 * float((d == obs).sum())
    agree = int((np.sign(d) == np.sign(med)).sum()) if med != 0 else int((d == 0).sum())
    r = U.loc[(st, ix)]
    checks = {
        'obs_change': abs(obs - r.obs_change) < 1e-6,
        'range': abs(lo - r.model_range_lo) < 1e-6 and abs(hi - r.model_range_hi) < 1e-6,
        'signed_margin': abs(margin - r.signed_margin) < 1e-6,
        'rank': abs(rank - r.obs_rank_among_11) < 1e-9,
        'median_change': abs(med - r.median_model_change) < 1e-6,
        'pooled_change': abs(pooled - r.pooled_ensemble_change) < 1e-6,
        'wilcoxon_p': abs(pw - r.pooled_wilcoxon_p) < 1e-12 * max(1, abs(pw)),
        'agreement': agree == r.model_agreement_count,
        'class_613': ('within range' if str(e.c613) == 'within' else
                      'magnitude offset' if str(e.c613) == 'magnitude' else 'directional reversal') == r.bounding_class_613,
    }
    print(f"{st} {ix}: model changes {np.round(d, 3).tolist()}")
    print(f"   obs {obs}; range [{lo}, {hi}]; margin {margin:.6f}; rank {rank}; "
          f"median {med}; pooled {pooled}; agreement {agree}; checks {checks}")
    assert all(checks.values()), (st, ix, checks)

for s in SEEDS:
    seed_check(*s)

print("\nGlobal reconciliation:")
print("  rows:", len(U), "(expect 132)")
print("  within range (6.13):", int((U.bounding_class_613 == 'within range').sum()), "(expect 115)")
print("  Bounded (v7):", int((U.bounding_class_v7 == 'Bounded').sum()), "(expect 115)")
print("  flipped cases:", int((U.perturbation_flip.fillna('') != '').sum()), "(expect 9)")
outside = U.signed_margin < 0
extreme = U.obs_rank_among_11.isin([1.0, 11.0])
print("  outside-range rows:", int(outside.sum()), "| rank 1/11 rows:", int(extreme.sum()),
      "| bridge holds for every row:", bool((outside == extreme).all()))
edge = U[(U.obs_rank_among_11 == 1.0) | (U.obs_rank_among_11 == 11.0)]
print("  ranks of outside rows:", sorted(set(U[outside].obs_rank_among_11)))
print("  sign disagreements:", int(U.sign_disagreement.sum()),
      U[U.sign_disagreement].index.tolist())
assert len(U) == 132 and int((U.bounding_class_613 == 'within range').sum()) == 115
assert int((U.perturbation_flip.fillna('') != '').sum()) == 9 and bool((outside == extreme).all())
print("ALL CHECKS PASSED")

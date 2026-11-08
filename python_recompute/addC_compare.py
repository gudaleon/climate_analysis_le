"""Addendum C: evaluate every numeric claim rule of the main audit on Branch T (as frozen) and on Branch P
(London model indices from the perturbed cell 24/717, a designed sensitivity experiment), and record every check whose recomputed value changes."""
import sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'code')
import engine
from engine import match
import v7branch
import rules_613, rules_v7
from run_verdicts import M10, ARW

tabs = {'613': json.load(open('out/tables_613.json')), 'v7': json.load(open('out/tables_v7.json'))}
RULES = {'613': rules_613.R, 'v7': rules_v7.R}


def table_cells(rule, tb):
    kind, names = rule.split(':'); out = {}
    for name in names.split(','):
        st = name.split('_')[1]; t = dict(tb.get(name, {}))
        for ix, cells in t.items():
            if kind == 'TABLE_P':
                for j, c in enumerate(cells):
                    m = M10[j % 10]; per = 'H' if j < 10 else 'P'
                    out[f'{st}/{ix}/{m}/{per} p'] = (c, engine.pval(st, ix, m, per))
            else:
                srcs = ([('OBS', 'P')] + [(m, 'P') for m in M10] + [('ENS', 'P')]) if len(cells) == 12 else \
                    ([(m, 'N') for m in M10] + [('ENS', 'N')] + [(m, 'F') for m in M10] + [('ENS', 'F')])
                for c, (src, comp) in zip(cells, srcs):
                    d = engine.chg(st, ix, src, comp)
                    p = engine.chg(st, ix, src, comp, 'p') if src not in ('OBS',) or True else None
                    out[f'{st}/{ix}/{src}/{comp} arrow'] = (c, ('n/a' if np.isnan(d) else ARW(d)) + ('*' if (not np.isnan(d) and abs(d) > 1e-9 and p < 0.05) else ''))
    return out


def snapshot():
    snap = {}
    for tgt, R in RULES.items():
        for cid, rule in R.items():
            if isinstance(rule, tuple):
                continue
            try:
                if isinstance(rule, str):
                    snap[(tgt, cid)] = {k: v for k, v in table_cells(rule, tabs[tgt]).items()}
                else:
                    snap[(tgt, cid)] = {f'{i}|{c[0]}': (c[1], c[2], c[3] if len(c) > 3 else 'auto') for i, c in enumerate(rule())}
            except Exception as ex:
                snap[(tgt, cid)] = {'ERROR': (None, repr(ex), None)}
    return snap


def ok(p, v, d='auto'):
    if p == 'lit': return None
    try:
        if isinstance(p, str): return str(p) == str(v)
        if d is None: return v is not None and not np.isnan(v) and abs(v - p) <= max(0.1 * abs(p), 0.5)
        return bool(match(p, v, None if d == 'auto' else d))
    except Exception:
        return False


def same(a, b):
    if isinstance(a, str) or isinstance(b, str): return str(a) == str(b)
    try:
        if a is None or b is None: return a is b
        if np.isnan(a) and np.isnan(b): return True
        return abs(float(a) - float(b)) <= 1e-9
    except Exception:
        return str(a) == str(b)


T = snapshot()
# ---- swap to Branch P
S = {k: pickle.load(open(f'out_addC/facts_P_{k2}.pkl', 'rb')) for k, k2 in (('V4', 'AUTHORS_v4'), ('H1', 'H1_reviewed'))}
engine.L['V4'], engine.L['H1'] = S['V4'], S['H1']
ms = pd.read_csv('out_addC/monthly_stats_P_London_models.csv')
mod = engine.MO['MOD']; engine.MO['MOD'] = pd.concat([mod[mod.station != 'London'], ms], ignore_index=True)
engine.C1['V4'] = v7branch.c1(S['V4'], include_obs=True); engine.C1['H1'] = v7branch.c1(S['H1'], include_obs=True)
engine.C1m['V4'] = v7branch.c1(S['V4'], include_obs=False)
for k in ('V4', 'H1'):
    engine.SC[k] = v7branch.skill_change(S[k])[0]; engine.D1[k] = v7branch.d1(S[k])
Sn = snapshot()

rows = []
for key in T:
    for lab, a in T[key].items():
        b = Sn[key].get(lab)
        if len(a) == 3:
            p, vt, d = a; vs = b[1]
        else:
            p, vt = a; vs = b[1]; d = None
            if isinstance(vt, str):
                okT, okP = [(x == 'n/a') if p == 'n/a' else (p == x.rstrip('*')) for x in (vt, vs)]
            else:
                okT, okP = [bool(np.isnan(x)) if p == 'nan' else (not np.isnan(x) and abs(round(x, 3) - float(p)) <= 0.0015) for x in (vt, vs)]
        if same(vt, vs): continue
        if len(a) == 3:
            okT, okP = ok(p, vt, d), ok(p, vs, d)
        rows.append(dict(target=key[0], claim=key[1], check=lab.split('|', 1)[-1], printed=p, T=vt, P=vs, printed_matches_T=okT, printed_matches_P=okP))
df = pd.DataFrame(rows)
df.to_csv('out_addC/claim_check_changes.csv', index=False)
print(len(df), 'changed checks in', df.groupby(['target', 'claim']).ngroups, 'claims;',
      'match-status flips:', int((df.printed_matches_T != df.printed_matches_P).sum()))

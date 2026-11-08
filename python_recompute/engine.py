"""Verdict engine: accessors over recomputed layers + comparison helpers."""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from v7branch import skill_change, c1 as c1tab, d1 as d1tab

L = {}
for k, b in [('V4', 'AUTHORS_v4'), ('AT', 'AUTHTAB'), ('H1', 'H1_reviewed'), ('H0', 'H0merged'), ('H2', 'H2_auto'),
             ('H1b', 'H1b_reviewed_force1985pruned')]:
    L[k] = pickle.load(open(f'out/facts_{b}.pkl', 'rb'))
MO = {}
_m = pd.read_csv('out/monthly_stats_H1_reviewed.csv')
MO['MOD'] = _m[_m.source != 'OBS']
MO['V4'] = pd.read_csv('out/monthly_stats_AUTHORS_v4.csv')
MO['H1'] = _m[_m.source == 'OBS']
MO['H0'] = pd.read_csv('out/monthly_stats_H0merged.csv')
MO['H2'] = pd.read_csv('out/monthly_stats_H2_auto.csv')
C1 = {k: c1tab(L[k], include_obs=True) for k in ('V4', 'H1')}
C1m = {k: c1tab(L[k], include_obs=False) for k in ('V4',)}
SC = {k: skill_change(L[k])[0] for k in ('V4', 'H1', 'H0', 'H2')}
D1 = {k: d1tab(L[k]) for k in ('V4', 'H1', 'H0', 'H2')}
TREF = {'London': 'NorESM', 'Fergus': 'EC', 'Harrow': 'EC'}
PIDX = ['RX1day', 'RX5day', 'PRCPTOT', 'R10mm', 'CDD', 'SPI3', 'SPI6', 'SPEI3', 'SPEI6']


def pm(st, ix, p, lay='V4'):  # pooled ten-model median
    return L[lay]['pmed'].set_index(['station', 'index']).loc[(st, ix), 'pooled_' + p]


def pmx(st, ix, p, which, lay='V4'):
    return L[lay]['pmed'].set_index(['station', 'index']).loc[(st, ix), f'{which}model_{p}']


def om(st, ix, p, lay='V4'):
    return L[lay]['pmed'].set_index(['station', 'index']).loc[(st, ix), 'obs_' + p]


def proj(st, ix, comp, col='ens_median', lay='V4'):
    return L[lay]['proj'].set_index(['station', 'comp', 'index']).loc[(st, comp, ix), col]


def env(st, ix, col='obs', lay='V4'):
    return L[lay]['env'].set_index(['station', 'index']).loc[(st, ix), col]


def chg(st, ix, src, comp='P', col='delta', lay='V4'):
    return L[lay]['pc'].set_index(['station', 'index', 'source', 'comp']).loc[(st, ix, src, comp), col]


def pval(st, ix, m, per, lay='V4'):
    mp = L[lay]['mp']
    return mp[(mp.station == st) & (mp['index'] == ix) & (mp.model == m) & (mp.period == per)].p.iloc[0]


def passes(st, m, grp, per=None, lay='V4'):
    mp = L[lay]['mp']; s = mp[(mp.station == st) & (mp.model == m) & (mp.group == grp)]
    if per: s = s[s.period == per]
    return int((s.p >= 0.05).sum())


def ipass(st, ix, lay='V4', per=None):  # passes of one index over models (x periods)
    mp = L[lay]['mp']; s = mp[(mp.station == st) & (mp['index'] == ix)]
    if per: s = s[s.period == per]
    return int((s.p >= 0.05).sum())


RND2 = True


def mon(st, src, ix, mo, col, lay=None):
    if src == 'OBS':
        t = MO[lay or 'V4']
        t = t[t.source == 'OBS']
    else:
        if src == 'T': src = TREF[st]
        if src == 'P': src = 'BCC'
        t = MO['MOD']
    r = t[(t.station == st) & (t.source == src) & (t['index'] == ix) & (t.month == mo)].iloc[0]
    if col.startswith('d_') and RND2:   # printed convention: differences of 2-dp rounded quartile medians
        a, b = {'HP': ('uq_H', 'uq_P'), 'NF': ('uq_N', 'uq_F'), 'HF': ('uq_H', 'uq_F')}[col[2:]]
        return float(np.round(r[b] + 1e-12, 2) - np.round(r[a] + 1e-12, 2))
    if col.startswith('uq_') and RND2:
        return float(np.round(r[col] + 1e-12, 2))
    return float(r[col])


def monpct(st, src, ix, mo, comp='HP', lay=None):
    d = mon(st, src, ix, mo, 'd_' + comp, lay); base = mon(st, src, ix, mo, 'uq_' + comp[0], lay)
    return 100 * d / base


def c1(st, ix, col, lay='V4'):
    return C1[lay].set_index(['station', 'index']).loc[(st, ix), col]


def cons_count(st, comp, grp=None, lay='V4'):
    c = L[lay]['cons']; s = c[(c.station == st) & (c.comp == comp) & c.strong]
    if grp: s = s[s.group == grp]
    return len(s)


# ---------------------------------------------------------------- comparison
def dec(x):
    s = repr(x) if not isinstance(x, str) else x
    return len(s.split('.')[1]) if '.' in s else 0


def match(printed, value, d=None, tol=None):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    if tol is not None:
        return abs(printed - value) <= tol + 1e-9
    d = dec(printed) if d is None else d
    return abs(printed - value) <= 0.5 * 10 ** (-d) + 1e-9


def fmt(v, d=2):
    if isinstance(v, (bool, np.bool_)): return str(v)
    if isinstance(v, str): return v
    try:
        if v is None or np.isnan(v): return 'NA'
    except TypeError:
        return str(v)
    return f'{v:.{d}f}' if abs(v - round(v)) > 1e-9 else str(int(round(v)))

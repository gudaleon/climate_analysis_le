"""Pass-1 statistics layer (shared) + both post hoc branches (arrow / bounding), from own annual indices."""
import sys, numpy as np, pandas as pd
from scipy.stats import norm, mannwhitneyu
sys.path.insert(0, 'code')
from cdx import INDICES, PREC, TEMP

ST = ['London', 'Fergus', 'Harrow']
MODELS = ['ACCESS', 'BCC', 'CanESM', 'CNRM', 'EC', 'GFDL', 'INM', 'MIROC', 'MRI', 'NorESM']
PER = {'H': (1950, 1986), 'P': (1987, 2023), 'N': (2024, 2062), 'F': (2063, 2100)}


import os
ROUND = None if os.environ.get('NOROUND') else 6   # 6 dp removes float noise from own index sums


def load(obs_branch='H1_reviewed', idxdir='out/idx'):
    D = {}
    rd = lambda f: pd.read_csv(f, index_col=0).round(ROUND) if ROUND is not None else pd.read_csv(f, index_col=0)
    for st in ST:
        for m in MODELS:
            D[(st, m)] = rd(f'{idxdir}/{st}_{m}_annual.csv')
        D[(st, 'OBS')] = rd(f'{idxdir}/{st}_OBS_{obs_branch}_annual.csv')
    return D


def per(df, p, ix):
    a, b = PER[p]
    x = df.loc[(df.index >= a) & (df.index <= b), ix].values.astype(float)
    return x[~np.isnan(x)]


def wilcox(x, y, correct=True, exact=False):
    """R wilcox.test(x, y, alternative='two.sided', exact=FALSE, correct=TRUE), mid-ranks for ties."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[~np.isnan(x)]; y = y[~np.isnan(y)]
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return np.nan
    if exact:
        try:
            return float(mannwhitneyu(x, y, alternative='two-sided', method='exact').pvalue)
        except Exception:
            return np.nan
    r = pd.Series(np.concatenate([x, y])).rank().values
    W = r[:n1].sum() - n1 * (n1 + 1) / 2
    z = W - n1 * n2 / 2
    _, cnt = np.unique(np.concatenate([x, y]), return_counts=True)
    N = n1 + n2
    sig = np.sqrt(n1 * n2 / 12 * ((N + 1) - np.sum(cnt ** 3 - cnt) / (N * (N - 1))))
    if sig == 0:
        return np.nan
    c = 0.5 * np.sign(z) if correct else 0.0
    zz = (z - c) / sig
    return float(2 * min(norm.cdf(zz), norm.sf(zz)))


def model_performance(D, **kw):
    rows = []
    for st in ST:
        for m in MODELS:
            for ix in INDICES:
                for p in ('H', 'P'):
                    pv = wilcox(per(D[(st, 'OBS')], p, ix), per(D[(st, m)], p, ix), **kw)
                    rows.append(dict(station=st, model=m, index=ix, period=p, p=pv, group='T' if ix in TEMP else 'P'))
    return pd.DataFrame(rows)


def pass_counts(mp, nan_pass=False):
    mp = mp.copy()
    mp['pass'] = (mp.p >= 0.05) | (mp.p.isna() & nan_pass)
    return mp.groupby(['station', 'model', 'group', 'period'])['pass'].sum().unstack('period').assign(tot=lambda d: d.H + d.P)


def ref_models(mp, nan_pass=False):
    pc = pass_counts(mp, nan_pass)
    out = {}
    for st in ST:
        t = pc.loc[(st, slice(None), 'T'), 'tot'].droplevel([0, 2])
        best = t[t == t.max()].index.tolist()
        mpt = mp[(mp.station == st) & (mp.group == 'T')].copy(); mpt['ok'] = (mpt.p >= 0.05) | (mpt.p.isna() & nan_pass)
        both = mpt.groupby(['model', 'index']).ok.all().groupby('model').sum()
        out[st] = dict(temp_scores=t.to_dict(), temp_best=best, both_periods={b: int(both[b]) for b in best},
                       temp_ref=max(best, key=lambda b: both[b]))
    pr = pass_counts(mp, nan_pass).xs('P', level='group')['tot'].groupby('model').sum()
    out['precip_sum'] = pr.to_dict(); out['precip_ref'] = pr.idxmax()
    return out


def med(x):
    return float(np.median(x)) if len(x) else np.nan


def period_change(D, **kw):
    rows = []
    for st in ST:
        srcs = ['OBS'] + MODELS + ['ENS']
        for ix in INDICES:
            for src in srcs:
                for p in (['P'] if src == 'OBS' else ['P', 'N', 'F']):
                    if src == 'ENS':
                        h = np.concatenate([per(D[(st, m)], 'H', ix) for m in MODELS])
                        q = np.concatenate([per(D[(st, m)], p, ix) for m in MODELS])
                    else:
                        h = per(D[(st, src)], 'H', ix); q = per(D[(st, src)], p, ix)
                    mh, mq = med(h), med(q)
                    pv = wilcox(h, q, **kw)
                    d = mq - mh
                    arrow = '–' if (np.isnan(d) or d == 0) else ('↑' if d > 0 else '↓')
                    rows.append(dict(station=st, index=ix, source=src, comp=p, med_h=mh, med_p=mq, delta=d, p=pv,
                                     arrow=arrow, sig=bool(pv < 0.05) if not np.isnan(pv) else False, nh=len(h), nq=len(q)))
    return pd.DataFrame(rows)


def envelope(pc, models=MODELS):
    """both branch classifications of observed H->P change against the model change range."""
    rows = []
    for st in ST:
        for ix in INDICES:
            o = pc[(pc.station == st) & (pc['index'] == ix) & (pc.source == 'OBS') & (pc.comp == 'P')].delta.iloc[0]
            md = pc[(pc.station == st) & (pc['index'] == ix) & (pc.source.isin(models)) & (pc.comp == 'P')].delta.values
            md = md[~np.isnan(md)]
            lo, hi = md.min(), md.max(); emed = np.median(md)
            within = lo <= o <= hi
            # 6.13: reversal = opposite sign to ensemble median change
            c613 = 'within' if within else ('reversal' if np.sign(o) != 0 and np.sign(o) == -np.sign(emed) else 'magnitude')
            opp_all = bool(np.all(np.sign(md) == -np.sign(o))) and np.sign(o) != 0
            # v7: sign reversal only when entire interval has the opposite sign
            cv7 = 'bounded' if within else ('sign_reversal' if (np.sign(lo) == np.sign(hi) and np.sign(lo) == -np.sign(o) and o != 0) else 'unbounded')
            rows.append(dict(station=st, index=ix, obs=o, lo=lo, hi=hi, ens_median=emed, within=within, c613=c613, cv7=cv7,
                             opposite_all=opp_all, group='T' if ix in TEMP else 'P'))
    return pd.DataFrame(rows)


def consensus(pc):
    rows = []
    for st in ST:
        for comp in ('N', 'F'):
            for ix in INDICES:
                s = pc[(pc.station == st) & (pc['index'] == ix) & (pc.source.isin(MODELS)) & (pc.comp == comp)]
                up = int(((s.delta > 0) & (s.p < 0.05)).sum()); dn = int(((s.delta < 0) & (s.p < 0.05)).sum())
                rows.append(dict(station=st, comp=comp, index=ix, up=up, down=dn, strong=max(up, dn) >= 8,
                                 group='T' if ix in TEMP else 'P'))
    return pd.DataFrame(rows)


def projected(pc):
    rows = []
    for st in ST:
        for comp in ('N', 'F'):
            for ix in INDICES:
                s = pc[(pc.station == st) & (pc['index'] == ix) & (pc.source.isin(MODELS)) & (pc.comp == comp)].delta.values
                e = pc[(pc.station == st) & (pc['index'] == ix) & (pc.source == 'ENS') & (pc.comp == comp)].iloc[0]
                rows.append(dict(station=st, comp=comp, index=ix, ens_median=np.nanmedian(s), lo=np.nanmin(s), hi=np.nanmax(s),
                                 pooled_delta=e.delta, pooled_p=e.p))
    return pd.DataFrame(rows)


def period_medians(D):
    rows = []
    for st in ST:
        for ix in INDICES:
            r = dict(station=st, index=ix)
            for p in PER:
                r['pooled_' + p] = med(np.concatenate([per(D[(st, m)], p, ix) for m in MODELS]))
                ms = [med(per(D[(st, m)], p, ix)) for m in MODELS]
                r['minmodel_' + p] = np.nanmin(ms); r['maxmodel_' + p] = np.nanmax(ms)
                if p in ('H', 'P'):
                    r['obs_' + p] = med(per(D[(st, 'OBS')], p, ix))
            rows.append(r)
    return pd.DataFrame(rows)

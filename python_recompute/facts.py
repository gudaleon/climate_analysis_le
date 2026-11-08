"""Compute every derived table for a given observation branch; pickle for the verdict scripts."""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from analysis import *


def boxstats(x):
    x = x[~np.isnan(x)]
    q1, md, q3 = np.quantile(x, [0.25, 0.5, 0.75])
    iqr = q3 - q1
    out = int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum())
    return md, q1, q3, out


def build(branch='H1_reviewed', idxdir='out/idx', **wkw):
    D = load(branch, idxdir)
    F = {'branch': branch}
    F['mp'] = model_performance(D, **wkw)
    F['pc'] = period_change(D, **wkw)
    F['env'] = envelope(F['pc'])
    F['cons'] = consensus(F['pc'])
    F['proj'] = projected(F['pc'])
    F['pmed'] = period_medians(D)
    F['refs'] = ref_models(F['mp'])
    rows = []
    for st in ST:
        for ix in INDICES:
            r = dict(station=st, index=ix)
            for p in PER:
                x = np.concatenate([per(D[(st, m)], p, ix) for m in MODELS])
                r.update({f'{k}_{p}': v for k, v in zip(['med', 'q1', 'q3', 'out'], boxstats(x))})
            rows.append(r)
    F['box'] = pd.DataFrame(rows)
    # observed sample sizes
    ns = []
    for st in ST:
        for ix in INDICES:
            ns.append(dict(station=st, index=ix, nH=len(per(D[(st, 'OBS')], 'H', ix)), nP=len(per(D[(st, 'OBS')], 'P', ix))))
    F['nobs'] = pd.DataFrame(ns)
    F['D'] = D
    return F


if __name__ == '__main__':
    branch = sys.argv[1] if len(sys.argv) > 1 else 'H1_reviewed'
    idxdir = sys.argv[2] if len(sys.argv) > 2 else 'out/idx'
    F = build(branch, idxdir)
    pickle.dump(F, open(f'out/facts_{branch}.pkl', 'wb'))
    e = F['env']
    print(branch, 'within', int(e.within.sum()), 'of', len(e), 'per station', e.groupby('station').within.sum().to_dict())
    print(' 6.13 classes', e.c613.value_counts().to_dict(), ' v7 classes', e.cv7.value_counts().to_dict())
    c = F['cons']; print(' consensus', c[c.strong].groupby(['station', 'comp', 'group']).size().to_dict())
    print(' refs', {k: (v['temp_ref'] if isinstance(v, dict) and 'temp_ref' in v else v) for k, v in F['refs'].items()})

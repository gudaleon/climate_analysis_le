"""Bounding branch (v7 Test 2, skill-vs-change, C1, D1) computed from my own facts; written-method and executed-method variants."""
import sys, numpy as np, pandas as pd
from scipy.stats import fisher_exact
sys.path.insert(0, 'code')
from analysis import ST, MODELS, PER, per
from cdx import INDICES, TEMP

GROUPS = {
    'Baseline temperature regime': (['TMm', 'TNm', 'TXm', 'TNn', 'TNx', 'TXn', 'TXx'], 1),
    'Cold extremes and cold waves': (['FD', 'ID', 'TN10p', 'TX10p', 'TNltm20', 'CSDI6', 'CSDI3', 'CWA', 'CWF'], 'cold'),
    'Heat extremes and heat waves': (['SU', 'TR', 'TN90p', 'TX90p', 'TXge30', 'TXgt50p', 'TXb3TNb3', 'WSDI6', 'WSDI3', 'HWA', 'HWF'], 1),
    'Growing season and heat accumulation': (['GSL', 'GDDgrow10'], 1),
    'Diurnal temperature structure': (['DTR', 'DTRgt15'], 'dom'),
    'Precipitation amount and frequency': (['PRCPTOT', 'R10mm', 'R20mm'], 1),
    'Extreme precipitation intensity': (['RX1day', 'RX3day', 'RX5day', 'SDII', 'R95p', 'R99p', 'R95pTOT', 'R99pTOT'], 1),
    'Wet-dry spell persistence': (['CDD', 'CWD'], 'dom'),
}


def skill_change(F):
    mp = F['mp'].copy(); mp['ok'] = mp.p >= 0.05
    np_ = mp.groupby(['station', 'index']).ok.sum(); pr = mp[mp.period == 'P'].groupby(['station', 'index']).ok.sum()
    e = F['env'].set_index(['station', 'index'])
    e['npass'] = np_; e['pr'] = pr
    b = e.cv7 == 'bounded'
    out = {}
    for name, sk in {'>=10of20': e.npass >= 10, '>=15of20': e.npass >= 15, 'Pres>=5': e.pr >= 5, 'Pres>=8': e.pr >= 8}.items():
        a, bb, c, d = int((sk & b).sum()), int((sk & ~b).sum()), int((~sk & b).sum()), int((~sk & ~b).sum())
        out[name] = dict(a=a, b=bb, c=c, d=d, misjudged=bb + c, skilful=a + bb, bounded_if_sk=100 * a / max(a + bb, 1),
                         bounded_if_not=100 * c / max(c + d, 1), fisher_p=fisher_exact([[a, bb], [c, d]])[1],
                         rev_among_skilful=int((sk & (e.cv7 == 'sign_reversal')).sum()))
    return out, e


def c1(F, include_obs=True):
    D = F['D']; rows = []
    for st in ST:
        for ix in INDICES:
            r = dict(station=st, index=ix)
            for p in PER:
                srcs = (['OBS'] + MODELS) if (include_obs and p in 'HP') else MODELS
                v = np.concatenate([per(D[(st, s)], p, ix) for s in srcs])
                q1, md, q3 = np.quantile(v, [0.25, 0.5, 0.75]); iqr = q3 - q1
                r.update({f'med_{p}': md, f'q1_{p}': q1, f'q3_{p}': q3, f'out_{p}': int(((v < q1 - 1.5 * iqr) | (v > q3 + 1.5 * iqr)).sum()), f'n_{p}': len(v)})
            dm = r['med_F'] - r['med_H']; ih = r['q3_H'] - r['q1_H']; iff = r['q3_F'] - r['q1_F']
            sh = 'Increase' if dm > 0 else ('Decrease' if dm < 0 else 'No Shift')
            if ih == 0 and iff == 0: sp = 'Stable Spread'
            elif ih == 0: sp = 'Spread Expanded'
            else:
                ratio = iff / ih
                sp = 'Spread Contracted' if ratio < 0.8 else ('Spread Expanded' if ratio > 1.25 else 'Stable Spread')
            r['label'] = f'{sh} ({sp})'
            rows.append(r)
    return pd.DataFrame(rows)


def _coh(vals, idx, sg, zero_ok=False):
    s = np.sign(np.round(np.asarray(vals, float), 6))
    if sg == 'dom':
        return max((s == 1).sum(), (s == -1).sum()) + ((s == 0).sum() if zero_ok else 0)
    ex = np.array([1 if i == 'CWA' else -1 for i in idx]) if sg == 'cold' else np.full(len(idx), sg)
    return int(((s == ex) | ((s == 0) & zero_ok)).sum())


def d1(F, c1tab=None, priori=None):
    """priori: override group direction for 'dom' groups (written method: a priori pattern)."""
    e = F['env']; D = F['D']; rows = []
    pm = lambda st, ix, p: np.median(np.concatenate([per(D[(st, m)], p, ix) for m in MODELS]))
    for g, (ks, sg) in GROUPS.items():
        if priori and g in priori: sg = priori[g]
        sub = e[e['index'].isin(ks)]; n = len(sub)
        fut = {}
        for p in 'NF':
            v, ix = [], []
            for st in ST:
                for k in ks:
                    v.append(pm(st, k, p) - pm(st, k, 'H')); ix.append(k)
            fut[p] = _coh(v, ix, sg)
        ch = _coh(sub.obs.values, sub['index'].values, sg)
        bnd = int((sub.cv7 == 'bounded').sum()); sr = int((sub.cv7 == 'sign_reversal').sum())
        zero = float(np.mean(np.round(sub.obs.values, 6) == 0))
        pc = [100 * ch / n, 100 * fut['N'] / n, 100 * fut['F'] / n]; pb = 100 * bnd / n
        agree = all(_coh(sub[sub.station == s].obs.values, sub[sub.station == s]['index'].values, sg) / max(len(sub[sub.station == s]), 1) >= 0.6 for s in ST)
        conf = 'Low' if (zero >= 0.5 or pb < 60 or sum(x < 60 for x in pc) >= 2) else ('High' if (sum(x >= 80 for x in pc) >= 2 and pb >= 80 and sr == 0 and agree) else 'Moderate')
        rows.append(dict(group=g, n=n, coh_HP=round(pc[0], 1), coh_N=round(pc[1], 1), coh_F=round(pc[2], 1), bounded=round(pb, 1),
                         sign_rev=sr, zero_share=round(100 * zero, 1), agree60=agree, conf=conf))
    return pd.DataFrame(rows)

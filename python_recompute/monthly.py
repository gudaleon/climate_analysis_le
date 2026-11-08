"""Monthly analysis (Pass 1): 14 monthly indices; upper-quartile (>= Q75, R type 7) subset per month x period
(lower quartile <= Q25 for TXn); subset median; change and Wilcoxon (same settings) for H->P and N->F."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from cdx import read_daily
from spei import spei_spi
from analysis import wilcox, PER, MODELS, ST

LAT = {'London': 43.033, 'Fergus': 43.735, 'Harrow': 42.034}
P = '/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/'
OBSF = {'London': 'LONDON', 'Fergus': 'FERGUS', 'Harrow': 'HARROW'}


def daily_path(st, src, branch):
    if src == 'OBS':
        if branch == 'H0merged':
            f = {'London': 'LONDON_merged_6144475_6144478.txt', 'Fergus': 'FERGUS_SHAND_DAM_6142400.txt', 'Harrow': 'HARROW_merged_6133360_613CC60_6133362.txt'}[st]
            return P + '1_Observations/b_Merged_daily_series/' + f
        if branch == 'AUTHORS_v4':
            return P + f'1_Observations/c_Homogenised_daily_series/{OBSF[st]}_homogenised_v4.txt'
        return f'out/homog_{branch}_{OBSF[st]}.csv'
    return P + f'2_Models/b_Daily_series/{st}_{src}.txt'


def monthly_table(st, src, branch='H1_reviewed', idxdir='out/idx'):
    tag = f'{st}_{src}' if src != 'OBS' else f'{st}_OBS_{branch}'
    m = pd.read_csv(f'{idxdir}/{tag}_monthly.csv', index_col=[0, 1])
    path = daily_path(st, src, branch)
    d = pd.read_csv(path) if path.endswith('.csv') else read_daily(path)
    g = d.groupby(['year', 'month'])
    tx = g.tx.mean(); tn = g.tn.mean()
    pr = g.pr.apply(lambda s: np.nan if s.isna().all() else s.sum(skipna=True))
    full = pd.MultiIndex.from_product([range(int(d.year.min()), int(d.year.max()) + 1), range(1, 13)], names=['year', 'month'])
    tx, tn, pr = [s.reindex(full).values for s in (tx, tn, pr)]
    yrs = full.get_level_values(0).values; mos = full.get_level_values(1).values
    sp = spei_spi(tx, tn, pr, yrs, mos, LAT[st])
    for k, v in sp.items():
        m[k] = pd.Series(v, index=full).reindex(m.index).values
    return m


IDX = ['TMm', 'TXx', 'TXn', 'ID', 'SU', 'RX1day', 'RX5day', 'PRCPTOT', 'R10mm', 'CDD', 'SPI3', 'SPI6', 'SPEI3', 'SPEI6']


def subset(x, ix):
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return x
    if ix == 'TXn':
        return x[x <= np.quantile(x, 0.25)]
    return x[x >= np.quantile(x, 0.75)]


def stats(m, months=range(1, 13)):
    rows = []
    for ix in IDX:
        for mo in months:
            s = {}
            for p, (a, b) in PER.items():
                sel = m.loc[(m.index.get_level_values(0) >= a) & (m.index.get_level_values(0) <= b) & (m.index.get_level_values(1) == mo), ix].values.astype(float)
                s[p] = subset(sel, ix)
                s['n' + p] = int((~np.isnan(sel)).sum()); s['all' + p] = sel[~np.isnan(sel)]
            r = dict(index=ix, month=mo)
            for p in PER:
                r['uq_' + p] = float(np.median(s[p])) if len(s[p]) else np.nan
                r['n_' + p] = s['n' + p]
            r['d_HP'] = r['uq_P'] - r['uq_H']; r['p_HP'] = wilcox(s['H'], s['P'])
            r['d_NF'] = r['uq_F'] - r['uq_N']; r['p_NF'] = wilcox(s['N'], s['F'])
            r['d_HF'] = r['uq_F'] - r['uq_H']
            r['pall_HP'] = wilcox(s['allH'], s['allP']); r['pall_NF'] = wilcox(s['allN'], s['allF'])
            rows.append(r)
    return pd.DataFrame(rows)


if __name__ == '__main__':
    branch = sys.argv[1] if len(sys.argv) > 1 else 'H1_reviewed'
    out = []
    for st in ST:
        for src in ['OBS'] + MODELS:
            if src != 'OBS' and branch not in ('H1_reviewed', 'MODELS'):
                continue
            try:
                m = monthly_table(st, src, branch)
            except FileNotFoundError as e:
                print('missing', e); continue
            s = stats(m); s['station'] = st; s['source'] = src
            out.append(s)
            print(st, src, flush=True)
    pd.concat(out).to_csv(f'out/monthly_stats_{branch}.csv', index=False)

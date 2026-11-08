import sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from engine import *
from analysis import wilcox, per, MODELS, ST
from cdx import read_daily
X = {}
P = '/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/'
S3 = ['London', 'Fergus', 'Harrow']
# 1. reference-model dependence of monthly headlines (all ten models in the reference role)
mods = MO['MOD']
def m(st, src, ix, mo, col):
    r = mods[(mods.station == st) & (mods.source == src) & (mods['index'] == ix) & (mods.month == mo)].iloc[0]
    return r[col]
rows = []
for src in MODELS:
    rows.append(dict(model=src,
                     wetter_jan_all3=all(m(s, src, 'PRCPTOT', 1, 'd_NF') > 0 for s in S3),
                     spei6_JAS_decline_all3=all(m(s, src, 'SPEI6', mo, 'd_NF') < 0 for s in S3 for mo in (7, 8, 9)),
                     spei6_AugSep_F_negative_all3=all(m(s, src, 'SPEI6', mo, 'uq_F') < 0 for s in S3 for mo in (8, 9)),
                     prcptot_JAS_decline_all3=all(m(s, src, 'PRCPTOT', mo, 'd_NF') < 0 for s in S3 for mo in (7, 8, 9)),
                     harrow_largest_JJAS_loss=min(S3, key=lambda s: sum(m(s, src, 'PRCPTOT', mo, 'd_NF') for mo in (6, 7, 8, 9))) == 'Harrow',
                     sep_rx5_F_above_H_all3=all(m(s, src, 'RX5day', 9, 'd_HF') > 0 for s in S3),
                     sep_TXx_HP_warms_all3=all(m(s, src, 'TXx', 9, 'd_HP') > 0 for s in S3),
                     gap_F_max=max(m(s, src, 'SPI6', mo, 'uq_F') - m(s, src, 'SPEI6', mo, 'uq_F') for s in S3 for mo in (6, 7, 8, 9))))
X['refmodel'] = pd.DataFrame(rows)
# 2. daily integrity: model DTR/DTRgt15 with tn>tx days removed (cleaning rule applied to obs only by authors)
dd = []
for st in S3:
    for mdl in MODELS:
        d = read_daily(P + f'2_Models/b_Daily_series/{st}_{mdl}.txt')
        bad = d.tn > d.tx
        yr = d.year
        raw = (d.tx - d.tn).groupby(yr).mean(); cln = (d.tx - d.tn).where(~bad).groupby(yr).mean()
        g15r = ((d.tx - d.tn) > 15).groupby(yr).sum()
        for p, (a, b) in (('H', (1950, 1986)), ('P', (1987, 2023))):
            dd.append(dict(station=st, model=mdl, period=p, dtr_raw=raw.loc[a:b].median(), dtr_clean=cln.loc[a:b].median(), n_bad=int(bad[(yr >= a) & (yr <= b)].sum())))
        # pass test for DTR with cleaned values
        for p, (a, b) in (('H', (1950, 1986)), ('P', (1987, 2023))):
            o = L['V4']['D'][(st, 'OBS')].loc[a:b, 'DTR'].dropna().values
            dd[-2 if p == 'H' else -1]['p_raw'] = wilcox(o, raw.loc[a:b].values); dd[-2 if p == 'H' else -1]['p_clean'] = wilcox(o, cln.loc[a:b].values)
X['dtr_clean'] = pd.DataFrame(dd)
# 3. calendar composition: effect of 365-day calendar on annual counts (expected extra Feb-29 day in 37 leap years)
X['leap'] = 'Gregorian models carry 37 Feb-29 days 1950-2100; 365-day models carry none (Climpact treats them as missing days).'
# 4. printed-definition TXb3TNb3 (warm compound events) vs executed (cold events): pass counts / envelope
for lay in ('V4',):
    D = L[lay]['D']
    res = {}
    for st in S3:
        pw = [wilcox(per(D[(st, 'OBS')], p, 'x_TXd3TNd3_warm_events') if 'x_TXd3TNd3_warm_events' in D[(st, 'OBS')] else [], per(D[(st, mm)], p, 'x_TXd3TNd3_warm_events')) for mm in MODELS for p in 'HP']
        pc = [wilcox(per(D[(st, 'OBS')], p, 'TXb3TNb3'), per(D[(st, mm)], p, 'TXb3TNb3')) for mm in MODELS for p in 'HP']
        dobs = np.median(per(D[(st, 'OBS')], 'P', 'x_TXd3TNd3_warm_events')) - np.median(per(D[(st, 'OBS')], 'H', 'x_TXd3TNd3_warm_events'))
        dm = [np.median(per(D[(st, mm)], 'P', 'x_TXd3TNd3_warm_events')) - np.median(per(D[(st, mm)], 'H', 'x_TXd3TNd3_warm_events')) for mm in MODELS]
        res[st] = dict(passes_cold_executed=int(sum(np.nan_to_num(pc, nan=0) >= 0.05)), passes_warm_printed=int(sum(np.nan_to_num(pw, nan=0) >= 0.05)),
                       warm_dobs=float(dobs), warm_lo=float(min(dm)), warm_hi=float(max(dm)), warm_bounded=bool(min(dm) <= dobs <= max(dm)),
                       warm_FF_ens_median=float(np.median([np.median(per(D[(st, mm)], 'F', 'x_TXd3TNd3_warm_events')) - np.median(per(D[(st, mm)], 'H', 'x_TXd3TNd3_warm_events')) for mm in MODELS])))
    X['txb3_variant'] = res
# 5. homogenisation dependence table
hd = {}
for lay in ('V4', 'H1', 'H1b', 'H0', 'H2'):
    e = L[lay]['env']
    hd[lay] = dict(bounded=int(e.within.sum()), per_station=e.groupby('station').within.sum().to_dict(), rev613=int((e.c613 == 'reversal').sum()),
                   mag613=int((e.c613 == 'magnitude').sum()), signrev=int((e.cv7 == 'sign_reversal').sum()),
                   signrev_list=sorted(f'{a} {b}' for a, b in e[e.cv7 == 'sign_reversal'][['station', 'index']].values),
                   rev613_list=sorted(f'{a} {b}' for a, b in e[e.c613 == 'reversal'][['station', 'index']].values),
                   allthree=int(e.groupby('index').within.all().sum()), refs={s: L[lay]['refs'][s]['temp_ref'] for s in S3},
                   temp_scores_ref={s: L[lay]['refs'][s]['temp_scores'][L[lay]['refs'][s]['temp_ref']] for s in S3})
    if lay in SC: hd[lay]['skill'] = {k: SC[lay]['>=10of20'][k] for k in ('a', 'b', 'c', 'd', 'misjudged', 'fisher_p')}
    if lay in D1: hd[lay]['D1'] = D1[lay].set_index('group').conf.to_dict()
X['homog'] = hd
# monthly obs headline dependence on homogenisation
mh = {}
for lay in ('V4', 'H1', 'H0', 'H2'):
    t = MO[lay]; t = t[t.source == 'OBS']
    q = lambda st, ix, mo, c: float(t[(t.station == st) & (t['index'] == ix) & (t.month == mo)][c].iloc[0])
    mh[lay] = dict(fergus_mar_tmm=(round(q('Fergus', 'TMm', 3, 'uq_H'), 2), round(q('Fergus', 'TMm', 3, 'uq_P'), 2)),
                   sep_txx_HP={s: round(q(s, 'TXx', 9, 'd_HP'), 2) for s in S3}, london_feb_txx=(round(q('London', 'TXx', 2, 'uq_H'), 2), round(q('London', 'TXx', 2, 'uq_P'), 2)),
                   mar_id_pct={s: round(100 * q(s, 'ID', 3, 'd_HP') / q(s, 'ID', 3, 'uq_H'), 1) for s in S3})
X['homog_monthly'] = mh
# 6. monthly test design flips
mp = pd.read_csv('out/monthly_p_compare.csv')
X['monthly_test_flips'] = dict(n=len(mp), flips=int(((mp.p_wb < 0.05) != (mp.p_subset < 0.05)).sum()),
                               sig_exec=int((mp.p_wb < 0.05).sum()), sig_printed_method=int((mp.p_subset < 0.05).sum()))
json.dump(X, open('out/extras.json', 'w'), indent=1, default=lambda o: o.to_dict(orient='records') if hasattr(o, 'to_dict') else str(o))
print(X['refmodel'].to_string()); print(X['dtr_clean'].groupby('period')[['n_bad']].sum(), (X['dtr_clean'].p_clean >= 0.05).sum(), (X['dtr_clean'].p_raw >= 0.05).sum())
print(json.dumps(X['txb3_variant'], indent=0)); print(json.dumps(X['homog'], indent=0, default=str)[:3500]); print(X['homog_monthly']); print(X['monthly_test_flips'])

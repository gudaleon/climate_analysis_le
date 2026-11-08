import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'code')
from cdx import read_daily
from homog import *

S = '/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/'
F = {'LONDON': 'LONDON_merged_6144475_6144478.txt', 'FERGUS': 'FERGUS_SHAND_DAM_6142400.txt', 'HARROW': 'HARROW_merged_6133360_613CC60_6133362.txt'}
raw = {}
for st, f in F.items():
    d = read_daily(S + '2_Data/1_Observations/b_Merged_daily_series/' + f)
    bad = d.tx < d.tn
    print(st, 'tx<tn days set missing before testing:', int(bad.sum()))
    d.loc[bad, ['tx', 'tn']] = np.nan
    d.index = pd.to_datetime(d[['year', 'month', 'day']])
    raw[st] = d
cand = pd.read_csv(S + '3_Code/step02_homogenisation/config/candidates.csv')
months = monthly_anom(raw['LONDON'], 'tx').index


def mi(yyyymm):
    y, m = divmod(int(yyyymm), 100)
    return months.get_loc((y, m)) - 1     # break = end of previous month (new segment starts at yyyymm)


def mdate(i):
    y, m = months[i + 1]
    return pd.Timestamp(year=y, month=m, day=1)


def diffseries(cur, st, v):
    oth = [s for s in F if s != st]
    a = monthly_anom(cur[st], v).values
    r = np.nanmean(np.vstack([monthly_anom(cur[o], v).values for o in oth]), 0)
    return a - r


def run_branch(mode, force=None):
    """mode: 'reviewed' or 'auto'. force: dict {(st,v,yyyymm): True/False} to force retain/prune."""
    logs = {}
    adj = {st: raw[st].copy() for st in F}
    for rnd in (1, 2):
        ref = raw if rnd == 1 else prev
        new = {st: raw[st].copy() for st in F}
        for st in F:
            for v in ('tx', 'tn'):
                cur = {s: (ref[s] if s != st else raw[st]) for s in F}
                x = diffseries(cur, st, v)
                if mode == 'reviewed':
                    c = cand[(cand.station == st) & (cand.variable == v)]
                    cl = [(mi(r.yyyymm), int(r.type)) for r in c.itertuples()]
                else:
                    oth = [s for s in F if s != st]
                    a = monthly_anom(raw[st], v).values
                    d1 = a - monthly_anom(cur[oth[0]], v).values
                    d2 = a - monthly_anom(cur[oth[1]], v).values
                    d12 = monthly_anom(cur[oth[0]], v).values - monthly_anom(cur[oth[1]], v).values
                    b0 = detect(x); b1 = detect(d1); b2 = detect(d2); b3 = detect(d12)
                    near = lambda b, L: any(abs(b - c) <= 18 for c in L)
                    cl = [(b, 1) for b in b0 if near(b, b1) and near(b, b2) and not near(b, b3)]
                kept, log, tests = prune(x, cl)
                if force:
                    for (fs, fv, ym), keep in force.items():
                        if fs == st and fv == v:
                            i = mi(ym)
                            if keep and i not in [k[0] for k in kept]:
                                kept = sorted(kept + [(i, 0)])
                            if not keep:
                                kept = [k for k in kept if k[0] != i]
                tests = step_tests(x, [k[0] for k in kept])
                logs[(rnd, st, v)] = dict(candidates=[f'{months[i+1][0]}-{months[i+1][1]:02d}' for i, _ in cl],
                                          retained=[f'{months[i+1][0]}-{months[i+1][1]:02d}' for i, _ in kept],
                                          steps=[round(t['step'], 2) for t in tests], sig=[t['sig'] for t in tests])
                if kept:
                    oth = [s for s in F if s != st]
                    refd = np.nanmean(np.vstack([cur[o][v].reindex(raw[st].index).values for o in oth]), 0)
                    new[st][v] = qm_adjust(raw[st], v, [mdate(i) for i, _ in kept], ref=refd)
            m = new[st].tn > new[st].tx
            new[st].loc[m, 'tn'] = new[st].loc[m, 'tx']
            logs[(rnd, st, 'clipped')] = int(m.sum())
        prev = new
    return prev, logs


if __name__ == '__main__':
    out = {}
    branches = {'H1_reviewed': ('reviewed', None),
                'H1a_reviewed_force1985kept': ('reviewed', {('FERGUS', 'tn', 198502): True}),
                'H1b_reviewed_force1985pruned': ('reviewed', {('FERGUS', 'tn', 198502): False}),
                'H2_auto': ('auto', None)}
    for name, (mode, force) in branches.items():
        series, logs = run_branch(mode, force)
        for st in F:
            d = series[st].copy()
            d[['year', 'month', 'day', 'pr', 'tx', 'tn']].to_csv(f'out/homog_{name}_{st}.csv', index=False)
        out[name] = {f'{k[0]}|{k[1]}|{k[2]}': v for k, v in logs.items()}
        nb = sum(len(v['retained']) for k, v in logs.items() if k[0] == 2 and k[2] != 'clipped')
        print(name, 'round-2 retained breaks:', nb)
        for k, v in logs.items():
            if k[0] == 2:
                print('   ', k, v)
    for st in F:
        raw[st][['year', 'month', 'day', 'pr', 'tx', 'tn']].to_csv(f'out/homog_H0_raw_{st}.csv', index=False)
    json.dump(out, open('out/homog_logs.json', 'w'), indent=1, default=str)

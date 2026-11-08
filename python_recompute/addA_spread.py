"""Addendum A item 5: size of the one-cell effect relative to the ten-model spread at Fergus, per branch."""
import pickle, numpy as np, pandas as pd, sys
sys.path.insert(0, 'code')
from cdx import INDICES, TEMP
X = pickle.load(open('out_addA/tables_AUTHORS_v4.pkl', 'rb'))
mm, pm, pcT, pcS = X['mm'], X['pm'], X['pcT'], X['pcS']
rows = []
for ix in INDICES:
    r = dict(index=ix, grp='T' if ix in TEMP else 'P')
    for p in 'HPNF':
        g = mm[(mm['index'] == ix) & (mm.period == p)]
        r[f'cell_{p}'] = np.nanmedian(np.abs(g.d))            # median over models of |S-T| in model period median
        r[f'spT_{p}'] = g['T'].max() - g['T'].min(); r[f'spS_{p}'] = g['S'].max() - g['S'].min()
        r[f'pool_{p}'] = abs(pm.loc[ix, f'd_{p}'])
    for comp in 'PNF':
        a = pcT[(pcT['index'] == ix) & pcT.source.isin(X['t1T'].index) & (pcT.comp == comp)].set_index('source').delta
        b = pcS[(pcS['index'] == ix) & pcS.source.isin(X['t1T'].index) & (pcS.comp == comp)].set_index('source').delta
        r[f'dcell_{comp}'] = np.nanmedian(np.abs(b - a)); r[f'dspT_{comp}'] = a.max() - a.min(); r[f'dspS_{comp}'] = b.max() - b.min()
        r[f'dens_{comp}'] = abs(np.nanmedian(b) - np.nanmedian(a))
    rows.append(r)
d = pd.DataFrame(rows).set_index('index')
for p in 'HPNF':
    d[f'ratio_{p}'] = d[f'cell_{p}'] / np.maximum(d[f'spT_{p}'], 1e-12)
for c in 'PNF':
    d[f'dratio_{c}'] = d[f'dcell_{c}'] / np.maximum(d[f'dspT_{c}'], 1e-12)
d.to_csv('out_addA/fergus_cell_vs_spread.csv')
pd.set_option('display.width', 250)
print(d[[f'ratio_{p}' for p in 'HPNF'] + [f'dratio_{c}' for c in 'PNF']].groupby(d.grp).median().round(3))
print(d[[f'ratio_{p}' for p in 'HPNF'] + [f'dratio_{c}' for c in 'PNF']].median().round(3).to_dict())
print(d[[f'ratio_{p}' for p in 'HPNF'] + [f'dratio_{c}' for c in 'PNF']].max().round(3).to_dict())
print(d[[f'ratio_{p}' for p in 'HPNF']].idxmax().to_dict(), d[[f'dratio_{c}' for c in 'PNF']].idxmax().to_dict())

"""Addendum B: monthly upper-quartile stats (monthly.py, unchanged settings) for the ten Branch P Harrow model series."""
import sys, pandas as pd
sys.path.insert(0, 'code')
import monthly
M = {'ACCESS': 'ACCESS-ESM1-5', 'BCC': 'BCC-CSM2-MR', 'CanESM': 'CanESM5', 'CNRM': 'CNRM-ESM2-1', 'EC': 'EC-Earth3-Veg',
     'GFDL': 'GFDL-ESM4', 'INM': 'INM-CM5-0', 'MIROC': 'MIROC-ES2L', 'MRI': 'MRI-ESM2-0', 'NorESM': 'NorESM2-LM'}
monthly.daily_path = lambda st, src, branch: f'out_addB/txt/HARROWP_{M[src]}.txt'
out = []
for src in M:
    s = monthly.stats(monthly.monthly_table('Harrow', src, 'H1_reviewed', idxdir='out_addB/idx')); s['station'] = 'Harrow'; s['source'] = src
    out.append(s); print(src, flush=True)
pd.concat(out).to_csv('out_addB/monthly_stats_P_Harrow_models.csv', index=False)

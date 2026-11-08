"""Addendum A: monthly upper-quartile stats (monthly.py, unchanged settings) for the ten Branch S Fergus model series."""
import sys, pandas as pd
sys.path.insert(0, 'code')
import monthly
Q = '/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final/txt/'
M = {'ACCESS': 'ACCESS-ESM1-5', 'BCC': 'BCC-CSM2-MR', 'CanESM': 'CanESM5', 'CNRM': 'CNRM-ESM2-1', 'EC': 'EC-Earth3-Veg',
     'GFDL': 'GFDL-ESM4', 'INM': 'INM-CM5-0', 'MIROC': 'MIROC-ES2L', 'MRI': 'MRI-ESM2-0', 'NorESM': 'NorESM2-LM'}
monthly.daily_path = lambda st, src, branch: Q + f'FERGUS_{M[src]}.txt'
out = []
for src in M:
    s = monthly.stats(monthly.monthly_table('Fergus', src, 'H1_reviewed', idxdir='out_addA/idx')); s['station'] = 'Fergus'; s['source'] = src
    out.append(s); print(src, flush=True)
pd.concat(out).to_csv('out_addA/monthly_stats_S_Fergus_models.csv', index=False)

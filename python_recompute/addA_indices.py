"""Addendum A: 44 annual + monthly indices (cdx.py, unchanged) on the Branch S Fergus model series (PCIC label FERGUS, cell 32/727)."""
import sys, os, pandas as pd
sys.path.insert(0, 'code'); from cdx import Series, read_daily
from multiprocessing import Pool
Q = '/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final/txt/'
M = {'ACCESS': 'ACCESS-ESM1-5', 'BCC': 'BCC-CSM2-MR', 'CanESM': 'CanESM5', 'CNRM': 'CNRM-ESM2-1', 'EC': 'EC-Earth3-Veg',
     'GFDL': 'GFDL-ESM4', 'INM': 'INM-CM5-0', 'MIROC': 'MIROC-ES2L', 'MRI': 'MRI-ESM2-0', 'NorESM': 'NorESM2-LM'}
def run(m):
    o = f'out_addA/idx/Fergus_{m}_annual.csv'
    if os.path.exists(o): return m
    s = Series(read_daily(Q + f'FERGUS_{M[m]}.txt'), f'Fergus_{m}')
    s.annual().to_csv(o); s.monthly().to_csv(f'out_addA/idx/Fergus_{m}_monthly.csv'); return m
if __name__ == '__main__':
    with Pool(2) as p:
        for n in p.imap_unordered(run, list(M)): print(n, flush=True)

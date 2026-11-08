"""Addendum B: assemble out_addB/idx (symlinks to out/idx for every series except the ten Harrow model
series) and compute the 44 annual + monthly indices (cdx.py, unchanged) on the Branch P Harrow model
series (perturbed cell 12/696, extracted in Stage 1 to out_addB/txt/HARROWP_<model>.txt)."""
import sys, os, pandas as pd
sys.path.insert(0, 'code'); from cdx import Series, read_daily
from multiprocessing import Pool
SRC = 'out/idx'; DST = 'out_addB/idx'
os.makedirs(DST, exist_ok=True)
M = {'ACCESS': 'ACCESS-ESM1-5', 'BCC': 'BCC-CSM2-MR', 'CanESM': 'CanESM5', 'CNRM': 'CNRM-ESM2-1', 'EC': 'EC-Earth3-Veg',
     'GFDL': 'GFDL-ESM4', 'INM': 'INM-CM5-0', 'MIROC': 'MIROC-ES2L', 'MRI': 'MRI-ESM2-0', 'NorESM': 'NorESM2-LM'}
for f in os.listdir(SRC):
    dst = os.path.join(DST, f)
    if any(f == f'Harrow_{m}_{k}.csv' for m in M for k in ('annual', 'monthly')):
        continue
    if not os.path.lexists(dst):
        os.symlink(os.path.abspath(os.path.join(SRC, f)), dst)

def run(m):
    o = f'{DST}/Harrow_{m}_annual.csv'
    if os.path.exists(o): return m
    s = Series(read_daily(f'out_addB/txt/HARROWP_{M[m]}.txt'), f'Harrow_{m}')
    s.annual().to_csv(o); s.monthly().to_csv(f'{DST}/Harrow_{m}_monthly.csv'); return m

if __name__ == '__main__':
    with Pool(2) as p:
        for n in p.imap_unordered(run, list(M)): print(n, flush=True)
    print('idx entries:', len(os.listdir(DST)), 'symlinks:', sum(os.path.islink(os.path.join(DST, f)) for f in os.listdir(DST)))

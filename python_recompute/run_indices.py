import sys, os, numpy as np, pandas as pd
sys.path.insert(0,'code'); from cdx import *
from multiprocessing import Pool
P='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/'
os.makedirs('out/idx',exist_ok=True)
jobs=[]
for st in ['London','Fergus','Harrow']:
    for m in ['ACCESS','BCC','CanESM','CNRM','EC','GFDL','INM','MIROC','MRI','NorESM']:
        jobs.append((f'{st}_{m}', P+f'2_Models/b_Daily_series/{st}_{m}.txt'))
OBS={'LONDON':'LONDON_merged_6144475_6144478.txt','FERGUS':'FERGUS_SHAND_DAM_6142400.txt','HARROW':'HARROW_merged_6133360_613CC60_6133362.txt'}
for st,f in OBS.items():
    jobs.append((f'{st.title()}_OBS_H0merged', P+'1_Observations/b_Merged_daily_series/'+f))
    for b in ['H0_raw','H1_reviewed','H1a_reviewed_force1985kept','H1b_reviewed_force1985pruned','H2_auto']:
        jobs.append((f'{st.title()}_OBS_{b}', f'out/homog_{b}_{st}.csv'))
if len(sys.argv)>1: jobs=[j for j in jobs if any(k in j[0] for k in sys.argv[1:])]
def run(j):
    name,path=j
    if os.path.exists(f'out/idx/{name}_annual.csv'): return name
    d=pd.read_csv(path) if path.endswith('.csv') else read_daily(path)
    s=Series(d,name)
    s.annual().to_csv(f'out/idx/{name}_annual.csv')
    s.monthly().to_csv(f'out/idx/{name}_monthly.csv')
    return name
if __name__=='__main__':
    with Pool(2) as p:
        for n in p.imap_unordered(run,jobs): print(n,flush=True)

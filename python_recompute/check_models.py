import sys, hashlib, numpy as np, pandas as pd
sys.path.insert(0,'code'); from cdx import read_daily
P='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/2_Models/b_Daily_series/'
P2='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data/2_Data/2_Models/b_Daily_series/'
Q='/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final/txt/'
M={'ACCESS':'ACCESS-ESM1-5','BCC':'BCC-CSM2-MR','CanESM':'CanESM5','CNRM':'CNRM-ESM2-1','EC':'EC-Earth3-Veg','GFDL':'GFDL-ESM4','INM':'INM-CM5-0','MIROC':'MIROC-ES2L','MRI':'MRI-ESM2-0','NorESM':'NorESM2-LM'}
h=lambda f: hashlib.sha256(open(f,'rb').read()).hexdigest()
rows=[]
for st in ['London','Fergus','Harrow']:
  for m,full in M.items():
    a=P+f'{st}_{m}.txt'; b=Q+f'{st.upper()}_{full}.txt'; c=P2+f'{st}_{m}.txt'
    da=read_daily(a); db=read_daily(b)
    same=h(a)==h(b); same2=h(a)==h(c)
    d=pd.to_datetime(dict(year=da.year,month=da.month,day=da.day))
    dup=d.duplicated().sum(); feb29=((da.month==2)&(da.day==29)).sum()
    gaps=(d.diff().dt.days>1).sum()
    eqv=np.allclose(da[['pr','tx','tn']].values, db[['pr','tx','tn']].values, equal_nan=True) if len(da)==len(db) else False
    rows.append(dict(station=st,model=m,rows=len(da),feb29=feb29,dup=dup,gaps_gt1day=gaps,
      sha_eq_pcic=same,values_eq_pcic=eqv,sha_eq_pkg2=same2,
      tn_gt_tx=int((da.tn>da.tx).sum()),neg_pr=int((da.pr<0).sum()),missing=int(da[['pr','tx','tn']].isna().sum().sum()),
      first=f'{da.year.iloc[0]}-{da.month.iloc[0]}-{da.day.iloc[0]}',last=f'{da.year.iloc[-1]}-{da.month.iloc[-1]}-{da.day.iloc[-1]}'))
df=pd.DataFrame(rows); df.to_csv('out/model_daily_integrity.csv',index=False); print(df.to_string())

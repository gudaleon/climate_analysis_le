import sys,numpy as np,pandas as pd; sys.path.insert(0,'code'); from cdx import INDICES
from analysis import MODELS
A='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/3_Annual_index_tables/'
NAME={'csdi':'CSDI6','csdi3':'CSDI3','wsdi':'WSDI6','wsdi3':'WSDI3','dtrgt15':'DTRgt15','gddgrow10':'GDDgrow10','txb3tnb3':'TXb3TNb3','txge30':'TXge30','txgt50p':'TXgt50p','tnltm20':'TNltm20','r95ptot':'R95pTOT','r99ptot':'R99pTOT','rx1day':'RX1day','rx3day':'RX3day','rx5day':'RX5day','r10mm':'R10mm','r20mm':'R20mm','prcptot':'PRCPTOT'}
rows=[]
for st in ['London','Fergus','Harrow']:
    t=pd.read_excel(A+f'All_{st}_observed_and_10_models_1950-2100.xlsx')
    t=t.replace(-99.9,np.nan); t['Index']=[NAME.get(str(i).strip().lower(),None) or next(x for x in INDICES if x.lower()==str(i).strip().lower()) for i in t.Index]
    for src in ['Observed']+MODELS:
        mine=pd.read_csv(f'out/idx/{st}_'+('OBS_AUTHORS_v4' if src=='Observed' else src)+'_annual.csv',index_col=0)
        for ix in INDICES:
            th=t[t.Index==ix].set_index('Year')[src]; mi=mine[ix].reindex(th.index)
            ok=~(th.isna()|mi.isna()); d=(th[ok]-mi[ok]).abs()
            rows.append(dict(station=st,source=src,index=ix,n_both=int(ok.sum()),na_mismatch=int((th.isna()!=mi.isna()).sum()),
                n_diff_gt_0p01=int((d>0.011).sum()),max_abs=float(d.max()) if len(d) else 0.0))
r=pd.DataFrame(rows); r.to_csv('out/diff_annual_vs_authors.csv',index=False)
print('cells compared',r.n_both.sum(),'cells differing >0.01',r.n_diff_gt_0p01.sum(),'NA-pattern mismatches',r.na_mismatch.sum())
g=r.groupby('index')[['n_both','n_diff_gt_0p01','na_mismatch','max_abs']].agg({'n_both':'sum','n_diff_gt_0p01':'sum','na_mismatch':'sum','max_abs':'max'})
print(g[(g.n_diff_gt_0p01>0)|(g.na_mismatch>0)].to_string())
print(r[r.source=='Observed'].groupby('station')[['n_diff_gt_0p01','na_mismatch']].sum())

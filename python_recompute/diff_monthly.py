import pandas as pd,numpy as np,sys
W=pd.read_excel('/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/4_Results/Thesis_6.13_results_new_data.xlsx',sheet_name='Monthly (Sec 3.4)')
mo=pd.read_csv('out/monthly_stats_H1_reviewed.csv'); ob=pd.read_csv('out/monthly_stats_AUTHORS_v4.csv')
mo=pd.concat([mo[mo.source!='OBS'],ob])
nm={'TMM':'TMm','TXX':'TXx','TXN':'TXn','ID':'ID','SU':'SU','RX1DAY':'RX1day','RX5DAY':'RX5day','PRCPTOT':'PRCPTOT','R10MM':'R10mm','CDD':'CDD','SPI3':'SPI3','SPI6':'SPI6','SPEI3':'SPEI3','SPEI6':'SPEI6'}
def src(s): return 'OBS' if s=='Observed' else {'NorESM2-LM':'NorESM','BCC-CSM2-MR':'BCC','EC-Earth3-Veg':'EC'}[s.split(' (')[0]]
bad=[];n=0;pb=[];rows=[]
for _,r in W.iterrows():
    ix=nm[r.Index]; s=src(r.Source)
    q=mo[(mo.station==r.Station)&(mo.source==s)&(mo['index']==ix)&(mo.month==r.Month)].iloc[0]
    for col,mc in [('Historical','uq_H'),('Present','uq_P'),('Near','uq_N'),('Far','uq_F')]:
        if pd.isna(r[col]): continue
        n+=1
        if abs(r[col]-q[mc])>0.011: bad.append((r.Station,s,ix,r.Month,col,r[col],round(q[mc],3)))
    for col,mc,mu in [('Wilcoxon p H vs P (all monthly values)','pall_HP','p_HP'),('Wilcoxon p Near vs Far (all monthly values)','pall_NF','p_NF')]:
        if pd.isna(r[col]): continue
        if abs(r[col]-q[mc])>0.0015: pb.append((r.Station,s,ix,r.Month,col[11:16],r[col],round(q[mc],4)))
        rows.append(dict(station=r.Station,source=s,index=ix,month=r.Month,comp=col[11:16],p_wb=r[col],p_all=q[mc],p_subset=q[mu]))
print('monthly medians compared',n,'mismatch',len(bad))
from collections import Counter; print(Counter((b[1],b[2]) for b in bad))
print(bad[:12])
print('pvals (all-values) mismatch',len(pb), Counter((b[1],b[2]) for b in pb))
P=pd.DataFrame(rows); P.to_csv('out/monthly_p_compare.csv',index=False)
sig_wb=(P.p_wb<0.05); sig_sub=(P.p_subset<0.05)
print('significance flips subset vs all-values:',int((sig_wb!=sig_sub).sum()),'of',len(P))

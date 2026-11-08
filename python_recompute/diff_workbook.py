import sys,pickle,numpy as np,pandas as pd; sys.path.insert(0,'code'); from claims import FULL
W='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/4_Results/Thesis_6.13_results_new_data.xlsx'
F=pickle.load(open('out/facts_AUTHORS_v4.pkl','rb'))
x=pd.ExcelFile(W)
# p-values
pv=x.parse('P-values (Tables 3, A1, A2)')
mp=F['mp'].copy(); mp['P']=mp.period.map({'H':'Historical','P':'Present'})
n=0;bad=[]
for _,r in pv.iterrows():
    for full,m in FULL.items():
        mine=mp[(mp.station==r.Station)&(mp['index']==r.Index)&(mp.P==r.Period)&(mp.model==m)].p.iloc[0]
        th=r[full]; n+=1
        if (pd.isna(th)!=pd.isna(mine)) and not (pd.isna(th) and mine==1.0) or (not pd.isna(th) and not pd.isna(mine) and abs(round(mine,3)-th)>0.0015): bad.append((r.Station,r.Index,r.Period,m,th,mine))
print('pvalues compared',n,'mismatch',len(bad)); print(bad[:15])
# changes long
ch=x.parse('Changes long (Δ, p)'); pc=F['pc']
cm={'Hist→Present':'P','Hist→Near':'N','Hist→Far':'F'}
src=lambda s:'OBS' if s=='Observed' else ('ENS' if s=='Ensemble' else s)
mpc=pc.set_index(['station','index','comp','source'])
nb=[];
for _,r in ch.iterrows():
    k=(r.Station,r.Index,cm.get(r.Comparison,r.Comparison),src(r.Source))
    if k not in mpc.index: nb.append(('missing',k)); continue
    m=mpc.loc[k]
    dd=abs(m.delta-r['Δ median']) if not pd.isna(r['Δ median']) else 0
    pp=abs(m.p-r['Wilcoxon p']) if not(pd.isna(r['Wilcoxon p']) or pd.isna(m.p)) else (0 if pd.isna(m.p)==pd.isna(r['Wilcoxon p']) else 9)
    if dd>0.006 or pp>0.0006: nb.append((k,r['Δ median'],round(m.delta,3),r['Wilcoxon p'],m.p))
print('changes compared',len(ch),'mismatch',len(nb)); print(nb[:20])
print(ch.Comparison.unique())

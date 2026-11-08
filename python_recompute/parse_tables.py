import re, json, sys
sys.path.insert(0,'code'); from cdx import INDICES
UP={i.upper():i for i in INDICES}
def parse(path):
    L=open(path).read().split('\n')
    pv=[];ar=[]
    for i,l in enumerate(L):
        t=l.split()
        if len(t)<13 or t[0].upper() not in UP: continue
        name=UP[t[0].upper()]; rest=t[1:]
        if all(re.fullmatch(r'[0-9]\.[0-9]{3}|nan',x) for x in rest) and len(rest)==20: pv.append((i,name,rest))
        elif all(x in ('↑','↓','–','n/a') for x in rest) and len(rest) in (12,22): ar.append((i,name,rest))
    return pv,ar
for tag,f in [('613','/home/hatch/workspace/jeremy_wu_redteam/thesis/thesis_613_layout.txt'),('v7','/home/hatch/workspace/jeremy_wu_redteam/thesis/thesis_v7_layout.txt')]:
    pv,ar=parse(f)
    tabs={}
    if tag=='613':
        names=['T3_London','A1_Fergus','A2_Harrow']
        for k,n in enumerate(names): tabs[n]={r[1]:r[2] for r in pv[k*44:(k+1)*44]}
        a12=[a for a in ar if len(a[2])==12]; a22=[a for a in ar if len(a[2])==22]
        tabs['T4_London']={r[1]:r[2] for r in a12[:44]}; tabs['B1_Fergus']={r[1]:r[2] for r in a12 if 4490<r[0]<4600}; tabs['B2_Harrow']={r[1]:r[2] for r in a12 if 4600<r[0]<4700}
        tabs['T5_London']={r[1]:r[2] for r in a22 if r[0]<4700}; tabs['C1_Fergus']={r[1]:r[2] for r in a22 if 4700<r[0]<4808}; tabs['C2_Harrow']={r[1]:r[2] for r in a22 if r[0]>4808}
        print('arrows',len(a12),len(a22), [a[0] for a in a12[43:46]],[a[0] for a in a12[87:90]],[a[0] for a in a22[43:46]],[a[0] for a in a22[87:90]])
    else:
        for k,n in enumerate(['T4_London','A1_Fergus','A2_Harrow']): tabs[n]={r[1]:r[2] for r in pv[k*44:(k+1)*44]}
    for n,t in tabs.items(): print(tag,n,len(t))
    json.dump(tabs,open(f'out/tables_{tag}.json','w'),ensure_ascii=False)

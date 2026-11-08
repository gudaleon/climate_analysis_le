import sys,numpy as np,pandas as pd,hashlib,glob,os; sys.path.insert(0,'code'); from cdx import INDICES
A='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/3_Annual_index_tables/'
low={i.lower():i for i in INDICES}; low.update({'csdi':'CSDI6','wsdi':'WSDI6'})
for st in ['London','Fergus','Harrow']:
    t=pd.read_excel(A+f'All_{st}_observed_and_10_models_1950-2100.xlsx').replace(-99.9,np.nan); t['I']=[low[i.strip().lower()] for i in t.Index]
    for src in ['Observed','ACCESS','BCC','CanESM','CNRM','EC','GFDL','INM','MIROC','MRI','NorESM']:
        w=t.pivot(index='Year',columns='I',values=src)[INDICES]
        if src=='Observed': w=w.loc[:2023]
        w.to_csv(f'out/idx_auth/{st}_'+('OBS_AUTHTAB' if src=='Observed' else src)+'_annual.csv')
B='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data/2_Data/'
P='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/'
diff=0;n=0
for f in glob.glob(P+'**/*',recursive=True):
    if os.path.isfile(f) and '2_Models/c_Climpact' not in f:
        g=f.replace(P,B); n+=1
        if not os.path.exists(g): print('absent in v7 pkg',f[len(P):]); diff+=1; continue
        if f.endswith('xlsx'):
            xa=pd.ExcelFile(f); xb=pd.ExcelFile(g)
            if xa.sheet_names!=xb.sheet_names or any(not xa.parse(s).equals(xb.parse(s)) for s in xa.sheet_names): print('XLSX content differs',f[len(P):]); diff+=1
        elif hashlib.md5(open(f,'rb').read()).digest()!=hashlib.md5(open(g,'rb').read()).digest(): print('differs',f[len(P):]); diff+=1
print('shared data files compared',n,'differing/absent',diff)

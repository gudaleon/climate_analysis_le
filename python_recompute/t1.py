import sys,time; sys.path.insert(0,'code'); from cdx import *
P='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/'
t=time.time(); s=Series(read_daily(P+'2_Models/b_Daily_series/London_NorESM.txt')); print('init',time.time()-t)
a=s.annual(); print('ann',time.time()-t); print(a.loc[[1950,1951,1986,2050,2100]].T.to_string())

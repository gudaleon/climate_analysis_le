import sys,os; sys.path.insert(0,'code'); from cdx import *
P='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/1_Observations/c_Homogenised_daily_series/'
from multiprocessing import Pool
def run(st):
    s=Series(read_daily(P+f'{st.upper()}_homogenised_v4.txt'))
    s.annual().to_csv(f'out/idx/{st}_OBS_AUTHORS_v4_annual.csv'); s.monthly().to_csv(f'out/idx/{st}_OBS_AUTHORS_v4_monthly.csv'); return st
with Pool(3) as p: print(p.map(run,['London','Fergus','Harrow']))

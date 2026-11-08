from independent_pass1 import *
from audit_monthly_and_homog import cdd
old=pd.read_csv(OUT/'conditional_monthly_all_models.csv');old.to_csv(OUT/'conditional_monthly_before_CDD_NA_fix.csv',index=False);out=old[~old['index'].str.startswith('CDD_')].to_dict('records');cds=[];checks=[]
for sta in ['London','Fergus','Harrow']:
 for mo in ['Observed']+list(MODELS):
  d=read(next((P1/'2_Data/1_Observations/c_Homogenised_daily_series').glob(sta.upper()+'*'))) if mo=='Observed' else read(PC/'txt'/f'{"FERGUS_SENS" if sta=="Fergus" else sta.upper()}_{MODELS[mo]}.txt');cd=cdd(d);cd['station']=sta;cd['model']=mo;cds.append(cd)
  fn='OBS_'+sta.upper() if mo=='Observed' else mo+'_'+sta;p=P1/'2_Data/4_Monthly_analysis/monthly_CDD'/f'{fn}.csv'
  if p.exists():
   v=pd.read_csv(p).iloc[:,1].to_numpy();x=cd.CDD_ending_recycled.to_numpy();checks.append(dict(station=sta,model=mo,different_cells=int(sum(~np.isclose(x,v,rtol=0,atol=0,equal_nan=True)))))
  for idx in ['CDD_ending_recycled','CDD_ending_proper','CDD_within_month']:
   for month in [1,2,3,6,7,8,9]:
    g=cd[cd.month==month];vv={p:g.loc[g.year.between(*yr),idx].dropna().to_numpy() for p,yr in PER.items()};tails={p:v[v>=np.quantile(v,.75)] if len(v) else np.array([]) for p,v in vv.items()}
    for p,q in [('Historical','Present')]+([] if mo=='Observed' else [('Near','Far')]):
     aa,bb=tails[p],tails[q];x=np.median(aa) if len(aa) else np.nan;y=np.median(bb) if len(bb) else np.nan;out.append(dict(station=sta,model=mo,index=idx,month=month,comparison=p+'->'+q,old=x,new=y,delta=y-x,pct=100*(y-x)/x if x else np.nan,p_full=test(vv[p],vv[q]),p_tail=test(aa,bb),n_old=len(vv[p]),n_new=len(vv[q]),tail_n_old=len(aa),tail_n_new=len(bb)))
pd.DataFrame(out).to_csv(OUT/'conditional_monthly_all_models.csv',index=False);pd.concat(cds,ignore_index=True).to_csv(OUT/'monthly_CDD_all_branches.csv',index=False);pd.DataFrame(checks).to_csv(OUT/'monthly_CDD_port_input_check.csv',index=False);print(checks)

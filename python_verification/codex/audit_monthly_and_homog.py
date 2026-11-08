from independent_pass1 import *
from io import StringIO
IDX={'TMM':'tmm','TXX':'txx','TXN':'txn','ID':'id','PRCPTOT':'prcptot','R10MM':'r10mm','RX1DAY':'rx1day','RX5DAY':'rx5day','SU':'su','SPEI3':'3month_spei','SPEI6':'6month_spei','SPI3':'3month_spi','SPI6':'6month_spi'}
def climate(p):
 text=p.read_text();lines=text.splitlines();h=next(i for i,l in enumerate(lines) if l.startswith('time'));d=pd.read_csv(StringIO('\n'.join(lines[h:])),skipinitialspace=True);d.columns=d.columns.str.strip();return d.replace(-99.9,np.nan)
def cdd(d):
 pr=d.pr.to_numpy();ym=(d.year*100+d.month).to_numpy();years=d.year.to_numpy();un,im=np.unique(ym,return_inverse=True);uy,iy=np.unique(years,return_inverse=True);end=np.zeros(len(pr));s,t=runs(pr<1);end[t-1]=t-s;v=[];monmiss=[]
 for j in range(len(un)):
  sel=im==j;mx=max(end[sel]);all_dry=not np.any(pr[sel]>=1);v.append(np.nan if mx==0 and all_dry else mx);monmiss.append(sum(np.isnan(pr[sel]))>3)
 valid=np.array([not ((np.isnan(pr[years==year]).sum()>15) or any(np.array(monmiss)[un//100==year])) for year in uy]);proper=np.array([1. if valid[np.flatnonzero(uy==year)[0]] else np.nan for year in un//100]);bug=np.resize(np.where(valid,1.,np.nan),len(un));return pd.DataFrame({'year':un//100,'month':un%100,'CDD_ending_recycled':np.array(v)*bug,'CDD_ending_proper':np.array(v)*proper,'CDD_within_month':[longest(pr[im==j]<1) if proper[j]==1 else np.nan for j in range(len(un))]})
if __name__=='__main__':
 qc=[];effects=[];homann=[];cdddiff=[];monthstats=[];inputdiff=[]
 for sta in ['London','Fergus','Harrow']:
  merged=read(next((P1/'2_Data/1_Observations/b_Merged_daily_series').glob(sta.upper()+'*')));adj=read(next((P1/'2_Data/1_Observations/c_Homogenised_daily_series').glob(sta.upper()+'*')))
  for label,d in [('merged',merged),('supplied_homogenised',adj)]:qc.append(integrity(d,sta+'_'+label,'proleptic_gregorian'))
  for v in ['pr','tx','tn']:
   equal=np.isclose(merged[v],adj[v],equal_nan=True);delta=adj[v]-merged[v];effects.append(dict(station=sta,variable=v,changed_days=int(sum(~equal)),missingness_changes=int(sum(merged[v].isna()!=adj[v].isna())),mean_adjustment=delta.mean(),max_abs_adjustment=delta.abs().max(),min_adjustment=delta.min(),max_adjustment=delta.max()))
  h=indices(adj);h['station']=sta;homann.append(h)
  for mo in ['Observed']+list(MODELS):
   if mo=='Observed':d=adj;run=sta.upper()+'_v4';folder=P1/'2_Data/1_Observations/d_Climpact_indices'/run
   else:d=read(PC/'txt'/f'{"FERGUS_SENS" if sta=="Fergus" else sta.upper()}_{MODELS[mo]}.txt');run=sta+'_'+mo;folder=P1/'2_Data/2_Models/c_Climpact_indices'/run
   cd=cdd(d);cd['station']=sta;cd['model']=mo;cdddiff.append(cd)
   vals=[]
   for idx,suffix in IDX.items():
    x=climate(folder/f'{run}_{suffix}_MON.csv');tm=x.iloc[:,0].astype(str).str.strip();r=pd.DataFrame({'year':tm.str[:4].astype(int),'month':tm.str[5:7].astype(int),'index':idx,'value':pd.to_numeric(x.iloc[:,1],errors='coerce')});vals.append(r)
   for branch in ['CDD_ending_recycled','CDD_ending_proper','CDD_within_month']:
    r=cd[['year','month',branch]].rename(columns={branch:'value'});r['index']=branch;vals.append(r)
   z=pd.concat(vals,ignore_index=True)
   for (idx,month),g in z[z.month.isin([1,2,3,6,7,8,9])].groupby(['index','month']):
    vv={p:g[g.year.between(*yr)].value.dropna().to_numpy() for p,yr in PER.items()};tails={}
    for p,arr in vv.items():
     if len(arr):q=np.quantile(arr,.25 if idx=='TXN' else .75);tails[p]=arr[arr<=q] if idx=='TXN' else arr[arr>=q]
     else:tails[p]=np.array([])
    for old,new in [('Historical','Present')]+([] if mo=='Observed' else [('Near','Far')]):
     aa,bb=tails[old],tails[new];x=np.median(aa) if len(aa) else np.nan;y=np.median(bb) if len(bb) else np.nan;monthstats.append(dict(station=sta,model=mo,index=idx,month=int(month),comparison=old+'->'+new,old=x,new=y,delta=y-x,pct=100*(y-x)/x if x else np.nan,p_full=test(vv[old],vv[new]),p_tail=test(aa,bb),n_old=len(vv[old]),n_new=len(vv[new]),tail_n_old=len(aa),tail_n_new=len(bb)))
  for branchroot,tag in [(P1,'613'),(P2,'v7')]:
   p=branchroot/'2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx';wb=pd.read_excel(p);wb.to_csv(OUT/f'supplied_monthly_summary_{tag}.csv',index=False)
 pd.DataFrame(qc).to_csv(OUT/'observation_integrity_pass2.csv',index=False);pd.DataFrame(effects).to_csv(OUT/'supplied_homogenisation_daily_effect.csv',index=False);pd.concat(homann,ignore_index=True).to_csv(OUT/'conditional_independent_indices_supplied_homogenised.csv',index=False);pd.concat(cdddiff,ignore_index=True).to_csv(OUT/'monthly_CDD_all_branches.csv',index=False);pd.DataFrame(monthstats).to_csv(OUT/'conditional_monthly_all_models.csv',index=False)
 print('monthly cases',len(monthstats));print(pd.DataFrame(effects).to_string(index=False))

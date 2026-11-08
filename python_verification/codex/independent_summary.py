from independent_pass1 import *
a=pd.read_csv(OUT/'annual_primary_selected_cells.csv');pct=pd.read_csv(OUT/'percentile_primary_selected_cells.csv');pct['month']=0;a=pd.concat([a,pct],ignore_index=True);rows=[]
for branch,models in [('raw',list(MODELS)),('remove_inverted_pairs',[x+'_clean' for x in MODELS])]:
 for (sta,idx),g in a[a.model.isin(models)].groupby(['station','index']):
  for rounding in ['native',1,2]:
   stats=[]
   for per,yr in PER.items():
    arr=g[g.year.between(*yr)].value.dropna().to_numpy();arr=arr if rounding=='native' else np.round(arr,rounding)
    q1,med,q3=np.quantile(arr,[.25,.5,.75]);n=int(sum((arr<q1-1.5*(q3-q1))|(arr>q3+1.5*(q3-q1))));stats.append((per,med,q1,q3,n,len(arr)))
   old,new=stats[0],stats[3];s0=old[3]-old[2];s1=new[3]-new[2];ratio=s1/s0 if s0 else (np.inf if s1 else 1.);shift=('Increase' if new[1]>old[1] else ('Decrease' if new[1]<old[1] else 'No Shift'))+' ('+('Spread Expanded' if ratio>1.25 else ('Spread Contracted' if ratio<.75 else 'Stable Spread'))+')'
   for per,med,q1,q3,n,ns in stats:rows.append(dict(branch=branch,rounding=rounding,station=sta,index=idx,period=per,median=med,q1=q1,q3=q3,outliers=n,n=ns,overall_shift=shift,iqr_ratio=ratio))
pd.DataFrame(rows).to_csv(OUT/'pooled_summary_independent.csv',index=False);print('summary rows',len(rows))

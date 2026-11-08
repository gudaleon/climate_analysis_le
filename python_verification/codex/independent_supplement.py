from independent_pass1 import *
a=pd.read_csv(OUT/'annual_pass1.csv');p=pd.read_csv(OUT/'projections_pass1.csv');c=pd.read_csv(OUT/'model_changes_pass1.csv');m=pd.read_csv(OUT/'monthly_pass1.csv');b=pd.read_csv(OUT/'unadjusted_branches_pass1.csv');b['opposite_median_anywhere']=b.observed_delta*b.model_median<0;b['reversal613']=(~b.bounded)&b.opposite_median_anywhere;b.to_csv(OUT/'unadjusted_branches_corrected_pass1.csv',index=False);rng=np.random.default_rng(20261107)
# Equal-composition null: shuffle observed changes only among stations within the same index; units preserved.
vals=[]
null_groups=[(g.observed_delta.to_numpy(),g.model_min.to_numpy(),g.model_max.to_numpy()) for _,g in b.groupby('index')]
for i in range(10000):
 n=0
 for orig,lo,hi in null_groups:
  obs=rng.permutation(orig);n+=int(sum((obs>=lo)&(obs<=hi)))
 vals.append(n)
null={'cases':len(b),'observed_unadjusted_bounded':int(b.bounded.sum()),'permutations':len(vals),'null_mean':float(np.mean(vals)),'null_95_percent_interval':np.quantile(vals,[.025,.975]).tolist(),'p_upper':float((1+sum(np.array(vals)>=b.bounded.sum()))/(1+len(vals))),'exchangeable_order_statistic_expected_rate_ten_models':9/11,'printed_rate':115/132,'printed_excess_over_exchangeable_null_cases':115-132*9/11,'warning':'Station-only null has just three exchangeable stations per index and is conditional on the unadjusted observation branch. Analytical 9/11 assumes eleven iid continuous changes; correlated heterogeneous CMIP6 changes need not satisfy it.'}
(OUT/'envelope_null_pass1.json').write_text(json.dumps(null,indent=2))
loo=[]
for omitted in MODELS:
 for (sta,idx,period),g in c[c.model!=omitted].groupby(['station','index','period']):
  obs=b[(b.station==sta)&(b['index']==idx)].iloc[0].observed_delta;sigup=int(sum(g.significant&(g.delta>0)));sigdn=int(sum(g.significant&(g.delta<0)));loo.append(dict(omitted=omitted,station=sta,index=idx,period=period,bounded=bool(g.delta.min()<=obs<=g.delta.max()) if period=='Present' else None,consensus=bool(max(sigup,sigdn)>=8),median_delta=g.delta.median()))
pd.DataFrame(loo).to_csv(OUT/'leave_one_out_pass1.csv',index=False)
monthly=[]
for (sta,model,idx,month),g in m[m.model.isin(MODELS)].groupby(['station','model','index','month']):
 if idx not in ['TMm','TXx','TXn','ID','SU','RX1day','RX5day','PRCPTOT','R10mm','CDD'] or month not in [1,2,3,6,7,8,9]:continue
 tails={}
 for per,ys in PER.items():
  arr=g[g.year.between(*ys)].value.dropna().to_numpy();q=np.quantile(arr,.25 if idx=='TXn' else .75);tails[per]=arr[arr<=q] if idx=='TXn' else arr[arr>=q]
 for old,new in [('Historical','Present'),('Near','Far')]:
  aa,bb=tails[old],tails[new];x,y=np.median(aa),np.median(bb);monthly.append(dict(station=sta,model=model,index=idx,month=month,comparison=old+'->'+new,old=x,new=y,delta=y-x,pct=100*(y-x)/x if x else np.nan,p=test(aa,bb),n_old=len(aa),n_new=len(bb)))
pd.DataFrame(monthly).to_csv(OUT/'monthly_reference_sensitivity_pass1.csv',index=False)
# Integrity propagation: clean sets both temperatures missing on inverted-temperature days; no corrected values are invented.
raw=a[a.model.isin(MODELS)].copy();clean=a[a.model.str.endswith('_clean')].copy();clean.model=clean.model.str.replace('_clean','');j=raw.merge(clean,on=['station','model','year','month','index'],suffixes=('_raw','_clean'));j['difference']=j.value_clean-j.value_raw;j=j[(~np.isclose(j.value_raw,j.value_clean,equal_nan=True))];j.to_csv(OUT/'temperature_cleaning_annual_effects_pass1.csv',index=False)
print(json.dumps(null,indent=2));print('changed annual values',len(j))

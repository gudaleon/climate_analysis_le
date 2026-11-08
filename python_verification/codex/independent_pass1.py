from pathlib import Path
import numpy as np, pandas as pd, scipy, scipy.stats as st, json, hashlib, platform, sys, datetime, calendar
ROOT=Path('/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026')
P1=ROOT/'Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data'
P2=ROOT/'Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data'
PC=Path('/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final')
OUT=Path('evidence');OUT.mkdir(exist_ok=True)
PER={'Historical':(1950,1986),'Present':(1987,2023),'Near':(2024,2062),'Far':(2063,2100)}
MODELS={'ACCESS':'ACCESS-ESM1-5','BCC':'BCC-CSM2-MR','CanESM':'CanESM5','CNRM':'CNRM-ESM2-1','EC':'EC-Earth3-Veg','GFDL':'GFDL-ESM4','INM':'INM-CM5-0','MIROC':'MIROC-ES2L','MRI':'MRI-ESM2-0','NorESM':'NorESM2-LM'}
COL=['year','month','day','pr','tx','tn']
def read(p):
 d=pd.read_csv(p,sep=r'\s+',header=None,names=COL); d[['pr','tx','tn']]=d[['pr','tx','tn']].replace(-99.9,np.nan);return d

def runs(mask):
 m=np.asarray(mask,bool); e=np.r_[False,m,False].astype(int);s=np.flatnonzero(np.diff(e)==1);t=np.flatnonzero(np.diff(e)==-1);return s,t

def longest(mask):
 s,t=runs(mask);return int(max(t-s,default=0))

def countspell(mask,n):
 s,t=runs(mask);return int(sum((t-s)[t-s>=n]))

def test(x,y,cc=True,exact=False):
 x=np.asarray(x,float);y=np.asarray(y,float);x=x[np.isfinite(x)];y=y[np.isfinite(y)]
 if not len(x) or not len(y) or np.ptp(np.r_[x,y])==0:return np.nan
 return st.mannwhitneyu(x,y,alternative='two-sided',method='exact' if exact else 'asymptotic',use_continuity=cc).pvalue

def indices(d,monthly=False,clean=False):
 d=d.copy()
 if clean:d.loc[d.tx<d.tn,['tx','tn']]=np.nan
 rows=[]
 # Fixed wet-day percentile thresholds, sample quantiles type 8. Temperature percentile/spell indices are excluded here: bootstrap not independently implemented.
 base=d[d.year.between(1950,1986)];wet=base.loc[base.pr>=1,'pr'];q95,q99=np.quantile(wet,[.95,.99],method='median_unbiased')
 for key,g in d.groupby(['year','month'] if monthly else ['year'],sort=True):
  year,month=(key if monthly else (key[0],0));pr=g.pr.to_numpy();tx=g.tx.to_numpy();tn=g.tn.to_numpy();tm=(tx+tn)/2;dt=tx-tn
  n=len(g);wet=pr>=1;tot=np.nansum(pr[wet]);wc=wet.sum()
  v={'PRCPTOT':tot,'R10mm':sum(pr>=10),'R20mm':sum(pr>=20),'RX1day':np.nanmax(pr),'SDII':tot/wc if wc else np.nan,'CDD':longest(pr<1),'CWD':longest(wet),'R95p':np.nansum(pr[pr>q95]),'R99p':np.nansum(pr[pr>q99]),'FD':sum(tn<0),'ID':sum(tx<0),'SU':sum(tx>25),'TR':sum(tn>20),'TNn':np.nanmin(tn),'TNx':np.nanmax(tn),'TXx':np.nanmax(tx),'TXn':np.nanmin(tx),'TXm':np.nanmean(tx),'TNm':np.nanmean(tn),'TMm':np.nanmean(tm),'DTR':np.nanmean(dt),'DTRgt15':sum(dt>15),'TXge30':sum(tx>=30),'TNltm20':sum(tn< -20),'GDDgrow10':np.nansum(np.maximum(tm-10,0))}
  for nn in [3,5]:v[f'RX{nn}day']=pd.Series(pr).rolling(nn,min_periods=nn).sum().max()
  for nn in [95,99]:v[f'R{nn}pTOT']=100*v[f'R{nn}p']/tot if tot else np.nan
  if not monthly:
   a,b=runs(tm>5);starts=a[(b-a)>=6];a,b=runs((tm<5)&(g.month.to_numpy()>=7));ends=a[(b-a)>=6]
   v['GSL']=int(ends[0]-starts[0]) if len(starts) and len(ends) and ends[0]>starts[0] else (n-int(starts[0]) if len(starts) and not len(ends) else 0)
  # Standard annual missingness >15 invalidates dependent variables; monthly >3. No inferred infilling.
  limit=3 if monthly else 15
  badpr=int(np.isnan(pr).sum());badtx=int(np.isnan(tx).sum());badtn=int(np.isnan(tn).sum());badpair=int((~np.isfinite(tx)|~np.isfinite(tn)).sum())
  for idx in v:
   bad=(badpr if idx in ['PRCPTOT','R10mm','R20mm','RX1day','RX3day','RX5day','SDII','CDD','CWD','R95p','R99p','R95pTOT','R99pTOT'] else (badtn if idx in ['FD','TR','TNn','TNx','TNltm20','TNm'] else (badtx if idx in ['ID','SU','TXx','TXn','TXm','TXge30'] else badpair)))
   if bad>limit:v[idx]=np.nan
  rows.extend(dict(year=int(year),month=int(month),index=k,value=float(val)) for k,val in v.items())
 return pd.DataFrame(rows)

def integrity(d,label,cal):
 dates=d[COL[:3]].astype(int);dup=int(dates.duplicated().sum());exp=sum(365 if cal in ['365_day','noleap'] else (366 if calendar.isleap(y) else 365) for y in range(int(d.year.min()),int(d.year.max())+1));return dict(series=label,calendar=cal,rows=len(d),expected=exp,duplicate_dates=dup,missing_dates=exp-len(dates.drop_duplicates()),feb29=int(((d.month==2)&(d.day==29)).sum()),tn_gt_tx=int((d.tn>d.tx).sum()),negative_pr=int((d.pr<0).sum()),missing_pr=int(d.pr.isna().sum()),missing_tx=int(d.tx.isna().sum()),missing_tn=int(d.tn.isna().sum()),min_tn=d.tn.min(),max_tx=d.tx.max())

def eccc(p):
 d=pd.read_csv(p,low_memory=False);out=pd.DataFrame({'year':d.LOCAL_YEAR,'month':d.LOCAL_MONTH,'day':d.LOCAL_DAY,'pr':d.TOTAL_PRECIPITATION,'tx':d.MAX_TEMPERATURE,'tn':d.MIN_TEMPERATURE});return out.set_index(COL[:3])

def rebuild():
 src=P1/'2_Data/1_Observations/a_ECCC_station_sources';dates=pd.date_range('1950-01-01','2023-12-31');ind=pd.MultiIndex.from_arrays([dates.year,dates.month,dates.day],names=COL[:3]);out={}
 for station in ['London','Fergus','Harrow']:
  if station=='Fergus':
   d=read(next(src.glob('Fergus*station_file.txt'))).set_index(COL[:3]).reindex(ind);extra=eccc(next(src.glob('Fergus*2012.csv')));d.loc[(2012,9,29),'pr']=extra.loc[(2012,9,29),'pr']
  elif station=='London':
   a=read(next(src.glob('London*station_file.txt'))).drop_duplicates(COL[:3],keep='first').set_index(COL[:3]).reindex(ind);b=eccc(next(src.glob('London_6144478*.csv'))).reindex(ind);mask=dates>=pd.Timestamp('2002-09-19');d=a.copy();d.loc[mask]=b.loc[mask].combine_first(a.loc[mask])
  else:
   a=pd.concat([eccc(p) for p in sorted(src.glob('Harrow_6133360*.csv'))]);a=a[~a.index.duplicated(keep='last')].reindex(ind);b=eccc(next(src.glob('Harrow_613CC60*.csv'))).reindex(ind);c=eccc(next(src.glob('Harrow_6133362*.csv'))).reindex(ind);d=a.copy();mb=(dates>='1992-01-01')&(dates<'2000-09-01');mc=dates>='2000-09-01';d.loc[mb]=b.loc[mb];d.loc[mc]=c.loc[mc];ma=(dates>='1992-04-01')&(dates<'1992-05-01');d.loc[ma]=a.loc[ma]
  out[station]=d.reset_index()
 return out

def main():
 meta=pd.read_csv(PC/'metadata.csv');checks=[]
 for r in meta.to_dict('records'):
  p=PC/'raw_nc'/r['raw_nc_file'];h=hashlib.sha256(p.read_bytes()).hexdigest();checks.append({'file':str(p),'computed':h,'printed':r['sha256'],'equal':h==r['sha256']})
 pd.DataFrame(checks).to_csv(OUT/'pcic_hashes.csv',index=False)
 rebuilt=rebuild();annual=[];month=[];qc=[];prov=[];merge=[]
 for station,d in rebuilt.items():
  p=next((P1/'2_Data/1_Observations/b_Merged_daily_series').glob(station.upper()+'*'));a=read(p);j=d.merge(a,on=COL[:3],suffixes=('_own','_pack'),how='outer')
  for col in ['pr','tx','tn']:
   equal=np.isclose(j[col+'_own'],j[col+'_pack'],equal_nan=True);merge.append({'station':station,'variable':col,'different_days':int((~equal).sum()),'max_difference':float(np.nanmax(np.abs(j[col+'_own']-j[col+'_pack']))),'example_dates':j.loc[~equal,COL[:3]].head(10).to_dict('records')})
  d.to_csv(OUT/f'merged_own_{station}.csv',index=False)
  for label,df in [('own_merged',d),('supplied_merged',a)]:
   qc.append(integrity(df,station+'_'+label,'proleptic_gregorian'))
   an=indices(df);an['station']=station;an['model']=label;annual.append(an);mo=indices(df,True);mo['station']=station;mo['model']=label;month.append(mo)
 for station in ['London','Fergus','Harrow']:
  for short,model in MODELS.items():
   d=read(PC/'txt'/f'{station.upper()}_{model}.txt');cal=meta[(meta.station==station.upper())&(meta.model==model)].iloc[0]['calendar'];qc.append(integrity(d,station+'_'+short,cal))
   for pk,root in [('613',P1),('v7',P2)]:
    a=read(root/'2_Data/2_Models/b_Daily_series'/f'{station}_{short}.txt');same=d.shape==a.shape and np.allclose(d.to_numpy(),a.to_numpy(),equal_nan=True);prov.append({'station':station,'model':short,'target':pk,'equal_pcic':bool(same),'different_cells':int((~np.isclose(d.to_numpy(),a.to_numpy(),equal_nan=True)).sum()) if d.shape==a.shape else None})
   for label,clean in [(short,False),(short+'_clean',True)]:
    an=indices(d,clean=clean);an['station']=station;an['model']=label;annual.append(an)
   mo=indices(d,True);mo['station']=station;mo['model']=short;month.append(mo)
 pd.DataFrame(qc).to_csv(OUT/'daily_integrity_pass1.csv',index=False);pd.DataFrame(prov).to_csv(OUT/'pcic_daily_comparison.csv',index=False);pd.DataFrame(merge).to_json(OUT/'source_merge_comparison.json',orient='records',indent=2)
 ann=pd.concat(annual,ignore_index=True);ann.to_csv(OUT/'annual_pass1.csv',index=False);mon=pd.concat(month,ignore_index=True);mon.to_csv(OUT/'monthly_pass1.csv',index=False)
 projections=[];changes=[]
 for (station,idx),g in ann[ann.model.isin(MODELS)].groupby(['station','index']):
  mods=[]
  for model,h in g.groupby('model'):
   vals={k:h[h.year.between(*yr)].value.dropna().to_numpy() for k,yr in PER.items()};med={k:np.median(v) if len(v) else np.nan for k,v in vals.items()}
   for period in ['Present','Near','Far']:
    delta=med[period]-med['Historical'];p=test(vals['Historical'],vals[period]);changes.append(dict(station=station,index=idx,model=model,period=period,delta=delta,p=p,direction=int(np.sign(delta)) if np.isfinite(delta) else 0,significant=bool(p<.05)))
  for period in ['Present','Near','Far']:
   sub=[r for r in changes if r['station']==station and r['index']==idx and r['period']==period];ds=np.array([r['delta'] for r in sub]);sigs=np.array([r['significant'] for r in sub]);dirs=np.sign(ds)
   old=g[g.year.between(*PER['Historical'])].value.dropna();new=g[g.year.between(*PER[period])].value.dropna();pdlt=new.median()-old.median();projections.append(dict(station=station,index=idx,period=period,median_model_delta=np.median(ds),min_delta=min(ds),max_delta=max(ds),pooled_delta=pdlt,pooled_p=test(old,new),significant_up=int(sum(sigs&(dirs>0))),significant_down=int(sum(sigs&(dirs<0))),consensus=bool(max(sum(sigs&(dirs>0)),sum(sigs&(dirs<0)))>=8)))
 pd.DataFrame(changes).to_csv(OUT/'model_changes_pass1.csv',index=False);pd.DataFrame(projections).to_csv(OUT/'projections_pass1.csv',index=False)
 # Both post hoc branches from unadjusted observations. These are sensitivities, not the thesis's adjusted-observation main analysis.
 branches=[]
 for (station,idx),g in ann[ann.model=='supplied_merged'].groupby(['station','index']):
  a=g[g.year.between(*PER['Historical'])].value.dropna();b=g[g.year.between(*PER['Present'])].value.dropna();delta=b.median()-a.median();pr=next(r for r in projections if r['station']==station and r['index']==idx and r['period']=='Present');lo,hi,mid=pr['min_delta'],pr['max_delta'],pr['median_model_delta'];bounded=lo<=delta<=hi;revall=delta*lo<0 and delta*hi<0;branches.append(dict(station=station,index=idx,observed_delta=delta,p=test(a,b),model_min=lo,model_max=hi,model_median=mid,bounded=bool(bounded),reversal613=bool((not bounded) and delta*mid<0),reversalv7=bool(revall),classv7='Bounded' if bounded else ('Sign reversal' if revall else 'Unbounded'),arrow='↑' if delta>0 else ('↓' if delta<0 else '–')))
 pd.DataFrame(branches).to_csv(OUT/'unadjusted_branches_pass1.csv',index=False)
 env={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'periods':PER,'annual_indices':sorted(ann['index'].unique()),'limitations':['Independent RHtests detection/pruning/quantile adjustment not implemented.','Temperature percentile bootstrap, compound threshold index, EHF/ECF and SPI/SPEI not implemented.','Unadjusted-observation branches are sensitivity calculations only.','RXn and CDD/CWD runs confined to aggregation boundary; cross-year definitions need Pass 2 audit.','GDDgrow10 uses entire aggregation year: growing window is not specified by printed table.'],'seal':'Pass 1 restricted computation concluded; not a complete Pass 1. Authors numbered scripts, workbooks and Climpact outputs not opened by this program or executor before this seal.'}
 (OUT/'pass1_execution.json').write_text(json.dumps(env,indent=2));print(json.dumps(env,indent=2))
if __name__=='__main__':main()

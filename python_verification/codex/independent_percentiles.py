from independent_pass1 import *
# Fixed calendar-day +/-2-day type-8 thresholds. No Zhang in-base bootstrap: sensitivity only.
def calculate(d):
 md=(d.month*100+d.day).to_numpy();ref=pd.date_range('2001-01-01','2001-12-31');lookup={x.month*100+x.day:i for i,x in enumerate(ref)};lookup[229]=58;day=np.array([lookup[x] for x in md]);base=d.year.between(1950,1986).to_numpy();tx=d.tx.to_numpy();tn=d.tn.to_numpy();thresholds={}
 for var,arr,ps in [('tx',tx,[.1,.5,.9]),('tn',tn,[.1,.9])]:
  for p in ps:
   q=np.array([np.nanquantile(arr[base&(np.minimum(abs(day-j),365-abs(day-j))<=2)],p,method='median_unbiased') for j in range(365)]);thresholds[(var,p)]=q[day]
 masks={'TN10p':tn<thresholds['tn',.1],'TN90p':tn>thresholds['tn',.9],'TX10p':tx<thresholds['tx',.1],'TX90p':tx>thresholds['tx',.9],'TXgt50p':tx>thresholds['tx',.5]};rows=[]
 for year,g in d.groupby('year'):
  wh=(d.year==year).to_numpy()
  for idx,m in masks.items():
   var=tn if idx.startswith('TN') else tx;valid=np.isfinite(var[wh]);val=100*sum(m[wh])/sum(valid) if sum(valid) else np.nan
   if sum(~valid)>15:val=np.nan
   rows.append(dict(year=int(year),index=idx,value=val))
  for idx,key,n in [('CSDI6','TN10p',6),('CSDI3','TN10p',3),('WSDI6','TX90p',6),('WSDI3','TX90p',3)]:rows.append(dict(year=int(year),index=idx,value=countspell(masks[key][wh],n)))
 return pd.DataFrame(rows)
if __name__=='__main__':
 rows=[]
 for station in ['London','Fergus','Harrow']:
  for short,model in MODELS.items():
   d=read(PC/'txt'/f'{station.upper()}_{model}.txt');r=calculate(d);r['station']=station;r['model']=short;rows.append(r)
 a=pd.concat(rows,ignore_index=True);a.to_csv(OUT/'percentile_sensitivity_pass1.csv',index=False);print('rows',len(a))

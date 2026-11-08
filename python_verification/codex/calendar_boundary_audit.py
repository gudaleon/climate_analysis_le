from independent_pass1 import *
a=pd.read_csv(OUT/'conditional_author_annual_long.csv',dtype={'target':str},low_memory=False);a=a[a.target=='613'];look={k:g.set_index('year').value for k,g in a.groupby(['station','model','index'])};rows=[];gslrows=[]
for sta in ['London','Fergus','Harrow']:
 for mo,name in MODELS.items():
  d=read(PC/'txt'/f'{"FERGUS_SENS" if sta=="Fergus" else sta.upper()}_{name}.txt');pr=d.pr.to_numpy();tx=d.tx.to_numpy();tn=d.tn.to_numpy();tm=(tx+tn)/2;yy=d.year.to_numpy();months=d.month.to_numpy();dates=pd.to_datetime(d[['year','month','day']]);dayofyear=dates.dt.dayofyear.to_numpy()
  for n in [3,5]:
   for label,center in [('right_aligned',False),('centered',True)]:
    roll=pd.Series(pr).rolling(n,min_periods=n,center=center).sum();v=roll.groupby(yy).max();ref=look[sta,mo,f'RX{n}day'].reindex(v.index);diff=v-ref
    for year,x,z in zip(v.index,v,ref):rows.append(dict(station=sta,model=mo,index=f'RX{n}day',branch=label,year=int(year),computed=x,provided=z,difference=x-z))
  for idx,mask in [('CDD',pr<1),('CWD',pr>=1)]:
   s,t=runs(mask);end=np.zeros(len(mask));end[t-1]=t-s;v=pd.Series(end).groupby(yy).max();ref=look[sta,mo,idx].reindex(v.index)
   for year,x,z in zip(v.index,v,ref):rows.append(dict(station=sta,model=mo,index=idx,branch='entire_spell_assigned_end_year',year=int(year),computed=x,provided=z,difference=x-z))
  for year,h in d.groupby('year'):
   wh=np.flatnonzero(yy==year);s,t=runs(tm[wh]>5);starts=s[t-s>=6];s,t=runs((tm[wh]<5)&(months[wh]>=7));ends=s[t-s>=6]
   if not len(starts):continue
   start=int(starts[0]);end=int(ends[0]) if len(ends) else len(wh);native=end-start;greg=(int(dayofyear[wh[end]]) if end<len(wh) else (366 if calendar.isleap(year) else 365)+1)-int(dayofyear[wh[start]]);ref=look[sta,mo,'GSL'].loc[year];gslrows.append(dict(station=sta,model=mo,year=int(year),native_days=native,gregorian_date_difference=greg,provided=ref,native_difference=native-ref,gregorian_difference=greg-ref))
pd.DataFrame(rows).to_csv(OUT/'boundary_geometry_sensitivity.csv',index=False);pd.DataFrame(gslrows).to_csv(OUT/'GSL_calendar_geometry.csv',index=False)
x=pd.DataFrame(rows);print(x.groupby(['index','branch']).difference.agg(lambda v:sum(abs(v)>1e-9)));g=pd.DataFrame(gslrows);print('GSL native differing',sum(abs(g.native_difference)>1e-9),'Gregorian differing',sum(abs(g.gregorian_difference)>1e-9))

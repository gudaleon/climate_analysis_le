from independent_pass1 import *
rows=[]
for sta in ['London','Fergus','Harrow']:
 for sh,mo in MODELS.items():
  d=read(PC/'txt'/f'{sta.upper()}_{mo}.txt')
  if not ((d.month==2)&(d.day==29)).any():continue
  for branch in ['own_calendar','leap_days_removed']:
   h=d if branch=='own_calendar' else d[~((d.month==2)&(d.day==29))];v=pd.DataFrame({'year':h.year,'TMm':(h.tx+h.tn)/2,'DTR':h.tx-h.tn,'FD':(h.tn<0).astype(float),'ID':(h.tx<0).astype(float),'DTRgt15':((h.tx-h.tn)>15).astype(float)})
   out=v.groupby('year').agg({'TMm':'mean','DTR':'mean','FD':'sum','ID':'sum','DTRgt15':'sum'}).reset_index().melt(id_vars='year',var_name='index',value_name='value');out['station']=sta;out['model']=sh;out['branch']=branch;rows.append(out)
pd.concat(rows,ignore_index=True).to_csv(OUT/'calendar_sensitivity_pass1.csv',index=False);print('done')

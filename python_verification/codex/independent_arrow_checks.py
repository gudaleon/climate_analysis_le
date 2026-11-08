from independent_pass1 import *
a=pd.read_csv(OUT/'annual_primary_selected_cells.csv');pct=pd.read_csv(OUT/'percentile_primary_selected_cells.csv');pct['month']=0;a=pd.concat([a,pct],ignore_index=True)
tab=pd.read_csv(OUT/'thesis_tables_613.csv').fillna('');rows=[];cache={}
all_indices=set(a['index'])|{'CWA','CWF','HWA','HWF','TXb3TNb3'};pct_indices=set(pct['index']);canonical={x.upper():x for x in all_indices}
groups={k:g for k,g in a.groupby(['station','index','model'])}
pools={k:g for k,g in a[a.model.isin(MODELS)].groupby(['station','index'])}
def result(sta,source,idx,period):
 key=(sta,source,idx,period)
 if key in cache:return cache[key]
 g=pools.get((sta,idx),pd.DataFrame(columns=a.columns)) if source=='Ensemble' else groups.get((sta,idx,'supplied_merged' if source=='Observed' else source),pd.DataFrame(columns=a.columns))
 old=g[g.year.between(*PER['Historical'])].value.dropna();new=g[g.year.between(*PER[period])].value.dropna()
 if not len(old) or not len(new):r=None
 else:
  delta=float(new.median()-old.median());p=test(old,new);r={'delta':delta,'p':p,'arrow':'↑' if delta>0 else ('↓' if delta<0 else '–'),'n_old':len(old),'n_new':len(new)}
 cache[key]=r;return r
for ti,sta,future in [(3,'London',False),(7,'Fergus',False),(8,'Harrow',False),(4,'London',True),(9,'Fergus',True),(10,'Harrow',True)]:
 t=tab[tab.table==ti]
 for ri,r in t.groupby('row'):
  first=r[r.column==0].iloc[0]['text'];first=canonical.get(first.upper(),first)
  if first not in all_indices:continue
  for cell in r[r.column>0].to_dict('records'):
   ci=cell['column'];period=('Near' if ci<=11 else 'Far') if future else 'Present';sources=list(MODELS)+['Ensemble'] if future else ['Observed']+list(MODELS)+['Ensemble'];source=sources[(ci-1)%11] if future else sources[ci-1];v=result(sta,source,first,period)
   if cell['text'] not in ['↑','↓','–','—','-','n/a','N/A','']:continue
   q=dict(table=ti,row=int(ri),column=int(ci),station=sta,index=first,source=source,period=period,printed_arrow=cell['text'],printed_fill=cell['fill'],method='unadjusted observation sensitivity' if source=='Observed' else ('fixed-percentile no-bootstrap sensitivity' if first in pct_indices else 'independent daily raw'))
   if v:q.update(own_arrow=v['arrow'],delta=v['delta'],p=v['p'],n_old=v['n_old'],n_new=v['n_new'],arrow_equal=v['arrow']==cell['text'],printed_significant=cell['fill'] in ['548DD4','E36C0A'],significance_equal=bool(v['p']<.05 and v['delta']!=0)==(cell['fill'] in ['548DD4','E36C0A']))
   else:q.update(own_arrow='NOT COMPUTED',arrow_equal=None)
   if source not in ['Observed','Ensemble']:
    cl=result(sta,source+'_clean',first,period)
    if cl:q.update(clean_arrow=cl['arrow'],clean_delta=cl['delta'],clean_p=cl['p'])
   rows.append(q)
pd.DataFrame(rows).to_csv(OUT/'every_printed_arrow_independent.csv',index=False);print('arrows',len(rows));print(pd.DataFrame(rows).groupby('method').agg({'arrow_equal':['count','sum']}))

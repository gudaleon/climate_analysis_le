from independent_pass1 import *
from independent_percentiles import calculate
# Independent daily input selection: all 20 Fergus package files match FERGUS_SENS exactly.
# Keep first computation untouched and create correctly selected-cell artifacts separately.
assert pd.read_csv(OUT/'fergus_sensitivity_provenance.csv').equal_fergus_sensitivity_cell.all()
a=pd.read_csv(OUT/'annual_pass1.csv');m=pd.read_csv(OUT/'monthly_pass1.csv');pc=pd.read_csv(OUT/'percentile_sensitivity_pass1.csv')
a=a[~((a.station=='Fergus')&(a.model.isin(list(MODELS)+[x+'_clean' for x in MODELS])))];m=m[~((m.station=='Fergus')&(m.model.isin(MODELS)))];pc=pc[pc.station!='Fergus'];ars=[];mos=[];pcs=[];qc=[]
for sh,mo in MODELS.items():
 d=read(PC/'txt'/f'FERGUS_SENS_{mo}.txt');qc.append(integrity(d,'Fergus_'+sh,'365_day' if sh in ['BCC','CanESM','GFDL','INM','NorESM'] else 'proleptic_gregorian'))
 for model,clean in [(sh,False),(sh+'_clean',True)]:
  r=indices(d,clean=clean);r['station']='Fergus';r['model']=model;ars.append(r)
 r=indices(d,True);r['station']='Fergus';r['model']=sh;mos.append(r);r=calculate(d);r['station']='Fergus';r['model']=sh;pcs.append(r)
a=pd.concat([a]+ars,ignore_index=True);m=pd.concat([m]+mos,ignore_index=True);pc=pd.concat([pc]+pcs,ignore_index=True);a.to_csv(OUT/'annual_primary_selected_cells.csv',index=False);m.to_csv(OUT/'monthly_primary_selected_cells.csv',index=False);pc.to_csv(OUT/'percentile_primary_selected_cells.csv',index=False);pd.DataFrame(qc).to_csv(OUT/'fergus_selected_cell_integrity.csv',index=False)
changes=[];projections=[];branches=[]
for (sta,idx),g in a[a.model.isin(MODELS)].groupby(['station','index']):
 for model,h in g.groupby('model'):
  v={per:h[h.year.between(*years)].value.dropna() for per,years in PER.items()}
  for per in ['Present','Near','Far']:
   delta=v[per].median()-v['Historical'].median();p=test(v['Historical'],v[per]);changes.append(dict(station=sta,index=idx,model=model,period=per,delta=delta,p=p,direction=int(np.sign(delta)),significant=bool(p<.05)))
 for per in ['Present','Near','Far']:
  sub=[r for r in changes if r['station']==sta and r['index']==idx and r['period']==per];ds=np.array([r['delta'] for r in sub]);sig=np.array([r['significant'] for r in sub]);old=g[g.year.between(*PER['Historical'])].value.dropna();new=g[g.year.between(*PER[per])].value.dropna();up=int(sum(sig&(ds>0)));dn=int(sum(sig&(ds<0)));projections.append(dict(station=sta,index=idx,period=per,median_model_delta=np.median(ds),min_delta=min(ds),max_delta=max(ds),pooled_delta=new.median()-old.median(),pooled_p=test(old,new),significant_up=up,significant_down=dn,consensus=max(up,dn)>=8))
 obs=a[(a.station==sta)&(a['index']==idx)&(a.model=='supplied_merged')];old=obs[obs.year.between(*PER['Historical'])].value.dropna();new=obs[obs.year.between(*PER['Present'])].value.dropna();delta=new.median()-old.median();pr=next(r for r in projections if r['station']==sta and r['index']==idx and r['period']=='Present');lo,hi,mid=pr['min_delta'],pr['max_delta'],pr['median_model_delta'];bounded=lo<=delta<=hi;rev=delta*lo<0 and delta*hi<0;branches.append(dict(station=sta,index=idx,observed_delta=delta,p=test(old,new),model_min=lo,model_max=hi,model_median=mid,bounded=bool(bounded),reversal613=bool(not bounded and delta*mid<0),reversalv7=bool(rev),classv7='Bounded' if bounded else ('Sign reversal' if rev else 'Unbounded'),arrow='↑' if delta>0 else ('↓' if delta<0 else '–')))
pd.DataFrame(changes).to_csv(OUT/'model_changes_primary.csv',index=False);pd.DataFrame(projections).to_csv(OUT/'projections_primary.csv',index=False);pd.DataFrame(branches).to_csv(OUT/'unadjusted_branches_primary.csv',index=False);print('selected-cell recomputation complete')

from independent_pass1 import *
from scipy.stats import fisher_exact,rankdata,binomtest
ALL=['CSDI6','CSDI3','WSDI6','WSDI3','FD','ID','SU','TR','TNn','TNx','TXx','TXn','TXm','TMm','TNm','TN10p','TN90p','TX10p','TX90p','DTR','DTRgt15','GDDgrow10','TXb3TNb3','TXge30','TXgt50p','TNltm20','GSL','CWA','CWF','HWA','HWF','PRCPTOT','R10mm','R20mm','RX1day','RX3day','RX5day','SDII','R95p','R95pTOT','R99p','R99pTOT','CDD','CWD']
MAP={x.lower():x for x in ALL};MAP.update(csdi='CSDI6',wsdi='WSDI6');TEMP=set(ALL[:31]);rng=np.random.default_rng(20261107)
frames=[]
for tag in ['613','v7']:
 for sta in ['London','Fergus','Harrow']:
  f=next(OUT.glob(f'authors_annual_{tag}_All_{sta}_*.pkl'));d=next(iter(pd.read_pickle(f).values()));d['Index']=d.Index.str.strip().str.lower().map(MAP);d=d.replace(-99.9,np.nan);d=d.melt(['Year','Index'],var_name='Source',value_name='value').rename(columns={'Year':'year','Index':'index','Source':'model'});d['station']=sta;d['target']=tag;frames.append(d)
a=pd.concat(frames,ignore_index=True);a.to_csv(OUT/'conditional_author_annual_long.csv',index=False)
groups={k:g for k,g in a.groupby(['target','station','index','model'])}
def values(tag,sta,idx,model,per):
 g=groups[tag,sta,idx,model];return g[g.year.between(*PER[per])].value.dropna().to_numpy(float)
def med(v):return float(np.median(v)) if len(v) else np.nan
pv=[];changes=[];summ=[];env=[];cons=[]
for tag in ['613','v7']:
 for sta in ['London','Fergus','Harrow']:
  for idx in ALL:
   for mo in MODELS:
    for per in ['Historical','Present']:
     x=values(tag,sta,idx,'Observed',per);y=values(tag,sta,idx,mo,per);p=test(x,y);cc0=test(x,y,False);const=len(x)>0 and len(y)>0 and np.ptp(np.r_[x,y])==0;ties=len(np.unique(np.r_[x,y]))<len(x)+len(y);exact=test(x,y,exact=True) if not ties else np.nan
     pv.append(dict(target=tag,station=sta,index=idx,group='T' if idx in TEMP else 'P',model=mo,period=per,n_obs=len(x),n_model=len(y),p=p,p_no_cc=cc0,p_constant_is_one=1. if const else p,constant=const,tied=ties,p_exact_untied=exact))
   for per in ['Present','Near','Far']:
    for mo in (['Observed'] if per=='Present' else [])+list(MODELS)+['Ensemble']:
     x=np.concatenate([values(tag,sta,idx,m,'Historical') for m in MODELS]) if mo=='Ensemble' else values(tag,sta,idx,mo,'Historical');y=np.concatenate([values(tag,sta,idx,m,per) for m in MODELS]) if mo=='Ensemble' else values(tag,sta,idx,mo,per);delta=med(y)-med(x);p=test(x,y);p=1. if len(x) and len(y) and np.ptp(np.r_[x,y])==0 else p;arrow='n/a' if not np.isfinite(delta) else ('↑' if delta>0 else ('↓' if delta<0 else '–'));changes.append(dict(target=tag,station=sta,index=idx,model=mo,period=per,delta=delta,p=p,arrow=arrow,significant=bool(p<.05 and abs(delta)>=1e-9),n_old=len(x),n_new=len(y)))
   for branch in ['models_only','observations_in_past']:
    vs={}
    for per in PER:
     sources=list(MODELS)+(['Observed'] if branch=='observations_in_past' and per in ['Historical','Present'] else []);v=np.concatenate([values(tag,sta,idx,m,per) for m in sources]);q1,mid,q3=np.quantile(v,[.25,.5,.75]);iqr=q3-q1;out=int(sum((v<q1-1.5*iqr)|(v>q3+1.5*iqr)));vs[per]=[q1,mid,q3,out,len(v)]
    ih=vs['Historical'][2]-vs['Historical'][0];iff=vs['Far'][2]-vs['Far'][0];delta=vs['Far'][1]-vs['Historical'][1];ratio=iff/ih if ih else (np.inf if iff else 1.)
    for threshold in [.75,.8]:
     shift=('Increase' if delta>0 else ('Decrease' if delta<0 else 'No Shift'))+' ('+('Spread Expanded' if ratio>1.25 else ('Spread Contracted' if ratio<threshold else 'Stable Spread'))+')'
     for per,(q1,mid,q3,n,nn) in vs.items():summ.append(dict(target=tag,station=sta,index=idx,branch=branch,contraction_threshold=threshold,period=per,median=mid,q1=q1,q3=q3,outliers=n,n=nn,delta_far_hist=delta,iqr_ratio=ratio,label=shift))
ch=pd.DataFrame(changes);pv=pd.DataFrame(pv);su=pd.DataFrame(summ);ch.to_csv(OUT/'conditional_changes.csv',index=False);pv.to_csv(OUT/'conditional_test1_pvalues.csv',index=False);su.to_csv(OUT/'conditional_pooled_composition.csv',index=False)
for (tag,sta,idx),g in ch[ch.period=='Present'].groupby(['target','station','index']):
 o=g[g.model=='Observed'].iloc[0].delta;ds=g[g.model.isin(MODELS)].delta.to_numpy();lo,hi=np.nanmin(ds),np.nanmax(ds);mid=np.nanmedian(ds);bound=bool(lo<=o<=hi);rev613=bool(not bound and o*mid<0);rev7=bool(not bound and ((lo>0 and o<0)or(hi<0 and o>0)));env.append(dict(target=tag,station=sta,index=idx,observed_delta=o,min_delta=lo,max_delta=hi,median_delta=mid,bounded=bound,reversal613=rev613,reversalv7=rev7,class613='Within envelope' if bound else ('Directional reversal' if rev613 else 'Magnitude bias'),classv7='Bounded' if bound else ('Sign reversal' if rev7 else 'Unbounded'),n_obs_hist=int(g[g.model=='Observed'].iloc[0].n_old),n_obs_present=int(g[g.model=='Observed'].iloc[0].n_new)))
en=pd.DataFrame(env);en.to_csv(OUT/'conditional_envelope.csv',index=False)
counts=[];refs=[]
for field in ['p','p_no_cc','p_constant_is_one']:
 p=pv.copy();p['pass']=p[field]>=.05
 pc=p.groupby(['target','station','group','model','period'])['pass'].sum().unstack('period').reset_index();pc['total']=pc.Historical+pc.Present;pc['setting']=field;both=p.pivot(index=['target','station','group','model','index'],columns='period',values='pass');bc=(both.Historical&both.Present).groupby(['target','station','group','model']).sum().reset_index(name='both');pc=pc.merge(bc);counts.append(pc)
 for (tag,sta),g in pc[pc.group=='T'].groupby(['target','station']):
  g=g.sort_values(['total','both'],ascending=False,kind='stable');refs.append(dict(target=tag,setting=field,station=sta,group='T',reference=g.iloc[0].model,total=int(g.iloc[0].total),both=int(g.iloc[0].both)))
 for tag,g in pc[pc.group=='P'].groupby('target'):
  g=g.groupby('model')[['total','both']].sum().sort_values(['total','both'],ascending=False);refs.append(dict(target=tag,setting=field,station='BASIN',group='P',reference=g.index[0],total=int(g.iloc[0].total),both=int(g.iloc[0].both)))
pc=pd.concat(counts,ignore_index=True);pc.to_csv(OUT/'conditional_pass_counts_sensitivity.csv',index=False);pd.DataFrame(refs).to_csv(OUT/'conditional_reference_sensitivity.csv',index=False)
# Full Test 2 null, preserving index units and permuting observed changes across the three stations.
b=en[en.target=='v7'];ng=[(g.observed_delta.to_numpy(),g.min_delta.to_numpy(),g.max_delta.to_numpy()) for _,g in b.groupby('index')];null=[]
for _ in range(10000):
 total=0
 for orig,lo,hi in ng:
  obs=rng.permutation(orig);total+=int(sum((obs>=lo)&(obs<=hi)))
 null.append(total)
null=np.array(null);ns=dict(printed=115,recomputed=int(b.bounded.sum()),cases=len(b),permutations=len(null),null_mean=float(null.mean()),null_95=np.quantile(null,[.025,.975]).tolist(),p_upper=float((1+sum(null>=b.bounded.sum()))/(len(null)+1)),exchangeable_continuous_expected_rate=9/11,exchangeable_continuous_expected_cases=132*9/11,illustrative_independent_binomial_p=float(binomtest(115,132,9/11,alternative='greater').pvalue));(OUT/'conditional_envelope_null.json').write_text(json.dumps(ns,indent=2))
loo=[]
for tag in ['613','v7']:
 for omit in ['NONE']+list(MODELS):
  for sta in ['London','Fergus','Harrow']:
   ee=en[(en.target==tag)&(en.station==sta)];bounded=0;rev613=0;rev7=0
   for idx in ALL:
    g=ch[(ch.target==tag)&(ch.station==sta)&(ch['index']==idx)&(ch.period=='Present')];ds=g[g.model.isin([m for m in MODELS if m!=omit])].delta.to_numpy();o=g[g.model=='Observed'].iloc[0].delta;lo,hi=np.nanmin(ds),np.nanmax(ds);ib=lo<=o<=hi;bounded+=ib;rev613+=not ib and o*np.nanmedian(ds)<0;rev7+=not ib and ((lo>0 and o<0)or(hi<0 and o>0))
   for per in ['Near','Far']:
    gg=ch[(ch.target==tag)&(ch.station==sta)&(ch.period==per)&(ch.model.isin([m for m in MODELS if m!=omit]))];ok=[]
    for idx,g in gg.groupby('index'):
     up=sum(g.significant&(g.delta>0));dn=sum(g.significant&(g.delta<0));ok.append((idx,max(up,dn)>=8))
    loo.append(dict(target=tag,omitted=omit,station=sta,period=per,bounded=int(bounded),reversals613=int(rev613),reversalsv7=int(rev7),consensus_all=sum(k[1] for k in ok),consensus_T=sum(k[1] for k in ok if k[0] in TEMP),consensus_P=sum(k[1] for k in ok if k[0] not in TEMP)))
pd.DataFrame(loo).to_csv(OUT/'conditional_leave_one_out.csv',index=False)
skill=[];sv=pv[pv.target=='v7'].copy();sv['pass']=sv.p>=.05
for (sta,idx),g in sv.groupby(['station','index']):
 e=b[(b.station==sta)&(b['index']==idx)].iloc[0];skill.append(dict(station=sta,index=idx,passes=int(g['pass'].sum()),present=int(g.loc[g.period=='Present','pass'].sum()),bounded=bool(e.bounded),classv7=e.classv7))
sk=pd.DataFrame(skill);sk['skilful']=sk.passes>=10;sk.to_csv(OUT/'conditional_skill_cases.csv',index=False);sr=[]
for rule,s in [('>=10/20',sk.passes>=10),('>=15/20',sk.passes>=15),('Present>=5/10',sk.present>=5),('Present>=8/10',sk.present>=8)]:
 a1=int(sum(s&sk.bounded));bb=int(sum(s&~sk.bounded));cc=int(sum(~s&sk.bounded));dd=int(sum(~s&~sk.bounded));sr.append(dict(rule=rule,skilful_bounded=a1,skilful_unbounded=bb,not_skilful_bounded=cc,neither=dd,misjudged=bb+cc,fisher_two_sided=float(fisher_exact([[a1,bb],[cc,dd]]).pvalue)))
pd.DataFrame(sr).to_csv(OUT/'conditional_skill_summary.csv',index=False)
# Compare every reported Test 1 p-value directly to the recomputation from its annual inputs.
wbs={t:pd.read_pickle(OUT/f'authors_results_{t}.pkl') for t in ['613','v7']};diffs=[]
for r in pv.to_dict('records'):
 if r['target']=='v7':
  q=wbs['v7']['Model-obs p-values'];q=q[(q.Station==r['station'])&(q.Index==r['index'])&(q.Model==MODELS[r['model']])];printed=float(q.iloc[0]['p_'+r['period']])
 else:
  q=wbs['613']['P-values (Tables 3, A1, A2)'];q=q[(q.Station==r['station'])&(q.Index==r['index'])&(q.Period==r['period'])];printed=float(q.iloc[0][MODELS[r['model']]])
 diffs.append(dict(target=r['target'],station=r['station'],index=r['index'],model=r['model'],period=r['period'],printed_workbook=printed,recomputed=r['p'],difference=r['p']-printed))
pd.DataFrame(diffs).to_csv(OUT/'conditional_pvalue_workbook_diff.csv',index=False)
# Raw independent annual values against the provided annual tables, without rounding away differences.
raw=pd.read_csv(OUT/'annual_primary_selected_cells.csv');raw=raw[raw.model.isin(MODELS)].copy();cmp=raw.merge(a[a.target=='613'],on=['station','index','model','year'],suffixes=('_independent','_provided'));cmp['difference']=cmp.value_independent-cmp.value_provided;cmp.to_csv(OUT/'independent_daily_to_author_annual_diff.csv',index=False)
print('Test2',en.groupby('target')[['bounded','reversal613','reversalv7']].sum().to_dict());print('null',ns);print('skill',sr);print('refs',refs)

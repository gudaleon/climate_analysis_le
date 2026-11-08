from independent_pass1 import *
from independent_percentiles import calculate
import shutil
D=OUT/'addendum_a';D.mkdir(exist_ok=True)
checks=[]
meta=pd.read_csv(PC/'metadata.csv');meta=meta[meta.station=='FERGUS']
for r in meta.to_dict('records'):
 p=PC/'raw_nc'/r['raw_nc_file'];h=hashlib.sha256(p.read_bytes()).hexdigest();checks.append(dict(file=str(p),expected=r['sha256'],actual=h,equal=h==r['sha256']))
assert len(checks)==30 and all(r['equal'] for r in checks)
pd.DataFrame(checks).to_csv(D/'checksums.csv',index=False)
# Verify text conversion against the authenticated netCDF values.
import xarray as xr
conv=[]
for mo in MODELS.values():
 d=read(PC/'txt'/f'FERGUS_{mo}.txt')
 for var,col in [('pr','pr'),('tasmax','tx'),('tasmin','tn')]:
  r=meta[(meta.model==mo)&(meta.variable==var)].iloc[0];ds=xr.open_dataset(PC/'raw_nc'/r.raw_nc_file,decode_times=False);v=np.asarray(ds[var]).reshape(-1);v=v-273.15 if var!='pr' and 'K' == ds[var].attrs.get('units') else v
  err=np.nanmax(abs(v-d[col].to_numpy()));conv.append(dict(model=mo,variable=var,max_absolute_rounding_error=err));print(mo,var,err,ds[var].attrs);assert err<.051
pd.DataFrame(conv).to_csv(D/'text_raw_verification.csv',index=False)
a=pd.read_csv(OUT/'annual_primary_selected_cells.csv');a=a[(a.station=='Fergus')&a.model.isin(MODELS)];pc=pd.read_csv(OUT/'percentile_primary_selected_cells.csv');pc=pc[pc.station=='Fergus'];pc['month']=0
t=pd.concat([a,pc],ignore_index=True);t['branch']='T';rows=[]
for sh,mo in MODELS.items():
 d=read(PC/'txt'/f'FERGUS_{mo}.txt');v=pd.concat([indices(d),calculate(d).assign(month=0)],ignore_index=True);v['model']=sh;v['branch']='S';rows.append(v)
s=pd.concat(rows,ignore_index=True);z=pd.concat([t,s],ignore_index=True);z.to_csv(D/'annual_values.csv',index=False)
p=[];ch=[];ar=[]
for (br,idx,mo),g in z.groupby(['branch','index','model']):
 vals={k:g[g.year.between(*ys)].value.dropna() for k,ys in PER.items()}
 for per,v in vals.items():p.append(dict(branch=br,index=idx,model=mo,period=per,median=v.median()))
 for per in ['Present','Near','Far']:
  delta=vals[per].median()-vals['Historical'].median();pv=test(vals['Historical'],vals[per]);ch.append(dict(branch=br,index=idx,model=mo,period=per,delta=delta,p=pv,arrow='↑' if delta>0 else '↓' if delta<0 else '–',shading='significant' if pv<.05 and delta!=0 else 'unshaded'))
p=pd.DataFrame(p);c=pd.DataFrame(ch);c.to_csv(D/'model_changes_arrows.csv',index=False)
piv=p.pivot(index=['index','model','period'],columns='branch',values='median').reset_index();piv['S_minus_T']=piv['S']-piv['T'];piv.to_csv(D/'period_medians.csv',index=False)
ens=[]
for (br,idx,per),g in p.groupby(['branch','index','period']):ens.append(dict(branch=br,index=idx,period=per,median=g['median'].median(),spread=g['median'].max()-g['median'].min()))
e=pd.DataFrame(ens);ep=e.pivot(index=['index','period'],columns='branch',values=['median','spread']);ep.columns=['_'.join(x) for x in ep.columns];ep=ep.reset_index();ep['effect']=ep.median_S-ep.median_T
obs=pd.read_csv(OUT/'annual_primary_selected_cells.csv');obs=obs[(obs.station=='Fergus')&(obs.model=='supplied_merged')];bounds=[];perf=[]
for (br,idx),g in z.groupby(['branch','index']):
 o=obs[obs['index']==idx]
 if len(o):
  old=o[o.year.between(*PER['Historical'])].value.dropna();new=o[o.year.between(*PER['Present'])].value.dropna();delta=new.median()-old.median();v=c[(c.branch==br)&(c['index']==idx)&(c.period=='Present')];lo,hi=v.delta.min(),v.delta.max();bounds.append(dict(branch=br,index=idx,observed=delta,minimum=lo,maximum=hi,classification='bounded' if lo<=delta<=hi else 'sign reversal' if delta*lo<0 and delta*hi<0 else 'magnitude offset'))
  for mo,h in g.groupby('model'):
   for per in ['Historical','Present']:
    pv=test(o[o.year.between(*PER[per])].value,h[h.year.between(*PER[per])].value);perf.append(dict(branch=br,index=idx,model=mo,period=per,p=pv,passed=pv>=.05,group='P' if idx in ['PRCPTOT','R10mm','R20mm','RX1day','RX3day','RX5day','SDII','CDD','CWD','R95p','R99p','R95pTOT','R99pTOT'] else 'T'))
b=pd.DataFrame(bounds);b.to_csv(D/'bounds.csv',index=False);f=pd.DataFrame(perf);f.to_csv(D/'test1_unadjusted_subset.csv',index=False)
counts=f.groupby(['branch','model','group']).passed.sum().unstack();counts['total']=counts.sum(axis=1);counts['rank']=counts.groupby(level=0).total.rank(method='min',ascending=False)
cons=c.assign(up=(c.p<.05)&(c.delta>0),down=(c.p<.05)&(c.delta<0)).groupby(['branch','index','period'])[['up','down']].sum();cons['consensus']=cons.max(axis=1)>=8
parts=['# ADDENDUM A — Fergus grid-cell fork\n\nExecuted 2026-11-07 in Python; this VM has no system R (R executable: '+str(shutil.which('R'))+'). Reuses independent_pass1.py and independent_percentiles.py without changing their definitions. Branch T is the saved selected-cell main-audit calculation; Branch S is FERGUS, grid (32,727), versus T FERGUS_SENS (32,728). This is a fork, not a correction.\n\nAll tables below use the ten models '+', '.join(MODELS)+'. Periods: '+str(PER)+'. Baseline 1950–1986; missing sentinel −99.9 becomes NA, annual dependent-variable missingness >15 invalidates the index. Rank-sum tests are two-sided, asymptotic, tie corrected, continuity corrected, alpha .05; constant combined samples return NA. Quantiles and run boundaries remain those in the saved implementation. Temperature percentile indices are fixed-threshold, no-bootstrap sensitivities.\n\nEvidence: [checksums](evidence/addendum_a/checksums.csv), [text versus authenticated raw NetCDF](evidence/addendum_a/text_raw_verification.csv). All 30 raw checksums pass; text values agree within 0.051 (one-decimal text rounding) in output units.\n\nThis fork tests two adjacent cells of one downscaled product. It does not test other products, resolutions, or observations. Every table inherits these axes and settings.\n\n## Annual values and period medians\n\nEvery annual value is in [annual_values.csv](evidence/addendum_a/annual_values.csv), with branch, model, index and year. The following table gives all model period medians and S−T differences, including zero differences. Units are °C for temperature levels/DTR; mm for rainfall amounts, mm/day for SDII; % for percentile fractions and R95pTOT/R99pTOT; degree-days for GDDgrow10; days for counts, spells and GSL.\n',piv.to_markdown(index=False),'\n\nEnsemble median of ten model period medians, ten-model range width, and cell effect in the same index units:\n',ep.to_markdown(index=False),'\n\n## Test 1\n\nThese are unadjusted-observation, 30-index subset counts (13 precipitation, 17 temperature, two periods: maxima 26/34/60), not the thesis 44-index adjusted-observation Test 1. T/P/total and ranks follow.\n',counts.reset_index().to_markdown(index=False),'\n\nThe main audit did not independently implement homogenisation or all 44 daily indices. Therefore the thesis-format full pass counts, ranking and reference-model selection under either thesis rule are NOT ESTABLISHED for S. Subset ranks must not be substituted for those selections.\n\n## Bounding and arrow branches\n\nUnadjusted observed Present−Historical change versus ten model changes, in the units above:\n',b.to_markdown(index=False),'\n\nAll model arrows and significance shading for Present, Near and Far versus Historical, T beside S:\n',c.pivot(index=['index','model','period'],columns='branch',values=['delta','p','arrow','shading']).to_markdown(),'\n\nConsensus uses at least eight significant same-direction models:\n',cons.to_markdown(),'\n\n## Headline aggregates and claims\n\nThe main report’s 115/132 bounded result was conditional on supplied full annual inputs. It cannot be restated for S from this independent subset. The independently computed 30-index unadjusted branch has the following Fergus bounded counts:\n',b.assign(bounded=b.classification=='bounded').groupby('branch').bounded.sum().to_markdown(),'\n\nFull 132-case bounded and 44-index consensus totals, adjusted-observation arrows, pooled ensemble shading for all thesis indices, monthly selected-reference headlines, and changes in reference selection remain NOT ESTABLISHED. The unchanged London/Harrow cases cannot fill missing Fergus computations.\n\nClaim inventory entries mentioning Fergus (each inherits that limitation; direct-index numeric changes are enumerated in the tables above):\n']
claims=pd.read_csv(OUT/'claim_verdicts.csv');q=claims[claims.printed.str.contains('Fergus',case=False,na=False)];parts.append(q[['claim','printed']].to_markdown(index=False))
parts.append('\n\n## Stability statement\n\nThe period median table states the cell effect against the ten-model spread for every computed index and period; the classification and arrow tables identify the cell-dependent readings directly. Only matching rows support fork-independent conclusions within this restricted implementation. No full-thesis stability conclusion follows from these subset results. This addendum is a completed restricted computation, but does not complete all computations requested in the addendum brief; missing full-index and adjusted-observation branches are explicitly unresolved.\n')
Path('REPORT_WuThesis_Codex_ADDENDUM_A_2026-11-07.md').write_text('\n'.join(parts))
print('report written',len(z))

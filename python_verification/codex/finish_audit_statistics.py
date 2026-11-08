from independent_pass1 import *
import re
# Arrays in these files are evidence from post-seal output audits, not a blind full-chain reimplementation.
m=pd.read_csv(OUT/'conditional_monthly_all_models.csv');raw=pd.read_csv(OUT/'monthly_primary_selected_cells.csv');out=[]
for (sta,idx,month),g in raw[(raw.model=='supplied_merged')&raw.month.isin([1,2,3,6,7,8,9])].groupby(['station','index','month']):
 if idx not in ['TMm','TXx','TXn','ID','SU','RX1day','RX5day','PRCPTOT','R10mm','CDD']:continue
 vals={p:g[g.year.between(*yr)].value.dropna().to_numpy() for p,yr in PER.items()};tails={}
 for p,arr in vals.items():
  if len(arr):q=np.quantile(arr,.25 if idx=='TXn' else .75);tails[p]=arr[arr<=q] if idx=='TXn' else arr[arr>=q]
  else:tails[p]=np.array([])
 old,new=tails['Historical'],tails['Present'];x,y=np.median(old),np.median(new);index=idx.upper();index='CDD_within_month' if index=='CDD' else index;z=m[(m.station==sta)&(m.model=='Observed')&(m['index']==index)&(m.month==month)].iloc[0];out.append(dict(station=sta,index=idx,month=int(month),unadjusted_old=x,unadjusted_new=y,unadjusted_delta=y-x,unadjusted_p_full=test(vals['Historical'],vals['Present']),supplied_adjusted_old=z.old,supplied_adjusted_new=z.new,supplied_adjusted_delta=z.delta,supplied_adjusted_p_full=z.p_full,delta_movement=z.delta-(y-x),direction_changed=bool(np.sign(z.delta)!=np.sign(y-x))))
pd.DataFrame(out).to_csv(OUT/'monthly_unadjusted_vs_supplied_adjusted.csv',index=False)
diffs=[]
for tag in ['613','v7']:
 w=pd.read_pickle(OUT/f'authors_results_{tag}.pkl');df=w['Monthly (Sec 3.4)' if tag=='613' else 'Monthly']
 for r in df.to_dict('records'):
  mo='Observed' if r['Source']=='Observed' else ('BCC' if r['Source'].startswith('BCC') else ('NorESM' if r['Source'].startswith('NorESM') else 'EC'));idx='CDD_ending_recycled' if r['Index']=='CDD' else r['Index'];q=m[(m.station==r['Station'])&(m.model==mo)&(m['index']==idx)&(m.month==r['Month'])]
  for comp,old,new,pcol in [('Historical->Present','Historical','Present','Wilcoxon p H vs P (all monthly values)'),('Near->Far','Near','Far','Wilcoxon p Near vs Far (all monthly values)')]:
   if not len(q[q.comparison==comp]):continue
   v=q[q.comparison==comp].iloc[0]
   for field,own,printed,precision in [(old,v.old,r[old],2),(new,v.new,r[new],2),('p',v.p_full,r[pcol],3)]:diffs.append(dict(target=tag,station=r['Station'],model=mo,index=r['Index'],month=r['Month'],comparison=comp,field=field,computed=own,printed_workbook=printed,raw_difference=own-printed,equal_printed_precision=(np.isnan(own) and pd.isna(printed)) or f'{own:.{precision}f}'==f'{printed:.{precision}f}'))
pd.DataFrame(diffs).to_csv(OUT/'monthly_statistics_workbook_diff.csv',index=False)
# Headline sensitivity to model choice, using each model in turn.
heads=m[(m.model!='Observed')&(m.comparison=='Near->Far')&(((m['index']=='PRCPTOT')&(m.month==1))|((m['index'].isin(['PRCPTOT','SPEI3','SPEI6','SPI3','SPI6']))&(m.month.isin([7,8,9]))))];sm=[]
for (sta,idx,month),g in heads.groupby(['station','index','month']):
 ref=g[g.model=='BCC'].iloc[0];sm.append(dict(station=sta,index=idx,month=int(month),BCC_delta=ref.delta,BCC_pct=ref.pct,BCC_p=ref.p_full,min_delta=g.delta.min(),median_delta=g.delta.median(),max_delta=g.delta.max(),models_decreasing=int(sum(g.delta<0)),models_increasing=int(sum(g.delta>0)),significant_decreases=int(sum((g.delta<0)&(g.p_full<.05))),significant_increases=int(sum((g.delta>0)&(g.p_full<.05)))))
pd.DataFrame(sm).to_csv(OUT/'monthly_headline_model_dependence.csv',index=False)
# Quantify the composition defect separately for every Table C1 row and every statistic.
s=pd.read_csv(OUT/'conditional_pooled_composition.csv',dtype={'target':str});s=s[(s.target=='v7')&(s.contraction_threshold==.8)];one=s[s.branch=='models_only'];mix=s[s.branch=='observations_in_past'];j=one.merge(mix,on=['target','station','index','period','contraction_threshold'],suffixes=('_models_only','_mixed'));fields=['median','q1','q3','outliers','n'];diff=[]
for r in j.to_dict('records'):
 for f in fields:
  aa,bb=r[f+'_models_only'],r[f+'_mixed'];diff.append(dict(station=r['station'],index=r['index'],period=r['period'],field=f,printed_code_mixed=bb,printed_method_models_only=aa,difference=aa-bb,changes_printed_precision=(round(aa,1)!=round(bb,1)) if f in ['median','q1','q3'] else aa!=bb))
pd.DataFrame(diff).to_csv(OUT/'v7_composition_every_statistic.csv',index=False)
labels=pd.read_csv(OUT/'conditional_pooled_composition.csv',dtype={'target':str});labels=labels[(labels.target=='v7')&(labels.period=='Far')];lo=labels[labels.contraction_threshold==.75];hi=labels[labels.contraction_threshold==.8];q=lo.merge(hi,on=['target','station','index','period','branch'],suffixes=('_printed_075','_code_080'));q=q[q.label_printed_075!=q.label_code_080];q.to_csv(OUT/'v7_spread_threshold_changed_labels.csv',index=False)
# Daily index discrepancies have exact residuals in the full artifact; this is only an index-level overview.
d=pd.read_csv(OUT/'independent_daily_to_author_annual_diff.csv');summary=[]
for idx,g in d.groupby('index'):
 finite=np.isfinite(g.value_independent)&np.isfinite(g.value_provided);eq=np.isclose(g.value_independent,g.value_provided,equal_nan=True,atol=1e-9,rtol=0);summary.append(dict(index=idx,cells=len(g),different_over_1e_9=int(sum(~eq)),missingness_differences=int(sum(g.value_independent.isna()!=g.value_provided.isna())),max_abs_difference=g.difference.abs().max()))
pd.DataFrame(summary).to_csv(OUT/'independent_daily_annual_difference_summary.csv',index=False)
# Match printed Table B1 values against the recomputation from the supplied annual inputs.
b=pd.read_csv(OUT/'printed_bound_internal_check_pass1.csv');e=pd.read_csv(OUT/'conditional_envelope.csv',dtype={'target':str});e=e[e.target=='v7'];z=b.merge(e,on=['station','index']);z['obs_difference']=z.observed_delta-z.printed_obs;z['min_difference']=z.min_delta-z.printed_min;z['max_difference']=z.max_delta-z.printed_max;z.to_csv(OUT/'every_printed_bound_checked.csv',index=False)
print('monthly matches',pd.DataFrame(diffs).equal_printed_precision.value_counts().to_dict());print('v7 composition cases moving a displayed statistic',j[(j.median_models_only.round(1)!=j.median_mixed.round(1))|(j.q1_models_only.round(1)!=j.q1_mixed.round(1))|(j.q3_models_only.round(1)!=j.q3_mixed.round(1))|(j.outliers_models_only!=j.outliers_mixed)][['station','index']].drop_duplicates().shape[0]);print('spread changed labels',len(q))

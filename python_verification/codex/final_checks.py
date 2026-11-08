from independent_pass1 import *
import re
# Complete-subtree checks must precede opening the v7 Climpact output files.
snap=json.loads((OUT/'mirror_snapshot_final.json').read_text());checks=[r for r in snap if r['path'].endswith('c_Climpact_indices')];assert all(r['files']==2941 and r['bytes']==163433847 for r in checks)
rows=[]
for sub in ['2_Data/2_Models/c_Climpact_indices','2_Data/1_Observations/d_Climpact_indices']:
 for p in sorted((P1/sub).rglob('*')):
  if not p.is_file():continue
  q=P2/p.relative_to(P1);aa=p.read_bytes();bb=q.read_bytes() if q.exists() else b'';rows.append(dict(path=str(p.relative_to(P1)),bytes613=len(aa),bytesv7=len(bb),equal=aa==bb,sha613=hashlib.sha256(aa).hexdigest(),shav7=hashlib.sha256(bb).hexdigest()))
pd.DataFrame(rows).to_csv(OUT/'shared_climpact_output_hashes.csv',index=False)
arr=pd.read_csv(OUT/'every_printed_arrow_independent.csv').fillna({'printed_arrow':'','printed_fill':''});ch=pd.read_csv(OUT/'conditional_changes.csv',dtype={'target':str});ch=ch[ch.target=='613'].rename(columns={'model':'source','arrow':'conditional_arrow','delta':'conditional_delta','p':'conditional_p','significant':'conditional_significant'});arr=arr.merge(ch[['station','index','source','period','conditional_arrow','conditional_delta','conditional_p','conditional_significant']],left_on=['station','index','source','period'],right_on=['station','index','source','period'],how='left');arr['conditional_arrow_with_code_tolerance']=np.where(arr.conditional_delta.abs()<1e-9,'–',arr.conditional_arrow);arr['conditional_matches_printed']=arr.printed_arrow==arr.conditional_arrow_with_code_tolerance;arr['printed_significant']=arr.printed_fill.isin(['548DD4','E36C0A']);arr['conditional_significance_matches']=arr.printed_significant==arr.conditional_significant;arr['cell_verdict']=np.where(arr.own_arrow=='NOT COMPUTED','CANNOT VERIFY',np.where(arr.arrow_equal==True,'CONFIRMED','DISPUTED'));arr.loc[arr.method!='independent daily raw','cell_verdict']='CANNOT VERIFY';arr['scope']='Model daily raw, fixed-percentile sensitivity or unadjusted-observation sensitivity as named; full-wave/compound inputs not independently calculated.';arr.to_csv(OUT/'every_arrow_final_audit.csv',index=False)
# Core observation mask/definition differences are retained exactly, not silently filled.
a=pd.read_csv(OUT/'conditional_author_annual_long.csv',dtype={'target':str},low_memory=False);a=a[(a.target=='613')&(a.model=='Observed')];o=pd.read_csv(OUT/'conditional_independent_indices_supplied_homogenised.csv');j=o.merge(a,on=['station','index','year'],suffixes=('_own','_provided'));j['difference']=j.value_own-j.value_provided;j.to_csv(OUT/'supplied_homogenised_daily_to_annual_diff.csv',index=False)
# R-like extended accumulation versus NumPy double median, on the same annual values.
diffs=[]
for (sta,idx,mo),g in pd.read_csv(OUT/'conditional_author_annual_long.csv',dtype={'target':str},low_memory=False).query('target == "613"').groupby(['station','index','model']):
 for per,yr in PER.items():
  v=np.sort(g[g.year.between(*yr)].value.dropna().to_numpy());n=len(v)
  if n and n%2==0:
   direct=float((v[n//2-1]+v[n//2])/2);extended=float((np.longdouble(v[n//2-1])+np.longdouble(v[n//2]))/2)
   if direct!=extended:diffs.append(dict(station=sta,index=idx,model=mo,period=per,numpy_median=direct,extended_precision_median=extended,difference=direct-extended))
pd.DataFrame(diffs).to_csv(OUT/'median_accumulation_sensitivity.csv',index=False)
# Deletion rows in a change list are not literal-text mismatches.
c=pd.read_csv(OUT/'change_list_613_text_check.csv');oldtext=re.sub(r'\s+',' ',(OUT/'text_613_new.txt').read_text()).replace('–','-').replace('−','-').replace('’',"'").strip();c['check_result']=np.where(c.new_text=='(deleted)',np.where(c.old_text.map(lambda s:s not in oldtext),'deletion verified','deletion NOT verified'),np.where(c.new_located,'new text located','new text NOT located'));c.to_csv(OUT/'change_list_613_text_check_final.csv',index=False)
print('shared Climpact',len(rows),'nonidentical',sum(not r['equal'] for r in rows));print('arrow cells',len(arr),'blank',sum(arr.printed_arrow==''),'conditional glyph mismatches',sum(~arr.conditional_matches_printed),'shade mismatches',sum(~arr.conditional_significance_matches));print('median accumulation changed',len(diffs));print(c.check_result.value_counts().to_dict())

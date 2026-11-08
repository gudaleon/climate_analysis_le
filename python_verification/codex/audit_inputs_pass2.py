from independent_pass1 import *
required=['annual_primary_selected_cells.csv','monthly_primary_selected_cells.csv','percentile_primary_selected_cells.csv','model_changes_primary.csv','projections_primary.csv','unadjusted_branches_primary.csv','pooled_summary_independent.csv','every_printed_arrow_independent.csv','envelope_null_primary.json','fergus_selected_netcdf_to_pcic_txt.csv','monthly_reference_sensitivity_primary.csv','temperature_cleaning_annual_effects_primary.csv']
assert all((OUT/f).exists() for f in required),'Independent artifacts not ready'
seal={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'Independent restricted computations finished; full RHtests and all-index Pass 1 not completed. Subsequent review is a limited Pass 2, not full protocol compliance.','artifacts':[{'file':f,'bytes':(OUT/f).stat().st_size,'sha256':hashlib.sha256((OUT/f).read_bytes()).hexdigest()} for f in required]}
(OUT/'pass1_final_seal_before_author_reads.json').write_text(json.dumps(seal,indent=2))
code=[];hashes=[];structures=[]
for tag,root in [('613',P1),('v7',P2)]:
 for p in sorted((root/'3_Code').rglob('*')):
  if p.is_file() and p.suffix.lower() in ['.r','.csv']:
   text=p.read_text(errors='replace');code.append('\n# FILE '+tag+' '+str(p.relative_to(root))+'\n'+'\n'.join(f'{i}: {x}' for i,x in enumerate(text.splitlines(),1)));hashes.append(dict(target=tag,path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 for p in sorted((root/'4_Results').glob('*.xlsx')):
  wb=pd.read_excel(p,sheet_name=None);(OUT/f'authors_results_{tag}_schema.json').write_text(json.dumps({k:{'rows':len(v),'columns':list(v.columns),'first_rows':v.head(2).fillna('NA').to_dict('records')} for k,v in wb.items()},default=str,indent=2));pd.to_pickle(wb,OUT/f'authors_results_{tag}.pkl')
  print(tag,'results',[(k,len(v),list(v.columns)[:8]) for k,v in wb.items()])
 for p in sorted((root/'2_Data/3_Annual_index_tables').glob('*.xlsx')):
  wb=pd.read_excel(p,sheet_name=None);pd.to_pickle(wb,OUT/f'authors_annual_{tag}_{p.stem}.pkl');structures.append(dict(target=tag,file=str(p),sheets=[dict(name=k,rows=len(v),columns=list(v.columns),first_rows=v.head(2).fillna('NA').to_dict('records')) for k,v in wb.items()]))
(OUT/'authors_numbered_code_with_lines.txt').write_text('\n'.join(code));pd.DataFrame(hashes).to_csv(OUT/'authors_code_hashes.csv',index=False);(OUT/'authors_annual_schemas.json').write_text(json.dumps(structures,default=str,indent=2))
shared=[]
for sub in ['2_Data/1_Observations','2_Data/3_Annual_index_tables','2_Data/4_Monthly_analysis']:
 for p in sorted((P1/sub).rglob('*')):
  if not p.is_file() or 'd_Climpact_indices' in str(p):continue
  rel=p.relative_to(P1);q=P2/rel;h1=hashlib.sha256(p.read_bytes()).hexdigest();h2=hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None;shared.append(dict(path=str(rel),sha613=h1,shav7=h2,equal=h1==h2))
pd.DataFrame(shared).to_csv(OUT/'shared_input_hash_comparison.csv',index=False)
print('shared equal',pd.DataFrame(shared).equal.value_counts().to_dict())

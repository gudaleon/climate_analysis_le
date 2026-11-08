from report_helpers import *
import hashlib,datetime,json,re
r=pd.read_csv(E/'claim_verdicts.csv',low_memory=False)
old='The code pools observations into the two past blocks contrary to §2.9. A displayed statistic moves under like-composed model-only blocks.'
new='Section 4.11 acknowledges observations in the past pools, conflicting with the ten-model method in Section 2.9. Values follow the former mixed reading; the displayed model-only alternative follows the latter. The verdict concerns this internal method conflict.'
r.loc[r.reason==old,'reason']=new
q=r.claim=='C1';r.loc[q,'evidence']='text_613_new.txt'
q=r.claim=='V7-C1000';r.loc[q,'recomputed']='Inventory label R99pTO is resolved as R99pTOT using the clean DOCX table; no distinct 45th index is invented. '+r.loc[q,'recomputed'].iloc[0]
s=pd.read_csv(E/'conditional_pooled_composition.csv',dtype={'target':str});s=s[(s.target=='v7')&(s.contraction_threshold==.8)&s.period.isin(['Historical','Present'])];a=s[s.branch=='models_only'];b=s[s.branch=='observations_in_past'];j=a.merge(b,on=['station','index','period'],suffixes=('_models','_mixed'));frac=100*(j.n_mixed-j.n_models)/j.n_mixed
q=r.claim=='V7-C649';r.loc[q,'recomputed']=f'Conditional observed contributions across past station-index pools range {frac.min():.9g}%–{frac.max():.9g}%, all below 10%. Sensitivity to actual homogenisation is a separate question; controlled 30-index and monthly before/after values are reported in Section 6.5.';r.loc[q,'reason']='The under-10% fraction is verified from supplied annual sample counts. The compound claim of consequent insensitivity has no specified numerical tolerance and was not established across the unexecuted RHtests branches.';r.loc[q,'evidence']='conditional_pooled_composition.csv'
r.to_csv(E/'claim_verdicts.csv',index=False)
text=(HERE/'REPORT_DRAFT.md').read_text();text=text.replace(old,new)
for tag,start,end in [('613','## 2. Target 1 — 6.13 — every inventory claim','## 3. Target 2 — v7 — every inventory claim'),('v7','## 3. Target 2 — v7 — every inventory claim','## 4. Pass 2 audit log')]:
 lo=text.index(start);hi=text.index(end,lo+len(start));t=r[r.claim.str.startswith('V7-') if tag=='v7' else ~r.claim.str.startswith('V7-')].copy();t['Evidence / limitation']=t.apply(lambda x:f'[{x.evidence}]({E/x.evidence}) — '+x.reason,axis=1);text=text[:lo]+start+'\n\n'+md(t[['claim','printed','recomputed','verdict','Evidence / limitation']])+'\n\n'+text[hi:]
needle='**Code that ran.**'
note=('**Sealed arrow artifact.** The initial arrow CSV contained 4,064 cells because four uppercase R95/R99 table labels and blank grey cells were not yet canonicalised. The later complete annex has 4,488 cells. A reconstruction of the original 4,064-cell file from the sealed raw-derived inputs is byte-identical to the pre-author-read seal (SHA-256 `638cc53e0f7839ac00756ad18cc7c304af2df463a4d17923ec6513284276acbc`), as recorded in '+f'[arrow_seal_reconstruction_check.json]({E/"arrow_seal_reconstruction_check.json"})'+'. The expanded annex and its scope-resolved cell verdicts are post-seal table-reading work; they are not represented as additional blind upstream computation.\n\n')
text=text.replace(needle,note+needle,1)
needle='This log identifies demonstrated differences and unresolved implementation choices.'
nuance=('**Two printed pooling descriptions.** Section 2.9 specifies annual simulated values across ten GCMs. Section 4.11 later explicitly says observations contribute less than 10% to the pooled results. The code follows the latter. This report grades the disagreement between those printed descriptions and quantifies both compositions; it does not claim the mixed pooling was nowhere disclosed. Actual past-pool observed contributions are '+f'{frac.min():.6f}%–{frac.max():.6f}%'+'.\n\n')
text=text.replace(needle,nuance+needle,1)
small=pd.read_csv(E/'monthly_statistics_workbook_diff.csv',dtype={'target':str});small=small[~small.equal_printed_precision]
needle='## 6. Composition audit — the six axes'
extra=('**Remaining monthly workbook rounding residuals.** The corrected CDD port exactly matches all nine supplied CDD inputs; its initial Python missing-value handling error was repaired in the auditor code. The following two export comparisons remain, both the same Harrow observed September TMm cell in the two workbooks. The full-precision residual is shown. Binary last-bit/serialization choices can select a different two-decimal rounding, so this is not a demonstrated physical-climate discrepancy.\n\n'+md(small)+'\n\n')
text=text.replace(needle,extra+needle,1)
# Regenerate the disputed-claim log to carry the resolved method descriptions and inventory alias.
lo=text.index('## 5. Discrepancy log');start=text.index('| claim |',lo);end=text.index('Independent annual-index differences',start);text=text[:start]+md(r[r.verdict=='DISPUTED'][['claim','printed','recomputed','reason']])+'\n\n'+text[end:]
# The additional processing is explicit, and the current source manifest includes this script.
marker='**Code that ran.**';text=text.replace(marker,'`finalize_report.py` subsequently resolved the §4.11 pooling disclosure, the R99pTO inventory abbreviation, the original arrow-seal reconstruction, and the remaining workbook rounding log; it regenerated the same claim counts and verdict tables.\n\n'+marker,1)
rows=[]
for p in sorted(HERE.glob('*.py')):rows.append(dict(script=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
pd.DataFrame(rows).to_csv(E/'audit_code_manifest.csv',index=False)
assert len(r)==1324 and r.claim.nunique()==1324
assert len(r[~r.claim.str.startswith('V7-')])==292 and len(r[r.claim.str.startswith('V7-')])==1032
assert set(r.verdict)=={'CONFIRMED','DISPUTED','CANNOT VERIFY'}
assert 'full blind two-pass audit' in text and 'not performed' in text
# Every linked local evidence file must exist. Empty intermediate CSVs are identified by their generating log, not fabricated rows.
links=re.findall(r'\]\((/[^)]+)\)',text);missing=[p for p in links if not Path(p).exists()];assert not missing,missing
(HERE/'REPORT_READY.md').write_text(text)
validation={'claims_613':292,'claims_v7':1032,'unique_claims':1324,'arrow_cells':4488,'printed_bound_rows':132,'verdict_counts':r.groupby('verdict').size().to_dict(),'report_bytes':len(text.encode()),'report_sha256':hashlib.sha256(text.encode()).hexdigest(),'missing_local_links':missing,'full_requested_independent_audit_completed':False,'drive_file_created':False,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(E/'report_validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation,indent=2))

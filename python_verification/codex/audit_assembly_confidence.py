from independent_pass1 import *
from io import StringIO
from zipfile import ZipFile
from lxml import etree
import re,difflib
A=pd.read_csv(OUT/'conditional_author_annual_long.csv',dtype={'target':str},low_memory=False);A=A[A.target=='613'];allidx=list(A['index'].unique());PSET={'PRCPTOT','R10mm','R20mm','RX1day','RX3day','RX5day','SDII','R95p','R95pTOT','R99p','R99pTOT','CDD','CWD'};TEMP=set(allidx)-PSET;groups={k:g.set_index('year').value for k,g in A.groupby(['station','index','model'])}
def climate(p):
 lines=p.read_text().splitlines();h=next(i for i,l in enumerate(lines) if l.startswith('time'));d=pd.read_csv(StringIO('\n'.join(lines[h:])),skipinitialspace=True);d.columns=d.columns.str.strip();return d.replace(-99.9,np.nan)
summary=[];nonzero=[]
for sta in ['London','Fergus','Harrow']:
 for mo in ['Observed']+list(MODELS):
  run=sta.upper()+'_v4' if mo=='Observed' else sta+'_'+mo;folder=P1/'2_Data/1_Observations/d_Climpact_indices'/run if mo=='Observed' else P1/'2_Data/2_Models/c_Climpact_indices'/run
  for idx in allidx:
   if idx=='DTRgt15':continue
   suffix={'CSDI6':'csdi','WSDI6':'wsdi'}.get(idx,idx.lower())
   if idx in ['CWA','CWF','HWA','HWF']:
    suffix='ecf_heatwave' if idx.startswith('C') else 'ehf_heatwave';d=climate(folder/f'{run}_{suffix}_ANN.csv');col=idx
   else:
    d=climate(folder/f'{run}_{suffix}_ANN.csv');col='duration' if 'duration' in d else ('sl' if 'sl' in d else d.columns[1])
   y=pd.to_numeric(d.iloc[:,0]).astype(int);v=pd.to_numeric(d[col]);s=groups[sta,idx,mo];provided=s.reindex(y).to_numpy();own=v.to_numpy();delta=own-provided;eq=(own==provided)|(np.isnan(own)&np.isnan(provided));summary.append(dict(station=sta,model=mo,index=idx,file=str(folder/f'{run}_{suffix}_ANN.csv'),rows=len(y),nonidentical_cells=int(sum(~eq)),max_abs_difference=float(np.nanmax(abs(delta))) if np.isfinite(delta).any() else 0.,missingness_mismatches=int(sum(np.isnan(own)!=np.isnan(provided)))))
   for year,x,z,ok in zip(y,own,provided,eq):
    if not ok:nonzero.append(dict(station=sta,model=mo,index=idx,year=int(year),climpact=x,annual_table=z,difference=x-z))
pd.DataFrame(summary).to_csv(OUT/'climpact_to_annual_assembly_summary.csv',index=False);pd.DataFrame(nonzero).to_csv(OUT/'climpact_to_annual_all_nonidentical_cells.csv',index=False)
# Workbook byte inequality is separated from actual cell inequality.
s1=pd.read_excel(P1/'2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx');s2=pd.read_excel(P2/'2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx');eq=s1.equals(s2);(OUT/'shared_monthly_workbook_cell_comparison.json').write_text(json.dumps({'shape613':list(s1.shape),'shapev7':list(s2.shape),'dataframe_equal':eq,'columns_equal':list(s1.columns)==list(s2.columns)},indent=2))
# Confidence under printed fixed rule and a correction of the cold compound index's group membership.
B=pd.read_csv(OUT/'conditional_envelope.csv',dtype={'target':str});B=B[B.target=='v7'];ch=pd.read_csv(OUT/'conditional_changes.csv',dtype={'target':str});ch=ch[(ch.target=='v7')&(ch.model=='Ensemble')];G={'Baseline temperature regime':(['TMm','TNm','TXm','TNn','TNx','TXn','TXx'],'warm'),'Loss of cold extremes':(['FD','ID','TN10p','TX10p','TNltm20','CSDI6','CSDI3','CWA','CWF'],'cold'),'Heat extremes and heat waves':(['SU','TR','TN90p','TX90p','TXge30','TXgt50p','TXb3TNb3','WSDI6','WSDI3','HWA','HWF'],'warm'),'Growing season and heat accumulation':(['GSL','GDDgrow10'],'warm'),'Diurnal temperature structure':(['DTR','DTRgt15'],'dom'),'Precipitation amount and frequency':(['PRCPTOT','R10mm','R20mm'],'warm'),'Extreme precipitation intensity':(['RX1day','RX3day','RX5day','SDII','R95p','R99p','R95pTOT','R99pTOT'],'warm'),'Wet-dry spell persistence':(['CDD','CWD'],'dom')}
def coherence(vals,idx,mode,zero=False):
 s=np.sign(np.round(np.asarray(vals,float),6));idx=np.asarray(idx);expected=np.where(idx=='CWA',1,-1) if mode=='cold' else np.ones(len(s));return int(max(sum(s==1),sum(s==-1))+(sum(s==0) if zero else 0)) if mode=='dom' else int(sum((s==expected)|((s==0)&zero)))
conf=[]
for branch in ['as_code','TXb3TNb3_moved_to_cold']:
 for name,(ks0,mode) in G.items():
  ks=list(ks0)
  if branch!='as_code':
   if name=='Heat extremes and heat waves':ks.remove('TXb3TNb3')
   if name=='Loss of cold extremes':ks.append('TXb3TNb3')
  z=B[B['index'].isin(ks)];n=len(z);cohs=[100*coherence(z.observed_delta,z['index'],mode)/n]
  for per in ['Near','Far']:
   q=ch[(ch.period==per)&ch['index'].isin(ks)];cohs.append(100*coherence(q.delta,q['index'],mode)/n)
  bound=100*z.bounded.mean();sr=int(z.reversalv7.sum());zeros=float(np.mean(np.round(z.observed_delta,6)==0));ag=all(coherence(q.observed_delta,q['index'],mode)/len(q)>=.6 for _,q in z.groupby('station'));rating='Low' if zeros>=.5 or bound<60 or sum(np.array(cohs)<60)>=2 else ('High' if sum(np.array(cohs)>=80)>=2 and bound>=80 and sr==0 and ag else 'Moderate');conf.append(dict(branch=branch,group=name,n_indices=len(ks),n_cases=n,hist_coherence=cohs[0],near_coherence=cohs[1],far_coherence=cohs[2],bounded_percent=bound,reversals=sr,zero_percent=100*zeros,station_agreement=ag,rating=rating))
pd.DataFrame(conf).to_csv(OUT/'conditional_confidence_recomputed.csv',index=False)
# Text checks: a failed literal/normalized search is only an unlocated row, not proof of numerical error.
def norm(s):return re.sub(r'\s+',' ',str(s)).replace('–','-').replace('−','-').replace('’',"'").strip()
changes=pd.read_excel(next((P1/'1_Thesis').glob('*.xlsx')));new=norm((OUT/'text_613_new.txt').read_text());old=norm((OUT/'text_613_old.txt').read_text());cl=[]
for r in changes.to_dict('records'):
 nt=norm(r['New text']);ot=norm(r['Old text']);cl.append(dict(row=r['#'],section=r['Section'],old_text=ot,new_text=nt,reason=r['Reason'],old_located=ot in old,new_located=nt in new))
pd.DataFrame(cl).to_csv(OUT/'change_list_613_text_check.csv',index=False)
p=next((P2/'1_Thesis').glob('Change_list*.docx'))
with ZipFile(p) as z:doc=etree.fromstring(z.read('word/document.xml'))
text='\n'.join(''.join(e.itertext()) for e in doc.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'));(OUT/'change_list_v6_v7_extracted.txt').write_text(text)
print('assembly rows',len(summary),'exact unequal cells',len(nonzero));print('shared monthly cells equal',eq);print(pd.DataFrame(conf).to_string(index=False));print('change-list rows',len(cl),'unlocated new',sum(not r['new_located'] for r in cl))

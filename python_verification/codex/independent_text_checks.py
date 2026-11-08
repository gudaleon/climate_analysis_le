from independent_pass1 import *
import re
inv=Path('/home/hatch/workspace/jeremy_wu_redteam/thesis/CLAIMS_INVENTORY_v7.md').read_text()
rows=[]
for cid,txt in re.findall(r'^- \*\*(V7-C\d+)\.\*\* (.*?)(?=\n- \*\*|\n##|\Z)',inv,re.M|re.S):
 if not txt.startswith('Table B1 reports for '):continue
 m=re.search(r'for (\w+) station index (\S+).*?observed shift \(Δobs\) of ([-\d.]+), a model minimum \(Δmin\) of ([-\d.]+) and a model maximum \(Δmax\) of ([-\d.]+).*?outcome of (Bounded|Unbounded|Sign [Rr]eversal)',txt)
 if not m:print('unparsed',cid);continue
 sta,idx,o,lo,hi,printed=m.groups();printed=printed.replace('Sign Reversal','Sign reversal');o,lo,hi=map(float,[o,lo,hi]);bound=lo<=o<=hi;rev=(o*lo<0 and o*hi<0);own='Bounded' if bound else ('Sign reversal' if rev else 'Unbounded');rows.append(dict(claim=cid,station=sta,index=idx,printed_obs=o,printed_min=lo,printed_max=hi,printed_class=printed,recomputed_from_printed=own,equal=printed==own))
pd.DataFrame(rows).to_csv(OUT/'printed_bound_internal_check_pass1.csv',index=False);print('rows',len(rows));print(pd.DataFrame(rows).query('not equal').to_string(index=False))

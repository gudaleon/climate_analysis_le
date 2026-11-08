from pathlib import Path
import pandas as pd,numpy as np,json,re
HERE=Path.cwd();E=HERE/'evidence';INV=Path('/home/hatch/workspace/jeremy_wu_redteam/thesis')
def claims(tag):
 s=(INV/f'CLAIMS_INVENTORY_{tag}.md').read_text();return [(k,' '.join(v.split())) for k,v in re.findall(r'^- \*\*((?:V7-)?C\d+)\.\*\* (.*?)(?=\n- \*\*|\n##|\Z)',s,re.M|re.S)]
def csv(name):return pd.read_csv(E/name)
def js(name):return json.loads((E/name).read_text())
def fmt(v):
 if isinstance(v,(float,np.floating)):return 'NA' if not np.isfinite(v) else f'{v:.9g}'
 return str(v)
def esc(x):return str(x).replace('|','\\|').replace('\n',' ')
def md(df,columns=None):
 if columns:df=df[columns]
 return '| '+' | '.join(esc(c) for c in df.columns)+' |\n| '+' | '.join('---' for c in df.columns)+' |\n'+'\n'.join('| '+' | '.join(esc(fmt(x)) for x in row)+' |' for row in df.itertuples(index=False,name=None))+'\n'
def link(name):return f'[{name}](evidence/{name})'
def summarize_values(a,station,index,models=None):
 g=a[(a.station==station)&(a['index']==index)];g=g[g.model.isin(models)] if models else g
 out=[]
 for per,(lo,hi) in {'Historical':(1950,1986),'Present':(1987,2023),'Near':(2024,2062),'Far':(2063,2100)}.items():
  x=g[g.year.between(lo,hi)].value.dropna().to_numpy()
  if not len(x):continue
  q1,m,q3=np.quantile(x,[.25,.5,.75]);n=int(sum((x<q1-1.5*(q3-q1))|(x>q3+1.5*(q3-q1))))
  out.append(dict(period=per,median=m,q1=q1,q3=q3,outliers=n,n=len(x)))
 return out

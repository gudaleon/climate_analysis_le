from independent_pass1 import *
d=read(PC/'txt'/'FERGUS_SENS_ACCESS-ESM1-5.txt');base=d[d.year.between(1950,1986)];wet=np.sort(np.rint(base.loc[base.pr>=1,'pr'].to_numpy()*10).astype(int));n=len(wet);num=(3*n+1)*19+20;den=60;j,rem=divmod(num,den);qnum=(den-rem)*wet[j-1]+rem*wet[j];qexact=qnum/(den*10);qfloat=np.quantile(wet/10,.95,method='median_unbiased');rows=[]
a=pd.read_csv(OUT/'conditional_author_annual_long.csv',dtype={'target':str},low_memory=False);a=a[(a.target=='613')&(a.station=='Fergus')&(a.model=='ACCESS')&(a['index']=='R95p')].set_index('year').value
for yr,g in d.groupby('year'):
 rr=np.rint(g.pr.to_numpy()*10).astype(int);v=np.sum(rr[rr*den>qnum])/10;rows.append(dict(year=int(yr),exact_decimal_quantile=qexact,numpy_quantile=repr(qfloat),recomputed=v,provided=a.loc[yr],difference=v-a.loc[yr]))
pd.DataFrame(rows).to_csv(OUT/'R95p_exact_decimal_threshold_branch.csv',index=False);print('threshold float',repr(qfloat),'exact',qexact,'remaining nonzero residuals',sum(abs(r['difference'])>1e-9 for r in rows))

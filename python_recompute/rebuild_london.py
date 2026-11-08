import sys, numpy as np, pandas as pd
sys.path.insert(0,'code'); exec(open('code/rebuild_merge.py').read().split("res={}")[0])
raw=read_daily(A+'London_6144475_LONDON_INTL_AIRPORT_station_file.txt'); raw['date']=pd.to_datetime(raw[['year','month','day']])
dd=raw[raw.date.duplicated(keep=False)].date; print('dup span',dd.min().date(),dd.max().date(),'days',dd.nunique())
apf=raw.drop_duplicates('date',keep='first').set_index('date')[['pr','tx','tn']]
apl=raw.drop_duplicates('date',keep='last').set_index('date')[['pr','tx','tn']]
cs=eccc('London_6144478_LONDON_CS_ECCC_daily.csv'); ape=eccc('London_6144475_LONDON_INTL_AIRPORT_ECCC_daily.csv')
t=read_daily(S+'b_Merged_daily_series/LONDON_merged_6144475_6144478.txt'); t['date']=pd.to_datetime(t[['year','month','day']]); t=t.set_index('date')[['pr','tx','tn']]
eq=lambda x,y: (np.abs(x-y)<0.051)|(x.isna()&y.isna())
for v in ['pr','tx','tn']:
    p=t.loc['2002-09-19':,v]
    srcs={'stfile_first':apf[v],'stfile_second':apl[v],'CS_ECCC':cs[v],'AP_ECCC':ape[v]}
    s={k:eq(p,x.reindex(p.index)) for k,x in srcs.items()}
    print(v,{k:int(x.sum()) for k,x in s.items()},'n',len(p),'neither',int((~s['stfile_first']&~s['stfile_second']&~s['CS_ECCC']&~s['AP_ECCC']).sum()))
    print('   2018+: ',{k:int(x.loc['2018':].sum()) for k,x in s.items()},'n',len(p.loc['2018':]))
    print('   pre-split == stfile:',int(eq(t.loc[:'2002-09-18',v],apf[v].reindex(t.loc[:'2002-09-18'].index)).sum()),'of',len(t.loc[:'2002-09-18']))
    # filled days in CS window: merged non-NA where CS NA
    c=cs[v].reindex(p.loc[:'2017'].index); fill=c.isna()&p.loc[:'2017'].notna()
    na=c.isna().values; iso=na & ~np.r_[False,na[:-1]] & ~np.r_[na[1:],False]
    print('   CS-window CS missing',int(c.isna().sum()),'filled',int(fill.sum()),'of which isolated gaps',int((fill.values&iso).sum()),'filled from multi-day gaps',int((fill.values&~iso).sum()),
          'still missing in merged',int((c.isna()&p.loc[:'2017'].isna()).sum()))

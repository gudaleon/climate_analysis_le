import sys, numpy as np, pandas as pd
sys.path.insert(0,'code'); from cdx import read_daily
S='/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/1_Observations/'
A=S+'a_ECCC_station_sources/'
def eccc(*fs):
    d=pd.concat([pd.read_csv(A+f,low_memory=False) for f in fs])
    d=d.rename(columns={'LOCAL_YEAR':'year','LOCAL_MONTH':'month','LOCAL_DAY':'day','TOTAL_PRECIPITATION':'pr','MAX_TEMPERATURE':'tx','MIN_TEMPERATURE':'tn'})
    d['date']=pd.to_datetime(d[['year','month','day']]); return d.drop_duplicates('date').set_index('date')[['pr','tx','tn']].astype(float)
def stf(f):
    d=read_daily(A+f); d['date']=pd.to_datetime(d[['year','month','day']]); return d.set_index('date')[['pr','tx','tn']]
def full(a,b): return pd.DataFrame(index=pd.date_range(f'{a}-01-01',f'{b}-12-31'))
def cmp(name, mine, theirs_f):
    t=read_daily(S+'b_Merged_daily_series/'+theirs_f); t['date']=pd.to_datetime(t[['year','month','day']]); t=t.set_index('date')[['pr','tx','tn']]
    m=mine.reindex(t.index)
    out={}
    for v in ['pr','tx','tn']:
        a,b=m[v].values,t[v].values
        diff=~((np.isnan(a)&np.isnan(b))|(np.abs(a-b)<0.051))
        out[v]=int(diff.sum()); 
        if diff.sum(): out[v+'_first']=str(t.index[diff][:5].date.tolist())
        out[v+'_missing_theirs']=int(np.isnan(b).sum())
    out['rows_theirs']=len(t); out['first']=str(t.index[0].date()); out['last']=str(t.index[-1].date())
    print(name,out); return t
res={}
# London: airport station file to 2002-09-18, then CS; airport ECCC fills missing CS days
ap=stf('London_6144475_LONDON_INTL_AIRPORT_station_file.txt'); cs=eccc('London_6144478_LONDON_CS_ECCC_daily.csv'); ape=eccc('London_6144475_LONDON_INTL_AIRPORT_ECCC_daily.csv')
L=full(1950,2023).join(ap.loc[:'2002-09-18']); L.update(cs.loc['2002-09-19':])
L1=L.copy()
for v in ['pr','tx','tn']:
    miss=L1[v].isna() & (L1.index>='2002-09-19')
    L1.loc[miss,v]=ape[v].reindex(L1.index[miss]).values
print('London station-file period ends', ap.index.max().date(), 'airport ECCC', ape.index.min().date(), ape.index.max().date(), 'CS', cs.index.min().date(), cs.index.max().date())
cmp('London fill-all',L1,'LONDON_merged_6144475_6144478.txt')
# isolated-only fill variant
L2=L.copy()
for v in ['pr','tx','tn']:
    na=L2[v].isna().values; iso=na & ~np.r_[False,na[:-1]] & ~np.r_[na[1:],False] & (L2.index>='2002-09-19')
    L2.loc[iso,v]=ape[v].reindex(L2.index[iso]).values
tL=cmp('London fill-isolated',L2,'LONDON_merged_6144475_6144478.txt')
# Harrow
h1=eccc('Harrow_6133360_HARROW_CDA_ECCC_daily_part1.csv','Harrow_6133360_HARROW_CDA_ECCC_daily_part2.csv','Harrow_6133360_HARROW_CDA_ECCC_daily_part3.csv')
h2=eccc('Harrow_613CC60_HARROW_AUTOMATIC_ECCC_daily.csv'); h3=eccc('Harrow_6133362_HARROW_CDA_AUTO_ECCC_daily.csv')
print('Harrow 6133360',h1.index.min().date(),h1.index.max().date(),'613CC60',h2.index.min().date(),h2.index.max().date(),'6133362',h3.index.min().date(),h3.index.max().date())
for endcc in ['2000-07-31','2000-08-31']:
    H=full(1950,2023).join(h1.loc[:'1991-12-31'])
    H.update(h2.loc['1992-01-01':endcc]); nxt=(pd.Timestamp(endcc)+pd.Timedelta(days=1))
    H.update(h3.loc[nxt:])
    H.loc['1992-04-01':'1992-04-30']=h1.reindex(pd.date_range('1992-04-01','1992-04-30')).values
    cmp(f'Harrow 613CC60 to {endcc}',H,'HARROW_merged_6133360_613CC60_6133362.txt')
# Fergus
F=full(1950,2023).join(stf('Fergus_6142400_FERGUS_SHAND_DAM_station_file.txt'))
fe=eccc('Fergus_6142400_FERGUS_SHAND_DAM_ECCC_daily_2012.csv')
print('Fergus 2012-09-29 station file',F.loc['2012-09-29'].values,'ECCC',fe.loc['2012-09-29'].values if '2012-09-29' in fe.index else None)
F.loc['2012-09-29','pr']=fe.loc['2012-09-29','pr']
cmp('Fergus',F,'FERGUS_SHAND_DAM_6142400.txt')

from independent_pass1 import *
src=P1/'2_Data/1_Observations/a_ECCC_station_sources';dates=pd.date_range('1950-01-01','2023-12-31');ind=pd.MultiIndex.from_arrays([dates.year,dates.month,dates.day],names=COL[:3]);a=read(next(src.glob('London*station_file.txt'))).drop_duplicates(COL[:3],keep='first').set_index(COL[:3]).reindex(ind);airport=eccc(next(src.glob('London_6144475*.csv'))).reindex(ind);a=airport.combine_first(a);b=eccc(next(src.glob('London_6144478*.csv'))).reindex(ind);d=a.copy();mask=dates>=pd.Timestamp('2002-09-19');d.loc[mask]=b.loc[mask].combine_first(a.loc[mask]);d=d.reset_index();d.to_csv(OUT/'merged_own_London_all_sources.csv',index=False)
pack=read(next((P1/'2_Data/1_Observations/b_Merged_daily_series').glob('LONDON*')));diff=[]
for v in ['pr','tx','tn']:
 ok=np.isclose(d[v],pack[v],equal_nan=True);diff.append(dict(variable=v,different_days=int(sum(~ok)),examples=d.loc[~ok,COL[:3]].to_dict('records')))
(OUT/'london_all_source_merge_check.json').write_text(json.dumps(diff,indent=2));print(diff)
indices(d).to_csv(OUT/'london_all_source_annual_pass1.csv',index=False)

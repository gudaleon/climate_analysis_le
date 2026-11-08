from independent_pass1 import *
import netCDF4
meta=pd.read_csv(PC/'metadata.csv');rows=[];nc_compare=[];grid=[]
coords={'FERGUS_SENS':(43.735,-80.330)}
for station,(lat,lon) in coords.items():
 for short,model in MODELS.items():
  subset=meta[(meta.station==station)&(meta.model==model)]
  txt=read(PC/'txt'/f'{station}_{model}.txt')
  for r in subset.to_dict('records'):
   with netCDF4.Dataset(PC/'raw_nc'/r['raw_nc_file']) as ds:
    t=ds.variables['time'];dates=netCDF4.num2date(t[:],t.units,getattr(t,'calendar','standard'));ymd=np.array([(x.year,x.month,x.day) for x in dates]);cal=getattr(t,'calendar','standard');v=ds.variables[r['variable']];arr=np.array(v[:]).squeeze();col={'pr':'pr','tasmax':'tx','tasmin':'tn'}[r['variable']];val=txt[col].to_numpy();rounded=np.round(arr,1);nc_compare.append(dict(station=station,model=short,variable=r['variable'],nc_calendar=cal,dates_equal=bool(np.array_equal(ymd,txt[COL[:3]].to_numpy())),nc_to_txt_rounded_differences=int(sum(~np.isclose(rounded,val,equal_nan=True))),max_abs_nc_txt=float(np.nanmax(np.abs(arr-val)))))
   if r['variable']=='pr':
    clat=r['cell_lat'];clon=r['cell_lon'];half=1/24
    grid.append(dict(station=station,model=short,printed_lat=lat,printed_lon=lon,cell_lat=clat,cell_lon=clon,assumed_spacing=1/12,contains_printed=bool(abs(lat-clat)<=half and abs(lon-clon)<=half),lat_difference=clat-lat,lon_difference=clon-lon))
pd.DataFrame(nc_compare).to_csv(OUT/'fergus_selected_netcdf_to_pcic_txt.csv',index=False);pd.DataFrame(grid).to_csv(OUT/'fergus_selected_grid_containment.csv',index=False)
print(pd.DataFrame(nc_compare).groupby('variable').agg({'dates_equal':'all','nc_to_txt_rounded_differences':'sum','max_abs_nc_txt':'max'}).to_string());print(pd.DataFrame(grid).groupby('station').contains_printed.sum())

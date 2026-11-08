"""Addendum A: verify Branch S (FERGUS) and Branch T (FERGUS_SENS) PCIC inputs against metadata.csv checksums,
rebuild the 1-dp text series from the raw NetCDF, and check the thesis packages' Fergus files against both cells."""
import hashlib, numpy as np, pandas as pd, netCDF4 as N, cftime
Q = '/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final/'
DM = '/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/'
PK = {'P1': DM + 'Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data/2_Data/2_Models/b_Daily_series/',
      'P2': DM + 'Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data/2_Data/2_Models/b_Daily_series/'}
M = {'ACCESS': 'ACCESS-ESM1-5', 'BCC': 'BCC-CSM2-MR', 'CanESM': 'CanESM5', 'CNRM': 'CNRM-ESM2-1', 'EC': 'EC-Earth3-Veg',
     'GFDL': 'GFDL-ESM4', 'INM': 'INM-CM5-0', 'MIROC': 'MIROC-ES2L', 'MRI': 'MRI-ESM2-0', 'NorESM': 'NorESM2-LM'}
h = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
meta = pd.read_csv(Q + 'metadata.csv')
rows = []
for lab in ['FERGUS', 'FERGUS_SENS']:
    txt = {}
    for m, full in M.items():
        t = pd.read_csv(Q + f'txt/{lab}_{full}.txt', sep='\t', header=None, names=['year', 'month', 'day', 'pr', 'tx', 'tn'])
        r = dict(label=lab, model=m)
        for var, col in [('pr', 'pr'), ('tasmax', 'tx'), ('tasmin', 'tn')]:
            md = meta[(meta.station == lab) & (meta.model == full) & (meta.variable == var)].iloc[0]
            f = Q + 'raw_nc/' + md.raw_nc_file
            r[f'sha_{var}'] = h(f) == md.sha256
            d = N.Dataset(f)
            assert d.station == lab and int(d.grid_cell_lat_index) == md.grid_cell_lat_index and int(d.grid_cell_lon_index) == md.grid_cell_lon_index
            r['nc_lat'], r['nc_lon'] = float(d['lat'][...]), float(d['lon'][...])
            v = d[var][:].filled(np.nan); tm = d['time']
            dates = cftime.num2date(tm[:], tm.units, tm.calendar)
            r[f'rows_{var}'] = len(v) == md.row_count == len(t)
            r[f'dates_{var}'] = all(a.year == y and a.month == mo and a.day == dd for a, y, mo, dd in zip(dates, t.year, t.month, t.day)) if len(dates) == len(t) else False
            # txt is 1-dp rounding of raw; allow half-even/float edge (0.05 + eps)
            r[f'val_{var}'] = bool(np.nanmax(np.abs(np.round(v, 1) - t[col].values)) <= 0.1001 and np.mean(np.abs(v - t[col].values) <= 0.0500001) == 1.0)
            r[f'maxdiff_{var}'] = float(np.nanmax(np.abs(v - t[col].values)))
        r['txt_sha'] = h(Q + f'txt/{lab}_{full}.txt')
        for k, p in PK.items():
            r[f'eq_{k}'] = h(p + f'Fergus_{m}.txt') == r['txt_sha']
        rows.append(r)
df = pd.DataFrame(rows)
df.to_csv('out_addA/input_verification.csv', index=False)
print(df.drop(columns='txt_sha').to_string())
print('ALL sha ok:', bool(df[[c for c in df if c.startswith('sha_')]].all().all()),
      ' rows/dates ok:', bool(df[[c for c in df if c.startswith(('rows_', 'dates_'))]].all().all()),
      ' values ok:', bool(df[[c for c in df if c.startswith('val_')]].all().all()))
# how different are the two cells' daily series?
for m, full in M.items():
    a = pd.read_csv(Q + f'txt/FERGUS_{full}.txt', sep='\t', header=None).values[:, 3:]
    b = pd.read_csv(Q + f'txt/FERGUS_SENS_{full}.txt', sep='\t', header=None).values[:, 3:]
    dd = b - a
    print(m, 'S-T daily mean diff pr/tx/tn', np.round(-dd.mean(0), 3), 'MAD', np.round(np.abs(dd).mean(0), 3), 'corr', [round(np.corrcoef(a[:, i], b[:, i])[0, 1], 4) for i in range(3)])

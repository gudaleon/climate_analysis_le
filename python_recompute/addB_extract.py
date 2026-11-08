"""Addendum B, Stage 1: extract the Harrow perturbed cell (lat index 12, lon index 696, one step west of the
Harrow station cell 12/697) from the PCIC CanDCS-U6 source NetCDF on the OPeNDAP service, following the
construction of jeremy_pcic/run_2026-10-19/final/code/download_pcic.py exactly (same catalogue URLs, same
cftime date axis, same unit-conversion rule, same one-decimal tab-separated text format).

Gate: the same code also pulls the control cell (12/697). The control series, formatted as text, must
reproduce the delivered txt/HARROW_<model>.txt files value for value, and the full-precision control
values must match the delivered raw subset NetCDF files, before the perturbed extraction is trusted.
"""
import sys, json, math, hashlib
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, cftime

FIN = Path('/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final')
OUT = Path('/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_claude/out_addB')
(OUT / 'raw_nc').mkdir(parents=True, exist_ok=True)
(OUT / 'txt').mkdir(parents=True, exist_ok=True)
IY, IX_T, IX_P = 12, 697, 696
ST_LAT, ST_LON = 42.033, -82.900
MODELS = ["ACCESS-ESM1-5", "BCC-CSM2-MR", "CanESM5", "CNRM-ESM2-1", "EC-Earth3-Veg",
          "GFDL-ESM4", "INM-CM5-0", "MIROC-ES2L", "MRI-ESM2-0", "NorESM2-LM"]
VARS = ["pr", "tasmax", "tasmin"]


def conversion_for(var, units):
    u = (units or "").strip()
    if var == "pr":
        if u == "kg m-2 s-1":
            return 86400.0, 0.0, "mm/day", "pr: kg m-2 s-1 -> mm/day (x86400)"
        if u in ("kg m-2 d-1", "kg m-2 day-1", "mm/day", "mm d-1"):
            return 1.0, 0.0, "mm/day", f"pr: units already {u} (= mm/day), no conversion"
        return None
    if u in ("K", "Kelvin"):
        return 1.0, -273.15, "degC", f"{var}: K -> degC (-273.15)"
    if u in ("degC", "degrees_C", "Celsius", "deg_C"):
        return 1.0, 0.0, "degC", f"{var}: units already {u}, no conversion"
    return None


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


meta = pd.read_csv(FIN / 'metadata.csv')
meta = meta[meta.station == 'HARROW'].set_index(['model', 'variable'])

ONLY = sys.argv[1:] if len(sys.argv) > 1 else MODELS
FRAG = OUT / 'frag'; FRAG.mkdir(exist_ok=True)
prov = []
gate_rows = []
for model in ONLY:
    ctrl, pert = {}, {}
    dates_ref = None
    for var in VARS:
        m = meta.loc[(model, var)]
        url = m['url']
        ds = xr.open_dataset(url, engine="pydap", decode_times=False)
        t_units = ds["time"].attrs.get("units", ""); t_cal = ds["time"].attrs.get("calendar", "")
        times_raw = np.asarray(ds["time"].values, dtype=float)
        dates = list(cftime.num2date(times_raw, t_units, calendar=t_cal))
        cell_lat_p = float(np.asarray(ds["lat"].values, float)[IY]); cell_lon_p = float(np.asarray(ds["lon"].values, float)[IX_P])
        orig_units = ds[var].attrs.get("units", "")
        conv = conversion_for(var, orig_units)
        assert conv is not None, f"{model} {var}: unrecognised units {orig_units}"
        factor, offset, out_units, conv_desc = conv
        def pull(ix):
            """Pull one cell's full time series in 5-year blocks with retries (a single full-column
            DAP2 request stalls against this server; block requests of ~3 s each succeed)."""
            n = len(times_raw); out = np.full(n, np.nan)
            for s0 in range(0, n, 1826):
                s1 = min(n, s0 + 1826)
                for attempt in range(1, 5):
                    try:
                        a = ds[var].isel(lat=IY, lon=ix, time=slice(s0, s1)).values
                        break
                    except Exception:
                        if attempt == 4: raise
                        import time as _t; _t.sleep(15 * attempt)
                        try: ds.close()
                        except Exception: pass
                        globals()['ds'] = xr.open_dataset(url, engine="pydap", decode_times=False)
                        a = None
                a = np.ma.filled(np.ma.asarray(a, dtype=float), np.nan) if np.ma.isMaskedArray(a) else np.asarray(a, dtype=float)
                out[s0:s1] = a
            return out
        a_t, a_p = pull(IX_T), pull(IX_P)
        ds.close()
        if dates_ref is None:
            dates_ref = dates
        else:
            assert len(dates) == len(dates_ref) and all((a.year, a.month, a.day) == (b.year, b.month, b.day) for a, b in zip(dates, dates_ref)), f"{model}: {var} date axis differs"
        # gate (ii): full-precision control vs delivered raw subset NetCDF
        loc = xr.open_dataset(FIN / 'raw_nc' / m['raw_nc_file'], decode_times=False)
        a_loc = np.asarray(loc[var].values, dtype=float); loc.close()
        same_nan = bool((np.isnan(a_t) == np.isnan(a_loc)).all())
        finite = ~np.isnan(a_t) & ~np.isnan(a_loc)
        maxdiff = float(np.abs(a_t[finite] - a_loc[finite]).max()) if finite.any() else 0.0
        gate_rows.append(dict(model=model, variable=var, n=len(a_t), nan_pattern_match=same_nan,
                              max_abs_diff_full_precision=maxdiff, conversion=conv_desc, calendar=t_cal))
        ctrl[var] = a_t * factor + offset
        pert[var] = a_p * factor + offset
        # save the perturbed raw subset NetCDF, mirroring the delivered format
        member = m['member']
        raw = xr.Dataset({var: (("time",), a_p)},
                         coords={"time": ("time", times_raw), "lat": cell_lat_p, "lon": cell_lon_p},
                         attrs={"source_url": url, "model": model, "member": member, "variable": var,
                                "station": "HARROW", "station_lat": ST_LAT, "station_lon": ST_LON,
                                "grid_cell_lat_index": IY, "grid_cell_lon_index": IX_P,
                                "branch": "P (Addendum B perturbed cell, one step west of the Harrow station cell)",
                                "extraction_code": "executor_runs/wu_claude/code/addB_extract.py"})
        raw["time"].attrs.update({"units": t_units, "calendar": t_cal})
        raw[var].attrs.update({"units": orig_units})
        nc_path = OUT / 'raw_nc' / f"HARROW_P_{model}_{var}.nc"
        raw.to_netcdf(nc_path)
        prov.append(dict(model=model, variable=var, member=member, url=url, lat_index=IY, lon_index=IX_P,
                         cell_lat=round(cell_lat_p, 6), cell_lon=round(cell_lon_p, 6), calendar=t_cal, units_original=orig_units,
                         conversion=conv_desc, rows=len(a_p), missing=int(np.isnan(a_p).sum()),
                         sha256=hashlib.sha256(nc_path.read_bytes()).hexdigest(), raw_nc_file=nc_path.name))
    # assemble text files exactly as download_pcic.py wrote them
    def fmt(vals_by_var):
        lines = []
        for i, dt in enumerate(dates_ref):
            row = [f"{dt.year}", f"{dt.month}", f"{dt.day}"]
            for var in VARS:
                v = vals_by_var[var][i]
                row.append("-99.9" if np.isnan(v) else f"{v:.1f}")
            lines.append("\t".join(row))
        return lines
    pert_lines = fmt(pert)
    (OUT / 'txt' / f"HARROWP_{model}.txt").write_text("\n".join(pert_lines) + "\n")
    # gate (i): control text vs delivered text, value for value
    delivered = (FIN / 'txt' / f"HARROW_{model}.txt").read_text().splitlines()
    ctrl_lines = fmt(ctrl)
    n_diff = sum(1 for a, b in zip(ctrl_lines, delivered) if a != b) + abs(len(ctrl_lines) - len(delivered))
    gate_rows.append(dict(model=model, variable='TXT_ASSEMBLED', n=len(delivered), nan_pattern_match=None,
                          max_abs_diff_full_precision=None, conversion=f'text lines differing: {n_diff}', calendar=''))
    print(f"{model}: rows={len(delivered)} txt_lines_differing={n_diff}", flush=True)

tag = "_".join(ONLY)
pd.DataFrame(gate_rows).to_csv(FRAG / f'gate_{tag}.csv', index=False)
pd.DataFrame(prov).to_csv(FRAG / f'prov_{tag}.csv', index=False)
print("GATE rows:"); print(pd.DataFrame(gate_rows).to_string())
print("distance station->perturbed centre (km):", round(haversine_km(ST_LAT, ST_LON, 42.041667, -82.958336), 2))

"""Addendum C, Stage 1 gate, recomputed entire from fresh control pulls: pull ONLY the London control
cell (lat index 24, lon index 718) from the PCIC OPeNDAP source, following addC_extract.py's construction
exactly (same catalogue URLs, same cftime date axis on each model's own calendar, same unit-conversion
rule, same one-decimal tab-separated text format, columns pulled in blocks of 1,826 days — the block
size is part of the construction, not a free parameter, because the OPeNDAP service silently truncates
any larger hyperslab response at 1,826 values, which is how the corrupted fast-transfer products of the
first attempt arose and why they were discarded), and compute both halves of the Stage 1 gate from that
one pull:
gate (i), the control series formatted as text against the delivered txt/LONDON_<model>.txt files, line
by line; and gate (ii), the full-precision control values against the archived London raw subset NetCDF
files, element by element with the missing-value patterns compared.

Why this script exists: in the first addC_extract.py run, two filename substitutions failed silently
(the perturbed text writer kept the addB file name HARROWP_<model>.txt, and the gate-(i) reader compared
the London control text against the delivered HARROW files, a meaningless comparison). The pulls
themselves used the correct London indices throughout. Because the slow extraction processes were later
stopped once the fast-transfer variant had produced the perturbed products, their in-memory gate rows
were never written to disk, so both gate halves are recomputed here from a single fresh control pull per
model, which is the same comparison the in-run gate would have reported. This script also checks, for
each model, that the perturbed text file (renamed to LONDONP_<model>.txt where the first run wrote the
old name) is exactly the text formatting of the saved perturbed raw subsets
out_addC/raw_nc/LONDON_P_<model>_<var>.nc."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr, cftime

FIN = Path('/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final')
OUT = Path('/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_claude/out_addC')
IY, IX_T = 24, 718
MODELS = ["ACCESS-ESM1-5", "BCC-CSM2-MR", "CanESM5", "CNRM-ESM2-1", "EC-Earth3-Veg",
          "GFDL-ESM4", "INM-CM5-0", "MIROC-ES2L", "MRI-ESM2-0", "NorESM2-LM"]
VARS = ["pr", "tasmax", "tasmin"]


def conversion_for(var, units):
    u = (units or "").strip()
    if var == "pr":
        if u == "kg m-2 s-1":
            return 86400.0, 0.0
        if u in ("kg m-2 d-1", "kg m-2 day-1", "mm/day", "mm d-1"):
            return 1.0, 0.0
        return None
    if u in ("K", "Kelvin"):
        return 1.0, -273.15
    if u in ("degC", "degrees_C", "Celsius", "deg_C"):
        return 1.0, 0.0
    return None


meta = pd.read_csv(FIN / 'metadata.csv')
meta = meta[meta.station == 'LONDON'].set_index(['model', 'variable'])
ONLY = sys.argv[1:] if len(sys.argv) > 1 else MODELS
rows = []
for model in ONLY:
    ctrl = {}
    dates_ref = None
    for var in VARS:
        m = meta.loc[(model, var)]
        url = m['url']
        ds = xr.open_dataset(url, engine="pydap", decode_times=False)
        t_units = ds["time"].attrs.get("units", ""); t_cal = ds["time"].attrs.get("calendar", "")
        times_raw = np.asarray(ds["time"].values, dtype=float)
        dates = list(cftime.num2date(times_raw, t_units, calendar=t_cal))
        conv = conversion_for(var, ds[var].attrs.get("units", ""))
        assert conv is not None
        factor, offset = conv
        n = len(times_raw); a = np.full(n, np.nan)
        for s0 in range(0, n, 1826):
            s1 = min(n, s0 + 1826)
            for attempt in range(1, 5):
                try:
                    blk = ds[var].isel(lat=IY, lon=IX_T, time=slice(s0, s1)).values
                    break
                except Exception:
                    if attempt == 4: raise
                    time.sleep(15 * attempt)
                    try: ds.close()
                    except Exception: pass
                    ds = xr.open_dataset(url, engine="pydap", decode_times=False)
                    blk = None
            blk = np.ma.filled(np.ma.asarray(blk, dtype=float), np.nan) if np.ma.isMaskedArray(blk) else np.asarray(blk, dtype=float)
            a[s0:s1] = blk
        ds.close()
        if dates_ref is None:
            dates_ref = dates
        else:
            assert len(dates) == len(dates_ref) and all((x.year, x.month, x.day) == (y.year, y.month, y.day) for x, y in zip(dates, dates_ref))
        # gate (ii): full-precision control vs delivered raw subset NetCDF
        loc = xr.open_dataset(FIN / 'raw_nc' / m['raw_nc_file'], decode_times=False)
        a_loc = np.asarray(loc[var].values, dtype=float); loc.close()
        same_nan = bool((np.isnan(a) == np.isnan(a_loc)).all())
        finite = ~np.isnan(a) & ~np.isnan(a_loc)
        maxdiff = float(np.abs(a[finite] - a_loc[finite]).max()) if finite.any() else 0.0
        rows.append(dict(model=model, variable=var, n=len(a), nan_pattern_match=same_nan,
                         max_abs_diff_full_precision=maxdiff, calendar=t_cal))
        ctrl[var] = a * factor + offset

    def fmt(vals_by_var):
        lines = []
        for i, dt in enumerate(dates_ref):
            row = [f"{dt.year}", f"{dt.month}", f"{dt.day}"]
            for var in VARS:
                v = vals_by_var[var][i]
                row.append("-99.9" if np.isnan(v) else f"{v:.1f}")
            lines.append("\t".join(row))
        return lines

    delivered = (FIN / 'txt' / f"LONDON_{model}.txt").read_text().splitlines()
    ctrl_lines = fmt(ctrl)
    n_diff = sum(1 for a, b in zip(ctrl_lines, delivered) if a != b) + abs(len(ctrl_lines) - len(delivered))
    # perturbed text consistency: LONDONP text vs the saved perturbed raw subsets, formatted identically
    pert = {}
    for var in VARS:
        loc = xr.open_dataset(OUT / 'raw_nc' / f"LONDON_P_{model}_{var}.nc", decode_times=False)
        pert[var] = np.asarray(loc[var].values, dtype=float); loc.close()
    pert_lines_saved = (OUT / 'txt' / f"LONDONP_{model}.txt").read_text().splitlines()
    n_diff_p = sum(1 for a, b in zip(fmt(pert), pert_lines_saved) if a != b) + abs(len(pert_lines_saved) - len(fmt(pert)))
    rows.append(dict(model=model, delivered_lines=len(delivered), control_text_lines_differing=n_diff,
                     perturbed_text_vs_saved_subsets_lines_differing=n_diff_p))
    print(f"{model}: control text lines differing = {n_diff} of {len(delivered)}; perturbed txt vs saved subsets differing = {n_diff_p}", flush=True)

tag = "_".join(ONLY)
pd.DataFrame(rows).to_csv(OUT / 'frag' / f'gate_i_{tag}.csv', index=False)
print(pd.DataFrame(rows).to_string())

#!/usr/bin/env python3
"""Pass 1 independent recompute. Does not read authors' R steps, results workbooks, or Climpact output."""
from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    ALL_INDICES, CAL365, CLIMPACT_LATLON, MODELS, OUT, PERIODS, PREC_INDICES,
    RETAINED_18, RETAINED_19, STATION_COORDS_PRINTED, STATIONS, TEMP_INDICES,
    TEMP_REF, PREC_REF, PCIC_META,
)
from io_daily import (
    authors_merged, authors_model, compare_model_files, integrity, merge_observations, pcic_model,
)
from homogenise import apply_breaks, auto_detect, compare_series
from indices import compute_annual, compute_monthly
from stats import (
    arrow_from_delta, classify_envelope_613, classify_envelope_v7, consensus_count,
    delta_medians, ensemble_stats, monthly_median_value, monthly_quartile_value,
    monthly_wilcoxon, pass_counts, pass_table, period_median, period_values,
    pooled_period_values, process_confidence, skill_vs_change, wilcoxon_r,
)

OUT.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def _annual_job(job):
    s, lab, df, lat, clip = job
    t1 = time.time()
    ann = compute_annual(df, lat, clip_tn_to_tx=clip)
    return s, lab, clip, ann, time.time() - t1


def save_df(df, name):
    p = OUT / name
    df.to_csv(p, index=False)
    return p


def main():
    t0 = time.time()
    report = {"notes": [], "merge": {}, "pcic": {}, "integrity": {}, "homog": {}}

    # ----- merge -----
    log("== merge observations (printed splice rules) ==")
    merged_printed = merge_observations("printed")
    merged_codeish = merge_observations("code_readme")
    auth_m = authors_merged()
    merge_cmp = []
    for s in STATIONS:
        c1 = compare_series(merged_printed[s], auth_m[s])
        c2 = compare_series(merged_codeish[s], auth_m[s])
        c1["station"] = s
        c1["rule"] = "printed"
        c2["station"] = s
        c2["rule"] = "code_readme"
        merge_cmp.append(c1)
        merge_cmp.append(c2)
        log(f"  {s} printed vs authors tx_rmse={c1['tx_rmse']:.4f} tn_rmse={c1['tn_rmse']:.4f} pr_n_diff={c1['pr_n_diff_gt_0.05']}")
        log(f"  {s} code_readme vs authors tx_rmse={c2['tx_rmse']:.4f} tn_rmse={c2['tn_rmse']:.4f} pr_n_diff={c2['pr_n_diff_gt_0.05']}")
    save_df(pd.DataFrame(merge_cmp), "merge_compare.csv")
    report["merge"]["compare"] = merge_cmp

    # Executed splice (station file after 2017 at London) matches the package merged files.
    # Printed splice (CS from 2002-09-19 through 2023) leaves London 2018-2023 empty.
    # Primary analysis uses the executed reconstruction; printed merge is a method branch.
    obs_merged = merged_codeish
    for s in STATIONS:
        n_print = int(merged_printed[s].tx.notna().sum())
        n_exec = int(merged_codeish[s].tx.notna().sum())
        n_auth = int(auth_m[s].tx.notna().sum())
        log(f"  {s} finite tx printed={n_print} executed={n_exec} authors_merged={n_auth}")

    # ----- homogenise -----
    log("== homogenise (19-break and 18-break) + auto-detect ==")
    auto = auto_detect(obs_merged)
    save_df(pd.DataFrame(auto, columns=["station", "var", "year", "month", "type", "step", "t"]), "auto_detect.csv")
    report["homog"]["auto_n"] = len(auto)
    report["homog"]["auto"] = [list(x) for x in auto]
    homog19 = apply_breaks(obs_merged, RETAINED_19)
    homog18 = apply_breaks(obs_merged, RETAINED_18)
    hcmp = []
    for s in STATIONS:
        d = compare_series(homog19[s], homog18[s], cols=("tx", "tn"))
        d["station"] = s
        d["n_tn_clipped_19"] = homog19[s].attrs.get("n_tn_clipped", None)
        d["n_tn_clipped_18"] = homog18[s].attrs.get("n_tn_clipped", None)
        hcmp.append(d)
        log(f"  {s} 19vs18 tn_mad={d['tn_mad']:.4f} nclip19={d['n_tn_clipped_19']}")
    save_df(pd.DataFrame(hcmp), "homog_18vs19.csv")

    # ----- PCIC vs authors model files -----
    log("== PCIC vs authors daily model files ==")
    pcic_cmp = compare_model_files()
    save_df(pcic_cmp, "pcic_vs_authors_models.csv")
    report["pcic"]["n_byte_identical"] = int(pcic_cmp.byte_identical.sum())
    report["pcic"]["n_pr_eq"] = int(pcic_cmp["pr_eq_0.05"].sum())
    report["pcic"]["n_tx_eq"] = int(pcic_cmp["tx_eq_0.05"].sum())
    report["pcic"]["n_tn_eq"] = int(pcic_cmp["tn_eq_0.05"].sum())
    log(f"  byte-identical {report['pcic']['n_byte_identical']}/30; pr_eq {report['pcic']['n_pr_eq']}/30")

    # ----- load models (PCIC independent provenance; fall back to authors if needed) -----
    models = {}
    integ_rows = []
    for s in STATIONS:
        for m in MODELS:
            try:
                df = pcic_model(s, m)
                src = "pcic"
            except Exception:
                df = authors_model(s, m)
                src = "authors"
            models[(s, m)] = df
            cal = "365" if m in CAL365 else "gregorian"
            info = integrity(df, cal)
            info.update({"station": s, "model": m, "src": src})
            integ_rows.append(info)
    for s in STATIONS:
        for lab, df in (("merged", obs_merged[s]), ("homog19", homog19[s]), ("homog18", homog18[s])):
            info = integrity(df, "gregorian")
            info.update({"station": s, "model": lab, "src": "obs"})
            integ_rows.append(info)
    integ = pd.DataFrame(integ_rows)
    save_df(integ, "integrity.csv")
    report["integrity"]["model_tmin_gt_tmax_total"] = int(integ[integ.src != "obs"].tmin_gt_tmax.sum())
    report["integrity"]["obs_tmin_gt_tmax"] = integ[integ.src == "obs"][["station", "model", "tmin_gt_tmax"]].to_dict("records")
    log(f"  model tmin>tmax total days: {report['integrity']['model_tmin_gt_tmax_total']}")

    # grid cells from PCIC metadata
    meta = pd.read_csv(PCIC_META)
    grid = (meta[meta.variable == "tasmax"][["station", "model", "cell_lat", "cell_lon", "distance_to_station_km", "calendar", "grid_cell_lat_index", "grid_cell_lon_index"]]
            .drop_duplicates())
    save_df(grid, "pcic_grid_cells.csv")

    # also indices on printed-rule merge (London 2018-2023 empty)
    log("== annual indices (parallel) ==")
    jobs = []
    for s in STATIONS:
        lat = CLIMPACT_LATLON[s][0]
        jobs.append((s, "merged", obs_merged[s], lat, False))
        jobs.append((s, "merged_printed", merged_printed[s], lat, False))
        jobs.append((s, "homog19", homog19[s], lat, False))
        jobs.append((s, "homog18", homog18[s], lat, False))
        for m in MODELS:
            jobs.append((s, m, models[(s, m)], lat, False))
            jobs.append((s, f"{m}_clip", models[(s, m)], lat, True))

    annual = {}
    annual_clip = {}

    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(_annual_job, j) for j in jobs]
        for i, fut in enumerate(as_completed(futs), 1):
            s, lab, clip, ann, dt = fut.result()
            if clip:
                annual_clip[(s, lab.replace("_clip", ""))] = ann
            else:
                annual[(s, lab)] = ann
            save_df(ann, f"annual_{s}_{lab}.csv")
            log(f"  [{i}/{len(jobs)}] {s} {lab} {dt:.1f}s")

    # ----- monthly (obs homog19 + ref models + next-best sensitivity) -----
    log("== monthly indices ==")
    monthly = {}
    for s in STATIONS:
        lat = CLIMPACT_LATLON[s][0]
        monthly[(s, "homog19")] = compute_monthly(homog19[s], lat)
        monthly[(s, "merged")] = compute_monthly(obs_merged[s], lat)
        save_df(monthly[(s, "homog19")], f"monthly_{s}_homog19.csv")
        for m in {TEMP_REF[s], PREC_REF[s], "NorESM", "EC", "BCC", "ACCESS", "MIROC"}:
            monthly[(s, m)] = compute_monthly(models[(s, m)], lat)
            save_df(monthly[(s, m)], f"monthly_{s}_{m}.csv")
            log(f"  monthly {s} {m}")

    # ----- analysis -----
    log("== Wilcoxon / envelope / consensus / projections ==")
    obs_primary = {s: annual[(s, "homog19")] for s in STATIONS}
    obs_merged_ann = {s: annual[(s, "merged")] for s in STATIONS}
    obs_18 = {s: annual[(s, "homog18")] for s in STATIONS}

    def models_of(s, store=annual):
        return {m: store[(s, m)] for m in MODELS}

    # pass counts
    pass_rows = []
    ptable = {}
    for s in STATIONS:
        ptable[s] = pass_table(obs_primary[s], models_of(s), ALL_INDICES)
        for grp, idxs in (("temp", TEMP_INDICES), ("prec", PREC_INDICES)):
            pc = pass_counts(ptable[s], idxs)
            pc["station"] = s
            pc["group"] = grp
            pass_rows.append(pc)
    pass_df = pd.concat(pass_rows, ignore_index=True)
    save_df(pass_df, "pass_counts.csv")

    # Wilcoxon sensitivity: continuity off
    def pass_counts_alt(obs_ann, model_annuals, indices, continuity):
        rows = []
        for m in MODELS:
            h = p = 0
            for idx in indices:
                for per, acc in (("Historical", "h"), ("Present", "p")):
                    ov = period_values(obs_ann, idx, per)
                    mv = period_values(model_annuals[m], idx, per)
                    pv = wilcoxon_r(ov, mv, continuity=continuity)
                    if np.isfinite(pv) and pv >= 0.05:
                        if per == "Historical":
                            h += 1
                        else:
                            p += 1
            rows.append({"model": m, "Historical": h, "Present": p, "cum": h + p})
        return pd.DataFrame(rows)

    alt_rows = []
    for s in STATIONS:
        for cont, lab in ((True, "cont_on"), (False, "cont_off")):
            for grp, idxs in (("temp", TEMP_INDICES), ("prec", PREC_INDICES)):
                pc = pass_counts_alt(obs_primary[s], models_of(s), idxs, cont)
                pc["station"] = s
                pc["group"] = grp
                pc["setting"] = lab
                alt_rows.append(pc)
    save_df(pd.concat(alt_rows, ignore_index=True), "pass_counts_wilcoxon_sensitivity.csv")

    # envelope both forks, H->P
    env_rows = []
    env613 = {s: {} for s in STATIONS}
    envv7 = {s: {} for s in STATIONS}
    for s in STATIONS:
        for idx in ALL_INDICES:
            d_obs, _, _ = delta_medians(obs_primary[s], idx, "Historical", "Present")
            d_mods = []
            for m in MODELS:
                d, _, _ = delta_medians(annual[(s, m)], idx, "Historical", "Present")
                d_mods.append(d)
            c613, dmin, dmax, dmed = classify_envelope_613(d_obs, d_mods)
            cv7, dmin7, dmax7 = classify_envelope_v7(d_obs, d_mods)
            env613[s][idx] = {"class": c613, "d_obs": d_obs, "dmin": dmin, "dmax": dmax, "dmed": dmed}
            envv7[s][idx] = {"class": cv7, "d_obs": d_obs, "dmin": dmin7, "dmax": dmax7}
            env_rows.append({
                "station": s, "index": idx, "d_obs": d_obs,
                "dmin": dmin7, "dmax": dmax7, "dmed": dmed,
                "class_613": c613, "class_v7": cv7,
                "group": "temp" if idx in TEMP_INDICES else "prec",
            })
    env_df = pd.DataFrame(env_rows)
    save_df(env_df, "envelope.csv")

    # homog dependence of envelope
    env_alt = []
    for lab, store in (("merged", obs_merged_ann), ("homog18", obs_18)):
        for s in STATIONS:
            for idx in ALL_INDICES:
                d_obs, _, _ = delta_medians(store[s], idx, "Historical", "Present")
                d_mods = [delta_medians(annual[(s, m)], idx, "Historical", "Present")[0] for m in MODELS]
                cv7, dmin, dmax = classify_envelope_v7(d_obs, d_mods)
                env_alt.append({"obs_branch": lab, "station": s, "index": idx, "d_obs": d_obs, "class_v7": cv7})
    save_df(pd.DataFrame(env_alt), "envelope_obs_branches.csv")

    # consensus
    cons_rows = []
    cons = {s: {} for s in STATIONS}
    for s in STATIONS:
        for idx in ALL_INDICES:
            for p2 in ("Near", "Far"):
                direction, ups, downs, _ = consensus_count(models_of(s), idx, "Historical", p2, k=8)
                cons_rows.append({
                    "station": s, "index": idx, "period": p2,
                    "consensus": direction, "n_up_sig": ups, "n_down_sig": downs,
                    "group": "temp" if idx in TEMP_INDICES else "prec",
                })
                cons[s].setdefault(idx, {})[p2] = direction
    cons_df = pd.DataFrame(cons_rows)
    save_df(cons_df, "consensus.csv")

    # leave-one-out envelope
    loo_rows = []
    for s in STATIONS:
        for left in MODELS:
            keep = [m for m in MODELS if m != left]
            n_b = 0
            for idx in ALL_INDICES:
                d_obs = envv7[s][idx]["d_obs"]
                d_mods = [delta_medians(annual[(s, m)], idx, "Historical", "Present")[0] for m in keep]
                cv7, _, _ = classify_envelope_v7(d_obs, d_mods)
                if cv7 == "Bounded":
                    n_b += 1
            loo_rows.append({"station": s, "left_out": left, "bounded": n_b, "of": 44})
    save_df(pd.DataFrame(loo_rows), "envelope_loo.csv")

    # envelope null: permute observed changes across indices within station
    rng = np.random.default_rng(20261107)
    null_rows = []
    for s in STATIONS:
        dobs = np.array([envv7[s][i]["d_obs"] for i in ALL_INDICES], float)
        dmod = {i: np.array([delta_medians(annual[(s, m)], i, "Historical", "Present")[0] for m in MODELS], float)
                for i in ALL_INDICES}
        rates = []
        for _ in range(2000):
            perm = rng.permutation(dobs)
            nb = 0
            for k, idx in enumerate(ALL_INDICES):
                cv7, _, _ = classify_envelope_v7(perm[k], dmod[idx])
                if cv7 == "Bounded":
                    nb += 1
            rates.append(nb)
        null_rows.append({
            "station": s, "obs_bounded": int((env_df[(env_df.station == s) & (env_df.class_v7 == "Bounded")].shape[0])),
            "null_mean": float(np.mean(rates)), "null_p95": float(np.percentile(rates, 95)),
            "null_p05": float(np.percentile(rates, 5)), "null_min": int(np.min(rates)), "null_max": int(np.max(rates)),
        })
    save_df(pd.DataFrame(null_rows), "envelope_null_permute.csv")

    # projections / period medians
    proj_rows = []
    for s in STATIONS:
        for idx in ALL_INDICES:
            for p2 in ("Present", "Near", "Far"):
                es = ensemble_stats(models_of(s), idx, "Historical", p2)
                proj_rows.append({
                    "station": s, "index": idx, "period": p2,
                    "ens_median_delta": es["ens_median_delta"],
                    "ens_min_delta": es["ens_min_delta"],
                    "ens_max_delta": es["ens_max_delta"],
                    "pooled_delta": es["pooled_delta"],
                    "pooled_median_hist": es["pooled_median"]["Historical"],
                    "pooled_median_p2": es["pooled_median"][p2],
                    "med_of_meds_hist": es["median_of_model_medians"]["Historical"],
                    "med_of_meds_p2": es["median_of_model_medians"][p2],
                    "min_model_med_p2": es["min_model_median"][p2],
                    "max_model_med_p2": es["max_model_median"][p2],
                    "obs_median_hist": period_median(obs_primary[s], idx, "Historical") if p2 == "Present" else np.nan,
                    "obs_median_pres": period_median(obs_primary[s], idx, "Present") if p2 == "Present" else np.nan,
                    "obs_delta": delta_medians(obs_primary[s], idx, "Historical", "Present")[0] if p2 == "Present" else np.nan,
                })
    proj_df = pd.DataFrame(proj_rows)
    save_df(proj_df, "projections.csv")

    # period medians all four periods (boxplot numbers)
    pmed_rows = []
    for s in STATIONS:
        for idx in ALL_INDICES:
            for per in PERIODS:
                es = ensemble_stats(models_of(s), idx, "Historical", per)
                pmed_rows.append({
                    "station": s, "index": idx, "period": per,
                    "pooled_median": es["pooled_median"][per],
                    "med_of_model_medians": es["median_of_model_medians"][per],
                    "min_model_median": es["min_model_median"][per],
                    "max_model_median": es["max_model_median"][per],
                    "obs_median": period_median(obs_primary[s], idx, per) if per in ("Historical", "Present") else np.nan,
                })
    save_df(pd.DataFrame(pmed_rows), "period_medians.csv")

    # arrows H->P for obs, models, ensemble (pooled)
    arrow_rows = []
    for s in STATIONS:
        for idx in ALL_INDICES:
            for src, ann in [("Observed", obs_primary[s]), *[ (m, annual[(s, m)]) for m in MODELS ]]:
                d, m1, m2 = delta_medians(ann, idx, "Historical", "Present")
                p = wilcoxon_r(period_values(ann, idx, "Historical"), period_values(ann, idx, "Present"))
                direction, sig = arrow_from_delta(d, p)
                arrow_rows.append({"station": s, "index": idx, "source": src, "comp": "H_P",
                                   "delta": d, "p": p, "arrow": direction, "sig": sig, "m1": m1, "m2": m2})
            # ensemble pooled
            a = pooled_period_values(models_of(s), idx, "Historical")
            b = pooled_period_values(models_of(s), idx, "Present")
            d = (np.median(b) - np.median(a)) if a.size and b.size else np.nan
            p = wilcoxon_r(a, b)
            direction, sig = arrow_from_delta(d, p)
            arrow_rows.append({"station": s, "index": idx, "source": "Ensemble", "comp": "H_P",
                               "delta": d, "p": p, "arrow": direction, "sig": sig,
                               "m1": float(np.median(a)) if a.size else np.nan,
                               "m2": float(np.median(b)) if b.size else np.nan})
            for p2, lab in (("Near", "H_N"), ("Far", "H_F")):
                for m in MODELS:
                    d, m1, m2 = delta_medians(annual[(s, m)], idx, "Historical", p2)
                    pv = wilcoxon_r(period_values(annual[(s, m)], idx, "Historical"),
                                    period_values(annual[(s, m)], idx, p2))
                    direction, sig = arrow_from_delta(d, pv)
                    arrow_rows.append({"station": s, "index": idx, "source": m, "comp": lab,
                                       "delta": d, "p": pv, "arrow": direction, "sig": sig, "m1": m1, "m2": m2})
                a = pooled_period_values(models_of(s), idx, "Historical")
                b = pooled_period_values(models_of(s), idx, p2)
                d = (np.median(b) - np.median(a)) if a.size and b.size else np.nan
                pv = wilcoxon_r(a, b)
                direction, sig = arrow_from_delta(d, pv)
                arrow_rows.append({"station": s, "index": idx, "source": "Ensemble", "comp": lab,
                                   "delta": d, "p": pv, "arrow": direction, "sig": sig,
                                   "m1": float(np.median(a)) if a.size else np.nan,
                                   "m2": float(np.median(b)) if b.size else np.nan})
    save_df(pd.DataFrame(arrow_rows), "arrows.csv")

    # skill vs change
    svc = skill_vs_change(ptable, envv7, n_pass_skill=10)
    with open(OUT / "skill_vs_change.json", "w") as f:
        json.dump(svc, f, indent=2)
    log(f"  skill vs change: {svc}")

    # process confidence
    pc = process_confidence(envv7, cons)
    with open(OUT / "process_confidence.json", "w") as f:
        json.dump(pc, f, indent=2)

    # monthly headlines
    log("== monthly quartile / median changes ==")
    mrows = []
    months_keep = [1, 2, 3, 6, 7, 8, 9]
    m_indices = ["TMm", "TXx", "TXn", "ID", "SU", "RX1day", "RX5day", "PRCPTOT", "R10mm", "CDD",
                 "SPI3", "SPI6", "SPEI3", "SPEI6"]
    for s in STATIONS:
        for src in ["homog19", TEMP_REF[s], PREC_REF[s], "ACCESS", "MIROC", "NorESM", "EC", "BCC"]:
            if (s, src) not in monthly:
                continue
            md = monthly[(s, src)]
            for idx in m_indices:
                for mo in months_keep:
                    for p1, p2, lab in (("Historical", "Present", "H_P"), ("Near", "Far", "N_F"),
                                        ("Historical", "Far", "H_F"), ("Historical", "Near", "H_N")):
                        lower = idx == "TXn"
                        q1 = monthly_quartile_value(md, idx, mo, p1, lower=lower)
                        q2 = monthly_quartile_value(md, idx, mo, p2, lower=lower)
                        med1 = monthly_median_value(md, idx, mo, p1)
                        med2 = monthly_median_value(md, idx, mo, p2)
                        pv = monthly_wilcoxon(md, idx, mo, p1, p2)
                        mrows.append({
                            "station": s, "source": src, "index": idx, "month": mo, "comp": lab,
                            "q1": q1, "q2": q2, "dq": (q2 - q1) if np.isfinite(q1) and np.isfinite(q2) else np.nan,
                            "med1": med1, "med2": med2,
                            "dmed": (med2 - med1) if np.isfinite(med1) and np.isfinite(med2) else np.nan,
                            "p": pv,
                        })
    save_df(pd.DataFrame(mrows), "monthly_changes.csv")

    # headline summaries
    def bounded_count(store_env):
        n = sum(1 for s in STATIONS for i in ALL_INDICES if store_env[s][i]["class"] in ("Bounded", "within"))
        return n

    n_v7 = int((env_df.class_v7 == "Bounded").sum())
    n_613_within = int((env_df.class_613 == "within").sum())
    n_613_rev = int((env_df.class_613 == "reversal_vs_median").sum())
    n_v7_rev = int((env_df.class_v7 == "Sign reversal").sum())
    headlines = {
        "bounded_v7": n_v7,
        "within_613": n_613_within,
        "reversals_613_vs_median": n_613_rev,
        "sign_reversals_v7": n_v7_rev,
        "skill_vs_change": svc,
        "seconds": time.time() - t0,
    }
    # TMm far deltas
    tm = proj_df[(proj_df.index == "TMm") | (proj_df["index"] == "TMm")]
    headlines["TMm_FF_ens_median_delta"] = {
        s: float(proj_df[(proj_df.station == s) & (proj_df["index"] == "TMm") & (proj_df.period == "Far")].ens_median_delta.iloc[0])
        for s in STATIONS
    }
    headlines["TMm_NF_ens_median_delta"] = {
        s: float(proj_df[(proj_df.station == s) & (proj_df["index"] == "TMm") & (proj_df.period == "Near")].ens_median_delta.iloc[0])
        for s in STATIONS
    }
    with open(OUT / "headlines.json", "w") as f:
        json.dump(headlines, f, indent=2, default=str)

    with open(OUT / "report_partial.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    log(f"DONE in {time.time()-t0:.1f}s  bounded_v7={n_v7}/132  within_613={n_613_within}/132  v7_rev={n_v7_rev}  613_rev={n_613_rev}")
    log(f"TMm FF deltas {headlines['TMm_FF_ens_median_delta']}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)

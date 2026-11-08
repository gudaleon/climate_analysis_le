#!/usr/bin/env python3
"""Pass 2: recompute analysis from the authors' annual index tables (Climpact products)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ALL_INDICES, MODELS, OUT, PKG613, PREC_INDICES, STATIONS, TEMP_INDICES
from stats import (
    classify_envelope_613, classify_envelope_v7, consensus_count, delta_medians,
    ensemble_stats, pass_counts, pass_table, period_median, period_values,
    skill_vs_change, wilcoxon_r, arrow_from_delta, pooled_period_values,
)

# Climpact names in the workbook (with possible leading space)
NAME_MAP = {
    "csdi": "CSDI6", "csdi3": "CSDI3", "wsdi": "WSDI6", "wsdi3": "WSDI3",
    "fd": "FD", "id": "ID", "su": "SU", "tr": "TR", "tnn": "TNn", "tnx": "TNx",
    "txx": "TXx", "txn": "TXn", "txm": "TXm", "tmm": "TMm", "tnm": "TNm",
    "tn10p": "TN10p", "tn90p": "TN90p", "tx10p": "TX10p", "tx90p": "TX90p",
    "dtr": "DTR", "dtrgt15": "DTRgt15", "gddgrow10": "GDDgrow10",
    "txb3tnb3": "TXb3TNb3", "txge30": "TXge30", "txgt50p": "TXgt50p",
    "tnltm20": "TNltm20", "gsl": "GSL", "cwa": "CWA", "cwf": "CWF",
    "hwa": "HWA", "hwf": "HWF", "prcptot": "PRCPTOT", "r10mm": "R10mm",
    "r20mm": "R20mm", "rx1day": "RX1day", "rx3day": "RX3day", "rx5day": "RX5day",
    "sdii": "SDII", "r95p": "R95p", "r95ptot": "R95pTOT", "r99p": "R99p",
    "r99ptot": "R99pTOT", "cdd": "CDD", "cwd": "CWD",
}


def load_station(st):
    p = PKG613 / "2_Data" / "3_Annual_index_tables" / f"All_{st}_observed_and_10_models_1950-2100.xlsx"
    df = pd.read_excel(p)
    df.columns = [str(c).strip() for c in df.columns]
    df["Index"] = df["Index"].astype(str).str.strip().str.lower().map(NAME_MAP)
    df = df.dropna(subset=["Index"])
    for c in ["Observed", *MODELS]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c] == -99.9, c] = np.nan
    return df


def col_to_annual(df, index, col):
    g = df[df.Index == index][["Year", col]].rename(columns={"Year": "year", col: index})
    return g


def main():
    tables = {s: load_station(s) for s in STATIONS}
    # build annual-like frames
    obs = {}
    models = {}
    for s in STATIONS:
        t = tables[s]
        o = t[["Year"]].drop_duplicates().rename(columns={"Year": "year"})
        for idx in ALL_INDICES:
            g = t[t.Index == idx]
            m = dict(zip(g.Year, g.Observed))
            o[idx] = o.year.map(m)
        obs[s] = o
        models[s] = {}
        for mname in MODELS:
            a = t[["Year"]].drop_duplicates().rename(columns={"Year": "year"})
            for idx in ALL_INDICES:
                g = t[t.Index == idx]
                mp = dict(zip(g.Year, g[mname]))
                a[idx] = a.year.map(mp)
            models[s][mname] = a

    ptable = {}
    pass_rows = []
    for s in STATIONS:
        ptable[s] = pass_table(obs[s], models[s], ALL_INDICES)
        for grp, idxs in (("temp", TEMP_INDICES), ("prec", PREC_INDICES)):
            pc = pass_counts(ptable[s], idxs)
            pc["station"] = s
            pc["group"] = grp
            pass_rows.append(pc)
    pass_df = pd.concat(pass_rows, ignore_index=True)
    pass_df.to_csv(OUT / "pass2_author_tables_pass_counts.csv", index=False)
    print("PASS COUNTS FROM AUTHOR TABLES")
    print(pass_df.pivot_table(index="model", columns=["station", "group"], values="cum"))

    env_rows = []
    envv7 = {s: {} for s in STATIONS}
    env613 = {s: {} for s in STATIONS}
    for s in STATIONS:
        for idx in ALL_INDICES:
            d_obs, _, _ = delta_medians(obs[s], idx, "Historical", "Present")
            d_mods = [delta_medians(models[s][m], idx, "Historical", "Present")[0] for m in MODELS]
            c613, dmin, dmax, dmed = classify_envelope_613(d_obs, d_mods)
            cv7, dmin7, dmax7 = classify_envelope_v7(d_obs, d_mods)
            env613[s][idx] = {"class": c613, "d_obs": d_obs}
            envv7[s][idx] = {"class": cv7, "d_obs": d_obs, "dmin": dmin7, "dmax": dmax7}
            env_rows.append({
                "station": s, "index": idx, "d_obs": d_obs, "dmin": dmin7, "dmax": dmax7, "dmed": dmed,
                "class_613": c613, "class_v7": cv7,
            })
    env = pd.DataFrame(env_rows)
    env.to_csv(OUT / "pass2_author_tables_envelope.csv", index=False)
    print("\nENVELOPE v7")
    print(env.groupby(["station", "class_v7"]).size().unstack(fill_value=0))
    print("bounded", (env.class_v7 == "Bounded").sum(), "/132")
    print("613 within", (env.class_613 == "within").sum())
    print("613 reversal_vs_median", (env.class_613 == "reversal_vs_median").sum())
    print("v7 sign reversal", env[env.class_v7 == "Sign reversal"][["station", "index", "d_obs"]].to_string(index=False))
    print("out:")
    print(env[env.class_v7 != "Bounded"][["station", "index", "d_obs", "dmin", "dmax", "class_v7", "class_613"]].to_string(index=False))

    svc = skill_vs_change(ptable, envv7, 10)
    print("\nSKILL VS CHANGE", svc)
    json.dump(svc, open(OUT / "pass2_author_tables_skill.json", "w"), indent=2)

    # consensus
    cons_rows = []
    for s in STATIONS:
        for idx in ALL_INDICES:
            for p2 in ("Near", "Far"):
                direction, ups, downs, _ = consensus_count(models[s], idx, "Historical", p2, k=8)
                cons_rows.append({"station": s, "index": idx, "period": p2, "consensus": direction,
                                  "group": "temp" if idx in TEMP_INDICES else "prec"})
    cons = pd.DataFrame(cons_rows)
    cons.to_csv(OUT / "pass2_author_tables_consensus.csv", index=False)
    for per in ("Near", "Far"):
        sub = cons[cons.period == per]
        print(per, "consensus not none", sub[sub.consensus != "none"].groupby("station").size().to_dict(),
              "prec", sub[(sub.group == "prec") & (sub.consensus != "none")].groupby("station").size().to_dict())

    # TMm deltas
    print("\nTMm ens median delta (median of 10 model median-changes)")
    for s in STATIONS:
        for p2 in ("Near", "Far"):
            es = ensemble_stats(models[s], "TMm", "Historical", p2)
            print(s, p2, "ens_med_delta", round(es["ens_median_delta"], 3),
                  "pooled_delta", round(es["pooled_delta"], 3),
                  "pooled_hist", round(es["pooled_median"]["Historical"], 2),
                  "pooled_p2", round(es["pooled_median"][p2], 2))

    # compare my homog19 TMm etc vs author observed
    print("\nOBS vs my homog19 (selected indices, period medians Historical)")
    for s in STATIONS:
        mine = pd.read_csv(OUT / f"annual_{s}_homog19.csv")
        for idx in ["TMm", "FD", "PRCPTOT", "SDII", "HWA", "HWF", "WSDI3", "CWA", "DTRgt15"]:
            a = period_median(obs[s], idx, "Historical")
            b = period_median(mine, idx, "Historical")
            print(f"  {s:7} {idx:10} author {a}  mine {b}")

if __name__ == "__main__":
    main()

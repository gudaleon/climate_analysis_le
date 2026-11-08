"""Daily-series I/O, independent station merge, PCIC comparison."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    NA, SRC, MERGED_AUTHORS, MODEL_AUTHORS, PCIC_TXT, MODEL_FULL, MODELS, STATIONS,
)


def _read_ymd_pr_tx_tn(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path, sep=r"\s+", header=None, names=["year", "month", "day", "pr", "tx", "tn"],
        engine="python",
    )
    for c in ("pr", "tx", "tn"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c] == NA, c] = np.nan
    return df


def read_daily(path: Path) -> pd.DataFrame:
    df = _read_ymd_pr_tx_tn(path)
    df["date"] = pd.to_datetime(dict(year=df.year, month=df.month, day=df.day), errors="coerce")
    return df


def eccc_csv(*names: str) -> pd.DataFrame:
    parts = []
    for n in names:
        d = pd.read_csv(SRC / n, dtype={"LOCAL_DATE": str}, low_memory=False)
        parts.append(pd.DataFrame({
            "date": pd.to_datetime(d["LOCAL_DATE"].str[:10], errors="coerce"),
            "pr": pd.to_numeric(d["TOTAL_PRECIPITATION"], errors="coerce"),
            "tx": pd.to_numeric(d["MAX_TEMPERATURE"], errors="coerce"),
            "tn": pd.to_numeric(d["MIN_TEMPERATURE"], errors="coerce"),
        }))
    d = pd.concat(parts, ignore_index=True).dropna(subset=["date"])
    d = d.drop_duplicates("date", keep="first").sort_values("date")
    return d.set_index("date")


def station_file(name: str) -> pd.DataFrame:
    d = _read_ymd_pr_tx_tn(SRC / name)
    d["date"] = pd.to_datetime(dict(year=d.year, month=d.month, day=d.day), errors="coerce")
    d = d.dropna(subset=["date"]).drop_duplicates("date", keep="first")
    return d.set_index("date")[["pr", "tx", "tn"]]


def _on_calendar(s: pd.DataFrame, days: pd.DatetimeIndex) -> pd.DataFrame:
    out = s.reindex(days)
    return out


def combine_first(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    out = a.copy()
    for c in ("pr", "tx", "tn"):
        out[c] = out[c].where(out[c].notna(), b[c])
    return out


def merge_observations(rule: str = "printed") -> dict[str, pd.DataFrame]:
    """Rebuild merged 1950-2023 series from ECCC sources.

    rule='printed': CS from 2002-09-19 through 2023 with airport fill (as printed).
    rule='code_readme': after 2017-12-31 fall back to the airport station file
    (documented in step-01 comments; used only as a sensitivity after Pass 1).
    """
    days = pd.date_range("1950-01-01", "2023-12-31", freq="D")

    air = _on_calendar(station_file("London_6144475_LONDON_INTL_AIRPORT_station_file.txt"), days)
    airE = _on_calendar(eccc_csv("London_6144475_LONDON_INTL_AIRPORT_ECCC_daily.csv"), days)
    cs = _on_calendar(eccc_csv("London_6144478_LONDON_CS_ECCC_daily.csv"), days)
    lon = air.copy()
    if rule == "printed":
        w = days >= "2002-09-19"
        lon.loc[w] = combine_first(cs.loc[w], airE.loc[w]).values
    else:
        w = (days >= "2002-09-19") & (days <= "2017-12-31")
        lon.loc[w] = combine_first(cs.loc[w], airE.loc[w]).values

    cda = _on_calendar(eccc_csv(
        "Harrow_6133360_HARROW_CDA_ECCC_daily_part1.csv",
        "Harrow_6133360_HARROW_CDA_ECCC_daily_part2.csv",
        "Harrow_6133360_HARROW_CDA_ECCC_daily_part3.csv",
    ), days)
    acs = _on_calendar(eccc_csv("Harrow_613CC60_HARROW_AUTOMATIC_ECCC_daily.csv"), days)
    auto = _on_calendar(eccc_csv("Harrow_6133362_HARROW_CDA_AUTO_ECCC_daily.csv"), days)
    har = cda.copy()
    m1 = (days >= "1992-01-01") & (days <= "2000-08-31")
    har.loc[m1] = acs.loc[m1].values
    # April 1992 filled from 6133360 (printed)
    apr = (days >= "1992-04-01") & (days <= "1992-04-30")
    har.loc[apr] = cda.loc[apr].values
    m2 = days >= "2000-09-01"
    har.loc[m2] = auto.loc[m2].values

    fer_sf = _on_calendar(station_file("Fergus_6142400_FERGUS_SHAND_DAM_station_file.txt"), days)
    fer_ec = _on_calendar(eccc_csv("Fergus_6142400_FERGUS_SHAND_DAM_ECCC_daily_2012.csv"), days)
    fer = fer_sf.copy()
    # 29 Sep 2012 precip missing in station file, taken from ECCC (step-02 README)
    d2012 = pd.Timestamp("2012-09-29")
    if d2012 in fer.index and pd.isna(fer.loc[d2012, "pr"]):
        fer.loc[d2012, "pr"] = fer_ec.loc[d2012, "pr"]

    def to_ymd(df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame({
            "year": days.year, "month": days.month, "day": days.day,
            "pr": df["pr"].to_numpy(), "tx": df["tx"].to_numpy(), "tn": df["tn"].to_numpy(),
            "date": days,
        })
        return out

    return {"London": to_ymd(lon), "Fergus": to_ymd(fer), "Harrow": to_ymd(har)}


def authors_merged() -> dict[str, pd.DataFrame]:
    names = {
        "London": "LONDON_merged_6144475_6144478.txt",
        "Fergus": "FERGUS_SHAND_DAM_6142400.txt",
        "Harrow": "HARROW_merged_6133360_613CC60_6133362.txt",
    }
    return {s: read_daily(MERGED_AUTHORS / n) for s, n in names.items()}


def authors_model(station: str, model: str) -> pd.DataFrame:
    return read_daily(MODEL_AUTHORS / f"{station}_{model}.txt")


def pcic_model(station: str, model: str) -> pd.DataFrame:
    return read_daily(PCIC_TXT / f"{station.upper()}_{MODEL_FULL[model]}.txt")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_model_files() -> pd.DataFrame:
    rows = []
    for st in STATIONS:
        for m in MODELS:
            a = MODEL_AUTHORS / f"{st}_{m}.txt"
            p = PCIC_TXT / f"{st.upper()}_{MODEL_FULL[m]}.txt"
            da, dp = _read_ymd_pr_tx_tn(a), _read_ymd_pr_tx_tn(p)
            n = min(len(da), len(dp))
            same_len = len(da) == len(dp)
            pr_eq = np.allclose(da.pr.fillna(NA).to_numpy()[:n], dp.pr.fillna(NA).to_numpy()[:n], atol=0.05, equal_nan=True)
            tx_eq = np.allclose(da.tx.fillna(NA).to_numpy()[:n], dp.tx.fillna(NA).to_numpy()[:n], atol=0.05, equal_nan=True)
            tn_eq = np.allclose(da.tn.fillna(NA).to_numpy()[:n], dp.tn.fillna(NA).to_numpy()[:n], atol=0.05, equal_nan=True)
            # max abs diff on overlapping finite
            def mad(x, y):
                x, y = x[:n], y[:n]
                mask = np.isfinite(x) & np.isfinite(y)
                return float(np.nanmax(np.abs(x[mask] - y[mask]))) if mask.any() else 0.0
            rows.append({
                "station": st, "model": m, "same_len": same_len,
                "n_authors": len(da), "n_pcic": len(dp),
                "pr_eq_0.05": pr_eq, "tx_eq_0.05": tx_eq, "tn_eq_0.05": tn_eq,
                "pr_mad": mad(da.pr.to_numpy(), dp.pr.to_numpy()),
                "tx_mad": mad(da.tx.to_numpy(), dp.tx.to_numpy()),
                "tn_mad": mad(da.tn.to_numpy(), dp.tn.to_numpy()),
                "sha_authors": file_sha256(a), "sha_pcic": file_sha256(p),
                "byte_identical": file_sha256(a) == file_sha256(p),
            })
    return pd.DataFrame(rows)


def integrity(df: pd.DataFrame, calendar: str) -> dict:
    pr, tx, tn = df.pr.to_numpy(), df.tx.to_numpy(), df.tn.to_numpy()
    years, months, days = df.year.to_numpy(), df.month.to_numpy(), df.day.to_numpy()
    n = len(df)
    tmin_gt_tmax = int(np.nansum((tn > tx) & np.isfinite(tn) & np.isfinite(tx)))
    neg_pr = int(np.nansum(pr < -1e-6))
    missing_pr = int(np.isnan(pr).sum())
    missing_tx = int(np.isnan(tx).sum())
    missing_tn = int(np.isnan(tn).sum())
    # date duplicates / gaps relative to stated calendar
    key = list(zip(years.tolist(), months.tolist(), days.tolist()))
    dup = n - len(set(key))
    feb29 = int(((months == 2) & (days == 29)).sum())
    return {
        "n": n, "tmin_gt_tmax": tmin_gt_tmax, "neg_pr": neg_pr,
        "missing_pr": missing_pr, "missing_tx": missing_tx, "missing_tn": missing_tn,
        "duplicate_ymd": dup, "feb29": feb29, "calendar": calendar,
    }

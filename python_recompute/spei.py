"""SPEI / SPI following Climpact 3.3 (climdex.spei / climdex.spi): monthly means of TX, TN and monthly
precipitation sums; Hargreaves PET (SPEI::hargreaves with Pre -> Droogers & Allen 2002 form);
rectangular accumulation; per-calendar-month fit on the reference period 1950-1986 using unbiased PWMs;
log-logistic (GLO) for SPEI, Gamma with zero-probability for SPI.  Independent re-implementation."""
import numpy as np
from scipy.stats import norm, gamma as gdist


def ra_month(lat, month):
    J = np.array([15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349])[month - 1]   # mid-month day of year
    phi = np.radians(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * J)
    delta = 0.409 * np.sin(2 * np.pi / 365 * J - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(delta))
    return 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def hargreaves(tmin, tmax, lat, pre, years, months):
    mlen = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])[months - 1].astype(float)
    Ra = ra_month(lat, months)
    Tr = tmax - tmin
    Tr = np.maximum(0, Tr)
    T = (tmin + tmax) / 2
    with np.errstate(invalid="ignore"):
        ab = Tr - 0.0123 * pre
        et = 0.0013 * 0.408 * Ra * (T + 17.0) * np.power(np.where(ab < 0, np.nan, ab), 0.76)
    et = np.where(np.isnan(et) & ~np.isnan(T) & ~np.isnan(pre), 0, et)
    et = np.maximum(et, 0) * mlen
    return et


def pwm_ub(x):
    x = np.sort(x); n = len(x); j = np.arange(1, n + 1)
    b0 = x.mean()
    b1 = np.sum((j - 1) / (n - 1) * x) / n
    b2 = np.sum((j - 1) * (j - 2) / ((n - 1) * (n - 2)) * x) / n
    return b0, b1, b2


def lmom(x):
    b0, b1, b2 = pwm_ub(x)
    l1 = b0; l2 = 2 * b1 - b0; l3 = 6 * b2 - 6 * b1 + b0
    return l1, l2, l3 / l2


def cdf_glo(x, l1, l2, t3):
    k = -t3
    a = l2 * np.sin(k * np.pi) / (k * np.pi)
    xi = l1 - a * (1 / k - np.pi / np.sin(k * np.pi))
    with np.errstate(invalid="ignore", divide="ignore"):
        arg = 1 - k * (x - xi) / a
        y = np.where(arg > 0, -np.log(np.where(arg > 0, arg, 1)) / k, np.nan)
        F = 1 / (1 + np.exp(-y))
        F = np.where(arg <= 0, 1.0 if k > 0 else 0.0, F)
    return F


def gam_par(l1, l2):
    t = l2 / l1
    if t < 0.5:
        z = np.pi * t * t
        al = (1 - 0.3080 * z) / (z - 0.05812 * z * z + 0.01765 * z ** 3)
    else:
        z = 1 - t
        al = (0.7213 * z - 0.5947 * z * z) / (1 - 2.1817 * z + 1.2113 * z * z)
    return al, l1 / al


def standardise(series, years, months, scale, dist, ref=(1950, 1986)):
    n = len(series)
    acc = np.full(n, np.nan)
    for t in range(scale - 1, n):
        acc[t] = np.sum(series[t - scale + 1:t + 1])        # NA propagates like R sum
    out = np.full(n, np.nan)
    inref = (years >= ref[0]) & (years <= ref[1])
    # SPEI::spei fits on window(data, ref.start, ref.end) re-accumulated inside the window
    refidx = np.where(inref)[0]
    acc_ref = np.full(n, np.nan)
    for t in refidx[scale - 1:]:
        acc_ref[t] = np.sum(series[t - scale + 1:t + 1])
    for m in range(1, 13):
        sel = (months == m)
        fit = acc_ref[sel & inref]; fit = fit[~np.isnan(fit)]
        if len(fit) < 3 or np.std(fit) == 0:
            continue
        x = acc[sel]
        if dist == "glo":
            l1, l2, t3 = lmom(fit)
            F = cdf_glo(x, l1, l2, t3)
        else:
            pze = np.mean(fit == 0)
            l1, l2, _ = lmom(fit)
            al, be = gam_par(l1, l2)
            F = pze + (1 - pze) * gdist.cdf(x, al, scale=be)
        z = norm.ppf(F)
        z[~np.isfinite(z)] = np.nan
        out[sel] = z
    return out


def spei_spi(mon_tx, mon_tn, mon_pr, years, months, lat):
    pet = hargreaves(mon_tn, mon_tx, lat, mon_pr, years, months)
    bal = mon_pr - pet
    r = {}
    for s in (3, 6):
        r[f"SPEI{s}"] = standardise(bal, years, months, s, "glo")
        r[f"SPI{s}"] = standardise(mon_pr, years, months, s, "gam")
    return r

"""Own implementation (Pass 1) of the step-02 documented homogenisation rules:
reference = mean of the other two stations (monthly means, <=3 missing days); candidate pruning on the
monthly difference series (type-1 removed when not significant, or marginal with |step|<0.2 C, weakest first,
re-test each time; type-0 never removed); daily quantile-matching adjustment (Mq=20, whole segments) to a base
segment (last segment if >=10 yr else longest); two rounds (round 2 uses round-1-adjusted neighbours; both rounds
adjust the raw series); tn clipped to tx where tn>tx; tx<tn days set missing before testing.
Detection branch: maximal-t binary segmentation on the difference series with AR(1) Monte-Carlo 95% critical values,
attribution by triangulation (+-18 months against each neighbour separately, not between neighbours).
This is an independent approximation of RHtestsV4 (PMT/StepSize/QMadj), not RHtests itself.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(20261107)
_crit = {}


def monthly_anom(df, v):
    x = df[v].copy()
    g = x.groupby([df.year, df.month])
    m = g.mean().where(g.apply(lambda s: s.isna().sum() <= 3))
    m.index.names = ["year", "month"]
    clim = m.groupby(level=1).transform("mean")
    return (m - clim)


def ar1(x):
    x = x[~np.isnan(x)]
    x = x - x.mean()
    return float(np.clip(np.sum(x[1:] * x[:-1]) / np.sum(x * x), 0, 0.9))


def tmax_stat(x, minseg=12):
    ok = ~np.isnan(x)
    y = x[ok]
    n = len(y)
    if n < 2 * minseg:
        return 0.0, None
    cs = np.cumsum(y); tot = cs[-1]; css = np.cumsum(y * y)
    k = np.arange(minseg, n - minseg + 1)
    m1 = cs[k - 1] / k; m2 = (tot - cs[k - 1]) / (n - k)
    sse = (css[k - 1] - k * m1 ** 2) + ((css[-1] - css[k - 1]) - (n - k) * m2 ** 2)
    s = np.sqrt(sse / (n - 2))
    t = np.abs(m1 - m2) / (s * np.sqrt(1 / k + 1 / (n - k)))
    i = int(np.argmax(t))
    pos = np.where(ok)[0][k[i] - 1]           # last index of first segment (in original indexing)
    return float(t[i]), pos


def crit(n, rho, q=0.95, nsim=400):
    key = (n // 24, round(rho, 1), q)
    if key not in _crit:
        vals = []
        nn = max(n, 30)
        for _ in range(nsim):
            e = RNG.standard_normal(nn)
            z = np.empty(nn); z[0] = e[0]
            for i in range(1, nn):
                z[i] = rho * z[i - 1] + e[i] * np.sqrt(1 - rho ** 2)
            vals.append(tmax_stat(z)[0])
        _crit[key] = float(np.quantile(vals, q))
    return _crit[key]


def detect(x, lo=0, out=None, depth=0):
    """binary segmentation; returns indices (end of first segment) of detected breaks."""
    if out is None:
        out = []
    t, pos = tmax_stat(x)
    if pos is None:
        return out
    n = int((~np.isnan(x)).sum())
    if t > crit(n, ar1(x)):
        out.append(lo + pos)
        detect(x[:pos + 1], lo, out, depth + 1)
        detect(x[pos + 1:], lo + pos + 1, out, depth + 1)
    return sorted(out)


def step_tests(x, bks):
    """for each break, t-test of mean difference of the adjacent segments with AR(1) effective n."""
    res = []
    edges = [-1] + sorted(bks) + [len(x) - 1]
    rho = ar1(x)
    for j, b in enumerate(sorted(bks)):
        a = x[edges[j] + 1:b + 1]; c = x[b + 1:edges[j + 2] + 1]
        a = a[~np.isnan(a)]; c = c[~np.isnan(c)]
        f = (1 - rho) / (1 + rho)
        na, nc = max(len(a) * f, 2), max(len(c) * f, 2)
        sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(c) - 1) * c.var(ddof=1)) / (len(a) + len(c) - 2))
        t = (c.mean() - a.mean()) / (sp * np.sqrt(1 / na + 1 / nc))
        from scipy.stats import t as tdist
        p = 2 * tdist.sf(abs(t), na + nc - 2)
        sig = "Yes" if p < 0.05 else ("?" if p < 0.10 else "No")
        res.append(dict(b=b, step=c.mean() - a.mean(), t=t, p=p, sig=sig))
    return res


def prune(x, cands):
    """cands: list of (index, type). returns retained list and log."""
    cur = list(cands); log = []
    while True:
        tests = step_tests(x, [c[0] for c in cur])
        bad = []
        for (idx, typ), r in zip(sorted(cur), tests):
            if typ == 1 and (r["sig"] == "No" or (r["sig"] == "?" and abs(r["step"]) < 0.2)):
                bad.append((abs(r["t"]), idx, typ, r))
        if not bad:
            return sorted(cur), log, tests
        bad.sort()
        _, idx, typ, r = bad[0]
        log.append(("removed", idx, r))
        cur = [c for c in cur if c[0] != idx]


def _anom(x, dates):
    doy = np.minimum(dates.dayofyear.values, 365)
    clim = pd.Series(x).groupby(doy).mean().reindex(range(1, 366)).values
    k = 15
    cc = np.concatenate([clim[-k:], clim, clim[:k]])
    cs = np.convolve(np.nan_to_num(cc, nan=np.nanmean(clim)), np.ones(2 * k + 1) / (2 * k + 1), "valid")
    return x - cs[doy - 1]


def _binmeans(v, mq):
    qs = np.linspace(0, 1, mq + 1); v = v[~np.isnan(v)]
    e = np.quantile(v, qs)
    return np.array([v[(v >= e[i]) & (v <= e[i + 1])].mean() for i in range(mq)])


def qm_adjust(daily, v, breaks_dates, mq=20, ref=None):
    """Quantile-matching relative to the reference: adj(q) = [Qt_base-Qt_seg](q) - [Qr_base-Qr_seg](q),
    so that climate change shared with the neighbours is not removed (RHtests estimates adjustments from the
    base-minus-reference series). ref: daily reference series (mean of neighbours) aligned to daily.index."""
    x = daily[v].values.astype(float)
    dates = daily.index
    an = _anom(x, dates)
    ra = _anom(ref, dates) if ref is not None else np.zeros_like(x)
    edges = [dates[0]] + sorted(breaks_dates) + [dates[-1] + pd.Timedelta(days=1)]
    segs = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]
    lens = [(e - s).days / 365.25 for s, e in segs]
    base = len(segs) - 1 if lens[-1] >= 10 else int(np.argmax(lens))
    bm = (dates >= segs[base][0]) & (dates < segs[base][1])
    bq = _binmeans(an[bm], mq); rbq = _binmeans(ra[bm], mq)
    qs = np.linspace(0, 1, mq + 1); mids = (qs[:-1] + qs[1:]) / 2
    out = x.copy()
    for i, (s, e) in enumerate(segs):
        if i == base:
            continue
        m = (dates >= s) & (dates < e)
        mm = m & ~np.isnan(an)
        adj = (bq - _binmeans(an[m], mq)) - (rbq - _binmeans(ra[m], mq))
        r = pd.Series(an[mm]).rank(pct=True).values
        out[np.where(mm)[0]] = x[mm] + np.interp(r, mids, adj)
    return out

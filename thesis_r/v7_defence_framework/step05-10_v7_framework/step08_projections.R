# Step 08 (v7 framework, Table C1): pooled projections and model consensus.
# C1: for every station, index and period the values of all years and models are pooled and
# summarised by median, Q1, Q3 and the number of outliers (beyond 1.5 IQR). The Historical and
# Present pools also include the observations (as in the thesis); Near and Far are models only.
# The Far-minus-Historical change of the median and the Far/Historical IQR ratio give the label
# "<Increase|Decrease|No Shift> (<Spread Contracted|Spread Expanded|Stable Spread>)".
# Consensus: an index counts when at least 8 of the 10 models show a
# significant (Wilcoxon p < 0.05) shift from their own Historical window in the same direction.
# Inputs : 2_Data/3_Annual_index_tables/All_<station>_observed_and_10_models_1950-2100.xlsx
# Outputs: 3_Code/output/v7_step08_projections/C1_projections.csv
#          3_Code/output/v7_step08_projections/model_consensus.csv
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step08_projections.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
od <- out_dir("v7_step08_projections")

# pooled summary of the given columns of one index in one period
pooled <- function(g, cols, p) {
  r <- PERIODS[[p]]; v <- unlist(g[g$Year >= r[1] & g$Year <= r[2], cols], use.names = FALSE); v <- v[!is.na(v)]
  q <- quantile(v, c(0.25, 0.5, 0.75), type = 7, names = FALSE); iqr <- q[3] - q[1]
  c(median = q[2], Q1 = q[1], Q3 = q[3], outliers = sum(v < q[1] - 1.5 * iqr | v > q[3] + 1.5 * iqr))
}
c1 <- function(x) {
  R <- list()
  for (k in sort(unique(x$Index), method = "radix")) {
    g <- x[x$Index == k, ]; r <- data.frame(Index = k)
    for (p in names(PERIODS)) {
      cols <- if (p %in% c("Hist", "Pres")) c("Observed", MODELS) else MODELS
      s <- pooled(g, cols, p)
      for (n in names(s)) r[[paste0(p, "_", n)]] <- s[[n]]
    }
    r$delta_m <- r$Far_median - r$Hist_median
    ih <- r$Hist_Q3 - r$Hist_Q1; iff <- r$Far_Q3 - r$Far_Q1
    r$IQR_ratio <- if (ih > 0) iff / ih else if (iff > 0) NA_real_ else 1
    sh <- if (r$delta_m > 0) "Increase" else if (r$delta_m < 0) "Decrease" else "No Shift"
    sp <- if (ih == 0 && iff == 0) "Stable Spread" else if (ih == 0) "Spread Expanded" else
          if (r$IQR_ratio < 0.8) "Spread Contracted" else if (r$IQR_ratio > 1.25) "Spread Expanded" else "Stable Spread"
    r$label <- sprintf("%s (%s)", sh, sp)
    R[[length(R) + 1]] <- r
  }
  do.call(rbind, R)
}
X <- lapply(setNames(STATIONS, STATIONS), load_annual)
C <- do.call(rbind, lapply(STATIONS, function(s) cbind(Station = s, c1(X[[s]]))))
write_csv_full(C, file.path(od, "C1_projections.csv"))

# ---- model consensus: >= 8 of 10 models with a significant shift in the same direction
cons <- list()
for (p in c("Near", "Far")) for (s in STATIONS) {
  x <- X[[s]]; ok <- c()
  for (k in sort(unique(x$Index), method = "radix")) {
    g <- x[x$Index == k, ]
    sig <- sapply(MODELS, function(m) {
      a <- per(g, m, "Hist"); b <- per(g, m, p); pv <- wilcox_p(a, b)
      if (!is.na(pv) && pv < 0.05) sign(median(b) - median(a)) else 0
    })
    ok[k] <- max(sum(sig == 1), sum(sig == -1)) >= 8
  }
  cons[[length(cons) + 1]] <- data.frame(Period = p, Station = s, All = sum(ok),
    Temperature = sum(ok[names(ok) %in% TEMP_INDICES]), Precipitation = sum(ok[!names(ok) %in% TEMP_INDICES]))
}
cons <- do.call(rbind, cons)
write_csv_full(cons, file.path(od, "model_consensus.csv"))
print(cons)

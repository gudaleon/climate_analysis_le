# Step 09 (6.13 method): period medians (6.13 Section 3.3).
# For each station and index: observed median in Historical and Present; median of the pooled ten-model
# sample in each period (models only, as in the Appendix E boxplots); and the lowest and highest single-model
# median in the Far period.
# Inputs : 2_Data/3_Annual_index_tables/All_<station>_observed_and_10_models_1950-2100.xlsx
# Output : 3_Code/output/v613_step09_period_medians/period_medians.csv (unrounded; missing = no values)
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step09_period_medians.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
od <- out_dir("v613_step09_period_medians")

med <- py_median
rows <- list()
for (st in STATIONS) {
  x <- load_annual(st)
  for (k in ORDER) {
    g <- x[x$Index == k, ]
    r <- data.frame(Station = st, Index = k, "Obs Historical" = med(per(g, "Observed", "Hist")),
                    "Obs Present" = med(per(g, "Observed", "Pres")), check.names = FALSE)
    for (p in c("Hist", "Pres", "Near", "Far")) {
      lab <- c(Hist = "Historical", Pres = "Present", Near = "Near", Far = "Far")[[p]]
      r[[paste("Pooled", lab)]] <- med(unlist(lapply(MODELS, function(m) per(g, m, p))))
    }
    mf <- sapply(MODELS, function(m) med(per(g, m, "Far")))
    mf <- mf[!is.na(mf)]
    r[["Lowest model median Far"]] <- if (length(mf)) min(mf) else NA_real_
    r[["Highest model median Far"]] <- if (length(mf)) max(mf) else NA_real_
    rows[[length(rows) + 1]] <- r
  }
}
write_out(do.call(rbind, rows), od, "period_medians.csv")

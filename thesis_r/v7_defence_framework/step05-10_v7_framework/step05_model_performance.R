# Step 05 (v7 framework, Test 1): model performance against observations.
# For every station, index and model, a Wilcoxon rank-sum test compares the model with the
# observations in the Historical (1950-1986) and Present (1987-2023) windows; a test passes
# when p >= 0.05. Pass counts are then summed by station, index group (T = temperature,
# P = precipitation) and model, and the reference models are picked.
# Inputs : 2_Data/3_Annual_index_tables/All_<station>_observed_and_10_models_1950-2100.xlsx
# Outputs: 3_Code/output/v7_step05_model_performance/
#            model_obs_pvalues.csv  (one row per station x index x model)
#            pass_counts.csv        (station x group x model: hist, present, total, both, max)
#            reference_models.csv   (temperature reference per station, precipitation reference)
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step05_model_performance.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
od <- out_dir("v7_step05_model_performance")

# All 44 indices in the thesis order; T = TEMP_INDICES, P = the rest
INDICES <- unname(INDEX_NAME)
group_of <- function(k) ifelse(k %in% TEMP_INDICES, "T", "P")

# Wilcoxon p as in the original calculation: when every value in both samples is identical
# (for example TXb3TNb3 = 0 in all years) the test returns no p-value, which counts as a fail.
# common.R's wilcox_p() returns 1 in that case, so it is overridden here.
test1_p <- function(a, b) {
  allv <- c(a, b)
  if (length(a) > 0 && length(b) > 0 && all(allv == allv[1])) return(NA_real_)
  wilcox_p(a, b)
}

# ---- p-values
pv <- list()
for (st in STATIONS) {
  x <- load_annual(st)
  for (k in INDICES) {
    g <- x[x$Index %in% k, ]
    for (m in MODELS) {
      pv[[length(pv) + 1]] <- data.frame(
        Station = st, Index = k, Group = group_of(k), Model = MODEL_FULL[[m]],
        p_Historical = test1_p(per(g, "Observed", "Hist"), per(g, m, "Hist")),
        p_Present    = test1_p(per(g, "Observed", "Pres"), per(g, m, "Pres")))
    }
  }
}
pv <- do.call(rbind, pv)
pv$pass_Historical <- !is.na(pv$p_Historical) & pv$p_Historical >= 0.05
pv$pass_Present    <- !is.na(pv$p_Present) & pv$p_Present >= 0.05
write_csv_full(pv, file.path(od, "model_obs_pvalues.csv"))

# ---- pass counts by station x group x model
pc <- list()
for (st in STATIONS) for (sec in c("T", "P")) for (m in MODELS) {
  s <- pv[pv$Station == st & pv$Group == sec & pv$Model == MODEL_FULL[[m]], ]
  h <- sum(s$pass_Historical); p <- sum(s$pass_Present)
  pc[[length(pc) + 1]] <- data.frame(station = toupper(st), group = sec, model = MODEL_FULL[[m]],
    hist = h, present = p, total = h + p, both = sum(s$pass_Historical & s$pass_Present), max = 2 * nrow(s))
}
pc <- do.call(rbind, pc)
write_csv_full(pc, file.path(od, "pass_counts.csv"))

# ---- reference models
# temperature: highest total per station, ties broken by 'both'
ref <- list()
for (st in toupper(STATIONS)) {
  t <- pc[pc$station == st & pc$group == "T", ]
  t <- t[order(-t$total, -t$both), ]
  ref[[length(ref) + 1]] <- data.frame(Station = st, Group = "T", Reference_model = t$model[1], Total = t$total[1], Both = t$both[1])
}
# precipitation: highest total summed over the three stations
p <- aggregate(total ~ model, data = pc[pc$group == "P", ], FUN = sum)
p <- p[order(-p$total), ]
ref[[length(ref) + 1]] <- data.frame(Station = "BASIN", Group = "P", Reference_model = p$model[1], Total = p$total[1], Both = NA)
ref <- do.call(rbind, ref)
write_csv_full(ref, file.path(od, "reference_models.csv"))
print(ref)

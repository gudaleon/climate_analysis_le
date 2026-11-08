# Step 05 (6.13 method): model performance against observations.
# For every station and index, a Wilcoxon rank-sum test compares the observed annual values with each
# model's annual values, separately for the Historical (1950-1986) and Present (1987-2023) periods.
# A model "passes" an index in a period when p >= 0.05. Pass counts are summed per station, group
# (T = temperature, P = precipitation) and model, and the 6.13 reference models are chosen from them:
#   temperature: highest cumulative pass count at each station (tie broken by the number of indices
#                passing in both periods, which decides Fergus);
#   precipitation: highest cumulative pass count summed over the three stations (one model for the basin).
# Inputs : 2_Data/3_Annual_index_tables/All_<station>_observed_and_10_models_1950-2100.xlsx
# Outputs: 3_Code/output/v613_step05_model_performance/
#   pvalues.csv          Station, Index, Group, Period, one column of p-values per model (Tables 3, A1, A2)
#   pass_counts.csv      station, group, model, hist, present, total, both, max
#   reference_models.csv the reference model per station and group, with the counts used to pick it
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step05_model_performance.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
od <- out_dir("v613_step05_model_performance")

INDICES <- unname(INDEX_NAME)   # thesis table order: temperature indices first, then precipitation
group_of <- function(k) ifelse(k %in% TEMP_INDICES, "T", "P")

# The published 6.13 p-values are missing, not 1, when every
# value in both samples is identical (no variance, e.g. TXb3TNb3 = 0 in every Present year). Such a case
# therefore counts as a fail. wilcox_p() from common.R returns 1 there, so it is wrapped here.
perf_p <- function(a, b) {
  allv <- c(a, b)
  if (length(a) > 0 && length(b) > 0 && all(allv == allv[1])) return(NA_real_)
  wilcox_p(a, b)
}

# p-values: one row per station x index x period, one column per model
prow <- list()
for (st in STATIONS) {
  x <- load_annual(st)
  for (k in INDICES) {
    g <- x[x$Index == k, ]
    for (p in c("Hist", "Pres")) {
      pv <- sapply(MODELS, function(m) perf_p(per(g, "Observed", p), per(g, m, p)))
      prow[[length(prow) + 1]] <- data.frame(Station = st, Index = k, Group = group_of(k),
        Period = ifelse(p == "Hist", "Historical", "Present"), t(setNames(pv, MODEL_FULL[MODELS])), check.names = FALSE)
    }
  }
}
PV <- do.call(rbind, prow)
write_out(PV, od, "pvalues.csv")

# pass counts (a missing p-value counts as a fail)
pass <- function(v) !is.na(v) & v >= 0.05
pc <- list()
for (st in STATIONS) for (grp in c("T", "P")) for (m in MODELS) {
  sub <- PV[PV$Station == st & PV$Group == grp, ]
  h <- pass(sub[sub$Period == "Historical", MODEL_FULL[m]])
  r <- pass(sub[sub$Period == "Present", MODEL_FULL[m]])
  pc[[length(pc) + 1]] <- data.frame(station = toupper(st), group = grp, model = unname(MODEL_FULL[m]),
    hist = sum(h), present = sum(r), total = sum(h) + sum(r), both = sum(h & r), max = 2 * length(h))
}
PC <- do.call(rbind, pc)
write_out(PC, od, "pass_counts.csv")

# reference models
ref <- list()
for (st in STATIONS) {
  t <- PC[PC$station == toupper(st) & PC$group == "T", ]
  t <- t[order(-t$total, -t$both), ]
  ref[[length(ref) + 1]] <- data.frame(Station = st, Group = "T", Model = t$model[1], Cumulative = t$total[1],
    Both = t$both[1], Runner_up = t$model[2], Runner_up_cumulative = t$total[2], Runner_up_both = t$both[2])
}
pp <- aggregate(cbind(total, both) ~ model, data = PC[PC$group == "P", ], FUN = sum)
pp <- pp[order(-pp$total, -pp$both), ]
for (st in c("All stations")) ref[[length(ref) + 1]] <- data.frame(Station = st, Group = "P", Model = pp$model[1],
  Cumulative = pp$total[1], Both = pp$both[1], Runner_up = pp$model[2], Runner_up_cumulative = pp$total[2], Runner_up_both = pp$both[2])
REF <- do.call(rbind, ref)
write_out(REF, od, "reference_models.csv")
print(REF)

# Step 08 (6.13 method): model consensus and projected change (6.13 Section 3.2.2).
# Consensus: an index has consensus at a station for a future period (Near 2024-2062, Far 2063-2100) when at
# least 8 of the 10 models show a significant (p < 0.05) change in the same direction relative to Historical.
# Counts are given for all 44 indices, temperature (31) and precipitation (13).
# Projected change: for each station, index and future period, the ensemble median of the ten model
# median changes with their minimum and maximum, plus the change of the pooled ten-model sample.
# Inputs : 3_Code/output/v613_step06_period_change/period_change.csv (run step06 first)
# Outputs: 3_Code/output/v613_step08_consensus_and_projected_change/
#   consensus.csv        Station, Comp, all, T, P
#   projected_change.csv Station, Index, Group, Near/Far ensemble median, min, max, Near/Far pooled change
#                        (unrounded; missing when no model has values, shown as n/a in the workbook)
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step08_consensus_and_projected_change.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
od <- out_dir("v613_step08_consensus_and_projected_change")

A <- read_step("v613_step06_period_change", "period_change.csv")

# consensus counts
cons <- list()
for (st in STATIONS) for (later in c("Near", "Far")) {
  sub <- A[A$Station == st & A$Comp == later & A$Source %in% MODELS, ]
  agree <- sapply(split(sub, sub$Index), function(g) max(sum(g$arrow == UP & g$sig), sum(g$arrow == DOWN & g$sig)) >= 8)
  temp <- names(agree) %in% TEMP_INDICES
  cons[[length(cons) + 1]] <- data.frame(Station = st, Comp = later, all = sum(agree), T = sum(agree[temp]), P = sum(agree[!temp]))
}
C <- do.call(rbind, cons)
write_out(C, od, "consensus.csv")
print(C)

# projected changes
nz <- function(f, v) if (all(is.na(v))) NA_real_ else f(v, na.rm = TRUE)
rows <- list()
for (st in STATIONS) for (k in ORDER) {
  r <- data.frame(Station = st, Index = k, Group = ifelse(k %in% TEMP_INDICES, "T", "P"))
  for (later in c("Near", "Far")) {
    d <- A$d[A$Station == st & A$Index == k & A$Comp == later & A$Source %in% MODELS]
    r[[paste0(later, ": ens. median \u0394")]] <- nz(function(v, na.rm) py_median(v), d)
    r[[paste0(later, ": min")]] <- nz(min, d)
    r[[paste0(later, ": max")]] <- nz(max, d)
  }
  for (later in c("Near", "Far"))
    r[[paste0(later, ": pooled \u0394")]] <- A$d[A$Station == st & A$Index == k & A$Comp == later & A$Source == "Ensemble"]
  rows[[length(rows) + 1]] <- r
}
write_out(do.call(rbind, rows), od, "projected_change.csv")

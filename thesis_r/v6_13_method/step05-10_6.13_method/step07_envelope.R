# Step 07 (6.13 method): observed change against the model envelope (6.13 Section 3.2.1).
# For each station and index, the observed Historical -> Present median change (dobs) is compared with the
# range [dmin, dmax] of the ten model changes (1e-9 tolerance). The 6.13 classes are:
#   "Within envelope"      dmin <= dobs <= dmax;
#   "Directional reversal" outside, and dobs has the opposite sign to the ensemble median change dmed
#                          (median of the ten model changes);
#   "Magnitude bias"       any other case outside the envelope.
# rev_all_models flags the stricter thesis v7 definition: outside and opposite in sign to every model.
# Inputs : 3_Code/output/v613_step06_period_change/period_change.csv (run step06 first)
# Output : 3_Code/output/v613_step07_envelope/envelope.csv
#          (Station, Index, Cat, dobs, dmin, dmax, dmed, inside, cls613, rev_all_models, obs_arrow, obs_sig)
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step07_envelope.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
od <- out_dir("v613_step07_envelope")

A <- read_step("v613_step06_period_change", "period_change.csv")
is_true <- function(v) !is.na(v) & v   # a comparison with a missing value counts as FALSE

rows <- list()
for (st in STATIONS) {
  sub <- A[A$Station == st & A$Comp == "Pres", ]
  for (k in sort(unique(sub$Index), method = "radix")) {
    q <- sub[sub$Index == k, ]
    dm <- q$d[match(MODELS, q$Source)]
    obs <- q[q$Source == "Observed", ]
    o <- obs$d
    lo <- min(dm, na.rm = TRUE); hi <- max(dm, na.rm = TRUE); med <- py_median(dm)
    inside <- is_true(lo - 1e-9 <= o & o <= hi + 1e-9)
    rev <- !inside && is_true(sign(o) != 0 & sign(o) == -sign(med))
    rev_all <- !inside && is_true((lo > 0 & o < 0) | (hi < 0 & o > 0))
    rows[[length(rows) + 1]] <- data.frame(Station = st, Index = k, Cat = q$Cat[1], dobs = o, dmin = lo, dmax = hi,
      dmed = med, inside = inside,
      cls613 = if (inside) "Within envelope" else if (rev) "Directional reversal" else "Magnitude bias",
      rev_all_models = rev_all, obs_arrow = obs$arrow, obs_sig = obs$sig)
  }
}
E <- do.call(rbind, rows)
write_out(E, od, "envelope.csv")

# console summary
for (st in STATIONS) {
  e <- E[E$Station == st, ]
  cat(st, "inside", sum(e$inside), "/44  T", sum(e$inside[e$Cat == "T"]), "/31  P", sum(e$inside[e$Cat == "P"]), "/13\n")
}
rv <- E[E$cls613 == "Directional reversal", ]
cat("out of range", sum(!E$inside), " reversals (6.13 def.)", nrow(rv), ":", paste(rv$Station, rv$Index, collapse = ", "), "\n")
cat("reversal vs all models", sum(E$rev_all_models), "\n")

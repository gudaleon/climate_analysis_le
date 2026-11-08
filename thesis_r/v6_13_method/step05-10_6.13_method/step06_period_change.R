# Step 06 (6.13 method): change between periods for every station, index, comparison and source.
# Comparisons: Historical -> Present (observations and models), Historical -> Near, Historical -> Far (models).
# Sources: Observed (Hist -> Present only), each of the ten models, and "Ensemble" = the ten models pooled
# into one sample per period (6.13 Section 2.6).
# For each row: d = median(later) - median(Historical); p = Wilcoxon rank-sum p (common.R wilcox_p);
# arrow = up / down by the sign of d, an en dash (U+2013) when the medians are identical, "n/a" when a period has no values;
# sig = p < 0.05 and the arrow is not the en dash.
# Inputs : 2_Data/3_Annual_index_tables/All_<station>_observed_and_10_models_1950-2100.xlsx
# Output : 3_Code/output/v613_step06_period_change/period_change.csv
#          (Station, Index, Cat, Comp, Source, nH, nL, d, p, arrow, sig), UTF-8
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step06_period_change.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
od <- out_dir("v613_step06_period_change")

change_row <- function(h, f) {
  if (length(h) == 0 || length(f) == 0) return(list(d = NA_real_, p = NA_real_, arrow = "n/a", sig = FALSE))
  d <- py_median(f) - py_median(h); p <- wilcox_p(h, f)
  arrow <- if (abs(d) < 1e-9) SAME else if (d > 0) UP else DOWN
  list(d = d, p = p, arrow = arrow, sig = (p < 0.05) && arrow != SAME)
}

rows <- list()
for (st in STATIONS) {
  x <- load_annual(st)
  idx <- sort(unique(x$Index), method = "radix")   # byte order, as Python sorted()
  for (k in idx) {
    g <- x[x$Index == k, ]
    for (later in c("Pres", "Near", "Far")) {
      srcs <- c(if (later == "Pres") "Observed", MODELS, "Ensemble")
      for (s in srcs) {
        if (s == "Ensemble") {
          h <- unlist(lapply(MODELS, function(m) per(g, m, "Hist")))
          f <- unlist(lapply(MODELS, function(m) per(g, m, later)))
        } else { h <- per(g, s, "Hist"); f <- per(g, s, later) }
        r <- change_row(as.numeric(h), as.numeric(f))
        rows[[length(rows) + 1]] <- data.frame(Station = st, Index = k, Cat = ifelse(k %in% TEMP_INDICES, "T", "P"),
          Comp = later, Source = s, nH = length(h), nL = length(f), d = r$d, p = r$p, arrow = r$arrow, sig = r$sig)
      }
    }
  }
}
A <- do.call(rbind, rows)
write_out(A, od, "period_change.csv")
cat("rows:", nrow(A), "\n")

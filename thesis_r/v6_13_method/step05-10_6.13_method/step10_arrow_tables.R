# Step 10 (6.13 method): wide arrow tables (thesis Tables 4, B1, B2 and Tables 5, C1, C2).
# One row per station and index (thesis row order), one column per comparison and source:
#   Historical -> Present: Observed, ten models, Ensemble;
#   Historical -> Near and Historical -> Far: ten models, Ensemble.
# Cells hold the arrow from step 06; a companion table holds the significance flag used for colouring.
# Inputs : 3_Code/output/v613_step06_period_change/period_change.csv (run step06 first)
# Outputs: 3_Code/output/v613_step10_arrow_tables/
#   arrows_hist_present.csv, significance_hist_present.csv
#   arrows_projected.csv,    significance_projected.csv
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step10_arrow_tables.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
od <- out_dir("v613_step10_arrow_tables")

A <- read_step("v613_step06_period_change", "period_change.csv")
A$key <- paste(A$Station, A$Index, A$Comp, A$Source)

wide <- function(comps, field) {
  cols <- do.call(rbind, lapply(comps, function(cp)
    data.frame(cp = cp, src = c(if (cp == "Pres") "Observed", MODELS, "Ensemble"))))
  out <- expand.grid(Index = ORDER, Station = STATIONS, stringsAsFactors = FALSE)[, c("Station", "Index")]
  for (j in seq_len(nrow(cols))) {
    hdr <- paste(COMP_LABEL[[cols$cp[j]]], cols$src[j])
    out[[hdr]] <- A[[field]][match(paste(out$Station, out$Index, cols$cp[j], cols$src[j]), A$key)]
  }
  out
}
write_out(wide("Pres", "arrow"), od, "arrows_hist_present.csv")
write_out(wide("Pres", "sig"), od, "significance_hist_present.csv")
write_out(wide(c("Near", "Far"), "arrow"), od, "arrows_projected.csv")
write_out(wide(c("Near", "Far"), "sig"), od, "significance_projected.csv")

# Step 12 (6.13 method): results workbook.
# Collects the outputs of steps 05-10 into one Excel workbook with the sheets of
# Thesis_6.13_results_new_data.xlsx: README, Pass counts, P-values (Tables 3, A1, A2),
# Arrows H-P (Tables 4, B1, B2), Arrows proj (Tables 5, C1, C2), Changes long, Envelope (Sec 3.2.1),
# Summary counts, Projected change (Sec 3.2.2), Period medians (Sec 3.3) and Monthly (Sec 3.4).
# The Monthly sheet is copied from 2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx.
# Values are rounded for display as in the original workbook (3 decimals for p-values and envelope values,
# 4 for the long change table, 2 for projected changes and medians).
# Inputs : outputs of steps 05, 06, 07, 08, 09 and 10 in 3_Code/output/ (run those first)
# Output : 3_Code/output/v613_step12_results_workbook/Thesis_6.13_results_new_data.xlsx
# Run    : cd <package root> && Rscript 3_Code/step05-10_6.13_method/step12_results_workbook.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(PKG, "3_Code", "step05-10_6.13_method", "v613_helpers.R"))
suppressPackageStartupMessages(library(openxlsx))
od <- out_dir("step13_results_workbook")

PC   <- read_step("v613_step05_model_performance", "pass_counts.csv")
PV   <- read_step("v613_step05_model_performance", "pvalues.csv")
A    <- read_step("v613_step06_period_change", "period_change.csv")
E    <- read_step("v613_step07_envelope", "envelope.csv")
C    <- read_step("v613_step08_consensus_and_projected_change", "consensus.csv")
PD   <- read_step("v613_step08_consensus_and_projected_change", "projected_change.csv")
MED  <- read_step("v613_step09_period_medians", "period_medians.csv")
AHP  <- read_step("v613_step10_arrow_tables", "arrows_hist_present.csv")
SHP  <- read_step("v613_step10_arrow_tables", "significance_hist_present.csv")
APR  <- read_step("v613_step10_arrow_tables", "arrows_projected.csv")
SPR  <- read_step("v613_step10_arrow_tables", "significance_projected.csv")
MON  <- read.xlsx(file.path(DATA, "4_Monthly_analysis", "Monthly_upper_quartile_summary.xlsx"), sheet = 1, check.names = FALSE, sep.names = " ")

# Two rounding rules reproduce the original workbook exactly (see v613_helpers.R): py_round() for values
# that were plain Python floats, np_round() for values that were numpy floats in the original script.

# Styles: Arial 10 throughout; fills as in the original
BOLD <- createStyle(textDecoration = "bold")
fill <- function(col) createStyle(fgFill = paste0("#", col))
F_PASS <- fill("DCE6F1"); F_FAIL <- fill("FFF2CC")
ARROW_FILL <- c(P_sig = "548DD4", P_ns = "95B3D7", T_sig = "E36C0A", T_ns = "FABF8F", na = "D9D9D9")

wb <- createWorkbook()
modifyBaseFont(wb, fontSize = 10, fontName = "Arial")

# Column widths as the original: max(10, min(40, longest printed value + 2)), less the 0.71 that openxlsx
# adds to every width. Widths are taken from the
# values as Python printed them (a whole float as "38.0", logicals as "True"/"False", missing as "nan").
pystr <- function(v, is_float) {
  if (is.logical(v)) return(ifelse(is.na(v), "", ifelse(v, "True", "False")))
  if (!is.numeric(v)) return(ifelse(is.na(v), "", as.character(v)))
  s <- as.character(v)
  if (is_float) s <- ifelse(is.na(v), "nan", ifelse(v == round(v), paste0(s, ".0"), s))
  ifelse(is.na(s), "", s)
}
auto_width <- function(sheet, df, float_cols = character(0), extra = NULL) {
  for (j in seq_along(df)) {
    vals <- c(names(df)[j], pystr(df[[j]], names(df)[j] %in% float_cols), if (!is.null(extra)) extra[[j]])
    setColWidths(wb, sheet, j, max(10, min(40, max(nchar(vals)) + 2)) - 0.71)
  }
}
# write a table, then put text (e.g. "n/a") into cells of numeric columns where the source had text
write_table <- function(sheet, df, text = NULL) {
  writeData(wb, sheet, df, keepNA = FALSE)
  if (!is.null(text)) for (j in seq_along(df)) {
    i <- which(!is.na(text[[j]]))
    for (r in i) writeData(wb, sheet, text[[j]][r], startCol = j, startRow = r + 1)
  }
  freezePane(wb, sheet, firstRow = TRUE)
}

# README
readme <- c("Thesis 6.13 method, recomputed with corrected inputs",
  "Models: CanDCS-U6 station series re-downloaded from PCIC, each model read on its own calendar (365-day for BCC-CSM2-MR, CanESM5, GFDL-ESM4, INM-CM5-0, NorESM2-LM). Fergus = grid cell nearest 43.735 N, 80.330 W (as in the thesis data).",
  "Observations: homogenised station series used in thesis v6/v7. Indices: Climpact 3.3.1, percentile base 1950\u20131986.",
  "Periods: Historical 1950\u20131986, Present 1987\u20132023, Near 2024\u20132062, Far 2063\u20132100.",
  "Tests: Wilcoxon rank-sum, two-sided, continuity correction, no exact p (as R wilcox.test(exact=FALSE, correct=TRUE)).",
  "Arrows: direction of change in period medians (later minus Historical); \u2013 = identical medians; n/a = no values in a period (e.g. CWA when no cold waves occur). Significant = p < 0.05.",
  "Ensemble column: all ten models pooled into one distribution per period (6.13 Section 2.6).",
  "Envelope (6.13 Section 3.2.1): observed Hist\u2192Present median change vs [min, max] of the ten model changes. \"Directional reversal (6.13)\" = outside the envelope and opposite in sign to the ensemble median change; \"reversal vs all models\" = opposite in sign to every model (stricter, used in thesis v7).",
  "Consensus (6.13 Section 3.2.2): at least 8 of 10 models significant in the same direction.",
  "Projected \u0394: per-model change in period medians; ensemble median = median of the ten model changes; envelope = min/max.",
  "Period medians: pooled ten-model medians (models only, as in the Appendix E boxplots) and observed medians.",
  "Monthly: median of the upper quartile of monthly values in each period (lower quartile for TXn), from observations and the reference models selected by the 6.13 cumulative pass count: temperature NorESM2-LM (London), EC-Earth3-Veg (Fergus, Harrow); precipitation BCC-CSM2-MR.")
addWorksheet(wb, "README")
writeData(wb, "README", readme, colNames = FALSE)
addStyle(wb, "README", BOLD, rows = 1, cols = 1, stack = TRUE)
setColWidths(wb, "README", 1, 160 - 0.71)

# Pass counts: station alphabetical, temperature before precipitation, highest cumulative first
sh <- "Pass counts"; addWorksheet(wb, sh)
pc <- PC[, c("station", "group", "model", "hist", "present", "total", "both", "max")]
pc$station <- paste0(substr(pc$station, 1, 1), tolower(substring(pc$station, 2)))
pc <- pc[order(pc$station, -xtfrm(pc$group), -pc$total, method = "radix"), ]
names(pc) <- c("Station", "Group (T/P)", "Model", "Historical passes", "Present passes", "Cumulative",
               "Indices passing both periods", "Max possible")
write_table(sh, pc); auto_width(sh, pc)

# P-values, coloured pass (>= 0.05) / fail
sh <- "P-values (Tables 3, A1, A2)"; addWorksheet(wb, sh)
pv <- PV; for (j in 5:14) pv[[j]] <- py_round(pv[[j]], 3)
write_table(sh, pv); auto_width(sh, pv, float_cols = names(pv)[5:14])
for (j in 5:14) {
  ok <- !is.na(pv[[j]]) & pv[[j]] >= 0.05
  if (any(ok))  addStyle(wb, sh, F_PASS, rows = which(ok) + 1, cols = j, stack = TRUE)
  if (any(!ok)) addStyle(wb, sh, F_FAIL, rows = which(!ok) + 1, cols = j, stack = TRUE)
}

# Arrow sheets: one block per station (name, header, 44 rows, two blank rows)
arrow_sheet <- function(sh, AR, SG) {
  addWorksheet(wb, sh)
  hdr <- names(AR)[-(1:2)]
  r0 <- 1
  for (st in STATIONS) {
    writeData(wb, sh, st, startRow = r0, startCol = 1); addStyle(wb, sh, BOLD, rows = r0, cols = 1, stack = TRUE)
    r0 <- r0 + 1
    writeData(wb, sh, t(c("Index", hdr)), startRow = r0, colNames = FALSE)
    addStyle(wb, sh, BOLD, rows = r0, cols = 1, stack = TRUE)
    addStyle(wb, sh, createStyle(textDecoration = "bold", textRotation = 90), rows = r0, cols = 1 + seq_along(hdr), stack = TRUE)
    r0 <- r0 + 1
    a <- AR[AR$Station == st, ]; s <- SG[SG$Station == st, ]
    a <- a[match(ORDER, a$Index), ]; s <- s[match(ORDER, s$Index), ]
    writeData(wb, sh, a[, -1], startRow = r0, colNames = FALSE)
    rows <- r0 + seq_along(ORDER) - 1
    addStyle(wb, sh, createStyle(halign = "center"), rows = rows, cols = 1 + seq_along(hdr), gridExpand = TRUE, stack = TRUE)
    cat_ <- ifelse(ORDER %in% TEMP_INDICES, "T", "P")
    for (j in seq_along(hdr)) {
      arr <- a[[hdr[j]]]; sg <- s[[hdr[j]]] %in% TRUE
      key <- ifelse(arr == "n/a", "na", ifelse(arr == SAME, NA, paste0(cat_, ifelse(sg, "_sig", "_ns"))))
      for (k in unique(na.omit(key))) addStyle(wb, sh, fill(ARROW_FILL[[k]]), rows = rows[which(key == k)], cols = j + 1, stack = TRUE)
    }
    r0 <- r0 + length(ORDER) + 2
  }
  setColWidths(wb, sh, 1, 12 - 0.71); setColWidths(wb, sh, 1 + seq_along(hdr), 4 - 0.71)
  freezePane(wb, sh, firstActiveRow = 2, firstActiveCol = 2)
}
arrow_sheet("Arrows H-P (Tables 4, B1, B2)", AHP, SHP)
arrow_sheet("Arrows proj (Tables 5, C1, C2)", APR, SPR)

# Long table of changes
sh <- "Changes long (\u0394, p)"; addWorksheet(wb, sh)
L <- A[, c("Station", "Index", "Cat", "Comp", "Source", "nH", "nL", "d", "p", "arrow", "sig")]
L$Comp <- c(Pres = "Hist\u2192Present", Near = "Hist\u2192Near", Far = "Hist\u2192Far")[L$Comp]
L$d <- py_round(L$d, 4); L$p <- py_round(L$p, 4)
names(L) <- c("Station", "Index", "Group", "Comparison", "Source", "n Historical", "n later", "\u0394 median",
              "Wilcoxon p", "Arrow", "Significant")
write_table(sh, L); auto_width(sh, L, float_cols = c("\u0394 median", "Wilcoxon p"))

# Envelope
sh <- "Envelope (Sec 3.2.1)"; addWorksheet(wb, sh)
E2 <- E; for (v in c("dobs", "dmin", "dmax", "dmed")) E2[[v]] <- py_round(E2[[v]], 3)
names(E2) <- c("Station", "Index", "Group", "\u0394 observed", "\u0394 min (models)", "\u0394 max (models)",
  "\u0394 ensemble median", "Within envelope", "Class (6.13 definition)", "Opposite to every model",
  "Observed arrow", "Observed significant")
write_table(sh, E2); auto_width(sh, E2, float_cols = names(E2)[4:7])

# Summary counts
sh <- "Summary counts"; addWorksheet(wb, sh)
S <- list(list("Item", "London", "Fergus", "Harrow", "Note"))
by_st <- function(f) lapply(STATIONS, function(st) f(E[E$Station == st, ]))
lst <- function(v) paste(v, collapse = ", ")
items <- list(
  "Indices within envelope (of 44)"   = function(e) sum(e$inside),
  "Temperature within (of 31)"        = function(e) sum(e$inside[e$Cat == "T"]),
  "Precipitation within (of 13)"      = function(e) sum(e$inside[e$Cat == "P"]),
  "Out-of-range cases"                = function(e) sum(!e$inside),
  "Directional reversals (6.13 def.)" = function(e) lst(e$Index[e$cls613 == "Directional reversal"]),
  "Magnitude biases"                  = function(e) lst(e$Index[e$cls613 == "Magnitude bias"]),
  "Opposite to every model"           = function(e) lst(e$Index[e$rev_all_models]))
for (lab in names(items)) S[[length(S) + 1]] <- c(list(lab), by_st(items[[lab]]))
all3 <- tapply(E$inside, E$Index, all); any3 <- tapply(E$inside, E$Index, any)
srt <- function(v) sort(names(v)[v], method = "radix")
S[[length(S) + 1]] <- list("Indices within envelope at all three stations", sum(all3), "", "", lst(srt(all3)))
S[[length(S) + 1]] <- list("Indices outside at all three stations", sum(!any3), "", "", lst(srt(!any3)))
S[[length(S) + 1]] <- list("Mixed (outside at one or two stations)", sum(any3 & !all3), "", "", lst(srt(any3 & !all3)))
S[[length(S) + 1]] <- list("Site-averaged agreement, temperature %", np_round(100 * mean(E$inside[E$Cat == "T"]), 1))
S[[length(S) + 1]] <- list("Site-averaged agreement, precipitation %", np_round(100 * mean(E$inside[E$Cat == "P"]), 1))
S[[length(S) + 1]] <- list()
S[[length(S) + 1]] <- list("Consensus (\u22658 of 10 significant, same direction)", "London", "Fergus", "Harrow")
for (cp in c("Near", "Far")) for (grp in c("all", "T", "P"))
  S[[length(S) + 1]] <- c(list(sprintf("%s: %s (of %d)", cp, grp, c(all = 44L, T = 31L, P = 13L)[[grp]])),
                          lapply(STATIONS, function(st) C[[grp]][C$Station == st & C$Comp == cp]))
for (i in seq_along(S)) for (j in seq_along(S[[i]])) {
  v <- S[[i]][[j]]
  if (!(is.character(v) && v == "")) writeData(wb, sh, v, startRow = i, startCol = j)
}
w <- sapply(1:5, function(j) max(c(0, sapply(S, function(r) if (length(r) >= j) nchar(pystr(r[[j]], is.double(r[[j]]) && !is.integer(r[[j]]))) else 0))))
setColWidths(wb, sh, 1:5, pmax(10, pmin(40, w + 2)) - 0.71)
freezePane(wb, sh, firstRow = TRUE)

# Projected change (numpy rounding: these were numpy floats in the original script)
sh <- "Projected \u0394 (Sec 3.2.2)"; addWorksheet(wb, sh)
P2 <- PD; txt <- lapply(P2, function(v) rep(NA_character_, nrow(P2)))
for (j in 4:11) { txt[[j]][is.na(P2[[j]])] <- "n/a"; P2[[j]] <- np_round(P2[[j]], 2) }
write_table(sh, P2, txt)
auto_width(sh, P2, float_cols = names(P2)[4:11], extra = lapply(txt, function(v) na.omit(v)))

# Period medians (observed medians and the single-model extremes were numpy floats; pooled medians plain floats)
sh <- "Period medians (Sec 3.3)"; addWorksheet(wb, sh)
M2 <- MED; txt <- lapply(M2, function(v) rep(NA_character_, nrow(M2)))
for (j in 3:10) {
  if (j >= 5) txt[[j]][is.na(M2[[j]])] <- "n/a"
  M2[[j]] <- if (j %in% 5:8) py_round(M2[[j]], 2) else np_round(M2[[j]], 2)
}
write_table(sh, M2, txt)
auto_width(sh, M2, float_cols = names(M2)[3:10], extra = lapply(txt, function(v) na.omit(v)))

# Monthly (copied)
sh <- "Monthly (Sec 3.4)"; addWorksheet(wb, sh)
write_table(sh, MON); auto_width(sh, MON, float_cols = names(MON)[5:10])

saveWorkbook(wb, file.path(od, "Thesis_6.13_results_new_data.xlsx"), overwrite = TRUE)
tidy_xlsx(file.path(od, "Thesis_6.13_results_new_data.xlsx"))
cat("written", file.path(od, "Thesis_6.13_results_new_data.xlsx"), "\n")

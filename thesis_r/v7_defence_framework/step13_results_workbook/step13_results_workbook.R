# Step 12 (v7 framework): results workbook for the defence version.
# Collects the tables of steps 05 to 10 and the monthly summary into one workbook with the sheets
# README, Pass counts, Model-obs p-values, Envelope (Test 2), Skill vs change, Projections,
# Process confidence, Monthly and Key numbers.
# Inputs : outputs of steps 05, 06, 07, 08, 09 and 10;
#          2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx (Monthly sheet)
# Outputs: 3_Code/output/v7_step12_results_workbook/Thesis_v7_results_new_data.xlsx
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step12_results_workbook.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
suppressPackageStartupMessages(library(openxlsx))
od <- out_dir("step13_results_workbook")
OUT <- file.path(od, "Thesis_v7_results_new_data.xlsx")
rd <- read_step

# ---- sheet contents
pc <- rd("v7_step05_model_performance", "pass_counts.csv")
names(pc) <- c("Station", "Group (T/P)", "Model", "Passes Historical", "Passes Present", "Total passes",
               "Indices passing both periods", "Maximum")
pv <- rd("v7_step05_model_performance", "model_obs_pvalues.csv")
B <- rd("v7_step06_change_test", "B1_envelope.csv")
names(B)[match(c("dobs", "dmin", "dmax", "nH", "nP", "cls"), names(B))] <-
  c("Observed change", "Model change min", "Model change max", "n Historical", "n Present", "Class")
SK <- rd("v7_step07_skill_vs_change", "skill_vs_change_cases.csv")
summ <- rd("v7_step07_skill_vs_change", "skill_vs_change_summary.csv")
summ$Value[7:8] <- round(summ$Value[7:8], 1)   # bounded rates (%)
summ$Value[9] <- round(summ$Value[9], 3)       # Fisher exact p
C <- rd("v7_step08_projections", "C1_projections.csv")
D <- rd("v7_step09_process_confidence", "D1_process_confidence.csv")
mon <- as.data.frame(read_excel(file.path(DATA, "4_Monthly_analysis", "Monthly_upper_quartile_summary.xlsx"),
                                sheet = "Monthly (Sec 3.4)"), check.names = FALSE)
key <- readLines(file.path(OUTD, "v7_step10_key_numbers", "key_numbers.txt"), encoding = "UTF-8")

readme <- c(
  "Thesis v7 (defence version): results recomputed with the re-downloaded CanDCS-U6 data (each model on its own calendar) and homogenised v4 observations.",
  "Periods: Historical 1950-1986, Present 1987-2023, Near Future 2024-2062, Far Future 2063-2100.",
  "Wilcoxon rank-sum, two-sided, continuity correction, normal approximation; pass = p >= 0.05.",
  NA,
  "Pass counts: Test 1 (model vs observations) pass counts per model, station and period.",
  "Model-obs p-values: every Test 1 p-value.",
  "Envelope (Test 2): observed Historical-to-Present change vs the range of the ten model changes; Bounded / Unbounded / Sign reversal (opposite to every model).",
  "Skill vs change: each index-station case, skilful if >= 10 of 20 model-window tests pass, crossed with the Test 2 class; summary with Fisher exact test.",
  "Projections: pooled ten-model medians and quartiles per period, change and IQR ratio (Table C1).",
  "Process confidence: Table D1 (coherence, bounding, sign reversals, rule-based confidence).",
  "Monthly: monthly upper-quartile medians and p-values for the reference models (NorESM2-LM London, EC-Earth3-Veg Fergus and Harrow, BCC-CSM2-MR precipitation).",
  "Key numbers: the key numbers from step 10 (numbers quoted in the thesis and the defence slides).")

# ---- write
wb <- createWorkbook()
put <- function(name, df, header = TRUE, startCol = 1) {
  if (!name %in% names(wb)) addWorksheet(wb, name)
  writeData(wb, name, df, startCol = startCol, colNames = header, keepNA = FALSE)
}
put("README", data.frame(x = readme), header = FALSE)
put("Pass counts", pc)
put("Model-obs p-values", pv)
put("Envelope (Test 2)", B)
put("Skill vs change", SK)
put("Skill vs change", summ, startCol = ncol(SK) + 2)
put("Projections", C)
put("Process confidence", D)
put("Monthly", mon)
put("Key numbers", data.frame(`Key numbers` = key, check.names = FALSE))

# ---- layout: bold Arial header on a light blue fill, frozen header row, column widths from
# the longest entry (number of characters + 2, at least 10, at most 60; README up to 160)
# text of a value as the original workbook held it when the widths were set: numbers stored with
# 16 significant digits and read back (shortest repr), logicals as True/False
cell_text <- function(v) {
  if (is.logical(v)) return(ifelse(is.na(v), NA, ifelse(v, "True", "False")))
  if (is.numeric(v)) return(num_text(suppressWarnings(as.numeric(sprintf("%.16g", v)))))
  as.character(v)
}
sheet_cols <- function(df, header) {
  lapply(seq_along(df), function(j) c(if (header) names(df)[j], cell_text(df[[j]])))
}
hs <- createStyle(fontName = "Arial", textDecoration = "bold", fgFill = "#DDE6F0")
layout <- list(
  "README" = sheet_cols(data.frame(x = readme), FALSE), "Pass counts" = sheet_cols(pc, TRUE),
  "Model-obs p-values" = sheet_cols(pv, TRUE), "Envelope (Test 2)" = sheet_cols(B, TRUE),
  "Skill vs change" = c(sheet_cols(SK, TRUE), list(character(0)), sheet_cols(summ, TRUE)),
  "Projections" = sheet_cols(C, TRUE), "Process confidence" = sheet_cols(D, TRUE),
  "Monthly" = sheet_cols(mon, TRUE), "Key numbers" = sheet_cols(data.frame(`Key numbers` = key, check.names = FALSE), TRUE))
for (name in names(layout)) {
  cols <- layout[[name]]
  w <- sapply(cols, function(v) { v <- v[!is.na(v)]; L <- if (length(v)) max(nchar(v)) else 8
                                  min(max(10, L + 2), if (name == "README") 160 else 60) })
  setColWidths(wb, name, cols = seq_along(w), widths = w - 0.71)   # openxlsx adds 0.71 to every width
  if (!name %in% c("README", "Monthly")) {
    addStyle(wb, name, hs, rows = 1, cols = seq_along(cols), gridExpand = TRUE)
    freezePane(wb, name, firstRow = TRUE)
  }
}
saveWorkbook(wb, OUT, overwrite = TRUE)
tidy_xlsx(OUT)
cat("written", OUT, "\n")

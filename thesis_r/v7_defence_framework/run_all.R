# Runs every step of the v7 (defence framework) analysis in order, from the package root:
#   Rscript 3_Code/run_all.R            (uses the Climpact output provided in 2_Data)
#   Rscript 3_Code/run_all.R climpact   (also reruns Climpact, step 03; slow, needs Climpact 3.3.1)
# Outputs go to 3_Code/output/<step>/.
args <- commandArgs(trailingOnly = TRUE)
steps <- c(
  "step01_merge_stations/merge_stations.R",
  "step02_homogenisation/homogenise.R",
  if ("climpact" %in% args) "step03_climpact/run_climpact.R",
  "step04_annual_tables/build_annual_tables.R",
  "step05-10_v7_framework/step05_model_performance.R",
  "step05-10_v7_framework/step06_change_test.R",
  "step05-10_v7_framework/step07_skill_vs_change.R",
  "step05-10_v7_framework/step08_projections.R",
  "step05-10_v7_framework/step09_process_confidence.R",
  "step05-10_v7_framework/step10_key_numbers.R",
  "step11_monthly_analysis/step11a_monthly_inputs.R",
  "step11_monthly_analysis/step11b_monthly_statistics.R",
  "step12_figures/run_figures_monthly.R",
  "step12_figures/boxplots_four_periods.R",
  "step13_results_workbook/step13_results_workbook.R")
for (s in steps) {
  cat("\n==== ", s, "\n")
  rc <- system2(file.path(R.home("bin"), "Rscript"), file.path("3_Code", s))
  if (rc != 0) stop("step failed: ", s)
}
cat("\nAll steps finished. Outputs are in 3_Code/output/\n")

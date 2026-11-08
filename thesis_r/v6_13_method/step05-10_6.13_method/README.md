# 6.13 method (R)

Run from the package root, in this order (`cd <package root> && Rscript 3_Code/step05-10_6.13_method/<script>.R`). Outputs go to `3_Code/output/v613_<step>/` as csv (plus an .rds copy that later steps read).

1. `step05_model_performance.R`: Wilcoxon p-values of each model against observations (Historical, Present), pass counts and the 6.13 reference models.
2. `step06_period_change.R`: median change, p-value, arrow and significance for every station, index, comparison (H→P, H→Near, H→Far) and source (Observed, ten models, pooled Ensemble).
3. `step07_envelope.R`: observed H→P change against the ten-model envelope, with the 6.13 classes (within envelope, magnitude bias, directional reversal).
4. `step08_consensus_and_projected_change.R`: consensus counts (at least 8 of 10 models significant in the same direction) and projected Near/Far changes (ensemble median, min, max, pooled).
5. `step09_period_medians.R`: observed and pooled ten-model medians per period, lowest and highest model median in the Far period.
6. `step10_arrow_tables.R`: wide arrow tables (Tables 4, B1, B2 and 5, C1, C2) with matching significance tables.
7. `../step13_results_workbook/step13_results_workbook.R`: the results workbook `Thesis_6.13_method_results_corrected_data.xlsx` from steps 05 to 10, with the Monthly sheet copied from `2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx`.

`v613_helpers.R` holds the shared helpers (UTF-8 arrows, numpy-style median, Python and numpy rounding, csv/rds output, workbook tidy-up).

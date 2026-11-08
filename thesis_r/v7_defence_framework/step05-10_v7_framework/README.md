# v7 framework (defence version) analysis

Run from the package root, in this order: `Rscript 3_Code/step05-10_v7_framework/<script>.R`. Each step writes to `3_Code/output/v7_<step name>/`. `v7_helpers.R` is sourced by every step (full-precision csv writing, UTF-8 handling).

1. `step05_model_performance.R`: Test 1, Wilcoxon p-values of every model against observations (Historical, Present), pass counts by station, group and model, reference models.
2. `step06_change_test.R`: Test 2 envelope (Table B1), Bounded / Unbounded / Sign reversal, diagnostic reason and basin tier.
3. `step07_skill_vs_change.R`: skilful cases (at least 10 of 20 passes) crossed with the Test 2 class, 2 x 2 table, Fisher exact test, alternative skill rules.
4. `step08_projections.R`: pooled projections (Table C1) with quartiles, outliers and labels, and the 8-of-10 model consensus counts.
5. `step09_process_confidence.R`: process groups, coherence and rule-based confidence (Table D1).
6. `step10_key_numbers.R`: numbers quoted in the thesis and slides (Test 1 pass counts, Test 2 bounding, skill versus change, projections, process confidence).
7. `../step13_results_workbook/step13_results_workbook.R`: results workbook Thesis_v7_results_new_data.xlsx (all tables above plus the Monthly sheet from 2_Data/4_Monthly_analysis).

# R code: thesis v7 (defence framework)

All code is R. Run everything from the package root (the folder that holds `1_Thesis`, `2_Data` and `3_Code`):

```
Rscript 3_Code/run_all.R            # every step, using the Climpact output provided in 2_Data
Rscript 3_Code/run_all.R climpact   # also reruns Climpact (slow; needs Climpact 3.3.1)
```

Each step can also be run on its own, e.g. `Rscript 3_Code/step05-10_v7_framework/step05_model_performance.R`. Results go to `3_Code/output/<step>/`. Every script begins with a comment saying what it does, what it reads and what it writes.

| Folder | Step | What it does | Main output |
|---|---|---|---|
| `common` | | shared settings: stations, models, periods, index names, data readers, Wilcoxon test | |
| `step01_merge_stations` | 1 | joins the ECCC station records into one daily series per station (London 6144475 + 6144478; Harrow 6133360 + 613CC60 + 6133362; Fergus 6142400) | merged daily series |
| `step02_homogenisation` | 2 | RHtestsV4 homogenisation of daily Tmax and Tmin (two rounds, quantile matching); `retest.R` pairwise check; `detect.R` first-pass detection | homogenised daily series |
| `step03_climpact` | 3 | runs Climpact 3.3.1 for the observations and the 30 model series, base period 1950 to 1986 | Climpact index files |
| `step04_annual_tables` | 4 | collects the annual indices of the observations and the ten models into one table per station; computes DTRgt15 | annual index tables |
| `step05-10_v7_framework` | 5 | **Test 1, model performance**: Wilcoxon test of each model against the observations in the Historical and Present periods, pass counts, reference models | p-values, pass counts, reference models |
| | 6 | **Test 2, change test**: is the observed Historical-to-Present change inside the range of the ten model changes (bounded, unbounded, sign reversal) | Table B1 |
| | 7 | **Skill versus change**: skilful cases (at least 10 of 20 tests passed) crossed with the Test 2 result, 2 x 2 table, Fisher exact test, alternative skill rules | 2 x 2 table |
| | 8 | **Projections**: pooled ten-model medians and quartiles for the four periods, change labels, model agreement (at least 8 of 10 significant in the same direction) | Table C1, agreement counts |
| | 9 | **Confidence by physical process**: process groups, directional coherence, bounding, sign reversals, confidence rule | Table D1 |
| | 10 | **Key numbers** quoted in the thesis and the slides | key_numbers.txt |
| `step11_monthly_analysis` | 11 | monthly index inputs for the reference models and the observations, monthly dry spells, upper-quartile medians, Historical-to-Present and Near-to-Far changes and p-values | monthly workbooks and summary |
| `step12_figures` | 12 | monthly window figures (Figures 3 to 8, E1 to E12) and four-period boxplots (F1 to F36) | PNG and PDF figures |
| `step13_results_workbook` | 13 | collects all results into one workbook | Thesis_v7_results_new_data.xlsx |

Checked: every step was run from a fresh copy and reproduces the thesis results (merged and homogenised series byte for byte; p-values, pass counts, B1, C1, D1, the 2 x 2 table, monthly statistics and the results workbook to machine precision).

R packages: readxl, openxlsx, dplyr, tidyr, ggplot2, patchwork, cowplot, stringr, forcats, zoo, data.table; RHtestsV4 is included; Climpact 3.3.1 only for step 3.

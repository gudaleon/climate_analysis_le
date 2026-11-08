# R code: thesis 6.13 method

All code is R. Run everything from the package root (the folder that holds `1_Thesis`, `2_Data` and `3_Code`):

```
Rscript 3_Code/run_all.R            # every step, using the Climpact output provided in 2_Data
Rscript 3_Code/run_all.R climpact   # also reruns Climpact (slow; needs Climpact 3.3.1)
```

Each step can also be run on its own, e.g. `Rscript 3_Code/step05-10_6.13_method/step05_model_performance.R`. Results go to `3_Code/output/<step>/`. Every script begins with a comment saying what it does, what it reads and what it writes.

| Folder | Step | What it does | Main output |
|---|---|---|---|
| `common` | | shared settings: stations, models, periods, index names, data readers, Wilcoxon test | |
| `step01_merge_stations` | 1 | joins the ECCC station records into one daily series per station (London 6144475 + 6144478; Harrow 6133360 + 613CC60 + 6133362; Fergus 6142400) | merged daily series |
| `step02_homogenisation` | 2 | RHtestsV4 homogenisation of daily Tmax and Tmin (two rounds, quantile matching); `retest.R` pairwise check; `detect.R` first-pass detection | homogenised daily series |
| `step03_climpact` | 3 | runs Climpact 3.3.1 for the observations and the 30 model series, base period 1950 to 1986 | Climpact index files |
| `step04_annual_tables` | 4 | collects the annual indices of the observations and the ten models into one table per station; computes DTRgt15 | annual index tables |
| `step05-10_6.13_method` | 5 | **Model performance**: Wilcoxon test of each model against the observations in the Historical and Present periods, pass counts, reference models | Tables 3, A1, A2 (p-values), pass counts |
| | 6 | **Period-to-period change**: median change, p-value and arrow for every station, index, comparison (Historical to Present, Near, Far) and source (observed, each model, pooled ensemble) | all changes and p-values |
| | 7 | **Observed change against the ensemble envelope**: within envelope, magnitude bias, directional reversal | envelope table |
| | 8 | **Consensus and projected change**: at least 8 of 10 models significant in the same direction; ensemble-median change with its range | consensus counts, projected changes |
| | 9 | **Period medians**: pooled ten-model medians per period (boxplots) | period medians |
| | 10 | **Arrow tables** in the layout of Tables 4, B1, B2, 5, C1, C2 | arrow tables |
| `step11_monthly_analysis` | 11 | monthly index inputs for the reference models and the observations, monthly dry spells, upper-quartile medians, changes and p-values | monthly workbooks and summary |
| `step12_figures` | 12 | monthly window figures (Figures 2 to 7, D1 to D12) and four-period boxplots (E1 to E36) | PNG and PDF figures |
| `step13_results_workbook` | 13 | collects all results into one workbook | Thesis_6.13_results_new_data.xlsx |

Checked: every step was run from a fresh copy and reproduces the thesis results (merged and homogenised series byte for byte; p-values, arrows, envelope classes, consensus, projected changes, period medians, monthly statistics and every sheet of the results workbook to machine precision).

R packages: readxl, openxlsx, dplyr, tidyr, ggplot2, patchwork, cowplot, stringr, forcats, zoo, data.table; RHtestsV4 is included; Climpact 3.3.1 only for step 3.

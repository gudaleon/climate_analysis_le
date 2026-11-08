# climate_analysis_le

Analysis code for the CMIP6 Lake Erie climate resilience analysis: the thesis research of Jeremy Liyan Wu, co-authored with Alex Neumann. The work examines daily temperature and precipitation records at three Ontario stations in the Lake Erie basin (London, Fergus and Harrow) together with daily series from ten CMIP6 global climate models, and it analyses how the climate of the basin has changed and how it is projected to change.

The analysis was produced and checked under Alex Neumann's "Researcher-led AI research" method: the thesis computations were recomputed independently, by more than one route, and the recomputed index tables were compared against the thesis tables cell by cell.

## Repository contents

### thesis_r

The author's original R pipeline, in the two versions of the thesis method.

- `thesis_r/v6_13_method`: the version 6.13 method pipeline.
- `thesis_r/v7_defence_framework`: the version 7 defence framework pipeline.

Both versions follow the same numbered steps: merge the station daily series (step01), homogenise the station records with breakpoint detection and retesting (step02), compute climate indices with Climpact (step03), build the annual index tables (step04), run the method steps covering model performance, period change and projections (step05 to step10), run the monthly analysis (step11) and draw the figures (step12). The v7 version adds a results workbook step (step13). Each step folder carries the author's own README.

Step02 uses the RHtests homogenisation package (the file `RHtestsV4_20180301.r`), a third party package distributed by Environment and Climate Change Canada, which the author bundled with the pipeline and which is kept here in the same place.

### python_recompute

An independent Python reimplementation of the index computation, written from the published Climpact 3.3 and climdex.pcic definitions rather than from the author's scripts.

- `cdx.py` computes the station climate indices, annual and monthly, from daily temperature and precipitation series.
- `spei.py` computes SPEI and SPI, with Hargreaves potential evapotranspiration.
- The remaining modules run the recompute over the station and model series, build the comparison fact tables, apply the claim rules that test the thesis statements against the recomputed values, check alternative branches of the method, and assemble the audit reports and comparison tables.
- The `addA_` modules run Addendum A, a perturbation test that shifts the Fergus grid cell one step west. The `addB_` modules run Addendum B, which extends the same perturbation test to the Harrow station.

### python_verification

Two further independent passes over the same thesis material, written separately from `python_recompute`.

- `python_verification/codex`: audit and independent check scripts covering the inputs, the monthly tables and homogenisation, calendar boundary and sensitivity checks, independent percentile and provenance checks, and report assembly.
- `python_verification/grok`: a compact independent pass with its own modules for daily input, homogenisation, index computation and statistics, plus verdict generation and report writing.

## Data

No data files are included in this repository. The pipelines read daily station observations and CMIP6 model daily series (text and CSV files) that are not distributed here, and they write their tables and figures to output folders that are likewise not included. The third party reference sources used during verification (the Climpact 3.3 and climdex.pcic source trees) are not included; the Python code reimplements their published index definitions.

## Authors

Jeremy Liyan Wu (thesis author) and Alex Neumann (co-author).

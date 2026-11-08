# Step 3: Climpact indices

`run_climpact.R` calculates the Climpact indices for the three homogenised station series and the 30 model series (3 stations x 10 models), in Climpact batch mode with base period 1950-1986. The station settings (latitude, longitude, wsdin = csdin = 3, Tb_HDD = Tb_CDD = 18, Tb_GDD = 10, rxnday = 3, rnnmm = 30, txtn = 3, SPEI = 24) are read from the `climpact_station_settings.txt` files in `2_Data/1_Observations/d_Climpact_indices` and `2_Data/2_Models/c_Climpact_indices`.

## Installing Climpact

The thesis used Climpact 3.3.1.

1. Download Climpact from https://github.com/ARCCSS-extremes/climpact (the release or commit for version 3.3.1) and extract it, for example to `~/climpact`.
2. Install the R packages it needs. Open R in the Climpact folder and run `source('server/climpact.master.installer.r')`. The batch mode needs at least climdex.pcic, foreach, doSNOW, doParallel, snow, zoo, zyp, qpdf, SPEI, lmomco and their dependencies. If they go to a personal library, point `R_LIBS` to it when running the script.

## Running

From the package root:

```
R_LIBS=<library with the Climpact packages> Rscript 3_Code/step03_climpact/run_climpact.R --climpact=~/climpact
```

Options: `--only=London_NorESM,LONDON_v4` runs only the named series; `--out=<folder>` changes the output folder (default `3_Code/output/step03_climpact`); `--cores=<n>` sets the number of cores Climpact uses. Instead of `--climpact`, the environment variable `CLIMPACT_DIR` can be set.

Each run takes several minutes, so all 33 take a long time.

## Output

- `<out>/<run>/`: the index csv files of each run (`LONDON_v4`, ..., `Harrow_NorESM`), laid out like `2_Data/1_Observations/d_Climpact_indices/<run>` and `2_Data/2_Models/c_Climpact_indices/<run>`.
- `<out>/work/observations/` and `<out>/work/models/`: the Climpact input folder, the settings file used, `climpact.log`, and the full Climpact output (indices, qc, plots, trend, thres, corr).

Apart from the `Date_of_calculation` line in each file header, the index files are the same as those in 2_Data.

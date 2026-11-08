# run_climpact.R
# Calculates the Climpact 3.3.1 indices (batch mode, base period 1950-1986) for the three homogenised
# station series and the 30 model series (3 stations x 10 models).
# Climpact itself is not part of this package; see README.md in this folder for how to install it.
# Inputs:  2_Data/1_Observations/c_Homogenised_daily_series/{STATION}_homogenised_v4.txt
#          2_Data/1_Observations/d_Climpact_indices/climpact_station_settings.txt   (stations, run names LONDON_v4 ...)
#          2_Data/2_Models/b_Daily_series/{Station}_{model}.txt
#          2_Data/2_Models/c_Climpact_indices/climpact_station_settings.txt         (models)
# Outputs: 3_Code/output/step03_climpact/{run}/  the index csv files of each run (as in 2_Data .../{run}/)
#          3_Code/output/step03_climpact/work/   full Climpact output (qc, plots, trend, thres, ...) and logs
# Run:     cd <package root> && Rscript 3_Code/step03_climpact/run_climpact.R [options]
#   --climpact=<dir>   Climpact folder (default: environment variable CLIMPACT_DIR)
#   --only=<runs>      comma-separated run names, e.g. --only=London_NorESM (default: all 33)
#   --out=<dir>        output folder (default: 3_Code/output/step03_climpact)
#   --cores=<n>        cores given to Climpact (default 1)
# The R packages Climpact needs must be on the library path (for example R_LIBS=/root/Rlib).
# All 33 runs take a long time (several minutes each).

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))

arg <- function(name, default) {
  a <- grep(paste0("^--", name, "="), commandArgs(TRUE), value = TRUE)
  if (length(a)) sub(paste0("^--", name, "="), "", a[1]) else default
}
CLIMPACT <- normalizePath(arg("climpact", Sys.getenv("CLIMPACT_DIR", "")), mustWork = FALSE)
if (!file.exists(file.path(CLIMPACT, "climpact.batch.stations.r"))) stop("Climpact not found; give --climpact=<dir> or set CLIMPACT_DIR")
OUT <- arg("out", out_dir("step03_climpact"))
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
OUT <- normalizePath(OUT)
ONLY <- arg("only", "")
ONLY <- if (ONLY == "") NULL else strsplit(ONLY, ",")[[1]]
CORES <- arg("cores", "1")
BASE <- c(1950, 1986)

# Climpact batch input: one folder with the daily files and one settings (metadata) file
groups <- list(
  observations = list(settings = file.path(DATA, "1_Observations", "d_Climpact_indices", "climpact_station_settings.txt"),
                      daily = function(f) file.path(DATA, "1_Observations", "c_Homogenised_daily_series",
                                                    sub("_v4\\.txt$", "_homogenised_v4.txt", f))),
  models = list(settings = file.path(DATA, "2_Models", "c_Climpact_indices", "climpact_station_settings.txt"),
                daily = function(f) file.path(DATA, "2_Models", "b_Daily_series", f)))

for (g in names(groups)) {
  meta <- read.table(groups[[g]]$settings, header = TRUE, colClasses = "character")
  runs <- sub("\\.txt$", "", meta$station_file)
  keep <- if (is.null(ONLY)) rep(TRUE, length(runs)) else runs %in% ONLY
  if (!any(keep)) next
  work <- file.path(OUT, "work", g)
  input <- file.path(work, "input")
  unlink(work, recursive = TRUE)
  dir.create(input, recursive = TRUE)
  # daily files under the names given in the settings file (Climpact names its outputs after them)
  for (f in meta$station_file[keep]) stopifnot(file.copy(groups[[g]]$daily(f), file.path(input, f)))
  settings <- file.path(work, "settings.txt")   # Climpact writes its output to work/settings/<run>/
  writeLines(readLines(groups[[g]]$settings)[c(TRUE, keep)], settings)
  cat("Climpact batch:", g, "-", sum(keep), "series\n")
  owd <- setwd(CLIMPACT)                         # Climpact sources its modules relative to its folder
  status <- system2("Rscript", c("climpact.batch.stations.r", shQuote(input), shQuote(settings), BASE[1], BASE[2], CORES),
                    stdout = file.path(work, "climpact.log"), stderr = file.path(work, "climpact.log"))
  setwd(owd)
  if (status != 0) stop("Climpact failed; see ", file.path(work, "climpact.log"))
  for (r in runs[keep]) {
    err <- file.path(work, "settings", paste0(r, ".errors.txt"))
    if (file.exists(err)) warning(r, ": Climpact reported errors, see ", err)
    dest <- file.path(OUT, r)
    unlink(dest, recursive = TRUE); dir.create(dest)
    idx <- list.files(file.path(work, "settings", r, "indices"), full.names = TRUE)
    file.copy(idx, dest)
    cat(r, ":", length(idx), "index files\n")
  }
}

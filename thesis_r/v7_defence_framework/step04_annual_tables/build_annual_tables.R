# build_annual_tables.R
# Builds the annual index tables from the Climpact ANN outputs: for each station one table with the
# columns Year, Index, Observed, ACCESS ... NorESM (44 indices x 1950-2100, index-major order).
#   * Observed: Climpact indices of the homogenised station series (1950-2023; later years empty).
#   * Models: Climpact indices of the ten bias-corrected model series (1950-2100).
#   * HWA/HWF and CWA/CWF come from the ehf/ecf heatwave files; for spell indices the 'duration'
#     column is used, for GSL the 'sl' column, otherwise the first data column. -99.9 = missing.
#   * DTRgt15 (days with tx - tn > 15 C) is not a Climpact output and is computed from the daily
#     series: a year is missing when any month has more than 3 missing days or the year more than 15.
# Inputs:  2_Data/1_Observations/d_Climpact_indices/{STATION}_v4/, 2_Data/1_Observations/c_Homogenised_daily_series/,
#          2_Data/2_Models/c_Climpact_indices/{Station}_{model}/, 2_Data/2_Models/b_Daily_series/
# Outputs: 3_Code/output/step04_annual_tables/Observed_annual_indices_{Station}.xlsx (Year, Index, Observed)
#          3_Code/output/step04_annual_tables/All_{Station}_observed_and_10_models_1950-2100.xlsx
#          3_Code/output/step04_annual_tables/verification.csv (comparison with the tables in 2_Data)
# Run:     cd <package root> && Rscript 3_Code/step04_annual_tables/build_annual_tables.R
# Observed column from the observation Climpact output; model columns from the model Climpact output.

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
suppressPackageStartupMessages(library(openxlsx))

OUT <- out_dir("step04_annual_tables")
YEARS <- 1950:2100
# Row layout of the tables: index-major, 1950-2100 within each index (labels as in the thesis tables)
INDEX_ORDER <- c("csdi", "csdi3", "wsdi", "wsdi3", "fd", "id", "su", "tr", "tnn", "tnx", "txx", "txn", "txm",
  "tmm", "tnm", "tn10p", "tn90p", "tx10p", "tx90p", "dtr", "DTRgt15", "gddgrow10", "prcptot", "r10mm", "r20mm",
  "rx1day", "rx3day", "rx5day", "sdii", "r95p", "r95ptot", "r99p", "r99ptot", "txb3tnb3", "txge30", "txgt50p",
  "tnltm20", "cdd", "cwd", "gsl", "cwa", "cwf", "hwa", "hwf")

# Climpact ANN csv: metadata lines, then a header starting with 'time'
read_climpact <- function(f) {
  t <- readLines(f)
  h <- which(startsWith(t, "time"))[1]
  d <- read.csv(text = t[h:length(t)], strip.white = TRUE, check.names = FALSE, colClasses = "character")
  names(d) <- trimws(names(d))
  d
}

# one annual index series (named by year), -99.9 -> NA; NULL when the file does not exist
climpact_series <- function(folder, run, k) {
  if (k %in% c("hwa", "hwf", "cwa", "cwf")) {
    d <- read_climpact(file.path(folder, sprintf("%s_%s_heatwave_ANN.csv", run, if (substr(k, 1, 1) == "h") "ehf" else "ecf")))
    v <- suppressWarnings(as.numeric(d[[toupper(k)]]))
  } else {
    fs <- list.files(folder, pattern = "_ANN\\.csv$")
    nm <- sub("_ANN\\.csv$", "", substring(fs, nchar(run) + 2))
    fs <- fs[startsWith(fs, paste0(run, "_")) & tolower(nm) == k]
    if (length(fs) == 0) return(NULL)
    d <- read_climpact(file.path(folder, fs[1]))
    col <- if ("duration" %in% names(d)) "duration" else if ("sl" %in% names(d)) "sl" else names(d)[2]
    v <- suppressWarnings(as.numeric(d[[col]]))
  }
  v[!is.na(v) & v == -99.9] <- NA
  setNames(v, as.integer(d$time))
}

# DTRgt15 from a daily series y m d pr tx tn (-99.9 = missing); duplicated dates keep the last record
dtrgt15 <- function(f) {
  d <- read.table(f, header = FALSE, col.names = c("y", "m", "d", "pr", "tx", "tn"))
  for (v in c("pr", "tx", "tn")) d[[v]][d[[v]] == -99.9] <- NA
  d <- d[!duplicated(d[, c("y", "m", "d")], fromLast = TRUE), ]
  e <- !is.na(d$tx) & !is.na(d$tn) & (d$tx - d$tn) > 15
  miss <- is.na(d$tx) | is.na(d$tn)
  mm <- tapply(miss, list(d$y * 100 + d$m), sum)
  bad_month_year <- tapply(mm > 3, as.integer(names(mm)) %/% 100, any)
  yt <- tapply(miss, d$y, sum)
  out <- tapply(e, d$y, sum) + 0
  yrs <- names(out)
  out[bad_month_year[yrs] | yt[yrs] > 15] <- NA
  setNames(as.numeric(out), yrs)
}

build_station <- function(st) {
  ST <- toupper(st)
  tab <- data.frame(Year = rep(YEARS, length(INDEX_ORDER)), Index = rep(INDEX_ORDER, each = length(YEARS)),
                    stringsAsFactors = FALSE)
  key <- tolower(tab$Index)
  fill <- function(get_series) {
    col <- rep(NA_real_, nrow(tab))
    for (k in unique(key)) {
      s <- get_series(k); m <- key == k
      col[m] <- unname(s[as.character(tab$Year[m])])
    }
    col
  }
  obs_run <- paste0(ST, "_v4")
  obs_dir <- file.path(DATA, "1_Observations", "d_Climpact_indices", obs_run)
  obs_daily <- file.path(DATA, "1_Observations", "c_Homogenised_daily_series", sprintf("%s_homogenised_v4.txt", ST))
  tab$Observed <- fill(function(k) if (k == "dtrgt15") dtrgt15(obs_daily) else climpact_series(obs_dir, obs_run, k))
  obs_only <- tab
  for (m in MODELS) {
    run <- paste0(st, "_", m)
    mdir <- file.path(DATA, "2_Models", "c_Climpact_indices", run)
    mdaily <- file.path(DATA, "2_Models", "b_Daily_series", paste0(run, ".txt"))
    tab[[m]] <- fill(function(k) if (k == "dtrgt15") dtrgt15(mdaily) else climpact_series(mdir, run, k))
  }
  write.xlsx(obs_only, file.path(OUT, sprintf("Observed_annual_indices_%s.xlsx", st)))
  tidy_xlsx(file.path(OUT, sprintf("Observed_annual_indices_%s.xlsx", st)))
  write.xlsx(tab, file.path(OUT, sprintf("All_%s_observed_and_10_models_1950-2100.xlsx", st)))
  tidy_xlsx(file.path(OUT, sprintf("All_%s_observed_and_10_models_1950-2100.xlsx", st)))
  list(obs = obs_only, all = tab)
}

# NaN-aware cell-by-cell comparison of value columns, labels compared exactly
compare <- function(new, ref, cols, what, st) {
  ref <- as.data.frame(ref)
  labels_ok <- nrow(new) == nrow(ref) && all(new$Year == ref$Year) && all(new$Index == as.character(ref$Index))
  do.call(rbind, lapply(cols, function(cl) {
    a <- new[[cl]]; b <- as.numeric(ref[[cl]]); b[!is.na(b) & b == -99.9] <- NA
    nan_mismatch <- sum(is.na(a) != is.na(b))
    d <- abs(a - b); d <- d[!is.na(d)]
    data.frame(table = what, station = st, column = cl, rows_and_labels_identical = labels_ok,
               nan_pattern_mismatches = nan_mismatch, max_abs_diff = if (length(d)) max(d) else 0,
               cells_over_1e9 = sum(d > 1e-9))
  }))
}

res <- list()
for (st in STATIONS) {
  b <- build_station(st)
  ref_obs <- read_excel(file.path(DATA, "1_Observations", "e_Annual_indices", sprintf("Observed_annual_indices_%s.xlsx", st)))
  ref_all <- read_excel(annual_table_file(st))
  res[[length(res) + 1]] <- compare(b$obs, ref_obs, "Observed", "e_Annual_indices", st)
  res[[length(res) + 1]] <- compare(b$all, ref_all, c("Observed", MODELS), "3_Annual_index_tables", st)
  cat(st, "written\n")
}
res <- do.call(rbind, res)
write.csv(res, file.path(OUT, "verification.csv"), row.names = FALSE)
print(res, row.names = FALSE)

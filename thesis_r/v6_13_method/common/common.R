# Shared settings and helpers. Every script is run from the package root:
#   Rscript 3_Code/<folder>/<script>.R
# Data are read from 2_Data/ and results written to 3_Code/output/<step>/.

suppressPackageStartupMessages({ library(readxl); library(dplyr); library(tidyr) })

PKG  <- Sys.getenv("THESIS_PKG", getwd())
DATA <- file.path(PKG, "2_Data")
OUTD <- file.path(PKG, "3_Code", "output")
out_dir <- function(step) { d <- file.path(OUTD, step); dir.create(d, recursive = TRUE, showWarnings = FALSE); d }

STATIONS <- c("London", "Fergus", "Harrow")
MODELS   <- c("ACCESS", "BCC", "CanESM", "CNRM", "EC", "GFDL", "INM", "MIROC", "MRI", "NorESM")
MODEL_FULL <- c(ACCESS = "ACCESS-ESM1-5", BCC = "BCC-CSM2-MR", CanESM = "CanESM5", CNRM = "CNRM-ESM2-1",
                EC = "EC-Earth3-Veg", GFDL = "GFDL-ESM4", INM = "INM-CM5-0", MIROC = "MIROC-ES2L",
                MRI = "MRI-ESM2-0", NorESM = "NorESM2-LM")
PERIODS <- list(Hist = c(1950, 1986), Pres = c(1987, 2023), Near = c(2024, 2062), Far = c(2063, 2100))

# Climpact file names (lower case) -> index names used in the thesis
INDEX_NAME <- c(csdi = "CSDI6", csdi3 = "CSDI3", wsdi = "WSDI6", wsdi3 = "WSDI3", fd = "FD", id = "ID", su = "SU",
  tr = "TR", tnn = "TNn", tnx = "TNx", txx = "TXx", txn = "TXn", txm = "TXm", tmm = "TMm", tnm = "TNm",
  tn10p = "TN10p", tn90p = "TN90p", tx10p = "TX10p", tx90p = "TX90p", dtr = "DTR", dtrgt15 = "DTRgt15",
  gddgrow10 = "GDDgrow10", txb3tnb3 = "TXb3TNb3", txge30 = "TXge30", txgt50p = "TXgt50p", tnltm20 = "TNltm20",
  gsl = "GSL", cwa = "CWA", cwf = "CWF", hwa = "HWA", hwf = "HWF", prcptot = "PRCPTOT", r10mm = "R10mm",
  r20mm = "R20mm", rx1day = "RX1day", rx3day = "RX3day", rx5day = "RX5day", sdii = "SDII", r95p = "R95p",
  r95ptot = "R95pTOT", r99p = "R99p", r99ptot = "R99pTOT", cdd = "CDD", cwd = "CWD")
TEMP_INDICES <- c("CSDI6", "CSDI3", "WSDI6", "WSDI3", "FD", "ID", "SU", "TR", "TNn", "TNx", "TXx", "TXn", "TXm",
  "TMm", "TNm", "TN10p", "TN90p", "TX10p", "TX90p", "DTR", "DTRgt15", "GDDgrow10", "TXb3TNb3", "TXge30",
  "TXgt50p", "TNltm20", "GSL", "CWA", "CWF", "HWA", "HWF")

# Annual index table: Year, Index, Observed, ten models (one workbook per station)
annual_table_file <- function(st) file.path(DATA, "3_Annual_index_tables", sprintf("All_%s_observed_and_10_models_1950-2100.xlsx", st))
load_annual <- function(st, file = annual_table_file(st)) {
  x <- read_excel(file)
  x[x == -99.9] <- NA
  x$Index <- unname(INDEX_NAME[tolower(trimws(as.character(x$Index)))])
  as.data.frame(x)
}
# values of one column for one index in one period, missing values dropped
per <- function(g, col, p) { r <- PERIODS[[p]]; v <- g[[col]][g$Year >= r[1] & g$Year <= r[2]]; v[!is.na(v)] }

# Wilcoxon rank-sum test: two-sided, continuity correction, normal approximation (no exact p)
wilcox_p <- function(a, b) {
  a <- as.numeric(a); b <- as.numeric(b)
  if (length(a) == 0 || length(b) == 0) return(NA_real_)
  allv <- c(a, b); if (all(allv == allv[1])) return(1)
  suppressWarnings(wilcox.test(a, b, alternative = "two.sided", exact = FALSE, correct = TRUE)$p.value)
}

# openxlsx 4.2.5 writes links to a drawing part it does not create; some readers then refuse the file.
# This removes the dangling links (uses the zip package, which openxlsx depends on).
tidy_xlsx <- function(path) {
  tmp <- tempfile("xlsx"); dir.create(tmp)
  zip::unzip(path, exdir = tmp)
  for (f in list.files(file.path(tmp, "xl", "worksheets", "_rels"), full.names = TRUE)) {
    x <- paste(readLines(f, warn = FALSE), collapse = "")
    for (r in regmatches(x, gregexpr("<Relationship [^>]*/>", x))[[1]]) {
      target <- sub('.*Target="([^"]*)".*', "\\1", r)
      if (!grepl("^\\.\\./", target)) next
      if (!file.exists(file.path(tmp, "xl", sub("^\\.\\./", "", target)))) x <- sub(r, "", x, fixed = TRUE)
    }
    writeLines(x, f, useBytes = TRUE)
  }
  ct <- file.path(tmp, "[Content_Types].xml")
  x <- paste(readLines(ct, warn = FALSE), collapse = "")
  for (p in regmatches(x, gregexpr('<Override PartName="[^"]*"[^>]*/>', x))[[1]])
    if (!file.exists(file.path(tmp, sub('.*PartName="/([^"]*)".*', "\\1", p)))) x <- sub(p, "", x, fixed = TRUE)
  writeLines(x, ct, useBytes = TRUE)
  unlink(path)
  zip::zipr(path, list.files(tmp, full.names = TRUE), include_directories = FALSE)
  unlink(tmp, recursive = TRUE)
  invisible(path)
}

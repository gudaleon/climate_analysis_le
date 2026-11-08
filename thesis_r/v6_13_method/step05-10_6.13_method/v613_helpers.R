# Small helpers shared by the 6.13-method scripts in this folder (sourced after common.R).

# Arrow symbols are written as UTF-8; make sure R handles them as such even under the C locale.
invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", "C.UTF-8")))
if (!l10n_info()$`UTF-8`) invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", "en_US.UTF-8")))

UP <- "\u2191"; DOWN <- "\u2193"; SAME <- "\u2013"

# Median as numpy computes it: the middle value, or (a + b) / 2 of the two middle values in plain double
# arithmetic. R's median() averages the two middle values with mean(), which accumulates in extended
# precision; this keeps the last bit identical to the Python results in every case. Missing values are dropped.
py_median <- function(x) {
  x <- sort(x[!is.na(x)]); n <- length(x)
  if (n == 0) return(NA_real_)
  if (n %% 2 == 1) x[(n + 1) / 2] else (x[n / 2] + x[n / 2 + 1]) / 2
}

# Rounding as round half to even: the exact binary value rounded to d decimals (C printf does this exactly).
# R round() uses a different algorithm and disagrees on a few near-half values.
py_round <- function(x, d) {
  out <- rep(NA_real_, length(x)); ok <- !is.na(x)
  out[ok] <- as.numeric(sprintf(paste0("%.", d, "f"), x[ok]))
  out
}
# Rounding as numpy round(): scale, round half to even, unscale (used where the original values were numpy floats)
np_round <- function(x, d) round(x * 10^d) / 10^d

# Each step writes its tables as csv (for reading) and as .rds next to it (exact copy used by later steps).
read_step <- function(step, file) {
  f <- file.path(OUTD, step, sub("\\.csv$", ".rds", file))
  if (!file.exists(f)) stop("Missing ", f, ": run ", step, ".R first")
  readRDS(f)
}
# csv numbers: 15 significant digits when that reads back to the same double, otherwise 17 (always exact).
# write.csv alone keeps only 15 digits.
num_text <- function(v) {
  out <- sprintf("%.15g", v)
  bad <- !is.na(v) & suppressWarnings(as.numeric(out)) != v
  out[bad] <- sprintf("%.17g", v[bad])
  out[is.na(v)] <- "NA"
  out
}
write_out <- function(x, dir, file) {
  saveRDS(x, file.path(dir, sub("\\.csv$", ".rds", file)))
  txt <- vapply(x, function(v) is.character(v) || is.factor(v), logical(1))
  for (j in which(vapply(x, is.double, logical(1)))) x[[j]] <- num_text(x[[j]])
  write.csv(x, file.path(dir, file), row.names = FALSE, fileEncoding = "UTF-8", quote = which(txt))
}

# Row order of the thesis tables (precipitation first, then temperature)
ORDER <- c("SDII", "RX1day", "RX3day", "RX5day", "R99pTOT", "R99p", "R95pTOT", "R95p", "R10mm", "R20mm", "PRCPTOT",
  "CWD", "CDD", "CSDI6", "CSDI3", "DTR", "DTRgt15", "FD", "GDDgrow10", "ID", "SU", "TMm", "TN10p", "TN90p", "TNltm20",
  "TNm", "TR", "TX10p", "TX90p", "TXb3TNb3", "TXge30", "TXgt50p", "TXm", "TXn", "WSDI6", "WSDI3", "CWA", "CWF", "GSL",
  "HWA", "HWF", "TNn", "TNx", "TXx")

COMP_LABEL <- c(Pres = "H\u2192P", Near = "H\u2192Near", Far = "H\u2192Far")

# openxlsx 4.2.5 refers to an empty drawing part for every sheet without writing it. Excel ignores this,
# but stricter readers (e.g. Python openpyxl) refuse the file, so references to parts that are not in the
# package are removed. zip is a dependency of openxlsx and therefore always installed with it.
# tidy_xlsx() now lives in common/common.R

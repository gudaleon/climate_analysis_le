# homog_helpers.R
# Shared functions for homogenise.R, retest.R and detect.R (sourced by them; not run on its own).
#   * reading the station series and writing RHtests input files
#   * calling the unmodified RHtestsV4 functions in this R session (rh())
# RHtestsV4_20180301.r is sourced unmodified (SHA-256 49b17c69e537a006ec2d9b4cd1055640bb670213823de07af948488133477e13).
# Only plotting is switched off, by masking lines() exactly as the former command-line wrapper did.

HOMOG_DIR <- file.path(PKG, "3_Code", "step02_homogenisation")
HOMOG_OUT <- out_dir("step02_homogenisation")
HOMOG_WORK <- file.path(HOMOG_OUT, "work")
dir.create(HOMOG_WORK, recursive = TRUE, showWarnings = FALSE)

H_STATIONS <- c("LONDON", "FERGUS", "HARROW")
H_INPUT_NAME <- c(LONDON = "LONDON_merged_6144475_6144478.txt",
                  FERGUS = "FERGUS_SHAND_DAM_6142400.txt",
                  HARROW = "HARROW_merged_6133360_613CC60_6133362.txt")
# Merged daily series: 2_Data by default; add the argument --from-step01 to use the step01 output instead
H_INPUT_DIR <- if ("--from-step01" %in% commandArgs(TRUE)) out_dir("step01_merge_stations") else
  file.path(DATA, "1_Observations", "b_Merged_daily_series")
H_INPUT <- setNames(file.path(H_INPUT_DIR, H_INPUT_NAME), names(H_INPUT_NAME))
H_FIRST <- c(1950, 1); H_LAST <- c(2023, 12)

# RHtests functions go into the global environment, where they keep their state (they assign there).
suppressMessages(source(file.path(HOMOG_DIR, "RHtestsV4_20180301.r")))
lines <- function(...) invisible(NULL)   # suppress plotting calls only; the algorithm is untouched
H_MV <- "-999.9"

# Run one RHtests function. Global objects that RHtests creates are removed afterwards, so every call
# starts from the same clean state as a fresh Rscript process. Console output is discarded.
rh <- function(what, ...) {
  a <- c(...)
  before <- ls(globalenv(), all.names = TRUE)
  invisible(capture.output(suppressWarnings(suppressMessages(switch(what,
    findu    = FindU.wRef(Bseries = a[1], Rseries = a[2], output = a[3], MissingValueCode = H_MV),
    stepsize = StepSize.wRef(Bseries = a[1], Rseries = a[2], InCs = a[3], output = a[4], MissingValueCode = H_MV),
    qm       = QMadj.GaussianDLY.wRef(Bseries = a[1], Rseries = a[2], MissingValueCode = H_MV, InCs = a[3],
                                      output = a[4], Iadj = as.numeric(a[5]), Mq = 20, Ny4a = 0))))))
  while (dev.cur() > 1) dev.off()
  new <- setdiff(ls(globalenv(), all.names = TRUE), before)
  rm(list = new, envir = globalenv())
}

# Station series y m d pr tx tn (-99.9 = missing); days with tx < tn set to missing in both
read_station <- function(path) {
  d <- read.table(path, header = FALSE, col.names = c("y", "m", "d", "pr", "tx", "tn"))
  for (v in c("pr", "tx", "tn")) d[[v]][d[[v]] == -99.9] <- NA
  bad <- !is.na(d$tx) & !is.na(d$tn) & d$tx < d$tn
  d$tx[bad] <- NA; d$tn[bad] <- NA
  d
}

write_lines_lf <- function(lines, path) {
  con <- file(path, "wb"); writeBin(charToRaw(paste0(lines, "\n", collapse = "")), con); close(con)
}

# Monthly means, NaN when more than 3 days are missing. The sum uses Kahan compensated summation in
# day order, as in the original ordering().mean() does, so the two-decimal values written are the same.
monthly_mean <- function(df, var) {
  key <- df$y * 100 + df$m
  grp <- match(key, unique(key))
  ng <- max(grp)
  x <- df[[var]]
  pos <- ave(seq_along(grp), grp, FUN = seq_along)
  M <- matrix(NA_real_, ng, max(pos)); M[cbind(grp, pos)] <- x
  ndays <- tabulate(grp, ng)
  s <- numeric(ng); comp <- numeric(ng); cnt <- integer(ng)
  for (j in seq_len(ncol(M))) {
    v <- M[, j]; ok <- !is.na(v)
    y <- v[ok] - comp[ok]
    t <- s[ok] + y
    comp[ok] <- t - s[ok] - y
    s[ok] <- t
    cnt[ok] <- cnt[ok] + 1L
  }
  mm <- ifelse(cnt > 0, s / cnt, NA_real_)
  mm[(ndays - cnt) > 3] <- NA
  first <- !duplicated(grp)
  data.frame(y = df$y[first], m = df$m[first], value = mm)
}

# RHtests input: 'y m d value' (daily, one decimal) or 'y m 0 value' (monthly means, two decimals)
write_series <- function(df, var, path, kind) {
  if (kind == "dly") {
    x <- df[[var]]
    lines <- paste(df$y, df$m, df$d, ifelse(is.na(x), "-999.9", sprintf("%.1f", x)))
  } else {
    mm <- monthly_mean(df, var)
    lines <- paste(mm$y, mm$m, 0, ifelse(is.na(mm$value), "-999.9", sprintf("%.2f", mm$value)))
  }
  write_lines_lf(lines, path)
}

# rounding to 1 decimal: round half to even of 10 x, then divide by 10
np_round1 <- function(x) round(x * 10) / 10

# Reference series: mean of two stations (daily values rounded to one decimal)
reference <- function(series, a, b, var, daily) {
  r <- series[[a]][, c("y", "m", "d")]
  r[[var]] <- (series[[a]][[var]] + series[[b]][[var]]) / 2
  if (daily) r[[var]] <- np_round1(r[[var]])
  r
}

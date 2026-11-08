# homogenise.R
# Homogenisation of daily maximum and minimum temperature at London, Fergus and Harrow with RHtestsV4
# (unmodified). See README.md in this folder for the method.
#   * Reference series for each station = mean of the other two stations.
#   * Candidate changepoints (config/candidates.csv) are tested with StepSize.wRef on monthly means.
#     Type-1 candidates are dropped one at a time (weakest first) while any has significance "No",
#     or "?" with |step| < 0.2 C. Type-0 candidates are never dropped.
#   * Daily adjustment with QMadj.GaussianDLY.wRef (Mq = 20, Ny4a = 0). Base segment = the most recent
#     segment if it is at least 10 years long, otherwise the longest segment.
#   * Two rounds: round 1 uses the unadjusted neighbours as reference, round 2 the neighbours adjusted in
#     round 1. Each round adjusts the RAW series again (adjustments are not stacked).
#   * 29 February (left unadjusted by RHtests) takes the 28 February adjustment.
#   * After adjustment, tn is clipped to tx on days where tn > tx. Precipitation is not adjusted.
# Input:  2_Data/1_Observations/b_Merged_daily_series (or, with --from-step01, the step01 output);
#         3_Code/step02_homogenisation/config/candidates.csv
# Output: 3_Code/output/step02_homogenisation/{LONDON,FERGUS,HARROW}_homogenised.txt and log.txt
#         (RHtests work files in 3_Code/output/step02_homogenisation/work/)
# Run:    cd <package root> && Rscript 3_Code/step02_homogenisation/homogenise.R [--from-step01]
#         (about 4 minutes)
# The output is byte-identical to c_Homogenised_daily_series/*_homogenised_v4.txt.

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step02_homogenisation", "homog_helpers.R"))

HLOG <- new.env(); HLOG$lines <- character(0)
add_log <- function(s) HLOG$lines <- c(HLOG$lines, s)

# Changepoint file for StepSize.wRef (monthly, day 00) or QMadj (daily, last day of the month)
write_changepoints <- function(dates, types, path, daily = FALSE) {
  out <- sprintf("%d changepoints", length(dates))
  for (i in seq_along(dates)) {
    y <- as.integer(substr(dates[i], 1, 4)); m <- as.integer(substr(dates[i], 5, 6))
    last_day <- as.integer(format(seq(as.Date(sprintf("%04d-%02d-01", y, m)), by = "month", length.out = 2)[2] - 1, "%d"))
    dd <- if (daily) sprintf("%02d", last_day) else "00"
    out <- c(out, sprintf("%d Yes   %d%02d%s (1.0000-1.0000) 0.950   10.0000 (    3.0000-    3.5000)", types[i], y, m, dd))
  }
  write_lines_lf(out, path)
}

# Repeat StepSize.wRef, dropping the weakest non-significant type-1 changepoint each time
prune <- function(st, var, dates, types, base_mly, ref_mly) {
  repeat {
    cs <- file.path(HOMOG_WORK, sprintf("%s_%s_cs.txt", st, var))
    write_changepoints(dates, types, cs)
    pre <- file.path(HOMOG_WORK, sprintf("%s_%s_SS", st, var))
    rh("stepsize", base_mly, ref_mly, cs, pre)
    rows <- readLines(paste0(pre, "_fCs.txt"))[-1]
    sig_flag <- sub("^\\s*\\d\\s+(\\S+).*$", "\\1", rows)
    sig_val <- as.numeric(sub("^.*?0\\.950\\s+([-0-9.]+).*$", "\\1", rows, perl = TRUE))
    txt <- readLines(paste0(pre, "_Fstat.txt"))
    k0 <- grep("Step-sizes", txt, fixed = TRUE)[1]
    steps <- as.numeric(strsplit(trimws(txt[k0 + 1]), "\\s+")[[1]])
    drop <- which(types == 1 & (sig_flag == "No" | (sig_flag == "?" & abs(steps) < 0.2)))
    if (length(drop) == 0) return(list(dates = dates, types = types, flag = sig_flag, steps = steps))
    k <- drop[which.min(sig_val[drop])]
    add_log(sprintf("  pruned %s %s %s (%s, step %+.2f)", st, var, dates[k], sig_flag[k], steps[k]))
    dates <- dates[-k]; types <- types[-k]
  }
}

base_segment <- function(dates) {
  ym <- as.integer(substr(dates, 1, 4)) * 12 + as.integer(substr(dates, 5, 6))
  bounds <- c(H_FIRST[1] * 12 + H_FIRST[2], ym + 1, H_LAST[1] * 12 + H_LAST[2])
  seglen <- diff(bounds)
  if (seglen[length(seglen)] >= 120) length(seglen) else which.max(seglen)
}

# carry the last non-missing value forward 
ffill <- function(x) { i <- cummax(ifelse(is.na(x), 0L, seq_along(x))); out <- x; out[i > 0] <- x[i[i > 0]]; out }

run_homogenisation <- function() {
  raw <- lapply(H_INPUT[H_STATIONS], read_station)
  cand <- read.csv(file.path(HOMOG_DIR, "config", "candidates.csv"), colClasses = c(yyyymm = "character"))
  groups <- unique(cand[, c("station", "variable")])          # order of first appearance
  ref_src <- raw
  for (rnd in 1:2) {
    add_log(sprintf("Round %d", rnd))
    cur <- raw
    for (gi in seq_len(nrow(groups))) {
      st <- groups$station[gi]; var <- groups$variable[gi]
      others <- setdiff(H_STATIONS, st); o1 <- others[1]; o2 <- others[2]
      g <- cand[cand$station == st & cand$variable == var, ]
      g <- g[order(g$yyyymm), ]
      wk <- function(f) file.path(HOMOG_WORK, f)
      base_mly <- wk(sprintf("%s_%s_mly.dat", st, var)); ref_mly <- wk(sprintf("REF%s_%s_mly.dat", st, var))
      write_series(raw[[st]], var, base_mly, "mly")
      write_series(reference(ref_src, o1, o2, var, FALSE), var, ref_mly, "mly")
      p <- prune(st, var, g$yyyymm, g$type, base_mly, ref_mly)
      add_log(paste0(sprintf("  kept %s %s: ", st, var),
                     paste(sprintf("%s (%s, %+.2f)", p$dates, p$flag, p$steps), collapse = ", ")))
      base_dly <- wk(sprintf("%s_%s_dly.dat", st, var)); ref_dly <- wk(sprintf("REF%s_%s_dly.dat", st, var))
      csd <- wk(sprintf("%s_%s_csd.txt", st, var))
      write_series(raw[[st]], var, base_dly, "dly")
      write_series(reference(ref_src, o1, o2, var, TRUE), var, ref_dly, "dly")
      write_changepoints(p$dates, p$types, csd, daily = TRUE)
      seg <- base_segment(p$dates)
      rh("qm", base_dly, ref_dly, csd, wk(sprintf("%s_%s_QM", st, var)), as.character(seg))
      q <- read.table(wk(sprintf("%s_%s_QM_QMadjDLYwRef.dat", st, var)), header = FALSE)
      q[q == -999.9] <- NA
      adj <- ffill(q[[5]] - q[[4]])                           # 29 Feb takes the 28 Feb adjustment
      x <- raw[[st]][[var]]
      new <- np_round1(x + adj)
      new[is.na(x)] <- NA
      cur[[st]][[var]] <- new
      add_log(sprintf("  adjusted %s %s to base segment %d", st, var, seg))
    }
    ref_src <- cur
  }
  fmt <- function(x) sprintf("%5.1f", ifelse(is.na(x), -99.9, x))
  for (st in H_STATIONS) {
    d <- cur[[st]]
    bad <- !is.na(d$tn) & !is.na(d$tx) & d$tn > d$tx
    add_log(sprintf("%s: tn clipped to tx on %d days", st, sum(bad)))
    d$tn[bad] <- d$tx[bad]
    rows <- sprintf("%d\t%d\t%d\t%s\t%s\t%s", as.integer(d$y), as.integer(d$m), as.integer(d$d), fmt(d$pr), fmt(d$tx), fmt(d$tn))
    con <- file(file.path(HOMOG_OUT, sprintf("%s_homogenised.txt", st)), "wb")
    writeBin(charToRaw(paste0(rows, "\r\n", collapse = "")), con); close(con)
    for (var in c("tx", "tn")) write_series(d, var, file.path(HOMOG_WORK, sprintf("%s_%s_final_mly.dat", st, var)), "mly")
  }
  write_lines_lf(HLOG$lines, file.path(HOMOG_OUT, "log.txt"))
  cat(HLOG$lines, sep = "\n")
}

run_homogenisation()

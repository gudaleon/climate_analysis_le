# detect.R
# Automatic candidate detection by triangulation. Documents how candidates arise; homogenise.R does not
# use it. For each station and variable:
#   1. FindU.wRef against the two-neighbour mean reference gives the candidate dates.
#   2. A candidate is attributed to the target station when a changepoint within +/-18 months is also
#      found against EACH neighbour separately, and NOT between the two neighbours.
# The final list in config/candidates.csv = these automatic candidates + the metadata break
# (London tn 1961-06) + candidates added or re-dated after review of the monthly difference series.
# Input:  the merged daily series (as in homogenise.R)
# Output: printed candidates; RHtests work files in 3_Code/output/step02_homogenisation/work/
# Run:    cd <package root> && Rscript 3_Code/step02_homogenisation/detect.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step02_homogenisation", "homog_helpers.R"))

TOL <- 18  # months

# changepoints in an RHtests _mCs.txt file: month number (y * 12 + m - 1), yyyymm, significance
read_cps <- function(path) {
  empty <- data.frame(t = integer(0), d = character(0), sig = character(0))
  if (!file.exists(path)) return(empty)
  l <- readLines(path)[-1]
  re <- "^\\s*(\\d)\\s+(\\S+)\\s+(\\d{8}).*?0\\.950\\s+([-0-9.]+)"
  l <- l[grepl(re, l, perl = TRUE)]
  if (length(l) == 0) return(empty)
  d <- sub(paste0(re, ".*$"), "\\3", l, perl = TRUE)
  data.frame(t = as.integer(substr(d, 1, 4)) * 12 + as.integer(substr(d, 5, 6)) - 1, d = substr(d, 1, 6),
             sig = sub(paste0(re, ".*$"), "\\2", l, perl = TRUE))
}

run_detect <- function() {
  raw <- lapply(H_INPUT[H_STATIONS], read_station)
  f <- function(s, v) file.path(HOMOG_WORK, sprintf("det_%s_%s.dat", s, v))
  wk <- function(x) file.path(HOMOG_WORK, x)
  for (s in H_STATIONS) for (v in c("tx", "tn")) write_series(raw[[s]], v, f(s, v), "mly")
  for (v in c("tx", "tn")) for (s in H_STATIONS) {
    others <- setdiff(H_STATIONS, s); o1 <- others[1]; o2 <- others[2]
    ref <- wk(sprintf("det_REF%s_%s.dat", s, v))
    write_series(reference(raw, o1, o2, v, FALSE), v, ref, "mly")
    rh("findu", f(s, v), ref, wk(sprintf("det_%s_%s_R", s, v)))
    for (p in list(c(s, o1), c(s, o2), c(o1, o2))) {
      out <- wk(sprintf("det_%s_vs_%s_%s", p[1], p[2], v))
      if (!file.exists(paste0(out, "_mCs.txt"))) rh("findu", f(p[1], v), f(p[2], v), out)
    }
    p1 <- read_cps(wk(sprintf("det_%s_vs_%s_%s_mCs.txt", s, o1, v)))
    p2 <- read_cps(wk(sprintf("det_%s_vs_%s_%s_mCs.txt", s, o2, v)))
    pn <- rbind(read_cps(wk(sprintf("det_%s_vs_%s_%s_mCs.txt", o1, o2, v))), read_cps(wk(sprintf("det_%s_vs_%s_%s_mCs.txt", o2, o1, v))))
    near <- function(t, L) any(abs(L$t - t) <= TOL)
    r <- read_cps(wk(sprintf("det_%s_%s_R_mCs.txt", s, v)))
    acc <- r$d[vapply(r$t, function(t) near(t, p1) && near(t, p2) && !near(t, pn), logical(1))]
    py_list <- function(x) paste0("[", paste0("'", x, "'", collapse = ", ")[length(x) > 0], "]")
    cat(sprintf("%s %s: candidates against reference %s; attributed %s\n", s, v, py_list(r$d), py_list(acc)))
  }
}

run_detect()

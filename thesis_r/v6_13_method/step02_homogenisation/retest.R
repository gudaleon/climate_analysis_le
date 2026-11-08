# retest.R
# Pairwise retest: FindU.wRef between each pair of stations, before and after homogenisation. Counts the
# changepoints still detected between station pairs (the thesis reports 50 before, 16 after).
# Input:  the merged daily series (as in homogenise.R) and 3_Code/output/step02_homogenisation/*_homogenised.txt
# Output: printed counts; RHtests work files in 3_Code/output/step02_homogenisation/work/
# Run:    cd <package root> && Rscript 3_Code/step02_homogenisation/retest.R   (after homogenise.R)
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step02_homogenisation", "homog_helpers.R"))

PAIRS <- list(c("LONDON", "FERGUS"), c("LONDON", "HARROW"), c("FERGUS", "HARROW"))

count_cps <- function(path) sum(grepl("^\\s*\\d\\s+\\S+\\s+\\d{8}.*?0\\.950", readLines(path)[-1], perl = TRUE))

run_retest <- function() {
  sets <- list(before = lapply(H_INPUT[H_STATIONS], read_station),
               after = lapply(setNames(file.path(HOMOG_OUT, sprintf("%s_homogenised.txt", H_STATIONS)), H_STATIONS), read_station))
  total <- c(before = 0, after = 0)
  for (tag in names(sets)) {
    for (var in c("tx", "tn")) for (p in PAIRS) {
      a <- p[1]; b <- p[2]
      fa <- file.path(HOMOG_WORK, sprintf("%s_%s_%s.dat", tag, a, var)); fb <- file.path(HOMOG_WORK, sprintf("%s_%s_%s.dat", tag, b, var))
      write_series(sets[[tag]][[a]], var, fa, "mly"); write_series(sets[[tag]][[b]], var, fb, "mly")
      out <- file.path(HOMOG_WORK, sprintf("rt_%s_%s%s_%s", tag, a, b, var))
      rh("findu", fa, fb, out)
      n <- count_cps(paste0(out, "_mCs.txt")); total[tag] <- total[tag] + n
      cat(sprintf("%-6s %s %s-%s: %d\n", tag, var, a, b, n))
    }
  }
  cat(sprintf("Pairwise changepoints: %d before, %d after\n", total[["before"]], total[["after"]]))
}

run_retest()

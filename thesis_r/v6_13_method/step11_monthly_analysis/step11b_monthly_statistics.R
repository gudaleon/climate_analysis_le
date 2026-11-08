# step11b_monthly_statistics.R
# Monthly statistics of the monthly (seasonal) analysis (6.13 Section 3.4, v7 seasonal results).
# For each station, source, index and month (Jan, Feb, Mar, Jun, Jul, Aug, Sep) and each period
# (Historical 1950-1986, Present 1987-2023, Near 2024-2062, Far 2063-2100):
#   upper-quartile median = median of the monthly values at or above the period's 75th percentile
#   (TXn: median of the values at or below the 25th percentile), percentiles as R quantile type 7.
# Changes Historical -> Present and Near -> Far, and Wilcoxon rank-sum p-values on all monthly
# values of the two periods (two-sided, continuity correction, normal approximation; NA when all
# values of both periods are identical, as the test returns no p-value there).
# Sources: Observed (all indices), the temperature reference model (NorESM2-LM London,
# EC-Earth3-Veg Fergus and Harrow; TMM, TXX, TXN, ID, SU) and BCC-CSM2-MR (precipitation indices
# PRCPTOT, R10MM, RX1DAY, RX5DAY, CDD, SPEI3, SPEI6, SPI3, SPI6).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,NorESM,EC,BCC}_<Station>.xlsx (built by step11a).
#          Pass --from-step11a to read 3_Code/output/step11a_monthly_inputs instead.
# Outputs: 3_Code/output/step11b_monthly_statistics/
#            monthly_upper_quartile_statistics.csv (full precision, one row per station, source,
#              index and month; same rows as the 'Monthly (Sec 3.4)' sheet and
#              2_Data/4_Monthly_analysis/Monthly_upper_quartile_summary.xlsx)
#            Monthly_upper_quartile_summary.xlsx (the sheet itself: medians to 2 dp, p to 3 dp)
#            seasonal_numbers.txt (the numbers quoted in the v7 seasonal text, as seasonal_nums.txt)
# Run:     cd <package root> && Rscript 3_Code/step11_monthly_analysis/step11b_monthly_statistics.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
suppressPackageStartupMessages(library(openxlsx))

IN  <- if ("--from-step11a" %in% commandArgs(TRUE)) out_dir("step11a_monthly_inputs") else file.path(DATA, "4_Monthly_analysis")
OUT <- out_dir("step11b_monthly_statistics")

TEMP_REF  <- c(London = "NorESM", Fergus = "EC", Harrow = "EC")
TEMP_IDX  <- c("TMM", "TXX", "TXN", "ID", "SU")
PREC_IDX  <- c("PRCPTOT", "R10MM", "RX1DAY", "RX5DAY", "CDD", "SPEI3", "SPEI6", "SPI3", "SPI6")
MONTHS    <- c(1, 2, 3, 6, 7, 8, 9)
PER_NAMES <- c(Hist = "Historical", Pres = "Present", Near = "Near", Far = "Far")

read_monthly <- function(name) {
  d <- as.data.frame(read_excel(file.path(IN, paste0(name, ".xlsx"))))
  names(d)[4] <- "v"
  d$v[d$v == -99.9] <- NA
  d
}

# median of the upper quartile (lower quartile when lower = TRUE)
uq_median <- function(v, lower = FALSE) {
  v <- v[!is.na(v)]
  if (length(v) == 0) return(NA_real_)
  t <- quantile(v, if (lower) 0.25 else 0.75, type = 7, names = FALSE)
  median(if (lower) v[v <= t] else v[v >= t])
}

# Wilcoxon p-value; NA without values or when every value is the same
monthly_p <- function(a, b) {
  if (length(a) == 0 || length(b) == 0) return(NA_real_)
  if (all(c(a, b) == a[1])) return(NA_real_)
  wilcox_p(a, b)
}

# monthly values of one index, one month and one period
mvals <- function(d, k, mo, p) {
  r <- PERIODS[[p]]
  v <- d$v[d$Index == k & d$Month == mo & d$Year >= r[1] & d$Year <= r[2]]
  v[!is.na(v)]
}

# ---- statistics table -------------------------------------------------------------------------
rows <- list(); DAT <- list()
for (st in STATIONS) {
  m <- TEMP_REF[[st]]
  srcs <- list(
    list(lab = "Observed", file = paste0("OBS_", st), ids = c(TEMP_IDX, PREC_IDX)),
    list(lab = sprintf("%s (temperature)", MODEL_FULL[[m]]), file = paste0(m, "_", st), ids = TEMP_IDX),
    list(lab = "BCC-CSM2-MR (precipitation)", file = paste0("BCC_", st), ids = PREC_IDX))
  for (s in srcs) {
    d <- read_monthly(s$file); DAT[[s$file]] <- d
    for (k in s$ids) for (mo in MONTHS) {
      v <- lapply(names(PERIODS), function(p) mvals(d, k, mo, p)); names(v) <- names(PERIODS)
      med <- sapply(v, uq_median, lower = (k == "TXN"))
      rows[[length(rows) + 1]] <- data.frame(
        Station = st, Source = s$lab, Index = k, Month = mo,
        Historical = med[["Hist"]], Present = med[["Pres"]], Near = med[["Near"]], Far = med[["Far"]],
        Change_Hist_to_Present = med[["Pres"]] - med[["Hist"]], Change_Near_to_Far = med[["Far"]] - med[["Near"]],
        p_Hist_vs_Present = monthly_p(v$Hist, v$Pres), p_Near_vs_Far = monthly_p(v$Near, v$Far),
        n_Hist = length(v$Hist), n_Present = length(v$Pres), n_Near = length(v$Near), n_Far = length(v$Far))
    }
  }
}
TAB <- do.call(rbind, rows)
write.csv(TAB, file.path(OUT, "monthly_upper_quartile_statistics.csv"), row.names = FALSE)

# the workbook sheet as in the 6.13 results workbook. Rounding as round half to even: on the exact
# binary value (sprintf), so 20.555 (stored as 20.55499...) gives 20.55, where R round() gives 20.56
round_py <- function(x, d) ifelse(is.na(x), NA_real_, suppressWarnings(as.numeric(sprintf(paste0("%.", d, "f"), x))))
SHEET <- TAB[, c("Station", "Source", "Index", "Month", "Historical", "Present", "Near", "Far")]
for (c in c("Historical", "Present", "Near", "Far")) SHEET[[c]] <- round_py(SHEET[[c]], 2)
SHEET[["Wilcoxon p H vs P (all monthly values)"]]    <- round_py(TAB$p_Hist_vs_Present, 3)
SHEET[["Wilcoxon p Near vs Far (all monthly values)"]] <- round_py(TAB$p_Near_vs_Far, 3)
wb <- createWorkbook(); addWorksheet(wb, "Monthly (Sec 3.4)")
writeData(wb, 1, SHEET, keepNA = FALSE); freezePane(wb, 1, firstRow = TRUE)
saveWorkbook(wb, file.path(OUT, "Monthly_upper_quartile_summary.xlsx"), overwrite = TRUE)
tidy_xlsx(file.path(OUT, "Monthly_upper_quartile_summary.xlsx"))

# ---- numbers quoted in the v7 seasonal text (reference models only) ---------------------------
model_file <- function(st, var) if (var == "T") paste0(TEMP_REF[[st]], "_", st) else paste0("BCC_", st)
val <- function(st, k, mo, p, var) uq_median(mvals(DAT[[model_file(st, var)]], k, mo, p), lower = (k == "TXN"))
f2 <- function(x) sprintf("%+.2f", x)
pct <- function(x, y) if (x != 0) sprintf("%+.1f%%", 100 * (y / x - 1)) else "+nan%"
txt <- character()
show <- function(k, mo, var, a, b) {
  o <- sapply(STATIONS, function(st) {
    x <- val(st, k, mo, a, var); y <- val(st, k, mo, b, var)
    sprintf("%s %.2f->%.2f d%s (%s)", substr(st, 1, 3), x, y, f2(y - x), pct(x, y))
  })
  txt <<- c(txt, sprintf("%-12s m%d %s->%s: %s", k, mo, a, b, paste(o, collapse = " | ")))
}
txt <- c(txt, "### 275 Hist->Pres")
show("TMM", 3, "T", "Hist", "Pres"); show("ID", 3, "T", "Hist", "Pres")
for (mo in 1:3) show("PRCPTOT", mo, "P", "Hist", "Pres")
txt <- c(txt, "### 276 Near->Far")
for (mo in 1:3) show("TXN", mo, "T", "Near", "Far")
show("TMM", 1, "T", "Near", "Far"); show("ID", 3, "T", "Near", "Far"); show("ID", 1, "T", "Near", "Far")
txt <- c(txt, "### 277")
show("PRCPTOT", 1, "P", "Near", "Far"); show("RX1DAY", 1, "P", "Near", "Far"); show("RX5DAY", 1, "P", "Near", "Far")
show("PRCPTOT", 3, "P", "Near", "Far"); show("RX5DAY", 3, "P", "Near", "Far"); show("PRCPTOT", 3, "P", "Hist", "Far")
txt <- c(txt, "### 282 Hist->Pres")
for (mo in 6:9) show("PRCPTOT", mo, "P", "Hist", "Pres")
show("CDD", 7, "P", "Hist", "Pres"); show("SU", 9, "T", "Hist", "Pres"); show("TXX", 9, "T", "Hist", "Pres")
show("TXN", 8, "T", "Hist", "Pres")
txt <- c(txt, "### 284 Near->Far")
show("SU", 9, "T", "Near", "Far"); show("TXX", 7, "T", "Near", "Far"); show("TXX", 8, "T", "Near", "Far")
for (mo in 6:9) show("TXN", mo, "T", "Near", "Far")
txt <- c(txt, "### 285/286")
for (k in c("SPEI6", "SPI6", "SPEI3", "SPI3")) for (mo in 6:9) show(k, mo, "P", "Near", "Far")
GAPS <- list()
for (p in c("Hist", "Near", "Far")) for (st in STATIONS) {
  g <- sapply(6:9, function(mo) val(st, "SPEI6", mo, p, "P") - val(st, "SPI6", mo, p, "P"))
  GAPS[[length(GAPS) + 1]] <- data.frame(Period = p, Station = st, Month = 6:9, SPEI6_minus_SPI6 = g)
  txt <- c(txt, sprintf("gap %s %s [%s]", p, st, paste(sprintf("%.2f", g), collapse = ", ")))
}
txt <- c(txt, "### 287")
for (mo in 6:9) show("PRCPTOT", mo, "P", "Near", "Far")
for (mo in 7:8) { show("RX1DAY", mo, "P", "Near", "Far"); show("R10MM", mo, "P", "Near", "Far") }
for (mo in 6:9) show("CDD", mo, "P", "Near", "Far")
show("RX5DAY", 9, "P", "Hist", "Far"); show("RX5DAY", 9, "P", "Near", "Far")
writeLines(txt, file.path(OUT, "seasonal_numbers.txt"))
write.csv(do.call(rbind, GAPS), file.path(OUT, "spei6_spi6_gaps.csv"), row.names = FALSE)
cat("rows:", nrow(TAB), "\n"); cat(txt, sep = "\n")

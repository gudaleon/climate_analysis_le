# Step 09 (v7 framework, Table D1): process-level confidence.
# Indices are grouped into eight climate-process groups, each with an expected direction of
# change (+1 increase, "cold" = decrease except CWA, "dom" = dominant sign). For each group:
#   coherence  share of index x station lines whose change has the expected sign, for the
#              observed Historical-to-Present change (Table B1) and for the pooled ten-model
#              median change Historical-to-Near and Historical-to-Far
#   bounded    share of lines bounded in Test 2, and the number of sign reversals
# Confidence rule:
#   Low      if >= 50% of historical lines have zero change, or bounded < 60%, or at least two
#            of the three coherences are below 60%
#   High     if at least two coherences are >= 80%, bounded >= 80%, no sign reversal and the
#            historical coherence is at least 60% at every station
#   Moderate otherwise
# Inputs : 3_Code/output/v7_step06_change_test/B1_envelope.csv, annual index tables
# Outputs: 3_Code/output/v7_step09_process_confidence/D1_process_confidence.csv
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step09_process_confidence.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
od <- out_dir("v7_step09_process_confidence")

G <- list(
  "Baseline temperature regime"          = list(c("TMm", "TNm", "TXm", "TNn", "TNx", "TXn", "TXx"), 1),
  "Loss of cold extremes"                = list(c("FD", "ID", "TN10p", "TX10p", "TNltm20", "CSDI6", "CSDI3", "CWA", "CWF"), "cold"),
  "Heat extremes and heat waves"         = list(c("SU", "TR", "TN90p", "TX90p", "TXge30", "TXgt50p", "TXb3TNb3", "WSDI6", "WSDI3", "HWA", "HWF"), 1),
  "Precipitation amount and frequency"   = list(c("PRCPTOT", "R10mm", "R20mm"), 1),
  "Growing season and heat accumulation" = list(c("GSL", "GDDgrow10"), 1),
  "Extreme precipitation intensity"      = list(c("RX1day", "RX3day", "RX5day", "SDII", "R95p", "R99p", "R95pTOT", "R99pTOT"), 1),
  "Diurnal temperature structure"        = list(c("DTR", "DTRgt15"), "dom"),
  "Wet-dry spell persistence"            = list(c("CDD", "CWD"), "dom"))

# number of lines with the expected sign (changes rounded to 6 decimals before taking the sign);
# zero_ok = TRUE also counts lines with zero change
coh <- function(vals, idx, sg, zero_ok = FALSE) {
  s <- sign(round(as.numeric(vals), 6))
  if (identical(sg, "dom")) return(max(sum(s == 1), sum(s == -1)) + if (zero_ok) sum(s == 0) else 0)
  ex <- if (identical(sg, "cold")) ifelse(idx == "CWA", 1, -1) else rep(sg, length(idx))
  sum(s == ex | (s == 0 & zero_ok))
}

B <- read_step("v7_step06_change_test", "B1_envelope.csv")
X <- lapply(setNames(STATIONS, STATIONS), load_annual)
# median of all model values (no observations) of one index in one period
pooled_models <- function(s, k, p) {
  g <- X[[s]][X[[s]]$Index == k, ]; r <- PERIODS[[p]]
  v <- unlist(g[g$Year >= r[1] & g$Year <= r[2], MODELS], use.names = FALSE); median(v[!is.na(v)])
}

R <- list()
for (gname in names(G)) {
  ks <- G[[gname]][[1]]; sg <- G[[gname]][[2]]
  sub <- B[B$Index %in% ks, ]; n <- nrow(sub)
  fut <- list()
  for (p in c("Near", "Far")) {
    v <- c(); ix <- c()
    for (s in STATIONS) for (k in ks) { v <- c(v, pooled_models(s, k, p) - pooled_models(s, k, "Hist")); ix <- c(ix, k) }
    fut[[p]] <- c(coh(v, ix, sg), coh(v, ix, sg, TRUE))
  }
  ch <- coh(sub$dobs, sub$Index, sg); ch0 <- coh(sub$dobs, sub$Index, sg, TRUE)
  bnd <- sum(sub$cls == "Bounded"); sr <- sum(sub$cls == "Sign reversal")
  zero_hist <- mean(round(sub$dobs, 6) == 0)
  pc <- c(100 * ch / n, 100 * fut$Near[1] / n, 100 * fut$Far[1] / n); pb <- 100 * bnd / n
  agree <- all(sapply(STATIONS, function(s) {
    ss <- sub[sub$Station == s, ]; coh(ss$dobs, ss$Index, sg) / max(nrow(ss), 1) >= 0.6 }))
  conf <- if (zero_hist >= 0.5 || pb < 60 || sum(pc < 60) >= 2) "Low" else
          if (sum(pc >= 80) >= 2 && pb >= 80 && sr == 0 && agree) "High" else "Moderate"
  R[[length(R) + 1]] <- data.frame(
    "Climate-process group" = gname, "Indices" = paste(ks, collapse = ", "), "n (lines)" = n,
    "Coherence Hist→Present (%)" = round(pc[1], 1), "Coherence Hist→Near (%)" = round(pc[2], 1),
    "Coherence Hist→Far (%)" = round(pc[3], 1), "Bounded (%)" = round(pb, 1), "Sign reversals" = sr,
    "Historical lines with zero change (%)" = round(100 * zero_hist, 1),
    "Historical coherence at least 60% at every station" = if (agree) "Yes" else "No",
    "Coherence Hist→Present, zeros counted (%)" = round(100 * ch0 / n, 1),
    "Coherence Hist→Far, zeros counted (%)" = round(100 * fut$Far[2] / n, 1),
    "Confidence (rule)" = conf, check.names = FALSE)
}
D <- do.call(rbind, R)
write_csv_full(D, file.path(od, "D1_process_confidence.csv"))
print(D[, c(1, 4:8, 13)])

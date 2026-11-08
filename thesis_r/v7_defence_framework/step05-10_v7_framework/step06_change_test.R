# Step 06 (v7 framework, Test 2, Table B1): change envelope test.
# For every station and index the observed Historical-to-Present change (median Present minus
# median Historical) is compared with the range of the ten model changes:
#   Bounded       observed change inside [min, max] of the model changes (1e-9 tolerance)
#   Sign reversal outside the range and opposite in sign to every model
#   Unbounded     outside the range otherwise
# Adds the diagnostic reason and the basin tier (how many stations are bounded per index).
# Inputs : 2_Data/3_Annual_index_tables/All_<station>_observed_and_10_models_1950-2100.xlsx
# Outputs: 3_Code/output/v7_step06_change_test/B1_envelope.csv
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step06_change_test.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
od <- out_dir("v7_step06_change_test")

# Index names as printed in thesis Table B1
INDEX_LONG <- c(CDD = "Consecutive Dry Days (Days)", CSDI3 = "Cold Spell Duration (Days)", CSDI6 = "Cold Spell Duration (Days)",
  CWA = "Cold Wave Amplitude (°C²)", CWD = "Consecutive Wet Days (Days)", CWF = "Cold Wave Frequency (Days)",
  DTR = "Diurnal Temp Range (°C)", DTRgt15 = "High DTR Days (Days)", FD = "Frost Days (Days)",
  GDDgrow10 = "Growing Degree-Days", GSL = "Growing Season Length (Days)", HWA = "Heat Wave Amplitude (°C²)",
  HWF = "Heat Wave Frequency (Days)", ID = "Ice Days (Days)", PRCPTOT = "Total Precipitation (mm)",
  R10mm = "Heavy Rain Days (Days)", R20mm = "Very Heavy Rain Days (Days)", R95p = "Very Wet Day Precip (mm)",
  R95pTOT = "Very Wet Contribution (%)", R99p = "Extremely Wet Precip (mm)", R99pTOT = "Extremely Wet Contrib (%)",
  RX1day = "Max 1-Day Rainfall (mm)", RX3day = "Max 3-Day Precip (mm)", RX5day = "Max 5-Day Precip (mm)",
  SDII = "Daily Intensity (mm/day)", SU = "Summer Days (Days)", TMm = "Mean Daily Temperature (°C)",
  TN10p = "Cool Nights (%)", TN90p = "Warm Nights (%)", TNltm20 = "Very Cold Nights (Days)",
  TNm = "Mean Minimum Temp (°C)", TNn = "Coldest Night of Year (°C)", TNx = "Warmest Night of Year (°C)",
  TR = "Tropical Nights (Days)", TX10p = "Cool Days (%)", TX90p = "Warm Days (%)", TXb3TNb3 = "Compound Warm Days",
  TXge30 = "Days with TX ≥ 30°C", TXgt50p = "Warm Days Above Median (%)", TXm = "Mean Maximum Temp (°C)",
  TXn = "Coldest Day of Year (°C)", TXx = "Warmest Day of Year (°C)", WSDI3 = "Warm Spell Duration (Days)",
  WSDI6 = "Warm Spell Duration (Days)")

classify <- function(o, lo, hi) {
  if (is.na(o) || is.na(lo)) return("NA")
  if (lo - 1e-9 <= o && o <= hi + 1e-9) return("Bounded")
  if ((lo > 0 && o < 0) || (hi < 0 && o > 0)) return("Sign reversal")
  "Unbounded"
}
# change of the median from Historical to Present (NA if a window is empty)
dmed <- function(g, col) {
  a <- per(g, col, "Pres"); b <- per(g, col, "Hist")
  if (length(a) == 0 || length(b) == 0) return(NA_real_)
  median(a) - median(b)
}
envelope <- function(x) {
  R <- list()
  for (k in sort(unique(x$Index), method = "radix")) {   # C-locale order, as in the original ordering
    g <- x[x$Index == k, ]
    dm <- sapply(MODELS, function(m) dmed(g, m)); o <- dmed(g, "Observed")
    lo <- if (all(is.na(dm))) NA_real_ else min(dm, na.rm = TRUE)
    hi <- if (all(is.na(dm))) NA_real_ else max(dm, na.rm = TRUE)
    r <- data.frame(Index = k, dobs = o, dmin = lo, dmax = hi,
                    nH = length(per(g, "Observed", "Hist")), nP = length(per(g, "Observed", "Pres")),
                    cls = classify(o, lo, hi))
    for (m in MODELS) r[[paste0("d_", m)]] <- dm[[m]]
    R[[length(R) + 1]] <- r
  }
  do.call(rbind, R)
}

B <- do.call(rbind, lapply(STATIONS, function(s) cbind(Station = s, envelope(load_annual(s)))))
B$Category <- ifelse(B$Index %in% TEMP_INDICES, "Temperature", "Precipitation")
B$`Index name` <- unname(INDEX_LONG[B$Index])
B$`Diagnostic reason` <- ifelse(B$cls == "Bounded", "Empirical shift bounded within GCM ensemble",
  ifelse(B$cls == "Sign reversal", "Directional error: observed shift opposite in sign to every model",
  ifelse(B$dobs < B$dmin, "Magnitude error: observed shift below the minimum model shift",
                          "Magnitude error: observed shift above the maximum model shift")))
# basin tier: number of stations bounded; any sign reversal or none bounded -> Qualified (Low)
tier <- sapply(split(B, B$Index), function(g) {
  nb <- sum(g$cls == "Bounded"); sr <- any(g$cls == "Sign reversal")
  if (sr || nb == 0) "Qualified (Low)" else c("Station-Specific Moderate", "Station-Specific High", "Basin-Wide High")[nb]
})
B$`Basin tier` <- unname(tier[B$Index])

write_csv_full(B, file.path(od, "B1_envelope.csv"))
print(table(B$Station, B$cls))

# step11a_monthly_inputs.R
# Builds the monthly index inputs of the monthly (seasonal) analysis, one workbook per station and
# source: the observations and the reference models BCC-CSM2-MR (precipitation, all stations),
# NorESM2-LM (temperature, London) and EC-Earth3-Veg (temperature, Fergus and Harrow).
#   1. Monthly CDD (longest dry spell, pr < 1 mm) from the daily series, computed as Climpact 3.3.1
#      does it (climdex.cdd with freq = "monthly", spells may span months and years): every dry
#      spell is credited with its full length to the month in which it ends, the monthly value is
#      the maximum, a month lying entirely inside a longer spell is NA, and the climdex annual
#      precipitation NA mask is applied. As in climdex.pcic, the annual mask (one value per year) is
#      multiplied with the monthly vector and therefore recycled over it. Port of S/figs/cdd331.R,
#      which called climdex.pcic directly; this script needs no Climpact packages.
#   2. The Climpact monthly (MON) outputs of TMm, TXx, TXn, ID, PRCPTOT, R10mm, RX1day, RX5day, SU,
#      SPEI3, SPEI6, SPI3, SPI6, stacked with the monthly CDD (missing values written as -99.9).
# Inputs:  2_Data/1_Observations/c_Homogenised_daily_series/<ST>_homogenised_v4.txt
#          2_Data/1_Observations/d_Climpact_indices/<ST>_v4/<ST>_v4_<index>_MON.csv
#          2_Data/2_Models/b_Daily_series/<Station>_<Model>.txt
#          2_Data/2_Models/c_Climpact_indices/<Station>_<Model>/<Station>_<Model>_<index>_MON.csv
# Outputs: 3_Code/output/step11a_monthly_inputs/monthly_CDD/{OBS_LONDON,...,BCC_London,...}.csv
#            (columns ym, v; identical to 2_Data/4_Monthly_analysis/monthly_CDD)
#          3_Code/output/step11a_monthly_inputs/{OBS,BCC,NorESM,EC}_<Station>.xlsx
#            (columns Year, Month, Index, <source>; same content as 2_Data/4_Monthly_analysis/*.xlsx)
# Run:     cd <package root> && Rscript 3_Code/step11_monthly_analysis/step11a_monthly_inputs.R

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
suppressPackageStartupMessages(library(openxlsx))

OUT <- out_dir("step11a_monthly_inputs")
OUT_CDD <- file.path(OUT, "monthly_CDD"); dir.create(OUT_CDD, showWarnings = FALSE)

# workbook index name -> Climpact file name
MON_INDICES <- c(TMM = "tmm", TXX = "txx", TXN = "txn", ID = "id", PRCPTOT = "prcptot", R10MM = "r10mm",
                 RX1DAY = "rx1day", RX5DAY = "rx5day", SU = "su", SPEI3 = "3month_spei",
                 SPEI6 = "6month_spei", SPI3 = "3month_spi", SPI6 = "6month_spi")

# ---- monthly CDD ----------------------------------------------------------------------------
# lengths of runs of TRUE, stored at the last day of each run (climdex get.series.lengths.at.ends)
run_lengths_at_ends <- function(x) {
  x[is.na(x)] <- FALSE
  n <- length(x); res <- numeric(n)
  start <- which(x & !c(FALSE, x[-n]))
  end   <- which(x & !c(x[-1], FALSE))
  res[end] <- end - start + 1
  res
}

monthly_cdd <- function(daily_file) {
  d <- read.table(daily_file)
  d <- d[!duplicated(d[, 1:3], fromLast = TRUE), ]
  d[d == -99.9] <- NA
  # full daily calendar from 1 Jan of the first year to 31 Dec of the last year; a series without
  # any 29 February is on the 365-day calendar (as the models read by Climpact with calendar 365)
  days <- seq(as.Date(sprintf("%d-01-01", min(d$V1))), as.Date(sprintf("%d-12-31", max(d$V1))), by = "day")
  if (!any(d$V2 == 2 & d$V3 == 29)) days <- days[format(days, "%m-%d") != "02-29"]
  key <- sprintf("%04d-%02d-%02d", d$V1, d$V2, d$V3)
  pr <- d$V4[match(format(days, "%Y-%m-%d"), key)]
  ym <- factor(format(days, "%Y-%m")); yr <- factor(format(days, "%Y"))

  dry   <- pr < 1
  spell <- run_lengths_at_ends(dry)
  max_spell <- tapply(spell, ym, max)
  all_dry   <- tapply(dry, ym, all)
  max_spell <- max_spell * c(1, NA)[as.integer(max_spell == 0 & all_dry) + 1]

  # climdex NA masks: a month is missing with > 3 missing days, a year with > 15 missing days or
  # any missing month
  miss <- is.na(pr)
  mask_month <- c(1, NA)[1 + as.numeric(tapply(miss, ym, sum) > 3)]
  mask_year  <- c(1, NA)[1 + as.numeric(tapply(miss, yr, sum) > 15)]
  mask_year  <- mask_year * as.numeric(tapply(mask_month, rep(seq_along(mask_year), each = 12), prod))
  v <- as.numeric(max_spell) * mask_year   # recycled over the months, as in climdex.pcic
  data.frame(ym = levels(ym), v = v)
}

# ---- Climpact monthly outputs -----------------------------------------------------------------
read_mon <- function(f) {
  txt <- readLines(f)
  h <- grep("^time", txt)[1]
  rows <- strsplit(txt[(h + 1):length(txt)], ",")
  tm <- trimws(sapply(rows, `[`, 1)); val <- trimws(sapply(rows, `[`, 2))
  data.frame(Year = as.integer(substr(tm, 1, 4)), Month = as.integer(substr(tm, 6, 7)),
             v = suppressWarnings(as.numeric(val)))
}

build <- function(idx_dir, run, daily_file, label, wb_name, cdd_name) {
  cdd <- monthly_cdd(daily_file)
  write.csv(cdd, file.path(OUT_CDD, paste0(cdd_name, ".csv")), row.names = FALSE)
  parts <- lapply(names(MON_INDICES), function(k) {
    d <- read_mon(file.path(idx_dir, sprintf("%s_%s_MON.csv", run, MON_INDICES[[k]])))
    data.frame(Year = d$Year, Month = d$Month, Index = k, v = d$v)
  })
  parts[[length(parts) + 1]] <- data.frame(Year = as.integer(substr(cdd$ym, 1, 4)),
                                           Month = as.integer(substr(cdd$ym, 6, 7)), Index = "CDD", v = cdd$v)
  D <- do.call(rbind, parts)
  D$v[is.na(D$v)] <- -99.9
  names(D)[4] <- label
  write.xlsx(D, file.path(OUT, paste0(wb_name, ".xlsx")))
  tidy_xlsx(file.path(OUT, paste0(wb_name, ".xlsx")))
  cat(wb_name, nrow(D), "rows\n")
}

OBS_IDX <- file.path(DATA, "1_Observations", "d_Climpact_indices")
OBS_DAY <- file.path(DATA, "1_Observations", "c_Homogenised_daily_series")
MOD_IDX <- file.path(DATA, "2_Models", "c_Climpact_indices")
MOD_DAY <- file.path(DATA, "2_Models", "b_Daily_series")
TEMP_REF <- c(London = "NorESM", Fergus = "EC", Harrow = "EC")

for (st in STATIONS) {
  ST <- toupper(st); run <- paste0(ST, "_v4")
  build(file.path(OBS_IDX, run), run, file.path(OBS_DAY, paste0(ST, "_homogenised_v4.txt")),
        "Observed", paste0("OBS_", st), paste0("OBS_", ST))
  for (m in c(TEMP_REF[[st]], "BCC")) {
    run <- paste0(st, "_", m)
    build(file.path(MOD_IDX, run), run, file.path(MOD_DAY, paste0(run, ".txt")), m, paste0(m, "_", st), paste0(m, "_", st))
  }
}

# merge_stations.R
# Builds the merged daily station series used for homogenisation (1950-01-01 to 2023-12-31).
#   London: London Int'l Airport (6144475) station file up to 18 Sep 2002; from 19 Sep 2002 to
#           31 Dec 2017 London CS (6144478, ECCC daily), with airport ECCC values filling days
#           missing at London CS; after 2017 the station file.
#   Harrow: Harrow CDA (6133360) to Dec 1991; Harrow automatic station (613CC60) Jan 1992 to
#           Aug 2000, except April 1992, which is taken from 6133360; Harrow CDA AUTO (6133362)
#           from Sep 2000.
#   Fergus: Fergus Shand Dam (6142400) station file, with the 29 Sep 2012 precipitation, missing
#           there, taken from the ECCC daily record of the same station.
# Input:  2_Data/1_Observations/a_ECCC_station_sources
# Output: 3_Code/output/step01_merge_stations/{LONDON_merged_6144475_6144478.txt,
#         HARROW_merged_6133360_613CC60_6133362.txt, FERGUS_SHAND_DAM_6142400.txt}
#         (year month day pr tmax tmin, tab-separated, one decimal, -99.9 = missing, CRLF line ends)
# Run:    cd <package root> && Rscript 3_Code/step01_merge_stations/merge_stations.R
# The output is byte-identical to 2_Data/1_Observations/b_Merged_daily_series.

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
suppressPackageStartupMessages(library(data.table))

SRC <- file.path(DATA, "1_Observations", "a_ECCC_station_sources")
OUT <- out_dir("step01_merge_stations")
DAYS <- seq(as.Date("1950-01-01"), as.Date("2023-12-31"), by = "day")
V <- c("pr", "tx", "tn")

# put a table with columns date, pr, tx, tn on the full daily calendar (first record of a date kept)
on_calendar <- function(d) {
  d <- d[!duplicated(d$date), ]
  m <- match(DAYS, d$date)
  data.frame(pr = d$pr[m], tx = d$tx[m], tn = d$tn[m])
}

# station file: year month day pr tx tn, whitespace separated, -99.9 = missing
station_file <- function(f) {
  d <- read.table(file.path(SRC, f), header = FALSE, col.names = c("y", "m", "d", V))
  for (v in V) d[[v]][d[[v]] == -99.9] <- NA
  d$date <- as.Date(sprintf("%04d-%02d-%02d", d$y, d$m, d$d))
  on_calendar(d)
}

# ECCC daily csv files (one or several parts), sorted by date
eccc <- function(...) {
  d <- rbindlist(lapply(c(...), function(f) fread(file.path(SRC, f), colClasses = list(character = "LOCAL_DATE"),
                                                  select = c("LOCAL_DATE", "TOTAL_PRECIPITATION", "MAX_TEMPERATURE", "MIN_TEMPERATURE"))))
  d <- data.frame(date = as.Date(substr(d$LOCAL_DATE, 1, 10)), pr = as.numeric(d$TOTAL_PRECIPITATION),
                  tx = as.numeric(d$MAX_TEMPERATURE), tn = as.numeric(d$MIN_TEMPERATURE))
  on_calendar(d[order(d$date), ])
}

write_series <- function(df, name) {
  fmt <- function(x) sprintf("%5.1f", ifelse(is.na(x), -99.9, x))
  lines <- paste(format(DAYS, "%Y"), as.integer(format(DAYS, "%m")), as.integer(format(DAYS, "%d")),
                 fmt(df$pr), fmt(df$tx), fmt(df$tn), sep = "\t")
  con <- file(file.path(OUT, name), "wb")
  writeBin(charToRaw(paste0(lines, "\r\n", collapse = "")), con)
  close(con)
  cat("written", name, "\n")
}

# fill missing values of a with values of b 
combine_first <- function(a, b) { for (v in V) a[[v]] <- ifelse(is.na(a[[v]]), b[[v]], a[[v]]); a }

# London
air  <- station_file("London_6144475_LONDON_INTL_AIRPORT_station_file.txt")
airE <- eccc("London_6144475_LONDON_INTL_AIRPORT_ECCC_daily.csv")
cs   <- eccc("London_6144478_LONDON_CS_ECCC_daily.csv")
lon <- air
w <- DAYS >= as.Date("2002-09-19") & DAYS <= as.Date("2017-12-31")
lon[w, ] <- combine_first(cs[w, ], airE[w, ])
write_series(lon, "LONDON_merged_6144475_6144478.txt")

# Harrow
cda  <- eccc("Harrow_6133360_HARROW_CDA_ECCC_daily_part1.csv", "Harrow_6133360_HARROW_CDA_ECCC_daily_part2.csv",
             "Harrow_6133360_HARROW_CDA_ECCC_daily_part3.csv")
acs  <- eccc("Harrow_613CC60_HARROW_AUTOMATIC_ECCC_daily.csv")
auto <- eccc("Harrow_6133362_HARROW_CDA_AUTO_ECCC_daily.csv")
har <- cda
m1 <- DAYS >= as.Date("1992-01-01") & DAYS <= as.Date("2000-08-31")
m2 <- DAYS >= as.Date("2000-09-01")
har[m1, ] <- acs[m1, ]
har[m2, ] <- auto[m2, ]
apr <- DAYS >= as.Date("1992-04-01") & DAYS <= as.Date("1992-04-30")
har[apr, ] <- cda[apr, ]
write_series(har, "HARROW_merged_6133360_613CC60_6133362.txt")

# Fergus
fer  <- station_file("Fergus_6142400_FERGUS_SHAND_DAM_station_file.txt")
ferE <- eccc("Fergus_6142400_FERGUS_SHAND_DAM_ECCC_daily_2012.csv")
k <- which(DAYS == as.Date("2012-09-29"))
fer$pr[k] <- ferE$pr[k]
write_series(fer, "FERGUS_SHAND_DAM_6142400.txt")

"""Pass-1 configuration. Paths and printed-method constants only."""
from pathlib import Path

PKG613 = Path("/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_6.13_method_new_data-2/Thesis_6.13_method_new_data")
PKGV7 = Path("/home/hatch/workspace/jeremy_wu_redteam/drive_mirror/JW_October_2026/Thesis_v7_defence_framework_new_data-2/Thesis_v7_defence_framework_new_data")
PCIC = Path("/home/hatch/workspace/jeremy_pcic/run_2026-10-19/final")
OUT = Path("/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_grok/pass1/out")
SRC = PKG613 / "2_Data" / "1_Observations" / "a_ECCC_station_sources"
MERGED_AUTHORS = PKG613 / "2_Data" / "1_Observations" / "b_Merged_daily_series"
MODEL_AUTHORS = PKG613 / "2_Data" / "2_Models" / "b_Daily_series"
PCIC_TXT = PCIC / "txt"
PCIC_NC = PCIC / "raw_nc"
PCIC_META = PCIC / "metadata.csv"

STATIONS = ("London", "Fergus", "Harrow")
STATION_COORDS_PRINTED = {
    "Fergus": (43.735, -80.330),
    "London": (43.033, -81.151),
    "Harrow": (42.034, -82.900),
}
# Climpact station-settings latitudes (from climpact_station_settings.txt; allowed as settings doc)
CLIMPACT_LATLON = {
    "London": (43.033, -81.151),
    "Fergus": (43.695, -80.377),
    "Harrow": (42.034, -82.900),
}

MODELS = (
    "ACCESS", "BCC", "CanESM", "CNRM", "EC", "GFDL", "INM", "MIROC", "MRI", "NorESM",
)
MODEL_FULL = {
    "ACCESS": "ACCESS-ESM1-5",
    "BCC": "BCC-CSM2-MR",
    "CanESM": "CanESM5",
    "CNRM": "CNRM-ESM2-1",
    "EC": "EC-Earth3-Veg",
    "GFDL": "GFDL-ESM4",
    "INM": "INM-CM5-0",
    "MIROC": "MIROC-ES2L",
    "MRI": "MRI-ESM2-0",
    "NorESM": "NorESM2-LM",
}
# Five 365-day models as printed
CAL365 = {"BCC", "CanESM", "GFDL", "INM", "NorESM"}
GREGORIAN = {"ACCESS", "CNRM", "EC", "MIROC", "MRI"}

PERIODS = {
    "Historical": (1950, 1986),  # 37 years
    "Present": (1987, 2023),     # 37 years
    "Near": (2024, 2062),        # 39 years
    "Far": (2063, 2100),         # 38 years
}

TEMP_INDICES = [
    "CSDI6", "CSDI3", "WSDI6", "WSDI3", "FD", "ID", "SU", "TR",
    "TNn", "TNx", "TXx", "TXn", "TXm", "TMm", "TNm",
    "TN10p", "TN90p", "TX10p", "TX90p", "DTR", "DTRgt15", "TXb3TNb3",
    "TXge30", "TXgt50p", "GDDgrow10", "TNltm20", "GSL", "CWA", "CWF", "HWA", "HWF",
]
PREC_INDICES = [
    "PRCPTOT", "R10mm", "R20mm", "RX1day", "RX3day", "RX5day", "SDII",
    "R95p", "R95pTOT", "R99p", "R99pTOT", "CDD", "CWD",
]
ALL_INDICES = TEMP_INDICES + PREC_INDICES  # 31 + 13 = 44
assert len(ALL_INDICES) == 44

MONTHLY_INDICES = [
    "TMm", "TXx", "TXn", "ID", "SU", "RX1day", "RX5day", "PRCPTOT", "R10mm",
    "CDD", "SPI3", "SPI6", "SPEI3", "SPEI6",
]
TEMP_REF = {"London": "NorESM", "Fergus": "EC", "Harrow": "EC"}
PREC_REF = {s: "BCC" for s in STATIONS}

# Documented homogenisation candidates (step-02 README; type 0 = never pruned)
# (station, variable tx|tn, year, month, type)
CANDIDATES = [
    ("London", "tx", 1954, 11, 1),
    ("London", "tx", 1989, 11, 1),
    ("London", "tn", 1952, 2, 1),
    ("London", "tn", 1961, 6, 0),  # metadata climatological-day change
    ("London", "tn", 1965, 3, 1),  # pruned in round 2
    ("Fergus", "tx", 1963, 4, 1),
    ("Fergus", "tx", 1965, 12, 1),
    ("Fergus", "tn", 1973, 7, 1),
    ("Fergus", "tn", 1985, 2, 1),  # round-dependent
    ("Fergus", "tn", 1992, 6, 1),
    ("Fergus", "tn", 1994, 4, 1),
    ("Fergus", "tn", 2018, 12, 1),
    ("Harrow", "tx", 1957, 2, 1),  # retained though marginally significant
    ("Harrow", "tx", 1960, 7, 1),
    ("Harrow", "tx", 1969, 3, 1),  # pruned
    ("Harrow", "tx", 2002, 6, 1),
    ("Harrow", "tx", 2010, 4, 1),  # pruned
    ("Harrow", "tn", 1965, 3, 1),
    ("Harrow", "tn", 1978, 11, 1),
    ("Harrow", "tn", 2005, 5, 1),
    ("Harrow", "tn", 2007, 12, 1),
    ("Harrow", "tn", 2010, 4, 1),
]
# Round-2 retained (19 breaks) as documented
RETAINED_19 = [
    ("London", "tx", 1954, 11),
    ("London", "tx", 1989, 11),
    ("London", "tn", 1952, 2),
    ("London", "tn", 1961, 6),
    ("Fergus", "tx", 1963, 4),
    ("Fergus", "tx", 1965, 12),
    ("Fergus", "tn", 1973, 7),
    ("Fergus", "tn", 1985, 2),
    ("Fergus", "tn", 1992, 6),
    ("Fergus", "tn", 1994, 4),
    ("Fergus", "tn", 2018, 12),
    ("Harrow", "tx", 1957, 2),
    ("Harrow", "tx", 1960, 7),
    ("Harrow", "tx", 2002, 6),
    ("Harrow", "tn", 1965, 3),
    ("Harrow", "tn", 1978, 11),
    ("Harrow", "tn", 2005, 5),
    ("Harrow", "tn", 2007, 12),
    ("Harrow", "tn", 2010, 4),
]
RETAINED_18 = [b for b in RETAINED_19 if b != ("Fergus", "tn", 1985, 2)]

NA = -99.9
MAX_MISSING_ANNUAL = 15
MAX_MISSING_MONTHLY = 3
WET_THRESH = 1.0  # mm
BASE_YEARS = (1950, 1986)

PROCESS_GROUPS = {
    "baseline_temperature": ["TMm", "TNm", "TXm", "TNn", "TNx", "TXn", "TXx"],
    "cold_extremes": ["FD", "ID", "TNltm20", "TN10p", "TX10p", "CSDI6", "CSDI3", "CWA", "CWF"],
    "heat_extremes": ["SU", "TR", "TXge30", "TN90p", "TX90p", "TXgt50p", "WSDI6", "WSDI3", "HWA", "HWF", "TXb3TNb3"],
    "growing_season": ["GSL", "GDDgrow10"],
    "diurnal": ["DTR", "DTRgt15"],
    "precip_amount": ["PRCPTOT", "R10mm", "R20mm", "SDII"],
    "precip_intensity": ["RX1day", "RX3day", "RX5day", "R95p", "R95pTOT", "R99p", "R99pTOT"],
    "spells": ["CDD", "CWD"],
}

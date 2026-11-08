# OBS_JJAS.R
# Boxplots of the observed Jun-Sep upper-quartile monthly values, Historical vs Present
# (upper quartile of each month's values per period, lower quartile for TXn), from the monthly
# index workbooks: one of the monthly figures (6.13 Figures 2-7 and D1-D12, v7 Figures 3-8 and
# E1-E12; the COMBINED figures, the single temperature and precipitation figures are written too).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,BCC,NorESM,EC}_<Station>.xlsx (as built by
#          monthly_analysis/step11a_monthly_inputs.R)
# Outputs: 3_Code/output/figures_monthly/<Station>_*.png and .pdf
# Run:     cd <package root> && Rscript 3_Code/step12_figures/OBS_JJAS.R <Station> <temperature model>
#          (London NorESM, Fergus EC, Harrow EC; or run_figures_monthly.R for all of them)
# Original script from S/figs_pcic/R; only the input and output folders were changed.
# ---- v4 update: configuration set from the command line (station) ----
args <- commandArgs(trailingOnly = TRUE)
station      <- args[1]
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
in_dir       <- file.path(DATA, "4_Monthly_analysis")
out_dir      <- out_dir("figures_monthly")
temp_model   <- "EC"
precip_model <- "BCC"
temp_model   <- if (length(args) > 1) args[2] else "EC"
temp_path    <- file.path(in_dir, paste0(temp_model, "_",  station, ".xlsx"))
precip_path  <- file.path(in_dir, paste0("BCC_", station, ".xlsx"))
obs_path     <- file.path(in_dir, paste0("OBS_", station, ".xlsx"))
ec_path      <- file.path(in_dir, paste0(temp_model, "_",  station, ".xlsx"))
# -----------------------------------------------------------------------
############################################################
# 1. Load Required Packages
############################################################
suppressPackageStartupMessages({
  library(readxl)
  library(dplyr)
  library(stringr)
  library(ggplot2)
  library(forcats)
  library(patchwork)
})

############################################################
# 2. Function: Compute Shared Y-Axis Limits per Index
############################################################

compute_shared_limits <- function(dat_ec, dat_obs) {
  all_indices <- sort(unique(c(dat_ec$Index_code, dat_obs$Index_code)))
  limits_list <- vector("list", length(all_indices))
  names(limits_list) <- all_indices
  
  for (idx in all_indices) {
    ec_vals  <- dat_ec$Value[dat_ec$Index_code == idx]
    obs_vals <- dat_obs$Value[dat_obs$Index_code == idx]
    all_vals <- c(ec_vals, obs_vals)
    all_vals <- all_vals[is.finite(all_vals)]
    
    if (length(all_vals) >= 2) {
      q1  <- quantile(all_vals, 0.25, na.rm = TRUE)
      q3  <- quantile(all_vals, 0.75, na.rm = TRUE)
      iqr <- q3 - q1
      lower_iqr <- q1 - 1.5 * iqr
      upper_iqr <- q3 + 1.5 * iqr
      
      lower_p <- quantile(all_vals, 0.01, na.rm = TRUE)
      upper_p <- quantile(all_vals, 0.99, na.rm = TRUE)
      
      lower <- max(min(all_vals), lower_iqr, lower_p)
      upper <- min(max(all_vals), upper_iqr, upper_p)
      
      if (!is.finite(lower) || !is.finite(upper) || lower >= upper) {
        lower <- min(all_vals, na.rm = TRUE)
        upper <- max(all_vals, na.rm = TRUE)
      }
      
      range_val <- upper - lower
      
      pad <- if (range_val < 10) range_val * 0.05 else range_val * 0.02
      pad <- min(pad, range_val * 0.1)
      
      limits_list[[idx]] <- c(lower - pad, upper + pad)
      
    } else if (length(all_vals) == 1) {
      pad <- max(1e-6, abs(all_vals) * 0.05)
      limits_list[[idx]] <- c(all_vals - pad, all_vals + pad)
      
    } else {
      limits_list[[idx]] <- c(0, 1)
    }
  }
  
  limits_list
}

############################################################
# 3. Read OBS Data (London)
############################################################

# [v4] obs_path <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/London/OBS_London.xlsx"

df <- read_excel(obs_path)

# Standardize column names
names(df) <- names(df) |>
  str_replace_all("[^A-Za-z0-9]+","_") |>
  str_replace_all("_+","_") |>
  str_replace_all("^_|_$","") |>
  tolower()

# Ensure first four columns follow expected naming
names(df)[c(1:4)] <- c("year", "month", "index", "observed")

# Construct standardized data frame
dat <- df |>
  transmute(
    Year  = as.integer(year),
    Month = as.integer(month),
    Index = as.character(index),
    Value = suppressWarnings(as.numeric(observed))
  )

############################################################
# 4. Assign Period (Historical vs Present) and Filter for Jun–Sep
############################################################

HIST_START <- 1950L; HIST_END <- 1986L
PRES_START <- 1987L; PRES_END <- 2023L

dat <- dat |>
  mutate(
    Period = dplyr::case_when(
      Year >= HIST_START & Year <= HIST_END ~ "Historical",
      Year >= PRES_START & Year <= PRES_END ~ "Present",
      TRUE ~ NA_character_
    )
  ) |>
  filter(
    Month %in% c(6,7,8,9),       # June–September
    Period %in% c("Historical","Present"),
    !is.na(Value),
    Value != -99.9              # Remove invalid values
  )

############################################################
# 5. Index Groups + Tail-Based 25% Selection
# ---------------------------------------------------------
# temp_indices: temperature-related indices
# precip_indices: precipitation / drought-related indices
############################################################

temp_indices   <- c("SU","TXX","TXN")
precip_indices <- c("SPEI3","SPEI6","SPI3","SPI6","CDD","PRCPTOT","R10MM","RX1DAY","RX5DAY")
keep_indices   <- c(temp_indices, precip_indices)

cold_indices <- c("TXN")  # indices using lower tail

dat <- dat |>
  mutate(Index_code = toupper(trimws(Index))) |>
  filter(Index_code %in% keep_indices) |>
  group_by(Index_code, Period, Month) |>
  mutate(
    p25 = quantile(Value, 0.25, na.rm = TRUE),
    p75 = quantile(Value, 0.75, na.rm = TRUE)
  ) |>
  ungroup() |>
  filter(
    (Index_code %in% cold_indices  & Value <= p25) |
      (!Index_code %in% cold_indices & Value >= p75)
  ) |>
  select(-p25, -p75)

############################################################
# 6. Read EC (GCM) Data for London + Apply Same Filtering
############################################################

# [v4] ec_path <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/London/EC_London.xlsx"

dat_ec <- read_excel(ec_path)
names(dat_ec)[1:4] <- c("year", "month", "index", "EC")

dat_ec <- dat_ec |>
  transmute(
    Year       = as.integer(year),
    Month      = as.integer(month),
    Index      = as.character(index),
    Index_code = toupper(trimws(index)),
    Value      = suppressWarnings(as.numeric(EC))
  ) |>
  filter(
    !is.na(Value),
    Value != -99.9,
    Month %in% c(6,7,8,9)
  ) |>
  mutate(
    Period = case_when(
      Year >= HIST_START & Year <= HIST_END ~ "Historical",
      Year >= PRES_START & Year <= PRES_END ~ "Present",
      TRUE ~ NA_character_
    )
  ) |>
  filter(
    Period %in% c("Historical","Present"),
    Index_code %in% keep_indices
  ) |>
  group_by(Index_code, Period, Month) |>
  mutate(
    p25 = quantile(Value, 0.25, na.rm = TRUE),
    p75 = quantile(Value, 0.75, na.rm = TRUE)
  ) |>
  ungroup() |>
  filter(
    (Index_code %in% cold_indices & Value <= p25) |
      (!Index_code %in% cold_indices & Value >= p75)
  ) |>
  select(-p25, -p75)

############################################################
# 7. Compute Shared OBS–GCM Y-Axis Limits per Index
############################################################

shared_limits <- compute_shared_limits(dat_ec, dat)

############################################################
# 8. Build Labels, Panel Order, and Month Factor Levels
############################################################

label_map <- c(
  "SU"      = "SU (Summer Days)",
  "TXX"     = "TXx (Hottest Day)",
  "TXN"     = "TXn (Coldest Day)",
  "PRCPTOT" = "PRCPTOT (Total Precipitation)",
  "R10MM"   = "R10mm (Heavy Rain Days)",
  "RX1DAY"  = "RX1day (Maximum 1-day precipitation)",
  "RX5DAY"  = "RX5day (Maximum 5-day precipitation)",
  "CDD"     = "CDD (Consecutive Dry Days)",
  "SPEI3"   = "SPEI-3 (3-month SPEI)",
  "SPEI6"   = "SPEI-6 (6-month SPEI)",
  "SPI3"    = "SPI-3 (3-month SPI)",
  "SPI6"    = "SPI-6 (6-month SPI)"
)

panel_order <- c(
  "SU",
  "TXX",
  "TXN",
  "SPEI3",
  "SPEI6",
  "SPI3",
  "SPI6",
  "CDD",
  "RX1DAY",
  "RX5DAY",
  "PRCPTOT",
  "R10MM"
)

present_codes <- unique(dat$Index_code)
ordered_codes <- c(
  panel_order[panel_order %in% present_codes],
  setdiff(present_codes, panel_order)
)

wrap_lab <- function(x, width = 28) stringr::str_wrap(x, width)

dat <- dat |>
  mutate(
    Index_label_raw = ifelse(Index_code %in% names(label_map),
                             label_map[Index_code], Index_code),
    Index_label = factor(
      wrap_lab(Index_label_raw, 28),
      levels = wrap_lab(ifelse(ordered_codes %in% names(label_map),
                               label_map[ordered_codes], ordered_codes), 28)
    ),
    Period    = factor(Period, levels = c("Historical","Present")),
    Month_lab = factor(
      Month, levels = c(6,7,8,9),
      labels = c("Jun","Jul","Aug","Sep")
    )
  )


############################################################
# 9. Unit Mapping and Y-Axis Title Helper
############################################################

unit_map <- c(
  "SU"      = "Days",
  "TXX"     = "°C",
  "TXN"     = "°C",
  "CDD"     = "Days",
  "SPI3"   = "",
  "SPI6"   = "",
  "SPEI3"   = "",
  "SPEI6"   = "",
  "PRCPTOT" = "mm",
  "R10MM"   = "Days",
  "RX1DAY"  = "mm",
  "RX5DAY"  = "mm"
)

y_title_for <- function(code) {
  if (code %in% c("SPEI3","SPEI6","SPI3","SPI6")) return("")
  u <- unit_map[[code]]
  if (is.null(u)) return("")
  u
}


############################################################
# 10. Color Palette (Historical vs Present)
############################################################

pal <- c(
  "Historical" = "#3B4CC0",
  "Present"    = "#CC79A7"
)


############################################################
# 11. Panel Plot Builder for Each Index
############################################################

make_panel <- function(code) {
  
  this_dat <- dplyr::filter(dat, Index_code == code)
  this_lab <- unique(this_dat$Index_label)
  y_lab    <- y_title_for(code)
  
  # Use shared OBS+EC limits
  ylims <- shared_limits[[code]]
  
  # Fallback if missing
  if (is.null(ylims)) {
    vals <- this_dat$Value
    vals <- vals[is.finite(vals)]
    if (length(vals) >= 2) {
      q1  <- quantile(vals, 0.25, na.rm = TRUE)
      q3  <- quantile(vals, 0.75, na.rm = TRUE)
      iqr <- q3 - q1
      
      lower_iqr <- q1 - 1.5 * iqr
      upper_iqr <- q3 + 1.5 * iqr
      
      lower_p <- quantile(vals, 0.01, na.rm = TRUE)
      upper_p <- quantile(vals, 0.99, na.rm = TRUE)
      
      lower <- max(min(vals), lower_iqr, lower_p)
      upper <- min(max(vals), upper_iqr, upper_p)
      
      if (!is.finite(lower) || !is.finite(upper) || lower >= upper) {
        lower <- min(vals)
        upper <- max(vals)
      }
      
      range_val <- upper - lower
      pad <- if (range_val < 10) range_val * 0.05 else range_val * 0.02
      pad <- min(pad, range_val * 0.1)
      
      ylims <- c(lower - pad, upper + pad)
      
    } else {
      ylims <- c(0, 1)
    }
  }
  
  ggplot(this_dat, aes(x = Month_lab, y = Value, fill = Period)) +
    geom_boxplot(
      width         = 0.65,
      position      = position_dodge(width = 0.75),
      # --- 修改处：加深离群点颜色，提高不透明度 ---
      outlier.shape = 16,            
      outlier.size  = 1.2,           
      outlier.alpha = 0.8,             # 将透明度从 0.5 提高到 0.8，让颜色更实
      outlier.colour = "darkred"       # 改为深红色
    ) +
    scale_fill_manual(
      values = pal,
      name   = NULL,
      limits = c("Historical","Present"),
      drop   = FALSE
    ) +
    scale_y_continuous(
      limits = ylims,
      expand = expansion(mult = 0.05) 
    ) +
    labs(
      title = as.character(this_lab),
      x = NULL,
      y = y_lab
    ) +
    theme_bw() +
    theme(
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      plot.title       = element_text(face = "bold", hjust = 0.5),
      
      # --- 修改处：XY 轴刻度和标题全部放大并加粗 ---
      axis.text.x      = element_text(vjust = 0.5, size = 12, face = "bold"),
      axis.text.y      = element_text(size = 12, face = "bold"),
      axis.title.x     = element_text(size = 14, face = "bold"),
      axis.title.y     = if (nzchar(y_lab)) {
        element_text(size = 14, face = "bold", margin = margin(r = 4))
      } else {
        element_blank()
      }
    )
}

############################################################
# 12. Generate Panels (Temp vs Precip), Combine, and Save
############################################################

# Split ordered_codes into temperature-related and precipitation-related groups
temp_codes   <- ordered_codes[ordered_codes %in% temp_indices]
precip_codes <- ordered_codes[ordered_codes %in% precip_indices]

# Temperature-related figure
plots_temp <- lapply(temp_codes, make_panel)

panels_temp <- wrap_plots(plots_temp, ncol = 3) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    
    # --- 修改处：图例文字放大并加粗，稍微放大色块 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

final_plot_temp <- panels_temp + plot_annotation(
  title = paste0("OBS ", station, " | Jun–Sep Temperature-related indices\nHistorical vs Present"),
  theme = theme(
    plot.title      = element_text(face = "bold", hjust = 0.5),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

# Precipitation-related figure
plots_precip <- lapply(precip_codes, make_panel)

panels_precip <- wrap_plots(plots_precip, ncol = 3) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    
    # --- 修改处：图例文字放大并加粗，稍微放大色块 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

final_plot_precip <- panels_precip + plot_annotation(
  title = paste0("OBS ", station, " | Jun–Sep Precipitation-related indices\nHistorical vs Present"),
  theme = theme(
    plot.title      = element_text(face = "bold", hjust = 0.5),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

# Save both outputs
# [v4] out_dir <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results"

out_png_temp   <- file.path(out_dir, paste0(station, "_panel_OBS_JunSep_Temp.png"))
out_png_precip <- file.path(out_dir, paste0(station, "_panel_OBS_JunSep_Precip.png"))

ggsave(out_png_temp,   final_plot_temp,   width = 12, height = 6, dpi = 600, bg = "white")
ggsave(out_png_precip, final_plot_precip, width = 12, height = 16, dpi = 600, bg = "white")

message("Saved temperature-related figure: ", out_png_temp)
message("Saved precipitation-related figure: ", out_png_precip)

############################################################
# 12. Generate Panels (Temp vs Precip), Combine, and Save
############################################################

# ... (这里保留你原来的绘图逻辑，即 final_plot_temp 和 final_plot_precip 的生成过程) ...

# 1. 定义输出目录
# [v4] out_dir <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results"

# 2. 定义所有输出文件的完整路径
out_png_temp   <- file.path(out_dir, paste0(station, "_panel_OBS_JunSep_Temp.png"))
out_png_precip <- file.path(out_dir, paste0(station, "_panel_OBS_JunSep_Precip.png"))
out_pdf_temp   <- file.path(out_dir, paste0(station, "_panel_OBS_JunSep_Temp.pdf"))
out_pdf_precip <- file.path(out_dir, paste0(station, "_panel_OBS_JunSep_Precip.pdf"))

# 3. 执行保存操作 (PNG)
ggsave(out_png_temp,   final_plot_temp,   width = 12, height = 6,  dpi = 600, bg = "white")
ggsave(out_png_precip, final_plot_precip, width = 12, height = 16, dpi = 600, bg = "white")

# 4. 执行保存操作 (PDF)
ggsave(out_pdf_temp,   final_plot_temp,   width = 12, height = 6,  bg = "white")
ggsave(out_pdf_precip, final_plot_precip, width = 12, height = 16, bg = "white")

# 5. 打印消息通知
message("All figures saved to: ", out_dir)
message("Created PNGs: ", basename(out_png_temp), ", ", basename(out_png_precip))
message("Created PDFs: ", basename(out_pdf_temp), ", ", basename(out_pdf_precip))
# =========================
# v4 update: Combined figure, same layout as the GCM scripts
# =========================
suppressPackageStartupMessages(library(cowplot))
combined_plot <- plot_grid(panels_precip, panels_temp, ncol = 1, rel_heights = c(16, 6.5),
                           labels = c("(a)", "(b)"), label_size = 18, hjust = 0, label_x = 0.005)
ggsave(file.path(out_dir, paste0(station, "_OBS_JunSep_PRECIP_TEMP_Hist_vs_Present_COMBINED.png")), combined_plot, width = 12, height = 22.5, dpi = 600, bg = "white")
ggsave(file.path(out_dir, paste0(station, "_OBS_JunSep_PRECIP_TEMP_Hist_vs_Present_COMBINED.pdf")), combined_plot, width = 12, height = 22.5, bg = "white")

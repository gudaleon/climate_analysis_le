# OBS_JFM.R
# Boxplots of the observed Jan-Mar upper-quartile monthly values, Historical vs Present
# (upper quartile of each month's values per period, lower quartile for TXn), from the monthly
# index workbooks: one of the monthly figures (6.13 Figures 2-7 and D1-D12, v7 Figures 3-8 and
# E1-E12; the COMBINED figures, the single temperature and precipitation figures are written too).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,BCC,NorESM,EC}_<Station>.xlsx (as built by
#          monthly_analysis/step11a_monthly_inputs.R)
# Outputs: 3_Code/output/figures_monthly/<Station>_*.png and .pdf
# Run:     cd <package root> && Rscript 3_Code/step12_figures/OBS_JFM.R <Station> <temperature model>
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
# 3. Read OBS Data (Harrow, non-homogenized)
############################################################

# [v4] obs_path <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/Harrow/OBS_Harrow.xlsx"

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
# 4. Assign Period (Historical vs Present) and Filter for Jan–Mar
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
    Month %in% c(1,2,3),       # Jan–Mar
    Period %in% c("Historical","Present"),
    !is.na(Value),
    Value != -99.9             # Remove invalid values
  )

############################################################
# 5. Index Groups + Tail-Based 25% Selection
# ---------------------------------------------------------
# temp_indices: temperature-related indices
# precip_indices: precipitation-related indices
############################################################

temp_indices   <- c("TMM","TXX","TXN","ID")
precip_indices <- c("PRCPTOT","R10MM","RX1DAY","RX5DAY")
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
# 6. Read EC (GCM) Data for Harrow + Apply Same Filtering
############################################################

# [v4] ec_path <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/Harrow/EC_Harrow.xlsx"

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
    Month %in% c(1,2,3)        # Jan–Mar
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
  "TMM"="TMM (Mean Temperature)",
  "TXX"="TXx (Hottest Day)",
  "TXN"="TXn (Coldest Day)",
  "ID" ="ID (Ice Days)",
  "RX1DAY" ="RX1DAY (Wettest Day)",
  "RX5DAY" ="RX5DAY (Max 5-day Precipitation)",
  "PRCPTOT"="PRCPTOT (Total Precipitation)",
  "R10MM" ="R10MM (Heavy Rain Days)"
)

panel_order <- c(
  "TMM","TXX","TXN","ID",
  "RX1DAY","RX5DAY","PRCPTOT","R10MM"
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
      levels = wrap_lab(
        ifelse(ordered_codes %in% names(label_map),
               label_map[ordered_codes], ordered_codes),
        28
      )
    ),
    Period    = factor(Period, levels = c("Historical","Present")),
    Month_lab = factor(
      Month, levels = c(1,2,3),
      labels = c("Jan","Feb","Mar")
    )
  )

############################################################
# 9. Unit Mapping and Y-Axis Title Helper
############################################################

unit_map <- c(
  "TMM"     = "°C",
  "TXX"     = "°C",
  "TXN"     = "°C",
  "ID"      = "Days",
  "PRCPTOT" = "mm",
  "R10MM"   = "Days",
  "RX1DAY"  = "mm",
  "RX5DAY"  = "mm"
)

y_title_for <- function(code) {
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
  
  ggplot(this_dat, aes(x = Month_lab, y = Value, fill = Period, color = Period)) + # 新增 color 映射
    geom_boxplot(
      width         = 0.65,
      position      = position_dodge(width = 0.75),
      # --- 修改：取消隐藏，设置离群点样式与颜色同步 ---
      color        = "black", 
      outlier.shape  = 16,    # 实心圆
      outlier.size   = 1.5,   # 点大小
      outlier.alpha  = 0.8,   # 透明度
      outlier.colour = "darkred"      
    ) +
    scale_fill_manual(
      values = pal,
      name   = NULL,
      limits = c("Historical","Present"),
      drop   = FALSE
    ) +
    scale_color_manual(       # 新增：确保离群点颜色与箱体颜色一致
      values = pal,
      name   = NULL,
      limits = c("Historical","Present"),
      drop   = FALSE
    ) +
    scale_y_continuous(
      limits = ylims,
      # --- 修改：增加 5% 留白确保离群点不被切掉 ---
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
      
      # 1. 修改 X 轴和 Y 轴的刻度文字（月份和具体数字）：变大并加粗
      axis.text.x      = element_text(vjust = 0.5, size = 12, face = "bold"),
      axis.text.y      = element_text(size = 12, face = "bold"),
      
      # 2. 修改 X 轴标题（虽然目前是 NULL，但加上备用）：变大并加粗
      axis.title.x     = element_text(size = 14, face = "bold"),
      
      # 3. 修改 Y 轴标题（单位标签）：变大并加粗
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

panels_temp <- wrap_plots(plots_temp, ncol = 2) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    
    # --- 新增：放大图例文字并加粗，稍微调大图例色块 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"), 
    
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

final_plot_temp <- panels_temp + plot_annotation(
  title = paste0("OBS ", station, " | Jan–Mar Temperature-related indices\nHistorical vs Present"),
  theme = theme(
    plot.title      = element_text(face = "bold", hjust = 0.5),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

# Precipitation-related figure
plots_precip <- lapply(precip_codes, make_panel)

panels_precip <- wrap_plots(plots_precip, ncol = 2) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    
    # --- 新增：放大图例文字并加粗，稍微调大图例色块 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

final_plot_precip <- panels_precip + plot_annotation(
  title = paste0("OBS ", station, " | Jan–Mar Precipitation-related indices\nHistorical vs Present"),
  theme = theme(
    plot.title      = element_text(face = "bold", hjust = 0.5),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

# Save both outputs
# [v4] out_dir <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results"

out_png_temp   <- file.path(out_dir, paste0(station, "_panel_OBS_JanMar_Temp.png"))
out_png_precip <- file.path(out_dir, paste0(station, "_panel_OBS_JanMar_Precip.png"))

ggsave(out_png_temp,   final_plot_temp,   width = 8, height = 12, dpi = 600, bg = "white")
ggsave(out_png_precip, final_plot_precip, width = 8, height = 12, dpi = 600, bg = "white")

message("Saved temperature-related figure: ", out_png_temp)
message("Saved precipitation-related figure: ", out_png_precip)

# 定义保存路径
out_png_temp   <- file.path(out_dir, paste0(station, "_panel_OBS_JanMar_Temp.png"))
out_pdf_temp   <- file.path(out_dir, paste0(station, "_panel_OBS_JanMar_Temp.pdf"))
out_png_precip <- file.path(out_dir, paste0(station, "_panel_OBS_JanMar_Precip.png"))
out_pdf_precip <- file.path(out_dir, paste0(station, "_panel_OBS_JanMar_Precip.pdf"))

# 保存 Temperature (PNG + PDF)
ggsave(out_png_temp, final_plot_temp, width = 8, height = 12, dpi = 600, bg = "white")
ggsave(out_pdf_temp, final_plot_temp, width = 8, height = 12, bg = "white")

# 保存 Precipitation (PNG + PDF)
ggsave(out_png_precip, final_plot_precip, width = 8, height = 12, dpi = 600, bg = "white")
ggsave(out_pdf_precip, final_plot_precip, width = 8, height = 12, bg = "white")

message("Saved PNG and PDF files to: ", out_dir)
# =========================
# v4 update: Combined figure, same layout as the GCM scripts
# =========================
suppressPackageStartupMessages(library(cowplot))
plots_all <- list(
  plots_precip[[1]], plots_precip[[2]], plots_temp[[1]], plots_temp[[2]],
  plots_precip[[3]], plots_precip[[4]], plots_temp[[3]], plots_temp[[4]]
)
grid_all <- wrap_plots(plots_all, ncol = 4) +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom", legend.text = element_text(size = 12, face = "bold"),
        legend.key.size = unit(1.5, "lines"),
        plot.background = element_rect(fill = "white", color = NA),
        panel.background = element_rect(fill = "white", color = NA))
combined_plot <- plot_grid(grid_all) +
  draw_label("(a)", x = 0.01, y = 0.99, hjust = 0, vjust = 1, fontface = "bold", size = 18) +
  draw_label("(b)", x = 0.51, y = 0.99, hjust = 0, vjust = 1, fontface = "bold", size = 18)
ggsave(file.path(out_dir, paste0(station, "_OBS_JanMar_PRECIP_TEMP_Hist_vs_Present_COMBINED.png")), combined_plot, width = 16, height = 12, dpi = 600, bg = "white")
ggsave(file.path(out_dir, paste0(station, "_OBS_JanMar_PRECIP_TEMP_Hist_vs_Present_COMBINED.pdf")), combined_plot, width = 16, height = 12, bg = "white")

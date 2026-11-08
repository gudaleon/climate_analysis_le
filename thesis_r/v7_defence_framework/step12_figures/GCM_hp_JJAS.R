# GCM_hp_JJAS.R
# Boxplots of the reference models Jun-Sep, Historical vs Present
# (upper quartile of each month's values per period, lower quartile for TXn), from the monthly
# index workbooks: one of the monthly figures (6.13 Figures 2-7 and D1-D12, v7 Figures 3-8 and
# E1-E12; the COMBINED figures, the single temperature and precipitation figures are written too).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,BCC,NorESM,EC}_<Station>.xlsx (as built by
#          monthly_analysis/step11a_monthly_inputs.R)
# Outputs: 3_Code/output/figures_monthly/<Station>_*.png and .pdf
# Run:     cd <package root> && Rscript 3_Code/step12_figures/GCM_hp_JJAS.R <Station> <temperature model>
#          (London NorESM, Fergus EC, Harrow EC; or run_figures_monthly.R for all of them)
# Original script from S/figs_pcic/R; only the input and output folders were changed.
# ---- v4 update: configuration set from the command line (station) ----
args <- commandArgs(trailingOnly = TRUE)
station      <- args[1]
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
in_dir       <- file.path(DATA, "4_Monthly_analysis")
out_dir      <- out_dir("figures_monthly")
temp_model   <- if (length(args) > 1) args[2] else "EC"
precip_model <- "BCC"
temp_path    <- file.path(in_dir, paste0(temp_model, "_",  station, ".xlsx"))
precip_path  <- file.path(in_dir, paste0("BCC_", station, ".xlsx"))
obs_path     <- file.path(in_dir, paste0("OBS_", station, ".xlsx"))
ec_path      <- file.path(in_dir, paste0(temp_model, "_",  station, ".xlsx"))
# -----------------------------------------------------------------------
############################################################
# 0. Packages
############################################################
suppressPackageStartupMessages({
  library(readxl); library(dplyr); library(stringr)
  library(ggplot2); library(forcats)
  library(patchwork); library(cowplot)
})

############################################################
# ★ Configuration 
############################################################
# [v4] station      <- "Harrow"          # 站名(标题与文件名用)
window_label <- "Jun–Sep"         # 窗口(标题里显示)
window_tag   <- "JunSep"          # 窗口(文件名里用)
# [v4] temp_model   <- "MIROC"   # 温度模型(标题/文件名显示)
# [v4] precip_model <- "BCC"             # 降水模型(标题/文件名显示)

# [v4] temp_path   <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/Harrow/MIROC_Harrow.xlsx"  # 温度指数用的模型数据
# [v4] precip_path <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/Harrow/BCC_Harrow.xlsx" # 降水/干旱指数用的模型
############################################################

############################################################
# 1. Function: Robust Shared Y-Axis Limits 
############################################################
compute_shared_limits <- function(dat_BCC, dat_obs) {
  all_indices <- sort(unique(c(dat_BCC$Index_code, dat_obs$Index_code)))
  limits_list <- vector("list", length(all_indices))
  names(limits_list) <- all_indices
  
  for (idx in all_indices) {
    BCC_vals  <- dat_BCC$Value[dat_BCC$Index_code == idx]
    obs_vals <- dat_obs$Value[dat_obs$Index_code == idx]
    all_vals <- c(BCC_vals, obs_vals)
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
# 2. Read data  (温度模型 + 降水模型)
############################################################
read_one <- function(path) {
  d <- read_excel(path)
  names(d) <- names(d) |>
    str_replace_all("[^A-Za-z0-9]+","_") |>
    str_replace_all("_+","_") |>
    str_replace_all("^_|_$","") |>
    tolower()
  vcol <- setdiff(names(d), c("year","month","index"))[1]      # 自动识别数值列
  stopifnot(all(c("year","month","index") %in% names(d)), !is.na(vcol))
  d$bcc <- suppressWarnings(as.numeric(d[[vcol]]))             # 统一改名成 bcc,下游代码不动
  d
}

df_temp   <- read_one(temp_path)
df_precip <- read_one(precip_path)

############################################################
# 3. Indices definition
############################################################
keep_indices <- c(
  "SU", "TXX", "TXN",                 # temperature
  "SPEI3", "SPEI6", "SPI3", "SPI6",   # drought indices
  "CDD",
  "RX1DAY", "RX5DAY",                 # daily extremes
  "PRCPTOT", "R10MM"                  # total precip
)

temp_indices   <- c("SU", "TXX", "TXN")
precip_indices <- c("PRCPTOT", "R10MM", "RX1DAY", "RX5DAY", "SPEI3", "SPEI6", "SPI3", "SPI6", "CDD")

############################################################
# 4. Build main data (Jun–Sep, Hist vs Present)
############################################################
df <- dplyr::bind_rows(                                       # 温度指数取温度模型,其余取降水模型
  dplyr::filter(df_temp,   toupper(trimws(index)) %in% temp_indices),
  dplyr::filter(df_precip, !toupper(trimws(index)) %in% temp_indices)
)

dat <- df |>
  transmute(
    Year  = as.integer(.data[["year"]]),
    Month = as.integer(.data[["month"]]),
    Index = as.character(.data[["index"]]),
    Value = suppressWarnings(as.numeric(.data[["bcc"]]))
  ) |>
  mutate(
    Period = dplyr::case_when(
      Year >= 1950L & Year <= 1986L ~ "Historical",
      Year >= 1987L & Year <= 2023L ~ "Present",
      TRUE ~ NA_character_
    )
  ) |>
  # keep only Jun–Sep and valid values
  filter(
    Month %in% c(6L, 7L, 8L, 9L),
    Period %in% c("Historical","Present"),
    !is.na(Value),
    Value != -99.9
  ) |>
  mutate(Index_code = toupper(trimws(Index))) |>
  filter(Index_code %in% keep_indices) |>
  group_by(Index_code, Period, Month) |>
  mutate(
    p25 = quantile(Value, 0.25, na.rm = TRUE),
    p75 = quantile(Value, 0.75, na.rm = TRUE)
  ) |>
  ungroup()

dat_full <- dat

############################################################
# 5. Tail-based filter (TXN bottom 25%, others top 25%)
############################################################
cold_indices <- c("TXN")

dat <- dat |>
  filter(
    (Index_code %in% cold_indices  & Value <= p25) |
      (!Index_code %in% cold_indices & Value >= p75)
  ) |>
  select(-p25, -p75)

############################################################
# 6. Compute robust BCC-only Y-axis limits (per index)
############################################################
shared_limits <- compute_shared_limits(dat, dat)

############################################################
# 7. Label mapping & factor levels
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
  "SU","TXX","TXN",
  "SPEI3","SPEI6","SPI3","SPI6","CDD",
  "RX1DAY","RX5DAY","PRCPTOT","R10MM")

present_codes <- unique(dat$Index_code)

ordered_codes <- c(
  panel_order[panel_order %in% present_codes],
  setdiff(present_codes, panel_order)
)

wrap_lab <- function(x, width = 28) stringr::str_wrap(x, width = width)

dat <- dat |>
  mutate(
    Index_label_raw = ifelse(Index_code %in% names(label_map), label_map[Index_code], Index_code),
    Index_label     = factor(
      wrap_lab(Index_label_raw, width = 28),
      levels = wrap_lab(
        ifelse(
          ordered_codes %in% names(label_map),
          label_map[ordered_codes],
          ordered_codes
        ),
        28
      )
    ),
    Period    = factor(Period, levels = c("Historical","Present")),
    Month_lab = factor(
      Month,
      levels = c(6,7,8,9),
      labels = c("Jun","Jul","Aug","Sep")
    )
  )

############################################################
# 8. Units
############################################################
unit_map <- c(
  "SU"      = "Days",
  "TXX"     = "°C",
  "TXN"     = "°C",
  "SPEI3"   = "",
  "SPEI6"   = "",
  "SPI3"    = "",
  "SPI6"    = "",
  "CDD"     = "Days",
  "RX1DAY"  = "mm",
  "RX5DAY"  = "mm",
  "PRCPTOT" = "mm",
  "R10MM"   = "Days"
)


y_title_for <- function(code) {
  if (code %in% c("SPEI3","SPEI6")) return("")  
  u <- unit_map[[code]]
  if (is.null(u)) return("")
  u
}

############################################################
# 9. Plot function（加上 shared_limits）
############################################################
pal <- c("Historical"="#3B4CC0", "Present"="#CC79A7")

make_panel <- function(code) {
  this_dat <- dplyr::filter(dat, Index_code == code)
  this_lab <- unique(this_dat$Index_label)
  y_lab    <- y_title_for(code)
  
  ylims <- shared_limits[[code]]
  
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
        lower <- min(vals, na.rm = TRUE)
        upper <- max(vals, na.rm = TRUE)
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
      color         = "black",      
      # --- 修改处：离群点变深红、放大、提高不透明度 ---
      outlier.shape  = 16,    
      outlier.size   = 1.2,   
      outlier.alpha  = 0.8,   
      outlier.colour = "darkred" 
    ) +
    scale_fill_manual(
      values = pal, name = NULL,
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
      
      # --- 修改处：小标题和XY轴全部放大并加粗 ---
      plot.title       = element_text(face = "bold", hjust = 0.5, size = 12), # 小标题调到 12
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
# 10. Temperature vs Precipitation panels
############################################################

ncol_temp   <- 3   
ncol_precip <- 3  

temp_codes   <- intersect(ordered_codes, temp_indices)
precip_codes <- intersect(ordered_codes, precip_indices)

plots_temp   <- lapply(temp_codes, make_panel)
plots_precip <- lapply(precip_codes, make_panel)

# Temp-related
temp_panels_with_legend <- wrap_plots(plots_temp, ncol = ncol_temp) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    # --- 修改处：图例文字放大并加粗，色块放大 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

temp_final_plot <- temp_panels_with_legend + plot_annotation(
  title = paste0(temp_model, " | ", window_label, " temperature indices (Historical vs Present)"),
  theme = theme(
    # --- 修改处：主标题放大到 16，镇住全场 ---
    plot.title     = element_text(face = "bold", hjust = 0.5, size = 16),
    plot.background= element_rect(fill = "white", color = NA)
  )
)

# Prep-related
precip_panels_with_legend <- wrap_plots(plots_precip, ncol = ncol_precip) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    # --- 修改处：图例文字放大并加粗，色块放大 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

precip_final_plot <- precip_panels_with_legend + plot_annotation(
  title = paste0(precip_model, " | ", window_label, " precipitation indices (Historical vs Present)"),
  theme = theme(
    # --- 修改处：主标题放大到 16 ---
    plot.title     = element_text(face = "bold", hjust = 0.5, size = 16),
    plot.background= element_rect(fill = "white", color = NA)
  )
)

# =========================
# 11. Combined: (a) Precipitation/Drought (上) / (b) Temperature (下)
#     统一网格 —— 所有 panel 等高
# =========================
plots_all <- c(plots_precip, plots_temp)   # 9 降水 + 3 温度 = 12 -> ncol=3 = 4 行(前3行降水,第4行温度)

grid_all <- wrap_plots(plots_all, ncol = 3) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

# (a) 顶部(降水块);(b) 第 4 行(温度块)顶部
combined_plot <- plot_grid(grid_all) +
  draw_label("(a)", x = 0.005, y = 0.99, hjust = 0, vjust = 1, fontface = "bold", size = 18) +
  draw_label("(b)", x = 0.005, y = 0.28, hjust = 0, vjust = 1, fontface = "bold", size = 18)

out_png_combined <- file.path(out_dir, paste0(station, "_GCM_", window_tag, "_PRECIP_TEMP_Hist_vs_Present_COMBINED.png"))
out_pdf_combined <- file.path(out_dir, paste0(station, "_GCM_", window_tag, "_PRECIP_TEMP_Hist_vs_Present_COMBINED.pdf"))

ggsave(out_png_combined, combined_plot, width = 12, height = 20, dpi = 600, bg = "white")
ggsave(out_pdf_combined, combined_plot, width = 12, height = 20, bg = "white")

message("Saved combined figure to: ", out_dir)
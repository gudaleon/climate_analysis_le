# GCM_nf_JJAS.R
# Boxplots of the reference models Jun-Sep, Near vs Far future
# (upper quartile of each month's values per period, lower quartile for TXn), from the monthly
# index workbooks: one of the monthly figures (6.13 Figures 2-7 and D1-D12, v7 Figures 3-8 and
# E1-E12; the COMBINED figures, the single temperature and precipitation figures are written too).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,BCC,NorESM,EC}_<Station>.xlsx (as built by
#          monthly_analysis/step11a_monthly_inputs.R)
# Outputs: 3_Code/output/figures_monthly/<Station>_*.png and .pdf
# Run:     cd <package root> && Rscript 3_Code/step12_figures/GCM_nf_JJAS.R <Station> <temperature model>
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
# =========================
# Packages
# =========================
suppressPackageStartupMessages({
  library(readxl); library(dplyr); library(stringr)
  library(ggplot2); library(forcats)
  library(patchwork); library(cowplot)   
})

# =========================
# ★ Configuration —— 每个站只改这里
# =========================
# [v4] station      <- "Harrow"
window_label <- "Jun–Sep"
window_tag   <- "JunSep"
period_label <- "Near future vs Far future"   # 标题里显示
period_tag   <- "Near_vs_Far"                 # 文件名里用
# [v4] temp_model   <- "MRI"   # 温度模型
# [v4] precip_model <- "BCC"             # 降水模型
# [v4] out_dir      <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results"
# [v4] temp_path    <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/Harrow/MIROC_Harrow.xlsx"  # 温度模型数据
# [v4] precip_path  <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/Harrow/BCC_Harrow.xlsx" # 降水模型数据

# =========================
# 0. Robust shared y-axis limits
# =========================
compute_shared_limits <- function(dat_BCC, dat_obs) {
  all_indices <- sort(unique(c(dat_BCC$Index_code, dat_obs$Index_code)))
  limits_list <- vector("list", length(all_indices))
  names(limits_list) <- all_indices
  
  for (idx in all_indices) {
    BCC_vals  <- dat_BCC$Value[dat_BCC$Index_code == idx]
    obs_vals  <- dat_obs$Value[dat_obs$Index_code == idx]
    all_vals  <- c(BCC_vals, obs_vals)
    all_vals  <- all_vals[is.finite(all_vals)]
    
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

# =========================
# 1. Read data  (温度模型 + 降水模型)
# =========================
read_one <- function(path) {
  d <- read_excel(path)
  names(d) <- names(d) |>
    str_replace_all("[^A-Za-z0-9]+","_") |>
    str_replace_all("_+","_") |>
    str_replace_all("^_|_$","") |>
    tolower()
  vcol <- setdiff(names(d), c("year","month","index"))[1]   # 自动识别数值列
  stopifnot(all(c("year","month","index") %in% names(d)), !is.na(vcol))
  d$bcc <- suppressWarnings(as.numeric(d[[vcol]]))           # 统一改名成 bcc,下游不动
  d
}

df_temp   <- read_one(temp_path)
df_precip <- read_one(precip_path)

temp_set <- c("SU","TXX","TXN")                              # 温度指数取温度模型,其余取降水模型
df <- dplyr::bind_rows(
  dplyr::filter(df_temp,   toupper(trimws(index)) %in% temp_set),
  dplyr::filter(df_precip, !toupper(trimws(index)) %in% temp_set)
)
stopifnot(all(c("year","month","index","bcc") %in% names(df)))

dat <- df |>
  transmute(
    Year  = as.integer(.data[["year"]]),
    Month = as.integer(.data[["month"]]),
    Index = as.character(.data[["index"]]),
    Value = suppressWarnings(as.numeric(.data[["bcc"]]))
  )

# =========================
# 2. Indices definition
# =========================
keep_indices <- c(
  "SU", "TXX", "TXN",                 # temperature-related
  "SPEI3", "SPEI6", "SPI3", "SPI6",   # drought / hydro-related
  "CDD",                              
  "RX1DAY", "RX5DAY",                 # precipitation extremes
  "PRCPTOT", "R10MM"                  # total precip & heavy rain days
)

temp_indices   <- c("SU", "TXX", "TXN")
precip_indices <- c("PRCPTOT", "R10MM", "RX1DAY", "RX5DAY",
                    "SPEI3", "SPEI6", "SPI3", "SPI6", "CDD")

# =========================
# 3. Define periods and filter months (Jun–Sep)
# =========================
HIST_START <- 1950L; HIST_END <- 1986L
NEAR_START <- 2024L; NEAR_END <- 2062L
FAR_START  <- 2063L; FAR_END  <- 2100L

dat <- dat |>
  mutate(
    Period = dplyr::case_when(
      Year >= HIST_START & Year <= HIST_END ~ "Historical",
      Year >= NEAR_START & Year <= NEAR_END ~ "Near future",
      Year >= FAR_START  & Year <= FAR_END  ~ "Far future",
      TRUE ~ NA_character_
    )
  ) |>
  filter(
    Month %in% c(6L, 7L, 8L, 9L),               # Jun–Sep
    Period %in% c("Near future","Far future"),  
    !is.na(Value),
    Value != -99.9
  )

# =========================
# 4. Tail-based filter (TXN bottom 25%, others top 25%)
# =========================
cold_indices <- c("TXN")

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

# =========================
# 4.5 Compute shared y-axis limits
# =========================
shared_limits <- compute_shared_limits(dat, dat)

# =========================
# 5. Labels and ordering
# =========================
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
  "RX1DAY","RX5DAY","PRCPTOT","R10MM"
)

present_codes <- unique(dat$Index_code)

ordered_codes <- c(
  panel_order[panel_order %in% present_codes],
  setdiff(present_codes, panel_order)
)

wrap_lab <- function(x, width = 28) stringr::str_wrap(x, width = width)

dat <- dat |>
  mutate(
    Index_label_raw = ifelse(Index_code %in% names(label_map),
                             label_map[Index_code], Index_code),
    Index_label = factor(
      wrap_lab(Index_label_raw, width = 28),
      levels = wrap_lab(
        ifelse(ordered_codes %in% names(label_map),
               label_map[ordered_codes], ordered_codes),
        28
      )
    ),
    Period    = factor(Period,
                       levels = c("Near future","Far future")),
    Month_lab = factor(
      Month,
      levels = c(6,7,8,9),
      labels = c("Jun","Jul","Aug","Sep")
    )
  )

# =========================
# 6. Units
# =========================
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
  if (code %in% c("SPEI3","SPEI6","SPI3","SPI6")) return("")  
  u <- unit_map[[code]]
  if (is.null(u)) return("")
  u
}

# =========================
# 7. Colors 
# =========================
pal <- c(
  "Near future" = "#45B39D",
  "Far future"  = "#8C2D3E"   
)

# =========================
# 8. Per-index panel builder + shared y-limits
# =========================
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
      width          = 0.65,
      position       = position_dodge(width = 0.75),
      color          = "black",      
      outlier.shape  = 16,    
      outlier.size   = 1.2,   
      outlier.alpha  = 0.8,   
      outlier.colour = "darkred"  
    ) +
    scale_fill_manual(
      values = pal, name = NULL,
      limits = c("Near future","Far future"),
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
      
      # --- 修改处：子图标题、XY 轴文字全部放大并加粗 ---
      plot.title       = element_text(face = "bold", hjust = 0.5, size = 12),
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

# =========================
# 9. Temperature vs Precipitation panels
# =========================
ncol_temp   <- 3   # 温度组每行几个 panel
ncol_precip <- 3   # 降水+干旱组每行几个 panel

temp_codes   <- intersect(ordered_codes, temp_indices)
precip_codes <- intersect(ordered_codes, precip_indices)

plots_temp   <- lapply(temp_codes,   make_panel)
plots_precip <- lapply(precip_codes, make_panel)

temp_panels_with_legend <- wrap_plots(plots_temp, ncol = ncol_temp) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    # --- 修改处：放大图例文字并加粗，稍微调大色块 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

temp_final_plot <- temp_panels_with_legend + plot_annotation(
  title = paste0(station, " | ", temp_model, " | ", window_label, " temperature indices\n(", period_label, ")"),
  theme = theme(
    # --- 修改处：主标题放大到 16 ---
    plot.title      = element_text(face = "bold", hjust = 0.5, size = 16),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

precip_panels_with_legend <- wrap_plots(plots_precip, ncol = ncol_precip) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    # --- 修改处：放大图例文字并加粗，稍微调大色块 ---
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

precip_final_plot <- precip_panels_with_legend + plot_annotation(
  title = paste0(station, " | ", precip_model, " | ", window_label, " precipitation indices\n(", period_label, ")"),
  theme = theme(
    # --- 修改处：主标题放大到 16 ---
    plot.title      = element_text(face = "bold", hjust = 0.5, size = 16),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

# =========================
# 10. Save
# =========================
out_png_temp   <- file.path(out_dir, paste0(station, "_", temp_model,   "_", window_tag, "_TEMP_",   period_tag, ".png"))
out_pdf_temp   <- file.path(out_dir, paste0(station, "_", temp_model,   "_", window_tag, "_TEMP_",   period_tag, ".pdf"))
out_png_precip <- file.path(out_dir, paste0(station, "_", precip_model, "_", window_tag, "_PRECIP_", period_tag, ".png"))
out_pdf_precip <- file.path(out_dir, paste0(station, "_", precip_model, "_", window_tag, "_PRECIP_", period_tag, ".pdf"))

# 保存 Temperature
ggsave(out_png_temp, temp_final_plot, width = 12, height = 6,  dpi = 600, bg = "white")
ggsave(out_pdf_temp, temp_final_plot, width = 12, height = 6,  bg = "white")

# 保存 Precipitation
ggsave(out_png_precip, precip_final_plot, width = 12, height = 16, dpi = 600, bg = "white")
ggsave(out_pdf_precip, precip_final_plot, width = 12, height = 16, bg = "white")

message("All figures (PNG & PDF) saved to: ", out_dir)

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
combined_plot <- cowplot::plot_grid(grid_all) +
  cowplot::draw_label("(a)", x = 0.005, y = 0.99, hjust = 0, vjust = 1, fontface = "bold", size = 18) +
  cowplot::draw_label("(b)", x = 0.005, y = 0.28, hjust = 0, vjust = 1, fontface = "bold", size = 18)

out_png_combined <- file.path(out_dir, paste0(station, "_", window_tag, "_PRECIP_TEMP_", period_tag, "_COMBINED.png"))
out_pdf_combined <- file.path(out_dir, paste0(station, "_", window_tag, "_PRECIP_TEMP_", period_tag, "_COMBINED.pdf"))

ggsave(out_png_combined, combined_plot, width = 12, height = 20, dpi = 600, bg = "white")
ggsave(out_pdf_combined, combined_plot, width = 12, height = 20, bg = "white")

message("Saved combined figure to: ", out_dir)
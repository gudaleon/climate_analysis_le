# GCM_hp_JFM.R
# Boxplots of the reference models Jan-Mar, Historical vs Present
# (upper quartile of each month's values per period, lower quartile for TXn), from the monthly
# index workbooks: one of the monthly figures (6.13 Figures 2-7 and D1-D12, v7 Figures 3-8 and
# E1-E12; the COMBINED figures, the single temperature and precipitation figures are written too).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,BCC,NorESM,EC}_<Station>.xlsx (as built by
#          monthly_analysis/step11a_monthly_inputs.R)
# Outputs: 3_Code/output/figures_monthly/<Station>_*.png and .pdf
# Run:     cd <package root> && Rscript 3_Code/step12_figures/GCM_hp_JFM.R <Station> <temperature model>
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
# 1. Load Required Packages
############################################################
suppressPackageStartupMessages({
  library(readxl); library(dplyr); library(stringr)
  library(ggplot2); library(forcats)
  library(patchwork); library(cowplot)
})

############################################################
# ★ Configuration —— 每个站只改这里
############################################################
# [v4] station      <- "London"
window_label <- "Jan–Mar"
window_tag   <- "JanMar"
# [v4] temp_model   <- "MIROC"   # 温度模型
# [v4] precip_model <- "BCC"             # 降水模型
# [v4] out_dir      <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results"
# [v4] temp_path    <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/London/MRI_London.xlsx"  # 温度模型数据
# [v4] precip_path  <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/London/BCC_London.xlsx" # 降水模型数据
############################################################

############################################################
# 2. Function: Compute Shared Y-Axis Limits per Index
#    (original function from your senior; here used BCC vs BCC)
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
# 3. Read BCC GCM Data (London, Jan–Mar) and Basic Filtering
############################################################

# Read both models: 温度 -> temp_path, 降水 -> precip_path
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

temp_set <- c("TMM","TXX","TXN","ID")                        # 温度指数取温度模型,其余取降水模型
df <- dplyr::bind_rows(
  dplyr::filter(df_temp,   toupper(trimws(index)) %in% temp_set),
  dplyr::filter(df_precip, !toupper(trimws(index)) %in% temp_set)
)
stopifnot(all(c("year","month","index","bcc") %in% names(df)))

# Indices kept (all)
keep_indices <- c("TXX","TXN","ID","PRCPTOT","R10MM","RX1DAY","RX5DAY","TMM")

# Build main data (all indices, before tail filter)
dat <- df |>
  transmute(
    Year  = as.integer(.data[["year"]]),
    Month = as.integer(.data[["month"]]),
    Index = as.character(.data[["index"]]),
    Value = suppressWarnings(as.numeric(.data[["bcc"]]))
  ) |>
  # period
  mutate(
    Period = dplyr::case_when(
      Year >= 1950L & Year <= 1986L ~ "Historical",
      Year >= 1987L & Year <= 2023L ~ "Present",
      TRUE ~ NA_character_
    )
  ) |>
  # keep only Jan–Mar and valid values
  filter(
    Month %in% c(1L, 2L, 3L),
    Period %in% c("Historical","Present"),
    !is.na(Value),
    Value != -99.9
  ) |>
  # normalize index
  mutate(Index_code = toupper(trimws(Index))) |>
  filter(Index_code %in% keep_indices) |>
  group_by(Index_code, Period, Month) |>
  mutate(
    p25 = quantile(Value, 0.25, na.rm = TRUE),
    p75 = quantile(Value, 0.75, na.rm = TRUE)
  ) |>
  ungroup()

# Save a full copy (no tail filter) for y-axis limits
dat_full <- dat

############################################################
# 4. Tail-Based 25% Filtering (TXN bottom 25%, others top 25%)
############################################################

cold_indices <- c("TXN")

dat <- dat |>
  filter(
    (Index_code %in% cold_indices  & Value <= p25) |
      (!Index_code %in% cold_indices & Value >= p75)
  ) |>
  select(-p25, -p75)

############################################################
# 5. Compute Robust BCC-Only Y-Axis Limits (Per Index)
############################################################

# Here we pass the same BCC dataset as both arguments:
# this reuses your senior's function but only with GCM data.
shared_limits <- compute_shared_limits(dat, dat)

############################################################
# 6. Label Mapping and Month Factors
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

wrap_lab <- function(x, width = 28) stringr::str_wrap(x, width = width)

dat <- dat |>
  mutate(
    Index_label_raw = ifelse(Index_code %in% names(label_map), label_map[Index_code], Index_code),
    Index_label     = wrap_lab(Index_label_raw, width = 28),
    Period          = factor(Period, levels = c("Historical","Present")),
    Month_lab       = factor(Month, levels = c(1,2,3), labels = c("Jan","Feb","Mar"))
  )

############################################################
# 7. Unit Mapping and Y-Axis Title Helper
############################################################

unit_map <- c(
  "R10MM"   = "Days",
  "ID"      = "Days",
  "TXX"     = "°C",
  "TXN"     = "°C",
  "TMM"     = "°C",
  "RX1DAY"  = "mm",
  "RX5DAY"  = "mm",
  "PRCPTOT" = "mm"
)

y_title_for <- function(code) {
  if (code %in% c("SPEI3","SPEI6")) return("")
  u <- unit_map[[code]]
  if (is.null(u)) return("")
  u
}

pal <- c("Historical"="#3B4CC0", "Present"="#CC79A7")

############################################################
# 8. Panel Builder (Boxplot with Robust Y-Limits)
############################################################

make_panel <- function(code, data) {
  this_dat <- dplyr::filter(data, Index_code == code)
  this_lab <- unique(this_dat$Index_label)
  y_lab    <- y_title_for(code)
  
  # y-axis limits from shared_limits
  ylims <- shared_limits[[code]]
  
  # Fallback if limits not found for some reason
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
      # --- 修改处：将边框和中值横线固定为黑色 ---
      color          = "black",      
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
      panel.background = element_rect(fill = "white", color = NA),
      
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

############################################################
# 9. Temperature-Related Indices Panels (TMM, TXX, TXN, ID)
############################################################
temp_indices      <- c("TMM","TXX","TXN","ID")
panel_order_temp  <- c("TMM","TXX","TXN","ID")

dat_temp <- dat |>
  filter(Index_code %in% temp_indices) |>
  mutate(
    Index_label = factor(
      Index_label,
      levels = wrap_lab(ifelse(panel_order_temp %in% names(label_map),
                               label_map[panel_order_temp], panel_order_temp), 28)
    )
  )

present_codes_temp <- unique(dat_temp$Index_code)
ordered_codes_temp <- c(
  panel_order_temp[panel_order_temp %in% present_codes_temp],
  setdiff(present_codes_temp, panel_order_temp)
)

plots_temp <- lapply(ordered_codes_temp, make_panel, data = dat_temp)

panels_with_legend_temp <- wrap_plots(plots_temp, ncol = 2) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

final_plot_temp <- panels_with_legend_temp + plot_annotation(
  title = paste0(station, " | ", temp_model, " | ", window_label,
                 " Temperature-related indices\n(Historical vs Present)"),
  theme = theme(
    plot.title      = element_text(face = "bold", hjust = 0.5, size = 16),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

out_png_temp <- file.path(out_dir, paste0(station, "_panel_", temp_model, "_", window_tag, "_Temp_Hist_vs_Present.png"))
out_pdf_temp <- file.path(out_dir, paste0(station, "_panel_", temp_model, "_", window_tag, "_Temp_Hist_vs_Present.pdf"))

ggsave(out_png_temp, final_plot_temp, width = 8, height = 12, dpi = 600, bg = "white")
ggsave(out_pdf_temp, final_plot_temp, width = 8, height = 12, bg = "white")
message("Saved Temp (PNG & PDF): ", out_dir)

############################################################
# 10. Precipitation-Related Indices Panels
#     (RX1DAY, RX5DAY, PRCPTOT, R10MM, CDD)
############################################################
precip_indices      <- c("PRCPTOT","R10MM","RX1DAY","RX5DAY")
panel_order_precip  <- c("RX1DAY","RX5DAY","PRCPTOT","R10MM")

dat_precip <- dat |>
  filter(Index_code %in% precip_indices) |>
  mutate(
    Index_label = factor(
      Index_label,
      levels = wrap_lab(ifelse(panel_order_precip %in% names(label_map),
                               label_map[panel_order_precip], panel_order_precip), 28)
    )
  )

present_codes_precip <- unique(dat_precip$Index_code)
ordered_codes_precip <- c(
  panel_order_precip[panel_order_precip %in% present_codes_precip],
  setdiff(present_codes_precip, panel_order_precip)
)

plots_precip <- lapply(ordered_codes_precip, make_panel, data = dat_precip)

panels_with_legend_precip <- wrap_plots(plots_precip, ncol = 2) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

final_plot_precip <- panels_with_legend_precip + plot_annotation(
  title = paste0(station, " | ", precip_model, " | ", window_label,
                 " Precipitation-related indices\n(Historical vs Present)"),
  theme = theme(
    plot.title      = element_text(face = "bold", hjust = 0.5, size = 16),
    plot.background = element_rect(fill = "white", color = NA)
  )
)

out_png_precip <- file.path(out_dir, paste0(station, "_panel_", precip_model, "_", window_tag, "_Precip_Hist_vs_Present.png"))
out_pdf_precip <- file.path(out_dir, paste0(station, "_panel_", precip_model, "_", window_tag, "_Precip_Hist_vs_Present.pdf"))

ggsave(out_png_precip, final_plot_precip, width = 8, height = 12, dpi = 600, bg = "white")
ggsave(out_pdf_precip, final_plot_precip, width = 8, height = 12, bg = "white")
message("Saved Precip (PNG & PDF): ", out_dir)

# =========================
# 11. Combined: (a) Precipitation | (b) Temperature(统一网格,panel 等大)
# =========================
library(cowplot)

# 2 行 × 4 列:左两列降水,右两列温度
plots_all <- list(
  plots_precip[[1]], plots_precip[[2]], plots_temp[[1]], plots_temp[[2]],  # 第一行
  plots_precip[[3]], plots_precip[[4]], plots_temp[[3]], plots_temp[[4]]   # 第二行
)

grid_all <- wrap_plots(plots_all, ncol = 4) +
  plot_layout(guides = "collect") &
  theme(
    legend.position  = "bottom",
    legend.text      = element_text(size = 12, face = "bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

# (a)(b) 画在顶部:(a) 左端,(b) 右半边起点
combined_plot <- plot_grid(grid_all) +
  draw_label("(a)", x = 0.01, y = 0.99, hjust = 0, vjust = 1, fontface = "bold", size = 18) +
  draw_label("(b)", x = 0.51, y = 0.99, hjust = 0, vjust = 1, fontface = "bold", size = 18)

out_png_combined <- file.path(out_dir, paste0(station, "_GCM_", window_tag, "_PRECIP_TEMP_Hist_vs_Present_COMBINED.png"))
out_pdf_combined <- file.path(out_dir, paste0(station, "_GCM_", window_tag, "_PRECIP_TEMP_Hist_vs_Present_COMBINED.pdf"))

ggsave(out_png_combined, combined_plot, width = 16, height = 12, dpi = 600, bg = "white")
ggsave(out_pdf_combined, combined_plot, width = 16, height = 12, bg = "white")

message("Saved combined figure to: ", out_dir)
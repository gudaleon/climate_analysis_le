# GCM_nf_JFM.R
# Boxplots of the reference models Jan-Mar, Near vs Far future
# (upper quartile of each month's values per period, lower quartile for TXn), from the monthly
# index workbooks: one of the monthly figures (6.13 Figures 2-7 and D1-D12, v7 Figures 3-8 and
# E1-E12; the COMBINED figures, the single temperature and precipitation figures are written too).
# Inputs:  2_Data/4_Monthly_analysis/{OBS,BCC,NorESM,EC}_<Station>.xlsx (as built by
#          monthly_analysis/step11a_monthly_inputs.R)
# Outputs: 3_Code/output/figures_monthly/<Station>_*.png and .pdf
# Run:     cd <package root> && Rscript 3_Code/step12_figures/GCM_nf_JFM.R <Station> <temperature model>
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
  library(patchwork)
})

# =========================
# ★ Configuration —— 每个站只改这里
# =========================
# [v4] station      <- "London"
window_label <- "Jan–Mar"
window_tag   <- "JanMar"
period_label <- "Near future vs Far future"
# [v4] temp_model   <- "MRI"   # 温度模型
# [v4] precip_model <- "BCC"     # 降水模型
# [v4] out_dir      <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results"
# [v4] temp_path    <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/London/MRI_London.xlsx"  # 温度模型数据
# [v4] precip_path  <- "G:/Research3/Verified_stations/Model_Performance&Trend_Analysis_results/London/BCC_London.xlsx" # 降水模型数据

# =========================
# 0. Shared Y-axis limits 
# =========================
compute_shared_limits <- function(dat_A, dat_B) {
  all_indices <- sort(unique(c(dat_A$Index_code, dat_B$Index_code)))
  limits_list <- vector("list", length(all_indices))
  names(limits_list) <- all_indices
  
  for (idx in all_indices) {
    vals <- c(dat_A$Value[dat_A$Index_code == idx],
              dat_B$Value[dat_B$Index_code == idx])
    vals <- vals[is.finite(vals)]
    
    if (length(vals) >= 2) {
      q1 <- quantile(vals, 0.25, na.rm=TRUE)
      q3 <- quantile(vals, 0.75, na.rm=TRUE)
      iqr <- q3 - q1
      lo <- max(min(vals), q1 - 1.5*iqr, quantile(vals, 0.01))
      hi <- min(max(vals), q3 + 1.5*iqr, quantile(vals, 0.99))
      if (!is.finite(lo)||!is.finite(hi)||lo>=hi) {lo=min(vals);hi=max(vals)}
      pad <- (hi-lo)*0.05
      limits_list[[idx]] <- c(lo-pad, hi+pad)
    } else {
      limits_list[[idx]] <- c(0,1)
    }
  }
  limits_list
}

# =========================
# 1. Read Data  (温度模型 + 降水模型)
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

temp_set <- c("TMM","TXX","TXN","ID")                        # 温度指数取温度模型,其余取降水模型
df <- dplyr::bind_rows(
  dplyr::filter(df_temp,   toupper(trimws(index)) %in% temp_set),
  dplyr::filter(df_precip, !toupper(trimws(index)) %in% temp_set)
)
stopifnot(all(c("year","month","index","bcc") %in% names(df)))

dat <- df |>
  transmute(
    Year  = as.integer(year),
    Month = as.integer(month),
    Index = toupper(index),
    Value = suppressWarnings(as.numeric(bcc))
  )

# =========================
# 2. Period + Month Filter (Jan–Mar + Near & Far)
# =========================
HIST_START <- 1950; HIST_END <- 1986
NEAR_START <- 2024; NEAR_END <- 2062
FAR_START  <- 2063; FAR_END  <- 2100

dat <- dat |>
  mutate(
    Period = case_when(
      Year>=HIST_START & Year<=HIST_END ~ "Historical",
      Year>=NEAR_START & Year<=NEAR_END ~ "Near future",
      Year>=FAR_START  & Year<=FAR_END  ~ "Far future",
      TRUE ~ NA_character_
    )
  ) |>
  filter(
    Month %in% 1:3,
    Period %in% c("Near future","Far future"),
    !is.na(Value), Value!=-99.9
  )

dat <- dat |>
  mutate(
    Period = factor(Period, levels = c("Near future", "Far future"))
  )


# =========================
# 3. Indices
# =========================
temp_indices   <- c("TMM","TXX","TXN","ID")
precip_indices <- c("RX1DAY","RX5DAY","PRCPTOT","R10MM")
keep_indices   <- c(temp_indices,precip_indices)

# =========================
# 4. Tail-based 25%
# =========================
cold_indices <- c("TXN")

dat <- dat |>
  mutate(Index_code = toupper(Index)) |>
  filter(Index_code %in% keep_indices) |>
  group_by(Index_code, Period, Month) |>
  mutate(
    p25 = quantile(Value,0.25,na.rm=TRUE),
    p75 = quantile(Value,0.75,na.rm=TRUE)
  ) |>
  ungroup() |>
  filter(
    (Index_code %in% cold_indices & Value <= p25) |
      (!Index_code %in% cold_indices & Value >= p75)
  ) |>
  select(-p25,-p75)

# =========================
# 4.5 Shared Y-axis 
# =========================
shared_limits <- compute_shared_limits(dat, dat)

# =========================
# 5. Label + Units 
# =========================
label_map <- c(
  "TMM"="TMM (Mean Temperature)",
  "TXX"="TXx (Hottest Day)",
  "TXN"="TXn (Coldest Day)",
  "ID" ="ID (Ice Days)",
  "RX1DAY" ="RX1DAY (Wettest Day)",
  "RX5DAY" ="RX5DAY (Max 5-day precip)",
  "PRCPTOT"="PRCPTOT (Total Precipitation)",
  "R10MM" ="R10MM (Heavy Rain Days)"
)

unit_map <- c(
  "TMM"="°C","TXX"="°C","TXN"="°C","ID"="Days",
  "RX1DAY"="mm","RX5DAY"="mm","PRCPTOT"="mm",
  "R10MM"="Days","CDD"="Days"
)

wrap_lab <- function(x,width=28) stringr::str_wrap(x,width)
y_title <- function(code) unit_map[[code]]

# =========================
# 6. Color scheme
# =========================
pal <- c("Near future"="#45B39D","Far future"="#8C2D3E")

# =========================
# 7. Plot function (修正：保留红色离群点，找回中位数线)
# =========================
make_panel <- function(code){
  d <- dplyr::filter(dat, Index_code==code)
  y_lab <- y_title(code) # 提取单位标签，用于下方判断
  
  ggplot(d, aes(x=factor(Month, labels=c("Jan","Feb","Mar")), y=Value, fill=Period)) +
    geom_boxplot(
      width         = 0.65,
      position      = position_dodge(0.75),
      color         = "black",      
      # --- 修改处：离群点变深红、放大、提高不透明度 ---
      outlier.shape  = 16,    
      outlier.size   = 1.2,   
      outlier.alpha  = 0.8,   
      outlier.colour = "darkred" 
    ) +
    scale_fill_manual(
      values = pal,
      name   = NULL,
      limits = c("Near future", "Far future"),
      drop   = FALSE
    ) +
    # 增加 5% expand 确保红点不被切掉
    scale_y_continuous(limits=shared_limits[[code]], expand=expansion(mult = 0.05)) +
    labs(title=wrap_lab(label_map[code]), y=y_lab, x=NULL) +
    theme_bw() +
    theme(
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      panel.background = element_rect(fill="white", color=NA),
      
      # --- 修改处：小标题和XY轴全部放大并加粗 ---
      plot.title       = element_text(face="bold", hjust=0.5, size=12),
      axis.text.x      = element_text(vjust=0.5, size=12, face="bold"),
      axis.text.y      = element_text(size=12, face="bold"),
      axis.title.x     = element_text(size=14, face="bold"),
      axis.title.y     = if (!is.null(y_lab) && nzchar(y_lab)) {
        element_text(size=14, face="bold", margin=margin(r=4))
      } else {
        element_blank()
      }
    )
}

# =========================
# 8. Temperature vs Precip plots & Saving
# =========================
ncol_temp   <- 2  
ncol_precip <- 2  

# --- Temperature
temp_panels <- lapply(temp_indices, make_panel)
temp_final  <- wrap_plots(temp_panels, ncol=ncol_temp) +
  plot_layout(guides="collect") &                     
  theme(
    legend.position  = "bottom",
    legend.text      = element_text(size=12, face="bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill="white", color=NA),
    panel.background = element_rect(fill="white", color=NA)
  )

temp_final <- temp_final + plot_annotation(
  title = paste0(station, " | ", temp_model, " | ", window_label,
                 " temperature indices\n(", period_label, ")"),
  theme=theme(
    plot.title      = element_text(face="bold", hjust=0.5, size=16),
    plot.background = element_rect(fill="white", color=NA)
  )
)

ggsave(file.path(out_dir, paste0(station, "_", temp_model, "_", window_tag, "_TEMP.png")), temp_final, width=8, height=12, dpi=600, bg="white")
ggsave(file.path(out_dir, paste0(station, "_", temp_model, "_", window_tag, "_TEMP.pdf")), temp_final, width=8, height=12, bg="white")


# --- Precipitation
precip_panels <- lapply(precip_indices, make_panel)
precip_final  <- wrap_plots(precip_panels, ncol=ncol_precip) +
  plot_layout(guides="collect") &                     
  theme(
    legend.position  = "bottom",
    legend.text      = element_text(size=12, face="bold"),
    legend.key.size  = unit(1.5, "lines"),
    plot.background  = element_rect(fill="white", color=NA),
    panel.background = element_rect(fill="white", color=NA)
  )

precip_final <- precip_final + plot_annotation(
  title = paste0(station, " | ", precip_model, " | ", window_label,
                 " precipitation indices\n(", period_label, ")"),
  theme=theme(
    plot.title      = element_text(face="bold", hjust=0.5, size=16),
    plot.background = element_rect(fill="white", color=NA)
  )
)

ggsave(file.path(out_dir, paste0(station, "_", precip_model, "_", window_tag, "_PRECIP.png")), precip_final, width=8, height=12, dpi=600, bg="white")
ggsave(file.path(out_dir, paste0(station, "_", precip_model, "_", window_tag, "_PRECIP.pdf")), precip_final, width=8, height=12, bg="white")

message("Done! Saved PNG and PDF files to: ", out_dir)

# =========================
# 9. Combined: (a) Precipitation | (b) Temperature(统一网格,panel 等大)
# =========================
library(cowplot)   # 这份脚本顶部没加载,这里补上

# 2 行 × 4 列:左两列降水 (a),右两列温度 (b)
plots_all <- list(
  precip_panels[[1]], precip_panels[[2]], temp_panels[[1]], temp_panels[[2]],  # 第一行
  precip_panels[[3]], precip_panels[[4]], temp_panels[[3]], temp_panels[[4]]   # 第二行
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

out_png_combined <- file.path(out_dir, paste0(station, "_", window_tag, "_PRECIP_TEMP_Near_vs_Far_COMBINED.png"))
out_pdf_combined <- file.path(out_dir, paste0(station, "_", window_tag, "_PRECIP_TEMP_Near_vs_Far_COMBINED.pdf"))

ggsave(out_png_combined, combined_plot, width = 16, height = 12, dpi = 600, bg = "white")
ggsave(out_pdf_combined, combined_plot, width = 16, height = 12, bg = "white")

message("Saved combined figure to: ", out_dir)
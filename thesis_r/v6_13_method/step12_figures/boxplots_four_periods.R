# boxplots_four_periods.R
# Appendix boxplots of the annual indices in the four periods (v7 Appendix F, 36 figures F1-F36).
# Each figure shows three indices (rows) of one station; the columns compare Historical with
# Present (Observed and the ten models), Near Future and Far Future (models only). The last box
# pair in every panel is the Ensemble: the ten models pooled into one distribution per period.
# Boxes: quartiles (type 7), whiskers to the furthest value within 1.5 IQR, red points beyond.
# Keeps its layout: 32 x 22 in at 300 dpi, the
# axes placed at the same positions, matplotlib's y tick algorithm (MaxNLocator, 9 bins) and its
# 5 % data margins.
# Inputs:  2_Data/3_Annual_index_tables/All_<Station>_observed_and_10_models_1950-2100.xlsx
# Outputs: 3_Code/output/figures_boxplots/F1.png ... F36.png
# Run:     cd <package root> && Rscript 3_Code/step12_figures/boxplots_four_periods.R [figure numbers]
#          (no numbers = all 36)

source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
suppressPackageStartupMessages({ library(ggplot2); library(grid) })

OUT <- out_dir("figures_boxplots")
# unit labels and the minus sign are non-ASCII: draw them in a UTF-8 locale (Rscript in a C/POSIX
# locale would print them as dots)
if (!isTRUE(l10n_info()[["UTF-8"]])) invisible(Sys.setlocale("LC_CTYPE", "C.UTF-8"))

# model labels as printed in the figures
ML <- c("ACCESS-ESM1-5", "BCC-CSM2-MR", "CanESM5", "CNRM-ESM2", "EC-Earth3-veg", "GFDL-ESM4", "INM-CM5",
        "MIROC-ES2L", "MRI-ESM2", "NorESM2-LM")
COL <- c(Hist = "#4E79A7", Pres = "#F28E2B", Near = "#59A14F", Far = "#8C564B")
LAB <- c(Hist = "Historical", Pres = "Present", Near = "Near Future", Far = "Far Future")
U <- c(PRCPTOT = "mm", R10mm = "Days", R20mm = "Days", RX1day = "mm", RX3day = "mm", RX5day = "mm",
       SDII = "mm/day", R95p = "mm", R95pTOT = "%", R99p = "mm", R99pTOT = "%", CDD = "Days",
       DTRgt15 = "Days", TNltm20 = "Days", CWA = "\u00b0C\u00b2", CWF = "Days", HWA = "\u00b0C\u00b2", HWF = "Days",
       FD = "Days", ID = "Days", GDDgrow10 = "\u00b0C\u00b7days", GSL = "Days", SU = "Days", TR = "Days",
       TXge30 = "Days", TXgt50p = "%", TNn = "\u00b0C", TNx = "\u00b0C", TXn = "\u00b0C", TXx = "\u00b0C", TN10p = "%",
       TN90p = "%", TX10p = "%", TX90p = "%", WSDI3 = "Days", CSDI3 = "Days")
G <- list(p1 = c("PRCPTOT", "R10mm", "R20mm"), p2 = c("RX1day", "RX3day", "RX5day"), p3 = c("SDII", "R95p", "R95pTOT"),
          p4 = c("R99p", "R99pTOT", "CDD"), t1 = c("DTRgt15", "TNltm20", "CWA"), t2 = c("CWF", "HWA", "HWF"),
          t3 = c("FD", "ID", "GDDgrow10"), t4 = c("GSL", "SU", "TR"), t5 = c("TXge30", "TXgt50p", "TNn"),
          t6 = c("TNx", "TXn", "TXx"), t7 = c("TN10p", "TN90p", "TX10p"), t8 = c("TX90p", "WSDI3", "CSDI3"))
# figure number -> station and index group (the order of the appendix)
FIGS <- rbind(
  data.frame(n = 1:12,  st = "London", g = c("p1", "p2", "p3", "p4", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8")),
  data.frame(n = 13:24, st = "Fergus", g = c("p4", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "p1", "p2", "p3")),
  data.frame(n = 25:36, st = "Harrow", g = c("t7", "t8", "p1", "p2", "p3", "p4", "t1", "t2", "t3", "t4", "t5", "t6")))

# ---- matplotlib look ------------------------------------------------------------------------
PT <- 1                               # text sizes in points as in matplotlib
lw <- function(pt) pt / (.pt * 72 / 96)  # line width in points -> ggplot linewidth
MINUS <- "\u2212"
W_IN <- 32; H_IN <- 22; DPI <- 300
AX_L <- 0.05; AX_R <- 0.99; AX_T <- 0.99; AX_B <- 0.17; HSP <- 0.04; WSP <- 0.12
AX_W <- (AX_R - AX_L) * W_IN / (3 + 2 * WSP)        # axes width and height in inches
AX_H <- (AX_T - AX_B) * H_IN / (3 + 2 * HSP)
NBINS <- 9                            # MaxNLocator('auto') for this axes height and font size

# matplotlib MaxNLocator(steps = c(1, 2, 2.5, 5, 10), min_n_ticks = 2) tick positions
mpl_ticks <- function(vmin, vmax, nbins = NBINS) {
  dv <- abs(vmax - vmin); meanv <- (vmax + vmin) / 2
  offset <- if (abs(meanv) / dv < 100) 0 else sign(meanv) * 10^floor(log10(abs(meanv)))
  scale <- 10^floor(log10(dv / nbins))
  steps <- c(0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20) * scale
  v0 <- vmin - offset; v1 <- vmax - offset
  raw <- (v1 - v0) / nbins
  istep <- which(steps >= raw)[1]
  tol <- if (offset > 0) min(0.4999, max(1e-10, 10^(log10(offset / steps[istep]) - 12))) else 1e-10
  for (step in rev(steps[1:istep])) {
    best <- floor(v0 / step) * step
    x <- v0 - best; d <- floor(x / step); m <- x - d * step
    low <- if (abs(m / step - 1) < tol) d + 1 else d
    x <- v1 - best; d <- floor(x / step); m <- x - d * step
    high <- if (abs(m / step) < tol) d else d + 1
    ticks <- (low:high) * step + best
    if (sum(ticks <= v1 & ticks >= v0) >= 2) break
  }
  ticks + offset
}
# ScalarFormatter-like labels: the fewest decimals that keep every tick exact, unicode minus
mpl_labels <- function(x) {
  d <- 0
  while (d < 8 && any(abs(round(x, d) - x) > 1e-8 * pmax(1, abs(x)))) d <- d + 1
  s <- sprintf(paste0("%.", d, "f"), x)
  s <- sub("^-", MINUS, s); s[s == paste0(MINUS, sprintf(paste0("%.", d, "f"), 0))] <- sprintf(paste0("%.", d, "f"), 0)
  s
}
# matplotlib default view limits: data range with 5 % margins (singular ranges widened first)
mpl_limits <- function(v) {
  if (length(v) == 0) return(c(0, 1))
  lo <- min(v); hi <- max(v)
  if (hi - lo < 1e-12 * max(1, abs(hi))) { e <- if (lo == 0) 0.05 else 0.05 * abs(lo); lo <- lo - e; hi <- hi + e }
  d <- (hi - lo) * 0.05; c(lo - d, hi + d)
}

# box statistics as matplotlib boxplot (whis = 1.5)
box_stats <- function(v, pos, per) {
  q <- quantile(v, c(0.25, 0.5, 0.75), type = 7, names = FALSE); iqr <- q[3] - q[1]
  hi <- max(v[v <= q[3] + 1.5 * iqr]); lo <- min(v[v >= q[1] - 1.5 * iqr])
  list(box = data.frame(pos = pos, per = per, q1 = q[1], med = q[2], q3 = q[3], lo = lo, hi = hi),
       out = data.frame(pos = rep(pos, sum(v < lo | v > hi)), v = v[v < lo | v > hi]))
}

panel_plot <- function(g, k, p2, obs, row, col) {
  cols <- c(if (obs) "Observed", MODELS, "Ensemble")
  boxes <- list(); outs <- list(); allv <- numeric()
  for (i in seq_along(cols)) for (j in 1:2) {
    p <- c("Hist", p2)[j]
    v <- if (cols[i] == "Ensemble") unlist(lapply(MODELS, function(m) per(g, m, p))) else per(g, cols[i], p)
    if (length(v) == 0) next
    s <- box_stats(v, (i - 1) + if (j == 1) -0.17 else 0.17, p)
    boxes[[length(boxes) + 1]] <- s$box; outs[[length(outs) + 1]] <- s$out; allv <- c(allv, v)
  }
  B <- do.call(rbind, boxes); O <- do.call(rbind, outs)
  lim <- mpl_limits(allv); br <- mpl_ticks(lim[1], lim[2]); br <- br[br >= lim[1] - 1e-12 & br <= lim[2] + 1e-12]
  per_levels <- c("Hist", p2)
  pl <- ggplot()
  if (!is.null(B)) {
    B$per <- factor(B$per, levels = per_levels)
    pl <- pl +
      geom_segment(data = B, aes(x = pos, xend = pos, y = q3, yend = hi), colour = "#333333", linewidth = lw(1)) +
      geom_segment(data = B, aes(x = pos, xend = pos, y = q1, yend = lo), colour = "#333333", linewidth = lw(1)) +
      geom_rect(data = B, aes(xmin = pos - 0.16, xmax = pos + 0.16, ymin = q1, ymax = q3, fill = per),
                colour = "#333333", linewidth = lw(1)) +
      geom_segment(data = B, aes(x = pos - 0.16, xend = pos + 0.16, y = med, yend = med), colour = "#222222",
                   linewidth = lw(2.2), lineend = "square")
  }
  if (!is.null(O) && nrow(O)) pl <- pl + geom_point(data = O, aes(x = pos, y = v), colour = "red", shape = 16, size = 1.75)
  pl +
    scale_fill_manual(values = COL[per_levels], labels = LAB[per_levels], limits = per_levels, drop = FALSE, name = NULL) +
    scale_x_continuous(limits = c(-0.6, length(cols) - 0.4), breaks = seq_along(cols) - 1,
                       labels = NULL, expand = c(0, 0)) +
    scale_y_continuous(limits = lim, breaks = br, labels = mpl_labels(br), expand = c(0, 0)) +
    labs(x = NULL, y = if (col == 1) paste0(k, "\n", U[[k]]) else NULL) +
    theme_void() +
    theme(
      panel.border = element_rect(colour = "black", fill = NA, linewidth = lw(0.8)),
      panel.background = element_rect(fill = "white", colour = NA),
      axis.ticks = element_line(colour = "black", linewidth = lw(0.8)),
      axis.ticks.length = unit(3.5, "pt"),
      axis.text.y = element_text(family = "DejaVu Sans Mono", size = 15 * PT, colour = "black", hjust = 1,
                                 margin = margin(r = 3.5, unit = "pt")),
      axis.text.x = element_blank(),     # bottom-row labels are drawn by draw_xlabels()
      axis.title.y = element_text(family = "DejaVu Sans", face = "bold", size = 18 * PT, angle = 90, lineheight = 1.0,
                                  margin = margin(r = 18, unit = "pt")),
      legend.position = if (row == 3) "bottom" else "none",
      legend.text = element_text(family = "DejaVu Sans", face = "bold", size = 20 * PT, margin = margin(l = 16, r = 24, unit = "pt")),
      legend.key.width = unit(1.6 * 20, "pt"), legend.key.height = unit(21, "pt"),
      plot.margin = margin(0, 0, 0, 0))
}

# draw a ggplot so that its panel fills exactly the given rectangle (inches from bottom left)
place_panel <- function(pl, x0, y0) {
  gt <- ggplotGrob(pl)
  legend <- NULL
  gi <- which(gt$layout$name == "guide-box-bottom" | gt$layout$name == "guide-box")
  if (length(gi)) {
    lg <- gt$grobs[[gi[1]]]
    if (!inherits(lg, "zeroGrob")) legend <- lg
  }
  # drop the legend from the plot table; it is placed separately as in matplotlib
  if (length(gi)) gt$grobs[gi] <- list(zeroGrob())
  pi <- which(gt$layout$name == "panel")
  L <- gt$layout[pi, ]
  wd <- function(i) if (length(i)) sum(convertWidth(gt$widths[i], "in", valueOnly = TRUE)) else 0
  ht <- function(i) if (length(i)) sum(convertHeight(gt$heights[i], "in", valueOnly = TRUE)) else 0
  nc <- length(gt$widths); nr <- length(gt$heights)
  gt$widths[L$l] <- unit(AX_W, "in"); gt$heights[L$t] <- unit(AX_H, "in")
  left <- wd(seq_len(L$l - 1)); right <- wd(if (L$r < nc) (L$r + 1):nc else integer())
  top <- ht(seq_len(L$t - 1)); bottom <- ht(if (L$b < nr) (L$b + 1):nr else integer())
  pushViewport(viewport(x = unit(x0 - left, "in"), y = unit(y0 - bottom, "in"), just = c("left", "bottom"),
                        width = unit(left + AX_W + right, "in"), height = unit(bottom + AX_H + top, "in")))
  grid.draw(gt); popViewport()
  legend
}

# x tick labels of the bottom row, rotated 45 degrees with the top right corner of each label's
# bounding box 7 pt (tick length + pad) below the tick, as matplotlib's rotation = 45, ha = "right"
draw_xlabels <- function(labs, x0, y0) {
  gp <- gpar(fontfamily = "DejaVu Sans", fontface = "bold", fontsize = 17 * PT)
  h <- convertHeight(grobHeight(textGrob("Ag", gp = gp)), "in", valueOnly = TRUE)
  n <- length(labs)
  for (i in seq_len(n)) {
    x <- x0 + ((i - 1) + 0.6) / (n + 0.2) * AX_W - 3 / 72   # 3 pt: text bounding box padding in matplotlib
    grid.text(labs[i], x = unit(x, "in"), y = unit(y0 - 7 / 72 - sin(pi / 4) * h, "in"), rot = 45,
              hjust = 1, vjust = 0, gp = gp)
  }
}

make_figure <- function(n, st, ks, X) {
  png(file.path(OUT, sprintf("F%d.png", n)), width = W_IN, height = H_IN, units = "in", res = DPI, bg = "white")
  grid.newpage()
  setup <- list(c("Pres", TRUE), c("Near", FALSE), c("Far", FALSE))
  for (r in 1:3) {
    g <- X[X$Index == ks[r], ]
    for (c in 1:3) {
      x0 <- (AX_L * W_IN) + (c - 1) * AX_W * (1 + WSP)
      y0 <- (AX_B * H_IN) + (3 - r) * AX_H * (1 + HSP)
      obs <- as.logical(setup[[c]][2])
      lg <- place_panel(panel_plot(g, ks[r], setup[[c]][1], obs, r, c), x0, y0)
      if (r == 3) draw_xlabels(c(if (obs) "Observed", ML, "Ensemble"), x0, y0)
      # legend: upper centre at (0.5, -0.42) in axes coordinates; the offsets stand for matplotlib's
      # legend border padding and for the space after the last label (24 pt) in the ggplot legend
      if (!is.null(lg)) {
        pushViewport(viewport(x = unit(x0 + AX_W / 2 + 12 / 72, "in"), y = unit(y0 - 0.42 * AX_H - 0.24, "in"), just = c("centre", "top"),
                              width = grobWidth(lg), height = grobHeight(lg)))
        grid.draw(lg); popViewport()
      }
    }
  }
  invisible(dev.off())
}

which_figs <- suppressWarnings(as.integer(commandArgs(TRUE)))
which_figs <- which_figs[!is.na(which_figs)]
cache <- list()
for (i in seq_len(nrow(FIGS))) {
  n <- FIGS$n[i]; st <- FIGS$st[i]
  if (length(which_figs) && !(n %in% which_figs)) next
  if (is.null(cache[[st]])) cache[[st]] <- load_annual(st)
  make_figure(n, st, G[[FIGS$g[i]]], cache[[st]])
  cat(n, "")
}
cat("\n")

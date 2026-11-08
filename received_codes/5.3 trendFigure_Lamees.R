# Libraries
library(data.table)
library(scales)
library(ggplot2)
library(stringr)

# Working directory
#setwd("~lamees/OneDrive - University of Toronto/Extreme Events/r")

# Load model output data
codasMay <- readRDS(file="output/coda_summary/May2021/codasMay.rds")
# Check analysis.R
maxLag <- readRDS("output/rdata/lagData2.rds")

# Create variable vectors/lists.
lmons <- c("D","J","F","M","A","M","J","J","A","S","O","N")

lst <- c("TRENTON A", "TORONTO LESTER B. PEARSON INT'L A","OTTAWA MACDONALD-CARTIER INT'L A","WINDSOR A","KENORA A","LONDON INT'L AIRPORT","WIARTON A","NORTH BAY A","KAPUSKASING A","SIOUX LOOKOUT A")
lstn <- c("TRENTON", "TORONTO","OTTAWA","WINDSOR","KENORA","LONDON","WIARTON","NORTH BAY","KAPUSKASING","SIOUX LOOKOUT")

# Subset beta parameters.
betas <- c("beta_m1[2]","beta_m1[3]","beta_m1[4]","beta_m1[5]","beta_m1[6]")
bname <- c("Time x20","PDO", "AO", "NAO", "MEI")
# Rename the variables.
betaDT <- codasMay[name %in% betas]
betaDT[, index := factor(name, labels = bname, levels = betas)]
# Another method.
DT <- codasMay[name %in% betas][
  ,index:=ifelse(name=="beta_m1[6]","MEI",
                  ifelse(name=="beta_m1[5]","NAO",
                         ifelse(name=="beta_m1[4]","AO",
                                ifelse(name=="beta_m1[2]","Time x20",
                                       ifelse(name=="beta_m1[3]","PDO",NA)))))][]
# Check if equal
all(betaDT==DT) # Yes.

# Temporal trend for every 20 years.
betaDT[index == "Time x20", median20 := median*20]

# Merge with lag data.
ggData <- maxLag[,.(month, station = station_name, variable = ws_variable,
                    index = Variable, max_lag)][
                      betaDT, on = c("station", "month", "variable", "index")] 
ggData[is.na(max_lag), max_lag := 0]

# Create column for angle.
ggData[, angle := max_lag * 45 + 90]

# Create column with shorter station names.
ggData[, stn := factor(station, levels = lst, labels = lstn)]

# Bubble figure function.
plot_func <- function(gdata, var, labn, grp) {
  g <- ggplot() +
    scale_size(expression(P*(italic(beta) > 0)), 
               breaks = (abs(c(0,0.1,0.5,0.9,1)-0.5)*2)^8, 
               labels = c(0,0.1,0.5,0.9,1))+
    scale_x_discrete(labels = lmons)+
    scale_colour_manual("Trend", values = c(`<0` = "red", `>0` = "darkgreen")) +
    scale_fill_gradient2(low = "red", mid = "yellow", high = "dark green", midpoint = 0) +
    theme_minimal() +
    labs(fill = "Median") +
    facet_grid(index ~ var_lab) +
 geom_point(data = gdata[variable %in% var],
               aes(x = factor(month, levels = c(12, 1:11)),
                   y = reorder(stn, !!rlang::sym(grp)),
                   size = (abs(p-0.5)*2)^8, fill = median20,
                   colour = ifelse(median20 < 0, "<0", ">0")),
               alpha = 0.7, shape = 21) + 
    ggnewscale::new_scale_colour() +
    geom_text(data = gdata[variable%in%var][(round(abs(p),1)==0)|(round(abs(p),1))==1][!index%in%'Time x20'],
              aes(x = factor(month),
                  y = reorder(stn,!!rlang::sym(grp)),
                  angle = angle,
                  colour = factor(max_lag)),
              label = "\U2192",
              hjust = 0.5,
              vjust = 0.38,
              alpha = 0.7) +
    scale_colour_manual(values = rep("black", length(unique(gdata$max_lag)))) +
    coord_fixed() +
    theme(text = element_text(family = "Times New Roman", size = 16))+
    labs(colour = "Lag", x = "Month", y = labn)
  return(g)
}


leg_func <- function(gt) {
  # https://stackoverflow.com/questions/64295406/is-there-a-way-to-include-different-angles-of-a-symbol-in-the-legend-in-r
  # Get indices for guide box and legend keys
  idx_guide_box <- which(gt$layout$name == "guide-box")
  idx_keys <- which(grepl("text",gt$grobs[[idx_guide_box]]$grobs[[2]]$grob)&
                      str_detect(gt$grobs[[idx_guide_box]]$grobs[[2]]$layout$name, "^key[\\-\\d]+$"))
  for (i in seq_along(idx_keys)) {
    angle <- (i - 1) * 45 + 90
    idx_grob <- idx_keys[[i]]
    # Set angle and label
    gt$grobs[[idx_guide_box]]$grobs[[2]]$grobs[[idx_grob]]$rot <- angle
    gt$grobs[[idx_guide_box]]$grobs[[2]]$grobs[[idx_grob]]$label <- "\U2192"
    }
  return(gt)
}

# Plot using latitude.
g <- plot_func(gdata = ggData, var = c("max_daily_precip","max_temp","min_temp","max_dew","min_dew"),
               labn = "Station\nSouth <———————> North\n", grp = "lat")
p <- plot_func(ggData, c("maxHumIncD95","minHumIncD5","maxWindIncD95","minWindIncD5"),"Station\nSouth <———————> North\n","lat")

# Get legends.
lgnd <- cowplot::get_legend(leg_func(ggplot_gtable(ggplot_build(g))))
lgnd2 <- cowplot::get_legend(leg_func(ggplot_gtable(ggplot_build(p))))

# Remove original legend.
g2 <- g + theme(legend.position="none") 
p2 <- p + theme(legend.position="none")

# Put together. 
g3 <- gridExtra::arrangeGrob(g2,lgnd,ncol=2,widths=c(8,1))
p3 <- gridExtra::arrangeGrob(p2,lgnd2,ncol=2,widths=c(8,1))

# Save.
# ggsave(g3,file="output/Bubble_Figures/Latitude_goodMods_May2021/GEV3.png",dpi=1000,width=13.5,height=9)
# ggsave(p3,file="output/Bubble_Figures/Latitude_goodMods/Poisson.png",dpi=1200,width=12.5,height=9.5)
# ggsave(p3,file="output/Bubble_Figures/Latitude_goodMods_May2021/Poisson3.png",dpi=1000,width=13.5,height=9)


# ggsave(g3,file="output/Bubble_Figures/new/GEV.png",dpi=1200,width=12.5,height=9.5)
# ggsave(p3,file="output/Bubble_Figures/new/Poisson.png",dpi=1200,width=12.5,height=9.5)
# ggsave(c3,file="output/Bubble_Figures/new/Precip.png",dpi=1200,width=6,height=9.5)

# ggsave(g3,file="output/Bubble_Figures/fill_in_blanks/GEV.png",dpi=1200,width=14,height=9.5)


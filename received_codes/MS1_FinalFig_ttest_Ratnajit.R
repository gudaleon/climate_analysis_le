
################MS1_Final Figure_t-test_Different Time frame####################


# Load required packages
library(openxlsx)
library(dplyr)

# Set working directory and file name
setwd("C:/Projects_Data Analysis/Study 1_Agroclimatic Indices & Crop Phenology/Manuscript 1_Agro-climatic Indices_Final-Draft_Aug 2025/MS1_Final Figure_t-test_230326/Soybean (MRI-CGCM3_RCP 4.5_April 25)_Ag-Indices/")
options(stringsAsFactors = FALSE)

data_file <- "Soybean (MRI-CGCM3_RCP 4.5_April 25)_Ag-Indices.xlsx"

# Get all sheet names
sheet_names <- getSheetNames(data_file)

# Read all sheets into a list
all_data <- lapply(sheet_names, function(s) {
  df <- read.xlsx(
    xlsxFile = data_file,
    sheet = s,
    detectDates = TRUE,
    skipEmptyRows = FALSE,
    colNames = TRUE
  )
  
  # Replace missing value code with NA
  df[df == -99.99] <- NA
  return(df)
})

# Assign sheet names to the list
names(all_data) <- sheet_names

# Filter each sheet into 4 climate time horizons
filtered_data <- lapply(all_data, function(mydata) {
  list(
    mydata1 = filter(mydata, between(Year, 1950, 1985)),
    mydata2 = filter(mydata, between(Year, 1986, 2020)),
    mydata3 = filter(mydata, between(Year, 2021, 2060)),
    mydata4 = filter(mydata, between(Year, 2061, 2100))
  )
})

# Select one sheet, for example the first sheet
sheet_result <- filtered_data[["Seed development drought"]]

# Extract Kenora values and remove NA
kenora2 <- na.omit(sheet_result$mydata2$Kenora)
kenora4 <- na.omit(sheet_result$mydata4$Kenora)


# Unpaired Welch Two Sample t-test
kenora_result <- t.test(
  kenora2,
  kenora4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(kenora_result)

# Save result to data frame
Kenora24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Kenora",
  Timeframe = "Present-FarFuture",
  statistic = unname(kenora_result$statistic),
  parameter = unname(kenora_result$parameter),
  p.value = kenora_result$p.value,
  conf.low = kenora_result$conf.int[1],
  conf.high = kenora_result$conf.int[2],
  estimate1 = unname(kenora_result$estimate[1]),
  estimate2 = unname(kenora_result$estimate[2]),
  method = kenora_result$method,
  alternative = kenora_result$alternative
)


# Extract Siouxlookout values and remove NA
Siouxlookout2 <- na.omit(sheet_result$mydata2$Siouxlookout)
Siouxlookout4 <- na.omit(sheet_result$mydata4$Siouxlookout)

# Unpaired Welch Two Sample t-test
Siouxlookout_result <- t.test(
  Siouxlookout2,
  Siouxlookout4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Siouxlookout_result)

# Save result to data frame
Siouxlookout24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Siouxlookout",
  Timeframe = "Present-FarFuture",
  statistic = unname(Siouxlookout_result$statistic),
  parameter = unname(Siouxlookout_result$parameter),
  p.value = Siouxlookout_result$p.value,
  conf.low = Siouxlookout_result$conf.int[1],
  conf.high = Siouxlookout_result$conf.int[2],
  estimate1 = unname(Siouxlookout_result$estimate[1]),
  estimate2 = unname(Siouxlookout_result$estimate[2]),
  method = Siouxlookout_result$method,
  alternative = Siouxlookout_result$alternative
)



# Extract Armstrong values and remove NA
Armstrong2 <- na.omit(sheet_result$mydata2$Armstrong)
Armstrong4 <- na.omit(sheet_result$mydata4$Armstrong)

# Unpaired Welch Two Sample t-test
Armstrong_result <- t.test(
  Armstrong2,
  Armstrong4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Armstrong_result)

# Save result to data frame
Armstrong24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Armstrong",
  Timeframe = "Present-FarFuture",
  statistic = unname(Armstrong_result$statistic),
  parameter = unname(Armstrong_result$parameter),
  p.value = Armstrong_result$p.value,
  conf.low = Armstrong_result$conf.int[1],
  conf.high = Armstrong_result$conf.int[2],
  estimate1 = unname(Armstrong_result$estimate[1]),
  estimate2 = unname(Armstrong_result$estimate[2]),
  method = Armstrong_result$method,
  alternative = Armstrong_result$alternative
)



# Extract Kapuskasing values and remove NA
Kapuskasing2 <- na.omit(sheet_result$mydata2$Kapuskasing)
Kapuskasing4 <- na.omit(sheet_result$mydata4$Kapuskasing)

# Unpaired Welch Two Sample t-test
Kapuskasing_result <- t.test(
  Kapuskasing2,
  Kapuskasing4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Kapuskasing_result)

# Save result to data frame
Kapuskasing24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Kapuskasing",
  Timeframe = "Present-FarFuture",
  statistic = unname(Kapuskasing_result$statistic),
  parameter = unname(Kapuskasing_result$parameter),
  p.value = Kapuskasing_result$p.value,
  conf.low = Kapuskasing_result$conf.int[1],
  conf.high = Kapuskasing_result$conf.int[2],
  estimate1 = unname(Kapuskasing_result$estimate[1]),
  estimate2 = unname(Kapuskasing_result$estimate[2]),
  method = Kapuskasing_result$method,
  alternative = Kapuskasing_result$alternative
)


# Extract Sault_ste_marie values and remove NA
Sault_ste_marie2 <- na.omit(sheet_result$mydata2$Sault_ste_marie)
Sault_ste_marie4 <- na.omit(sheet_result$mydata4$Sault_ste_marie)

# Unpaired Welch Two Sample t-test
Sault_ste_marie_result <- t.test(
  Sault_ste_marie2,
  Sault_ste_marie4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Sault_ste_marie_result)

# Save result to data frame
Sault_ste_marie24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Sault_ste_marie",
  Timeframe = "Present-FarFuture",
  statistic = unname(Sault_ste_marie_result$statistic),
  parameter = unname(Sault_ste_marie_result$parameter),
  p.value = Sault_ste_marie_result$p.value,
  conf.low = Sault_ste_marie_result$conf.int[1],
  conf.high = Sault_ste_marie_result$conf.int[2],
  estimate1 = unname(Sault_ste_marie_result$estimate[1]),
  estimate2 = unname(Sault_ste_marie_result$estimate[2]),
  method = Sault_ste_marie_result$method,
  alternative = Sault_ste_marie_result$alternative
)


# Extract North_Bay values and remove NA
North_Bay2 <- na.omit(sheet_result$mydata2$North_Bay)
North_Bay4 <- na.omit(sheet_result$mydata4$North_Bay)

# Unpaired Welch Two Sample t-test
North_Bay_result <- t.test(
  North_Bay2,
  North_Bay4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(North_Bay_result)

# Save result to data frame
North_Bay24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "North_Bay",
  Timeframe = "Present-FarFuture",
  statistic = unname(North_Bay_result$statistic),
  parameter = unname(North_Bay_result$parameter),
  p.value = North_Bay_result$p.value,
  conf.low = North_Bay_result$conf.int[1],
  conf.high = North_Bay_result$conf.int[2],
  estimate1 = unname(North_Bay_result$estimate[1]),
  estimate2 = unname(North_Bay_result$estimate[2]),
  method = North_Bay_result$method,
  alternative = North_Bay_result$alternative
)


# Extract Ottawa values and remove NA
Ottawa2 <- na.omit(sheet_result$mydata2$Ottawa)
Ottawa4 <- na.omit(sheet_result$mydata4$Ottawa)

# Unpaired Welch Two Sample t-test
Ottawa_result <- t.test(
  Ottawa2,
  Ottawa4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Ottawa_result)

# Save result to data frame
Ottawa24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Ottawa",
  Timeframe = "Present-FarFuture",
  statistic = unname(Ottawa_result$statistic),
  parameter = unname(Ottawa_result$parameter),
  p.value = Ottawa_result$p.value,
  conf.low = Ottawa_result$conf.int[1],
  conf.high = Ottawa_result$conf.int[2],
  estimate1 = unname(Ottawa_result$estimate[1]),
  estimate2 = unname(Ottawa_result$estimate[2]),
  method = Ottawa_result$method,
  alternative = Ottawa_result$alternative
)


# Extract Wiarton values and remove NA
Wiarton2 <- na.omit(sheet_result$mydata2$Wiarton)
Wiarton4 <- na.omit(sheet_result$mydata4$Wiarton)

# Unpaired Welch Two Sample t-test
Wiarton_result <- t.test(
  Wiarton2,
  Wiarton4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Wiarton_result)

# Save result to data frame
Wiarton24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Wiarton",
  Timeframe = "Present-FarFuture",
  statistic = unname(Wiarton_result$statistic),
  parameter = unname(Wiarton_result$parameter),
  p.value = Wiarton_result$p.value,
  conf.low = Wiarton_result$conf.int[1],
  conf.high = Wiarton_result$conf.int[2],
  estimate1 = unname(Wiarton_result$estimate[1]),
  estimate2 = unname(Wiarton_result$estimate[2]),
  method = Wiarton_result$method,
  alternative = Wiarton_result$alternative
)


# Extract Trenton values and remove NA
Trenton2 <- na.omit(sheet_result$mydata2$Trenton)
Trenton4 <- na.omit(sheet_result$mydata4$Trenton)

# Unpaired Welch Two Sample t-test
Trenton_result <- t.test(
  Trenton2,
  Trenton4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Trenton_result)

# Save result to data frame
Trenton24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Trenton",
  Timeframe = "Present-FarFuture",
  statistic = unname(Trenton_result$statistic),
  parameter = unname(Trenton_result$parameter),
  p.value = Trenton_result$p.value,
  conf.low = Trenton_result$conf.int[1],
  conf.high = Trenton_result$conf.int[2],
  estimate1 = unname(Trenton_result$estimate[1]),
  estimate2 = unname(Trenton_result$estimate[2]),
  method = Trenton_result$method,
  alternative = Trenton_result$alternative
)


# Extract Toronto values and remove NA
Toronto2 <- na.omit(sheet_result$mydata2$Toronto)
Toronto4 <- na.omit(sheet_result$mydata4$Toronto)

# Unpaired Welch Two Sample t-test
Toronto_result <- t.test(
  Toronto2,
  Toronto4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Toronto_result)

# Save result to data frame
Toronto24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Toronto",
  Timeframe = "Present-FarFuture",
  statistic = unname(Toronto_result$statistic),
  parameter = unname(Toronto_result$parameter),
  p.value = Toronto_result$p.value,
  conf.low = Toronto_result$conf.int[1],
  conf.high = Toronto_result$conf.int[2],
  estimate1 = unname(Toronto_result$estimate[1]),
  estimate2 = unname(Toronto_result$estimate[2]),
  method = Toronto_result$method,
  alternative = Toronto_result$alternative
)


# Extract London values and remove NA
London2 <- na.omit(sheet_result$mydata2$London)
London4 <- na.omit(sheet_result$mydata4$London)

# Unpaired Welch Two Sample t-test
London_result <- t.test(
  London2,
  London4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(London_result)

# Save result to data frame
London24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "London",
  Timeframe = "Present-FarFuture",
  statistic = unname(London_result$statistic),
  parameter = unname(London_result$parameter),
  p.value = London_result$p.value,
  conf.low = London_result$conf.int[1],
  conf.high = London_result$conf.int[2],
  estimate1 = unname(London_result$estimate[1]),
  estimate2 = unname(London_result$estimate[2]),
  method = London_result$method,
  alternative = London_result$alternative
)


# Extract Windsor values and remove NA
Windsor2 <- na.omit(sheet_result$mydata2$Windsor)
Windsor4 <- na.omit(sheet_result$mydata4$Windsor)

# Unpaired Welch Two Sample t-test
Windsor_result <- t.test(
  Windsor2,
  Windsor4,
  alternative = "two.sided",
  mu = 0,
  paired = FALSE,
  var.equal = FALSE,
  conf.level = 0.95
)

# View result
print(Windsor_result)

# Save result to data frame
Windsor24 <- data.frame(
  Indices_Name = "Seed development drought",
  Station = "Windsor",
  Timeframe = "Present-FarFuture",
  statistic = unname(Windsor_result$statistic),
  parameter = unname(Windsor_result$parameter),
  p.value = Windsor_result$p.value,
  conf.low = Windsor_result$conf.int[1],
  conf.high = Windsor_result$conf.int[2],
  estimate1 = unname(Windsor_result$estimate[1]),
  estimate2 = unname(Windsor_result$estimate[2]),
  method = Windsor_result$method,
  alternative = Windsor_result$alternative
)

# Combine both results in one CSV file
Seed_development_drought_results <- rbind(Kenora24, Siouxlookout24, Armstrong24, Kapuskasing24, Sault_ste_marie24, North_Bay24, Wiarton24, Ottawa24, Trenton24, Toronto24, London24, Windsor24)

# Write result to csv
write.csv(Seed_development_drought_results, "April 25_RCP 4.5_Seed_development_drought_Present-FarFuture_ttest.csv", row.names = FALSE)








#####################MS1_Final Figure_p-value and t-value########################


library(tidyverse)
library(grid)

ttest_data <- read.csv("C:/Projects_Data Analysis/Study 1_Agroclimatic Indices & Crop Phenology/Manuscript 1_Agro-climatic Indices_Final-Draft_Aug 2025/MS1_Final Figure_t-test_230326/MS1_ttest_Obs-GCM_Early-Regular_Final.csv",
  header = TRUE, stringsAsFactors = FALSE)

# Station order
station_order <- c("Ar", "Si", "Ke", "Ka", "Sa", "Nb", "Ot", "Wi", "Tr", "To", "Lo", "Wd")

# Station labels
station_labels <- c(
  "Ar" = "Ar", "Si" = "Si", "Ke" = "Ke", "Ka" = "Ka",
  "Sa" = "Sa", "Nb" = "Nb", "Ot" = "Ot", "Wi" = "Wi",
  "Tr" = "Tr", "To" = "To", "Lo" = "Lo", "Wd" = "Wd"
)

# Index order
index_order <- c("GDD", "NGDD", "PSC", "EF", "SKF", "CN", "WN", "MSF", "PFD", "EKF", "EH", "SDD", "FKF")

# Timeframe order
timeframe_order <- c(
  "Obs(1950-1985 vs 1986-2020)",
  "GCM(1986-2020 vs 2021-2060)",
  "GCM(1986-2020 vs 2061-2100)"
)

ttest_data <- ttest_data %>%
  mutate(
    Station_full = recode(Station, !!!station_labels),
    Station_full = factor(Station_full, levels = rev(station_labels[station_order])),
    Indices = factor(Indices, levels = index_order),
    Timeframe = factor(Timeframe, levels = timeframe_order),
    Data = factor(Data, levels = c("Obs", "RCP 4.5", "RCP 8.5")),
    Seeding = factor(Seeding, levels = c("Early", "Regular")),
    
    Trend = case_when(
      statistic.t > 0 ~ ">0",
      statistic.t < 0 ~ "<0",
      TRUE ~ "0"
    ),
    
    # Absolute t value for bubble diameter
    abs_t = abs(statistic.t),
    
    # Bubble size classes for legend
    abs_t_class = case_when(
      abs_t >= 0  & abs_t <= 5  ~ "0-5",
      abs_t > 5   & abs_t <= 10 ~ "6-10",
      abs_t > 10  & abs_t <= 15 ~ "11-15",
      abs_t > 15  & abs_t <= 21 ~ "16-21",
      TRUE ~ NA_character_
    ),
    
    abs_t_class = factor(
      abs_t_class,
      levels = c("0-5", "6-10", "11-15", "16-21")
    ),
    
    # Bubble boundary by p-value
    p_border = case_when(
      p.value < 0.05  ~ "<0.05",
      p.value >= 0.05 ~ ">0.05",
      TRUE ~ NA_character_
    ),
    
    # Custom row panels
    Row_group = case_when(
      Seeding == "Early"   & Data %in% c("Obs", "RCP 4.5") ~ "Early, RCP 4.5",
      Seeding == "Regular" & Data %in% c("Obs", "RCP 4.5") ~ "Regular, RCP 4.5",
      Seeding == "Early"   & Data == "RCP 8.5"             ~ "Early, RCP 8.5",
      Seeding == "Regular" & Data == "RCP 8.5"             ~ "Regular, RCP 8.5",
      TRUE ~ NA_character_
    ),
    
    Row_group = factor(
      Row_group,
      levels = c(
        "Early, RCP 4.5",
        "Regular, RCP 4.5",
        "Early, RCP 8.5",
        "Regular, RCP 8.5"
      )
    )
  ) %>%
  filter(!is.na(Row_group))

Fig_ttest <- ggplot(ttest_data, aes(x = Indices, y = Station_full)) +
  
  geom_point(
    data = ttest_data %>% filter(Trend != "0"),
    aes(size = abs_t_class, fill = statistic.t, color = p_border),
    shape = 21, stroke = 1.2, alpha = 0.9
  ) +
  
  geom_point(
    data = ttest_data %>% filter(Trend == "0"),
    shape = 4, size = 2.2, stroke = 0.8, color = "black"
  ) +
  
  facet_grid(Row_group ~ Timeframe, scales = "fixed") +
  
  scale_fill_gradient2(
    low = "#6A5ACD",
    mid = "white",
    high = "#B22222",
    midpoint = 0,
    name = "t-value"
  ) +
  
  scale_color_manual(
    values = c("<0.05" = "darkgreen", ">0.05" = "red"),
    name = "p-value"
  ) +
  
  scale_size_manual(
    values = c(
      "0-5"   = 2.4,
      "6-10"  = 3.6,
      "11-15" = 4.8,
      "16-21" = 6
    ),
    name = "Absolute t-value"
  ) +
  
  labs(
    x = "Indices (Emergence <---------------------> Full Maturity)",
    y = "Stations (South <-----------------> North)"
  ) +
  
  guides(
    fill = guide_colorbar(order = 1),
    size = guide_legend(
      order = 2,
      override.aes = list(fill = "white", color = "black", shape = 21, stroke = 1)
    ),
    color = guide_legend(
      order = 3,
      override.aes = list(size = 4, fill = "white", shape = 21, stroke = 1.5)
    )
  ) +
  
  theme_bw(base_family = "serif") +
  theme(
    strip.background = element_blank(),
    strip.text.x = element_text(size = 12, face = "bold"),
    strip.text.y = element_text(size = 12, face = "bold", angle = 90),
    axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1, size = 12),
    axis.text.y = element_text(size = 12),
    axis.title = element_text(size = 12, face = "bold"),
    panel.grid = element_blank(),
    panel.border = element_blank(),
    axis.line = element_line(color = "black"),
    panel.spacing = unit(0.6, "lines"),
    legend.position = "right",
    legend.title = element_text(size = 12, face = "bold"),
    legend.text = element_text(size = 12),
    legend.key.size = unit(1, "cm")
  )

print(Fig_ttest)

# Save the plot as a high-resolution JPEG
ggsave("C:/Projects_Data Analysis/Study 1_Agroclimatic Indices & Crop Phenology/Manuscript 1_Agro-climatic Indices_Final-Draft_Aug 2025/MS1_Final Figure_t-test_230326/MS1_Final-Fig_p&t-value_Final1.jpeg",
  plot = Fig_ttest, width = 14, height = 12, dpi = 600, units = "in")


#####################################################################################



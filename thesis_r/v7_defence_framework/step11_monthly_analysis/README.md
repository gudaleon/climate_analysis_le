# Monthly analysis (Section 3.4 / v7 seasonal results)

- `step11a_monthly_inputs.R`: monthly CDD from the daily series (Climpact/climdex method) and the monthly index workbooks (observations, BCC-CSM2-MR, NorESM2-LM London, EC-Earth3-Veg Fergus and Harrow) from the Climpact MON outputs; same content as `2_Data/4_Monthly_analysis`.
- `step11b_monthly_statistics.R`: upper-quartile medians per month and period (lower quartile for TXn), Hist to Present and Near to Far changes, Wilcoxon p-values, the 'Monthly (Sec 3.4)' workbook sheet and the numbers quoted in the v7 seasonal text (incl. SPEI6 minus SPI6 gaps and CDD).

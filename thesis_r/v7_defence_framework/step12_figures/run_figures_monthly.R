# run_figures_monthly.R
# Runs the six monthly boxplot scripts (OBS_JFM, OBS_JJAS, GCM_hp_JFM, GCM_hp_JJAS, GCM_nf_JFM,
# GCM_nf_JJAS) for the three stations with their temperature reference model (London NorESM2-LM,
# Fergus and Harrow EC-Earth3-Veg; precipitation always BCC-CSM2-MR).
# Inputs:  2_Data/4_Monthly_analysis/*.xlsx
# Outputs: 3_Code/output/figures_monthly/
# The scripts are run in a UTF-8 locale so that the degree sign and the en dash in the labels are
# drawn (in a C/POSIX locale R draws them as dots, as in the PNGs of S/figs_pcic/out).
# Run:     cd <package root> && Rscript 3_Code/step12_figures/run_figures_monthly.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
if (!isTRUE(l10n_info()[["UTF-8"]])) Sys.setenv(LC_ALL = "C.UTF-8")
TEMP_REF <- c(London = "NorESM", Fergus = "EC", Harrow = "EC")
for (s in c("OBS_JFM", "OBS_JJAS", "GCM_hp_JFM", "GCM_hp_JJAS", "GCM_nf_JFM", "GCM_nf_JJAS")) {
  for (st in STATIONS) {
    cat(s, st, "\n")
    rc <- system2(file.path(R.home("bin"), "Rscript"), c(file.path(PKG, "3_Code", "step12_figures", paste0(s, ".R")), st, TEMP_REF[[st]]),
                  stdout = FALSE, stderr = FALSE)
    if (rc != 0) stop(s, " failed for ", st)
  }
}

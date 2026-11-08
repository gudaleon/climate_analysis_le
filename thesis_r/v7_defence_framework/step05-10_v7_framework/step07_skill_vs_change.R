# Step 07 (v7 framework): does Test 1 skill predict the Test 2 outcome?
# Each index x station case is skilful when at least 10 of its 20 model-window tests pass
# (10 models x Historical/Present, from step 05). Skill is crossed with the Test 2 class from
# step 06: 2 x 2 table (skilful vs change bounded), Fisher exact test, bounded rates, and the
# number of cases a skill-only screen would misjudge under alternative rules
# (>= 15 of 20, >= 5 of 10 Present passes, >= 8 of 10 Present passes).
# Inputs : 3_Code/output/v7_step05_model_performance/model_obs_pvalues.csv
#          3_Code/output/v7_step06_change_test/B1_envelope.csv
# Outputs: 3_Code/output/v7_step07_skill_vs_change/
#            skill_vs_change_cases.csv  (one row per case, as the workbook sheet)
#            skill_vs_change_summary.csv (2 x 2 counts, rates, Fisher p)
#            skill_by_class.csv          (skilful x all three Test 2 classes)
#            alternative_rules.csv       (misjudged cases under other skill rules)
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step07_skill_vs_change.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
od <- out_dir("v7_step07_skill_vs_change")

pv <- read_step("v7_step05_model_performance", "model_obs_pvalues.csv")
B  <- read_step("v7_step06_change_test", "B1_envelope.csv")

# passes per case: all 20 tests, and the 10 Present tests only
np <- aggregate(cbind(npass = pass_Historical + pass_Present, pr = pass_Present) ~ Station + Index, data = pv, FUN = sum)

# cases in Table B1 order
SK <- merge(B[, c("Station", "Index", "Category", "cls")], np, by = c("Station", "Index"), all.x = TRUE, sort = FALSE)
SK <- SK[match(paste(B$Station, B$Index), paste(SK$Station, SK$Index)), ]
skil <- SK$npass >= 10; bnd <- SK$cls == "Bounded"
cases <- data.frame(Station = SK$Station, Index = SK$Index, Category = SK$Category, Class = SK$cls,
  `Model-window passes (of 20)` = SK$npass, `Skilful (>= 10 of 20)` = skil, `Change bounded` = bnd,
  Outcome = ifelse(skil & bnd, "Skilful and bounded", ifelse(skil & !bnd, "Skilful, not bounded (Type I)",
            ifelse(!skil & bnd, "Not skilful, bounded (Type II)", "Not skilful, not bounded"))),
  check.names = FALSE)
write_csv_full(cases, file.path(od, "skill_vs_change_cases.csv"))

# 2 x 2 table: a = skilful & bounded, b = skilful & not bounded, c = not skilful & bounded, d = neither
a <- sum(skil & bnd); b <- sum(skil & !bnd); c_ <- sum(!skil & bnd); d <- sum(!skil & !bnd)
pf <- fisher.test(matrix(c(a, c_, b, d), 2))$p.value
summ <- data.frame(Item = c("Cases (index x station)", "Skilful and bounded", "Skilful, not bounded (Type I)",
                            "Not skilful, bounded (Type II)", "Not skilful, not bounded", "Misjudged by a skill-only screen",
                            "Bounded rate if skilful (%)", "Bounded rate if not skilful (%)", "Fisher exact p"),
                   Value = c(nrow(cases), a, b, c_, d, b + c_, 100 * a / (a + b), 100 * c_ / (c_ + d), pf))
write_csv_full(summ, file.path(od, "skill_vs_change_summary.csv"))

# skilful x three classes, and sign reversals among skilful cases
byc <- as.data.frame.matrix(table(Skilful = skil, SK$cls))
byc <- cbind(Skilful = rownames(byc), byc)
write_csv_full(byc, file.path(od, "skill_by_class.csv"))

# alternative skill rules: misjudged = skilful & not bounded + not skilful & bounded
alt <- list(">=10 of 20" = SK$npass >= 10, ">=15 of 20" = SK$npass >= 15, "Present >=5 of 10" = SK$pr >= 5, "Present >=8 of 10" = SK$pr >= 8)
altd <- data.frame(Rule = names(alt), Misjudged = sapply(alt, function(s) sum(s & !bnd) + sum(!s & bnd)), row.names = NULL)
write_csv_full(altd, file.path(od, "alternative_rules.csv"))

cat(sprintf("2x2 [[%d, %d], [%d, %d]]  misjudged %d  bounded if skilful %.1f%%  if not %.1f%%  Fisher p %.3f  reversals among skilful %d\n",
            a, b, c_, d, b + c_, 100 * a / (a + b), 100 * c_ / (c_ + d), pf, sum(skil & SK$cls == "Sign reversal")))
print(altd)

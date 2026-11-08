# Step 10 (v7 framework): numbers quoted in the thesis text and the defence slides.
# Prints the key numbers quoted in the thesis and slides: S9 (Test 1 pass counts), S10
# (Test 2 envelope), S11 (skill vs change), S12/14 (pooled projections) and S16 (process
# confidence), line by line in the same wording. The monthly part (S15) is produced by the
# monthly analysis scripts.
# Inputs : outputs of steps 05, 06, 08 and 09; annual index tables (observed PRCPTOT change)
# Outputs: 3_Code/output/v7_step10_key_numbers/key_numbers.txt (the printout)
#          3_Code/output/v7_step10_key_numbers/key_numbers.csv (same lines, one column)
# Run    : cd <package root> && Rscript 3_Code/step05-10_v7_framework/step10_key_numbers.R
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "common", "common.R"))
source(file.path(Sys.getenv("THESIS_PKG", getwd()), "3_Code", "step05-10_v7_framework", "v7_helpers.R"))
od <- out_dir("v7_step10_key_numbers")
rd <- read_step
pc <- rd("v7_step05_model_performance", "pass_counts.csv")
pv <- rd("v7_step05_model_performance", "model_obs_pvalues.csv")
B  <- rd("v7_step06_change_test", "B1_envelope.csv")
C  <- rd("v7_step08_projections", "C1_projections.csv")
D1 <- rd("v7_step09_process_confidence", "D1_process_confidence.csv")

# ---- small formatters that print values as in the original output
pyfloat <- function(x) {            # float text: shortest exact text, ".0" on whole numbers
  if (is.na(x)) return("nan")
  s <- num_text(x); if (!grepl("[.e]", s)) s <- paste0(s, ".0"); s
}
q <- function(s) paste0("'", s, "'")
pylist <- function(items) paste0("[", paste(items, collapse = ", "), "]")
pydict <- function(keys, vals) paste0("{", paste(paste0(q(keys), ": ", vals), collapse = ", "), "}")
pct1 <- function(x) sprintf("%+.1f", x)
rj <- function(s, w) paste0(strrep(" ", pmax(0, w - nchar(s))), s)   # right-justify to width (characters)
lj <- function(s, w) paste0(s, strrep(" ", pmax(0, w - nchar(s))))   # left-justify
fmt_signed <- function(x, d) if (is.na(x)) "+nan" else sprintf(paste0("%+.", d, "f"), x)

L <- c()
add <- function(...) L <<- c(L, paste0(...))

# ---- S9: Test 1
add("== S9")
t <- pc[pc$station == "LONDON" & pc$group == "T", ]; t <- t[order(-t$total), ]
add("London T ", pylist(sprintf("[%s, %d]", q(t$model), t$total)))
for (st in c("FERGUS", "HARROW")) {
  t <- pc[pc$station == st & pc$group == "T", ]; t <- t[order(-t$total), ][1:3, ]
  add(st, " T top3 ", pylist(sprintf("[%s, %d]", q(t$model), t$total)))
}
tt <- tapply(pc$total[pc$group == "T"], pc$station[pc$group == "T"], sum)
tt <- tt[sort(names(tt), method = "radix")]
add("station T totals ", pydict(names(tt), tt))
KS <- c("DTR", "DTRgt15", "SDII", "R20mm", "CWD", "PRCPTOT", "R95p", "R99p", "R95pTOT", "R99pTOT")
for (st in STATIONS) {
  n <- sapply(KS, function(k) { s <- pv[pv$Station == st & pv$Index == k, ]; sum(s$pass_Historical) + sum(s$pass_Present) })
  add(toupper(st), " ", pydict(KS, n))
}

# ---- S10: Test 2
add("== S10")
allb <- names(which(tapply(B$cls == "Bounded", B$Index, all)))
allb <- sort(allb, method = "radix")
add("bounded all3 ", length(allb), " thermal ", sum(allb %in% TEMP_INDICES), " precip ", pylist(q(allb[!allb %in% TEMP_INDICES])))
sp <- tapply(B$cls == "Bounded", B$Station, function(v) round(100 * mean(v), 1)); sp <- sp[sort(names(sp), method = "radix")]
add("station % ", pydict(names(sp), sapply(sp, pyfloat)))
add("temp % ", pyfloat(round(100 * mean(B$cls[B$Index %in% TEMP_INDICES] == "Bounded"), 1)),
    " precip % ", pyfloat(round(100 * mean(B$cls[!B$Index %in% TEMP_INDICES] == "Bounded"), 1)))
EX <- c("RX1day", "RX3day", "RX5day", "SDII", "R95p", "R99p", "R95pTOT", "R99pTOT")
add("extreme bounded ", sum(B$cls[B$Index %in% EX] == "Bounded"), " /24")
vc <- sort(table(B$cls), decreasing = TRUE)
rev_ <- B[B$cls == "Sign reversal", ]
add("classes ", pydict(names(vc), as.integer(vc)), " reversals ", pylist(sprintf("[%s, %s]", q(rev_$Station), q(rev_$Index))))

# ---- S11: skill vs change (cases in the order of the p-value table)
add("== S11")
np <- aggregate(cbind(npass = pass_Historical + pass_Present, pr = pass_Present) ~ Station + Index, data = pv, FUN = sum)
key <- unique(pv[, c("Station", "Index")])
M <- merge(key, np, sort = FALSE); M <- M[match(paste(key$Station, key$Index), paste(M$Station, M$Index)), ]
M$cls <- B$cls[match(paste(M$Station, M$Index), paste(B$Station, B$Index))]
b <- M$cls == "Bounded"; sk <- M$npass >= 10
# crosstab printed as in the original output
cl <- sort(unique(M$cls), method = "radix")
tab <- sapply(cl, function(k) c(sum(!sk & M$cls == k), sum(sk & M$cls == k)))
w <- pmax(nchar(cl), apply(tab, 2, function(v) max(nchar(v))))
w0 <- max(nchar(c("cls", "npass", "False", "True")))
add(lj("cls", w0), paste0("  ", rj(cl, w), collapse = ""))
add(lj("npass", w0), strrep(" ", sum(w + 2)))
for (i in 1:2) add(lj(c("False", "True")[i], w0), paste0("  ", rj(tab[i, ], w), collapse = ""))
a_ <- sum(sk & b); b_ <- sum(sk & !b); c_ <- sum(!sk & b); d_ <- sum(!sk & !b)
pf <- fisher.test(matrix(c(a_, c_, b_, d_), 2))$p.value
add(sprintf("mis %d pass->b %.1f fail->b %.1f p %.3f rev among pass %d", b_ + c_, 100 * a_ / (a_ + b_), 100 * c_ / (c_ + d_), pf,
            sum(sk & M$cls == "Sign reversal")))
alt <- list(">=15" = M$npass >= 15, "pres>=5" = M$pr >= 5, "pres>=8" = M$pr >= 8)
add("alt rules ", pydict(names(alt), sapply(alt, function(s) sum(s & !b) + sum(!s & b))))
s <- M[M$Station == "London" & M$Index %in% c("R95p", "R20mm", "CWD"), ]
add(pylist(sprintf("[%s, %d, %s]", q(s$Index), s$npass, q(s$cls))))

# ---- S12/14: pooled projections (Table C1)
add("== S12/14 C1")
for (k in c("TMm", "TXge30", "ID", "PRCPTOT", "R95p", "R99p", "TR", "FD")) {
  parts <- sapply(STATIONS, function(s) {
    r <- C[C$Station == s & C$Index == k, ]; h <- r$Hist_median; f <- r$Far_median
    rel <- if (h != 0) 100 * (f / h - 1) else NA
    sprintf("%s %.2f->%.2f (%s, %s%%)", substr(s, 1, 3), h, f, fmt_signed(f - h, 2), fmt_signed(rel, 1))
  })
  add(k, " ", paste(parts, collapse = " | "))
}

# ---- S16: process confidence (Table D1), printed as a table
add("== S16 D1")
cols <- c("Climate-process group", "n (lines)", "Coherence Hist→Present (%)", "Coherence Hist→Near (%)",
          "Coherence Hist→Far (%)", "Bounded (%)", "Sign reversals", "Confidence (rule)")
# table layout: one space between columns, every value with a leading space, and a leading
# space on the header of numeric columns; percentages (doubles) with one decimal
num <- sapply(cols, function(cn) is.numeric(D1[[cn]]))
cells <- lapply(cols, function(cn) { v <- D1[[cn]]; paste0(" ", if (is.double(v)) sprintf("%.1f", v) else as.character(v)) })
hdr <- ifelse(num, paste0(" ", cols), cols)
ww <- mapply(function(h, v) max(nchar(h), nchar(v)), hdr, cells)
idx <- as.character(seq_len(nrow(D1)) - 1); wi <- max(nchar(idx))
add(strrep(" ", wi), paste0(" ", rj(hdr, ww), collapse = ""))
for (i in seq_len(nrow(D1)))
  add(rj(idx[i], wi), paste0(" ", mapply(function(v, w) rj(v[i], w), cells, ww), collapse = ""))
# observed Historical-to-Present change of PRCPTOT, full precision (recomputed from the annual tables)
obs <- sapply(STATIONS, function(s) { g <- load_annual(s); g <- g[g$Index %in% "PRCPTOT", ]
  median(per(g, "Observed", "Pres")) - median(per(g, "Observed", "Hist")) })
add("obs PRCPTOT ", pylist(sprintf("[%s, %s]", q(STATIONS), sapply(obs, pyfloat))))

writeLines(L, file.path(od, "key_numbers.txt"), useBytes = TRUE)
write_csv_full(data.frame(`Key numbers` = L, check.names = FALSE), file.path(od, "key_numbers.csv"))
cat(L, sep = "\n")

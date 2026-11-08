# Helpers shared by the v7 framework steps (sourced after common.R).
#   num_text()       shortest text that reads back to exactly the same double (as in the original output)
#   write_csv_full() write.csv with doubles at full precision (write.csv keeps only 15 digits)
#   read_step()      read a csv written by an earlier step

# the index names and table headings contain non-ASCII characters (degree sign, arrows)
if (!l10n_info()$`UTF-8`) invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", "C.UTF-8")))

num_text <- function(x) {
  out <- rep(NA_character_, length(x)); todo <- which(!is.na(x))
  whole <- todo[is.finite(x[todo]) & x[todo] == round(x[todo]) & abs(x[todo]) < 1e15]
  out[whole] <- sprintf("%.0f", x[whole]); todo <- setdiff(todo, whole)
  for (d in 1:17) {
    if (!length(todo)) break
    s <- trimws(formatC(x[todo], digits = d, format = "g"))
    ok <- as.numeric(s) == x[todo]
    out[todo[ok]] <- s[ok]; todo <- todo[!ok]
  }
  out
}

write_csv_full <- function(df, file) {
  chr <- which(!sapply(df, is.numeric) & !sapply(df, is.logical))
  for (j in which(sapply(df, is.double))) df[[j]] <- num_text(df[[j]])
  write.csv(df, file, row.names = FALSE, quote = chr, na = "NA")
}

read_step <- function(step, f) read.csv(file.path(OUTD, step, f), check.names = FALSE, encoding = "UTF-8")

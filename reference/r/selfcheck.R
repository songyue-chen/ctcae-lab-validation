# selfcheck.R - proves that the R loader and comparator work, without any grading implementation: the published
# expectations themselves play the part of a perfect implementation, then they are corrupted on purpose.
#
#   Rscript reference/r/selfcheck.R [path/to/ctcae-lab-validation]
#
# Prints SELFCHECK PASSED and exits with status 0, or stops with an error.

args <- commandArgs(trailingOnly = TRUE)
dir <- if (length(args)) args[1] else {
  f <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", f[grepl("^--file=", f)])
  if (length(f)) normalizePath(file.path(dirname(f), "..", "..")) else getwd()
}
source(file.path(dir, "reference", "r", "load_records.R"))
source(file.path(dir, "reference", "r", "compare_results.R"))
d <- ctcval_load(dir)
fails <- 0L
expect <- function(cmp, status, mismatches, label) {
  if (cmp$status != status || cmp$mismatches != mismatches) {
    fails <<- fails + 1L
    message("ERROR: selfcheck ", label, " - expected ", status, " with ", mismatches, " mismatches but got ",
            cmp$status, " with ", cmp$mismatches)
  } else message("ok: selfcheck ", label, " (", status, " with ", mismatches, " mismatches)")
}
r <- d$records

# 1. a perfect bidirectional implementation of CTCAE v5 (the wide expectation columns)
perfect_v5 <- data.frame(RECORD_ID = r$RECORD_ID, GRL = r$EXP_GRADE_LOW_V5, GRH = r$EXP_GRADE_HIGH_V5,
                         TRL = r$EXP_TERM_LOW_V5, TRH = r$EXP_TERM_HIGH_V5, stringsAsFactors = FALSE)
cols5 <- list(grade_low = "GRL", grade_high = "GRH", term_low = "TRL", term_high = "TRH")
expect(ctcval_compare(perfect_v5, 5, cols = cols5, data = d, print = FALSE), "PASS", 0, "1 perfect bidirectional v5")

# 2. a perfect single-scale implementation of CTCAE v6
perfect_v6 <- data.frame(RECORD_ID = r$RECORD_ID, G = r$EXP_GRADE_V6, T = r$EXP_TERM_V6, stringsAsFactors = FALSE)
expect(ctcval_compare(perfect_v6, 6, cols = list(grade = "G", term = "T"), data = d, print = FALSE), "PASS", 0, "2 perfect single-scale v6")

# 3. four corrupted records: three grades raised, one record removed, one term in lower case with blanks (never counts)
corrupt_v5 <- perfect_v5
corrupt_v5$GRL[2:4] <- corrupt_v5$GRL[2:4] + 1L
corrupt_v5$TRL[6] <- paste0(tolower(corrupt_v5$TRL[6]), "   ")
corrupt_v5 <- corrupt_v5[-5, ]
cmp3 <- ctcval_compare(corrupt_v5, 5, cols = cols5, data = d, print = FALSE)
expect(cmp3, "FAIL", 4, "3 corrupted bidirectional v5")
if (!identical(sort(cmp3$mismatch$RECORD_ID[!duplicated(cmp3$mismatch$RECORD_ID)]), c(2L, 3L, 4L, 5L))) {
  fails <- fails + 1L; message("ERROR: selfcheck 3 - the mismatch listing does not name records 2 to 5")
}

# 4. the module filter: the corrupted records are CORE records, so UNITS and CATEGORY still pass
expect(ctcval_compare(corrupt_v5, 5, cols = cols5, modules = c("UNITS", "CATEGORY"), data = d, print = FALSE), "PASS", 0, "4 module filter")

# 5. grades only (terms not compared) and the convention-dependent records excluded
expect(ctcval_compare(perfect_v5, 5, cols = list(grade_low = "GRL", grade_high = "GRH"), convdep = FALSE, data = d, print = FALSE),
       "PASS", 0, "5 grades only without convention-dependent records")

# 6. an alternative profile: perfect results built from the BESTCASE_ENZYMES rows pass under that profile, and the
#    DEFAULT results fail under it on exactly the records the profile changes
e <- d$expectations
alt <- e[e$VERSION == 5 & e$PROFILE == "BESTCASE_ENZYMES" & e$DIRECTION %in% c("LOW", "HIGH"), ]
def <- e[e$VERSION == 5 & e$PROFILE == "DEFAULT", ]
def <- def[match(paste(alt$RECORD_ID, alt$DIRECTION), paste(def$RECORD_ID, def$DIRECTION)), ]
changed <- !((is.na(alt$GRADE) & is.na(def$GRADE)) | (!is.na(alt$GRADE) & !is.na(def$GRADE) & alt$GRADE == def$GRADE)) | alt$TERM != def$TERM
n_bestcase <- length(unique(alt$RECORD_ID[changed]))
bestcase_v5 <- perfect_v5
for (dirn in c("LOW", "HIGH")) {
  a <- alt[alt$DIRECTION == dirn, ]
  i <- match(a$RECORD_ID, bestcase_v5$RECORD_ID)
  if (dirn == "LOW") { bestcase_v5$GRL[i] <- a$GRADE; bestcase_v5$TRL[i] <- a$TERM } else { bestcase_v5$GRH[i] <- a$GRADE; bestcase_v5$TRH[i] <- a$TERM }
}
expect(ctcval_compare(bestcase_v5, 5, profile = "BESTCASE_ENZYMES", cols = cols5, data = d, print = FALSE), "PASS", 0, "6a perfect BESTCASE_ENZYMES v5")
expect(ctcval_compare(perfect_v5, 5, profile = "BESTCASE_ENZYMES", cols = cols5, data = d, print = FALSE), "FAIL", n_bestcase, "6b DEFAULT results under BESTCASE_ENZYMES v5")

# 7. the ADaM and SDTM namings load
adam <- ctcval_load(dir, naming = "adam")$records
sdtm_d <- ctcval_load(dir, naming = "sdtm"); sdtm <- sdtm_d$records
n_adam <- sum(!is.na(adam$AVAL) & !is.na(adam$ADT)); n_sdtm <- sum(!is.na(sdtm$LBSTRESN) & sdtm$LBDTC != "")
if (n_adam != n_sdtm || n_adam == 0) { fails <- fails + 1L; message("ERROR: selfcheck 7 namings - ADaM and SDTM loads differ") } else message("ok: selfcheck 7 namings (", n_adam, " records with a value under both namings)")
# 7b. the comparator works on the SDTM-named load (STATUS is renamed LBSTAT there)
perfect_sdtm <- data.frame(RECORD_ID = sdtm$RECORD_ID, GRL = sdtm$EXP_GRADE_LOW_V5, GRH = sdtm$EXP_GRADE_HIGH_V5)
expect(ctcval_compare(perfect_sdtm, 5, cols = list(grade_low = "GRL", grade_high = "GRH"), data = sdtm_d, print = FALSE),
       "PASS", 0, "7b comparison on the SDTM-named load")

# one printed example of the report
invisible(ctcval_compare(corrupt_v5, 5, cols = cols5, modules = "CORE", data = d))

if (fails == 0L) cat("\nSELFCHECK PASSED - loader and comparator work in this R session\n") else stop("SELFCHECK FAILED - ", fails, " check(s) failed")

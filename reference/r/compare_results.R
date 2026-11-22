# compare_results.R - compares an implementation's grades with the expected values (base R, no packages needed)
#
#   source("reference/r/load_records.R"); source("reference/r/compare_results.R")
#   d <- ctcval_load("path/to/ctcae-lab-validation")
#   cmp <- ctcval_compare(results, version = 5, profile = "DEFAULT",
#                         cols = list(id = "RECORD_ID", grade_low = "ATOXGRL", grade_high = "ATOXGRH",
#                                     term_low = "ATOXDSCL", term_high = "ATOXDSCH"), data = d)
#   cmp <- ctcval_compare(results, version = 6, cols = list(grade = "ATOXGR", term = "ATOXDSC"), data = d)   # single scale
#
# results: a data frame with the record key and your grade (numeric 0-4, NA = not graded) and term columns.
# Give grade_low and grade_high (bidirectional designs) or grade (single worst grade); term columns are optional.
# Terms are compared case- and whitespace-insensitively. A record absent from results is compared as "no grade,
# no term". modules = c("CORE", "BASELINE") limits the comparison; convdep = FALSE excludes CONVENTION_DEP = Y records.
#
# Returns (invisibly when print = TRUE) a list: status ("PASS"/"FAIL"), records, mismatches, absent, module (status by
# module), mismatch (listing), rules (coverage and status by criteria RULE_ID of the version), detail, record.

ctcval_compare <- function(results, version = 5, profile = "DEFAULT", cols = list(), modules = NULL, convdep = TRUE,
                           data = NULL, dir = NULL, print = TRUE) {
  if (is.null(data)) {
    if (is.null(dir)) stop("ctcval_compare: give data = ctcval_load(dir) or dir =")
    data <- ctcval_load(dir)
  }
  cols <- utils::modifyList(list(id = "RECORD_ID", grade_low = NULL, grade_high = NULL, term_low = NULL, term_high = NULL,
                                 grade = NULL, term = NULL), cols)
  if (!is.null(cols$grade_low) && !is.null(cols$grade_high)) {
    mode <- "DIRECTIONAL"; terms <- !is.null(cols$term_low) && !is.null(cols$term_high)
  } else if (!is.null(cols$grade)) {
    mode <- "WORST"; terms <- !is.null(cols$term)
  } else stop("ctcval_compare: give cols grade_low and grade_high, or grade")
  need <- unlist(cols[c("id", if (mode == "DIRECTIONAL") c("grade_low", "grade_high", if (terms) c("term_low", "term_high"))
                        else c("grade", if (terms) "term"))])
  absent_cols <- setdiff(need, names(results))
  if (length(absent_cols)) stop("ctcval_compare: results has no column ", paste(absent_cols, collapse = ", "))
  profile <- toupper(profile)
  norm <- function(x) gsub("\\s+", "", toupper(ifelse(is.na(x), "", as.character(x))))

  # 1. expected values of the version under the profile: DEFAULT rows, overridden by the profile rows
  ex <- data$expectations[data$expectations$VERSION == version & data$expectations$PROFILE %in% c("DEFAULT", profile), ]
  if (!nrow(ex)) stop("ctcval_compare: no expectations for version ", version)
  key <- function(x) paste(x$RECORD_ID, x$DIRECTION)
  pr <- ex[ex$PROFILE != "DEFAULT", ]
  df <- ex[ex$PROFILE == "DEFAULT" & !(key(ex) %in% key(pr)), ]
  ex <- rbind(df, pr)
  pick <- function(d, col) { x <- ex[ex$DIRECTION == d, ]; x[[col]][match(rec$RECORD_ID, x$RECORD_ID)] }

  # 2. records in scope (STATUS is not kept: naming = "sdtm" renames it to LBSTAT)
  rec <- data$records[, c("RECORD_ID", "SCENARIO_ID", "MODULE", "GRADABLE", "RULE_IDS", "CONVENTIONS",
                          "CONVENTION_DEP", "DESCRIPTION")]
  if (!is.null(modules)) rec <- rec[rec$MODULE %in% toupper(modules), ]
  if (!isTRUE(convdep)) rec <- rec[rec$CONVENTION_DEP != "Y", ]
  if (!nrow(rec)) stop("ctcval_compare: no record selected (check modules and convdep)")
  res <- results[!duplicated(results[[cols$id]]), ]
  if (nrow(res) < nrow(results)) warning("ctcval_compare: ", nrow(results) - nrow(res), " duplicate ", cols$id, " rows in results dropped (first kept)")
  m <- match(rec$RECORD_ID, res[[cols$id]])
  got <- function(col) if (is.null(col)) rep(NA, nrow(rec)) else res[[col]][m]

  # 3. one row per record x direction
  one <- function(d, exp_grade, exp_term, got_grade, got_term) {
    grade_ok <- (is.na(exp_grade) & is.na(got_grade)) | (!is.na(exp_grade) & !is.na(got_grade) & exp_grade == got_grade)
    term_ok <- if (terms) norm(exp_term) == norm(got_term) else rep(TRUE, nrow(rec))
    data.frame(rec, DIRECTION = d, EXP_GRADE = exp_grade, GOT_GRADE = as.numeric(got_grade),
               EXP_TERM = ifelse(is.na(exp_term), "", exp_term), GOT_TERM = ifelse(is.na(got_term), "", as.character(got_term)),
               GRADE_OK = grade_ok, TERM_OK = term_ok, OK = grade_ok & term_ok, IN_RESULTS = !is.na(m),
               stringsAsFactors = FALSE)
  }
  if (mode == "DIRECTIONAL") {
    detail <- rbind(one("LOW", pick("LOW", "GRADE"), pick("LOW", "TERM"), got(cols$grade_low), got(cols$term_low)),
                    one("HIGH", pick("HIGH", "GRADE"), pick("HIGH", "TERM"), got(cols$grade_high), got(cols$term_high)))
  } else {
    detail <- one("WORST", pick("WORST", "GRADE"), pick("WORST", "TERM"), got(cols$grade), got(cols$term))
  }
  detail <- detail[order(detail$RECORD_ID, detail$DIRECTION), ]
  rownames(detail) <- NULL

  # 4. record level, module summary, mismatch listing, rule coverage
  ok_rec <- tapply(detail$OK, detail$RECORD_ID, all)
  record <- rec
  record$OK <- as.logical(ok_rec[as.character(rec$RECORD_ID)])
  record$IN_RESULTS <- !is.na(m)
  module <- do.call(rbind, lapply(split(record, record$MODULE), function(x)
    data.frame(MODULE = x$MODULE[1], RECORDS = nrow(x), AGREE = sum(x$OK), MISMATCHES = sum(!x$OK),
               NOT_IN_RESULTS = sum(!x$IN_RESULTS), STATUS = if (all(x$OK)) "PASS" else "FAIL", stringsAsFactors = FALSE)))
  rownames(module) <- NULL
  mismatch <- detail[!detail$OK, c("RECORD_ID", "SCENARIO_ID", "MODULE", "DIRECTION", "EXP_GRADE", "GOT_GRADE", "EXP_TERM",
                                   "GOT_TERM", "IN_RESULTS", "RULE_IDS", "CONVENTIONS", "DESCRIPTION")]
  rownames(mismatch) <- NULL
  rl <- strsplit(record$RULE_IDS, " ", fixed = TRUE)
  rr <- data.frame(RULE_ID = unlist(rl), OK = rep(record$OK, lengths(rl)), stringsAsFactors = FALSE)
  rr <- rr[startsWith(rr$RULE_ID, paste0("V", version)), ]
  crit <- unique(data$criteria[data$criteria$VERSION == version & data$criteria$LAB_DERIVABLE == "Y", c("RULE_ID", "CTCAE_TERM", "GRADE")])
  crit <- crit[order(crit$RULE_ID), ]
  n_by <- tapply(rr$OK, rr$RULE_ID, length); bad_by <- tapply(!rr$OK, rr$RULE_ID, sum)
  rules <- data.frame(crit, RECORDS = ifelse(is.na(n_by[crit$RULE_ID]), 0L, as.integer(n_by[crit$RULE_ID])),
                      MISMATCHES = ifelse(is.na(bad_by[crit$RULE_ID]), 0L, as.integer(bad_by[crit$RULE_ID])), stringsAsFactors = FALSE)
  rules$STATUS <- ifelse(rules$RECORDS == 0, "NONE", ifelse(rules$MISMATCHES == 0, "PASS", "FAIL"))
  rownames(rules) <- NULL

  out <- list(status = if (all(record$OK)) "PASS" else "FAIL", version = version, profile = profile,
              records = nrow(record), mismatches = sum(!record$OK), absent = sum(!record$IN_RESULTS),
              module = module, mismatch = mismatch, rules = rules, detail = detail, record = record)
  if (print) {
    cat(sprintf("ctcval_compare - CTCAE v%d profile %s - status by module\n", version, profile))
    print(module, row.names = FALSE)
    if (nrow(mismatch)) {
      cat(sprintf("\n%d mismatching record(s), first %d direction rows:\n", out$mismatches, min(20L, nrow(mismatch))))
      print(utils::head(mismatch[, c("SCENARIO_ID", "DIRECTION", "EXP_GRADE", "GOT_GRADE", "EXP_TERM", "GOT_TERM", "RULE_IDS")], 20), row.names = FALSE)
    }
    nr <- rules[rules$STATUS != "PASS", ]
    if (nrow(nr)) {
      cat(sprintf("\n%d criteria rule(s) with a mismatch or without a compared record:\n", nrow(nr)))
      print(nr, row.names = FALSE)
    }
    cat(sprintf("\n%s: %d of %d records agree with CTCAE v%d profile %s (%d absent from results)\n",
                out$status, nrow(record) - out$mismatches, nrow(record), version, profile, out$absent))
    invisible(out)
  } else out
}

# load_records.R - reads the ctcae-lab-validation tables into data frames (base R, no packages needed)
#
#   source("reference/r/load_records.R")
#   d <- ctcval_load("path/to/ctcae-lab-validation", naming = "neutral")
#
# Returns a list: records (one row per laboratory record, DATE and REF_DATE as Date), expectations (long:
# record x version x profile x direction), criteria (machine-readable CTCAE criteria), conventions, dir.
# naming = "adam" renames the input columns of records to ADaM names (USUBJID PARAMCD PARAM AVAL AVALU ANRLO
# ANRHI ADT ADY TRTSDT ABLFL BASE BNRLO BNRHI); naming = "sdtm" to SDTM names (USUBJID LBSTRESN LBSTRESU LBSTNRLO
# LBSTNRHI LBDTC LBDY RFSTDTC LBBLFL LBSTAT, the dates as ISO 8601 character). Expectation columns keep their names.

ctcval_record_classes <- c(
  RECORD_ID = "integer", SUBJECT_ID = "character", SCENARIO_ID = "character", MODULE = "character", RULE_IDS = "character",
  LBTESTCD = "character", LBTEST = "character", LBSPEC = "character", LBDUR = "character",
  VAL = "numeric", UNIT = "character", LLN = "numeric", ULN = "numeric",
  VAL_SI = "numeric", UNIT_SI = "character", LLN_SI = "numeric", ULN_SI = "numeric",
  VAL_CONV = "numeric", UNIT_CONV = "character", LLN_CONV = "numeric", ULN_CONV = "numeric",
  DATE = "Date", STUDY_DAY = "integer", REF_DATE = "Date", BASELINE_FLAG = "character",
  BASE_VAL = "numeric", BASE_UNIT = "character", BASE_LLN = "numeric", BASE_ULN = "numeric",
  BASE_VAL_SI = "numeric", BASE_LLN_SI = "numeric", BASE_ULN_SI = "numeric",
  BASE_VAL_CONV = "numeric", BASE_LLN_CONV = "numeric", BASE_ULN_CONV = "numeric",
  STATUS = "character", GRADABLE = "character",
  EXP_GRADE_LOW_V5 = "integer", EXP_GRADE_HIGH_V5 = "integer", EXP_TERM_LOW_V5 = "character", EXP_TERM_HIGH_V5 = "character",
  EXP_BASE_GRADE_LOW_V5 = "integer", EXP_BASE_GRADE_HIGH_V5 = "integer", EXP_GRADE_V5 = "integer", EXP_TERM_V5 = "character",
  EXP_GRADE_LOW_V6 = "integer", EXP_GRADE_HIGH_V6 = "integer", EXP_TERM_LOW_V6 = "character", EXP_TERM_HIGH_V6 = "character",
  EXP_BASE_GRADE_LOW_V6 = "integer", EXP_BASE_GRADE_HIGH_V6 = "integer", EXP_GRADE_V6 = "integer", EXP_TERM_V6 = "character",
  VERSION_DELTA = "character", CONVENTIONS = "character", CONVENTION_DEP = "character", DESCRIPTION = "character"
)
ctcval_expectation_classes <- c(RECORD_ID = "integer", VERSION = "integer", PROFILE = "character", DIRECTION = "character",
                                GRADE = "integer", TERM = "character", BASE_GRADE = "integer")
ctcval_criteria_classes <- c(
  RULE_ID = "character", CLAUSE_SEQ = "integer", VERSION = "integer", LBTESTCD = "character", LBSPEC = "character",
  CTCAE_TERM = "character", SOC = "character", DIRECTION = "character", BASELINE_ARM = "character", GRADE = "integer",
  LAB_DERIVABLE = "character", WORDING = "character", CLAUSE = "character", COMPARATOR = "character", OPERAND = "character",
  THRESHOLD = "character", THRESHOLD_UNIT = "character", THRESHOLD_CONV = "character", THRESHOLD_CONV_UNIT = "character",
  CONDITION = "character", QUALIFIER = "character", CONVENTION = "character", SOURCE_DOC = "character",
  SOURCE_PAGE = "integer", NOTE = "character"
)

ctcval_adam_names <- c(SUBJECT_ID = "USUBJID", LBTESTCD = "PARAMCD", LBTEST = "PARAM", VAL = "AVAL", UNIT = "AVALU",
                       LLN = "ANRLO", ULN = "ANRHI", DATE = "ADT", STUDY_DAY = "ADY", REF_DATE = "TRTSDT",
                       BASELINE_FLAG = "ABLFL", BASE_VAL = "BASE", BASE_LLN = "BNRLO", BASE_ULN = "BNRHI")
ctcval_sdtm_names <- c(SUBJECT_ID = "USUBJID", VAL = "LBSTRESN", UNIT = "LBSTRESU", LLN = "LBSTNRLO", ULN = "LBSTNRHI",
                       DATE = "LBDTC", STUDY_DAY = "LBDY", REF_DATE = "RFSTDTC", BASELINE_FLAG = "LBBLFL", STATUS = "LBSTAT")

ctcval_read <- function(dir, name, classes) {
  path <- file.path(dir, "data", paste0(name, ".csv"))
  if (!file.exists(path)) stop("ctcval_load: ", path, " not found (dir must hold data/records.csv)")
  header <- names(utils::read.csv(path, nrows = 1, check.names = FALSE))
  if (!is.null(names(classes))) {
    missing_cols <- setdiff(header, names(classes))
    if (length(missing_cols)) stop("ctcval_load: ", name, ".csv has columns the loader does not know: ", paste(missing_cols, collapse = " "))
    classes <- classes[header]
  }
  utils::read.csv(path, colClasses = classes, na.strings = character(0), check.names = FALSE,
                  stringsAsFactors = FALSE, encoding = "UTF-8")
}

ctcval_load <- function(dir, naming = c("neutral", "adam", "sdtm")) {
  naming <- match.arg(naming)
  records <- ctcval_read(dir, "records", ctcval_record_classes)
  expectations <- ctcval_read(dir, "expectations", ctcval_expectation_classes)
  criteria <- ctcval_read(dir, "criteria", ctcval_criteria_classes)
  conventions <- ctcval_read(dir, "conventions", "character")
  if (naming == "adam") {
    names(records) <- ifelse(names(records) %in% names(ctcval_adam_names), ctcval_adam_names[names(records)], names(records))
  } else if (naming == "sdtm") {
    records$DATE <- format(records$DATE, "%Y-%m-%d")
    records$REF_DATE <- format(records$REF_DATE, "%Y-%m-%d")
    names(records) <- ifelse(names(records) %in% names(ctcval_sdtm_names), ctcval_sdtm_names[names(records)], names(records))
  }
  message("ctcval_load: ", nrow(records), " records, ", nrow(expectations), " expectation rows loaded from ", dir, " (naming = ", naming, ")")
  list(records = records, expectations = expectations, criteria = criteria, conventions = conventions, dir = dir)
}

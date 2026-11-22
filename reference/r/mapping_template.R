# mapping_template.R - where an adopter connects the dataset to a grading function (template, edit freely)
#
# The dataset is implementation-free: records carry CDISC LBTESTCD / LBSPEC codes, neutral or ADaM / SDTM column
# names (ctcval_load naming =), the result as received (VAL, UNIT, LLN, ULN) and the baseline both as a flagged record
# and as BASE_* columns. Four things usually need mapping:
#   1. your test codes      -> recode LBTESTCD (or PARAMCD) into the codes your function expects
#   2. your categories      -> derive a category from LBSPEC when your function joins on one
#   3. your column names    -> rename what ctcval_load does not already provide
#   4. your term names      -> after grading, map internal term text to the official CTCAE term text
# Then call ctcval_compare on the function's output.

ctcval_dir <- "path/to/ctcae-lab-validation"
source(file.path(ctcval_dir, "reference", "r", "load_records.R"))
source(file.path(ctcval_dir, "reference", "r", "compare_results.R"))
d <- ctcval_load(ctcval_dir, naming = "adam")
lab <- d$records

# 1. test codes: one entry per code that differs from the CDISC LBTESTCD (examples only)
my_codes <- c(CK = "MYCK", LIPASET = "MYLIP", GFRBSCRT = "MYEGFR")
lab$MYPARAMCD <- ifelse(lab$PARAMCD %in% names(my_codes), my_codes[lab$PARAMCD], lab$PARAMCD)

# 2. category from the specimen, when your function joins on one
lab$PARCAT1 <- c(URINE = "URINALYSIS", BLOOD = "HEMATOLOGY", SERUM = "CHEMISTRY", PLASMA = "CHEMISTRY")[lab$LBSPEC]

# 3. further renames or derivations your function expects go here

# run your grading function on lab here, once per CTCAE version, e.g.
#   graded_v5 <- my_grade(lab, version = 5, paramcd = "MYPARAMCD", aval = "AVAL", unit = "AVALU", lo = "ANRLO", hi = "ANRHI")

# 4. map internal term names to the official CTCAE term text when they differ (examples only), then compare
#   graded_v5$TERMHIGH <- ifelse(toupper(graded_v5$ATOXDSCH) == "CPK INCREASED", "CPK increased", graded_v5$ATOXDSCH)
#   ctcval_compare(graded_v5, version = 5, profile = "DEFAULT",
#                  cols = list(id = "RECORD_ID", grade_low = "ATOXGRL", grade_high = "ATOXGRH", term_low = "ATOXDSCL", term_high = "TERMHIGH"),
#                  data = d)
#   single-scale designs: ctcval_compare(graded_v5, 5, cols = list(grade = "ATOXGR", term = "ATOXDSC"), data = d)

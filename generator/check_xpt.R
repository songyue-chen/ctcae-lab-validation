# check_xpt.R - reads records.xpt back with haven and checks every value against records.csv
#   Rscript generator/check_xpt.R <release folder>
suppressMessages(library(haven))
args <- commandArgs(trailingOnly = TRUE)
x <- read_xpt(file.path(args[1], "records.xpt"))
csv <- read.csv(file.path(args[1], "records.csv"), colClasses = "character", na.strings = character(0), check.names = FALSE)
cat("xpt rows", nrow(x), "cols", ncol(x), "| csv rows", nrow(csv), "cols", ncol(csv), "\n")
labels <- sapply(x, function(v) attr(v, "label"))
stopifnot(identical(unname(labels), names(csv)))
bad <- 0; exact <- TRUE
for (i in seq_along(csv)) {
  cn <- names(csv)[i]; xv <- x[[i]]; cv <- csv[[i]]
  if (cn %in% c("DATE", "REF_DATE")) {
    xd <- as.Date(xv); ok <- all(ifelse(cv == "", is.na(xd), !is.na(xd) & format(xd, "%Y-%m-%d") == cv))
  } else if (is.numeric(xv)) {
    cvn <- suppressWarnings(as.numeric(cv)); ok <- all(ifelse(cv == "", is.na(xv), !is.na(xv) & xv == cvn))
  } else {
    ok <- all(trimws(xv, "right") == cv)
  }
  if (!isTRUE(ok)) { bad <- bad + 1; cat("MISMATCH in", cn, "\n") }
}
cat("DATE class:", class(x$DATE), "| first DATE:", format(as.Date(x$DATE[1])), "| dataset label:", attr(x, "label"), "| names:", paste(head(names(x), 6), collapse = " "), "\n")
if (bad == 0) cat("XPT CHECK PASSED: every value of records.xpt equals records.csv exactly\n") else stop(bad, " columns differ")

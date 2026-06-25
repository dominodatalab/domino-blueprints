#' @keywords internal
NULL

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

#' Load a prompt template by name
#'
#' Looks for the template in two locations (in order):
#'   1. Runtime override: DOMINO_CLAUDERUS_PROMPTS_DIR env var, or
#'      {DOMINO_WORKING_DIR}/clauderus-prompts/
#'   2. Package inst/prompts/ (baked into Compute Environment image)
#'
#' This two-level resolution means prompt teams can iterate without
#' triggering a full CE rebuild — drop an overriding .md file into the
#' project folder and changes take effect on the next addin run.
#'
#' @param name Template filename without .md extension
#' @param vars Named list of {{variable}} substitutions
#' @return Character string with variables substituted
.load_prompt <- function(name, vars = list()) {
  override_dir <- Sys.getenv("DOMINO_CLAUDERUS_PROMPTS_DIR", unset = "")
  if (nchar(override_dir) == 0) {
    domino_dir <- Sys.getenv("DOMINO_WORKING_DIR", unset = "")
    if (nchar(domino_dir) > 0) {
      override_dir <- file.path(domino_dir, "clauderus-prompts")
    }
  }

  prompt_file <- NULL
  if (nchar(override_dir) > 0) {
    candidate <- file.path(override_dir, paste0(name, ".md"))
    if (file.exists(candidate)) {
      prompt_file <- candidate
      message("[dominoClaudeRus] Using runtime prompt override: ", candidate)
    }
  }

  if (is.null(prompt_file)) {
    prompt_file <- system.file("prompts", paste0(name, ".md"),
                               package = "dominoClaudeRus")
    if (!nchar(prompt_file)) {
      stop("Prompt template not found: ", name,
           "\nExpected at: inst/prompts/", name, ".md")
    }
  }

  tmpl <- paste(readLines(prompt_file, warn = FALSE), collapse = "\n")
  for (key in names(vars)) {
    tmpl <- gsub(paste0("{{", key, "}}"), vars[[key]], tmpl, fixed = TRUE)
  }
  tmpl
}

# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

prompt_check_logs <- function(content) {
  .load_prompt("check_logs", list(content = content))
}

prompt_inspect_data <- function(summary_text) {
  .load_prompt("inspect_data", list(summary = summary_text))
}

prompt_fix_warning_message <- function(content) {
  .load_prompt("fix_warnings_message", list(content = content))
}

prompt_fix_warning_code <- function(content) {
  .load_prompt("fix_warnings_code", list(content = content))
}

prompt_review_sap <- function(content) {
  .load_prompt("review_sap", list(content = content))
}

prompt_generate_job_config <- function(content, script_name = "script.R") {
  if (nchar(content) > 8000) {
    content <- paste0(substr(content, 1, 8000), "\n[... truncated ...]")
  }
  .load_prompt("generate_job_config",
               list(content = content, script_name = script_name))
}

# ---------------------------------------------------------------------------
# Data summary builder — COMPLIANCE SAFE
#
# Sends only structural metadata to Claude:
#   - Column names, types, NA counts
#   - Numeric: min/max/mean/sd only
#   - Character/factor: unique value COUNT only — no actual values
#   - Date ranges: count only, actual dates redacted
#   - No sample rows, no actual patient data
#
# Nothing in this output contains PII or clinical subject data.
# ---------------------------------------------------------------------------

#' Build a compliance-safe structural summary of a data frame
#' @param obj A data frame
#' @param obj_name Character string name of the object
#' @return Character string summary safe to send to Claude
.build_data_summary <- function(obj, obj_name) {
  n_rows <- nrow(obj)
  n_cols <- ncol(obj)

  col_summary <- vapply(seq_len(n_cols), function(i) {
    col   <- obj[[i]]
    cname <- names(obj)[i]
    ctype <- class(col)[1]
    n_na  <- sum(is.na(col))
    pct_na <- round(100 * n_na / max(n_rows, 1), 1)

    if (is.numeric(col)) {
      vals <- col[!is.na(col)]
      if (length(vals) == 0) {
        details <- "all NA"
      } else {
        details <- sprintf("min=%.4g  max=%.4g  mean=%.4g  sd=%.4g",
                           min(vals), max(vals), mean(vals), sd(vals))
      }
    } else if (inherits(col, "Date") || inherits(col, "POSIXct")) {
      vals  <- col[!is.na(col)]
      uvals <- length(unique(vals))
      if (length(vals) == 0) {
        details <- "all NA"
      } else {
        # Count only — actual dates could identify subjects
        details <- sprintf("%d unique dates (range redacted for compliance)", uvals)
      }
    } else {
      # Character / factor — count only, no sample values
      uvals <- length(unique(col[!is.na(col)]))
      details <- sprintf("%d unique values", uvals)
    }

    sprintf("%-28s | %-12s | NA:%d(%.1f%%) | %s",
            cname, ctype, n_na, pct_na, details)
  }, character(1))

  paste0(
    "Dataset: ", obj_name,
    "  [", n_rows, " rows x ", n_cols, " cols]",
    "  Duplicate rows: ", sum(duplicated(obj)), "\n\n",
    "NOTE: This summary contains structural metadata only. ",
    "No patient data or actual cell values have been included.\n\n",
    "Columns:\n", paste(col_summary, collapse = "\n")
  )
}

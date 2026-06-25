#' Check R Logs with Claude
#'
#' RStudio Addin. Sends selected R log text to Claude for clinical-aware
#' analysis. Select log output in the editor before running.
#' @export
addin_check_logs <- function() {
  if (!.check_claude()) return(invisible(NULL))

  content <- .get_editor_content(prefer_selection = TRUE)

  if (nchar(trimws(content)) == 0) {
    rstudioapi::showDialog("Claude: Check R Logs",
      "No text selected.\nSelect R log output in the editor, then run this addin.")
    return(invisible(NULL))
  }

  message("[dominoClaudeRus] Analysing R logs...")
  .show_result(
    .run_claude(prompt_check_logs(content)),
    title = "Claude: R Log Analysis"
  )
}


#' Inspect Data with Claude
#'
#' RStudio Addin. Analyses a named data frame for clinical data quality issues.
#' Sends only structural metadata — no patient data or actual cell values leave
#' the workspace.
#' Select a variable name in the editor or type it when prompted.
#' @export
addin_inspect_data <- function() {
  if (!.check_claude()) return(invisible(NULL))

  sel <- trimws(.get_editor_content(prefer_selection = TRUE))

  if (nchar(sel) == 0 || grepl("\n", sel) || nchar(sel) > 100) {
    obj_name <- rstudioapi::showPrompt(
      "Claude: Inspect Data",
      "Enter the name of the data frame to inspect:", "")
    if (is.null(obj_name) || nchar(trimws(obj_name)) == 0) return(invisible(NULL))
    obj_name <- trimws(obj_name)
  } else {
    obj_name <- sel
  }

  obj <- tryCatch(get(obj_name, envir = globalenv()), error = function(e) NULL)

  if (is.null(obj) || !is.data.frame(obj)) {
    rstudioapi::showDialog("Claude: Inspect Data",
      paste0("'", obj_name, "' not found or is not a data frame ",
             "in the global environment."))
    return(invisible(NULL))
  }

  message("[dominoClaudeRus] Building compliance-safe data summary for: ", obj_name)
  summary_text <- .build_data_summary(obj, obj_name)

  message("[dominoClaudeRus] Sending structural metadata to Claude...")
  .show_result(
    .run_claude(prompt_inspect_data(summary_text)),
    title = paste0("Claude: Data Inspection — ", obj_name)
  )
}


#' Fix R Warnings with Claude
#'
#' RStudio Addin. Select a warning message for an explanation and fix,
#' or select R code to have it corrected in-place.
#' @export
addin_fix_warnings <- function() {
  if (!.check_claude()) return(invisible(NULL))

  content <- .get_editor_content(prefer_selection = TRUE)

  if (nchar(trimws(content)) == 0) {
    rstudioapi::showDialog("Claude: Fix R Warnings",
      paste0("No text selected.\n",
             "Select a warning message for an explanation, or\n",
             "select R code to have it corrected in-place."))
    return(invisible(NULL))
  }

  is_msg <- grepl("^Warning|^Error|simpleWarning|simpleError",
                  trimws(content))

  if (is_msg) {
    message("[dominoClaudeRus] Explaining warning/error...")
    .show_result(
      .run_claude(prompt_fix_warning_message(content)),
      title = "Claude: Warning Fix"
    )
  } else {
    message("[dominoClaudeRus] Generating code fix...")
    .show_result(
      .run_claude(prompt_fix_warning_code(content)),
      title   = "Claude: Fixed Code",
      insert_into_editor = TRUE
    )
  }
}


#' Review SAP Section with Claude
#'
#' RStudio Addin. Sends selected SAP text to Claude for review against
#' ICH E9 and CDISC ADaM clinical programming standards.
#' @export
addin_review_sap <- function() {
  if (!.check_claude()) return(invisible(NULL))

  content <- .get_editor_content(prefer_selection = TRUE)

  if (nchar(trimws(content)) == 0) {
    rstudioapi::showDialog("Claude: Review SAP Section",
      "No text selected.\nSelect the SAP section to review, then run this addin.")
    return(invisible(NULL))
  }

  message("[dominoClaudeRus] Reviewing SAP section...")
  .show_result(
    .run_claude(prompt_review_sap(content)),
    title = "Claude: SAP Review"
  )
}


#' Generate Domino Job Config with Claude
#'
#' RStudio Addin. Analyses the current R script and generates a recommended
#' Domino job configuration. No selection needed — uses the full active document.
#' @export
addin_generate_job_config <- function() {
  if (!.check_claude()) return(invisible(NULL))

  content <- .get_editor_content(prefer_selection = FALSE)

  if (nchar(trimws(content)) == 0) {
    rstudioapi::showDialog("Claude: Generate Job Config",
      "No active R script. Open a script and try again.")
    return(invisible(NULL))
  }

  ctx <- tryCatch(rstudioapi::getActiveDocumentContext(), error = function(e) NULL)
  script_name <- if (!is.null(ctx) && nchar(ctx$path) > 0)
    basename(ctx$path) else "script.R"

  message("[dominoClaudeRus] Generating Domino job configuration for: ", script_name)
  .show_result(
    .run_claude(prompt_generate_job_config(content, script_name)),
    title = paste0("Claude: Job Config — ", script_name)
  )
}

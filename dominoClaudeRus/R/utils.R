#' @keywords internal
NULL

# ---------------------------------------------------------------------------
# Claude CLI detection
# ---------------------------------------------------------------------------

#' Find the claude CLI binary
#' Checks ~/.local/bin/claude first (Claude Code installer default),
#' then falls back to PATH.
#' @return Character path to claude binary, or NULL if not found
.claude_bin <- function() {
  candidates <- c(
    file.path(Sys.getenv("HOME"), ".local", "bin", "claude"),
    Sys.which("claude")
  )
  for (p in candidates) {
    if (nchar(p) > 0 && file.exists(p)) return(p)
  }
  NULL
}

# ---------------------------------------------------------------------------
# LLM provider detection
# ---------------------------------------------------------------------------

#' Detect which LLM backend Claude Code CLI will use
#'
#' Checks environment variables in priority order:
#'   1. Amazon Bedrock  (CLAUDE_CODE_USE_BEDROCK=1)
#'   2. Domino AI Gateway / custom endpoint  (ANTHROPIC_BASE_URL set)
#'   3. Direct Anthropic API  (default)
#'
#' No API call is made — this is purely an env-var inspection.
#'
#' @return Named list: provider (character), detail (character)
.detect_provider <- function() {
  if (identical(Sys.getenv("CLAUDE_CODE_USE_BEDROCK"), "1")) {
    region <- Sys.getenv("AWS_REGION", unset = Sys.getenv("AWS_DEFAULT_REGION", unset = "us-east-1"))
    model  <- Sys.getenv("ANTHROPIC_MODEL",
                         unset = Sys.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", unset = "(default)"))
    return(list(
      provider = "Amazon Bedrock",
      detail   = sprintf("region=%s  model=%s", region, model)
    ))
  }

  base_url <- Sys.getenv("ANTHROPIC_BASE_URL", unset = "")
  if (nchar(base_url) > 0) {
    return(list(
      provider = "Custom endpoint (Domino AI Gateway or self-hosted LLM)",
      detail   = base_url
    ))
  }

  list(
    provider = "Anthropic API (direct)",
    detail   = "Set CLAUDE_CODE_USE_BEDROCK=1 or ANTHROPIC_BASE_URL to use a different provider"
  )
}

#' Check claude is available; show a friendly dialog if not.
#' Also logs the active LLM provider to the console.
#' @return Invisible TRUE/FALSE
.check_claude <- function() {
  bin <- .claude_bin()
  if (is.null(bin)) {
    msg <- paste0(
      "Claude Code CLI not found.\n",
      "Expected at: ~/.local/bin/claude\n",
      "Try opening a terminal and running: claude --version\n\n",
      "See the dominoClaudeRus blueprint for installation instructions:\n",
      "https://github.com/dominodatalab/domino-blueprints/tree/main/dominoClaudeRus"
    )
    if (rstudioapi::isAvailable()) rstudioapi::showDialog("Claude Not Found", msg)
    else message(msg)
    return(invisible(FALSE))
  }

  # Log the active provider so it's visible in the console on every addin run
  p <- .detect_provider()
  message("[dominoClaudeRus] LLM provider: ", p$provider)
  message("[dominoClaudeRus]               ", p$detail)

  invisible(TRUE)
}

# ---------------------------------------------------------------------------
# Editor helpers
# ---------------------------------------------------------------------------

#' Get selected text from editor, or full document if nothing selected
#' @param prefer_selection If TRUE, return selection before full document
#' @return Character string
.get_editor_content <- function(prefer_selection = TRUE) {
  if (!rstudioapi::isAvailable()) return("")
  ctx <- rstudioapi::getActiveDocumentContext()
  sel <- ctx$selection[[1]]$text
  if (prefer_selection && nchar(trimws(sel)) > 0) return(sel)
  paste(ctx$contents, collapse = "\n")
}

# ---------------------------------------------------------------------------
# Claude invocation
# ---------------------------------------------------------------------------

#' Run claude CLI with a prompt, return response as character string
#' @param prompt Character string — the full prompt to send
#' @param timeout Seconds before giving up (default 120)
#' @return Character string response, or NULL on error
.run_claude <- function(prompt, timeout = 120) {
  bin <- .claude_bin()
  if (is.null(bin)) return(NULL)

  tmp_in  <- tempfile(fileext = ".txt")
  tmp_out <- tempfile(fileext = ".txt")
  on.exit({ unlink(tmp_in); unlink(tmp_out) }, add = TRUE)

  writeLines(prompt, tmp_in)

  exit_code <- system2(
    command = bin,
    args    = c("--print"),
    stdin   = tmp_in,
    stdout  = tmp_out,
    stderr  = tmp_out,
    timeout = timeout
  )

  if (!file.exists(tmp_out)) {
    message("[dominoClaudeRus] No output produced (exit code: ", exit_code, ")")
    return(NULL)
  }

  result <- trimws(paste(readLines(tmp_out, warn = FALSE), collapse = "\n"))

  if (nchar(result) == 0) {
    message("[dominoClaudeRus] Empty response (exit code: ", exit_code, ")")
    return(NULL)
  }

  result
}

# ---------------------------------------------------------------------------
# Result display
# ---------------------------------------------------------------------------

#' Render Claude response as HTML and show in RStudio Viewer pane.
#' Always echoes to console as fallback.
#' @param text Character string — Claude's response
#' @param title String shown as the page heading
.show_in_viewer <- function(text, title = "Claude Response") {
  # Always echo to console — output is never lost even if Viewer fails
  message("\n", paste(rep("=", 60), collapse = ""))
  message("[dominoClaudeRus] ", title)
  message(paste(rep("=", 60), collapse = ""))
  message(text)
  message(paste(rep("=", 60), collapse = ""))

  # Build HTML with simple markdown-style rendering
  html_text <- gsub("&", "&amp;", text)
  html_text <- gsub("<", "&lt;",  html_text)
  html_text <- gsub(">", "&gt;",  html_text)
  lines     <- strsplit(html_text, "\n")[[1]]
  in_block  <- FALSE
  out_lines <- character(length(lines))

  for (i in seq_along(lines)) {
    l <- lines[i]
    if (grepl("^```", l)) {
      if (!in_block) { out_lines[i] <- "<pre><code>"; in_block <- TRUE  }
      else           { out_lines[i] <- "</code></pre>"; in_block <- FALSE }
    } else if (in_block) {
      out_lines[i] <- paste0(l, "\n")
    } else if (grepl("^#{1,3} ", l)) {
      lvl <- nchar(regmatches(l, regexpr("^#{1,3}", l)))
      out_lines[i] <- paste0("<h", lvl + 2, ">",
                             sub("^#{1,3} ", "", l),
                             "</h", lvl + 2, ">")
    } else if (grepl("^\\*\\*|^\\d+\\. |^- |^\\* ", l)) {
      out_lines[i] <- paste0("<p class='item'>", l, "</p>")
    } else {
      out_lines[i] <- paste0("<p>", l, "</p>")
    }
  }

  html <- paste0(
    '<!DOCTYPE html><html><head><meta charset="UTF-8"><style>',
    'body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;',
    'font-size:13px;line-height:1.6;padding:16px 20px;color:#2d2d2d;max-width:900px}',
    'h2{color:#1a6b3c;border-bottom:2px solid #f0f0f0;padding-bottom:8px;margin-top:0}',
    'h3,h4,h5{color:#444;margin-top:16px}',
    'pre{background:#f5f5f5;border:1px solid #ddd;border-radius:4px;',
    'padding:12px;overflow-x:auto;font-size:12px;font-family:monospace}',
    'p{margin:3px 0}',
    'p.item{margin-left:12px}',
    '.badge{display:inline-block;background:#1a6b3c;color:white;',
    'border-radius:3px;padding:2px 10px;font-size:11px;',
    'margin-bottom:14px;font-weight:600;letter-spacing:0.3px}',
    '</style></head><body>',
    '<div class="badge">dominoClaudeRus</div>',
    '<h2>', title, '</h2>',
    paste(out_lines, collapse = "\n"),
    '</body></html>'
  )

  tmp <- tempfile(fileext = ".html")
  writeLines(html, tmp)

  # Bare path required — RStudio Server behind Domino proxy mangles file:// URIs
  tryCatch(
    rstudioapi::viewer(tmp),
    error = function(e) message("[dominoClaudeRus] Viewer unavailable — see console output above.")
  )

  invisible(tmp)
}

#' Show Claude result — in Viewer pane or inserted into editor
#' @param result Character string from .run_claude()
#' @param title Viewer pane heading
#' @param insert_into_editor If TRUE, replace selected text in editor
.show_result <- function(result, title = "Claude Response",
                         insert_into_editor = FALSE) {
  if (is.null(result) || nchar(result) == 0) {
    rstudioapi::showDialog(title, "No response received from Claude.")
    return(invisible(NULL))
  }
  if (insert_into_editor && rstudioapi::isAvailable()) {
    ctx <- rstudioapi::getActiveDocumentContext()
    rstudioapi::insertText(
      location = ctx$selection[[1]]$range,
      text     = result,
      id       = ctx$id
    )
  } else {
    .show_in_viewer(result, title)
  }
  invisible(result)
}

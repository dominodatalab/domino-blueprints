# =============================================================================
# dominoClaudeRus — Addin Test Script
#
# Purpose:  Provides ready-to-use test content for manually verifying each
#           of the five RStudio addins after installing dominoClaudeRus in a
#           Domino Compute Environment.
#
# Usage:    Open this file in RStudio, follow the instructions for each
#           section, and run the corresponding addin from the Addins menu.
#           Expected output is described for each test.
#
# Requirements:
#   - dominoClaudeRus installed in the active Compute Environment
#   - Claude Code CLI authenticated (~/.local/bin/claude)
#   - RStudio Server workspace on Domino
# =============================================================================


# =============================================================================
# ADDIN 1: Claude: Check R Logs
#
# How to test:
#   1. Select ALL the text between the dashes below (the log block)
#   2. Addins menu → "Claude: Check R Logs"
#
# Expected output in Viewer pane:
#   - Identifies the merge key suffix issue (TRTSDT.x / TRTSDT.y)
#   - Flags the NA coercion as a potential data quality risk
#   - Suggests specific fixes for each issue
# =============================================================================

# ---- SELECT FROM HERE --------------------------------------------------------
# Warning message:
# In merge(adsl, adlb, by = "USUBJID") :
#   column names 'TRTSDT.x', 'TRTSDT.y' introduced due to common name conflict
#
# Warning message:
# In as.numeric(adlb$AVAL) : NAs introduced by coercion
#
# Error in dplyr::left_join(adsl, ex, by = c("USUBJID", "STUDYID")) :
#   Join columns must be present in data.
#   x Problem with `STUDYID`: column not found.
#   i Did you mean: `STUDY`?
# ---- SELECT TO HERE ----------------------------------------------------------


# =============================================================================
# ADDIN 2: Claude: Inspect Data
#
# How to test:
#   1. Run the block below to create a synthetic test data frame (no real data)
#   2. Select the variable name:  adsl_test
#   3. Addins menu → "Claude: Inspect Data"
#
# Expected output in Viewer pane:
#   - CDISC naming convention review (flags non-standard column names)
#   - NA pattern analysis (AGE has 10% missing, flags RACE all-NA)
#   - Type mismatch warning (TRTSDT stored as character, not Date)
#   - Recommendations before running analysis pipeline
#
# Note: only structural metadata is sent to Claude — no actual values.
# =============================================================================

set.seed(42)
n <- 200

adsl_test <- data.frame(
  USUBJID  = sprintf("SUBJ-%03d", seq_len(n)),          # subject ID
  STUDYID  = "STUDY-001",                                # study ID
  AGE      = c(sample(40:75, n - 20, replace = TRUE),
               rep(NA_integer_, 20)),                    # 10% missing
  SEX      = sample(c("M", "F"), n, replace = TRUE),
  RACE     = rep(NA_character_, n),                      # all NA — flaggable
  ARM      = sample(c("TREATMENT", "PLACEBO"), n,
                    replace = TRUE),
  TRTSDT   = sample(                                     # stored as character
               format(seq(as.Date("2023-01-01"),
                          as.Date("2024-06-01"), by="day"),
                      "%d%b%Y"),
               n, replace = TRUE),
  AVAL     = round(rnorm(n, mean = 5.2, sd = 1.1), 2),  # numeric result
  nonStdNm = seq_len(n),                                 # non-CDISC name
  stringsAsFactors = FALSE
)

# After running: select  adsl_test  above and run Claude: Inspect Data


# =============================================================================
# ADDIN 3: Claude: Fix R Warnings  (mode A — warning message)
#
# How to test:
#   1. Select the warning text between the dashes below
#   2. Addins menu → "Claude: Fix R Warnings"
#
# Expected output in Viewer pane:
#   - Root cause explanation (factor level dropped on subset)
#   - Exact code fix with inline comments
#   - Note on whether this could affect downstream analysis results
# =============================================================================

# ---- SELECT FROM HERE --------------------------------------------------------
# Warning message:
# In `[.factor`(adsl$ARM, adsl$AGE > 65) :
#   invalid factor level, NA generated
# ---- SELECT TO HERE ----------------------------------------------------------


# =============================================================================
# ADDIN 3: Claude: Fix R Warnings  (mode B — code correction)
#
# How to test:
#   1. Select the R code block between the dashes below
#   2. Addins menu → "Claude: Fix R Warnings"
#
# Expected output:
#   - Corrected code inserted back into the editor in-place
#   - Common issues flagged: as.numeric on factor without unlevel,
#     subset dropping unused levels, format mismatch on date merge
# =============================================================================

# ---- SELECT FROM HERE --------------------------------------------------------
adsl_sub <- adsl_test[adsl_test$ARM == "TREATMENT", ]
adsl_sub$TRTSDT_num <- as.numeric(adsl_sub$TRTSDT)
adsl_sub$AGE_grp <- ifelse(adsl_sub$AGE > 65, "Elderly", "Non-elderly")
merged <- merge(adsl_sub, adsl_test, by = "USUBJID")
# ---- SELECT TO HERE ----------------------------------------------------------


# =============================================================================
# ADDIN 4: Claude: Review SAP Section
#
# How to test:
#   1. Select ALL the text between the dashes below (the SAP excerpt)
#   2. Addins menu → "Claude: Review SAP Section"
#
# Expected output in Viewer pane:
#   - Flags missing visit window specification
#   - Questions about missing data handling (LOCF/BOCF/MI not specified)
#   - Notes ambiguity in population definition (screen failures unclear)
#   - Flags missing flagging variable specification (ANL01FL)
#   - Clarifying questions to raise with the statistician
# =============================================================================

# ---- SELECT FROM HERE --------------------------------------------------------
# 3.2 Primary Efficacy Analysis
#
# The primary efficacy endpoint is the change from baseline in AVAL at
# Week 24. The analysis will be performed using a mixed model for repeated
# measures (MMRM) with treatment arm, visit, and baseline value as
# covariates. The full analysis set (FAS) will be used, which includes all
# randomised subjects who received at least one dose of study medication and
# have at least one post-baseline assessment.
#
# Subjects with missing data at Week 24 will be handled using the model-based
# approach. Sensitivity analyses will be conducted as described in Section 5.
# The significance level is set at alpha = 0.05 (two-sided).
# ---- SELECT TO HERE ----------------------------------------------------------


# =============================================================================
# ADDIN 5: Claude: Generate Job Config
#
# How to test:
#   This addin uses the FULL active script — no selection needed.
#   1. Make sure THIS file is the active document in RStudio
#   2. Addins menu → "Claude: Generate Job Config"
#
# Expected output in Viewer pane:
#   - Recommended Domino job command
#   - Hardware tier suggestion with reasoning (script is light — small tier)
#   - Environment variables to set
#   - Package dependencies identified (dplyr not loaded but used in log test)
#   - Parallelisation opportunities (none in this script)
#   - Expected output files (none explicitly — will flag this)
# =============================================================================

message("dominoClaudeRus test script loaded. Follow instructions above each section.")

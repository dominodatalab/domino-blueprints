test_that("prompt_check_logs inserts content", {
  result <- prompt_check_logs("Error in foo(): object not found")
  expect_true(grepl("Error in foo()", result, fixed = TRUE))
  expect_true(grepl("R LOG", result))
})

test_that("prompt_inspect_data inserts summary", {
  result <- prompt_inspect_data("Dataset: adsl [100 rows x 5 cols]")
  expect_true(grepl("100 rows", result, fixed = TRUE))
})

test_that("prompt_fix_warning_message inserts content", {
  result <- prompt_fix_warning_message("Warning: NAs introduced by coercion")
  expect_true(grepl("NAs introduced by coercion", result, fixed = TRUE))
})

test_that("prompt_fix_warning_code inserts content", {
  result <- prompt_fix_warning_code("x <- as.integer('abc')")
  expect_true(grepl("as.integer", result, fixed = TRUE))
})

test_that("prompt_review_sap inserts content", {
  result <- prompt_review_sap("Population: all randomised subjects")
  expect_true(grepl("all randomised subjects", result, fixed = TRUE))
})

test_that("prompt_generate_job_config inserts script name and content", {
  result <- prompt_generate_job_config("library(dplyr)\n# analysis", "derive_adsl.R")
  expect_true(grepl("derive_adsl.R", result, fixed = TRUE))
  expect_true(grepl("library(dplyr)", result, fixed = TRUE))
})

test_that("prompt_generate_job_config truncates at 8000 chars", {
  long_content <- paste(rep("x", 9000), collapse = "")
  result <- prompt_generate_job_config(long_content, "big.R")
  expect_true(grepl("truncated", result, fixed = TRUE))
})

test_that("runtime override takes precedence over baked-in prompt", {
  withr::with_tempdir({
    dir.create("clauderus-prompts")
    writeLines("Custom prompt: {{content}}", "clauderus-prompts/check_logs.md")
    withr::with_envvar(
      c(DOMINO_WORKING_DIR = getwd()),
      {
        result <- prompt_check_logs("test log")
        expect_true(grepl("Custom prompt", result, fixed = TRUE))
        expect_true(grepl("test log", result, fixed = TRUE))
      }
    )
  })
})

test_that("DOMINO_CLAUDERUS_PROMPTS_DIR env var overrides prompt dir", {
  withr::with_tempdir({
    writeLines("Env override: {{content}}", "check_logs.md")
    withr::with_envvar(
      c(DOMINO_CLAUDERUS_PROMPTS_DIR = getwd()),
      {
        result <- prompt_check_logs("env test")
        expect_true(grepl("Env override", result, fixed = TRUE))
      }
    )
  })
})

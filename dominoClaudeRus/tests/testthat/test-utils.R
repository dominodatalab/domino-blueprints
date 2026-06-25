test_that(".build_data_summary returns expected structure", {
  df <- data.frame(
    USUBJID = c("001", "002", "003"),
    AGE     = c(45L, 60L, 52L),
    SEX     = c("M", "F", "M"),
    TRTSDT  = as.Date(c("2024-01-01", "2024-01-15", "2024-02-01")),
    stringsAsFactors = FALSE
  )
  result <- dominoClaudeRus:::.build_data_summary(df, "adsl")

  expect_true(grepl("adsl", result))
  expect_true(grepl("3 rows x 4 cols", result))
  expect_true(grepl("USUBJID", result))
  expect_true(grepl("AGE", result))
  expect_true(grepl("unique values", result))      # character columns: count only
  expect_true(grepl("unique dates", result))        # date columns: count only
  expect_false(grepl("001", result))                # no actual USUBJID values
  expect_false(grepl("2024-01-01", result))         # no actual dates
  expect_true(grepl("compliance", result))          # compliance note present
})

test_that(".build_data_summary handles all-NA numeric column", {
  df <- data.frame(x = NA_real_, y = 1L)
  result <- dominoClaudeRus:::.build_data_summary(df, "test_df")
  expect_true(grepl("all NA", result))
})

test_that(".build_data_summary counts duplicate rows", {
  df <- data.frame(a = c(1, 1, 2), b = c("x", "x", "y"))
  result <- dominoClaudeRus:::.build_data_summary(df, "dup_df")
  expect_true(grepl("Duplicate rows: 1", result))
})

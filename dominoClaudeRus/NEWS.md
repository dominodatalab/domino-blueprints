# dominoClaudeRus News

## 0.1.0 (2026-06-24)

### Initial release
* Five RStudio addins for clinical programming workflows on Domino:
  - Claude: Check R Logs
  - Claude: Inspect Data
  - Claude: Fix R Warnings
  - Claude: Review SAP Section
  - Claude: Generate Job Config
* Prompt templates externalised to `inst/prompts/*.md` — iterate without
  a Compute Environment rebuild
* Runtime prompt override via `DOMINO_CLAUDERUS_PROMPTS_DIR` env var or
  a `clauderus-prompts/` folder in the Domino project root
* Compliance-safe data summary builder: sends structural metadata only,
  no patient data or actual cell values
* Results rendered in RStudio Viewer pane with console fallback

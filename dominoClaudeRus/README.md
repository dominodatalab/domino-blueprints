# dominoClaudeRus

> RStudio addins that surface Claude Code CLI as point-and-click AI assistance for clinical programmers working in Domino workspaces. CDISC-aware, compliance-safe, provider-agnostic.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

---

## ⚠️ This is a reference implementation

This repository is a **working example** published as part of the
[dominoClaudeRus Domino Blueprint](https://domino.ai/resources/blueprints/domino-clauderus).
It is intended to be **forked or copied** into your own organisation's GitHub,
adapted to your environment, and deployed from there.

**Do not install directly from this example repository in production.** Instead:

1. Fork or copy this code into your own GitHub repository
2. Review and customise the prompt templates in `inst/prompts/` for your organisation's standards
3. Create your own release tags (e.g. `v0.1.0`) in your repo
4. Reference your own repo in your Domino Compute Environment Dockerfile (see [Installation](#installation))

---

## Architecture

```
RStudio Addin (Addins menu or keyboard shortcut)
        │
        ▼
  dominoClaudeRus R package
  ├── reads selection / full document from RStudio editor
  ├── loads prompt template  ← inst/prompts/*.md
  │      └── override resolution (first match wins):
  │            1. DOMINO_CLAUDERUS_PROMPTS_DIR env var
  │            2. {DOMINO_WORKING_DIR}/clauderus-prompts/ folder
  │            3. baked-in package prompt (CE image)
  └── invokes Claude Code CLI  (claude --print, via stdin)
              │
              ▼
        Claude Code CLI  (~/.local/bin/claude)
              │
              ├── Anthropic API (direct, default)
              ├── Amazon Bedrock  (CLAUDE_CODE_USE_BEDROCK=1)
              └── Domino AI Gateway  (ANTHROPIC_BASE_URL=...)
              │
              ▼
        Response → RStudio Viewer pane (HTML) + console echo
```

---

## The five addins

| Addin | Select before running | Output |
|---|---|---|
| **Claude: Check R Logs** | R console / job log output | Viewer: categorised errors, root causes, fixes |
| **Claude: Inspect Data** | Data frame name (or type when prompted) | Viewer: CDISC ADaM/SDTM quality report — structural metadata only, no patient data |
| **Claude: Fix R Warnings** | Warning message → explanation + fix; R code → corrected code inserted in-place | Viewer or editor |
| **Claude: Review SAP Section** | SAP text | Viewer: ICH E9 / CDISC ADaM gaps, ambiguities, pre-coding questions |
| **Claude: Generate Job Config** | Nothing — uses full active script | Viewer: hardware tier, env vars, parallelisation recommendations |

---

## Getting started

### Step 1 — Fork or copy this repo

Create your own GitHub repository from this code. This gives you full control
over versioning, prompt customisation, and your release cadence.

```
# Option A — Fork on GitHub (recommended)
# Click "Fork" on this repo page, then clone your fork

# Option B — Copy into an existing repo as a subfolder
# Download the zip from the blueprint page and push to your repo
```

Your repo will be referenced as `YOUR_ORG/YOUR_REPO` in the steps below.

### Step 2 — Customise prompt templates

Review and edit the files in `inst/prompts/` before your first deployment.
These are plain Markdown files — no R knowledge required:

| File | Addin | What to customise |
|---|---|---|
| `check_logs.md` | Check R Logs | Add error patterns specific to your tech stack |
| `inspect_data.md` | Inspect Data | Add your organisation's CDISC naming conventions |
| `fix_warnings_message.md` | Fix R Warnings | Add regulatory context relevant to your submissions |
| `fix_warnings_code.md` | Fix R Warnings (code mode) | Add internal coding style guidance |
| `review_sap.md` | Review SAP Section | **Most important** — add your organisation's SAP standards and endpoint conventions |
| `generate_job_config.md` | Generate Job Config | Add your Domino hardware tier names and environment conventions |

The `{{content}}` and `{{summary}}` placeholders are where selected text is
injected at runtime — do not remove them.

### Step 3 — Create a release tag

Once you're happy with the prompts, create a release tag in your repo.
This is what pins your Compute Environment to a known-good version:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then create a GitHub Release from that tag so there's a changelog entry.

### Step 4 — Add to your Compute Environment Dockerfile Instructions

```dockerfile
USER root
RUN Rscript -e "install.packages('remotes', repos='https://cran.r-project.org', quiet=TRUE)" && \
    Rscript -e "remotes::install_github(
                  'YOUR_ORG/YOUR_REPO',
                  ref='v0.1.0',
                  quiet=TRUE)" && \
    echo "[OK] dominoClaudeRus installed"
USER domino
```

Replace `YOUR_ORG/YOUR_REPO` with your actual GitHub org and repo name.
Replace `v0.1.0` with your release tag.

> **Always pin to a release tag.** Never use `ref='main'` in a CE build —
> it makes images non-reproducible and complicates GxP audit trails.

### Step 5 — Rebuild the CE and verify

Rebuild the Compute Environment in Domino, then launch an RStudio workspace.
Open **Addins** menu → five `Claude:` entries should appear.

Quick smoke test — paste this into a script, select it, run **Claude: Check R Logs**:

```
Warning message:
In merge(adsl, adlb, by = "USUBJID") : column names 'TRTSDT.x', 'TRTSDT.y' introduced
```

You should see a Viewer pane open with Claude's triage within a few seconds.

---

## Installation

### Prerequisites

| Requirement | Notes |
|---|---|
| Domino workspace with RStudio Server | Any Domino 6.x deployment |
| Claude Code CLI at `~/.local/bin/claude` | See [Claude Code on Domino blueprint](https://domino.ai/resources/blueprints/claude-code-on-domino) |
| R ≥ 4.0 | |
| `rstudioapi` ≥ 0.13 | Only runtime R dependency |

### Configure your LLM provider (optional)

By default, addins call the **Anthropic API directly**. Set Domino Environment
Variables in the CE to switch provider — no R code changes needed:

#### Option A — Amazon Bedrock *(recommended for AWS-hosted Domino)*

Traffic stays within your AWS account. Bills through your existing AWS agreement.
IAM instance roles on EKS are picked up automatically — no API keys needed.

```
CLAUDE_CODE_USE_BEDROCK  = 1
AWS_REGION               = us-east-1
ANTHROPIC_MODEL          = us.anthropic.claude-sonnet-4-6
```

For key-based auth (Bedrock long-term API key):
```
CLAUDE_CODE_USE_BEDROCK  = 1
AWS_REGION               = us-east-1
ANTHROPIC_MODEL          = us.anthropic.claude-sonnet-4-6
AWS_BEARER_TOKEN_BEDROCK = <your-bedrock-long-term-api-key>
```

> **One-time AWS account setup:** Submit the Anthropic use-case form in the
> Bedrock console Model catalog. Access is granted immediately. Once per AWS
> account (or once at the AWS Organizations management account level).

#### Option B — Domino AI Gateway / self-hosted LLM *(air-gapped)*

```
ANTHROPIC_BASE_URL = https://your-domino-ai-gateway/
ANTHROPIC_API_KEY  = your-gateway-token
```

#### Option C — Direct Anthropic API *(default)*

No environment variables needed. Requires `ANTHROPIC_API_KEY` or an authenticated
Claude Code session (`claude login`) baked into the CE.

Every addin run logs the active provider to the R console:

```
[dominoClaudeRus] LLM provider: Amazon Bedrock
[dominoClaudeRus]               region=us-east-1  model=us.anthropic.claude-sonnet-4-6
```

### Runtime prompt overrides (no CE rebuild needed)

Override any prompt at runtime by dropping an `.md` file into your project:

```
my-domino-project/
└── clauderus-prompts/
    ├── inspect_data.md     ← overrides baked-in version immediately
    └── review_sap.md       ← add your organisation's SAP standards
```

Or set `DOMINO_CLAUDERUS_PROMPTS_DIR` as a Domino Environment Variable for a
team-wide override across all projects using this CE.

---

## Updating to a new version

1. Make changes in your fork (prompt edits, new addins, bug fixes)
2. Check [`NEWS.md`](NEWS.md) — prompt-only changes can use the runtime override; no rebuild needed
3. Create a new release tag in your repo (e.g. `v0.1.1`)
4. Update the `ref=` tag in your CE Dockerfile instruction and rebuild

| What changed | Version bump | CE rebuild? |
|---|---|---|
| Prompt text only (`inst/prompts/*.md`) | Patch `0.1.x` | No — use runtime override |
| New addin or R logic change | Minor `0.x.0` | Yes |
| Breaking change | Major `x.0.0` | Yes |
| LLM provider switch | None | No — update env vars only |

---

## Compliance and data safety

The **Inspect Data** addin never sends actual clinical data to any LLM endpoint.
`.build_data_summary()` sends only:

- Column names, R types, NA counts and percentages
- **Numeric columns:** min, max, mean, sd — no actual values
- **Character/factor columns:** unique value *count* only — no actual strings
- **Date columns:** unique date *count* only — actual dates explicitly redacted

No `head()`, no sample rows, no patient identifiers reach the LLM in any circumstance.

---

## For clinical programmers — improving prompts

Prompts live in [`inst/prompts/`](inst/prompts/). You do **not** need to know R
or request a CE rebuild to improve a prompt.

### Via Pull Request (permanent change)

1. Open the relevant `.md` file in `inst/prompts/` in your repo on GitHub
2. Click the pencil (edit) icon
3. Edit — `{{content}}` or `{{summary}}` is where selected text is injected; keep these placeholders
4. **Commit changes** → new branch → open a Pull Request
5. Get a colleague to review and approve → merge → new release tag
6. Notify the Domino platform team to rebuild the CE

### Via runtime override (same-day, no rebuild)

Drop an overriding `.md` into `clauderus-prompts/` in your project root (see above).

---

## For developers — repo structure

```
dominoClaudeRus/
├── R/
│   ├── addins.R       # five addin entry points
│   ├── prompts.R      # prompt loading + .build_data_summary()
│   └── utils.R        # Claude CLI detection, provider logging, Viewer rendering
├── inst/
│   ├── rstudio/
│   │   └── addins.dcf               # addin registry
│   └── prompts/
│       ├── check_logs.md
│       ├── inspect_data.md
│       ├── fix_warnings_message.md
│       ├── fix_warnings_code.md
│       ├── review_sap.md
│       └── generate_job_config.md
├── tests/
│   └── testthat/
│       ├── test-prompts.R
│       └── test-utils.R
├── DESCRIPTION
├── NAMESPACE
└── NEWS.md
```

### Running tests locally

```r
install.packages(c("testthat", "withr"))
devtools::test()
```

### Adding a new addin

1. Write a prompt template in `inst/prompts/your_addin.md`
2. Add a one-function wrapper in `R/addins.R` following the existing pattern
3. Register it in `inst/rstudio/addins.dcf`
4. No framework changes needed

---

## Support

- Issues: open an issue in your own fork
- Blueprint doc and background: [dominoClaudeRus on Domino](https://domino.ai/resources/blueprints/domino-clauderus)
- Domino platform questions: contact your Customer Success Manager or Professional Services team

# AGENTS.md — ct-samplesize v3.7.0

## Overview

`ct-samplesize`: An easy-to-use sample size & power tool for clinical trial practitioners. Powered by R + 20+ packages (rpact/gsDesign/TrialSize/PowerTOST etc.), it performs 49+ complex calculations via natural-language prompts (output in Chinese or English per OS language setting, prompt can force-switch). The generated R code is shown in SAFE PREVIEW (not executed unless --yes) and can be provided in full on request for verification, submission, or re-run.

---

## Core Rules

### 1. R Environment Detection
- Detect R via PATH or RSCRIPT_PATH env
- Installed → report version + check packages
- Not installed → recommend install + offer Python fallback

### 2. Extended Tool Selection

|User Need|Path|
|:----------|:-----|
| Basic stats (t-test/ANOVA/proportion) | Python → auto gen R code |
| Longitudinal / Repeated measures | R: `simr` (mixed model) |
| Diagnostic trial | R: `pROC` (ROC formula) |
| Count data / Recurrent events | R: custom Wald test |
| Cluster randomized | R: design effect formula |
| Method comparison | R: Bland-Altman (Lu et al.) |
| Bioequivalence | R: `PowerTOST` (TOST) |
| Group sequential / Adaptive | R: `gsDesign` / `rpact` |
| Non-inferiority | R: `TrialSize` (exact) / `powerSurvEpi` |
| Survival | R: `rpact` |
| Vaccine efficacy | R: Halloran formula |
| Bayesian design | R: `BayesCTDesign` |
| Dose escalation | R: `escalation` |
| Multiple endpoints | R: correlation method |
| Win-Ratio composite | R: `BuyseTest` power simulation |
| Must-Win / Co-Primary | R: correlation inflation factor |
| Historical Controls | R: `RBesT` MAP prior |
| MAMS | R: `rpact` |
| Conditional Power / SSR | R: `rpact` |
| Superiority by Margin | R: custom formula |
| Assurance | R: Monte Carlo simulation |
| Dunnett comparisons | R: `MCPAN` |
| Mediation | R: `powerMediation` |

### 3. Code Execution
- R via subprocess (Rscript), path: auto-detect (RSCRIPT_PATH env or PATH search)
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`)
- **Default: dry-run mode.** R code is displayed; execution requires `-y`/`--yes`
- Temp R files written to system temp dir (`tempfile.gettempdir()`), auto-cleaned after run

### 4. Result Output (v3.4.4)

Every analysis includes:
- Input parameters + defaults used
- Calculation result (sample size / power / effect size)
- Dropout adjustment (if applicable)
- Assumptions & limitations
- **Default = SAFE PREVIEW (code shown, NOT executed)**; use `--yes`/`-y` to execute & compute, `--show-code` to display the code (no execution), or `--dry-run` to preview only
- R code is generated and shown by default but NOT run unless `--yes` is given; `-y`/`--yes` explicitly executes and computes
- **`--test adaptive_simulate`**: primary engine is the inlined pure base-R function library `ADAPTIVE_SIM_R` (in `scripts/r_libs.py`, no extra packages) — the CLI writes it to a temp `.R` file, sources it, and calls `run_adaptive_sim` (SAFE PREVIEW, `--yes` to run, base R only). To drive it from R directly, run the CLI with `--show-code`/`-y` and copy the printed R code. When R is unavailable, the skill automatically falls back to the equivalent pure-Python module `scripts/adaptive_simulator.py`. See `references/adaptive_simulator.md`.

### 5. Language Detection
- **Follow OS language setting**: Output language (Chinese or English) follows the OS language setting — Chinese on a Chinese-OS, English otherwise.
- **Prompt can force-switch**: The user may override the OS-based default anytime via an explicit language request (e.g. "switch to English").
- **Detection method**: Linux/macOS read `LANG`/`LC_ALL`/`LANGUAGE`; Windows use `Get-Culture`/`Get-WinSystemLocale` or `os` env to check if the language code starts with `zh`; if the `<response_language>` tag specifies a language, follow it.
- **Docs are English-only (ct-base §13.2)**: The skill documentation (SKILL.md, AGENTS.md, references, etc.) is English-only. Runtime output for common modules may still be English + Chinese per OS setting; complex/rare modules are English-only.
- **Complex/rare modules may be English-only**: e.g. `group_sequential`, `adaptive`, `mixed_model`, `bayesian`, `win_ratio`, `mams`, `vaccine_efficacy` etc.
- **This policy does not affect code output**: R/Python code is always English, shown per `--show-code`.

### 6. Mixed Model Specifics
- Use `simr::makeLmer()` / `makeGlmer()` to build model from literature parameters
- Run `powerSim()` with nsim ≥ 500 for stable estimates
- Always run `powerCurve()` to find minimum sample size
- Report computation time (can be 1-5 min for complex models)

### 7. Menu Navigation Design — Non-Exclusive
- The interactive "quick menu" that guides users to pick a test type MUST NOT be a mutually-exclusive tree. The same test can appear under multiple top-level entries, mirroring PASS's menu design.
- Rationale: with 49 test types, classification dimensions intersect (design family × endpoint type). A strict tree would hide reachable paths. The menu is a *navigation aid*, not a taxonomy.
- Example: sequential survival analysis (`gsd_survival` = `group_sequential` + survival endpoint) must be reachable BOTH from a **Survival Analysis** top-level menu AND from a **Sequential Group-Sequential Design** top-level menu.
- Rule of thumb for future extensions: any test classifiable along multiple axes (e.g. sequential/adaptive × means/proportion/survival/rate) must be listed under every relevant top-level entry — do NOT hang it on a single node.
- **Menu structure is now formalized in `references/menu.md`** (primary tree by endpoint + design-family cross-index) and surfaced in SKILL.md `## Quick Menu`. When guiding a user to pick a test, read `references/menu.md` to stay consistent with the canonical classification.

### 8. Triage (ct-base §5.2) — Three-Way Interaction

Before any user interaction, triage first (ct-base §5.2), then decide whether / how to show a menu.

|Class|Trigger|Action|
|:---|:---|:---|
|**Simple**|Direct t-test/ANOVA/proportion-style question with clear how/why|Answer directly; 1–2 turns; pick from the 49 test types|
|**Complex**|Multi-step or design-family question (sequential/adaptive/mixed/survival)|Consult `references/menu.md` → present the relevant menu; guide step-by-step|
|**Vague**|Under-specified ask (missing endpoint, design, or effect size)|Use `grill-me` to ask 1–3 clarifying questions → then re-triage|

- Choose menu depth based on simple vs complex.
- `references/menu.md` defines the **Complex** path; Simple and Vague rarely need the full menu.

---

## Security Fixes (v3.3+)

|Fix|Implementation|
|:----|:--------------|
| Default dry-run | R code displayed, not executed unless `-y` confirmed |
| Output sanitization | `sanitize_output()` strips paths, truncates |
| No hardcoded R path | RSCRIPT_PATH env + PATH lookup |
| Narrowed triggers | Removed generic terms like "sample size" alone |
| Permissions declared | `permissions` block in SKILL.md frontmatter (top-level) |
| User warnings | `## ⚠️ User Warnings` section |
| Fixed `minfup` | Examples: `minfup <- T - R` (24 months, matches prose) |
| Fixed dropout code | Valid R syntax throughout |

---

## Dependencies

### R Packages (install on demand)
R packages do NOT need to be pre-installed all at once. When the skill detects a missing package it prints the install command in output; the user runs it once.

|Tier|Package|Used for|
|:---|:---|:---|
|**Core (high-freq)**|`TrialSize`, `pwr`, `rpact`, `gsDesign`, `PowerTOST`, `powerSurvEpi`|NI, equivalence, survival, superiority margin, group-sequential, BE etc.|
|**Aux (mid-freq)**|`simr`, `lme4`, `pROC`, `survival`|mixed model, ROC, exact survival ROC|
|**Low-freq**|`BayesCTDesign`, `escalation`, `BuyseTest`, `RBesT`, `MCPAN`, `powerMediation`, `BlandAltmanLeh`|vaccine, dose escalation, Win-Ratio, historical control, Dunnett, mediation|
|**No R package**|—|`ttest_*` (partial), `anova`, `poisson`, `cluster`, `bland_altman`, `vaccine_efficacy`, `bayesian`, `dose_escalation`, `assurance`, `multiple_endpoints`, `must_win`, `mediation`|

**When the user requests one-click install, run**
```r
install.packages(c("TrialSize", "pwr", "rpact", "gsDesign", "PowerTOST", "simr", "lme4", "pROC", "powerSurvEpi", "survival"))
```

**Or**
```bash
python scripts/samplesize_power.py --install-all-packages
```

### Python (pinned)
```
statsmodels==0.14.2
numpy==1.24.3
scipy==1.11.4
```

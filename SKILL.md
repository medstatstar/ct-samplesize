---
slug: ct-samplesize
displayName: 临床试验样本量与检验效能计算专家 / Clinical Trial Sample Size & Power
name: ct-samplesize
cn_name: 临床试验样本量与检验效能计算专家
version: 3.8.1
required_commands: [Rscript, python]
summary: 为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，自然语言驱动，支持 49 种检验。可应要求提供可复现 R 代码；默认按操作系统语言设定输出中文或英文（提示词可强制切换）。
license: MIT
description: "为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，自然语言驱动，支持 49 种检验。可应要求提供可复现 R 代码；默认按操作系统语言设定输出中文或英文（提示词可强制切换）。 / Easy-to-use sample size and power calculation tool for clinical trial practitioners. Backed by R + 20+ professional R packages including rpact/gsDesign/TrialSize/PowerTOST, natural language driven, supporting 49 test types. Reproducible R code available on request; default output in Chinese or English per OS language setting (prompt can force-switch)."
triggers:
  - "clinical trial sample size"
  - "样本量计算"
  - "clinical trial power"
  - "检验效能计算"
  - "临床试验 设计"
  - "non-inferiority sample size"
  - "非劣效 样本量"
  - "equivalence sample size"
  - "等效性 样本量"
  - "survival analysis sample size"
  - "生存分析 样本量"
  - "adaptive design"
  - "适应性设计"
  - "group sequential design"
  - "Bayesian clinical trial"
  - "贝叶斯 临床试验"
metadata:
  openclaw: { emoji: "📊" }
  authors: ["medstatstar", "phoe-zip"]
  license: "MIT"
  tags: [clinical-trial, sample-size, power, R, adaptive-design, bayesian, win-ratio]
  homepage: "https://github.com/medstatstar/ct-samplesize"
permissions:
  scope: "user-space-only"
  network: "optional"
  network_note: "Used ONLY by --run-install to fetch R packages from CRAN. Default analysis mode is fully offline; no network is touched unless the user explicitly adds --run-install."
  filesystem: "writes only to system temp (generated R script) and to the current working directory (generated curve PNG reports); otherwise read-only"
  data: "no external data transmission (except CRAN download under --run-install)"

---

# Clinical Trial Sample Size & Power

> **⚠️ Safe by default — preview, not execute**: By default the skill generates R code and shows it in a SAFE PREVIEW (no execution). Execution requires an explicit opt-in: CLI `--yes`/`-y`, or the agent adds `--yes` when it needs the actual number. `--show-code` shows code; `--dry-run` is the default preview mode.
>
> **Output language**: By default the output language follows the OS language setting — Chinese on a Chinese-OS, English otherwise. The user may force-switch anytime via a prompt (e.g. "switch to English"). Docs are English-only (ct-base §13.2); runtime output may still be English + Chinese per OS setting. This setting does not affect code output.

## Language

- **English guide** → [README.md](https://github.com/medstatstar/ct-samplesize/blob/main/README.md)
- **中文指南** → [README_zh-CN.md](https://github.com/medstatstar/ct-samplesize/blob/main/README_zh-CN.md)

### Language policy

> Docs are English-only per **ct-base §13.2**; runtime output follows the OS language setting (Chinese on zh/CN OS, else English) and the user may force-switch via a prompt. Code output is always English. See `references/language_policy.md`.

- This skill's documentation (SKILL.md, AGENTS.md, references/*) is English-only — no Chinese required in docs.
- Runtime output for common modules may still be English + Chinese per OS setting; complex/rare modules are English-only. The user may force-switch the output language via a prompt at any time.
- Common modules: `ttest_*`, `anova`, `proportion_*`, `odds_ratio`, `risk_ratio`, `roc`, `poisson`, `non_inferiority`, `superiority_margin`, `be_tost`, `equivalence`, `survival`, `ni_survival`, `cluster`, `dunnett`.
- Complex/rare modules (EN-only): `group_sequential`, `gsd_proportion`, `gsd_survival`, `gsd_survival_sim`, `gsd_hazard`, `gsd_hazard_sim`, `gsd_poisson`, `adaptive`, `adaptive_simulate`, `mixed_model`, `bayesian`, `win_ratio`, `historical_controls`, `assurance`, `conditional_power`, `dose_escalation`, `vaccine_efficacy`, `mams`, `survival_exact`, `mediation` etc.

## Purpose

This skill provides clinical trial researchers with an easy-to-use, comprehensive sample size & power calculation tool. Powered by R and 20+ professional R packages (rpact, gsDesign, TrialSize, PowerTOST, etc.), users can perform 49 complex calculations through natural language prompts — output in Chinese or English per the OS language setting (prompt can force-switch). Reproducible R code is available on request.

---

## Features

| Capability | Description | Typical Scenario |
|:---|:---|:---|
| **① Sample size ⇄ Power (bidirectional)** | Solve n given target power, AND solve achievable power given fixed n. `--power` (forward) and `--nobs` (reverse) are mutually exclusive; covers all 49 types. | Sample size fixed, evaluate if power meets target |
| **② Power curve** | Given a sample-size sequence, batch-compute and plot the **Power curve** (x=sample size, y=power), with a target-power reference line. | Sample-size sensitivity analysis, protocol reporting |
| **③ Sample-size curve** | Given a power-target sequence, batch-compute and plot the **sample-size curve** (x=target power, y=required n). | Resource planning, feasibility assessment |

- ②③ curve mode: list `"20,40,200"` or auto-seq `"20:20:200"` (start:step:stop); overlay multiple effect-size curves for sensitivity; default PNG + data table. All reuse the same validated formulas.
- Full parameters & 49-test examples → `references/cli_examples.md`.

---

## Interaction — Triage first (inherit ct-base §5.2)

Before answering, triage the request into **Simple / Complex / Vague** (ct-base §5.2):
- **Simple** (test already named, params mostly given) → answer directly, **no menu**.
- **Complex** (pick test type / design family / many params) → show the **routing menu** below.
- **Vague** ("not sure which test to use") → **grill-me branch-by-branch probing**, do **not** dump the menu.

> **Triage gate (inherits ct-base §5.2):** classify the request first — Simple → answer directly, no menu; Complex → show the routing menu below; Vague → use grill-me branch-by-branch probing. **The `## Quick Menu` below is for the Complex branch only.**

## Quick Menu

> Authoritative layered menu: [`references/menu.md`](references/menu.md) · CLI examples & bidirectional solve: [`references/cli_examples.md`](references/cli_examples.md) · Operation SOP: [`references/operation_sop.md`](references/operation_sop.md).

**Top-level entry points (6 endpoint categories):**
- ① **Continuous** — `ttest_ind` `ttest_paired` `ttest_one` `anova` `equivalence` `mixed_model`
- ② **Binary / Proportions** — `proportion_one` `proportion_two` `proportion_paired` `odds_ratio` `risk_ratio` `non_inferiority` `superiority_margin` `be_tost` `vaccine_efficacy` `gsd_proportion`
- ③ **Count / Rates** — `poisson` `recurrent_events` `gsd_poisson`
- ④ **Survival / Time-to-event** — `survival` `ni_survival` `survival_equivalence` `survival_superiority` `cox_covariate` `survival_one_sample` `competing_risks` `survival_historical` `survival_exact` `gsd_survival` `gsd_hazard` `gsd_survival_sim` `gsd_hazard_sim`
- ⑤ **Diagnostic / Method comparison** — `roc` `bland_altman`
- ⑥ **Special / Advanced designs** — `group_sequential` `adaptive` `adaptive_simulate` `bayesian` `dose_escalation` `mams` `dunnett` `win_ratio` `must_win` `historical_controls` `conditional_power` `assurance` `multiple_endpoints` `mediation` `cluster`

**Design-family cross-index** (non-exclusive second entry — full list in `references/menu.md`): Group-Sequential · Adaptive · Equivalence / Non-inferiority · Bayesian · Dose-escalation · MAMS · Historical control · Vaccine · Win-statistics …

> The menu is a *navigation aid*, not a strict taxonomy: the same test is reachable from multiple top-level menus (e.g. `gsd_survival` from both ④ Survival and the Group-Sequential index).

### Adaptive-trial Monte-Carlo simulator

Beyond the 49 analytic tests, `--test adaptive_simulate` runs a Monte-Carlo simulator to **validate** adaptive / group-sequential designs empirically: power, type I error, expected sample size, early-stop probabilities. **Primary engine: an inlined pure base-R function library** (`ADAPTIVE_SIM_R` in `scripts/r_libs.py`, no extra packages) — the CLI writes it to a temp `.R` file and `source()`s it, then calls `run_adaptive_sim()` (one-shot with report) or the individual `simulate_group_sequential()` / `simulate_adaptive_reestimate()` / `simulate_drop_the_loser()` / `optimize_power()` functions directly. The CLI shows this `source(...)` + `run_adaptive_sim(...)` code in SAFE PREVIEW (like every other test) and executes it with `--yes`; it needs only base R (no extra packages). **Fallback: when R is not installed**, the skill automatically runs the equivalent pure-Python module `scripts/adaptive_simulator.py` so the user still gets results. Designs: `group_sequential`, `adaptive_reestimate` (promising-zone SSR with Cui-Hung-Wang statistic), `drop_the_loser` (multi-arm). Spending: `obrien_fleming` / `pocock` / `power_family`. Also supports `--futility`, `--optimize` (min-N search) and `--visualize`. Full guide: `references/adaptive_simulator.md`.

---

## Requirements

| Requirement | Details |
|:---|:---|
| **R** | ≥ 4.1.0 (install on demand, see `references/r_packages.md`) |
| **Python** | ≥ 3.8 + statsmodels≥0.14.2, numpy≥1.24.3, scipy≥1.11.4. Used by the `adaptive_simulate` **no-R fallback** and `--visualize` (matplotlib≥3.4). R is the primary engine for `adaptive_simulate`. |

---

## ⚠️ Safety

- R code is NOT executed by default — it runs in SAFE PREVIEW (code shown, not run); use `--yes`/`-y` to explicitly execute and compute
- All computations are local; no data transmission
- Output for reference only; validate before regulatory submissions

### Security model (transparent disclosure)

| Behavior | Description |
|:---|:---|
| **Local process call** | Run DYNAMICALLY GENERATED (never raw user input) R code locally via `subprocess.run([Rscript, '--vanilla', tmp])`, timeout 300s, NO shell. Execution is OPT-IN: by default the code is only previewed; it runs only when `--yes` is passed. Every user string that reaches the R code is validated against a strict allowlist first, so it cannot break out of an R string (no RCE). |
| **R code source** | All generated by the skill's built-in templates (`scripts/r_templates/`), no static `.R` files, no remote script download. By default the skill runs in SAFE PREVIEW — generated R code is shown but NOT executed; `--yes` executes, `--show-code` reveals the code. |
| **Output sanitization** | R stdout/stderr passes through `sanitize_output()` to strip local absolute paths and truncate over-long content before display, avoiding environment leakage or content injection. |
| **Network access** | Default analysis is fully offline, zero network. The only network touchpoint is the optional R-package install: by default it only prints `install.packages()` commands, not executed; you must explicitly add `--run-install` to download & install from CRAN (supply-chain risk triggered only after user is informed). The permission manifest declares `network: "optional"` (used only by `--run-install`). The full install R code is printed before execution. |
| **Filesystem** | Writes only a temp R script in the skill dir / system temp, discarded after use; never reads/writes user data files. |

---

## Implementation

> **Default = SAFE PREVIEW (dry-run):** generate & show R code, do NOT execute. Add `--yes`/`-y` to execute & compute; `--show-code` shows the code. Full CLI examples (all 49 tests, reverse-solve, curve mode, R-package install) → `references/cli_examples.md`. Data format guide → `references/data_format_guide.md`.

**Bidirectional solve:** `--power` (default) solves required `n` given target power; `--nobs N` reverses to achievable power given fixed `n` (mutually exclusive, `--nobs` wins).

**Common params:**
- `--side one|two` (default `two`): test direction; affects t-test, proportion tests, and significance level / required n in curve mode.
- `--sd FLOAT` (optional): treats `--effect` as raw mean difference Δ and auto-computes Cohen's d = Δ / sd; when omitted, `--effect` is Cohen's d directly.

**Curve mode:** `--n_seq "20:20:200"` → Power curve; `--power_seq "0.8,0.9"` → sample-size curve; `--plot_effects` overlays sensitivity curves; plotting uses base R graphics (no ggplot2), 22 test types supported.

**R package install (safe):** `--install-all-packages` only prints `install.packages()` commands; append `--run-install` to actually install from CRAN. Full list → `references/cli_examples.md` and `references/r_packages.md`.

> **Architecture & security:** all algorithms are pre-written R functions (`ss_*`) in `scripts/r_templates/`; the dispatcher injects params and calls `.format()` — no scattered R code. R-package tests auto-fall back to analytic approximations on package failure. Version history & hardening → `CHANGELOG.md`.

---

## Formulas & Reports

**Formulas:** `references/formulas.md` | **Full functions:** `references/extended_functions.md`

| Scenario | Formula |
|:---|:---|
| Independent t | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| Proportion (arcsin) | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| Survival (Schoenfeld) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |
| Survival Equivalence (TOST/log-HR) | $D = \frac{[2(Z_{1-\alpha} + Z_{1-\beta})]^2}{(\log\delta_E)^2},\ n_{pg}=\frac{D/2}{e}$ |
| Survival Superiority w/ margin | $\delta=\log\delta_S-\log HR;\ D = \frac{[2(Z_{1-\alpha} + Z_{1-\beta})]^2}{\delta^2}$ |
| Cox w/ covariate (Vittinghoff) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(1-R^2)\,p(1-p)\,(\log HR)^2}$ |
| One-sample exponential | $\lambda_j=\frac{\log2}{m_j},\ e_j=1-e^{-\lambda_j\bar t},\ n=\lceil\frac{\mu_1}{e_1}\rceil,\ \mu_1=(\frac{Z_{1-\alpha}\sqrt r+Z_{1-\beta}}{r-1})^2$ |
| Competing risks (CIF) | $n_{pg}=\lceil\frac{(Z_{1-\alpha/2}+Z_{1-\beta})^2[\pi_C(1-\pi_C)+\pi_T(1-\pi_T)]}{(\pi_C-\pi_T)^2}\rceil$ |
| Recurrent events (Poisson) | $n_{pg}=\lceil\frac{(Z_{1-\alpha/2}+Z_{1-\beta})^2(\lambda_1+\lambda_2)}{t(\lambda_1-\lambda_2)^2}\rceil$ |
| Historical-control logrank | single-arm vs historical median $m_H$; same one-sample exponential structure |
| Cluster DEFF | $DEFF = 1 + (m - 1) \times ICC$ |

---

## Errors

| Error | Fix |
|:---|:---|
| "Rscript not found" | Install R or specify path |
| "package not found" | install.packages("xxx") |
| ImportError: statsmodels | pip install statsmodels |
| simr timeout | Reduce --nsim |

---

## Related skills (ct- library, agent chains as needed)

- **Upstream (context)**: `ct-registry` (competitor / disease landscape, Tier B, provided by `ct-pipeline` public-intel orchestration)
- **Downstream (handoff)**: `ct-protocol` (protocol skeleton, A default / B retrieval) → `ct-ecrf` (CRF + SDTM mapping spec, Tier A)
- **Same category (design scope, to build)**: `ct-protocol` / `ct-ecrf` / `ct-eligibility`(D)
- **Public-intel orchestration (Tier B, no direct dispatch dependency)**: `ct-pipeline` (`intel` / `surveillance` presets, dispatches `ct-registry` / `ct-safety` / `ct-literature`)
- **Authoritative mapping / tier**: see `ct-base/BASE.md` §1.5 / §9

**Version**: v3.8.0 | **Updated**: 2026-08-02 | **License**: MIT

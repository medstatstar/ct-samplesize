# AGENTS.md — ct-samplesize v3.4.8

## Overview / 技能概述

`ct-samplesize`: An easy-to-use sample size & power tool for clinical trial practitioners. Powered by R + 20+ packages (rpact/gsDesign/TrialSize/PowerTOST etc.), it performs 37 complex calculations via natural-language prompts (English by default, auto-Chinese on Chinese-OS). The generated R code is shown in SAFE PREVIEW (not executed unless --yes) and can be provided in full on request for verification, submission, or re-run. / ct-samplesize：面向临床试验从业者的易用型样本量与检验效能计算工具。后台以 R 软件及 rpact/gsDesign/TrialSize/PowerTOST 等 20+ R工具包为依托，用户只需使用自然语言对话方式的提示词，即可完成（默认英文输出，OS 中文环境时自动切换中文）37 种复杂专业的样本量与检验效能计算工作。生成的 R 代码默认以安全预览展示（不执行，除非加 --yes），也可应要求完整提供，供用户核查、递交代码或修改后重跑。

---

## Core Rules / 核心规则

### 1. R Environment Detection / R 环境检测
- Detect R via PATH or RSCRIPT_PATH env
- Installed → report version + check packages
- Not installed → recommend install + offer Python fallback

### 2. Extended Tool Selection / 扩展工具选择

| User Need 用户需求 | Path 路径 |
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

### 3. Code Execution / 代码执行规范
- R via subprocess (Rscript), path: auto-detect (RSCRIPT_PATH env or PATH search)
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`)
- **Default: dry-run mode.** R code is displayed; execution requires `-y`/`--yes`
- Temp R files written to system temp dir (`tempfile.gettempdir()`), auto-cleaned after run

### 4. Result Output / 结果输出标准 (v3.4.4)

Every analysis includes:
- Input parameters + defaults used
- Calculation result (sample size / power / effect size)
- Dropout adjustment (if applicable)
- Assumptions & limitations
- **Default = SAFE PREVIEW (code shown, NOT executed)**; use `--yes`/`-y` to execute & compute, `--show-code` to display the code (no execution), or `--dry-run` to preview only
- R code is generated and shown by default but NOT run unless `--yes` is given; `-y`/`--yes` explicitly executes and computes
- **`--test adaptive_simulate`**: primary engine is the standalone pure base-R function library `scripts/adaptive_sim.R` — the CLI sources it and calls `run_adaptive_sim()` (SAFE PREVIEW, `--yes` to run, base R only, no extra packages). You can also `source("scripts/adaptive_sim.R")` in R yourself and call `run_adaptive_sim()` / `simulate_*()` directly. When R is unavailable, the skill automatically falls back to the equivalent pure-Python module `scripts/adaptive_simulator.py`. See `references/adaptive_simulator.md`. / `--test adaptive_simulate`：主引擎为独立纯 base-R 函数库 `scripts/adaptive_sim.R`——CLI 通过 `source()` 它并调用 `run_adaptive_sim()`（安全预览默认、`--yes` 执行，仅需 base R）；你也可在 R 中自行 `source("scripts/adaptive_sim.R")` 后直接调用 `run_adaptive_sim()`/`simulate_*()`。未装 R 时自动回退至等价的纯 Python 模块 `scripts/adaptive_simulator.py`。详见 `references/adaptive_simulator.md`。

### 5. Language Detection / 语言检测
- **Default English / 默认英文**: All user-facing prompt content defaults to English. / 所有面向用户的提示内容默认使用英文。
- **Auto-switch to Chinese on Chinese-OS / OS 中文环境自动切换中文**: When the OS is detected as Chinese (locale contains `zh`/`CN`, e.g. `LANG=zh_CN.UTF-8`, Windows UI language `zh-CN`), prompt content auto-switches to Chinese without explicit user request. / 当检测到操作系统为中文环境（locale 含 `zh`/`CN`，如 `LANG=zh_CN.UTF-8`、Windows UI 语言 `zh-CN`）时，给用户的提示内容自动切换为中文，无需用户显式要求。
  - **Detection method / 检测方法**: Linux/macOS read `LANG`/`LC_ALL`/`LANGUAGE`; Windows use `Get-Culture`/`Get-WinSystemLocale` or `os` env to check if the language code starts with `zh`; if the `<response_language>` tag specifies a language, follow it. / Linux/macOS 读 `LANG`/`LC_ALL`/`LANGUAGE`；Windows 用 `Get-Culture`/`Get-WinSystemLocale` 或 `os` 环境变量判断语言代码是否以 `zh` 开头；若 `<response_language>` 标签明确指定，则服从该标签。
- **Common modules must prepare bilingual / 常用模块须备双语**: English + Chinese prompt content for common test types, report template, quick menu, flag reference. / 常用检验类型、报告模板、快速引导菜单、参数速查表须准备英文 + 中文两套提示内容。
- **Complex/rare modules may be English-only / 复杂/少用模块可暂只英文**: e.g. `group_sequential`, `adaptive`, `mixed_model`, `bayesian`, `win_ratio`, `mams`, `vaccine_efficacy` etc. / 如 `group_sequential`、`adaptive`、`mixed_model`、`bayesian`、`win_ratio`、`mams`、`vaccine_efficacy` 等。
- **This policy does not affect code output / 此策略不影响代码输出**: R/Python code is always English, shown per `--show-code`. / R/Python 代码始终英文，按 `--show-code` 展示。

### 6. Mixed Model Specifics / 混合模型特别说明
- Use `simr::makeLmer()` / `makeGlmer()` to build model from literature parameters
- Run `powerSim()` with nsim ≥ 500 for stable estimates
- Always run `powerCurve()` to find minimum sample size
- Report computation time (can be 1-5 min for complex models)

---

## Security Fixes (v3.3+)

| Fix 修复 | Implementation 实现 |
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

## Dependencies / 依赖

### R Packages (install on demand) / R 包（按需安装）
R packages do NOT need to be pre-installed all at once. When the skill detects a missing package it prints the install command in output; the user runs it once. / R 包不需要全部预装。技能检测到某包缺失时会在输出中提示安装命令。用户只需执行一次即可。

| Tier 依赖层级 | Package 包 | Used for 用到时 |
|:---|:---|:---|
| **Core (high-freq) / 核心（高频）** | `TrialSize`, `pwr`, `rpact`, `gsDesign`, `PowerTOST`, `powerSurvEpi` | NI, equivalence, survival, superiority margin, group-sequential, BE etc. / 非劣效、等效、生存、优效界值、组序贯、BE 等 |
| **Aux (mid-freq) / 辅助（中频）** | `simr`, `lme4`, `pROC`, `survival` | mixed model, ROC, exact survival / 混合模型、ROC、精确生存 |
| **Low-freq / 低频** | `BayesCTDesign`, `escalation`, `BuyseTest`, `RBesT`, `MCPAN`, `powerMediation`, `BlandAltmanLeh` | vaccine, dose escalation, Win-Ratio, historical control, Dunnett, mediation / 疫苗、剂量递增、Win-Ratio、历史对照、Dunnett、中介 |
| **No R package / 无需 R 包** | — | `ttest_*` (partial), `anova`, `poisson`, `cluster`, `bland_altman`, `vaccine_efficacy`, `bayesian`, `dose_escalation`, `assurance`, `multiple_endpoints`, `must_win`, `mediation` |

**When the user requests one-click install, run / 用户要求一键安装时，执行：**
```r
install.packages(c("TrialSize", "pwr", "rpact", "gsDesign", "PowerTOST", "simr", "lme4", "pROC", "powerSurvEpi", "survival"))
```

**Or / 或：**
```bash
python scripts/samplesize_power.py --install-all-packages
```

### Python (pinned) / Python（固定版本）
```
statsmodels==0.14.2
numpy==1.24.3
scipy==1.11.4
```

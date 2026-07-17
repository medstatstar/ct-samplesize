# AGENTS.md — ct-samplesize v3.3

## Overview / 技能概述

`ct-samplesize`: 面向临床试验从业者的易用型样本量与检验效能计算工具。后台以 R 软件及 rpact/gsDesign/TrialSize/PowerTOST 等 20+ R工具包为依托，用户只需使用自然语言对话方式的提示词，即可完成（默认英文输出，OS 中文环境时自动切换中文）37 种复杂专业的样本量与检验效能计算工作。可应要求提供可复现 R 代码（默认不展示），供用户核查、递交代码或修改后重跑。

---

## Core Rules / 核心规则

### 1. R Environment Detection / R 环境检测
- Detect R via PATH or RSCRIPT_PATH env
- Installed → report version + check packages
- Not installed → recommend install + offer Python fallback

### 2. Extended Tool Selection / 扩展工具选择

| User Need | Path |
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

### 4. Result Output / 结果输出标准 (v4.0)

Every analysis includes:
- Input parameters + defaults used
- Calculation result (sample size / power / effect size)
- Dropout adjustment (if applicable)
- Assumptions & limitations
- **Generated R code hidden by default**; shown via `--show-code` (execute + show) or `--dry-run` (preview only)
- Default = execute & return result (no code shown); `-y`/`--yes` kept for backward compatibility

### 5. Language Detection / 语言检测
- **默认英文**：所有面向用户的提示内容默认使用英文。
- **OS 中文环境自动切换中文**：当检测到操作系统为中文环境（locale 含 `zh`/`CN`，如 `LANG=zh_CN.UTF-8`、Windows UI 语言 `zh-CN`）时，给用户的提示内容**自动切换为中文**，无需用户显式要求。
  - 检测方法：Linux/macOS 读 `LANG`/`LC_ALL`/`LANGUAGE`；Windows 用 `Get-Culture`/`Get-WinSystemLocale` 或 `os` 环境变量判断语言代码是否以 `zh` 开头；若 `<response_language>` 标签明确指定，则服从该标签。
- **常用模块须备双语**（英文 + 中文两套提示内容）：常用检验类型、报告模板、快速引导菜单、参数速查表。
- **复杂 / 少用模块可暂只英文**：如 `group_sequential`、`adaptive`、`mixed_model`、`bayesian`、`win_ratio`、`mams`、`vaccine_efficacy` 等。
- 此策略**不影响代码输出**（R/Python 代码始终英文，按 `--show-code` 展示）。

### 6. Mixed Model Specifics / 混合模型特别说明
- Use `simr::makeLmer()` / `makeGlmer()` to build model from literature parameters
- Run `powerSim()` with nsim ≥ 500 for stable estimates
- Always run `powerCurve()` to find minimum sample size
- Report computation time (can be 1-5 min for complex models)

---

## Security Fixes (v3.3+)

| Fix | Implementation |
|:----|:--------------|
| Default dry-run | R code displayed, not executed unless `-y` confirmed |
| Output sanitization | `sanitize_output()` strips paths, truncates |
| No hardcoded R path | RSCRIPT_PATH env + PATH lookup |
| Narrowed triggers | Removed generic terms like "sample size" alone |
| Permissions declared | `permissions` block in SKILL.md frontmatter |
| User warnings | `## ⚠️ User Warnings` section |
| Fixed `minfup` | Examples: `minfup <- T - R` (24 months, matches prose) |
| Fixed dropout code | Valid R syntax throughout |

---

## Dependencies / 依赖

### R Packages (按需安装)
R 包**不需要全部预装**。技能检测到某包缺失时会在输出中提示安装命令。用户只需执行一次即可。

| 依赖层级 | 包 | 用到时 |
|:---|:---|:---|
| **核心（高频）** | `TrialSize`, `pwr`, `rpact`, `gsDesign`, `PowerTOST`, `powerSurvEpi` | 非劣效、等效、生存、优效界值、组序贯、BE 等 |
| **辅助（中频）** | `simr`, `lme4`, `pROC`, `survival` | 混合模型、ROC、精确生存 |
| **低频** | `BayesCTDesign`, `escalation`, `BuyseTest`, `RBesT`, `MCPAN`, `powerMediation`, `BlandAltmanLeh` | 疫苗、剂量递增、Win-Ratio、历史对照、Dunnett、中介 |
| **无需 R 包** | — | `ttest_*`（部分）、`anova`、`poisson`、`cluster`、`bland_altman`、`vaccine_efficacy`、`bayesian`、`dose_escalation`、`assurance`、`multiple_endpoints`、`must_win`、`mediation` |

**用户要求一键安装时，执行：**
```r
install.packages(c("TrialSize", "pwr", "rpact", "gsDesign", "PowerTOST", "simr", "lme4", "pROC", "powerSurvEpi", "survival"))
```

**或：**
```bash
python scripts/samplesize_power.py --install-all-packages
```

### Python (pinned)
```
statsmodels==0.14.2
numpy==1.24.3
scipy==1.11.4
```

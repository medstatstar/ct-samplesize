# AGENTS.md — ct-samplesize v3.1

## Overview / 技能概述

`ct-samplesize`: Clinical trial sample size & power calculator. Supports 18 test types covering all major clinical trial scenarios. Bilingual EN/CN. **R code output is hidden by default and provided only on user request.**

---

## Core Rules / 核心规则

### 1. R Environment Detection / R 环境检测
- PowerShell: `Get-Command Rscript -ErrorAction SilentlyContinue`
- Detected → report version + check packages
- Not detected → strongly recommend install + offer Python fallback

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
| Non-inferiority | R: `TrialSize` (exact) |
| Survival | R: `rpact` |
| Vaccine efficacy | R: Halloran formula |
| Bayesian design | R: `BayesCTDesign` |
| Dose escalation | R: `escalation` |
| Multiple endpoints | R: correlation method |

### 3. Code Execution / 代码执行规范
- R via PowerShell, path: auto-detect (RSCRIPT_PATH env or PATH search)
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`)
- **Default: dry-run mode.** R code is printed for review; execution requires `-y`/`--yes`
- Output temp files to script directory, not system temp

### 4. 📋 Result Output / 结果输出标准 (v3.1 — R Code On Demand)

**默认输出（不带 R 代码）**：每次分析必须包含：
- 输入参数 + 使用的默认值
- 计算结果（样本量 / 效能 / 效应量）
- 脱落调整（如适用）
- 前提假设与局限
- 末尾附一句提示：「💡 需要可复现 R 代码？说 **'带代码'** 或 **'with R code'** 获取」

**R 代码触发短语 / R Code Trigger Phrases:**
| 中文 | English |
|:------|:---------|
| "带代码" | "with R code" |
| "输出R代码" | "output R code" |
| "给代码" | "show me the code" |
| "review 一下代码" | "review the code" |
| "展示R code" | "display R code" |
| "我需要复现代码" | "I need the code" |

**触发后行为**：
1. 展示完整可运行 R 代码（含 install.packages + library + 参数 + 注释）
2. 提供文字解释
3. 标注文件路径供保存

### 5. Language Detection / 语言检测
Detect from `<response_language>` tag or user input. Respond in the **same language**.

### 6. Mixed Model Specifics / 混合模型特别说明
- Use `simr::makeLmer()` / `makeGlmer()` to build model from literature parameters
- Run `powerSim()` with nsim ≥ 500 for stable estimates
- Always run `powerCurve()` to find minimum sample size
- Report computation time (can be 1-5 min for complex models)

---

## Security Fixes (v3.1)

| Fix | Implementation |
|:----|:--------------|
| Default dry-run | R code shown, not executed unless `-y` confirmed |
| Output sanitization | `sanitize_output()` strips paths, truncates |
| No hardcoded R path | RSCRIPT_PATH env + PATH lookup |
| Narrowed triggers | Removed "clinical trial design", "effect size" |
| Permissions declared | `permissions` block in SKILL.md frontmatter |
| User warnings | `## ⚠️ User Warnings` section |
| Fixed `minfup` | Examples: `minfup <- T - R` (24 months, matches prose) |
| Fixed dropout code | Valid R syntax: `dropout_rate <- 0.10; n_adj <- ceiling(n_per / (1 - dropout_rate))` |

---

## Dependencies / 依赖

### R Packages (v3.1)
```r
install.packages(c(
  "rpact",          # Adaptive + Group Sequential
  "gsDesign",       # Classical Group Sequential
  "TrialSize",      # Comprehensive (80+ functions)
  "pwr",            # Teaching/demo
  "PowerTOST",      # Bioequivalence (TOST)
  "simr",           # Mixed model power (Monte Carlo)
  "pROC",           # ROC curve formulas
  "BlandAltmanLeh", # Bland-Altman LoA
  "lme4",           # Linear mixed models
  "lmerTest",       # P-values for lme4
  "survival",       # Survival analysis
  "powerSurvEpi",   # Survival power
  "BayesCTDesign",  # Bayesian design
  "escalation"      # Dose escalation
))
```

### Python (pinned)
```
statsmodels==0.14.2
numpy==1.24.3
scipy==1.11.4
```

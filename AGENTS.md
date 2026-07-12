# AGENTS.md — ct-samplesize v2.0

## Overview / 技能概述

`ct-samplesize`: Clinical trial sample size & power calculator. Supports 14 test types: basic stats (t-test/ANOVA/proportion/non-inferiority), advanced designs (group sequential/adaptive/platform), mixed models (simr), bioequivalence (PowerTOST), ROC, Poisson, cluster randomized, Bland-Altman. Bilingual EN/CN.

`ct-samplesize`: 临床试验样本量与检验效能计算工具。支持 14 种检验类型：基础统计(t检验/方差分析/率/非劣效)，高级设计(组序贯/适应性/平台)，混合效应模型，生物等效性，ROC，Poisson率，类随机，Bland-Altman。中英双语。

---

## Core Rules / 核心规则

### 1. R Environment Detection / R 环境检测
```
Must detect user's R installation:
- PowerShell: `Get-Command Rscript -ErrorAction SilentlyContinue`
- Detected → report version + check packages
- Not detected → strongly recommend install + offer Python fallback
```

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

### 3. Code Execution / 代码执行规范
- R via PowerShell (CREATE_NO_WINDOW), path: `C:\Tools\R-4.5.1\bin\x64\Rscript.exe`
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`)
- Output temp files to workbuddy project dir, not C:\Temp

### 4. Result Output / 结果输出标准
Every analysis must include:
- Input parameters + defaults used
- Calculation result (sample size / power / effect size)
- Dropout adjustment (if applicable)
- Assumptions & limitations
- **Standalone reproducible R code** (🔴 mandatory)

### 5. 🔴 Mandatory R Code / 强制输出 R 代码
**Regardless of calculation path (Python/R/both), every analysis MUST include standalone, reproducible R code.**

- R code must include: `install.packages()`, `library()`, hardcoded params, calculation, formatted output
- User can copy-paste to R Studio / Rscript

### 6. Language Detection / 语言检测
**EN:** Detect from `<response_language>` tag or user input. Respond in the **same language**. Pick the matching bilingual template from SKILL.md.

**CN:** 从 `<response_language>` 标签或用户输入语言自动检测，用**同一种语言**回复。使用 SKILL.md 中的双语模板，选择对应版本。

### 7. Mixed Model Specifics / 混合模型特别说明
- Use `simr::makeLmer()` / `makeGlmer()` to build model from literature parameters
- Run `powerSim()` with nsim ≥ 500 for stable estimates
- Always run `powerCurve()` to find minimum sample size
- Report computation time (can be 1-5 min for complex models)
- For Poisson GLMM: use `family = poisson` in makeGlmer

---

## File Structure / 文件结构
```
ct-samplesize/
├── SKILL.md              ← skill definition (bilingual, concise)
├── README.md             ← English version
├── README_ZH.md          ← Chinese version
├── AGENTS.md             ← this file (core rules)
├── assets/
│   └── icon.svg          ← skill icon (104×104)
├── scripts/
│   └── samplesize_power.py  ← Python calc + auto R code gen (v2.0)
└── references/
    ├── r_packages_zh.md     ← R package reference
    ├── formulas_zh.md       ← formula reference
    ├── python_usage.md      ← Python quick ref
    ├── r_usage.md           ← R quick ref
    ├── effect_size.md       ← effect size standards
    ├── report_template.md   ← report template
    ├── examples.md          ← 3 full examples
    └── extended_functions.md ← NEW: mixed model/ROC/Poisson/cluster/BE
```

---

## Dependencies / 依赖

### R Packages (v2.0)
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
  "lme4",           # Linear mixed models (simr dependency)
  "lmerTest",       # P-values for lme4 (simr dependency)
  "survival",       # Survival analysis
  "powerSurvEpi"    # Survival power
))
```

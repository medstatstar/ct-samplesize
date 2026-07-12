# AGENTS.md — ct-samplesize

## Overview / 技能概述
`ct-samplesize`: Clinical trial sample size & power calculator. Intelligently detects R environment, recommends optimal tools, completes calculations with bilingual output.

`ct-samplesize`: 临床试验样本量与检验效能计算工具。智能检测 R 环境，推荐最优工具，完成计算与双语输出。

---

## Core Rules / 核心规则

### 1. R Environment Detection / R 环境检测
```
Must detect user's R installation:
- PowerShell: `Get-Command Rscript -ErrorAction SilentlyContinue`
- Detected → report version + check packages
- Not detected → strongly recommend install + offer Python fallback
```

### 2. Tool Selection / 工具选择
- Simple (t/ANOVA/prop/noninfer/survival simpl) → Python
- Complex (GS/adaptive/multi-arm/platform/BE) → R required

### 3. Code Execution / 代码执行规范
- R via PowerShell (CREATE_NO_WINDOW)
- Python via Anaconda (`C:\Tools\anaconda3\python.exe`)

### 4. Result Output / 结果输出标准
Every analysis must include: input params, calculation result, dropout adjustment, assumptions, limitations, **standalone R code**.

每次必须包含：输入参数、计算结果、脱落调整、前提假设、方法学限制、**可独立运行的 R 代码**。

### 5. 🔴 Mandatory R Code / 强制输出 R 代码

**Regardless of calculation path (Python/R/both), every analysis MUST include standalone, reproducible R code.**

**无论使用哪种计算路径（Python/R/混合），每次分析都必须附带可独立运行的原始 R 代码。**

- User can copy R code to R Studio / Rscript to reproduce
- Must include `install.packages()`, `library()`, hardcoded params, calculation, formatted output
- For survival, group sequential, etc., R code is the only precise method

### 6. Language Detection / 语言检测

**EN:** Detect user's language from system prompt (`<response_language>` tag) or input language. Respond in the **same language**. Use the bilingual templates in SKILL.md — pick the version matching the user's language.

**CN:** 从系统 prompt 的 `<response_language>` 标签或用户输入语言自动检测用户语言，并用**同一种语言**回复。使用 SKILL.md 中的双语模板，选择与用户语言一致的版本。

---

## File Structure / 文件结构
```
ct-samplesize/
├── SKILL.md              ← skill definition (bilingual, concise)
├── README.md             ← ClawHub recommended
├── AGENTS.md             ← this file (core rules)
├── assets/
│   └── icon.svg          ← skill icon (104×104)
├── scripts/
│   └── samplesize_power.py  ← Python calc + auto R code gen
└── references/
    ├── r_packages_zh.md     ← R package reference (20+ pkgs, bilingual)
    ├── formulas_zh.md       ← formula reference (bilingual)
    ├── python_usage.md      ← Python quick ref (bilingual)
    ├── r_usage.md           ← R quick ref (bilingual)
    ├── effect_size.md       ← effect size standards (bilingual)
    ├── report_template.md   ← report template (bilingual)
    └── examples.md          ← 3 full examples (bilingual output + R code)
```

---

## Dependencies / 依赖
- Python: statsmodels >= 0.14, numpy >= 1.24, scipy >= 1.11
- R: rpact >= 4.0, gsDesign >= 3.5, TrialSize >= 1.1

---
name: ct-samplesize
cn_name: 临床样本量与检验效能计算专家 / Clinical Sample Size Expert
version: 1.0.0
required_commands: [Rscript, python]
required_environment_variables: []
required_privileges: non-root
description: "Skill for clinical trial sample size & power calculation. Simple designs (t-test/ANOVA/proportion) support dual R/Python code; advanced designs (group sequential/adaptive/platform trial/bioequivalence) fully R-based; every analysis mandates standalone reproducible R code for user verification. | 本技能专用于解决临床试验相关的样本量与检验效能计算问题，简单的计算(t检验/方差分析/率比较)支持R和Python双代码，高级设计方法(组序贯/适应性/多臂平台/生物等效性)则完全基于R进行，每次分析强制输出可独立运行的R代码供用户核查和复现结果。"
triggers:
  - "sample size"
  - "power analysis"
  - "effect size"
  - "interim analysis"
  - "adaptive design"
  - "group sequential"
  - "platform trial"
  - "survival analysis"
  - "临床 trial"
  - "样本量"
  - "检验效能"
  - "效应量"
  - "期中分析"
  - "适应性设计"
  - "非劣效"
  - "等效性"
  - "生物等效性"
  - "组序贯"
  - "多臂试验"
  - "剂量递增"
  - "生存分析"
metadata:
  openclaw: { emoji: "📊", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  version: "1.0.0"
  license: "MIT"
  tags: [clinical-trial, sample-size, power, statistics, biostatistics, R, experimental-design, interim-analysis, adaptive-design, group-sequential, bioequivalence]
  homepage: "https://github.com/medstatstar/ct-samplesize"
  hermes: { platform: "Windows, macOS, Linux", required_binaries: [Rscript, python] }
  required_binaries: [Rscript, python]
---

# CT Sample Size & Power / 临床样本量与检验效能计算专家

> Detect environment → recommend optimal tools → calculate & explain | 自动检测环境 → 推荐最优工具 → 完成计算与解释
>
> **🔴 Mandatory Rule | 强制规则**: Every analysis must include standalone, reproducible R code. | 每次分析都必须附带可独立运行的原始 R 代码。

---

## Language Detection / 语言检测

**EN:** Detect from `<response_language>` tag or user input. Respond in the **same language**. All templates below are bilingual — use the matching version.

**CN:** 从 `<response_language>` 标签或用户输入语言自动检测用户语言，并用**同一种语言**回复。以下所有输出模板均为中英双语，选择与用户语言一致的版本。

---

## Requirements / 要求

| Requirement 要求 | Details 详情 |
|:-----------|:-----------|
| **R** | ≥ 3.6.0（推荐 ≥ 4.1.0）+ rpact, gsDesign, TrialSize, pwr, PowerTOST |
| **Python** | ≥ 3.8 + statsmodels ≥ 0.14, numpy ≥ 1.24, scipy ≥ 1.11 |
| **OS** | Windows / macOS / Linux |
| **Privileges 权限** | non-root（所有计算在用户空间完成）|

---

## Phase 1: Environment Detection / 环境检测

**Step 1 — Detect R / 检测 R** (System PATH → Default path → Registry query)

| R Status | Behavior |
|:---------|:---------|
| **Installed 已安装** | Report version + check packages |
| **Not Installed 未安装** | ⚠️ Strongly recommend install + offer Python fallback |
| **Refused 被拒** | ⚠️ Python for simple designs only; explain limitations |

**Step 2 — Collect Requirements / 收集需求**

| Parameter | Example |
|:----------|:--------|
| Design Type 设计类型 | Parallel / Crossover / Group Sequential |
| Primary Endpoint 主要终点 | Continuous / Binary / Time-to-Event |
| Hypothesis 假设检验 | Superiority / Non-inferiority / Equivalence |
| Effect 期望效应 | HR=0.75 / Cohen's d=0.5 |
| α, power | Two-sided 0.05 / 0.85 |
| Dropout Rate 脱落率 | 10% |

> **EN/CN:** 参数缺失时先给默认值(α=0.05, power=0.80)的初步结果，再逐步调参。| When parameters are missing, provide preliminary results with defaults, then iteratively refine.

---

## Phase 2: Tool Selection / 工具选择

```
User need
├── "Simple" 简单设计 → Python ✅ (Two means / Proportions / Non-inferiority / Survival simplified)
├── "Complex" 复杂设计 → R required ⭐
│   ├── Group Sequential → gsDesign / rpact
│   ├── Adaptive Design → rpact
│   ├── MAMS / Platform Trial → gsMAMS / NCC
│   ├── Bioequivalence → PowerTOST
│   └── Exact Survival → rpact / gsDesign
└── "Cross-validation / Submission" 交叉验证 → Python + R combined
```

---

## Phase 3: Result Standards / 结果标准

> **🔴 EN/CN:** Regardless of calculation path (Python/R/both), every analysis MUST include **standalone, reproducible R code**.

| Item 项目 | Mandatory 强制性 |
|:---------|:----------------:|
| Input Parameters 输入参数 | ✅ |
| Calculation Result 计算结果 | ✅ |
| Interpretation 结果解释 | ✅ |
| **Reproducible R Code 可复现R代码** | 🔴 Mandatory 强制 |
| Assumptions 前提假设 | ✅ |
| Dropout Adjustment 脱落调整 | ✅ |

---

## Implementation / 实施

### Python (Simple Designs / 简单设计)

**EN:** Run via CLI, auto-generate R code. Full docs: `references/python_usage.md`
**CN:** 通过 CLI 执行，自动生成 R 代码。详见 `references/python_usage.md`

```bash
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --alpha 0.05 --power 0.9
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
python scripts/samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80
```

### R (Complex Designs / 复杂设计)

| Scenario 场景 | R Package | Function |
|:--------------|:----------|:---------|
| Two means 两均数 | TrialSize | `NTwoMeans(α, β, delta, sigma)` |
| Group Sequential 组序贯 | gsDesign | `gsSurv(k=3, sfu=sfLDOF)` |
| Adaptive 适应性 | rpact | `getSampleSizeMeans(adaptation="onesided")` |
| Bioequivalence 生物等效 | PowerTOST | `sampleN.TOST(theta0=0.95, CV=0.25)` |

**EN:** Full R docs: `references/r_usage.md` | Package map: `references/r_packages_zh.md`
**CN:** R 完整文档：`references/r_usage.md` | 包名映射：`references/r_packages_zh.md`

---

## Formula & Report / 公式与报告

**Formulas 公式推导:** `references/formulas_zh.md`

| Scenario | Formula |
|:---------|:--------|
| Independent t (equal) | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| Proportion (arcsin) | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| Survival (Schoenfeld) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |

**Effect size standards:** `references/effect_size.md`

**Report template (含强制 R 代码块):** `references/report_template.md`

```r
# ---- Parameters 参数设置 ----
alpha <- [value]; power <- [value]; effect <- [value]
# ---- Calculation 计算 ----
[core function call]
# ---- Dropout Adjustment 脱落调整 ----
n_adj <- ceiling(n / (1 - dropout_rate))
```

---

## Common Errors / 常见错误

| Error 错误 | Fix 解决 |
|:----------|:--------|
| "Rscript not found" | Install R or specify path |
| "package not found" | install.packages("xxx") |
| ImportError: statsmodels | Anaconda: pip install statsmodels |

---

## Usage Examples / 使用示例

**EN:** See `references/examples.md` for 3 complete walkthroughs (proportion / group sequential / non-inferiority) with bilingual output + R code.

**CN:** 详见 `references/examples.md`（率比较/组序贯/非劣效 3 个完整示例，含双语输出 + R 代码）。

---

## References / 参考文献

- rpact: https://www.rpact.org/
- gsDesign: https://keaven.github.io/gsDesign/
- TrialSize: https://cran.r-project.org/web/packages/TrialSize/
- PowerTOST: https://cran.r-project.org/web/packages/PowerTOST/
- CRAN ClinicalTrials View: https://cran.r-project.org/web/views/ClinicalTrials.html

**Version 版本**: v1.0.0 | **Created 创建**: 2026-07-12 | **License 许可**: MIT-0

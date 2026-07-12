---
name: ct-samplesize
cn_name: 临床样本量与检验效能计算专家 / Clinical Sample Size Expert
version: 3.1.0
required_commands: [Rscript, python]
required_environment_variables: []
required_privileges: non-root
description: "Clinical trial sample size & power expert (v3.1): 18 test types, bilingual EN/CN, R code on demand. | 临床试验样本量计算专家(v3.1)：18种检验，中英双语，R代码按需索取。"
triggers:
  - "sample size"
  - "power analysis"
  - "样本量"
  - "检验效能"
  - "样本量计算"
  - "临床 trial"
  - "统计设计"
  - "mixed model"
  - "repeated measures"
  - "diagnostic trial"
  - "cluster randomized"
  - "vaccine efficacy"
  - "dose escalation"
  - "Bayesian design"
  - "混合模型"
  - "重复测量"
  - "诊断试验"
  - "类随机"
  - "疫苗效力"
  - "剂量递增"
  - "贝叶斯设计"
  - "期中分析"
  - "适应性设计"
  - "非劣效"
  - "等效性"
  - "生物等效性"
  - "组序贯"
  - "多臂试验"
  - "生存分析"
  - "interim analysis"
  - "adaptive design"
  - "group sequential"
  - "platform trial"
  - "survival analysis"
  - "bioequivalence"
metadata:
  openclaw: { emoji: "📊", icon: "assets/icon.svg" }
  authors: ["medstatstar", "phoe-zip"]
  version: "3.1.0"
  license: "MIT-0"
  tags: [clinical-trial, sample-size, power, statistics, biostatistics, R, experimental-design, interim-analysis, adaptive-design, group-sequential, bioequivalence, mixed-model, diagnostic-trial, cluster-randomized, bland-altman, poisson, vaccine-efficacy, dose-escalation, bayesian]
  homepage: "https://github.com/medstatstar/ct-samplesize"
  hermes: { platform: "Windows, macOS, Linux", required_binaries: [Rscript, python] }
  required_binaries: [Rscript, python]
  permissions:
    scope: "user-space-only"
    network: "none"
    filesystem: "read-only (except temp R script)"
    execution: "R code execution requires explicit user confirmation (-y/--yes)"
    data: "no external data transmission"
---

# CT Sample Size & Power / 临床样本量与检验效能计算专家

> Auto detect → recommend optimal tools → calculate & explain | 自动检测环境 → 推荐最优工具 → 完成计算与解释
>
> **📋 Output Rule | 输出规则**: 每次分析必须给出完整结果报告（参数 + 结论 + 解释）。可复现 R 代码默认**不展示**，仅在用户明确要求时提供。 | Every analysis must include a complete report (parameters + results + interpretation). Reproducible R code is **hidden by default** and provided only when the user explicitly requests it.

---

## Purpose / 技能目的

**EN:** This skill is a specialized **clinical trial sample size & power calculation expert** supporting **18 test types** covering all major clinical trial scenarios. It auto-detects the user's R environment, recommends the optimal calculation path, and delivers a complete results report. Reproducible R code is available on demand. Supports bilingual EN/CN with automatic language detection. Menu-driven selection for rapid navigation.

**CN:** 本技能是专用于**临床试验样本量与检验效能计算**的专家级工具，支持 **18 种检验类型**，覆盖全部主要临床试验场景。自动检测用户 R 环境，推荐最优计算路径，输出完整结果报告。可复现 R 代码按需索取。中英双语自动切换。菜单式引导快速定位功能。

---

## Language Detection / 语言检测

**EN:** Detect from `<response_language>` tag or user input. Respond in the **same language**. All templates below are bilingual — use the matching version.

**CN:** 从 `<response_language>` 标签或用户输入语言自动检测，用**同一种语言**回复。以下模板均为中英双语，选择对应版本。

---

## 🔷 Quick Menu / 快速引导菜单

> **Step 1 — Select primary endpoint type:** | **第一步 — 选择主要终点类型：**

| Category 类别 | Test Type 检验类型 | Clinical Scenario 临床场景 | R 包 / 方法 |
|:---|:---|:---|:---|
| **Continuous 连续变量** | `ttest_ind` | 两均数比较（平行设计） | `pwr`, `TrialSize` |
| | `ttest_paired` | 配对t / 交叉设计2×2 | `pwr`, `TrialSize` |
| | `anova` | 多组比较（k组） | `pwr`, `TrialSize` |
| | `equivalence` | 等效性检验（均数） | `TrialSize` |
| | `mixed_model` | **重复测量 / 纵向数据** | `simr` |
| **Binary 二分类** | `proportion_one` | 单组率检验 | `pwr` |
| | `proportion_two` | 两组率比较（卡方） | `pwr`, `TrialSize` |
| | `non_inferiority` | 非劣效设计（率） | `TrialSize` |
| | `be_tost` | **生物等效性 (TOST)** | `PowerTOST` |
| **计数/事件率** | `poisson` | **Poisson率 / 复发性事件** | Wald 检验 |
| | `vaccine_efficacy` | **疫苗效力** | Halloran 公式 |
| **Time-to-Event 生存** | `survival` | 生存分析（简化） | Schoenfeld 公式 |
| | `survival_exact` | 生存分析（精确） | `rpact` |
| **诊断/方法学** | `roc` | **ROC曲线 / 诊断试验** | `pROC` |
| | `bland_altman` | **Bland-Altman方法学比对** | Lu et al. 公式 |
| **特殊设计** | `cluster` | **类随机设计** | DEFF 公式 |
| | `multiple_endpoints` | **多终点 / 复合终点** | 相关系数法 |
| | `bayesian` | **贝叶斯设计** | `BayesCTDesign` |
| | `dose_escalation` | **剂量递增 (I期)** | `escalation` |
| | `group_sequential` | **组序贯 / 期中分析** | `gsDesign`, `rpact` |
| | `adaptive` | **适应性设计** | `rpact` |

> **Step 2 — If unsure, answer these three questions:** | **第二步 — 如不确定，回答以下三个问题：**

1. **Primary endpoint type?** (Continuous / Binary / Time-to-Event / Count / Other)
   **主要终点类型？** (连续 / 二分类 / 生存 / 计数 / 其他)
2. **Hypothesis?** (Superiority / Non-inferiority / Equivalence / Other)
   **假设检验？** (优效 / 非劣效 / 等效 / 其他)
3. **Design complexity?** (Parallel / Paired / Repeated / Cluster / Other)
   **设计复杂度？** (平行 / 配对 / 重复测量 / 类随机 / 其他)

---

## Requirements / 要求

| Requirement 要求 | Details 详情 |
|:-----------|:-----------|
| **R** | ≥ 4.1.0 + rpact, gsDesign, TrialSize, pwr, PowerTOST, simr, pROC, BlandAltmanLeh, BayesCTDesign, escalation |
| **Python** | ≥ 3.8 + statsmodels==0.14.2, numpy==1.24.3, scipy==1.11.4 |
| **Privileges 权限** | non-root（所有计算在用户空间完成）|

## ⚠️ User Warnings / 用户安全提示

**EN:**
- This skill generates and executes R code locally on your machine.
- Review all R code BEFORE execution (use `--dry-run` first).
- Never paste untrusted parameters into CLI arguments.
- Outputs are for reference only; validate results before using in regulatory submissions.
- R execution requires explicit `-y`/`--yes` flag confirmation.

**CN:**
- 本技能会在你的机器本地生成并执行 R 代码。
- 执行前务必先审查所有 R 代码（先用 `--dry-run` 查看）。
- 不要将不受信任的参数粘贴到命令行参数中。
- 输出仅供参考，用于监管申报前需独立验证结果。
- R 执行需要显式的 `-y`/`--yes` 标志确认。

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
| Design Type 设计类型 | Parallel / Crossover / Group Sequential / Longitudinal |
| Primary Endpoint 主要终点 | Continuous / Binary / Time-to-Event / Count |
| Hypothesis 假设检验 | Superiority / Non-inferiority / Equivalence |
| Effect 期望效应 | HR=0.75 / Cohen's d=0.5 / AUC=0.75 |
| α, power | Two-sided 0.05 / 0.85 |
| Dropout Rate 脱落率 | 10% |

> **EN/CN:** 参数缺失时先给默认值(α=0.05, power=0.80)的初步结果，再逐步调参。

---

## Phase 2: Tool Selection / 工具选择

```
User need
├── "Simple" → Python ✅ (auto-generate R code)
│   ├── ttest_ind, ttest_paired, anova
│   ├── proportion_one, proportion_two
│   ├── non_inferiority (prop, approx)
│   ├── survival (Schoenfeld approx)
│   └── roc, bland_altman (formula)
│
├── "Advanced" → R required ⭐
│   ├── Group Sequential → gsDesign / rpact
│   ├── Adaptive Design → rpact
│   ├── Mixed Model (repeated measures) → simr
│   ├── Bioequivalence → PowerTOST
│   ├── Exact Survival → rpact / gsDesign
│   ├── Poisson Rate → Wald test
│   ├── Cluster Randomized → DEFF method
│   ├── Vaccine Efficacy → Halloran formula
│   ├── Multiple Endpoints → correlation method
│   ├── Bayesian Design → BayesCTDesign
│   └── Dose Escalation → escalation
│
└── "Cross-validation" → Python + R combined
```

---

## Phase 3: Result Standards / 结果标准

> **📋 Output Rule | 输出规则**: 每次分析必须给出完整结果报告（参数 + 结论 + 解释）。可复现 R 代码默认**不展示**，仅在用户明确要求时提供。

| Item 项目 | Mandatory 强制性 | Default 默认 |
|:---------|:----------------:|:---------:|
| Input Parameters 输入参数 | ✅ | ✅ 展示 |
| Calculation Result 计算结果 | ✅ | ✅ 展示 |
| Interpretation 结果解释 | ✅ | ✅ 展示 |
| Assumptions 前提假设 | ✅ | ✅ 展示 |
| Dropout Adjustment 脱落调整 | ✅ | ✅ 展示 |
| Reproducible R Code 可复现R代码 | ✅ | ❌ **隐藏**（用户要求时提供） |

**R 代码触发短语 / R Code Trigger Phrases:**
| 中文 | English |
|:------|:---------|
| "带代码" | "with R code" |
| "输出R代码" | "output R code" |
| "给代码" | "show me the code" |
| "review 一下代码" | "review the code" |
| "展示R code" | "display R code" |
| "我需要复现代码" | "I need the code" |
| "coderef" (缩写) | "R code please" |

**使用触发短语时的行为:**
1. 展示完整可运行的 R 代码
2. 确保代码包含所有必要注释和包引用
3. 同时仍提供文字解释

---

## Implementation / 实施

**Full docs:** `references/extended_functions.md`

> **EN:** ℹ️ Default mode is dry-run (R code shown, NOT executed). Add `-y`/`--yes` to execute after reviewing.
> **CN:** ℹ️ 默认为 dry-run 模式（仅显示 R 代码，不执行）。添加 `-y`/`--yes` 在审查后执行。

```bash
# === Continuous / 连续变量 ===
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test ttest_paired --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.8
python scripts/samplesize_power.py --test equivalence --margin 2.0 --effect 3.0 --power 0.8
python scripts/samplesize_power.py --test mixed_model --effect 0.5 --nsim 500

# === Binary / 二分类 ===
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
python scripts/samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80 --power 0.8
python scripts/samplesize_power.py --test be_tost --theta0 0.95 --cv 0.25 --design "2x2"

# === Count / 计数 ===
python scripts/samplesize_power.py --test poisson --lambda1 0.05 --lambda2 0.03 --t1 2 --t2 2 --power 0.8
python scripts/samplesize_power.py --test vaccine_efficacy --ve_control 0.02 --ve_treatment 0.005 --power 0.8

# === Survival / 生存 ===
python scripts/samplesize_power.py --test survival --hazard_ratio 0.75 --power 0.85

# === Diagnostic / Method Comparison / 诊断/方法学比对 ===
python scripts/samplesize_power.py --test roc --auc0 0.5 --auc1 0.75 --power 0.8
python scripts/samplesize_power.py --test bland_altman --sd_diff 5 --w 2.5

# === Special Designs / 特殊设计 ===
python scripts/samplesize_power.py --test cluster --icc 0.05 --m 30 --n_indiv 64
python scripts/samplesize_power.py --test multiple_endpoints --effect 0.3 --correlation 0.5
python scripts/samplesize_power.py --test bayesian --prob_control 0.3 --prob_treatment 0.15 --prior_a0 0.5
python scripts/samplesize_power.py --test dose_escalation --n_doses 5 --target_dlt 0.33
```

---

## Formula & Report / 公式与报告

**Formulas:** `references/formulas_zh.md` | **Extended:** `references/extended_functions.md`

| Scenario | Formula |
|:---------|:--------|
| Independent t (equal) | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| Proportion (arcsin) | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| Survival (Schoenfeld) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |
| ROC (Obuchowski) | $n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{4(\arcsin\sqrt{AUC_1} - \arcsin\sqrt{AUC_0})^2}$ |
| Cluster DEFF | $DEFF = 1 + (m - 1) \times ICC$ |
| Bland-Altman | $n = 2(\frac{Z_{1-\alpha/2} \times SD_{diff}}{W})^2$ |

**Effect size:** `references/effect_size.md` | **Report template:** `references/report_template.md`

---

## Common Errors / 常见错误

| Error 错误 | Fix 解决 |
|:----------|:--------|
| "Rscript not found" | Install R or specify path |
| "package not found" | install.packages("xxx") |
| ImportError: statsmodels | Anaconda: pip install statsmodels |
| simr timeout | Reduce --nsim or simplify model |

---

## Usage Examples / 使用示例

See `references/examples.md` for complete walkthroughs with bilingual output + R code.

---

## References / 参考文献

- rpact: https://www.rpact.org/
- gsDesign: https://keaven.github.io/gsDesign/
- TrialSize: https://cran.r-project.org/web/packages/TrialSize/
- PowerTOST: https://cran.r-project.org/web/packages/PowerTOST/
- simr: https://github.com/pitakakariki/simr
- BayesCTDesign: https://cran.r-project.org/web/packages/BayesCTDesign/
- CRAN ClinicalTrials View: https://cran.r-project.org/web/views/ClinicalTrials.html

---

**Version**: v3.1.0 | **Created**: 2026-07-12 | **Updated**: 2026-07-12 | **License**: MIT-0

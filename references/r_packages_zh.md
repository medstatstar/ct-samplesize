# Clinical Sample Size — R Package Reference / 临床样本量计算 — R包参考指南

> **EN:** Based on CRAN [ClinicalTrials Task View](https://cran.r-project.org/web/views/ClinicalTrials.html)
> **CN:** 基于 CRAN [ClinicalTrials Task View](https://cran.r-project.org/web/views/ClinicalTrials.html)

---

## Quick Recommendation / 总体推荐

| Scenario 场景 | Package 包 | Python Alt? |
|:--------------|:-----------|:-----------:|
| t-test / ANOVA / Chi-square 基础检验 | `pwr`, `TrialSize` | ✅ |
| Adaptive Design 适应性设计 | `rpact` | ❌ R only |
| Group Sequential 组序贯设计 | `gsDesign`, `ldbounds` | ❌ R only |
| MAMS 多臂多阶段 | `gsMAMS`, `MAMS` | ❌ R only |
| I期剂量递增 CRM/BOIN | `escalation`, `BOIN` | ❌ R only |
| Survival (exact) 精确生存分析 | `rpact`, `gsDesign` | ⚠️ Limited |
| Bioequivalence 生物等效性 | `PowerTOST` | ❌ R only |
| Bayesian Trial 贝叶斯试验 | `BayesCTDesign` | ❌ R only |
| Platform Trial 平台试验 | `NCC`, `cats` | ❌ R only |
| Trial Simulation 试验模拟 | `TrialSimulator` | ❌ R only |
| Blinded SSR 盲态样本量重算 | `blindrecalc` | ❌ R only |

---

## Core Package Details / 核心包详解

### 1. rpact — Adaptive & Group Sequential / 适应性与组序贯

```r
install.packages("rpact")
library(rpact)

# Continuity endpoint sample size / 连续性终点
getSampleSizeMeans(alpha=0.025, beta=0.2, normalApproximation=FALSE,
                   alternative=0.5, stDev=1, groups=2)

# Survival endpoint / 生存终点
getSampleSizeSurvival(alpha=0.025, beta=0.1, hazardRatio=0.7,
                      accrualTime=12, followUpTime=12)

# Group sequential design / 组序贯设计
getDesignGroupSequential(kMax=3, alpha=0.025, beta=0.2,
                         informationRates=c(0.33,0.67,1),
                         typeOfDesign="asOF")
```

**Key functions:** `getSampleSizeMeans()`, `getSampleSizeRates()`, `getSampleSizeSurvival()`, `getDesignGroupSequential()`, `getDesignInverseNormal()`, `getAnalysisResults()`, `getSimulationResults()`

---

### 2. gsDesign — Group Sequential Design / 组序贯设计

```r
install.packages("gsDesign")
library(gsDesign)

# Group sequential survival / 生存组序贯
gsSurv(k=3, alpha=0.025, beta=0.1, hr=0.7, R=12, T=36, minfup=24)

# Generic group sequential / 通用组序贯
gsDesign(k=4, delta=0.3, sfu=sfLDOF, test.type=2)
```

**Key functions:** `gsDesign()`, `gsSurv()`, `gsBinomial()`, `toInteger()`

**Spending functions:** `sfHSD()` (Hwang-Shih-DeCani), `sfLDPocock()` (Pocock-like), `sfLDOF()` (O'Brien-Fleming-like), `sfLinear()`, `sfExponential()`

---

### 3. TrialSize — Comprehensive (80+ functions) / 全面样本量

```r
install.packages("TrialSize")
library(TrialSize)

NTwoMeans(alpha=0.05, beta=0.2, delta=0.5, sigma=1)
NTwoArmRates(alpha=0.05, beta=0.2, p1=0.3, p2=0.15, delta=0)
NSurvival(alpha=0.05, beta=0.2, t=24, lambda1=0.05, lambda2=0.03)
NPropTwoSidedNonInferiority(alpha=0.025, beta=0.2, pe=0.8, pc=0.8, delta=0.1)
NRepeatedANOVA(alpha=0.05, beta=0.2, delta=0.5, sigma=1, n.reps=4, rho=0.5)
NClusteredTwoArmMeans(alpha=0.05, beta=0.2, delta=0.5, m=30, icc=0.05)
```

**Key functions:** `NTwoMeans()`, `NTwoArmRates()`, `NMultipleArmMeans()`, `NSurvival()`, `NOneArmSurvival()`, `NOneMean()`, `NPropComp()`, `NPropTwoSidedNonInferiority()`, `NPropTwoSidedEquivalence()`, `NMeansTwoSidedNonInferiority()`, `NSurvivalNonInferiority()`, `NSubjectCrossOver2x2()`, `NRepeatedANOVA()`, `NClusteredTwoArmMeans()`, `NDOR()`, `NRiskDiff()`, `NRiskRatio()`, `NHazardRatio()`, `NTimeToEvent()`, `NLogRank()`

---

### 4. PowerTOST — Bioequivalence / 生物等效性

```r
install.packages("PowerTOST")
library(PowerTOST)

# 2x2x2 crossover / 两序列两周期交叉
sampleN.TOST(theta0=0.95, theta1=0.80, theta2=1.25, CV=0.25, design="2x2")

# Partial replicate / 部分重复交叉
sampleN.TOST(theta0=0.95, CV=0.30, design="2x3x3", targetpower=0.9)

# Parallel design / 平行设计
sampleN.TOST(theta0=0.95, CV=0.35, design="parallel")
```

---

### 5. pwr — Basic Power Analysis (Teaching) / 基础功效分析

```r
install.packages("pwr")
library(pwr)

pwr.t.test(d=0.5, power=0.8, sig.level=0.05, type="two.sample")
pwr.anova.test(k=3, f=0.25, sig.level=0.05, power=0.8)
pwr.chisq.test(w=0.3, df=3, sig.level=0.05, power=0.8)
pwr.p.test(h=0.3, sig.level=0.05, power=0.8)
pwr.2p.test(h=0.3, sig.level=0.05, power=0.8)
```

---

### 6. Other Packages / 其他推荐包

| Package 包 | Scenario 场景 | Key Function |
|:-----------|:-------------|:-------------|
| `longpower` | Longitudinal / Mixed models 纵向数据 | `power.mmrm()` |
| `MKpower` | Multiple tests 多种检验 | `power.welch.test()` |
| `presize` | CI precision based 精度导向 | `precisely::prec_t()` |
| `blindrecalc` | Blinded SSR 盲态重算 | `ssr_blinded()` |
| `BayesCTDesign` | Bayesian adaptive 贝叶斯适应性 | `bayes_ct_design()` |
| `lrstat` | Non-phrhazard Log-rank 非比例风险 | `lrstat()` |
| `ssanv` | Non-compliance adjust 非依从性 | `ssanv()` |
| `pmvalsampsize` | Prediction model validation | `pmvalsampsize()` |

---

## Quick Map: Scenario→R Function / 常见场景→R函数映射

| Clinical Scenario 临床场景 | R Code 代码片段 |
|:---------------------------|:---------------|
| Two means (fixed) | `TrialSize::NTwoMeans(α, β, delta, sigma)` |
| Two proportions (Chi-sq) | `TrialSize::NTwoArmRates(α, β, p1, p2, delta)` |
| ANOVA (k groups) | `TrialSize::NMultipleArmMeans(α, β, k, means, sigma)` |
| Survival (1 interim + final) | `rpact::getSampleSizeSurvival(α, β, hr=0.7)` |
| Group sequential (3-stage, OBF) | `gsDesign::gsSurv(k=3, sfu=sfLDOF)` |
| Non-inferiority (rate) | `TrialSize::NPropTwoSidedNonInferiority(α, β, pe, pc, delta)` |
| Bioequivalence | `PowerTOST::sampleN.TOST(theta0, CV=0.25)` |
| 2×2 Crossover | `TrialSize::NSubjectCrossOver2x2(α, β, delta, sigma)` |
| Repeated measures | `TrialSize::NRepeatedANOVA(α, β, delta, sigma, n.reps=4)` |
| Cluster randomization | `TrialSize::NClusteredTwoArmMeans(α, β, delta, m, icc)` |
| Platform trial | `cats::cats_design()` |
| Dose escalation I期 | `escalation::get_design("crmloc")` |
| Sample size re-estimation | `rpact::getSampleSizeMeans(adaptation="onesided")` |

---

## Installation / 安装命令

```r
install.packages(c(
  "rpact",        # Adaptive + Group Seq 适应性+组序贯
  "gsDesign",     # Classical Group Seq 经典组序贯
  "TrialSize",    # Comprehensive 全面样本量
  "pwr",          # Teaching / Demo 教学用例
  "PowerTOST",    # Bioequivalence 生物等效性
  "longpower",    # Longitudinal 纵向数据
  "MKpower",      # Multiple tests 多种检验
  "presize",      # CI precision 精度导向
  "blindrecalc"   # Blinded SSR 盲态重算
))
```

---

## Python↔R Correspondence / Python↔R 对应关系

| Python (statsmodels/scipy) | R | Notes 说明 |
|:--------------------------|:-|:-----------|
| `TTestPower.solve_power()` | `pwr.t.test()` | One-sample/paired t |
| `TTestIndPower.solve_power()` | `pwr.t.test(type="two.sample")` | Independent t |
| `FTestAnovaPower.solve_power()` | `pwr.anova.test()` | ANOVA |
| arcsin + t | `pwr.p.test()` | Proportion (approx) |
| —— | `rpact::getSampleSize*()` | **Group seq / Adaptive (no Python alt)** |
| —— | `gsDesign` | **Group sequential (no Python alt)** |
| —— | `TrialSize` | **Full coverage (80+ functions)** |

---

_Document version: 2026-07 | Data source: CRAN ClinicalTrials Task View_

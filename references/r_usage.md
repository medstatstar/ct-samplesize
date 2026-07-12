# R Implementation Reference / R 实施参考

> **EN:** R path for exact & complex designs (group sequential, adaptive, platform trials).
> **CN:** R 路径用于精确 & 复杂设计（组序贯、适应性、平台试验）。

---

## Environment / 环境要求

| Item | Requirement |
|:-----|:------------|
| R version | ≥ 3.6.0 (recommended ≥ 4.1.0) |
| Install | CRAN binary |
| Windows path | `C:\Tools\R-4.5.1\bin\x64\Rscript.exe` |

---

## Execution Template / 执行模板

```python
import subprocess

script = """
library(rpact)
result <- getSampleSizeMeans(
  alpha = 0.025, beta = 0.2, normalApproximation = FALSE,
  alternative = 0.5, stDev = 1, groups = 2,
  allocationRatioPlanned = 1
)
print(getDesignSampleSizeArrays(result))
"""

with open(r"C:\temp\clin_calc.R", "w", encoding="utf-8") as f:
    f.write(script)

result = subprocess.run(
    [r"C:\Tools\R-4.5.1\bin\x64\Rscript.exe", r"C:\temp\clin_calc.R"],
    capture_output=True, text=True, timeout=60,
    creationflags=subprocess.CREATE_NO_WINDOW
)
print(result.stdout)
```

---

## Scenario→R Package Mapping / 场景→R包映射

| Scenario 场景 | R Package | Function |
|:--------------|:----------|:---------|
| Two means 两均数 | TrialSize | `NTwoMeans(α, β, delta, sigma)` |
| Group Seq (survival) 组序贯(生存) | gsDesign | `gsSurv(k=3, sfu=sfLDOF)` |
| Adaptive 适应性 | rpact | `getSampleSizeMeans(adaptation="onesided")` |
| Bioequivalence 生物等效性 | PowerTOST | `sampleN.TOST(theta0=0.95, CV=0.25)` |
| Platform trial 平台试验 | NCC | `NCC::ncc_design()` |

---

## Code Snippets / 代码片段

### 1. Two Means / 两组均数

```r
library(TrialSize); library(pwr)
result <- NTwoMeans(alpha=0.05, beta=0.2, delta=0.5, sigma=1)
print(result)
pwr.t.test(d=0.5, power=0.8, sig.level=0.05, type="two.sample")
```

### 2. Group Sequential / 组序贯

```r
library(gsDesign)
x <- gsSurv(k=3, alpha=0.025, beta=0.1, hr=0.7, R=12, T=36, minfup=12)
print(x)
cat("Events:", x$events, "\n")
cat("Max N:", x$n.I[x$k], "\n")
```

### 3. Adaptive / 适应性

```r
library(rpact)
design <- getDesignGroupSequential(
  kMax = 3, alpha = 0.025, beta = 0.2,
  informationRates = c(0.33, 0.67, 1),
  typeOfDesign = "asOF"
)
result <- getSampleSizeMeans(
  design = design, normalApproximation = FALSE,
  alternative = 0.5, stDev = 1
)
print(getDesignSampleSizeArrays(result))
```

### 4. Non-inferiority / 非劣效

```r
library(TrialSize)
result <- NPropTwoSidedNonInferiority(
  alpha = 0.025, beta = 0.2,
  pe = 0.65, pc = 0.70, delta = 0.10, ratio = 1
)
print(result)
```

### 5. Bioequivalence / 生物等效性

```r
library(PowerTOST)
sampleN.TOST(
  theta0 = 0.95, theta1 = 0.80, theta2 = 1.25,
  CV = 0.25, design = "2x2", alpha = 0.05, targetpower = 0.8
)
```

### 6. Survival (simplified vs exact)

```r
# Simplified Schoenfeld / 简化公式
# d = (Z_alpha/2 + Z_beta)^2 / (log HR)^2

# R exact (rpact) / R 精确法
library(rpact)
result <- getSampleSizeSurvival(
  alpha = 0.05, beta = 0.2, hazardRatio = 0.7,
  accrualTime = 12, followUpTime = 12, maxNumberOfSubjects = 1000
)
print(result)
```

---

## Python↔R Correspondence / Python↔R 对应关系

| Python (statsmodels/scipy) | R | Notes 说明 |
|:--------------------------|:-|:-----------|
| `TTestPower.solve_power()` | `pwr.t.test()` | One-sample/paired t |
| `TTestIndPower.solve_power()` | `pwr.t.test(type="two.sample")` | Independent t |
| `FTestAnovaPower.solve_power()` | `pwr.anova.test()` | ANOVA |
| arcsin + t test | `pwr.p.test()` | Proportion (approx) |
| —— | `rpact::getSampleSize*()` | **Group seq / Adaptive (no Python alt)** |
| —— | `gsDesign` | **Group sequential (no Python alt)** |
| —— | `TrialSize` | **Full coverage (80+ functions)** |

---

## R Package Installation / R 包安装

```r
install.packages(c(
  "rpact",        # Adaptive + Group Seq
  "gsDesign",     # Classical Group Seq
  "TrialSize",    # Comprehensive
  "pwr",          # Teaching/demo
  "PowerTOST",    # Bioequivalence
  "longpower",    # Longitudinal
  "MKpower",      # Multiple tests
  "presize",      # Precision-focused
  "blindrecalc"   # Blinded SSR
))
```

> Full R package reference (20+ packages): `references/r_packages_zh.md`

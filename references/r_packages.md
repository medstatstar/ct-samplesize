# Clinical Sample Size — R Package Reference

> Based on CRAN [ClinicalTrials Task View](https://cran.r-project.org/web/views/ClinicalTrials.html)

---

## Quick Recommendation

| Scenario | Package | Python Alt? |
|:--------------|:-----------|:-----------:|
| t-test / ANOVA / Chi-square | `pwr`, `TrialSize` | ✅ |
| Adaptive Design | `rpact` | ❌ R only |
| Group Sequential | `gsDesign`, `ldbounds` | ❌ R only |
| MAMS | `gsMAMS`, `MAMS` | ❌ R only |
| I CRM / BOIN | `escalation`, `BOIN` | ❌ R only |
| Survival (exact) | `rpact`, `gsDesign` | ⚠️ Limited |
| Bioequivalence | `PowerTOST` | ❌ R only |
| Bayesian Trial | `BayesCTDesign` | ❌ R only |
| Platform Trial | `NCC`, `cats` | ❌ R only |
| Trial Simulation | `TrialSimulator` | ❌ R only |
| Blinded SSR | `blindrecalc` | ❌ R only |

---

## Core Package Details

### 1. rpact — Adaptive & Group Sequential

```r
install.packages("rpact")
library(rpact)

# Continuity endpoint sample size
getSampleSizeMeans(alpha=0.025, beta=0.2, normalApproximation=FALSE,
                   alternative=0.5, stDev=1, groups=2)

# Survival endpoint
getSampleSizeSurvival(alpha=0.025, beta=0.1, hazardRatio=0.7,
                      accrualTime=12, followUpTime=12)

# Group sequential design
getDesignGroupSequential(kMax=3, alpha=0.025, beta=0.2,
                         informationRates=c(0.33,0.67,1),
                         typeOfDesign="asOF")
```

**Key functions:** `getSampleSizeMeans()`, `getSampleSizeRates()`, `getSampleSizeSurvival()`, `getDesignGroupSequential()`, `getDesignInverseNormal()`, `getAnalysisResults()`, `getSimulationResults()`

---

### 2. gsDesign — Group Sequential Design

```r
install.packages("gsDesign")
library(gsDesign)

# Group sequential survival
gsSurv(k=3, alpha=0.025, beta=0.1, hr=0.7, R=12, T=36, minfup=24)

# Generic group sequential
gsDesign(k=4, delta=0.3, sfu=sfLDOF, test.type=2)
```

**Key functions:** `gsDesign()`, `gsSurv()`, `gsBinomial()`, `toInteger()`

**Spending functions:** `sfHSD()` (Hwang-Shih-DeCani), `sfLDPocock()` (Pocock-like), `sfLDOF()` (O'Brien-Fleming-like), `sfLinear()`, `sfExponential()`

---

### 3. TrialSize — Comprehensive (80+ functions)

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

### 4. PowerTOST — Bioequivalence

```r
install.packages("PowerTOST")
library(PowerTOST)

# 2x2x2 crossover
sampleN.TOST(theta0=0.95, theta1=0.80, theta2=1.25, CV=0.25, design="2x2")

# Partial replicate
sampleN.TOST(theta0=0.95, CV=0.30, design="2x3x3", targetpower=0.9)

# Parallel design
sampleN.TOST(theta0=0.95, CV=0.35, design="parallel")
```

---

### 5. pwr — Basic Power Analysis (Teaching)

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

### 6. Other Packages

| Package | Scenario | Key Function |
|:-----------|:-------------|:-------------|
| `longpower` | Longitudinal Mixed models | `power.mmrm()` |
| `MKpower` | Multiple tests | `power.welch.test()` |
| `presize` | CI precision based | `precisely::prec_t()` |
| `blindrecalc` | Blinded SSR | `ssr_blinded()` |
| `BayesCTDesign` | Bayesian adaptive | `bayes_ct_design()` |
| `lrstat` | Non-proportional hazard Log-rank | `lrstat()` |
| `ssanv` | Non-compliance adjust | `ssanv()` |
| `pmvalsampsize` | Prediction model validation | `pmvalsampsize()` |

---

## Quick Map: Scenario → R Function

| Clinical Scenario | R Code |
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
| Dose escalation I | `escalation::get_design("crmloc")` |
| Sample size re-estimation | `rpact::getSampleSizeMeans(adaptation="onesided")` |

---

## Installation

```r
install.packages(c(
  "rpact",        # Adaptive + Group Seq
  "gsDesign",     # Classical Group Seq
  "TrialSize",    # Comprehensive
  "pwr",          # Teaching / Demo
  "PowerTOST",    # Bioequivalence
  "longpower",    # Longitudinal
  "MKpower",      # Multiple tests
  "presize",      # CI precision
  "blindrecalc"   # Blinded SSR
))
```

---

## Python ↔ R Correspondence

| Python (statsmodels/scipy) | R | Notes |
|:--------------------------|:-|:-----------|
| `TTestPower.solve_power()` | `pwr.t.test()` | One-sample/paired t |
| `TTestIndPower.solve_power()` | `pwr.t.test(type="two.sample")` | Independent t |
| `FTestAnovaPower.solve_power()` | `pwr.anova.test()` | ANOVA |
| arcsin + t | `pwr.p.test()` | Proportion (approx) |
| N/A | `rpact::getSampleSize*()` | **Group seq / Adaptive (no Python alt)** |
| N/A | `gsDesign` | **Group sequential (no Python alt)** |
| N/A | `TrialSize` | **Full coverage (80+ functions)** |

---

_Document version: 2026-07 | Data source: CRAN ClinicalTrials Task View_

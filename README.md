# ct-samplesize

[🇨🇳 中文 (Chinese)](./README_ZH.md) | [🇺🇸 English (Current)](#)

> **Easy-to-use Clinical Sample Size & Power Calculator for Clinical Researchers**
>
> This skill provides clinical trial researchers with an easy-to-use, comprehensive sample size & power calculation tool. Powered by R and 20+ professional R packages (rpact, gsDesign, TrialSize, PowerTOST, etc.), users can perform 30+ complex calculations through natural language prompts — bilingual EN/CN menu-driven. **100% reproducible R code** for verification, submission, or re-execution.
>
> **⚠️ R Code Display:** Generated R code is **displayed by default** (dry-run mode). Add `-y/--yes` to execute.

---

## Installation

No extra installation needed. Auto-loads as a WorkBuddy / OpenClaw skill.

### R Packages (On-Demand)

R packages are **not pre-installed**. The skill prompts you to install only when needed:

```r
# When you see: Warning: 'TrialSize' package not found.
install.packages("TrialSize")
```

**One-click install all:**
```bash
python scripts/samplesize_power.py --install-all-packages
```

**Or in R:**
```r
install.packages(c("TrialSize","pwr","rpact","gsDesign","PowerTOST","simr","lme4","pROC","powerSurvEpi","survival"))
```

**No R package needed for:** `poisson`, `cluster`, `bland_altman`, `vaccine_efficacy`, `bayesian`, `dose_escalation`, `survival` (Schoenfeld only), `must_win`, `multiple_endpoints`, `assurance`, `dunnett`, `mediation`, `win_ratio`

---

## Quick Start

```
"Control 20%, treatment 35%, chi-square test, two-sided α=0.05, power=0.8"
"Survival trial with 1 interim analysis, HR=0.75, 1:1 randomization"
"Non-inferiority trial, margin=0.1, control rate=85%, treatment rate=80%"
```

---

## Supported Test Types (30+)

| Category | Test Type | Clinical Scenario | R Package(s) |
|:---|:---|:---|:---|
| **Continuous** | `ttest_ind` | Two-means comparison (parallel) | `pwr`, `TrialSize` |
| | `ttest_paired` | Paired t / 2×2 crossover | `pwr`, `TrialSize` |
| | `anova` | Multi-group (k groups) | `pwr`, `TrialSize` |
| | `equivalence` | Equivalence (means) | `TrialSize` |
| | `mixed_model` | Repeated measures / longitudinal | `simr` |
| **Binary** | `proportion_one` | Single-group rate | `pwr` |
| | `proportion_two` | Two-group rate (chi-square) | `pwr`, `TrialSize` |
| | `non_inferiority` | Non-inferiority (rate) | `TrialSize` |
| | `be_tost` | Bioequivalence (TOST) | `PowerTOST` |
| | `superiority_margin` | Superiority by margin | `TrialSize` |
| **Count/Rate** | `poisson` | Poisson rate / recurrent events | Wald test |
| | `vaccine_efficacy` | Vaccine efficacy | Halloran formula |
| **Time-to-Event** | `survival` | Survival (simplified) | Schoenfeld formula |
| | `survival_exact` | Survival (exact) | `rpact` |
| | `ni_survival` | Non-inferiority survival | `powerSurvEpi` |
| **Diagnostic** | `roc` | ROC curve / diagnostic trial | `pROC` |
| | `bland_altman` | Bland-Altman method comparison | Lu et al. formula |
| **Special Designs** | `cluster` | Cluster-randomized | DEFF formula |
| | `multiple_endpoints` | Multiple/compound endpoints | Correlation method |
| | `bayesian` | Bayesian design | `BayesCTDesign` |
| | `dose_escalation` | Dose escalation (Phase I) | `escalation` |
| | `group_sequential` | Group sequential / interim | `gsDesign`, `rpact` |
| | `adaptive` | Adaptive design | `rpact` |
| | `mams` | Multi-arm multi-stage (MAMS) | `rpact` |
| **Advanced** | `win_ratio` | Win-Ratio composite endpoint | `BuyseTest` simulation |
| | `must_win` | Must-Win / co-primary endpoints | Correlation method |
| | `historical_controls` | Historical control borrowing | `RBesT` MAP prior |
| | `conditional_power` | Conditional power / SSR | `rpact` |
| | `assurance` | Bayesian assurance | Monte Carlo |
| | `dunnett` | Dunnett comparisons | Custom formula |
| | `mediation` | Mediation effects | `powerMediation` |

---

## CLI Examples

```bash
# === Continuous ===
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test ttest_paired --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.8
python scripts/samplesize_power.py --test equivalence --margin 2.0 --effect 3.0 --power 0.8
python scripts/samplesize_power.py --test mixed_model --effect 0.5 --nsim 500

# === Binary ===
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
python scripts/samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80 --power 0.8
python scripts/samplesize_power.py --test be_tost --theta0 0.95 --cv 0.25 --design "2x2"
python scripts/samplesize_power.py --test superiority_margin --sup_margin 0.05 --p_control_sup 0.3 --delta_sup 0.15

# === Count ===
python scripts/samplesize_power.py --test poisson --lambda1 0.05 --lambda2 0.03 --t1 2 --t2 2 --power 0.8
python scripts/samplesize_power.py --test vaccine_efficacy --ve_control 0.02 --ve_treatment 0.005 --power 0.8

# === Survival ===
python scripts/samplesize_power.py --test survival --hazard_ratio 0.75 --power 0.85
python scripts/samplesize_power.py --test survival_exact --hr_exact 0.75 --accrual_exact 12 --followup_exact 0.85
python scripts/samplesize_power.py --test ni_survival --ni_margin_surv 1.25 --accrual_time 12 --followup_time 12

# === Diagnostic / Method Comparison ===
python scripts/samplesize_power.py --test roc --auc0 0.5 --auc1 0.75 --power 0.8
python scripts/samplesize_power.py --test bland_altman --sd_diff 5 --w 2.5

# === Special Designs ===
python scripts/samplesize_power.py --test cluster --icc 0.05 --m 30 --n_indiv 64
python scripts/samplesize_power.py --test multiple_endpoints --effect 0.3 --correlation 0.5
python scripts/samplesize_power.py --test bayesian --prob_control 0.3 --prob_treatment 0.15 --prior_a0 0.5
python scripts/samplesize_power.py --test dose_escalation --n_doses 5 --target_dlt 0.33

# === Advanced Endpoints (v3.3) ===
python scripts/samplesize_power.py --test win_ratio --win_ratio_theta 1.5 --n_sim 1000
python scripts/samplesize_power.py --test must_win --n_endpoints_must 3 --effect_must 0.3 --correlation_must 0.5
python scripts/samplesize_power.py --test historical_controls --historical_response 15 --historical_n 100 --a0_borrowing 0.5
python scripts/samplesize_power.py --test mams --n_arms_mams 3 --n_stages_mams 2 --delta_effect 0.3
python scripts/samplesize_power.py --test conditional_power --timing 0.5 --observed_effect 0.2 --planned_effect 0.3
python scripts/samplesize_power.py --test assurance --n_assurance 100 --n_sim_assurance 5000
python scripts/samplesize_power.py --test dunnett --n_groups_dunnett 3 --n_control_dunnett 50 --effect_dunnett 0.4
python scripts/samplesize_power.py --test mediation --a_path 0.3 --b_path 0.3
python scripts/samplesize_power.py --test group_sequential --n_interim 1 --effect_gs 0.4
python scripts/samplesize_power.py --test adaptive --n_stages_adapt 2 --effect_adaptive 0.4
```

### Reverse Calculation: Power given Sample Size

By default (`--power` or omitted) the tool solves for **n** given a target power.
Pass `--nobs N` to reverse the direction: solve for **achieved power** given a fixed sample size.
`--power` and `--nobs` are mutually exclusive.

```bash
# n=50 per group → achieved power for two-sample t-test
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --nobs 50

# n=20 per sequence → achieved power for bioequivalence TOST
python scripts/samplesize_power.py --test be_tost --nobs 20

# n=100 per group → achieved power for MAMS design
python scripts/samplesize_power.py --test mams --nobs 100
```

All 31 test types support this bidirectional solving. Native reverse functions
(`pwr.*`, `PowerTOST::power.TOST`, `rpact::getPowerMeans/getPowerSurvival`) are used
where available; analytic inverse formulas cover self-written tests; precision-style
tests (`bland_altman`) report achievable CI half-width instead of power.

### Curve Mode: Power / Sample-size Curves

Batch-plot curves to visualize the sample-size ↔ power relationship.

- `--n_seq "20,40,200"` → **Power curve** (x = sample size, y = power)
- `--n_seq "20:20:200"` → same, but auto-expanded start:step:stop
- `--power_seq "0.6:0.05:0.95"` → **Sample-size curve** (x = power, y = n)
- `--plot_effects "0.3,0.5,0.8"` → overlay multiple effect-size curves (sensitivity)
- `--out path.png` → PNG output (defaults to system temp dir)

```bash
# Power curve with 3 overlaid effect sizes
python scripts/samplesize_power.py --test ttest_ind --n_seq "20:20:200" --plot_effects "0.3,0.5,0.8" --out power_curve.png

# Sample-size curve across power 0.6–0.95
python scripts/samplesize_power.py --test ttest_ind --power_seq "0.6:0.05:0.95" --out n_curve.png
```

Supported for 22 test types (ttest_*, anova, proportion_*, odds_ratio, risk_ratio,
roc, poisson, non_inferiority, superiority_margin, be_tost, survival, ni_survival,
mams, dunnett, group_sequential, survival_exact, equivalence, vaccine_efficacy).
Curves reuse the same validated formulas as single-point solving; `group_sequential`
and `survival_exact` use fixed-design / Schoenfeld approximations (noted in output).

---

## Core Formulas

| Scenario | Formula |
|:---|:---|
| Independent t (equal n) | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| Proportion (arcsin) | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| Survival (Schoenfeld) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |
| ROC (Obuchowski) | $n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{4(\arcsin\sqrt{AUC_1} - \arcsin\sqrt{AUC_0})^2}$ |
| Cluster DEFF | $DEFF = 1 + (m - 1) \times ICC$ |
| Bland-Altman | $n = 2(\frac{Z_{1-\alpha/2} \times SD_{diff}}{W})^2$ |
| Win-Ratio (approx) | $n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\ln WR)^2 / SE_{approx}^2}$ |
| Must-Win inflation | $n = n_{single} \times [1 + (k-1)\rho \times 0.5]$ |
| MAMS (Bonferroni) | $n = \frac{(Z_{1-\alpha/(2k)} + Z_{1-\beta})^2}{\delta^2}$ |
| Assurance | $P(\text{success}) = \frac{1}{N}\sum_{i=1}^N I(\text{trial}_i \text{ significant})$ |

**Full formulas:** `references/formulas_zh.md` | **Extended functions:** `references/extended_functions.md`

---

## System Requirements

| Component | Requirement |
|:----------|:------------|
| R | ≥ 4.1.0 (≥ 4.1.0 recommended) |
| Python | ≥ 3.8 + statsmodels ≥ 0.14, numpy ≥ 1.24, scipy ≥ 1.11 |
| OS | Windows / macOS / Linux |

---

## Common Errors

| Error | Fix |
|:----------|:--------|
| "Rscript not found" | Install R or specify path |
| "package not found" | install.packages("xxx") |
| ImportError: statsmodels | pip install statsmodels |
| simr timeout | Reduce --nsim or simplify model |
| BuyseTest convergence | Increase n_sim, check prior specification |
| rpact error | Update rpact to latest version |

---

## Safety & Disclaimer

- R code is **displayed by default** (dry-run); `-y/--yes` required to execute
- All computations are local; no data transmission
- Outputs for reference only; validate before regulatory submissions

---

## File Structure

```
ct-samplesize/
├── SKILL.md              ← Skill definition (bilingual, concise)
├── README.md             ← This file (English)
├── README_ZH.md          ← Chinese version
├── AGENTS.md             ← Core execution rules (bilingual)
├── assets/
│   └── icon.svg          ← Skill icon (104×104)
├── scripts/
│   └── samplesize_power.py  ← Python calculator + auto R code gen
└── references/
    ├── r_packages_zh.md     ← R package reference (20+ pkgs)
    ├── formulas_zh.md       ← Formula derivations
    ├── python_usage.md      ← Python quick ref
    ├── r_usage.md           ← R quick ref
    ├── effect_size.md       ← Effect size standards (d/f/h + Z table)
    ├── report_template.md   ← Report template + mandatory R code
    ├── data_format_guide.md ← 31 test types data format + examples
    └── examples.md          ← 3 full walkthroughs (proportion/GS/noninferiority)
```

---

## Core Features

1. **Smart Env Detection**: Auto-detect R installation on every trigger
2. **Dual-path**: Python (simple) + R (exact & complex)
3. **Mandatory R Code**: Regardless of path, always include reproducible R script
4. **Comprehensive**: 20+ R packages, full formula derivations, 3 complete examples
5. **Natural Language**: Just describe your trial in plain language
6. **Bilingual**: Full EN/CN support with auto-detection

---

## References

- rpact: https://www.rpact.org/
- gsDesign: https://keaven.github.io/gsDesign/
- TrialSize: https://cran.r-project.org/web/packages/TrialSize/
- PowerTOST: https://cran.r-project.org/web/packages/PowerTOST/
- simr: https://github.com/pitakakariki/simr/
- powerSurvEpi: https://cran.r-project.org/web/packages/powerSurvEpi/
- BayesCTDesign: https://cran.r-project.org/web/packages/BayesCTDesign/
- BuyseTest: https://cran.r-project.org/web/packages/BuyseTest/
- RBesT: https://cran.r-project.org/web/packages/RBesT/
- MCPAN: https://cran.r-project.org/web/packages/MCPAN/
- powerMediation: https://cran.r-project.org/web/packages/powerMediation/
- CRAN ClinicalTrials View: https://cran.r-project.org/web/views/ClinicalTrials.html

---

## Source Code

https://github.com/medstatstar/ct-samplesize

---

**Version**: v3.3.0 | **License**: MIT | **Authors**: medstatstar, phoe-zip

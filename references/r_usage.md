# R Implementation Reference R

> **English:** R path for complex designs (group sequential, adaptive, platform trials). By default runs in SAFE PREVIEW: generated R code is shown but NOT executed; use `--yes` to execute & compute, `--show-code` to display (no execution), or `--dry-run` to preview only. R **** R **** `--yes` `--show-code` `--dry-run`

---

## Environment

| Item | Requirement |
|:-----|:------------|
| R version | ≥ 4.1.0 |
| Install | CRAN binary |
| Rscript | Auto-detect via PATH or RSCRIPT_PATH env |

---

## CLI Usage CLI

```bash
# Preview R code (--dry-run, NOT executed)
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8

# Execute R code (optionally show with --show-code)
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8 -y
```

---

## Key Packages

| Package | Use |
|:--------|:----|
| rpact | Adaptive + Group Sequential |
| gsDesign | Classical Group Sequential |
| TrialSize | Comprehensive (80+ functions) |
| pwr | Basic t-test / ANOVA |
| PowerTOST | Bioequivalence (TOST) |
| simr | Mixed model power (Monte Carlo) |
| pROC | ROC curve formulas |
| BayesCTDesign | Bayesian design |
| escalation | Dose escalation |

# R Implementation Reference / R 实施参考

> **EN:** R path for complex designs (group sequential, adaptive, platform trials). Generated R code is hidden by default; use `--show-code` to display (execute + show) or `--dry-run` to preview only.
> **CN:** R 路径用于复杂设计（组序贯、适应性、平台试验）。生成的 R 代码默认不展示；用 `--show-code` 展示（执行+展示），或 `--dry-run` 仅预览。

---

## Environment / 环境要求

| Item | Requirement |
|:-----|:------------|
| R version | ≥ 4.1.0 |
| Install | CRAN binary |
| Rscript | Auto-detect via PATH or RSCRIPT_PATH env |

---

## CLI Usage / CLI 使用

```bash
# Preview R code (--dry-run, NOT executed)
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8

# Execute R code (optionally show with --show-code)
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8 -y
```

---

## Key Packages / 核心包

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

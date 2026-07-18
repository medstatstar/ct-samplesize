# R Implementation Reference / R 实施参考

> **English / 中文:** R path for complex designs (group sequential, adaptive, platform trials). By default runs in SAFE PREVIEW: generated R code is shown but NOT executed; use `--yes` to execute & compute, `--show-code` to display (no execution), or `--dry-run` to preview only. / R 路径用于复杂设计（组序贯、适应性、平台试验）。默认运行于**安全预览模式**：展示生成的 R 代码但**不执行**；用 `--yes` 执行并计算，`--show-code` 仅展示代码（不执行），或 `--dry-run` 仅预览。

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

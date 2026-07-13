# Python Implementation Reference / Python 实施参考

> **EN:** Python path is the fallback when the user refuses R installation. Supports simple, fixed designs only.
> **CN:** Python 路径用于用户拒绝安装 R 时的降级方案。仅支持简单固定设计。

---

## Quick Usage / 快速使用

```bash
# Two-sample t-test / 两独立样本t
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --alpha 0.05 --power 0.9

# Given n, find power / 给定样本量求效能
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --alpha 0.05 --nobs1 44

# One-sample / Paired t / 单样本/配对 t
python scripts/samplesize_power.py --test ttest_one --effect 0.625 --alpha 0.05 --power 0.9

# ANOVA (3 groups) / 3组ANOVA
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.9

# Two proportions (arcsin) / 两样本率(arcsin变换)
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8

# Non-inferiority / 非劣效性
python scripts/samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80

# Survival (simplified) / 生存分析(简化)
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8
```

---

## Parameters / 参数说明

| Parameter | Description 说明 | Applicable Tests 适用检验 |
|:----------|:-----------------|:------------------------|
| `--test` | Test type (required) / 检验类型（必填） | all 全部 |
| `--effect` | Effect size (Cohen's d or f) / 效应量 | ttest_one/ttest_ind/anova |
| `--alpha` | Significance level / 显著性水平 | all 全部 |
| `--power` | Desired power / 期望效能 | all 全部 |
| `--nobs1` | Sample size (when solving for power) / 样本量 | ttest_one/ttest_ind |
| `--k_groups` | Number of groups / 组数 | anova |
| `--p1`, `--p2` | Two rates / 两组率 | proportion_two/non_inferiority |
| `--margin` | Non-inferiority margin / 非劣效界值 | non_inferiority |
| `--hazard_ratio` | Hazard ratio / 风险比 | survival |

---

## Supported Test Types / 支持的检验类型

| test value 值 | Description 描述 | Method 方法 |
|:--------------|:-----------------|:------------|
| `ttest_one` | One-sample / Paired t / 单样本/配对 t | statsmodels.TTestPower |
| `ttest_ind` | Two independent samples t / 两独立样本 t | statsmodels.TTestIndPower |
| `anova` | One-way ANOVA / 单因素 ANOVA | statsmodels.FTestAnovaPower |
| `proportion_one` | One-sample rate / 单样本率 | Normal approx 正态近似 |
| `proportion_two` | Two-sample rate / 两样本率 | arcsin + independent t |
| `non_inferiority` | Non-inferiority (rate) / 非劣效率比较 | Standard formula 标准公式 |
| `survival` | Survival (simplified) / 生存分析（简化） | Schoenfeld formula |

---

## Auto R Code Generation / 自动 R 代码生成

**EN:** The Python script has built-in R code templates. Default mode prints the R code for review. Execution of the generated R code requires explicit `-y`/`--yes` confirmation (see dry-run behavior).

**CN:** Python 脚本内置 R 代码模板。默认模式打印 R 代码供审查，执行生成的 R 代码需要显式的 `-y`/`--yes` 确认（参见 dry-run 行为）。

---

## ANaconda Execution / Anaconda 执行

```python
import subprocess
result = subprocess.run(
    [r"%USERPROFILE%\AppData\Local\Programs\Python\313\python.exe",
     r"%USERPROFILE%\.workbuddy\skills\ct-samplesize\scripts\samplesize_power.py",
     "--test", "ttest_ind", "--effect", "0.5", "--alpha", "0.05", "--power", "0.9"],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
```

---

## Limitations / 限制

- **EN:** Simple, fixed designs only. Survival uses simplified Schoenfeld formula.
- **CN:** 仅支持简单固定设计；生存分析使用简化 Schoenfeld 公式。
- **EN:** Does NOT support group sequential, adaptive, or platform designs.
- **CN:** **不支持**组序贯、适应性设计、多臂平台试验。
- **EN:** For precise/complex results, R is mandatory.
- **CN:** 如需精确结果或复杂设计，**必须安装 R**。

# Effect Size Reference / 效应量参考

> **EN:** Cohen's d / f / h standards for judging effect size magnitude.
> **CN:** Cohen's d / f / h 标准，用于判断效应量大小。

## Cohen's d / Cohen's d 标准

| Size 大小 | d | Clinical Example 临床意义示例 |
|:---------:|:--:|:-----------------------------|
| Small 小 | 0.2 | Blood pressure ↓ 5 mmHg |
| Medium 中 | 0.5 | Blood pressure ↓ 10-15 mmHg |
| Large 大 | 0.8 | Blood pressure ↓ >20 mmHg |

## Cohen's f / Cohen's f 标准

| Size 大小 | f | ANOVA Interpretation |
|:---------:|:--:|:---------------------|
| Small 小 | 0.10 | Groups slightly different |
| Medium 中 | 0.25 | Clinically relevant |
| Large 大 | 0.40 | Clearly separated |

## h Effect Size (arcsin-transformed rates) / h 效应量（率变换后）

| Size 大小 | h | arcsin Rate Difference |
|:---------:|:--:|:----------------------|
| Small 小 | 0.20 | ~0.10 (rate diff) |
| Medium 中 | 0.50 | ~0.25 (rate diff) |
| Large 大 | 0.80 | ~0.40 (rate diff) |

## Conversion Formulas / 效应量转换公式

| Conversion 转换 | Formula 公式 |
|:----------------|:-------------|
| Cohen's d → f | $f = d/2$ |
| Cohen's d → r | $r = d/\sqrt{d^2+4}$ |
| r → Cohen's d | $d = 2r/\sqrt{1-r^2}$ |
| OR → Cohen's d | $d = \log(OR) \times \sqrt{3}/\pi$ |
| η² → Cohen's f | $f = \sqrt{\eta^2/(1-\eta^2)}$ |

## Z-Value Quick Reference / 常见 Z 值速查表

| $\alpha$ | One-sided $Z_{1-\alpha}$ | Two-sided $Z_{1-\alpha/2}$ |
|:--------:|:------------------------:|:--------------------------:|
| 0.10 | 1.282 | 1.645 |
| 0.05 | 1.645 | 1.960 |
| 0.025 | 1.960 | 2.242 |
| 0.01 | 2.326 | 2.576 |
| 0.001 | 3.090 | 3.291 |

| $\beta$ | $Z_{1-\beta}$ |
|:-------:|:------------:|
| 0.20 | 0.842 |
| 0.10 | 1.282 |
| 0.05 | 1.645 |
| 0.01 | 2.326 |

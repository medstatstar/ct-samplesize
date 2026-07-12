# Sample Size & Power — Formula Reference / 样本量与检验效能 — 公式参考

> **EN:** Complete formula derivations from the *Python Statistical Analysis* course notes and classical statistics textbooks.
> 适用于独立样本、正态性假设。

---

## 1. Basic Concepts / 基本概念

| Symbol | Definition 定义 |
|:-------|:----------------|
| α | Type I error (false positive), typically 0.05 |
| β | Type II error (false negative), typically 0.1 or 0.2 |
| 1-β | Power (检验效能), typically 0.8 or 0.9 |
| δ | True difference between groups (effect size) |
| σ | Population standard deviation |
| n | Sample size per group |

---

## 2. t-Test Sample Size / t 检验样本量

### 2.1 One-Sample / Paired t / 单样本/配对 t

$$n = \left( \frac{Z_{1-\alpha/2} + Z_{1-\beta}}{\delta/\sigma} \right)^2$$

**Example:** New drug lowers cholesterol by δ=0.5 mmol/L, σ=0.8, α=0.05 one-sided, power=0.9
$$n = \left( \frac{1.645 + 1.282}{0.625} \right)^2 \approx 23$$

### 2.2 Two Independent Samples t / 两独立样本 t

$$n_1 = \left( \frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d} \right)^2 \left( 1 + \frac{1}{r} \right), \quad n_2 = r \cdot n_1$$

**Example:** d=0.5, r=1, α=0.05 two-sided, power=0.9 → $n_1 \approx 84$

---

## 3. ANOVA / 方差分析

$$n = \frac{2 \sigma^2}{\delta^2} (Z_{1-\alpha/2} + Z_{1-\beta})^2 f(k)$$

Cohen's f: $f = \frac{\sigma_{means}}{\sigma_{within}}$

---

## 4. Proportion Comparison / 率的比较

### 4.1 Two-Sample Rate (arcsin) / 两样本率(arcsin变换)

$$h = 2(\arcsin\sqrt{p_1} - \arcsin\sqrt{p_2})$$

$$n_1 = \left( \frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h} \right)^2 \left( 1 + \frac{1}{r} \right)$$

### 4.2 One-Sample Rate / 单样本率

$$n = \left( \frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h} \right)^2$$

---

## 5. Non-Inferiority / 非劣效性

### 5.1 Rate Non-Inferiority / 率的非劣效

$$n_E = \left( \frac{Z_{1-\alpha} + Z_{1-\beta}}{(\pi_E - \pi_C) + \delta} \right)^2 \left[ \pi_E(1-\pi_E) + \frac{\pi_C(1-\pi_C)}{r} \right]$$

### 5.2 Mean Non-Inferiority / 均数非劣效

$$n = \left( \frac{Z_{1-\alpha} + Z_{1-\beta}}{\delta - |\mu_E - \mu_C|} \right)^2 \times 2\sigma^2$$

---

## 6. Survival Analysis / 生存分析

Schoenfeld formula:

$$d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$$

where d = total events required, HR = hazard ratio.

**Note:** Simplified. For exact results with accrual time, censoring, non-proportional hazards → use R `rpact` or `gsDesign`.

---

## 7. Repeated Measures / 重复测量

$$n = \frac{2\sigma^2}{\delta^2}(Z_{1-\alpha/2} + Z_{1-\beta})^2 \cdot \frac{1+(k-1)\rho}{k}$$

where k = number of repetitions, ρ = ICC.

---

## 8. Cluster Randomization / 整群随机

$$n_{individuals} = \left( \frac{Z_{1-\alpha/2} + Z_{1-\beta}}{\delta} \right)^2 \left[ \frac{\sigma^2}{m} (1+(m-1)\rho) \right] \times 2$$

Design Effect = $1 + (m-1)\rho$

---

## 9. Crossover Design / 交叉设计

$$n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2 \sigma_{within}^2}{\delta^2 \cdot 2}$$

---

## 10. Adaptive Design / 适应性设计

O'Brien-Fleming boundary:
$$\alpha(t^*) = 2\left[1 - \Phi\left(\frac{z_{\alpha/2}}{\sqrt{t^*}}\right)\right]$$

Pocock boundary:
$$\alpha(t^*) = -\log(1-\alpha) \cdot \frac{\log(1+t^* \cdot (e-1))}{t^*}$$

---

## 11. Z-Value Quick Reference / Z 值速查表

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

---

## 12. Effect Size Conversion / 效应量转换

| Conversion 转换 | Formula 公式 |
|:----------------|:-------------|
| Cohen's d → f | $f = d/2$ |
| Cohen's d → r | $r = d/\sqrt{d^2+4}$ |
| r → Cohen's d | $d = 2r/\sqrt{1-r^2}$ |
| OR → Cohen's d | $d = \log(OR) \times \sqrt{3}/\pi$ |
| η² → Cohen's f | $f = \sqrt{\eta^2/(1-\eta^2)}$ |

---

## 13. Degrees of Freedom Correction / 自由度修正

Small-sample correction:

$$n_{adj} = n \times \left(1 + \frac{4}{n \cdot d^2}\right)$$

---

_Document version: 2026-07 | Data source: Python Statistical Analysis course notes + Cohen (1988)_

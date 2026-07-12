# Complete Usage Examples / 完整使用示例

> **EN:** 3 typical scenarios with full bilingual output + mandatory R code.
> **CN:** 3 个典型场景，含完整双语输出 + 强制 R 代码。

---

## Example 1: Simple Design / 简单设计

**User query:**
> "对照组有效率20%、试验组35%，做两组率比较的卡方检验，α=0.05双侧，power=0.8"
> "Control 20%, treatment 35%, chi-square test, α=0.05 two-sided, power=0.8"

**AI Execution:**
1. Detect R → Not installed
2. Recommend R install (download link)
3. User refuses → Python fallback
4. Run: `python samplesize_power.py --test proportion_two --p1 0.35 --p2 0.20 --alpha 0.05 --power 0.8`
5. Output result + dropout adjustment + limitations
6. 🔴 Mandatory R code output

---

## 📊 Sample Size Report | 样本量计算报告

### Trial Design / 检验设计
- **Design | 设计类型**: Parallel
- **Endpoint | 主要终点**: Binary (response rate)
- **Hypothesis | 假设检验**: Superiority
- **Direction | 检验方向**: Two-sided

### Input Parameters / 输入参数
- α = 0.05 (two-sided | 双侧)
- power = 0.80
- h effect size (arcsin): 0.3388
- p₁ = 0.35 (treatment | 试验组)
- p₂ = 0.20 (control | 对照组)

### Results / 计算结果
- **Per-group N | 每组样本量**: 138 → Total 276
- Adjusted for 10% dropout: 154/group → Total 308

### Interpretation / 结果解释
With two-sided α=0.05 and power=0.80, 138 subjects per group (276 total) are needed to detect a rate difference of 35% vs 20%.

---

## 📋 Reproducible R Code | 可复现的 R 代码

```r
# Two-Sample Proportion (arcsin) / 两样本率(arcsin变换)
# install.packages(c("TrialSize", "pwr"))
library(TrialSize); library(pwr)

p1 <- 0.35; p2 <- 0.20; alpha <- 0.05; power <- 0.80

# Method 1: TrialSize / TrialSize法
h <- 2 * (asin(sqrt(p1)) - asin(sqrt(p2)))
n1 <- TrialSize::NTwoArmRates(alpha=alpha, beta=1-power, p1=p1, p2=p2, delta=0)
print(n1)

# Method 2: pwr / pwr法
result <- pwr::pwr.2p.test(h=h, n=NULL, sig.level=alpha, power=power)
n_per <- ceiling(result$n)
cat(sprintf("Per group: %d | Total: %d\n", n_per, n_per*2))

# Method 3: Chi-square approx / 卡方近似
z_a <- qnorm(1-alpha/2); z_b <- qnorm(power)
n_chisq <- ceiling((z_a+z_b)^2 * (p1*(1-p1)+p2*(1-p2)) / (p1-p2)^2)
cat(sprintf("Chi-square approx: %d\n", n_chisq))

# Dropout Adjustment 脱落调整
# 脱落率 10%，则调整后样本量 = n / (1 - dropout_rate)
dropout_rate <- 0.10
n_adj <- ceiling(n_per / (1 - dropout_rate))
cat(sprintf("Adjusted: %d/group | Total: %d\n", n_adj, n_adj*2))
```

---

## Example 2: Group Sequential / 组序贯设计

**User query:**
> "含2次期中分析的生存终点试验，HR=0.7，α=0.025，power=0.9，入组12月，总36月"
> "Survival trial with 2 interim analyses, HR=0.7, α=0.025, power=0.9, accrual 12mo, total 36mo"

**AI Execution:**
1. Detect R → Installed
2. Confirm gsDesign installed
3. Execute R script
4. Parse results
5. 🔴 Output runnable R code

---

## 📊 Sample Size Report (Group Sequential) | 样本量计算报告（组序贯设计）

### Trial Design / 检验设计
- **Design | 设计类型**: Group Sequential (O'Brien-Fleming spending)
- **Endpoint | 主要终点**: Overall Survival (OS)
- **Hypothesis | 假设检验**: Superiority
- **Direction | 检验方向**: One-sided α=0.025

### Input Parameters / 输入参数
- HR = 0.70
- α = 0.025 (one-sided | 单侧)
- power = 0.90
- Accrual time | 入组时间 = 12 months | 月
- Total duration | 总时长 = 36 months | 月
- Min follow-up | 最短随访 = 24 months | 月

### Results / 计算结果
- Total events required | 所需总事件数: ~252 → 366
- Per-group N | 每组样本量: ~174 → Total 348
- OBF boundaries (3 analyses Z): [3.47, 2.45, 2.00]

---

## 📋 Reproducible R Code | 可复现的 R 代码

```r
# Group Sequential Survival Design | 生存终点组序贯设计 (gsDesign)
# install.packages("gsDesign")
library(gsDesign)

alpha <- 0.025; beta <- 0.10; hr <- 0.70
R <- 12; T <- 36
# minfup = minimum follow-up = T - R = 36 - 12 = 24 months
# minfup = 最短随访时间 = 总时长 - 入组时间
minfup <- T - R
lambdaC <- log(2) / 12  # Median OS 12mo | 中位OS=12月

x <- gsSurv(k=3, alpha=alpha, beta=beta, timeratio=FALSE,
            hr=hr, lambdaC=lambdaC, R=R, T=T, minfup=minfup, ratio=1,
            sfu=sfLDOF, test.type=1)

print(x)

cat("\n===== Interim Z Boundaries | 期中分析Z边界 =====\n")
cat(sprintf("1st (33%% info): Z = %.2f\n", x$upper$bound[1]))
cat(sprintf("2nd (67%% info): Z = %.2f\n", x$upper$bound[2]))
cat(sprintf("3rd (100%% info): Z = %.2f\n", x$upper$bound[3]))
cat(sprintf("\nTotal events | 总事件数: %.0f\n", x$events))
cat(sprintf("Max sample | 最大样本量: %.0f\n", x$n.I[x$k]))
cat(sprintf("Per group | 每组: %.0f\n", ceiling(x$n.I[x$k]/2)))
```

---

## Example 3: Non-inferiority / 非劣效设计

**User query:**
> "非劣效检验，对照组率70%，试验组预期65%，非劣效界值10%，α=0.025单侧，power=0.8"
> "Non-inferiority, control 70%, treatment 65%, margin 10%, α=0.025 one-sided, power=0.8"

---

## 📋 Reproducible R Code | 可复现的 R 代码

```r
# Non-Inferiority Proportion | 非劣效性-率比较
# install.packages("TrialSize")
library(TrialSize)

alpha <- 0.025; beta <- 0.20
pe <- 0.65; pc <- 0.70; delta <- 0.10; ratio <- 1

# Method 1: TrialSize | TrialSize法
result <- NPropTwoSidedNonInferiority(alpha=alpha, beta=beta,
                                       pe=pe, pc=pc, delta=delta, ratio=ratio)
print(result)
n_per <- ceiling(result[2, "n"])
cat(sprintf("Per group: %d | Total: %d\n", n_per, n_per*2))

# Method 2: Large-sample formula | 大样本公式验证
z_a <- qnorm(1-alpha); z_b <- qnorm(1-beta)
se2 <- pe*(1-pe) + pc*(1-pc)/ratio
delta_real <- pe - pc
n_formula <- ceiling(((z_a+z_b)^2 * se2) / (delta - abs(delta_real))^2)
cat(sprintf("Formula verify | 公式验证: %d\n", n_formula))

# Dropout | 脱落调整
dropout <- 0.10
n_adj <- ceiling(n_per / (1-dropout))
cat(sprintf("Adjusted | 考虑脱落: %d/group | Total: %d\n", n_adj, n_adj*2))
```

---

## Execution Notes / 执行要点

1. **Simple (Ex 1)**: Python + R code output simultaneously
2. **Complex (Ex 2)**: Must detect R; if missing, pause & guide install
3. **Non-inferiority (Ex 3)**: Always output complete R code regardless of path

> All R code blocks follow `references/report_template.md` standards.
> 所有 R 代码块遵循 `references/report_template.md` 标准。

# Command-Line Examples / CLI 命令示例

> This file collects all common CLI examples for `scripts/samplesize_power.py`, referenced by `SKILL.md`. / 本文件集中收录 `scripts/samplesize_power.py` 的全部常用命令行示例，供 `SKILL.md` 引用。
> By default the skill runs in SAFE PREVIEW: generated R/Python code is shown but NOT executed. Pass `--yes`/`-y` to actually execute and compute; `--show-code` displays the code (no execution); `--dry-run` is the default preview mode (code shown, not run). / 默认运行于**安全预览模式**：展示生成的 R/Python 代码但**不执行**。追加 `--yes`/`-y` 才真正执行并计算；`--show-code` 仅展示代码（不执行）；`--dry-run` 为默认预览模式（展示代码、不执行）。
> Sequences support two formats: comma list `"20,40,200"` or auto-generated `"20:20:200"` (start:step:stop). / 序列支持两种格式：逗号显式 `"20,40,200"` 或 自动生成 `"20:20:200"`（起:步:止）。

---

## Quick Menu / 快速引导菜单（检验类型对照表）

| Category 类别 | Test Type 检验类型 | Clinical Scenario 临床场景 | R Package(s) R 包 |
|:---|:---|:---|:---|
| **Continuous** | `ttest_ind` | Two-means comparison (parallel) / 两均数比较（平行设计） | `pwr`, `TrialSize` |
| | `ttest_paired` | Paired t / 2×2 crossover / 配对t / 交叉设计2×2 | `pwr`, `TrialSize` |
| | `anova` | Multi-group comparison (k groups) / 多组比较（k组） | `pwr`, `TrialSize` |
| | `equivalence` | Equivalence test (means) / 等效性检验（均数） | `TrialSize` |
| | `mixed_model` | Repeated measures / longitudinal / 重复测量 / 纵向数据 | `simr` |
| **Binary** | `proportion_one` | Single-group rate / 单组率检验 | `pwr` |
| | `proportion_two` | Two-group rate (chi-square) / 两组率比较（卡方） | `pwr`, `TrialSize` |
| | `non_inferiority` | Non-inferiority (rate) / 非劣效设计（率） | `TrialSize` |
| | `be_tost` | Bioequivalence (TOST) / 生物等效性 (TOST) | `PowerTOST` |
| | `superiority_margin` | Superiority (margin) / 优效性检验（界值法） | `TrialSize` |
| **Count/Event rate** | `poisson` | Poisson rate / recurrent events / Poisson率 / 复发性事件 | Wald test |
| | `vaccine_efficacy` | Vaccine efficacy / 疫苗效力 | Halloran formula |
| **Time-to-Event** | `survival` | Survival (simplified) / 生存分析（简化） | Schoenfeld formula |
| | `survival_exact` | Survival (exact) / 生存分析（精确） | `rpact` |
| | `ni_survival` | Non-inferiority survival / 非劣效生存设计 | `powerSurvEpi` |
| **Diagnostic/Methodology** | `roc` | ROC curve / diagnostic trial / ROC曲线 / 诊断试验 | `pROC` |
| | `bland_altman` | Bland-Altman method comparison / Bland-Altman方法学比对 | Lu et al. formula |
| **Special Designs** | `cluster` | Cluster randomized / 类随机设计 | DEFF formula |
| | `multiple_endpoints` | Multi-endpoint / composite / 多终点 / 复合终点 | Correlation method |
| | `bayesian` | Bayesian design / 贝叶斯设计 | `BayesCTDesign` |
| | `dose_escalation` | Dose escalation (Phase I) / 剂量递增 (I期) | `escalation` |
| | `group_sequential` | Group sequential / interim analysis / 组序贯 / 期中分析 | `gsDesign`, `rpact` |
| | `adaptive` | Adaptive design / 适应性设计 | `rpact` |
| | `mams` | Multi-arm multi-stage (MAMS) / 多臂多阶段 (MAMS) | `rpact` |
| **Advanced** | `win_ratio` | Win-Ratio composite / Win-Ratio复合终点 | `BuyseTest` simulation |
| | `must_win` | Must-Win / co-primary / Must-Win / 共主要终点 | Correlation method |
| | `historical_controls` | Historical control borrowing / 历史对照借用 | `RBesT` MAP prior |
| | `conditional_power` | Conditional power / SSR / 条件效能 / 样本量重估计 | `rpact` |
| | `assurance` | Bayesian assurance / 贝叶斯确信度 | Monte Carlo |
| | `dunnett` | Dunnett multiple comparison / Dunnett 多重比较 | Custom formula |
| | `mediation` | Mediation effect / 中介效应样本量 | `powerMediation` |

---

## Common Flags / 标准参数速查

| Flag 参数 | Meaning 含义 |
|:---|:---|
| `--test <type>` | Test type (required) / 检验类型（必填） |
| `--power 0.8` | Target power (forward: solve n given power) / 目标效能（正向：给定效能求样本量 n） |
| `--nobs N` | Given sample size (reverse: solve power; mutually exclusive with `--power`, `--nobs` wins) / 给定样本量（反向：求可达效能 power；与 `--power` 互斥，同时传以 `--nobs` 为准） |
| `--n_seq "20:20:200"` | Sample-size sequence → Power curve (x=n, y=power) / 样本量序列 → 绘制 **Power 曲线**（x=样本量, y=效能） |
| `--power_seq "0.6:0.05:0.95"` | Power sequence → sample-size curve (x=power, y=n) / 效能序列 → 绘制 **样本量曲线**（x=效能, y=样本量） |
| `--plot_effects "0.3,0.5,0.8"` | Overlay multiple effect-size curves (sensitivity; some types) / 多效应量叠加多条曲线（敏感性分析，仅部分类型支持） |
| `--out path.png` | Curve PNG output path (default: system temp) / 曲线 PNG 输出路径（默认写入系统临时目录） |
| `-y/--yes` | Explicitly execute R code and compute the result (default is SAFE PREVIEW, no execution) / 显式执行 R 代码并计算（默认为安全预览、不执行） |
| `--dry-run` | Show generated R code only, no execution (safe preview) / 仅展示生成的 R 代码、不执行（安全预览） |

---

## Implementation Examples / 实施示例

```bash
# === Continuous / 连续变量 ===
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test ttest_paired --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.8
python scripts/samplesize_power.py --test equivalence --margin 2.0 --effect 3.0 --power 0.8

# === Binary / 二分类 ===
# proportion_* convention / proportion_* 约定: --p1 = control/original, --p2 = experimental/new
python scripts/samplesize_power.py --test proportion_two --p1 0.15 --p2 0.30 --power 0.8
python scripts/samplesize_power.py --test proportion_two --p1 0.15 --p2 0.30 --power 0.8 --side one
python scripts/samplesize_power.py --test proportion_one --p1 0.40 --p2 0.50 --power 0.8
python scripts/samplesize_power.py --test proportion_paired --p1 0.15 --p2 0.30 --power 0.8
python scripts/samplesize_power.py --test odds_ratio --p1 0.30 --p2 0.50 --power 0.8
python scripts/samplesize_power.py --test risk_ratio --p1 0.30 --p2 0.50 --power 0.8
python scripts/samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80 --power 0.8
python scripts/samplesize_power.py --test superiority_margin --sup_margin 0.05 --p_control_sup 0.3 --delta_sup 0.15

# === Count / 计数 ===
python scripts/samplesize_power.py --test poisson --lambda1 0.05 --lambda2 0.03 --t1 2 --t2 2 --power 0.8

# === Survival / 生存 ===
python scripts/samplesize_power.py --test survival --hazard_ratio 0.75 --power 0.85

# === Special Designs / 特殊设计 ===
python scripts/samplesize_power.py --test cluster --icc 0.05 --m 30 --n_indiv 64
python scripts/samplesize_power.py --test group_sequential --n_interim 1 --effect_gs 0.4
```

---

## Reverse Examples / 双向求解示例（给定样本量求效能）

```bash
# Reverse / 反向：n=50 per group → achieved power for two-sample t-test
# 反向：给定 n=50/组，求两独立样本 t 检验可达效能
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --nobs 50

# Reverse / 反向：n=20 per sequence → achieved power for bioequivalence TOST
# 反向：给定 n=20/序列，求 BE 等效可达效能
python scripts/samplesize_power.py --test be_tost --nobs 20

# Reverse / 反向：n=100 per group → achieved power for MAMS design
# 反向：给定 n=100/组，求多臂多阶段(MAMS)设计可达效能
python scripts/samplesize_power.py --test mams --nobs 100
```

**Covers all 37 test types / 覆盖全部 37 种检验类型.** Reverse-solve strategy:
- **Native package reverse (priority) / 原生包反解（优先）**: `pwr.*` (`pwr.t.test(n=)` auto-reverses), `PowerTOST::power.TOST(n=)`, `rpact::getPowerMeans/getPowerSurvival(n=)` — exact. / `pwr.*`（`pwr.t.test(n=)` 等自动反解）、`PowerTOST::power.TOST(n=)`、`rpact::getPowerMeans/getPowerSurvival(n=)`，精确反解。
- **Analytic inverse / 解析逆公式**: self-written tests (ROC, Poisson, vaccine efficacy, multi-endpoint, Bayesian, Win Ratio, MAMS etc.) back-solve `z_b` via non-centrality, then `power = pnorm(z_b)`. / 自写检验（ROC、Poisson、疫苗效力、多终点、贝叶斯、Win Ratio、MAMS 等）通过非中心参数逆推 `z_b`，再 `power = pnorm(z_b)`。
- **Approx/precision / 近似/精度型**: `bland_altman` returns achievable CI half-width (precision, not power); `dose_escalation` is heuristic design (power N/A); `conditional_power`/`assurance` `--nobs` maps directly to planned/assurance sample size. / `bland_altman` 回报可达 CI 半宽（精度而非效能）；`dose_escalation` 为启发式设计，效能不适用；`conditional_power`/`assurance` 的 `--nobs` 直接映射至计划样本量/保证样本量。

*Note / 注：部分类型（如 `roc` 需 `--auc1`/`--effect`、`mixed_model` 需 `--effect_name`）在双向均要求提供必需参数，缺失时返回参数校验错误（符合预期）。*

---

## Curve Mode Examples / 曲线模式示例

```bash
# Power curve / Power 曲线：n = 20,40,...,200，叠加 3 条效应量曲线
python scripts/samplesize_power.py --test ttest_ind --n_seq "20:20:200" --plot_effects "0.3,0.5,0.8" --out power_curve.png

# Sample-size curve / 样本量曲线：power = 0.6,0.65,...,0.95
python scripts/samplesize_power.py --test ttest_ind --power_seq "0.6:0.05:0.95" --out n_curve.png
```

**Curve mode supports 22 test types / 曲线模式支持的检验类型（22 种）**: ttest_ind, ttest_paired, ttest_one, anova, proportion_one, proportion_two, proportion_paired, odds_ratio, risk_ratio, roc, poisson, non_inferiority, superiority_margin, be_tost, survival, ni_survival, mams, dunnett, group_sequential, survival_exact, equivalence, vaccine_efficacy.

Curve mode reuses the same validated formulas as single-point solving (pwr / PowerTOST / analytic inverse) — numerically identical; `group_sequential`, `survival_exact` use fixed-design / Schoenfeld approximation (noted in plot). / 曲线复用与单点求解**同一套已验证公式**（pwr / PowerTOST / 解析逆公式），数值完全一致；`group_sequential`、`survival_exact` 采用固定设计 / Schoenfeld 近似（图注已标注）。

Other types (mixed_model, bayesian, win_ratio, must_win, historical_controls, assurance, conditional_power, adaptive, dose_escalation, bland_altman, cluster) are not yet covered by curve mode and print a clear notice at runtime. / 其余类型（mixed_model、bayesian、win_ratio、must_win、historical_controls、assurance、conditional_power、adaptive、dose_escalation、bland_altman、cluster）曲线模式暂未覆盖，运行时会给出清晰提示。

---

## R Package Install / R 包安装

- **Install on demand / 按需安装**: when the skill prints `Warning: 'xxx' package not found.`, run `install.packages("xxx")` / 技能输出 `Warning: 'xxx' package not found.` 时执行 `install.packages("xxx")`
- **One-click install / 一键安装**: `python scripts/samplesize_power.py --install-all-packages` / `python scripts/samplesize_power.py --install-all-packages`
- **No R package needed / 无需 R 包**: `poisson`, `cluster`, `bland_altman`, `survival` (Schoenfeld only), `vaccine_efficacy`, `bayesian`, `dose_escalation` etc. / `poisson`、`cluster`、`bland_altman`、`survival`（仅 Schoenfeld）、`vaccine_efficacy`、`bayesian`、`dose_escalation` 等

Full R package list: `references/r_packages_zh.md`. / 完整 R 包清单见 `references/r_packages_zh.md`。

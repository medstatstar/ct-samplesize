# CLI 命令示例 / Command-Line Examples

> 本文件集中收录 `scripts/samplesize_power.py` 的全部常用命令行示例，供 `SKILL.md` 引用。
> **R 代码默认执行并返回结果，且始终展示生成的 R 代码**。添加 `--dry-run` 仅预览代码、不执行。`-y/--yes` 保留以兼容旧命令（默认即执行）。
> 序列支持两种格式：逗号显式 `"20,40,200"` 或 自动生成 `"20:20:200"`（起:步:止）。

---

## 快速引导菜单 / Quick Menu（检验类型对照表）

| Category | Test Type | Clinical Scenario | R Package(s) |
|:---|:---|:---|:---|
| **Continuous** | `ttest_ind` | 两均数比较（平行设计） | `pwr`, `TrialSize` |
| | `ttest_paired` | 配对t / 交叉设计2×2 | `pwr`, `TrialSize` |
| | `anova` | 多组比较（k组） | `pwr`, `TrialSize` |
| | `equivalence` | 等效性检验（均数） | `TrialSize` |
| | `mixed_model` | 重复测量 / 纵向数据 | `simr` |
| **Binary** | `proportion_one` | 单组率检验 | `pwr` |
| | `proportion_two` | 两组率比较（卡方） | `pwr`, `TrialSize` |
| | `non_inferiority` | 非劣效设计（率） | `TrialSize` |
| | `be_tost` | 生物等效性 (TOST) | `PowerTOST` |
| | `superiority_margin` | 优效性检验（界值法） | `TrialSize` |
| **计数/事件率** | `poisson` | Poisson率 / 复发性事件 | Wald 检验 |
| | `vaccine_efficacy` | 疫苗效力 | Halloran 公式 |
| **Time-to-Event** | `survival` | 生存分析（简化） | Schoenfeld 公式 |
| | `survival_exact` | 生存分析（精确） | `rpact` |
| | `ni_survival` | 非劣效生存设计 | `powerSurvEpi` |
| **诊断/方法学** | `roc` | ROC曲线 / 诊断试验 | `pROC` |
| | `bland_altman` | Bland-Altman方法学比对 | Lu et al. 公式 |
| **特殊设计** | `cluster` | 类随机设计 | DEFF 公式 |
| | `multiple_endpoints` | 多终点 / 复合终点 | 相关系数法 |
| | `bayesian` | 贝叶斯设计 | `BayesCTDesign` |
| | `dose_escalation` | 剂量递增 (I期) | `escalation` |
| | `group_sequential` | 组序贯 / 期中分析 | `gsDesign`, `rpact` |
| | `adaptive` | 适应性设计 | `rpact` |
| | `mams` | 多臂多阶段 (MAMS) | `rpact` |
| **Advanced** | `win_ratio` | Win-Ratio复合终点 | `BuyseTest` 模拟 |
| | `must_win` | Must-Win / 共主要终点 | 相关系数法 |
| | `historical_controls` | 历史对照借用 | `RBesT` MAP先验 |
| | `conditional_power` | 条件效能 / 样本量重估计 | `rpact` |
| | `assurance` | 贝叶斯确信度 | Monte Carlo |
| | `dunnett` | Dunnett 多重比较 | 自定义公式 |
| | `mediation` | 中介效应样本量 | `powerMediation` |

---

## 标准参数速查 / Common Flags

| Flag | 含义 |
|:---|:---|
| `--test <type>` | 检验类型（必填） |
| `--power 0.8` | 目标效能（正向：给定效能求样本量 n） |
| `--nobs N` | 给定样本量（反向：求可达效能 power；与 `--power` 互斥，同时传以 `--nobs` 为准） |
| `--n_seq "20:20:200"` | 样本量序列 → 绘制 **Power 曲线**（x=样本量, y=效能） |
| `--power_seq "0.6:0.05:0.95"` | 效能序列 → 绘制 **样本量曲线**（x=效能, y=样本量） |
| `--plot_effects "0.3,0.5,0.8"` | 多效应量叠加多条曲线（敏感性分析，仅部分类型支持） |
| `--out path.png` | 曲线 PNG 输出路径（默认写入系统临时目录） |
| `-y/--yes` | 显式执行 R 代码（默认即执行，保留以兼容旧命令） |
| `--dry-run` | 仅展示生成的 R 代码、不执行（安全预览） |

---

## 实施示例 / Implementation Examples

```bash
# === Continuous / 连续变量 ===
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test ttest_paired --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.8
python scripts/samplesize_power.py --test equivalence --margin 2.0 --effect 3.0 --power 0.8

# === Binary / 二分类 ===
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
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

## 双向求解示例 / Reverse Examples（给定样本量求效能）

```bash
# 反向：给定 n=50/组，求两独立样本 t 检验可达效能
# Reverse: n=50 per group → achieved power for two-sample t-test
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --nobs 50

# 反向：给定 n=20/序列，求 BE 等效可达效能
# Reverse: n=20 per sequence → achieved power for bioequivalence TOST
python scripts/samplesize_power.py --test be_tost --nobs 20

# 反向：给定 n=100/组，求多臂多阶段(MAMS)设计可达效能
# Reverse: n=100 per group → achieved power for MAMS design
python scripts/samplesize_power.py --test mams --nobs 100
```

**覆盖全部 31 种检验类型 / Covers all 31 test types.** 反向求解实现策略：
- **原生包反解**（优先）：`pwr.*`（`pwr.t.test(n=)` 等自动反解）、`PowerTOST::power.TOST(n=)`、`rpact::getPowerMeans/getPowerSurvival(n=)`，精确反解。
- **解析逆公式**：自写检验（ROC、Poisson、疫苗效力、多终点、贝叶斯、Win Ratio、MAMS 等）通过非中心参数逆推 `z_b`，再 `power = pnorm(z_b)`。
- **近似/精度型**：`bland_altman` 回报可达 CI 半宽（精度而非效能）；`dose_escalation` 为启发式设计，效能不适用；`conditional_power`/`assurance` 的 `--nobs` 直接映射至计划样本量/保证样本量。

*注：部分类型（如 `roc` 需 `--auc1`/`--effect`、`mixed_model` 需 `--effect_name`）在双向均要求提供必需参数，缺失时返回参数校验错误（符合预期）。*

---

## 曲线模式示例 / Curve Mode Examples

```bash
# Power 曲线：n = 20,40,...,200，叠加 3 条效应量曲线
python scripts/samplesize_power.py --test ttest_ind --n_seq "20:20:200" --plot_effects "0.3,0.5,0.8" --out power_curve.png

# 样本量曲线：power = 0.6,0.65,...,0.95
python scripts/samplesize_power.py --test ttest_ind --power_seq "0.6:0.05:0.95" --out n_curve.png
```

**曲线模式支持的检验类型（22 种）**：ttest_ind、ttest_paired、ttest_one、anova、proportion_one、proportion_two、proportion_paired、odds_ratio、risk_ratio、roc、poisson、non_inferiority、superiority_margin、be_tost、survival、ni_survival、mams、dunnett、group_sequential、survival_exact、equivalence、vaccine_efficacy。

曲线复用与单点求解**同一套已验证公式**（pwr / PowerTOST / 解析逆公式），数值完全一致；`group_sequential`、`survival_exact` 采用固定设计 / Schoenfeld 近似（图注已标注）。

其余类型（mixed_model、bayesian、win_ratio、must_win、historical_controls、assurance、conditional_power、adaptive、dose_escalation、bland_altman、cluster）曲线模式暂未覆盖，运行时会给出清晰提示。

---

## R 包安装 / Package Install

- **按需安装**：技能输出 `Warning: 'xxx' package not found.` 时执行 `install.packages("xxx")`
- **一键安装**：`python scripts/samplesize_power.py --install-all-packages`
- **无需 R 包**：`poisson`、`cluster`、`bland_altman`、`survival`（仅 Schoenfeld）、`vaccine_efficacy`、`bayesian`、`dose_escalation` 等

完整 R 包清单见 `references/r_packages_zh.md`。

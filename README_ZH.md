# ct-samplesize

[🇺🇳 English](./README.md) | [🇨🇳 中文 (Chinese, 当前)](#)

> **面向临床试验从业者的易用型样本量与检验效能计算工具**
>
> 本技能为临床试验从业人员提供一整套简单易用的样本量与检验效能计算工具。后台以 R 软件及 rpact/gsDesign/TrialSize/PowerTOST 等 20+ R工具包为依托，用户只需使用自然语言对话方式的提示词，就可以在中英双语的菜单式引导下，完成30+ 种复杂专业的样本量与检验效能计算工作。且**100% 提供可复现 R 代码**，供用户核查、递交代码或修改后重跑。
>
> **⚠️ R 代码默认展示**：默认展示 R 代码（dry-run），添加 `-y/--yes` 执行。

---

## 安装

无需额外安装。作为 WorkBuddy 技能自动加载。

### R 包安装（按需）

R 包**不需要全部预装**。技能在用到某包时自动提示安装：

```r
# 当输出: Warning: 'TrialSize' package not found.
install.packages("TrialSize")
```

**一键安装全部：**
```bash
python scripts/samplesize_power.py --install-all-packages
```

**或在 R 控制台：**
```r
install.packages(c("TrialSize","pwr","rpact","gsDesign","PowerTOST","simr","lme4","pROC","powerSurvEpi","survival"))
```

**无需 R 包的检测类型：** `poisson`, `cluster`, `bland_altman`, `vaccine_efficacy`, `bayesian`, `dose_escalation`, `survival`（仅 Schoenfeld）, `must_win`, `multiple_endpoints`, `assurance`, `dunnett`, `mediation`, `win_ratio`

---

## 快速开始

```
"对照组有效率20%，试验组35%，做两组率比较的卡方检验，α=0.05双侧，power=0.8"
"设计一个含1次期中分析的生存终点试验，HR=0.75，两组1:1随机"
"非劣效设计，margin=0.1，对照组有效率85%，试验组80%"
```

---

## 支持的检验类型（30+）

| 分类 | 检验类型 | 临床场景 | R 包 / 方法 |
|:---|:---|:---|:---|
| **连续变量** | `ttest_ind` | 两均数比较（平行设计） | `pwr`, `TrialSize` |
| | `ttest_paired` | 配对t / 交叉设计2×2 | `pwr`, `TrialSize` |
| | `anova` | 多组比较（k组） | `pwr`, `TrialSize` |
| | `equivalence` | 等效性检验（均数） | `TrialSize` |
| | `mixed_model` | 重复测量 / 纵向数据 | `simr` |
| **二分类** | `proportion_one` | 单组率检验 | `pwr` |
| | `proportion_two` | 两组率比较（卡方） | `pwr`, `TrialSize` |
| | `non_inferiority` | 非劣效设计（率） | `TrialSize` |
| | `be_tost` | 生物等效性 (TOST) | `PowerTOST` |
| | `superiority_margin` | 优效性检验（界值法） | `TrialSize` |
| **计数/事件率** | `poisson` | Poisson率 / 复发性事件 | Wald 检验 |
| | `vaccine_efficacy` | 疫苗效力 | Halloran 公式 |
| **生存分析** | `survival` | 生存分析（简化） | Schoenfeld 公式 |
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
| **高级终点** | `win_ratio` | Win-Ratio复合终点 | `BuyseTest` 模拟 |
| | `must_win` | Must-Win / 共主要终点 | 相关系数法 |
| | `historical_controls` | 历史对照借用 | `RBesT` MAP先验 |
| | `conditional_power` | 条件效能 / 样本量重估计 | `rpact` |
| | `assurance` | 贝叶斯确信度 | Monte Carlo |
| | `dunnett` | Dunnett 多重比较 | 自定义公式 |
| | `mediation` | 中介效应样本量 | `powerMediation` |

---

## CLI 命令示例

```bash
# === 连续变量 ===
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test ttest_paired --effect 0.5 --power 0.8
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.8
python scripts/samplesize_power.py --test equivalence --margin 2.0 --effect 3.0 --power 0.8
python scripts/samplesize_power.py --test mixed_model --effect 0.5 --nsim 500

# === 二分类 ===
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
python scripts/samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80 --power 0.8
python scripts/samplesize_power.py --test be_tost --theta0 0.95 --cv 0.25 --design "2x2"
python scripts/samplesize_power.py --test superiority_margin --sup_margin 0.05 --p_control_sup 0.3 --delta_sup 0.15

# === 计数 ===
python scripts/samplesize_power.py --test poisson --lambda1 0.05 --lambda2 0.03 --t1 2 --t2 2 --power 0.8
python scripts/samplesize_power.py --test vaccine_efficacy --ve_control 0.02 --ve_treatment 0.005 --power 0.8

# === 生存 ===
python scripts/samplesize_power.py --test survival --hazard_ratio 0.75 --power 0.85
python scripts/samplesize_power.py --test survival_exact --hr_exact 0.75 --accrual_exact 12 --followup_exact 0.85
python scripts/samplesize_power.py --test ni_survival --ni_margin_surv 1.25 --accrual_time 12 --followup_time 12

# === 诊断/方法比对 ===
python scripts/samplesize_power.py --test roc --auc0 0.5 --auc1 0.75 --power 0.8
python scripts/samplesize_power.py --test bland_altman --sd_diff 5 --w 2.5

# === 特殊设计 ===
python scripts/samplesize_power.py --test cluster --icc 0.05 --m 30 --n_indiv 64
python scripts/samplesize_power.py --test multiple_endpoints --effect 0.3 --correlation 0.5
python scripts/samplesize_power.py --test bayesian --prob_control 0.3 --prob_treatment 0.15 --prior_a0 0.5
python scripts/samplesize_power.py --test dose_escalation --n_doses 5 --target_dlt 0.33

# === 高级终点 (v3.3) ===
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

### 双向求解：给定样本量求检验效能

默认（`--power` 或省略）为**正向**：给定目标效能求解所需样本量 `n`。
传入 `--nobs N` 切换为**反向**：给定样本量求解可达检验效能（power）。
`--power` 与 `--nobs` **互斥**。

```bash
# 给定 n=50/组，求两独立样本 t 检验可达效能
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --nobs 50

# 给定 n=20/序列，求生物等效 TOST 可达效能
python scripts/samplesize_power.py --test be_tost --nobs 20

# 给定 n=100/组，求多臂多阶段(MAMS)设计可达效能
python scripts/samplesize_power.py --test mams --nobs 100
```

**覆盖全部 31 种检验类型。** 反向求解策略：优先使用原生包反解（`pwr.*`、`PowerTOST::power.TOST`、`rpact::getPowerMeans/getPowerSurvival`）；自写检验采用解析逆公式（非中心参数逆推 `z_b` 后 `power = pnorm(z_b)`）；精度型检验（`bland_altman`）回报可达 CI 半宽而非效能。

### 曲线模式：Power / 样本量曲线

在双向求解基础上，支持**批量绘制曲线**，直观展示样本量与检验效能的关系。

- `--n_seq "20,40,200"` → **Power 曲线**（x=样本量，y=效能）
- `--n_seq "20:20:200"` → 同上，但按「起:步:止」自动展开
- `--power_seq "0.6:0.05:0.95"` → **样本量曲线**（x=效能，y=样本量）
- `--plot_effects "0.3,0.5,0.8"` → 多效应量叠加多条曲线（敏感性分析）
- `--out path.png` → 指定 PNG 输出路径（默认写入系统临时目录）

```bash
# Power 曲线：n = 20,40,...,200，叠加 3 条效应量曲线
python scripts/samplesize_power.py --test ttest_ind --n_seq "20:20:200" --plot_effects "0.3,0.5,0.8" --out power_curve.png

# 样本量曲线：power = 0.6,0.65,...,0.95
python scripts/samplesize_power.py --test ttest_ind --power_seq "0.6:0.05:0.95" --out n_curve.png
```

**曲线模式支持 22 种检验类型**：ttest_ind、ttest_paired、ttest_one、anova、proportion_one、proportion_two、proportion_paired、odds_ratio、risk_ratio、roc、poisson、non_inferiority、superiority_margin、be_tost、survival、ni_survival、mams、dunnett、group_sequential、survival_exact、equivalence、vaccine_efficacy。曲线复用与单点求解**同一套已验证公式**，数值完全一致；`group_sequential`、`survival_exact` 采用固定设计 / Schoenfeld 近似（输出已标注）。其余类型（mixed_model、bayesian、win_ratio、must_win、historical_controls、assurance、conditional_power、adaptive、dose_escalation、bland_altman、cluster）曲线模式暂未覆盖，运行时会给出清晰提示。

---

## 核心公式

| 场景 | 公式 |
|:---|:---|
| 独立样本 t（等样本） | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| 率比较（arcsin） | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| 生存（Schoenfeld） | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |
| ROC（Obuchowski） | $n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{4(\arcsin\sqrt{AUC_1} - \arcsin\sqrt{AUC_0})^2}$ |
| 类随机 DEFF | $DEFF = 1 + (m - 1) \times ICC$ |
| Bland-Altman | $n = 2(\frac{Z_{1-\alpha/2} \times SD_{diff}}{W})^2$ |
| Win-Ratio（近似） | $n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\ln WR)^2 / SE_{approx}^2}$ |
| Must-Win 膨胀因子 | $n = n_{single} \times [1 + (k-1)\rho \times 0.5]$ |
| MAMS（Bonferroni） | $n = \frac{(Z_{1-\alpha/(2k)} + Z_{1-\beta})^2}{\delta^2}$ |
| 确信度 | $P(\text{success}) = \frac{1}{N}\sum_{i=1}^N I(\text{trial}_i \text{ significant})$ |

**完整公式推导：** `references/formulas_zh.md` | **扩展函数：** `references/extended_functions.md`

---

## 系统要求

| 组件 | 要求 |
|:-----|:-----|
| R | ≥ 4.1.0（推荐 ≥ 4.1.0） |
| Python | ≥ 3.8 + statsmodels ≥ 0.14, numpy ≥ 1.24, scipy ≥ 1.11 |
| 操作系统 | Windows / macOS / Linux |

---

## 常见错误

| 错误 | 解决方案 |
|:-----|:---------|
| "Rscript not found" | 安装 R 或指定路径 |
| "package not found" | install.packages("xxx") |
| ImportError: statsmodels | pip install statsmodels |
| simr timeout | 减少 --nsim 或简化模型 |
| BuyseTest convergence | 增加 n_sim，检查先验分布 |
| rpact error | 更新 rpact 至最新版本 |

---

## 安全与声明

- 生成的 R 代码默认展示（dry-run）；`-y/--yes` 才执行
- 纯本地计算，无数据外传
- 输出仅供参考，监管申报前需独立验证

---

## 文件结构

```
ct-samplesize/
├── SKILL.md              ← 技能定义（中英双语，精简版）
├── README.md             ← 英文版说明
├── README_ZH.md          ← 中文版说明（当前）
├── AGENTS.md             ← 核心执行规则（中英双语）
├── assets/
│   └── icon.svg          ← 技能图标 (104×104)
├── scripts/
│   └── samplesize_power.py  ← Python 计算 + 自动 R 代码生成
└── references/
    ├── r_packages_zh.md     ← R 包推荐（20+ 包）
    ├── formulas_zh.md       ← 公式推导
    ├── python_usage.md      ← Python 速查
    ├── r_usage.md           ← R 速查
    ├── effect_size.md       ← 效应量标准 (d/f/h + Z 值表)
    ├── report_template.md   ← 汇报模板 + 强制 R 代码模板
    ├── data_format_guide.md ← 31 种检验数据框架 + 示例
    └── examples.md          ← 3 个完整走查（率比较/GS/非劣效）
```

---

## 核心功能

1. **智能环境检测**：每次触发自动检测 R 安装
2. **双路径**：Python（简单）+ R（精确）
3. **强制 R 代码**：无论哪种路径，始终提供可复现 R 代码
4. **全面**：20+ R 包，完整公式推导，3 个完整示例
5. **自然语言**：日常语言描述试验设计即可
6. **中英双语**：完整 EN/CN 支持，自动检测语言

---

## 参考文献

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

## 开源代码

https://github.com/medstatstar/ct-samplesize

---

**Version**: v3.3.0 | **License**: MIT | **Authors**: medstatstar, phoe-zip

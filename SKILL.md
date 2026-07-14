---
slug: ct-samplesize
displayName: 临床试验样本量与检验效能计算专家 / Clinical Trial Sample Size & Power
name: ct-samplesize
cn_name: 临床试验样本量与检验效能计算专家
version: 3.3.1
required_commands: [Rscript, python]
summary: 为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，自然语言驱动，支持 30+ 种检验，100% 提供可复现 R 代码。
license: MIT
description: "Easy-to-use sample size & power calculator for clinical trial researchers. R backend + 20+ packages (rpact/gsDesign/TrialSize/PowerTOST). Natural language driven. 30+ test types. Bilingual EN/CN. 100% reproducible R code. | 为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，用户仅需自然语言提示词，即可在中英双语菜单引导下完成 30+ 种复杂计算，且 100% 提供可复现 R 代码。"
triggers:
  - "clinical trial sample size"
  - "clinical trial power"
  - "样本量计算"
  - "检验效能计算"
  - "临床试验 样本量"
  - "临床 trial 设计"
  - "mixed model sample size"
  - "repeated measures power"
  - "diagnostic trial sample size"
  - "cluster randomized sample size"
  - "vaccine clinical trial"
  - "dose escalation trial"
  - "Bayesian clinical trial"
  - "混合模型 样本量"
  - "重复测量 检验效能"
  - "诊断试验 样本量"
  - "类随机设计"
  - "疫苗 临床试验"
  - "剂量递增 试验"
  - "贝叶斯 临床试验"
  - "期中分析 试验"
  - "适应性设计 试验"
  - "非劣效 临床试验"
  - "等效性 临床试验"
  - "生物等效性 试验"
  - "组序贯 试验"
  - "多臂试验 设计"
  - "生存分析 样本量"
  - "win-ratio sample size"
  - "must-win endpoints"
  - "co-primary endpoints"
  - "historical controls borrowing"
  - "MAMS sample size"
  - "conditional power"
  - "sample size re-estimation"
  - "assurance Bayesian"
  - "superiority margin"
  - "Dunnett comparisons"
  - "mediation sample size"
  - "复合终点 样本量"
  - "历史对照 样本量"
  - "样本量重估计"
  - "贝叶斯确信度"
  - "多臂多阶段 设计"
metadata:
  openclaw: { emoji: "📊" }
  authors: ["medstatstar", "phoe-zip"]
  license: "MIT"
  tags: [clinical-trial, sample-size, power, R, adaptive-design, bayesian, win-ratio]
  homepage: "https://github.com/medstatstar/ct-samplesize"
  permissions:
    scope: "user-space-only"
    network: "none"
    filesystem: "read-only (except temp R script in skill dir)"
    data: "no external data transmission"
---

# Clinical Trial Sample Size & Power / 临床试验样本量与检验效能计算专家

> Auto detect → recommend → calculate & explain | 自动检测环境 → 推荐最优工具 → 完成计算与解释
>
> **⚠️ R Code Always Shown**: Executes by default and returns results, **always showing the generated R code** for review. Use `--dry-run` to preview code only. | **⚠️ R 代码始终展示**：默认执行并返回结果，**始终附上生成的 R 代码**供浏览。加 `--dry-run` 仅预览代码、不执行。
>
> **Output language / 输出语言**: Explanations follow the user's language by default (bilingual EN/CN menus are available on request); this is a preference, not a hard requirement. | 解释默认跟随用户使用的语言（如需可提供中英双语菜单引导）；此为偏好而非强制。

## Purpose / 技能目的

**CN:** 本技能为临床试验从业人员提供一整套简单易用的样本量与检验效能计算工具。后台以 R 软件及 rpact/gsDesign/TrialSize/PowerTOST 等 20+ R 工具包为依托，用户只需使用自然语言对话方式的提示词，就可以在中英双语的菜单式引导下，完成 30+ 种复杂专业的样本量与检验效能计算工作。且 **100% 提供可复现 R 代码**，供用户核查、递交代码或修改后重跑。

**EN:** This skill provides clinical trial researchers with an easy-to-use, comprehensive sample size & power calculation tool. Powered by R and 20+ professional R packages (rpact, gsDesign, TrialSize, PowerTOST, etc.), users can perform 30+ complex calculations through natural language prompts — bilingual EN/CN menu-driven. **100% reproducible R code** for verification, submission, or re-execution.

---

## Features / 功能特性

除基础的"给定目标效能 → 求解样本量"外，本技能还提供三项进阶能力，覆盖方案设计阶段最常见的分析需求：

| 能力 | 说明 | 典型场景 |
|:---|:---|:---|
| **① 样本量 ⇄ 检验效能 双向计算** | 除正向求解样本量外，支持给定固定样本量反解可达检验效能（power）。`--power`（正向）与 `--nobs`（反向）互斥，覆盖全部 31 种检验类型。 | 样本量已定，评估把握度是否达标 |
| **② 样本量变化曲线图** | 给定一组样本量序列，批量计算并绘制 **Power 曲线**（横轴=样本量，纵轴=检验效能），直观呈现"样本量越大、效能越高"的走势，并叠加目标效能参考线。 | 样本量敏感性分析、方案汇报 |
| **③ 检验效能变化曲线图** | 给定一组效能目标序列，批量计算并绘制 **样本量曲线**（横轴=目标效能，纵轴=所需样本量），一眼看出"要达到某把握度需多少样本"。 | 资源规划、可行性评估 |

- ② ③ 曲线模式支持**两种序列输入**：显式列表 `"20,40,200"` 或自动生成 `"20:20:200"`（起:步:止），并可叠加多条效应量曲线做敏感性分析，默认输出 PNG 并附数据表。
- ① 的反向求解与 ②③ 的曲线均**复用与单点求解同一套已验证公式**，数值完全一致。
- 详细命令参数、31 种检验示例与曲线支持的检验类型清单，分别见下方 *Implementation / 实施* 与 `references/cli_examples.md`。

---

## Quick Menu / 快速引导菜单

> 完整检验类型对照表与全部命令行示例见 `references/cli_examples.md`（含 31 种检验、双向求解、曲线模式、R 包安装）。

> **如何选择：** 1️⃣ 终点类型 2️⃣ 假设方向 3️⃣ 设计复杂度；不确定时从该参考文件查表。

---

## Requirements / 要求

| Requirement | Details |
|:---|:---|
| **R** | ≥ 4.1.0（按需安装，详见 `references/r_packages_zh.md`）|
| **Python** | ≥ 3.8 + statsmodels==0.14.2, numpy==1.24.3, scipy==1.11.4 |

---

## ⚠️ Safety / 安全

- R code is **executed by default** and the code is **always displayed**; `--dry-run` previews code only (no execution)
- All computations are local; no data transmission
- Outputs for reference only; validate before regulatory submissions
- 默认**执行并返回结果**，且 R 代码**始终展示**；`--dry-run` 仅预览代码、不执行
- 纯本地计算，无数据外传
- 输出仅供参考，监管申报前需独立验证

### Security model / 安全模型（透明披露）

本技能的行为已在此显式披露，便于审计：

| 行为 | 说明 |
|:---|:---|
| **本地进程调用** | 通过 `subprocess.run([Rscript, '--vanilla', tmp])` 在本地运行动态生成的 R 代码，超时 300s；不启动网络服务、不执行任意用户输入命令。 |
| **R 代码来源** | 全部由本技能内置模板参数化生成（`scripts/r_templates/`），无静态 `.R` 文件、不下载远程脚本。生成的代码始终打印供审阅。 |
| **输出脱敏** | R 的 stdout/stderr 经 `sanitize_output()` 过滤本地绝对路径并截断超长内容后再展示，避免泄露环境信息或注入过长内容。 |
| **网络访问** | 常规计算**全程离线**。唯一联网点是 R 包安装，且**默认只打印命令不执行**，须显式追加 `--run-install` 才会从 CRAN 下载安装（供应链风险由用户知情后触发）。 |
| **文件系统** | 仅在技能目录/系统临时目录写入临时 R 脚本，用后即弃；不读写用户数据文件。 |

---

## Implementation / 实施

> Default = execute & show R code. Add `--dry-run` to preview code only. | 默认执行并展示 R 代码，添加 `--dry-run` 仅预览代码。
> **数据格式指南：** `references/data_format_guide.md`

> **全部 31 种检验的命令行示例**见 `references/cli_examples.md` → *Implementation Examples*。

### 双向求解：给定样本量求效能 / Reverse — Power given N

默认 `--power`（或省略）为**正向**：给定目标效能 → 求解所需样本量 `n`。
传入 `--nobs N` 切换为**反向**：给定样本量 → 求解可达检验效能（power）。
`--power` 与 `--nobs` **互斥**，同时传入时以 `--nobs` 为准。

Bidirectional solving: omit `--nobs` (or set `--power`) to solve for **n** given target power;
pass `--nobs N` to solve for **achieved power** given a fixed sample size. The two flags are mutually exclusive.

> **反向求解命令行示例**见 `references/cli_examples.md` → *Reverse Examples*。

**覆盖全部 31 种检验类型 / Covers all 31 test types.** 反向求解实现策略：
- **原生包反解**（优先）：`pwr.*`（`pwr.t.test(n=)` 等自动反解）、`PowerTOST::power.TOST(n=)`、`rpact::getPowerMeans/getPowerSurvival(n=)`，精确反解。
- **解析逆公式**：自写检验（ROC、Poisson、疫苗效力、多终点、贝叶斯、Win Ratio、MAMS 等）通过非中心参数逆推 `z_b`，再 `power = pnorm(z_b)`。
- **近似/精度型**：`bland_altman` 回报可达 CI 半宽（精度而非效能）；`dose_escalation` 为启发式设计，效能不适用；`conditional_power`/`assurance` 的 `--nobs` 直接映射至计划样本量/保证样本量。

*注：部分类型（如 `roc` 需 `--auc1`/`--effect`、`mixed_model` 需 `--effect_name`）在双向均要求提供必需参数，缺失时返回参数校验错误（符合预期）。*

### 曲线模式：Power / Sample-size 曲线

在双向求解基础上，支持**批量绘制曲线**，直观展示样本量与检验效能的关系。

- `--n_seq`：给定样本量序列 → 绘制 **Power 曲线**（x=样本量, y=效能）
- `--power_seq`：给定效能序列 → 绘制 **样本量曲线**（x=效能, y=样本量）
- 序列支持两种格式（均支持）：
  - **显式列表**：`"20,40,200"`
  - **自动生成**：`"20:20:200"`（起:步:止，自动展开为 20,40,…,200）
- `--plot_effects "0.3,0.5,0.8"`：多效应量叠加多条曲线（敏感性分析，仅部分类型支持）
- `--out path.png`：指定 PNG 输出路径（默认写入系统临时目录）

> **曲线模式命令行示例**见 `references/cli_examples.md` → *Curve Mode Examples*。

**曲线模式支持的检验类型（22 种）**：ttest_ind、ttest_paired、ttest_one、anova、proportion_one、proportion_two、proportion_paired、odds_ratio、risk_ratio、roc、poisson、non_inferiority、superiority_margin、be_tost、survival、ni_survival、mams、dunnett、group_sequential、survival_exact、equivalence、vaccine_efficacy。

曲线复用与单点求解**同一套已验证公式**（pwr / PowerTOST / 解析逆公式），数值完全一致；`group_sequential`、`survival_exact` 采用固定设计 / Schoenfeld 近似（图注已标注）。

其余类型（mixed_model、bayesian、win_ratio、must_win、historical_controls、assurance、conditional_power、adaptive、dose_escalation、bland_altman、cluster）曲线模式暂未覆盖，运行时会给出清晰提示。

### R 包安装（默认仅打印命令，需二次确认）

出于供应链安全考虑，本技能**不会自动联网安装** R 包：

- **查看安装命令（默认，安全）**：`python scripts/samplesize_power.py --install-all-packages`
  仅打印 `install.packages()` 命令供人工审阅，**不联网、不执行**。
- **确认后真正安装**：`python scripts/samplesize_power.py --install-all-packages --run-install`
  显式追加 `--run-install` 才会从 CRAN 联网下载并安装 10 个 R 包。
- 也可将打印出的命令复制到 R 控制台中手动执行，完全避免脚本联网。
- 完整 R 包清单与按需安装说明见 `references/cli_examples.md` → *R 包安装* 及 `references/r_packages_zh.md`。

---

## Formulas & Reports / 公式与报告

**公式：** `references/formulas_zh.md` | **完整函数：** `references/extended_functions.md`

| Scenario | Formula |
|:---|:---|
| Independent t | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| Proportion (arcsin) | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| Survival (Schoenfeld) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |
| Cluster DEFF | $DEFF = 1 + (m - 1) \times ICC$ |

---

## Errors / 常见错误

| Error | Fix |
|:---|:---|
| "Rscript not found" | Install R or specify path |
| "package not found" | install.packages("xxx") |
| ImportError: statsmodels | pip install statsmodels |
| simr timeout | Reduce --nsim |

---

**Version**: v3.3.0 | **Updated**: 2026-07-13 | **License**: MIT

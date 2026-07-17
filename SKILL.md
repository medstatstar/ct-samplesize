---
slug: ct-samplesize
displayName: 临床试验样本量与检验效能计算专家 / Clinical Trial Sample Size & Power
name: ct-samplesize
cn_name: 临床试验样本量与检验效能计算专家
version: 3.3.7
required_commands: [Rscript, python]
summary: 为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，自然语言驱动，支持 37 种检验，可应要求提供 R 代码（默认不展示）；默认英文输出，中文操作系统自动切换中文。
license: MIT
description: "Easy-to-use sample size & power calculator for clinical trial researchers. R backend + 20+ packages (rpact/gsDesign/TrialSize/PowerTOST). Natural language driven. 37 test types. English by default, auto-switches to Chinese on Chinese-OS (locale zh/CN). Reproducible R code available on request (hidden by default). | 为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，用户仅需自然语言提示词，即可完成 37 种复杂计算（默认英文输出；当操作系统为中文环境时自动切换为中文），可应要求提供可复现 R 代码（默认不展示）。"
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
    network: "optional"
    network_note: "Used ONLY by --run-install to fetch R packages from CRAN. Default analysis mode is fully offline; no network is touched unless the user explicitly adds --run-install."
    filesystem: "read-only (except temp R script in skill dir / system temp)"
    data: "no external data transmission (except CRAN download under --run-install)"
---

# Clinical Trial Sample Size & Power / 临床试验样本量与检验效能计算专家

> Auto detect → recommend → calculate & explain | 自动检测环境 → 推荐最优工具 → 完成计算与解释
>
> **⚠️ R 代码默认不提供（仅按需）**: 默认执行并返回结果，**不展示 R 代码**；仅在**使用者明确要求**时才提供可复现代码（有 R 时附 R 代码，无 R 时附 Python 代码）。默认回复末尾提示"如需可复现 R 代码请告知"。命令行可用 `--show-code` 执行并展示代码，或 `--dry-run` 仅预览不执行。 | **⚠️ R code hidden by default (on request only)**: Execute & return results without showing code; show reproducible code ONLY when the user explicitly asks. End the default reply with a note like "Ask me if you want the reproducible R code." CLI: `--show-code` executes & shows, `--dry-run` previews only.
>
> **Output language / 输出语言**: **Default = English** for all user-facing content; **auto-switch to Chinese** when the OS environment is Chinese (locale contains `zh`/`CN`, e.g., `LANG=zh_CN.UTF-8` or Windows UI language `zh-CN`). Common modules must prepare BOTH English & Chinese prompt content; complex/rarely-used modules may temporarily be English-only. This setting does not affect code output. | **默认全部英文**，但**当操作系统为中文环境时自动切换为中文**（locale 含 `zh`/`CN`，如 `LANG=zh_CN.UTF-8` 或 Windows UI 语言 `zh-CN`）。**常用模块须同时准备英文与中文两套提示内容**；**复杂/少用模块可暂只提供英文**。此设置不影响代码输出。

### Language policy / 语言策略

- **默认英文**：所有面向用户的提示内容（报告、解释、菜单）默认使用英文。
- **中文环境自动切换**：检测到操作系统为中文环境（locale 含 `zh`/`CN`）时，给用户的提示内容**自动切换为中文**，无需用户显式要求。
  - 检测方法：Linux/macOS 读取 `LANG` / `LC_ALL` / `LANGUAGE`；Windows 用 `Get-Culture` / `Get-WinSystemLocale` 或 `os` 环境变量判断语言代码是否以 `zh` 开头（如 `zh-CN`）。
- **常用模块须备双语（英文 + 中文两套提示内容）**：
  - 常用检验类型：`ttest_ind`、`ttest_paired`、`ttest_one`、`anova`、`proportion_one` / `proportion_two` / `proportion_paired`、`odds_ratio`、`risk_ratio`、`roc`、`poisson`、`non_inferiority`、`superiority_margin`、`be_tost`、`equivalence`、`survival`、`ni_survival`、`cluster`、`dunnett`
  - 通用组件：报告模板（`references/report_template.md`）、快速引导菜单、参数速查表
- **复杂 / 少用模块可暂只英文**（后续再补中文）：`group_sequential`、`adaptive`、`mixed_model`、`bayesian`、`win_ratio`、`must_win`、`historical_controls`、`assurance`、`conditional_power`、`dose_escalation`、`bland_altman`、`vaccine_efficacy`、`mams`、`survival_exact`、`mediation`
- 此策略**不影响代码输出**：R / Python 代码本身始终为英文，按 `--show-code` 规则展示。

## Purpose / 技能目的

**CN:** 本技能为临床试验从业人员提供一整套简单易用的样本量与检验效能计算工具。后台以 R 软件及 rpact/gsDesign/TrialSize/PowerTOST 等 20+ R 工具包为依托，用户只需使用自然语言对话方式的提示词，即可完成（默认英文输出，OS 中文环境时自动切换中文）37 种复杂专业的样本量与检验效能计算工作。默认不主动提供代码，**仅在用户要求时**附上可复现 R 代码（无 R 时附 Python 代码），供用户核查、递交或修改后重跑。

**EN:** This skill provides clinical trial researchers with an easy-to-use, comprehensive sample size & power calculation tool. Powered by R and 20+ professional R packages (rpact, gsDesign, TrialSize, PowerTOST, etc.), users can perform 37 complex calculations through natural language prompts — English by default, auto-Chinese on Chinese-OS (locale zh/CN). **Reproducible code available on request (hidden by default)**: R code when R is available, Python (statsmodels/scipy) code when R is not, for verification, submission, or re-execution.

---

## Features / 功能特性

除基础的"给定目标效能 → 求解样本量"外，本技能还提供三项进阶能力，覆盖方案设计阶段最常见的分析需求：

| 能力 | 说明 | 典型场景 |
|:---|:---|:---|
| **① 样本量 ⇄ 检验效能 双向计算** | 除正向求解样本量外，支持给定固定样本量反解可达检验效能（power）。`--power`（正向）与 `--nobs`（反向）互斥，覆盖全部 37 种检验类型。 | 样本量已定，评估把握度是否达标 |
| **② 样本量变化曲线图** | 给定一组样本量序列，批量计算并绘制 **Power 曲线**（横轴=样本量，纵轴=检验效能），直观呈现"样本量越大、效能越高"的走势，并叠加目标效能参考线。 | 样本量敏感性分析、方案汇报 |
| **③ 检验效能变化曲线图** | 给定一组效能目标序列，批量计算并绘制 **样本量曲线**（横轴=目标效能，纵轴=所需样本量），一眼看出"要达到某把握度需多少样本"。 | 资源规划、可行性评估 |

- ② ③ 曲线模式支持**两种序列输入**：显式列表 `"20,40,200"` 或自动生成 `"20:20:200"`（起:步:止），并可叠加多条效应量曲线做敏感性分析，默认输出 PNG 并附数据表。
- ① 的反向求解与 ②③ 的曲线均**复用与单点求解同一套已验证公式**，数值完全一致。
- 详细命令参数、37 种检验示例与曲线支持的检验类型清单，分别见下方 *Implementation / 实施* 与 `references/cli_examples.md`。

---

## Quick Menu / 快速引导菜单

> 完整检验类型对照表与全部命令行示例见 `references/cli_examples.md`（含 37 种检验、双向求解、曲线模式、R 包安装）。

> **如何选择：** 1️⃣ 终点类型 2️⃣ 假设方向 3️⃣ 设计复杂度；不确定时从该参考文件查表。

---

## Requirements / 要求

| Requirement | Details |
|:---|:---|
| **R** | ≥ 4.1.0（按需安装，详见 `references/r_packages_zh.md`）|
| **Python** | ≥ 3.8 + statsmodels==0.14.2, numpy==1.24.3, scipy==1.11.4 |

---

## ⚠️ Safety / 安全

- R code is **executed by default** but **hidden from output**; shown only on request (`--show-code`), `--dry-run` previews code only (no execution)
- All computations are local; no data transmission
- Outputs for reference only; validate before regulatory submissions
- 默认**执行并返回结果**，R 代码**默认不展示**；仅当使用者要求时提供（`--show-code` 展示或回复中提示可提供），`--dry-run` 仅预览代码、不执行
- 纯本地计算，无数据外传
- 输出仅供参考，监管申报前需独立验证

### Security model / 安全模型（透明披露）

本技能的行为已在此显式披露，便于审计：

| 行为 | 说明 |
|:---|:---|
| **本地进程调用** | 通过 `subprocess.run([Rscript, '--vanilla', tmp])` 在本地运行动态生成的 R 代码，超时 300s；不启动网络服务、不执行任意用户输入命令。 |
| **R 代码来源** | 全部由本技能内置模板参数化生成（`scripts/r_templates/`），无静态 `.R` 文件、不下载远程脚本。生成的代码默认不打印；仅当使用者要求（`--show-code`）或 `--dry-run` 预览时才展示。 |
| **输出脱敏** | R 的 stdout/stderr 经 `sanitize_output()` 过滤本地绝对路径并截断超长内容后再展示，避免泄露环境信息或注入过长内容。 |
| **网络访问** | **默认计算全程离线、零联网**。唯一联网点是可选的 R 包安装：默认仅打印 `install.packages()` 命令、不执行；须**显式追加 `--run-install`** 才会从 CRAN 下载安装（供应链风险由用户知情后触发）。权限清单已据此声明 `network: "optional"`（仅 `--run-install` 使用）。执行前会完整打印将要运行的安装 R 代码。 |
| **文件系统** | 仅在技能目录/系统临时目录写入临时 R 脚本，用后即弃；不读写用户数据文件。 |

---

## Implementation / 实施

> Default = execute & return result (R code hidden by default; use `--show-code` to display, or `--dry-run` to preview only). | 默认执行并返回结果（R 代码默认不展示；用 `--show-code` 展示，或 `--dry-run` 仅预览）。
> **数据格式指南：** `references/data_format_guide.md`

> **全部 37 种检验的命令行示例**见 `references/cli_examples.md` → *Implementation Examples*。

### 双向求解：给定样本量求效能 / Reverse — Power given N

默认 `--power`（或省略）为**正向**：给定目标效能 → 求解所需样本量 `n`。
传入 `--nobs N` 切换为**反向**：给定样本量 → 求解可达检验效能（power）。
`--power` 与 `--nobs` **互斥**，同时传入时以 `--nobs` 为准。

Bidirectional solving: omit `--nobs` (or set `--power`) to solve for **n** given target power;
pass `--nobs N` to solve for **achieved power** given a fixed sample size. The two flags are mutually exclusive.

> **反向求解命令行示例**见 `references/cli_examples.md` → *Reverse Examples*。

**覆盖全部 37 种检验类型 / Covers all 37 test types.** 反向求解实现策略：
- **原生包反解**（优先）：`pwr.*`（`pwr.t.test(n=)` 等自动反解）、`PowerTOST::power.TOST(n=)`、`rpact::getPowerMeans/getPowerSurvival(n=)`，精确反解。
- **解析逆公式**：自写检验（ROC、Poisson、疫苗效力、多终点、贝叶斯、Win Ratio、MAMS 等）通过非中心参数逆推 `z_b`，再 `power = pnorm(z_b)`。
- **近似/精度型**：`bland_altman` 回报可达 CI 半宽（精度而非效能）；`dose_escalation` 为启发式设计，效能不适用；`conditional_power`/`assurance` 的 `--nobs` 直接映射至计划样本量/保证样本量。

*注：部分类型（如 `roc` 需 `--auc1`/`--effect`、`mixed_model` 需 `--effect_name`）在双向均要求提供必需参数，缺失时返回参数校验错误（符合预期）。*

> **实现架构（v3.3.5）**：本技能所有检验算法均以**预编写的 R 函数**（`ss_*`）形式提供，存放于 `scripts/r_templates/` 下各模板文件；`samplesize_power.py` 的主分发逻辑仅做参数注入与模板 `.format()` 调用，**不再包含散落的 R 代码片段**。含 R 包的类型（`equivalence` / `be_tost` / `survival_exact` / `ni_survival` / `group_sequential` / `adaptive` / `mixed_model` 等）在包调用失败时均自动回退至解析闭式近似（Schoenfeld / O'Brien-Fleming 等），保证结果稳定、可复现、零崩溃。
>
> **安全加固（v3.3.5，对应 ClawHub 审计 9 findings）**：① 权限清单 `network` 由 `none` 改为 `optional`，并显式声明仅 `--run-install` 从 CRAN 下载；② R 执行前校验 `Rscript` 为真实二进制（`is_valid_rscript`），临时脚本路径做 containment 检查，`subprocess` 以列表调用（无 shell，杜绝命令注入），并对生成的 R 代码做危险 token 拦截（`system`/`eval`/`source`/`download.file`/`shell`/反引号等）；③ `--run-install` 执行前完整打印将运行的安装 R 代码并加网络横幅，消除"透明性落差"。审计 #7「强制双语+必给R代码」已按用户指示解决：**默认英文、不强制双语，但 OS 中文环境时自动切换中文**（中文可应要求提供），**R 代码默认不提供，仅使用者明确要求时提供（默认回复提示可提供）**，与用户最新指示一致。

### 常用参数：检验方向 `--side` 与效应量输入 `--sd`

- **`--side one|two`**（默认 `two`）：检验方向。`one` = 单侧（`alternative="greater"`，预期处理组更优）；`two` = 双侧。影响 t 检验、比例类检验（`proportion_one` / `proportion_two` / `proportion_paired` / `odds_ratio` / `risk_ratio`）及曲线模式的显著性水平与所需样本量。比例类自 v3.3.2 起统一以 R 函数（`ss_prop_one` / `ss_prop_two` / `ss_prop_paired` / `ss_or_rr`）形式提供，并接 `alternative`。
- **`--sd FLOAT`**（可选）：提供时，`--effect` 视为**原始均差 Δ**（如 0.5 mmol/L），脚本自动折算 **Cohen's d = Δ / sd**；不提供时 `--effect` 直接作为 Cohen's d。避免手动换算，更贴合医学文献"差值 + 标准差"的报法。

示例（两独立组、单侧、Δ=0.5、sd=0.8 → d=0.625）：

```bash
python scripts/samplesize_power.py --test ttest_ind --side one --sd 0.8 --effect 0.5 --power 0.9
# → n = 45 / 组（单侧）；双侧则 n = 53 / 组
```

### 曲线模式：Power / Sample-size 曲线

在双向求解基础上，支持**批量绘制曲线**，直观展示样本量与检验效能的关系。

- `--n_seq`：给定样本量序列 → 绘制 **Power 曲线**（x=样本量, y=效能）
- `--power_seq`：给定效能序列 → 绘制 **样本量曲线**（x=效能, y=样本量）
- 序列支持两种格式（均支持）：
  - **显式列表**：`"20,40,200"`
  - **自动生成**：`"20:20:200"`（起:步:止，自动展开为 20,40,…,200）
- `--plot_effects "0.3,0.5,0.8"`：多效应量叠加多条曲线（敏感性分析，仅部分类型支持）
- `--out path.png`：指定 PNG 输出路径（默认写入系统临时目录）
- **绘图零额外依赖**：曲线图使用 **基础 R 图形**（`png()`+`plot()`+`abline()`）绘制，**无需 `ggplot2`**；随 `pwr`/`PowerTOST` 等计算包一并加载即可，避免未安装包导致的失败。

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

**Version**: v3.3.7 | **Updated**: 2026-07-17 | **License**: MIT

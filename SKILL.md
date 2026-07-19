---
slug: ct-samplesize
displayName: 临床试验样本量与检验效能计算专家 / Clinical Trial Sample Size & Power
name: ct-samplesize
cn_name: 临床试验样本量与检验效能计算专家
version: 3.4.7
required_commands: [Rscript, python]
summary: 为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，自然语言驱动，支持 37 种检验。可应要求提供可复现 R 代码；默认英文输出，中文操作系统自动切换中文。
license: MIT
description: "为临床试验从业者提供的易用样本量与检验效能计算工具。后台依托 R + rpact/gsDesign/TrialSize/PowerTOST 等 20+ 专业 R 包，自然语言驱动，支持 37 种检验。可应要求提供可复现 R 代码；默认英文输出，中文操作系统自动切换中文。 / Easy-to-use sample size and power calculation tool for clinical trial practitioners. Backed by R + 20+ professional R packages including rpact/gsDesign/TrialSize/PowerTOST, natural language driven, supporting 37 test types. Reproducible R code available on request; default English output with auto-switch to Chinese on Chinese OS."
triggers:
  - "clinical trial sample size"
  - "样本量计算"
  - "clinical trial power"
  - "检验效能计算"
  - "临床试验 设计"
  - "non-inferiority sample size"
  - "非劣效 样本量"
  - "equivalence sample size"
  - "等效性 样本量"
  - "survival analysis sample size"
  - "生存分析 样本量"
  - "adaptive design"
  - "适应性设计"
  - "group sequential design"
  - "Bayesian clinical trial"
  - "贝叶斯 临床试验"
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
  filesystem: "writes only to system temp (generated R script) and to the current working directory (generated curve PNG reports); otherwise read-only"
  data: "no external data transmission (except CRAN download under --run-install)"
---

# Clinical Trial Sample Size & Power / 临床试验样本量与检验效能计算专家

> Auto detect → recommend → calculate & explain / 自动检测环境 → 推荐最优工具 → 完成计算与解释
>
> **⚠️ Safe by default — preview, not execute / 默认安全：仅预览、不执行**: By default the skill generates R code and shows it in a SAFE PREVIEW (no execution). Execution requires an explicit opt-in: CLI `--yes`/`-y`, or the agent adds `--yes` when it needs the actual number. `--show-code` shows code; `--dry-run` is the default preview mode. / 技能默认生成 R 代码并以**安全预览模式**展示（不执行）。执行需显式确认：命令行用 `--yes`/`-y`；Agent 在需要真实数值时显式加上 `--yes`。`--show-code` 展示代码；`--dry-run` 即默认预览模式。
>
> **Output language / 输出语言**: Default = English for all user-facing content; auto-switch to Chinese when the OS environment is Chinese (locale contains `zh`/`CN`, e.g. `LANG=zh_CN.UTF-8` or Windows UI language `zh-CN`). Common modules must prepare BOTH English & Chinese prompt content; complex/rarely-used modules may temporarily be English-only. This setting does not affect code output. / 默认全部英文，但当操作系统为中文环境时自动切换为中文（locale 含 `zh`/`CN`，如 `LANG=zh_CN.UTF-8` 或 Windows UI 语言 `zh-CN`）。常用模块须同时准备英文与中文两套提示内容；复杂/少用模块可暂只提供英文。此设置不影响代码输出。

### Language policy / 语言策略

> Detailed bilingual rules (detection, module list) in `references/language_policy.md`. Key: English by default; auto-switch to Chinese when OS locale is zh/CN; common modules prepare EN+ZH, complex/rare EN-only. Code output unaffected (always English). / 详细双语细则（检测方式、模块清单）见 `references/language_policy.md`。要点：默认英文；检测到 OS 为中文环境（locale 含 `zh`/`CN`）时自动切换中文；常用模块备英/中两套，复杂/少用模块暂只英文。代码输出不受影响（始终英文）。

- Applies the user-level "bilingual policy" (~/.workbuddy/MEMORY.md): this skill is a statistical-analysis skill published on ClawHub, so bilingual is required. / 本技能适用「双语语言策略」（用户级规范，见 `~/.workbuddy/MEMORY.md`）：属统计分析类且已发布 ClawHub，故需双语。
- Common modules (EN+ZH): `ttest_*`, `anova`, `proportion_*`, `odds_ratio`, `risk_ratio`, `roc`, `poisson`, `non_inferiority`, `superiority_margin`, `be_tost`, `equivalence`, `survival`, `ni_survival`, `cluster`, `dunnett` + report template / quick menu / flag reference. / 常用模块（英/中双套）：上述常用检验类型 + 报告模板/快速菜单/参数速查。
- Complex/rare modules (EN-only for now): `group_sequential`, `adaptive`, `adaptive_simulate`, `mixed_model`, `bayesian`, `win_ratio`, `historical_controls`, `assurance`, `conditional_power`, `dose_escalation`, `vaccine_efficacy`, `mams`, `survival_exact`, `mediation` etc. / 复杂/少用模块（暂只英文）：上述复杂/少用检验类型。

## Purpose / 技能目的

This skill provides clinical trial researchers with an easy-to-use, comprehensive sample size & power calculation tool. Powered by R and 20+ professional R packages (rpact, gsDesign, TrialSize, PowerTOST, etc.), users can perform 37 complex calculations through natural language prompts — English by default, auto-Chinese on Chinese-OS (locale zh/CN). Reproducible R code is available on request. / 本技能为临床试验从业人员提供一整套简单易用的样本量与检验效能计算工具。后台以 R 软件及 rpact/gsDesign/TrialSize/PowerTOST 等 20+ R 工具包为依托，用户只需使用自然语言对话方式的提示词，即可完成（默认英文输出，OS 中文环境时自动切换中文）37 种复杂专业的样本量与检验效能计算工作。可复现代码按需提供（无 R 时附 Python 代码）。

---

## Features / 功能特性

Beyond basic "solve n given target power", the skill offers three advanced capabilities covering the most common analysis needs in the design phase:

除基础的"给定目标效能 → 求解样本量"外，本技能还提供三项进阶能力，覆盖方案设计阶段最常见的分析需求：

| Capability 能力 | Description 说明 | Typical Scenario 典型场景 |
|:---|:---|:---|
| **① Sample size ⇄ Power (bidirectional) / ① 样本量 ⇄ 检验效能（双向计算）** | Solve n given target power, AND solve achievable power given fixed n. `--power` (forward) and `--nobs` (reverse) are mutually exclusive; covers all 37 types. / 除正向求解样本量外，支持给定固定样本量反解可达检验效能（power）。`--power`（正向）与 `--nobs`（反向）互斥，覆盖全部 37 种检验类型。 | Sample size fixed, evaluate if power meets target / 样本量已定，评估把握度是否达标 |
| **② Power curve / ② 样本量变化曲线图** | Given a sample-size sequence, batch-compute and plot the **Power curve** (x=sample size, y=power), with a target-power reference line. / 给定一组样本量序列，批量计算并绘制 **Power 曲线**（横轴=样本量，纵轴=检验效能），直观呈现"样本量越大、效能越高"的走势，并叠加目标效能参考线。 | Sample-size sensitivity analysis, protocol reporting / 样本量敏感性分析、方案汇报 |
| **③ Sample-size curve / ③ 检验效能变化曲线图** | Given a power-target sequence, batch-compute and plot the **sample-size curve** (x=target power, y=required n). / 给定一组效能目标序列，批量计算并绘制 **样本量曲线**（横轴=目标效能，纵轴=所需样本量），一眼看出"要达到某把握度需多少样本"。 | Resource planning, feasibility assessment / 资源规划、可行性评估 |

- ②③ curve mode supports two sequence formats: explicit list `"20,40,200"` or auto-generated `"20:20:200"` (start:step:stop); multiple effect-size curves can be overlaid for sensitivity analysis, default PNG output with a data table. / ②③ 曲线模式支持两种序列输入：显式列表 `"20,40,200"` 或自动生成 `"20:20:200"`（起:步:止），并可叠加多条效应量曲线做敏感性分析，默认输出 PNG 并附数据表。
- The ① reverse solve and ②③ curves reuse the same validated formulas as the single-point solve — numerically identical. / ① 的反向求解与 ②③ 的曲线均复用与单点求解同一套已验证公式，数值完全一致。
- Full command parameters, 37-test examples and the curve-supported type list: see *Implementation / 实施* below and `references/cli_examples.md`. / 详细命令参数、37 种检验示例与曲线支持的检验类型清单，分别见下方 *Implementation / 实施* 与 `references/cli_examples.md`。

---

## Quick Menu / 快速引导菜单

> Full test-type cross-reference table and all CLI examples: `references/cli_examples.md` (37 tests, bidirectional solve, curve mode, R package install). / 完整检验类型对照表与全部命令行示例见 `references/cli_examples.md`（含 37 种检验、双向求解、曲线模式、R 包安装）。

> **How to choose / 如何选择:** 1️⃣ endpoint type 2️⃣ hypothesis direction 3️⃣ design complexity; if unsure, look up the table in that reference file. / 1️⃣ 终点类型 2️⃣ 假设方向 3️⃣ 设计复杂度；不确定时从该参考文件查表。

### Adaptive-trial Monte-Carlo simulator / 自适应试验蒙特卡洛仿真器

Beyond the 37 analytic tests, `--test adaptive_simulate` runs a Monte-Carlo simulator to **validate** adaptive / group-sequential designs empirically: power, type I error, expected sample size, early-stop probabilities. **Primary engine: a standalone, `source()`-able pure base-R function library** (`scripts/adaptive_sim.R`) — `source()` it in R to call `run_adaptive_sim()` (one-shot with report) or the individual `simulate_group_sequential()` / `simulate_adaptive_reestimate()` / `simulate_drop_the_loser()` / `optimize_power()` functions directly. The CLI shows this `source(...)` + `run_adaptive_sim(...)` code in SAFE PREVIEW (like every other test) and executes it with `--yes`; it needs only base R (no extra packages). **Fallback: when R is not installed**, the skill automatically runs the equivalent pure-Python module `scripts/adaptive_simulator.py` so the user still gets results. Designs: `group_sequential`, `adaptive_reestimate` (promising-zone SSR with Cui-Hung-Wang statistic), `drop_the_loser` (multi-arm). Spending: `obrien_fleming` / `pocock` / `power_family`. Also supports `--futility`, `--optimize` (min-N search) and `--visualize`. Full guide: `index.md` / `references/adaptive_simulator.md`. / 除 37 种解析检验外，`--test adaptive_simulate` 运行蒙特卡洛仿真器经验验证自适应/成组序贯设计的功效、I 类错误、期望样本量与早停概率。**主引擎：独立、可直接 `source()` 的纯 base-R 函数库**（`scripts/adaptive_sim.R`）——在 R 中 `source()` 后可直接调用 `run_adaptive_sim()`（一键出报告）或各底层函数 `simulate_group_sequential()`/`simulate_adaptive_reestimate()`/`simulate_drop_the_loser()`/`optimize_power()`。CLI 默认以安全预览展示该 `source(...)` + `run_adaptive_sim(...)` 代码、用 `--yes` 执行，仅需 base R（无需额外 R 包）。**备用：当本机未安装 R 时**，技能自动改跑等价的纯 Python 模块 `scripts/adaptive_simulator.py`，保证仍能出结果。设计含 `group_sequential`、`adaptive_reestimate`（promising-zone + CHW 统计量）、`drop_the_loser`（多臂）；消耗函数 `obrien_fleming`/`pocock`/`power_family`；支持 `--futility`、`--optimize`、`--visualize`。完整说明见 `index.md` / `references/adaptive_simulator.md`。

---

## Requirements / 要求

| Requirement 要求 | Details 详情 |
|:---|:---|
| **R** | ≥ 4.1.0 (install on demand, see `references/r_packages_zh.md`) / ≥ 4.1.0（按需安装，详见 `references/r_packages_zh.md`）|
| **Python** | ≥ 3.8 + statsmodels≥0.14.2, numpy≥1.24.3, scipy≥1.11.4. Used by the `adaptive_simulate` **no-R fallback** and `--visualize` (matplotlib≥3.4). R is the primary engine for `adaptive_simulate`. / 用于 `adaptive_simulate` 的**无 R 备用路径**与 `--visualize`（matplotlib≥3.4）。`adaptive_simulate` 的主引擎是 R。 |

---

## ⚠️ Safety / 安全

- R code is NOT executed by default — it runs in SAFE PREVIEW (code shown, not run); use `--yes`/`-y` to explicitly execute and compute / R 代码**默认不执行**，运行于安全预览模式（展示代码、不运行）；使用 `--yes`/`-y` 才显式执行并计算
- All computations are local; no data transmission / 纯本地计算，无数据外传
- Output for reference only; validate before regulatory submissions / 输出仅供参考，监管申报前需独立验证

### Security model / 安全模型（透明披露）

This skill's behavior is explicitly disclosed here for auditing:

本技能的行为已在此显式披露，便于审计：

| Behavior 行为 | Description 说明 |
|:---|:---|
| **Local process call / 本地进程调用** | Run DYNAMICALLY GENERATED (never raw user input) R code locally via `subprocess.run([Rscript, '--vanilla', tmp])`, timeout 300s, NO shell. Execution is OPT-IN: by default the code is only previewed; it runs only when `--yes` is passed. Every user string that reaches the R code is validated against a strict allowlist first, so it cannot break out of an R string (no RCE). / 在本地运行**动态生成（绝非原始用户输入）**的 R 代码，通过 `subprocess.run([Rscript, '--vanilla', tmp])`，超时 300s，无 shell。执行是**显式确认**的：默认仅预览代码，仅当传入 `--yes` 才运行。所有进入 R 代码的用户字符串都会先经严格白名单校验，无法逃逸出 R 字符串（杜绝 RCE）。 |
| **R code source / R 代码来源** | All generated by the skill's built-in templates (`scripts/r_templates/`), no static `.R` files, no remote script download. By default the skill runs in SAFE PREVIEW — generated R code is shown but NOT executed; `--yes` executes, `--show-code` reveals the code. / 全部由本技能内置模板参数化生成（`scripts/r_templates/`），无静态 `.R` 文件、不下载远程脚本。默认运行于安全预览模式——生成的 R 代码会展示但**不执行**；`--yes` 才执行，`--show-code` 展示代码。 |
| **Output sanitization / 输出脱敏** | R stdout/stderr passes through `sanitize_output()` to strip local absolute paths and truncate over-long content before display, avoiding environment leakage or content injection. / R 的 stdout/stderr 经 `sanitize_output()` 过滤本地绝对路径并截断超长内容后再展示，避免泄露环境信息或注入过长内容。 |
| **Network access / 网络访问** | Default analysis is fully offline, zero network. The only network touchpoint is the optional R-package install: by default it only prints `install.packages()` commands, not executed; you must explicitly add `--run-install` to download & install from CRAN (supply-chain risk triggered only after user is informed). The permission manifest declares `network: "optional"` (used only by `--run-install`). The full install R code is printed before execution. / 默认计算全程离线、零联网。唯一联网点是可选的 R 包安装：默认仅打印 `install.packages()` 命令、不执行；须显式追加 `--run-install` 才会从 CRAN 下载安装（供应链风险由用户知情后触发）。权限清单已据此声明 `network: "optional"`（仅 `--run-install` 使用）。执行前会完整打印将要运行的安装 R 代码。 |
| **Filesystem / 文件系统** | Writes only a temp R script in the skill dir / system temp, discarded after use; never reads/writes user data files. / 仅在技能目录/系统临时目录写入临时 R 脚本，用后即弃；不读写用户数据文件。 |

---

## Implementation / 实施

> Default = SAFE PREVIEW (dry-run): generate & show R code, do NOT execute. Add `--yes`/`-y` to execute and compute the result; `--show-code` also shows the code during execution. / 默认**安全预览（dry-run）**：生成并展示 R 代码，但不执行。追加 `--yes`/`-y` 才执行并计算；`--show-code` 在执行时也会展示代码。
> **Data format guide / 数据格式指南:** `references/data_format_guide.md`

> **All 37 test CLI examples / 全部 37 种检验的命令行示例** see `references/cli_examples.md` → *Implementation Examples*.

### Reverse — Power given N / 双向求解：给定样本量求效能

Default `--power` (or omitted) is **forward**: given target power → solve required sample size `n`. Pass `--nobs N` to switch to **reverse**: given sample size → solve achievable power. `--power` and `--nobs` are mutually exclusive; when both are passed, `--nobs` wins.

默认 `--power`（或省略）为**正向**：给定目标效能 → 求解所需样本量 `n`。传入 `--nobs N` 切换为**反向**：给定样本量 → 求解可达检验效能（power）。`--power` 与 `--nobs` **互斥**，同时传入时以 `--nobs` 为准。

Bidirectional solving: omit `--nobs` (or set `--power`) to solve for **n** given target power; pass `--nobs N` to solve for **achieved power** given a fixed sample size. The two flags are mutually exclusive.

反向求解命令行示例见 `references/cli_examples.md` → *Reverse Examples*.

**Covers all 37 test types / 覆盖全部 37 种检验类型.** Reverse-solve strategy:
- **Native package reverse / 原生包反解（优先）**: `pwr.*` (`pwr.t.test(n=)` auto-reverses), `PowerTOST::power.TOST(n=)`, `rpact::getPowerMeans/getPowerSurvival(n=)` — exact. / `pwr.*`（`pwr.t.test(n=)` 等自动反解）、`PowerTOST::power.TOST(n=)`、`rpact::getPowerMeans/getPowerSurvival(n=)`，精确反解。
- **Analytic inverse / 解析逆公式**: self-written tests (ROC, Poisson, vaccine efficacy, multi-endpoint, Bayesian, Win Ratio, MAMS etc.) back-solve `z_b` via non-centrality, then `power = pnorm(z_b)`. / 自写检验（ROC、Poisson、疫苗效力、多终点、贝叶斯、Win Ratio、MAMS 等）通过非中心参数逆推 `z_b`，再 `power = pnorm(z_b)`。
- **Approx/precision / 近似/精度型**: `bland_altman` returns achievable CI half-width (precision, not power); `dose_escalation` is heuristic design (power N/A); `conditional_power`/`assurance` `--nobs` maps directly to planned/assurance sample size. / `bland_altman` 回报可达 CI 半宽（精度而非效能）；`dose_escalation` 为启发式设计，效能不适用；`conditional_power`/`assurance` 的 `--nobs` 直接映射至计划样本量/保证样本量。

*Note: some types (e.g. `roc` needs `--auc1`/`--effect`, `mixed_model` needs `--effect_name`) require mandatory params in both directions; missing params returns a validation error (expected). / 注：部分类型（如 `roc` 需 `--auc1`/`--effect`、`mixed_model` 需 `--effect_name`）在双向均要求提供必需参数，缺失时返回参数校验错误（符合预期）。*

> **Implementation architecture / 实现架构**: All test algorithms are provided as pre-written R functions (`ss_*`) in `scripts/r_templates/`; the main dispatcher only injects params and calls `.format()` — no scattered R code. Types that use R packages auto-fall back to analytic closed-form approximations (Schoenfeld / O'Brien-Fleming etc.) on package failure — stable, reproducible, zero crash. / 所有检验算法以预编写的 R 函数（`ss_*`）形式提供，存放于 `scripts/r_templates/`；主分发脚本仅做参数注入与模板 `.format()` 调用，无散落 R 代码。含 R 包的类型在包调用失败时自动回退至解析闭式近似（Schoenfeld / O'Brien-Fleming 等），结果稳定可复现、零崩溃。
>
> **Security hardening & version history / 安全加固与版本历史** see `CHANGELOG.md` (v3.3.5 fix of ClawHub 9 findings, v3.3.8 permission-declaration fix). / 见 `CHANGELOG.md`（含 v3.3.5 对 ClawHub 审计 9 findings 的整改、v3.3.8 权限声明修复）。

### Common params: --side and --sd / 常用参数：检验方向 --side 与效应量输入 --sd

- **`--side one|two`** (default `two`): test direction. `one` = one-sided (`alternative="greater"`, expecting treatment better); `two` = two-sided. Affects t-test, proportion tests (`proportion_one`/`proportion_two`/`proportion_paired`/`odds_ratio`/`risk_ratio`) and the significance level / required n in curve mode. Proportion tests since v3.3.2 uniformly use R functions (`ss_prop_one`/`ss_prop_two`/`ss_prop_paired`/`ss_or_rr`) wired to `alternative`. / 检验方向。`one` = 单侧（`alternative="greater"`，预期处理组更优）；`two` = 双侧。影响 t 检验、比例类检验（`proportion_one` / `proportion_two` / `proportion_paired` / `odds_ratio` / `risk_ratio`）及曲线模式的显著性水平与所需样本量。比例类自 v3.3.2 起统一以 R 函数（`ss_prop_one` / `ss_prop_two` / `ss_prop_paired` / `ss_or_rr`）形式提供，并接 `alternative`。
- **`--sd FLOAT`** (optional): when provided, `--effect` is treated as the raw mean difference Δ (e.g. 0.5 mmol/L) and the script auto-computes **Cohen's d = Δ / sd**; when omitted, `--effect` is directly Cohen's d. Avoids manual conversion, fits the medical literature "difference + SD" reporting. / 提供时，`--effect` 视为原始均差 Δ（如 0.5 mmol/L），脚本自动折算 **Cohen's d = Δ / sd**；不提供时 `--effect` 直接作为 Cohen's d。避免手动换算，更贴合医学文献"差值 + 标准差"的报法。

Example (two independent groups, one-sided, Δ=0.5, sd=0.8 → d=0.625) / 示例（两独立组、单侧、Δ=0.5、sd=0.8 → d=0.625）：

```bash
python scripts/samplesize_power.py --test ttest_ind --side one --sd 0.8 --effect 0.5 --power 0.9
# → n = 45 / group (one-sided); two-sided → n = 53 / group
```

### Curve Mode: Power / Sample-size Curve / 曲线模式：Power / Sample-size 曲线

On top of bidirectional solving, supports batch curve plotting to visualize the sample-size ⇄ power relationship.

在双向求解基础上支持**批量绘制曲线**，直观展示样本量 ⇄ 检验效能关系。

- `--n_seq "20,40,200"` or `"20:20:200"` (start:step:stop) → **Power curve** (x=sample size, y=power) / `--n_seq "20,40,200"` 或 `"20:20:200"`（起:步:止）→ **Power 曲线**（x=样本量, y=效能）
- `--power_seq "0.8,0.9"` → **sample-size curve** (x=power, y=sample size) / `--power_seq "0.8,0.9"` → **样本量曲线**（x=效能, y=样本量）
- `--plot_effects "0.3,0.5,0.8"`: overlay multiple effect-size curves (sensitivity analysis, some types); `--out path.png` sets output / 多效应量叠曲线（敏感性分析，部分类型支持）；`--out path.png` 指定输出
- Plotting uses **base R graphics** (`png()`+`plot()`), **no ggplot2 needed** / 绘图用**基础 R 图形**（`png()`+`plot()`），**无需 ggplot2**
- Supports 22 test types (see `references/cli_examples.md` → *Curve Mode Examples*); other types print a clear "not yet covered" notice at runtime / 支持 22 种检验类型（详见 `references/cli_examples.md` → *Curve Mode Examples*）；其余类型运行时会提示暂未覆盖

### R Package Install (print commands by default) / R 包安装（默认仅打印命令）

For supply-chain safety, the skill does **not** auto-install R packages over the network: `--install-all-packages` only prints `install.packages()` commands (not executed); appending `--run-install` actually downloads & installs the 10 packages from CRAN. Full list: `references/cli_examples.md` → *R 包安装* and `references/r_packages_zh.md`.

出于供应链安全，本技能**不自动联网安装** R 包：`--install-all-packages` 仅打印 `install.packages()` 命令（不执行）；追加 `--run-install` 才从 CRAN 下载安装 10 个包。完整清单见 `references/cli_examples.md` → *R 包安装* 及 `references/r_packages_zh.md`。

---

## Formulas & Reports / 公式与报告

**Formulas / 公式:** `references/formulas_zh.md` | **Full functions / 完整函数:** `references/extended_functions.md`

| Scenario 场景 | Formula 公式 |
|:---|:---|
| Independent t | $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$ |
| Proportion (arcsin) | $n = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{h})^2$ |
| Survival (Schoenfeld) | $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$ |
| Cluster DEFF | $DEFF = 1 + (m - 1) \times ICC$ |

---

## Errors / 常见错误

| Error 错误 | Fix 修复 |
|:---|:---|
| "Rscript not found" | Install R or specify path / 安装 R 或指定路径 |
| "package not found" | install.packages("xxx") / 安装缺失包 |
| ImportError: statsmodels | pip install statsmodels / 安装 statsmodels |
| simr timeout | Reduce --nsim / 减小 --nsim |

---

**Version**: v3.4.4 | **Updated**: 2026-07-18 | **License**: MIT

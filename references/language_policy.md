# Language Policy / 双语语言策略

> 本文件是 `SKILL.md` 中「Language policy / 语言策略」的详版补充。适用原因：本技能属**统计分析类**且**已发布 ClawHub**，故遵循用户级「双语语言策略」规范（见 `~/.workbuddy/MEMORY.md`）。

## 三条核心规则

1. **默认英文**：所有面向用户的提示内容（报告、解释、菜单、警告框）默认使用英文。
2. **中文环境自动切换**：检测到操作系统为中文环境（locale 含 `zh`/`CN`）时，给用户的提示内容**自动切换为中文**，**无需用户显式要求**。
3. **代码输出不受影响**：R / Python 代码本身始终为英文，按 `--show-code` 规则展示，不受上述语言策略影响。

## 中文环境检测方法

| 平台 | 检测方式 |
|:---|:---|
| Linux / macOS | 读取 `LANG` / `LC_ALL` / `LANGUAGE` 环境变量，判断语言代码是否以 `zh` 开头（如 `zh_CN.UTF-8`） |
| Windows | 用 `Get-Culture` / `Get-WinSystemLocale` PowerShell cmdlet，或读取 `os` 环境变量判断语言代码是否以 `zh` 开头（如 `zh-CN`） |

判定为「中文环境」即自动用中文生成提示内容；否则用英文。

## 模块分级：双语覆盖要求

### 常用模块（须同时准备英文 + 中文两套提示内容）

- **常用检验类型**：`ttest_ind`、`ttest_paired`、`ttest_one`、`anova`、`proportion_one` / `proportion_two` / `proportion_paired`、`odds_ratio`、`risk_ratio`、`roc`、`poisson`、`non_inferiority`、`superiority_margin`、`be_tost`、`equivalence`、`survival`、`ni_survival`、`cluster`、`dunnett`
- **通用组件**：报告模板（`report_template.md`）、快速引导菜单、参数速查表——均须英/中双语共存

### 复杂 / 少用模块（可暂只提供英文，后续再补中文）

`group_sequential`、`adaptive`、`mixed_model`、`bayesian`、`win_ratio`、`must_win`、`historical_controls`、`assurance`、`conditional_power`、`dose_escalation`、`bland_altman`、`vaccine_efficacy`、`mams`、`survival_exact`、`mediation`

> 后续维护时，若用户频繁使用上述某模块，应优先补上中文提示内容，使其升为「常用模块」。

## 文档语言约定（面向维护者）

- `README.md`：纯英文（顶部保留中英文切换菜单）。
- `README_ZH.md`：纯中文。
- `SKILL.md` / `AGENTS.md` / `report_template.md` / `cli_examples.md` 等：英/中双语共存，标题双语、菜单双语保留。
- 编辑文档时，**已有中文内容（标题双语 / 菜单双语 / 中文对照表）一律保留，不删除**。

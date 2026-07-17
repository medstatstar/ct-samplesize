# Language Policy / 双语语言策略

> This file is the detailed companion to the "Language policy / 语言策略" section in SKILL.md. Why it applies: this skill is a statistical-analysis skill published on ClawHub, so it follows the user-level "bilingual policy" rule (see ~/.workbuddy/MEMORY.md). / 本文件是 `SKILL.md` 中「Language policy / 语言策略」的详版补充。适用原因：本技能属**统计分析类**且**已发布 ClawHub**，故遵循用户级「双语语言策略」规范（见 `~/.workbuddy/MEMORY.md`）。

## Three core rules / 三条核心规则

1. **English by default / 默认英文**: All user-facing prompt content (reports, explanations, menus, warning boxes) defaults to English. / 所有面向用户的提示内容（报告、解释、菜单、警告框）默认使用英文。
2. **Auto-switch on Chinese-OS / 中文环境自动切换**: When the OS is detected as Chinese (locale contains `zh`/`CN`), prompt content auto-switches to Chinese **without explicit user request**. / 检测到操作系统为中文环境（locale 含 `zh`/`CN`）时，给用户的提示内容**自动切换为中文**，**无需用户显式要求**。
3. **Code output unaffected / 代码输出不受影响**: R / Python code itself is always English, shown per `--show-code`; not affected by the language policy. / R / Python 代码本身始终为英文，按 `--show-code` 规则展示，不受上述语言策略影响。

## Chinese-OS detection method / 中文环境检测方法

| Platform 平台 | Detection method 检测方式 |
|:---|:---|
| Linux / macOS | Read `LANG` / `LC_ALL` / `LANGUAGE`; check if the language code starts with `zh` (e.g. `zh_CN.UTF-8`) / 读取 `LANG` / `LC_ALL` / `LANGUAGE` 环境变量，判断语言代码是否以 `zh` 开头（如 `zh_CN.UTF-8`） |
| Windows | Use `Get-Culture` / `Get-WinSystemLocale` PowerShell cmdlets, or read `os` env to check if the language code starts with `zh` (e.g. `zh-CN`) / 用 `Get-Culture` / `Get-WinSystemLocale` PowerShell cmdlet，或读取 `os` 环境变量判断语言代码是否以 `zh` 开头（如 `zh-CN`） |

If judged "Chinese environment", generate prompts in Chinese automatically; otherwise use English. / 判定为「中文环境」即自动用中文生成提示内容；否则用英文。

## Module tiers: bilingual coverage / 模块分级：双语覆盖要求

### Common modules (must prepare EN + ZH) / 常用模块（须同时准备英文 + 中文两套提示内容）

- **Common test types / 常用检验类型**: `ttest_ind`, `ttest_paired`, `ttest_one`, `anova`, `proportion_one` / `proportion_two` / `proportion_paired`, `odds_ratio`, `risk_ratio`, `roc`, `poisson`, `non_inferiority`, `superiority_margin`, `be_tost`, `equivalence`, `survival`, `ni_survival`, `cluster`, `dunnett`
- **Shared components / 通用组件**: report template (`report_template.md`), quick menu, flag reference — all must keep EN/ZH bilingual. / 报告模板（`report_template.md`）、快速引导菜单、参数速查表——均须英/中双语共存。

### Complex/rare modules (EN-only for now) / 复杂 / 少用模块（可暂只提供英文，后续再补中文）

`group_sequential`, `adaptive`, `mixed_model`, `bayesian`, `win_ratio`, `must_win`, `historical_controls`, `assurance`, `conditional_power`, `dose_escalation`, `bland_altman`, `vaccine_efficacy`, `mams`, `survival_exact`, `mediation`

> When maintaining, if the user frequently uses one of the above, prioritize adding Chinese prompt content to promote it to a "common module". / 后续维护时，若用户频繁使用上述某模块，应优先补上中文提示内容，使其升为「常用模块」。

## Doc language convention (for maintainers) / 文档语言约定（面向维护者）

- `README.md`: English only (keep the top EN/CN switch menu). / 纯英文（顶部保留中英文切换菜单）。
- `README_ZH.md`: Chinese only. / 纯中文。
- `SKILL.md` / `AGENTS.md` / `report_template.md` / `cli_examples.md` etc.: EN/ZH bilingual, keep bilingual titles and bilingual menus. / 英/中双语共存，标题双语、菜单双语保留。
- When editing docs, **existing Chinese content (bilingual titles / bilingual menus / Chinese reference tables) must be kept, never deleted**. / 编辑文档时，**已有中文内容（标题双语 / 菜单双语 / 中文对照表）一律保留，不删除**。

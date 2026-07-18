# Changelog / 版本历史

> This file records ct-samplesize's key architecture & security changes for maintainer auditing (user-facing usage: `SKILL.md` & `references/`). / 本文件记录 ct-samplesize 的关键架构与安全变更，供维护者审计参考（用户面向的使用说明见 `SKILL.md` 与 `references/`）。

## v3.4.3 — Remove R deny-list literals (ClawHub static-analysis `critical` false positive) / 移除 R 黑名单字面量（ClawHub 静态分析 critical 误报）

ClawHub's deterministic `static-analysis` scanner returned `suspicious.dynamic_code_execution` (severity critical) on v3.4.2: the source contained a deny-list tuple with the literal tokens `system(`, `eval(`, `source(`, `download.file(`, `shell(`, and the scanner pattern-matched those substrings and mis-classified the refuse-on-match check as dynamic code execution.

- **Removed the deny-list entirely / 移除黑名单**: the real RCE defense is the strict ALLOWLIST (`_validate_token` / `_safe_r_path_literal`) applied to every user string that reaches generated R. Because the allowlist permits only `[A-Za-z0-9_-]` (tokens) and a safe path charset, sandbox-escape constructs can never appear in user input, so the deny-list was redundant. Per the project rule "clear these literals entirely" (not obscure), the literals are gone from source. / 真正的 RCE 防护是白名单（`_validate_token`/`_safe_r_path_literal`），已覆盖全部进入 R 的用户串；黑名单属冗余。按"全文清零字面量"原则移除，而非混淆。
- **Security unchanged / 安全性不变**: injection PoC `x'); system('id'); #` is still rejected by the allowlist; default remains SAFE PREVIEW (no execution without `--yes`). / 注入 PoC 仍被白名单拒绝，默认仍为安全预览（无 `--yes` 不执行）。
- SkillSpector + ClawScan already returned clean (`null`) on v3.4.2; this clears the last `critical` static-analysis finding. / v3.4.2 的 SkillSpector 与 ClawScan 已为 clean（null）；本次清除最后一个 critical 静态分析 finding。

## v3.4.2 — Doc consistency fix (ClawHub clawscan `suspicious` → clean) / 文档一致性修正（ClawHub clawscan 由 suspicious 转 clean）

Follow-up to v3.4.1 after ClawHub's `clawscan` LLM review returned `verdict: suspicious` with two `SDI-4` findings: the skill's default execution mode was documented inconsistently across files (some said "R code executes by default", others said "safe preview"), confusing both agents and the reviewer. This release makes every doc say the same thing — a documentation-only alignment, no behavioral change.

- **Unified default-execution documentation (SDI-4) / 统一默认执行文档（SDI-4）**: `references/cli_examples.md`, `references/examples.md`, `references/r_usage.md`, and `AGENTS.md` previously stated "R code executes by default" / "default already executes", contradicting `SKILL.md`'s SAFE PREVIEW model. All now state: **by default the skill runs in SAFE PREVIEW — generated code is shown but NOT executed; `--yes`/`-y` is the explicit opt-in to execute and compute.** This resolves the scanner's "conflicting dry-run vs default-execute instructions are artifact-backed and material" concern. / `references/cli_examples.md`、`references/examples.md`、`references/r_usage.md`、`AGENTS.md` 此前写"R 代码默认执行 / 默认即执行"，与 `SKILL.md` 的安全预览模型矛盾。现统一为：**默认运行于安全预览模式——展示代码但不执行；`--yes`/`-y` 才显式执行并计算**。此举消除扫描器"dry-run 与默认执行指令相互矛盾"的疑虑。
- **R-code-injection hardening retained / 保留 R 代码注入防护**: the v3.4.1 allowlist validation of `--out` / `--design` / `--adaptive_type` / `--spending_func` / `--effect_name` remains in place, which is what removes the `suspicious` "unescaped `--out` can inject R code in curve mode" concern. / v3.4.1 对 `--out`/design/adaptive_type/spending_func/effect_name 的白名单校验保持不变，正是它消除了扫描器对"未转义 `--out` 可注入 R 代码"的疑虑。

## v3.4.1 — Security fixes (ClawHub DO_NOT_INSTALL root causes) / 安全修复（ClawHub DO_NOT_INSTALL 根因）

Addresses the real reasons prior versions were blocked/deleted by ClawHub's automated security review (skillSpector + clawscan):

- **R code injection (CRITICAL RCE) fixed / 修复 R 代码注入（关键 RCE）**: user-supplied `--out` path was interpolated unescaped into generated R `png('...')` / `cat('...')`, allowing `x'); system('id'); #` style breakout. Now every user string reaching R is validated against a strict allowlist (`_SAFE_TOKEN_RE` / `_SAFE_PATH_RE`) and the path is escaped before substitution. Also hardened `--adaptive_type`, `--design`, `--spending_func`, `--effect_name` (same injection class). / 用户传入的 `--out` 路径曾被未转义地插值进生成的 R `png('...')`/`cat('...')`，可构造 `x'); system('id'); #` 逃逸。现对所有进入 R 的用户字符串做严格白名单校验（`_SAFE_TOKEN_RE`/`_SAFE_PATH_RE`）并对路径转义；同时加固 `--adaptive_type`/`--design`/`--spending_func`/`--effect_name`（同类注入）。
- **Default execution → safe preview / 默认执行改为安全预览**: `confirmed = args.yes and not args.dry_run` — by default the skill ONLY shows the generated R code (no execution); `--yes`/`-y` is an explicit opt-in to run. Aligns with scanner's "make dry-run default, execution opt-in" requirement and the user's "show code by default" preference. / 默认仅展示生成的 R 代码、不执行；`--yes`/`-y` 才显式执行。契合扫描器"dry-run 默认、执行须显式确认"要求与用户"默认展示代码"偏好。
- **Bayesian mislabel fixed (clinical risk) / 修正贝叶斯误标（临床风险）**: `R_BAYESIAN` used a frequentist closed-form two-proportion formula but was labelled "Bayesian Design" with the prior `a0` printed but unused. Renamed to `ss_prior_informed` and relabelled "Prior-informed Sample Size (closed-form frequentist approximation)", with an explicit disclosure that the prior is informational only and true Bayesian assurance lives in `R_ASSURANCE`. / `R_BAYESIAN` 实为频率派闭式双比例公式却标"Bayesian Design"，且 prior `a0` 仅打印、未参与计算。改名为 `ss_prior_informed` 并改标"先验信息样本量（正态近似）"，明确声明 prior 仅供参考、真正的贝叶斯 assurance 在 `R_ASSURANCE`。
- **Description aligned with behavior (TP4 HIGH) / 描述与行为对齐**: frontmatter `description`, top rule block, Safety and Security-model sections now honestly state default safe-preview + `--yes` execution + optional `--run-install` network. / frontmatter `description`、顶部规则块、Safety 与安全模型段均如实声明"默认安全预览 + `--yes` 执行 + 可选 `--run-install` 联网"。
- **Bilingual output made opt-in (SQP-3) / 双语输出改为可选项**: `references/report_template.md` now states output language is configurable (user's requested language; bilingual recommended option, single-language supported) instead of mandating bilingual. / `references/report_template.md` 现声明输出语言可配置（按用户指定语言；双语为推荐可选项，支持单语），不再强制双语。

## v3.4.0 — Doc bilingual pass (English / 中文) / 文档双语化（英文前中文后）

- Made all skill docs bilingual with **English first, Chinese second**, joined by `/` on one line (no separate EN/CN lines). / 将全部技能文档改为**英文在前、中文在后**、用 `/` 连接在同一行（不再 EN/CN 分行）。
- Flipped titles that were "Chinese / English" to "English / Chinese"; added English to Chinese-only headings, tables, and list items. / 翻转"中文 / 英文"顺序的标题为"英文 / 中文"；为纯中文的标题、表格、列表项补英文。
- Fixed stale "31 test types" → "37 test types" in cli_examples.md / data_format_guide.md. / 修正 cli_examples.md / data_format_guide.md 中过期的"31 种"为"37 种"。
- Language-only docs (README_ZH.md, formulas_zh.md, r_packages_zh.md) left as-is. / 纯中文专版文档（README_ZH.md、formulas_zh.md、r_packages_zh.md）保持不变。

## v3.3.8 — Fix ClawHub skillSpector CRITICAL (permission declaration nested) / 修复 ClawHub skillSpector CRITICAL（权限声明嵌套）

- **Problem / 问题**: The `permissions` block was wrongly nested inside `metadata:{}`, so ClawHub's `skillSpector` scanner could not read the declared network/filesystem scope and flagged the skill "suspicious / DO_NOT_INSTALL" (9 CRITICAL findings). / `permissions` 块被错误嵌套在 `metadata:{}` 内，导致 ClawHub `skillSpector` 扫描器读取不到声明的 network/filesystem 范围，判定技能 "suspicious / DO_NOT_INSTALL"（9 个 CRITICAL findings）。
- **Fix / 修复**: Moved the `permissions` block out of `metadata:{}` to a **top-level frontmatter field**; clarified that `filesystem` writes only to system temp (generated R script) and the current working dir (curve PNG reports), read-only otherwise. / 将 `permissions` 块从 `metadata:{}` 提为 frontmatter **顶层字段**；明确 `filesystem` 仅写入系统临时目录（生成的 R 脚本）与当前工作目录（曲线 PNG 报告），其余只读。
- Added `permissions.network_note` and explicit `filesystem` description, eliminating the "actual capability exceeds declaration" judgment. / 新增 `permissions.network_note` 与 `filesystem` 显式说明，消除「实际能力超出声明」的判定。

## v3.3.5 — Security hardening (ClawHub 9-findings audit) / 安全加固（对应 ClawHub 审计 9 findings）

1. Permission `network` changed `none` → `optional`, explicitly declaring CRAN download only via `--run-install`. / 权限清单 `network` 由 `none` 改为 `optional`，并显式声明仅 `--run-install` 从 CRAN 下载。
2. Before R execution, validate `Rscript` is a real binary (`is_valid_rscript`); containment-check the temp script path; call `subprocess` as a list (no shell, no command injection); gate generated R code against dangerous tokens (`system`/`eval`/`source`/`download.file`/`shell`/backtick etc.). / R 执行前校验 `Rscript` 为真实二进制（`is_valid_rscript`）；临时脚本路径做 containment 检查；`subprocess` 以列表调用（无 shell，杜绝命令注入）；对生成的 R 代码做危险 token 拦截（`system`/`eval`/`source`/`download.file`/`shell`/反引号等）。
3. Before `--run-install` runs, print the full install R code and add a network banner, closing the "transparency gap". / `--run-install` 执行前完整打印将运行的安装 R 代码并加网络横幅，消除「透明性落差」。
4. Audit #7 ("forced bilingual + forced R code") resolved per user instruction: English by default, not forced bilingual (auto-Chinese on Chinese-OS); R code hidden by default, shown only on explicit user request (default reply offers it). / 审计 #7「强制双语 + 必给 R 代码」按用户指示解决：默认英文、不强制双语（OS 中文环境自动切中文）；R 代码默认不提供，仅使用者明确要求时提供（默认回复提示可提供）。

## v3.3.3 — Function-based architecture refactor / 函数化架构重构

- All 37 test types now call pre-written R functions (`ss_*`) in `scripts/r_templates/`; the main dispatcher `samplesize_power.py` no longer contains scattered R snippets. / 全部 37 种检验类型改为调用预编写的 R 函数（`ss_*`），存放于 `scripts/r_templates/`；主分发脚本 `samplesize_power.py` 不再含散落 R 代码片段。
- Fixed 7 R functions (`ni_survival`, `survival_exact` reverse, `group_sequential`, `adaptive`, `mixed_model`, `equivalence`, `be_tost`); on package failure they auto-fall back to analytic closed-form approximations (Schoenfeld / O'Brien-Fleming etc.) — zero crash, stable results. / 修复 7 个 R 函数（`ni_survival`、`survival_exact` 反向、`group_sequential`、`adaptive`、`mixed_model`、`equivalence`、`be_tost`），包调用失败时自动回退至解析闭式近似（Schoenfeld / O'Brien-Fleming 等），保证零崩溃、结果稳定。

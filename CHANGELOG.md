# Changelog / 版本历史

> This file records ct-samplesize's key architecture & security changes for maintainer auditing (user-facing usage: `SKILL.md` & `references/`). / 本文件记录 ct-samplesize 的关键架构与安全变更，供维护者审计参考（用户面向的使用说明见 `SKILL.md` 与 `references/`）。

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

# Changelog / 版本历史

> 本文件记录 ct-samplesize 的关键架构与安全变更，供维护者审计参考（用户面向的使用说明见 `SKILL.md` 与 `references/`）。

## v3.3.8 — 修复 ClawHub skillSpector CRITICAL（权限声明嵌套）

- **问题**：`permissions` 块被错误嵌套在 `metadata:{}` 内，导致 ClawHub `skillSpector` 扫描器读取不到声明的 network/filesystem 范围，判定技能 "suspicious / DO_NOT_INSTALL"（9 个 CRITICAL findings）。
- **修复**：将 `permissions` 块从 `metadata:{}` 提为 frontmatter **顶层字段**；明确 `filesystem` 仅写入系统临时目录（生成的 R 脚本）与当前工作目录（曲线 PNG 报告），其余只读。
- 新增 `permissions.network_note` 与 `filesystem` 显式说明，消除「实际能力超出声明」的判定。

## v3.3.5 — 安全加固（对应 ClawHub 审计 9 findings）

1. 权限清单 `network` 由 `none` 改为 `optional`，并显式声明仅 `--run-install` 从 CRAN 下载。
2. R 执行前校验 `Rscript` 为真实二进制（`is_valid_rscript`）；临时脚本路径做 containment 检查；`subprocess` 以列表调用（无 shell，杜绝命令注入）；对生成的 R 代码做危险 token 拦截（`system`/`eval`/`source`/`download.file`/`shell`/反引号等）。
3. `--run-install` 执行前完整打印将运行的安装 R 代码并加网络横幅，消除「透明性落差」。
4. 审计 #7「强制双语 + 必给 R 代码」按用户指示解决：默认英文、不强制双语（OS 中文环境自动切中文）；R 代码默认不提供，仅使用者明确要求时提供（默认回复提示可提供）。

## v3.3.3 — 函数化架构重构

- 全部 37 种检验类型改为调用预编写的 R 函数（`ss_*`），存放于 `scripts/r_templates/`；主分发脚本 `samplesize_power.py` 不再含散落 R 代码片段。
- 修复 7 个 R 函数（`ni_survival`、`survival_exact` 反向、`group_sequential`、`adaptive`、`mixed_model`、`equivalence`、`be_tost`），包调用失败时自动回退至解析闭式近似（Schoenfeld / O'Brien-Fleming 等），保证零崩溃、结果稳定。

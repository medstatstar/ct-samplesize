# AGENTS.md — ct-samplesize v5.7.26

## Overview

`ct-samplesize`: An easy-to-use sample size & power tool for clinical trial practitioners. The **default authoritative engine is a remote coze R compute service** (rpact/TrialSize/PowerTOST etc., 20+ packages running server-side — no local R required); it performs all 65 test types via natural-language prompts (output in Chinese or English per OS language setting, prompt can force-switch). In the published skill **no R or shell runs locally and there is no local compute fallback**; only trial-design parameters are sent to coze, and full R code can be returned on request for verification, submission, or re-run.

---

## Core Rules

### 1. Compute Backend Detection (coze only)
- **Published skill:** the ONLY backend is the coze R service (`CTSS_COZE_ENDPOINT`, default pre-whitelisted `https://ct-samplesize.coze.site/run`); all 65 tests compute server-side, no local R and **no local compute fallback**. If the endpoint is unreachable, the skill reports the missing config — it never silently degrades.
- **Dev-only (not shipped):** a legacy local-R backend exists in `adapters/local-r/` (`CTSS_BACKEND=local-r` / `CTSS_FORCE_R=1`), used only for offline development/contribution; it is not routed by the v5 `select_backend` and is excluded from the published package.

### 2. Extended Tool Selection

> All rows below run **server-side on coze** in the published skill (only design params are sent).

|User Need|Path|
|:----------|:-----|
| Basic stats (t-test/ANOVA/proportion) | coze (R) |
| Longitudinal / Repeated measures | R: `simr` (mixed model) |
| Diagnostic trial | R: `pROC` (ROC formula) |
| Count data / Recurrent events | R: custom Wald test |
| Cluster randomized | R: design effect formula |
| Method comparison | R: Bland-Altman (Lu et al.) |
| Bioequivalence | R: `PowerTOST` (TOST) |
| Group sequential / Adaptive | R: `rpact` (gsDesign on-demand only) |
| Non-inferiority | R: `TrialSize` (exact) / `powerSurvEpi` |
| Survival | R: `rpact` |
| Vaccine efficacy | R: Halloran formula |
| Bayesian design | R: `BayesCTDesign` |
| Dose escalation | R: `escalation` |
| Multiple endpoints | R: correlation method |
| Win-Ratio composite | R: `BuyseTest` power simulation |
| Must-Win / Co-Primary | R: correlation inflation factor |
| Historical Controls | R: `RBesT` MAP prior |
| MAMS | R: `rpact` |
| Conditional Power / SSR | R: `rpact` |
| Superiority by Margin | R: custom formula |
| Assurance | R: Monte Carlo simulation |
| Dunnett comparisons | R: `MCPAN` |
| Mediation | R: `powerMediation` |

### 3. Code Execution
- **Published skill:** no local R/shell and no local compute fallback. The orchestration layer (`scripts/samplesize_power.py`) routes via `ComputeBackend` (`scripts/compute_backend.py`) to `CozeBackend` — the only backend in v5 (legacy local-R dev backend in `adapters/local-r/` is dev-only, not shipped).
- **Default: safe preview.** `--dry-run` prints the exact coze request envelope (no send); the natural-language trigger ("please compute" / 请直接计算) is what sends and computes — **`--yes` is not needed for coze** (stateless remote compute; the legacy `--yes` gate applies only to the optional local-R dev backend).
- Python (orchestration + fallback) via the bundled interpreter; figures from coze are written to `CTSS_OUTPUT_DIR` (default `./outputs`).

### 4. Result Output (v3.4.4)

Every analysis includes:
- Input parameters + defaults used
- Calculation result (sample size / power / effect size)
- Dropout adjustment (if applicable)
- Assumptions & limitations
- **Default = SAFE PREVIEW (coze request envelope shown, NOT sent)**; the natural-language trigger ("please compute" / 请直接计算) sends to coze & computes — **no `--yes` needed for coze** (stateless remote compute; `--yes` applies only to the legacy local-R dev backend). `--show-code` displays the coze request JSON (no send), `--dry-run` previews only.
- The optional local-R dev backend (adapters/local-r) behaves like v3.x: R code is shown but NOT run unless `--yes` is given; `-y`/`--yes` explicitly executes locally.
- **`--test adaptive_simulate`**: the authoritative engine is the inlined pure base-R function library `ADAPTIVE_SIM_R` (maintained in `adapters/local-r/local_r_backend.py`, no extra packages) running **server-side on coze** in the published skill. A legacy pure-Python module `adapters/local-r/legacy/adaptive_simulator.py` is retained for offline dev/testing. The CLI shows the coze request envelope in SAFE PREVIEW and computes via coze. See `references/adaptive_simulator.md`.

### 5. Language Detection
- **Follow OS language setting**: Output language (Chinese or English) follows the OS language setting — Chinese on a Chinese-OS, English otherwise.
- **Prompt can force-switch**: The user may override the OS-based default anytime via an explicit language request (e.g. "switch to English").
- **Detection method**: Linux/macOS read `LANG`/`LC_ALL`/`LANGUAGE`; Windows use `Get-Culture`/`Get-WinSystemLocale` or `os` env to check if the language code starts with `zh`; if the `<response_language>` tag specifies a language, follow it.
- **Docs are English-only**: The skill documentation (SKILL.md, AGENTS.md, references, etc.) is English-only. Runtime output for common modules may still be English + Chinese per OS setting; complex/rare modules are English-only.
- **Complex/rare modules may be English-only**: e.g. `group_sequential`, `adaptive`, `mixed_model`, `bayesian`, `win_ratio`, `mams`, `vaccine_efficacy` etc.
- **This policy does not affect code output**: R/Python code is always English, shown per `--show-code`.

### 6. Mixed Model Specifics
- Use `simr::makeLmer()` / `makeGlmer()` to build model from literature parameters
- Run `powerSim()` with nsim ≥ 500 for stable estimates
- Always run `powerCurve()` to find minimum sample size
- Report computation time (can be 1-5 min for complex models)

### 7. Menu Navigation Design — Non-Exclusive
- The interactive "quick menu" that guides users to pick a test type MUST NOT be a mutually-exclusive tree. The same test can appear under multiple top-level entries, mirroring PASS's menu design.
- Rationale: with 65 test types, classification dimensions intersect (design family × endpoint type). A strict tree would hide reachable paths. The menu is a *navigation aid*, not a taxonomy.
- Example: sequential survival analysis (`gsd_survival` = `group_sequential` + survival endpoint) must be reachable BOTH from a **Survival Analysis** top-level menu AND from a **Sequential Group-Sequential Design** top-level menu.
- Rule of thumb for future extensions: any test classifiable along multiple axes (e.g. sequential/adaptive × means/proportion/survival/rate) must be listed under every relevant top-level entry — do NOT hang it on a single node.
- **Menu structure is now formalized in `references/menu.md`** (primary tree by endpoint + design-family cross-index) and surfaced in SKILL.md `## Quick Menu`. When guiding a user to pick a test, read `references/menu.md` to stay consistent with the canonical classification.

### 8. Triage — Four-Way Interaction

Before any user interaction, triage first into **Simple / Middle / Complex / Vague**, then decide whether / how to show a menu.

|Class|Trigger|Action|
|:---|:---|:---|
|**Simple**|Direct t-test/ANOVA/proportion-style question with clear how/why|Answer directly; 1–2 turns; pick from the 65 test types; no menu|
|**Middle**|Single-point but deep (ICH guidance detail, statistical parameter, compliance gray zone; needs 3–4 points)|Still answer directly, **no menu** (same path as Simple); mark `difficulty = "middle"` for a richer multi-point answer. When Simple vs Middle is unclear, prefer **Middle**|
|**Complex**|Multi-step or design-family question (sequential/adaptive/mixed/survival)|Consult `references/menu.md` → present the relevant menu; guide step-by-step|
|**Vague**|Under-specified ask (missing endpoint, design, or effect size)|Use `grill-me` to ask 1–3 clarifying questions → then re-triage|

- Choose menu depth based on simple vs complex.
- `references/menu.md` defines the **Complex** path; Simple and Vague rarely need the full menu.
- **Routing gate (audit follow-up — avoid accidental remote compute):** a remote coze compute (data leaves the machine) fires **only** when the user's intent is explicitly a sample-size / power / curve **calculation**. Advisory / consulting asks — "help me figure it out", methodology, ICH guidance, "what test should I use" — are answered **locally, nothing sent** (menu / grill-me flow as needed). On ambiguous phrasing, ask for calculation intent before any coze call.

---

## Security Fixes (v3.3+)

|Fix|Implementation|
|:----|:--------------|
| Default dry-run | R code displayed, not executed unless `-y` confirmed |
| Output sanitization | `sanitize_output()` strips paths, truncates |
| No hardcoded R path | RSCRIPT_PATH env + PATH lookup |
| Narrowed triggers | Removed generic terms like "sample size" alone |
| Permissions declared | `permissions` block in SKILL.md frontmatter (top-level) |
| User warnings | `## ⚠️ User Warnings` section |
| Fixed `minfup` | Examples: `minfup <- T - R` (24 months, matches prose) |
| Fixed dropout code | Valid R syntax throughout |

---

## Dependencies

### R Packages (dev / coze-side — NOT in published skill)
In the published skill, all R packages run **server-side on coze**; you never install them locally. This section applies only when running the optional local-R backend (`CTSS_BACKEND=local-r`, requires `adapters/local-r/`):
R packages do NOT need to be pre-installed all at once. When the dev backend detects a missing package it prints the install command in output; the user runs it once.

|Tier|Package|Used for|
|:---|:---|:---|
|**Core (high-freq)**|`TrialSize`, `pwr`, `rpact`, `PowerTOST`, `powerSurvEpi`|NI, equivalence, survival, superiority margin, group-sequential, BE etc.|
|**Aux (mid-freq)**|`simr`, `lme4`, `pROC`, `survival`|mixed model, ROC, exact survival ROC|
|**Low-freq**|`BayesCTDesign`, `escalation`, `BuyseTest`, `RBesT`, `MCPAN`, `powerMediation`, `BlandAltmanLeh`|vaccine, dose escalation, Win-Ratio, historical control, Dunnett, mediation|
|**No R package**|—|`ttest_*` (partial), `anova`, `poisson`, `cluster`, `bland_altman`, `vaccine_efficacy`, `bayesian`, `dose_escalation`, `assurance`, `multiple_endpoints`, `must_win`, `mediation`|

**When the user requests one-click install (dev backend only), run**
```r
install.packages(c("TrialSize", "pwr", "rpact", "PowerTOST", "simr", "lme4", "pROC", "powerSurvEpi", "survival"))
```
(Note: the legacy CLI flag `--install-all-packages` was removed in v5.0.2 — use the R snippet above for the dev backend; the published coze engine needs no local install.)

### Python (v5: stdlib only — no third-party compute deps)
```
# No pip requirements for the published skill: argparse / json / urllib / math (stdlib only).
# The v5 refactor removed statsmodels / numpy / scipy (no local Python computation).
# Optional: cairosvg — only for --figure-mode png_file (local SVG→PNG rasterization).
```

## Test Infrastructure / 测试基建

> 沉淀自 v5.13.42 全量回归实战。**纪律全文见 ct-base `references/workbench_ui.md` §21.6（jsdom 断言纪律）与 §22（计算正确性实证裁决）**——叶技能遵循 ct-base 底座子集约束。核心三条：闭式/近似公式必须 MC 实证裁决（自洽性断言只证明实现忠实、不证明正确）；jsdom 断言匹配渲染后显示文本（`paramLabel` 会把 `power` 译成「目标检验效能」）；机检项负例双向验证（违例真报 + 合法真过）。

### Suites / 套件一览

| 套件 | 命令 | 覆盖 | 备注 |
|---|---|---|---|
| 本地 NL 路由 | `python tests/test_nl_local.py` | 意图判定 / 咨询拦截 / 分类路由 / 参数提取 | 零网络 |
| 特性回归 | `python tests/test_features.py` | 5 本地用例（其余 live-only 自动跳过） | |
| 合约信封 | `python tests/coze_cases_regression.py` | 67 检验契约信封结构 | 零网络 |
| 合约 live | `CTSS_COZE_LIVE=1 python tests/coze_cases_regression.py` | 真实端点 21 案例 | 打 coze，注意 429 |
| NL 30 案例 | `python tests/test_natural_language.py` | 自然语言端到端 | 打 coze |
| 全覆盖 69 | `python tests/test_full_coverage.py` | 全检验矩阵 | 打 coze |
| 矩阵缺口 | `CTSS_COZE_LIVE=1 python tests/test_matrix_gaps.py` | FD-B2 反求等 57 项 | live-only；报告落 `tests/matrix_gaps_report.json` |
| jsdom UI | `NODE_PATH="C:/Users/WintoneFileSrv/.workbuddy/binaries/node/workspace/node_modules" node tests/test_meta_ui_jsdom.js` | catalog 驱动 UI 回归 26 断言 | 夹具在 `%TEMP%/ctss_fix/` |
| **工作台全自动化**（下） | 见下 | 工作台页面五层 110 例：静态契约/后端API/前端单元/E2E/布局a11y | **发布前强制闸门**，mock |
| **scratch 四件套**（下） | 见下 | wilcoxon 新增链 + 本轮 UI 修复聚焦 | 本地夹具，gitignored |

**429 限流判据（§22.2）**：live 套件批量"失败"先看信封——`{"ok": false, "error": "rate_limited"}` = 基础设施节流非回归，用同端点其他套件全过反证。Heavy 套件连打（150+ 调用/小时）会烧掉配额，套件之间留间隔；限流未退不反复探测（探测也耗配额）。

### scratch/ 回归脚本四件套（tests/scratch/，本地资产，勿当垃圾清理）

| 脚本 | 运行 | 断言数 | 用途 |
|---|---|---|---|
| `verify_wilcoxon.R` | `"C:/Tools/R-4.6.1/bin/x64/Rscript.exe" tests/scratch/verify_wilcoxon.R adapters/coze/src/r_engine` | 20 | wilcoxon 双检验 R 单元：折算路径 / Noether 闭式 / 最小整数性 / 单双侧 / 不等比例 / ARE 自洽 / **MC 锚定**（n=30 模拟 0.802） |
| `mc_wilcoxon.R` | `"C:/Tools/R-4.6.1/bin/x64/Rscript.exe" tests/scratch/mc_wilcoxon.R` | — | 蒙特卡洛裁决（20000 次精确 `wilcox.test`）——**公式正确性的唯一证据来源**（§22.1） |
| `e2e_wilcoxon.py` | `python tests/scratch/e2e_wilcoxon.py` | 16 | `run_task.R --input json --output json` dispatch 全路径：求解 / 反求 / 两路径 / 单侧 / 脱落 / 错误路径 / 曲线 |
| `ui_focus_check.js` | `NODE_PATH=... node tests/scratch/ui_focus_check.js` | 26 | 本轮 UI 修复聚焦：菜单落位 / 占位提示 / 求解方向切换输出 / **or 组必填提示五情形** / 缺失参数转义 / 叙述结构化 |

维护纪律：① 夹具从活服务器（`CTSS_COZE_MOCK=1 PORT=8791 python workbench/server.py 8791`）`/api/schema` 导出，**必须用 Python 无 BOM 写盘**（PowerShell `Set-Content utf8` 加 BOM 会崩 Node `JSON.parse`）；② 断言匹配显示文本非内部键名；③ 期望值实证锚定（贴线值先精算）；④ 改 R 公式后必须同跑 `mc_wilcoxon.R` 再收。

### 界面机检（C-detail-*）

```bash
# ct-base 通用引擎（零依赖，默认全开含 C-detail-escape）；本技能无 rules.json 走家族默认
python "C:/Users/WintoneFileSrv/.workbuddy/skills/ct-base/scripts/wb_detail_check.py" --html workbench/workbench.html
# 发布副本同步复检
python "C:/Users/WintoneFileSrv/.workbuddy/skills/ct-base/scripts/wb_detail_check.py" --html workbench/publish/workbench/workbench.html
```
任一 FAIL = 禁止交付。v5.13.42 起工作台与发布副本均全绿（label / placeholder / claim / i18n-ph / escape）。

### 工作台全自动化测试（标准检验流程 / release gate）

> 规范全文：`references/workbench_qa.md`（zh：`references/workbench_qa_zh-CN.md`）；套件实操：`workbench/autotest/README.md`。与上方 `C-detail-*` 机检互补——C-detail 查静态细节（label/placeholder/escape），本套件查**运行时行为 + 后端契约 + 真实流程 + 布局**。

**强制闸门**：改 `workbench.html` / `server.py` / `form_schema.py` / `tokens.css` / `wb-list.css` / `wb-list.js` 任一，或跑 `build_publish.py` / `install_genie.py` 前，**必须**全量跑通：

```bash
cd workbench/autotest
python run_all.py                # 五层 110 例，约 70s，全绿才允许发布
python run_all.py --layer L1 L3  # 开发迭代只跑指定层
```

判据：**5 层 0 failed / 0 error**；任一失败 = 禁止发布。报告落 `autotest/report/<ts>/`（summary.md / failures.md / junit_L*.xml）。

**五层**：L1 静态契约（纯 Python 解析 HTML，不启浏览器）· L2 后端 API（起 `server.py` 子进程 + requests，67 方法全参数化、非法输入必 4xx、凭据白名单、限流）· L3 前端单元（Playwright 内直调页面 JS）· L4 端到端（真实点击：选方法→填参→计算→历史→导出→反馈弹窗）· L5 布局/响应式/a11y（三档视口：桌面/平板/手机，横向溢出、44px 热区、对比度）。

**回归基线（7 个真实 bug，持续守护）**：① P0 `#v-domain` 缺闭合标签致历史页/页脚被吞、功能 0×0 不可用；② P0 `/config/llm_key.py` 等凭据文件可被 HTTP GET 下载；③ P1 argparse usage 打 stderr 在容器里拖死请求（点计算一直转圈）；④ P1 `survival` optional 用 CLI 别名 `hr` 渲染空控件；⑤ P2 切 EN 残留中文（域标题/会话下拉）；⑥ P2 `title`/`aria-label` 无 i18n；⑦ P2 移动端 CTA 40px < 44px。完整根因与修法见 `references/workbench_qa_zh-CN.md` §四。

**🔴 强制护栏**：跑 `build_publish.py` 前先备份 `publish/.wbapp_*.genie` 与 `publish/.workbuddy/applications.yaml`——其 PRUNE 会剪掉 appId 认领标记，丢失后再发布会生成带后缀新域名、无法回到 `https://ct-samplesize.app.workbuddy.host/`。本套件**不进**工作台发布载荷（白名单构建，`autotest/` 不在白名单）。



---
slug: ct-samplesize
displayName: 临床试验样本量与检验效能专家 / Clinical Trial Sample Size & Power
name: ct-samplesize
cn_name: 临床试验样本量与检验效能专家
version: 5.1.0
invocable: true
required_commands: [python]
summary: 为临床试验从业者提供的样本量与检验效能计算工具。本地无需安装 R，直接提供云端 R 计算服务（覆盖 49 种检验，并提供 SVG 出版级别图形）。自然语言驱动，可应要求返回完整 R 代码；默认按操作系统语言设定输出中文或英文（提示词可强制切换）。
license: MIT
description: "为临床试验从业者提供的样本量与检验效能计算工具。本地无需安装 R，直接提供云端 R 计算服务（覆盖 49 种检验，并提供 SVG 出版级别图形）。自然语言驱动，可应要求返回完整 R 代码；默认按操作系统语言设定输出中文或英文（提示词可强制切换）。 / Sample size and power calculation tool for clinical trial practitioners. No local R install needed — a cloud R compute service covers all 49 test types and returns publication-grade SVG figures. Natural-language driven; full R code can be returned on request; default output in Chinese or English per OS language setting (prompt can force-switch)."
triggers:
  - "clinical trial sample size"
  - "样本量计算"
  - "clinical trial power"
  - "检验效能计算"
  - "临床试验 设计"
  - "non-inferiority sample size"
  - "equivalence sample size"
  - "survival analysis sample size"
  - "adaptive design"
  - "group sequential design"
  - "Bayesian clinical trial"
metadata: { openclaw: { emoji: "📊" }, authors: ["medstatstar", "phoe-zip"], license: "MIT", tags: [clinical-trial, sample-size, power, coze, adaptive-design, bayesian, win-ratio], homepage: "https://github.com/medstatstar/ct-samplesize" }
permissions:
  scope: "user-space-only"
  network: "required"
  network_note: "v5 requires the remote coze compute endpoint (CTSS_COZE_ENDPOINT, or CTSS_COZE_MOCK=1 for a local demo) — the published skill has no local compute fallback. Only trial-design parameters leave the machine (no patient data); every request also carries a hostname hash `query_origin` (sha256, for server attribution/rate-limit, ct-base §8.6) and the OS-language-derived `locale`. Outbound authorization gate (ct-base §5): the public endpoint is pre-whitelisted in config/config.json auto_approve_endpoints (never prompts, but the assistant states what is sent on first use); user-custom endpoints trigger a one-time AUTH-BLOCK user confirmation before any data leaves the machine. Payloads are sanitized (PII stripped) before sending."
  filesystem: "writes figures to CTSS_OUTPUT_DIR (default ./outputs) and optional curve PNGs; otherwise read-only"
  data: "no patient/external data leaves the boundary — only trial-design parameters plus the hostname hash (query_origin) and locale metadata are sent to the coze service"

---

# Clinical Trial Sample Size & Power

## Language

Guides: [README.md](https://github.com/medstatstar/ct-samplesize/blob/main/README.md) · [README_zh-CN.md](https://github.com/medstatstar/ct-samplesize/blob/main/README_zh-CN.md)

### Language policy

- This skill's documentation (SKILL.md, AGENTS.md, references/*) is English-only per **ct-base §4** — no Chinese required in docs. The coze R engine emits **bilingual templates via an explicit `locale` parameter** (zh/en; default en = language-neutral) — numbers & standard labels come from the dictionary, never through a generative model. The **local LLM presentation layer** arranges the template narrative into natural user language, quoting stats values verbatim; auto-switch on zh/CN OS, or explicit prompt override. Code output is always English.
- **Hybrid bilingual (mixed model).** The R engine reads `req$locale` (`zh`/`en`) and outputs the narrative in that language using the built-in bilingual dictionary; absent a `locale` field it defaults to English (language-neutral, deterministic, independent of server locale). The local CLI sends `locale` automatically (`coze_client` resolves it from OS detection); a prompt can override it. **Force-switch at CLI level:** set `CTSS_LOCALE=zh|en` (e.g. `CTSS_LOCALE=en python scripts/samplesize_power.py ...`) — required on a Chinese-Windows host where `LANG` cannot override OS detection.
- **Numeric fidelity is a hard rule.** `stats` JSON values must be quoted verbatim by the presentation layer — never rewritten, rounded, or re-translated by the LLM.
- **Figures are special-cased.** The SVG returned by coze is **always English**, regardless of `locale` — curve/visualize labels are hard-coded English in the R engine (server headless has no CJK fonts; a server-rendered bitmap with Chinese would be tofu). If user-supplied text (e.g. a Chinese project name) ends up in the SVG, the local LLM must, **before rendering**, detect CJK runs and extend their `font-family` with a CJK font (e.g. `"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC"`) so Chinese renders correctly client-side.

## Purpose

This skill provides clinical trial researchers with an easy-to-use, comprehensive sample size & power calculation tool. **The default authoritative engine is a remote coze R compute service** (rpact / gsDesign / TrialSize / PowerTOST, 20+ packages — running server-side, so your machine needs **no local R**), covering all 49 test types. Results come in Chinese or English per the OS language setting (prompt can force-switch). Reproducible R code is available on request (coze returns it, or forced via `CTSS_RETURN_R_CODE`).

---

## Features

| Capability | Description | Typical Scenario |
|:---|:---|:---|
| **① Sample size ⇄ Power (bidirectional)** | Solve n given target power, AND solve achievable power given fixed n. `--power` (forward) and `--nobs` (reverse) are mutually exclusive; covers all 49 types. | Sample size fixed, evaluate if power meets target |
| **② Power curve** | Given a sample-size sequence, batch-compute and plot the **Power curve** (x=sample size, y=power), with a target-power reference line. | Sample-size sensitivity analysis, protocol reporting |
| **③ Sample-size curve** | Given a power-target sequence, batch-compute and plot the **sample-size curve** (x=target power, y=required n). | Resource planning, feasibility assessment |

- ②③ curve mode: list `"20,40,200"` or auto-seq `"20:20:200"` (start:step:stop); overlay multiple effect-size curves for sensitivity (continuous/survival solvers; proportion solvers plot the single p1/p2 series); returns the figure (SVG default per ct-base §19, PNG fallback) **plus the numeric series as machine-readable stats (x/y arrays)**. Full parameters & 49-test examples → `references/cli_examples.md`.
- **★ Auto-curve on simple one/two-group solves (default, user rule 2026-08-20):** for the simple one/two-group tests (`ttest_ind` `ttest_paired` `ttest_one` `proportion_one` `proportion_two`), a curve is **auto-attached by default** when the user did NOT request a curve explicitly — forward solve (`--power`, solving n) appends the **sample-size curve** (x=target power, y=n; default `0.6:0.05:0.95`); reverse solve (`--nobs`, solving power) appends the **power curve** (x=n, y=power; auto range ±50% around the given n). Inline SVG is emitted as usual. Opt out: pass an explicit `--n_seq` / `--power_seq`, or `--dry-run`.

---

## Interaction — Triage first (inherit ct-base §6.2)

Before answering, triage the request into **Simple / Middle / Complex / Vague** (ct-base §6.2):
- **Simple** (test already named, params mostly given) → answer directly, **no menu**.
- **Middle** (single-point but deep — ICH guidance detail, statistical parameter, compliance gray zone, needs 3–4 points) → still answer **directly, no menu** (same path as Simple; mark `difficulty = "middle"` for a richer multi-point answer). When Simple vs Middle is unclear, prefer **Middle**.
- **Complex** (pick test type / design family / many params) → show the **routing menu** below (**the `## Quick Menu` is for the Complex branch only**).
- **Vague** ("not sure which test to use") → **grill-me branch-by-branch probing**, do **not** dump the menu.

**Routing gate (audit follow-up — avoid accidental remote compute):** a **remote coze compute** (data leaves the machine) happens **only** when the user's intent is explicitly a sample-size / power / curve **calculation**. General consulting — "help me figure out my trial design", methodology questions, ICH guidance, "what test should I use" — must be answered **locally without sending anything**, and may use the menu / grill-me flow. Do not fire a coze request on vague or advisory phrasing; ask for the calculation intent first.

## Quick Menu

> Authoritative layered menu: [`references/menu.md`](references/menu.md) · CLI examples & bidirectional solve: [`references/cli_examples.md`](references/cli_examples.md) · Operation SOP: [`references/operation_sop.md`](references/operation_sop.md).

**Top-level entry points (6 endpoint categories):**
- ① **Continuous** — `ttest_ind` `ttest_paired` `ttest_one` `anova` `equivalence` `mixed_model`
- ② **Binary / Proportions** — `proportion_one` `proportion_two` `proportion_paired` `odds_ratio` `risk_ratio` `non_inferiority` `superiority_margin` `be_tost` `vaccine_efficacy` `gsd_proportion`
- ③ **Count / Rates** — `poisson` `recurrent_events` `gsd_poisson`
- ④ **Survival / Time-to-event** — `survival` `ni_survival` `survival_equivalence` `survival_superiority` `cox_covariate` `survival_one_sample` `competing_risks` `survival_historical` `survival_exact` `gsd_survival` `gsd_hazard` `gsd_survival_sim` `gsd_hazard_sim`
- ⑤ **Diagnostic / Method comparison** — `roc` `bland_altman`
- ⑥ **Special / Advanced designs** — `group_sequential` `adaptive` `adaptive_simulate` `bayesian` `dose_escalation` `mams` `dunnett` `win_ratio` `must_win` `historical_controls` `conditional_power` `assurance` `multiple_endpoints` `mediation` `cluster`

**Design-family cross-index** (non-exclusive second entry — full list in `references/menu.md`): Group-Sequential · Adaptive · Equivalence / Non-inferiority · Bayesian · Dose-escalation · MAMS · Historical control · Vaccine · Win-statistics …

> The menu is a *navigation aid*, not a strict taxonomy: the same test is reachable from multiple top-level menus (e.g. `gsd_survival` from both ④ Survival and the Group-Sequential index).

### Adaptive-trial Monte-Carlo simulator

`--test adaptive_simulate` validates adaptive / group-sequential designs empirically (power, type I error, expected N). Designs / spending / futility / `--optimize` / legacy fallback / full guide → [`references/adaptive_simulator.md`](references/adaptive_simulator.md).

---

## Requirements

| Requirement | Details |
|:---|:---|
| **coze compute endpoint** | **Production default.** Set `CTSS_COZE_ENDPOINT` (or `COZE_ENDPOINT`) to the coze R service; covers all 49 tests. For a no-network demo, set `CTSS_COZE_MOCK=1`. |
| **Python** | ≥ 3.8, **stdlib only** (argparse / json / urllib). The v5 refactor removed the local pure-Python fallback and all third-party compute deps (statsmodels / numpy / scipy are no longer required). No local R required. |
| **R (dev / optional)** | **Not shipped in the published skill.** The coze R engine source lives in `adapters/coze/src/r_engine/` (excluded from the publish package, synced to coze). The legacy local-R backend (`adapters/r-assets/local_r_backend.py`) and R templates (`adapters/r-assets/r_templates/`) are kept for offline dev / contribution only — **the v5 `select_backend` no longer routes to them**; they are not part of the published skill. |

---

## ⚠️ Safety

- **No local R / shell is ever executed.** The published skill never runs R or a shell on your machine. The default engine is the remote **coze** compute service: only trial-design parameters (never patient data) are sent, and results come back as numbers + optional figures — inherently safe (stateless compute, no local code execution).
- **SAFE PREVIEW is the default for inspection.** `--dry-run` prints the exact request envelope (test, params, mode) that *would* be sent to coze, without sending anything. `--show-code` reveals the coze request JSON (and, on request, the R source coze used). The legacy `--yes` gate applies only to the optional local-R dev backend (`adapters/r-assets/`).
- **First-use outbound disclosure (audit follow-up):** even though the public coze endpoint is pre-whitelisted (never prompts), the assistant MUST state on first outbound use in a session — in one line: "This will send your trial-design parameters plus a hostname hash (query_origin) and locale to the cloud service https://ct-samplesize.coze.site/run for computation — proceed?" (zh: 本次将把您的试验设计参数连同主机名哈希与系统语言发送至云端服务 https://ct-samplesize.coze.site/run 进行计算，继续吗？). Custom endpoints still trigger the one-time AUTH-BLOCK confirmation.
- Output for reference only; validate before regulatory submissions.

### Security model (transparent disclosure)

> Full disclosure table (remote compute / server-side R / output / network / outbound gate / filesystem), upload confidentiality, and the natural-language outbound guidance → [`references/security_model.md`](references/security_model.md). Key guarantees: no local R/shell; SAFE PREVIEW default; only trial-design parameters ever leave the machine.

---

## User-Uploaded Documents (ct-base §6.7)

This skill is **parameter-driven** (design params via CLI / natural language). When the user uploads a document (protocol / SAP / design brief as `.docx` / `.pptx` / `.pdf` / `.doc`), **convert it to md/text first**, then extract the design parameters — the coze endpoint is a plain-text JSON contract and does **not** accept attachments. Converter: shared **`scripts/office_to_md.py`** (stdlib-only, single parser for docx+pptx; ct-base §6.7 / publish_inject):

| Uploaded format | Handling (ct-base §6.7.1) |
|---|---|
| `.docx` / `.pptx` | `python scripts/office_to_md.py <file>` → md (pptx sectioned by `### Slide N`) |
| `.pdf` / `.doc` / scanned | env `pdf` skill (OCR prompt) / word-reader / text-version prompt — never hand-write a parser |

**🔔 User notice before ANY conversion (ct-base §6.7.2 — show this exact notice first):**
> ⚠️ 所有上传文档将转换为 **md 格式**处理；**PPT 文档转换容易丢失大量信息**（图片、版式、动画、图表等非文本元素），建议用户**最好先自行转换为 md 格式并做内容检查**后再提问，以保证关键内容不丢失。

**Confidentiality (ct-base §6.7.3)**: the skill does **not** judge data confidentiality — the document is converted as-is; **only the extracted design parameters** (test, effect, α, power, n …) are ever sent to coze; the raw document md is used **locally for parameter extraction only** and never forwarded. If the user requires data-not-leaving, guide them to keep computation fully local (extract params and compute manually, or use the legacy dev backend `adapters/r-assets/local_r_backend.py`) — never send document content to coze.

---

## Implementation

**Bidirectional solve:** `--power` (default) solves required `n` given target power; `--nobs N` reverses to achievable power given fixed `n` (mutually exclusive, `--nobs` wins). Default = **SAFE PREVIEW**: `--dry-run` prints the coze request envelope without sending; `--show-code` reveals it (and, with `CTSS_RETURN_R_CODE=1`, the R source coze used); no `--yes` needed for coze (stateless remote compute). Full CLI examples (all 49 tests, reverse-solve, curve mode) → `references/cli_examples.md`; data format → `references/data_format_guide.md`.

**Common params:**
- `--side one|two` (default `two`): test direction; affects t-test, proportion tests, and significance level / required n in curve mode.
- `--sd FLOAT` (optional): treats `--effect` as raw mean difference Δ and auto-computes Cohen's d = Δ / sd; when omitted, `--effect` is Cohen's d directly.

**Curve mode:** `--n_seq "20:20:200"` → Power curve; `--power_seq "0.8,0.9"` → sample-size curve; `--plot_effects` overlays sensitivity curves; base R graphics (no ggplot2). **9 tests support curves** (`.curve_solvers`: `ttest_ind` `ttest_paired` `ttest_one` `anova` `proportion_one` `proportion_two` `survival` `equivalence` `be_tost`); others return "curve not supported".

**R package management (v5):** all R packages run **server-side on coze** (image pre-installs via `adapters/coze/docker/r_packages.txt`) — the published skill never installs R packages locally, and the legacy local-R install flags (`--install-all-packages` / `--run-install`) were **removed in v5.0.2** (dev-only backend uses `adapters/r-assets/`, not shipped). Full test list → `references/cli_examples.md`.

> **Architecture & security:** orchestration (`scripts/samplesize_power.py`) contains **no R code**; `ComputeBackend` (`scripts/compute_backend.py`) routes to `CozeBackend` (default authoritative, server-side R) — the only backend in v5. All R logic (`ss_*` + `run_task.R`) lives in `adapters/coze/src/r_engine/` (synced to coze; published package excludes `adapters/coze/`). Every user string reaching server-side R is validated against a strict allowlist. History → `CHANGELOG.md`.

---

## Figure Output & Rendering (ct-base §19)

Curves and any coze-returned `figures[].svg` follow the **ct-base §19 uniform SVG spec** (same pipeline as `meta-analysis`; no bespoke rendering).

- **★ Agent rule (mandatory):** inline the returned SVG **directly into the conversation stream** (visualization channel) — file-first is forbidden; persisted files are backup/editing only. If inline fails, fall back ① HTML-wrapped preview (vector) → ② PNG. Guide users with natural-language prompts (「图形无法预览，请改用 PNG 图片格式重新出图」/ EN equivalent), never CLI flags.
- **★ No hand-redraw:** present the skill-generated SVG as-is (axes, labels, power reference line included — the fallback generator draws the reference line itself, same `sy()` mapping as data points). Never rebuild curves with ad-hoc coordinates in the reply; charting stays under skill control.
- Details — figure_mode, render-hint thresholds, fallback ladder, reference line rule, reference implementation → [`references/rendering_rules.md`](references/rendering_rules.md).

---

## Formulas & Reports

**Formulas:** `references/formulas.md` (all 49 types) | **Full functions:** `references/extended_functions.md`

Key analytic formulas — e.g. independent t: $n_1 = 2(\frac{Z_{1-\alpha/2} + Z_{1-\beta}}{d})^2$; Schoenfeld survival: $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\log HR)^2}$; Cox w/ covariate (Vittinghoff): $d = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(1-R^2)\,p(1-p)\,(\log HR)^2}$; Cluster DEFF: $DEFF = 1 + (m - 1) \times ICC$. Full table → `references/formulas.md`.

---

## Errors

| Error | Fix |
|:---|:---|
| "云端服务未配置" / "云端服务不可达" | Set `CTSS_COZE_ENDPOINT` (real) or `CTSS_COZE_MOCK=1` (demo); v5 has no local compute route (dev: run the legacy backend from `adapters/r-assets/` directly) |

## Bug Reporting (ct-base §20.3, adapter: `adapters/bug_report.py`)

- **Trigger:** two paths — (A) **explicit user request** ("report a bug" / "反馈问题" / "提交错误报告"): go straight to two-stage confirmation, no strong signal needed, unlimited per session; (B) **strong signal** (CLI non-zero exit / engine error / user questions correctness) **and** the same test was retried ≥1 → at most 1 unsolicited proposal/session. Weak signal (just repeated tuning) never triggers.
- **Two-stage confirmation (2026-08-21, from three-stage):** ① propose-with-preview — give the bilingual `confirm_prompt` **together with** the full report (`render_report_text`, state "sanitized, no input data", invite a problem description; if the user adds a description, re-render and re-show before consent) → ② on explicit consent, `send_to_endpoint` (auto action=report, endpoint `https://ct-bugreport.coze.site/run`, token = embedded §5 public credential). If the user declines, never re-propose this session.
- **Sanitization is hard:** report contains only the 11-key whitelist (skill/version/test/error_type/error_code/engine_status/**description**/locale/query_origin/session_hash/attempts) — never raw data files or subject records. `description` is the single free-text field for debugging, **user-reviewed disclosure**: write the symptom / reproduction / expected vs actual / **algorithm or function used** (e.g. Schoenfeld formula) / error message; values and study design (HR, power, allocation ratio) are OK if needed to reproduce. The one hard boundary: no identifiable person/institution/subject info. The user reviews it in the stage ① preview before consent; empty description omits the key (old-endpoint compatible). If the session had **no** coze call, use `save_local_report()` (local md + author email, data never leaves the machine).
- **Client-only:** this adapter sends `report` only. The governance actions (get/update/download/delete — pull pending, mark done, download all, clean up) are reserved for the `ct-update` skill (author side); never call them from here.
- **Post-send history回执 (2026-08-22):** after a successful send, the endpoint returns `history` (last submission for the same `query_origin`, or `""`). Compose the reply from `confirm_thanks(locale)` + `build_followup(history, locale)` — bilingual, auto-switched by `locale`: empty `history` → end; `history.resultstr == "done"` → also show the fix note from `history.memo`; otherwise show "not yet fixed". All user-facing strings are bilingual via `_MSGS` and `_current_locale()` auto-detection.

---

## Related skills (ct- library, agent chains as needed)

- **Upstream (context)**: `ct-registry` (competitor / disease landscape, Tier B, via `ct-pipeline` public-intel orchestration)
- **Downstream (handoff)**: `ct-protocol` (protocol skeleton) → `ct-ecrf` (CRF + SDTM mapping spec)
- **Same category (design scope)**: `ct-protocol` / `ct-ecrf` / `ct-eligibility` (D)
- **Public-intel orchestration (Tier B)**: `ct-pipeline` (dispatches `ct-registry` / `ct-safety` / `ct-literature`)

**Version**: v5.1.0 | **Updated**: 2026-08-22 | **License**: MIT

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
由 coze_cases/_contract_index.json 生成 adapters/r-assets/coze_contract.md。

单一真相源 = _contract_index.json（与 CLI --test choices / R 引擎 dispatch 三者一致）。
本脚本把它渲染为人类可读的 49 test 逐枚举契约文档，避免文档与索引漂移。
"""
from __future__ import annotations
import os, json

_HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(_HERE, "_contract_index.json")
OUT = os.path.join(_HERE, "..", "adapters", "r-assets", "coze_contract.md")

# 信封层级约定（与 coze_client.build_params / call 一致），作为文档前置背景
ENVELOPE_SECTION = """\
# ct-samplesize v5 — coze R 引擎契约（coze_contract）

> 单一真相源：`coze_cases/_contract_index.json`（与 CLI `--test` choices、R 引擎
> `run_task.R` dispatch 三者名称完全一致）。本文档由该索引自动生成，勿手改；
> 改契约请改索引后用 `python coze_cases/gen_contract_doc.py` 重新渲染。

## 1. 角色与端点

- 唯一计算后端 = 远端 coze R 计算服务（`CozeBackend`），本地不跑 R。
- `select_backend(test)` 只返回 `CozeBackend`；coze 不可达即报错，无本地回退。
- 出站受 ct-base §5 授权门控；payload 经 `sanitize()` 脱敏；`CTSS_COZE_MOCK=1` 走本地 mock 信封（不触网、不走授权）。

## 2. 请求信封（build_params 序列化）

`build_params(test, args, ctx)` 仅序列化计算相关 CLI 参数字段（本地控制标志
`--yes/--dry-run/--show_code/--test` 及曲线序列 `n_seq/power_seq/plot_effects` 不进入
`params`）；并附三个派生量：

- `solve_for_power`：给定 `nobs` 求效能时为 `true`，否则 `false`（求样本量）。
- `alt`：`one-sided` → `"greater"`，`two-sided` → `"two.sided"`。
- `d_val`：提供 `--sd` 时 `--effect` 视为原始均差 Δ，`d = Δ/sd`；否则 `--effect` 直接为 Cohen's d。

顶层信封字段：`{test, params, mode, return_r_code, locale, query_origin, resolved_spec}`。

## 3. 响应信封（v5 协议）

`{status, stats, narrative, figures, warnings, notes, repro}`：

- `status`：`"ok"` / `"error"`。
- `stats`：数值结果（n_per_arm / total_n / power / conditional_power / assurance_prob / events …）。
- `narrative`：人类可读的中文/英文叙述。
- `figures`：可选，SVG/PNG/HTML 图形（曲线类请求返回）。
- `warnings` / `notes`：提示与备注。
- `repro`：R 源码 + R 版本 + 所用包（受 `return_r_code` 控制回传）。

## 4. 49 test 逐枚举表

| # | `--test` | 家族 | R 函数 | 必备参数 (CLI) | 关键输出 | 备注 |
|---|----------|------|--------|----------------|----------|------|
"""


def render_row(i, t):
    test = t["test"]
    fam = t.get("family", "")
    fn = t.get("r_function", "")
    req = ", ".join(t.get("required", [])) or "—"
    out = ", ".join(t.get("output", [])) or "—"
    note = t.get("notes", "").replace("\n", " ")
    # 表格内管道符转义
    def esc(s):
        return s.replace("|", "\\|")
    return "| %d | `%s` | %s | `%s` | %s | %s | %s |" % (
        i, test, esc(fam), esc(fn), esc(req), esc(out), esc(note))


def main():
    with open(INDEX, encoding="utf-8") as f:
        idx = json.load(f)
    rows = "\n".join(render_row(i + 1, t) for i, t in enumerate(idx["tests"]))
    footer = (
        "\n## 5. 一致性校验\n\n"
        "- `coze_cases/_contract_index.json`：机器可读的 49 test 契约索引（本文档来源）。\n"
        "- `tests/coze_cases_regression.py`：离线断言每例请求信封契约 + 49 test 全量 smoke\n"
        "  （防 `--yes/--dry-run/--test` 等控制标志外泄进 `params`）；`CTSS_COZE_LIVE=1`\n"
        "  时追加真实 coze 响应信封形态回归。\n"
        "- `tests/test_nl_local.py`：E1/E2 本地确定性层（classify_test + param_aliases）单测。\n"
        "- 三者任一变更须重跑回归，保持 CLI / R 引擎 / 文档 三者命名与参数一致。\n"
    )
    doc = ENVELOPE_SECTION + rows + footer
    out_path = os.path.normpath(OUT)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote %s (%d tests)" % (out_path, len(idx["tests"])))


if __name__ == "__main__":
    main()

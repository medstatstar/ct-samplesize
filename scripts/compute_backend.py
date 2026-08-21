#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_backend.py — ct-samplesize v4.0 计算后端抽象层

架构原则（v4.0.1，来自用户需求）：
  1. **默认一律优先调用 coze 工作流**（CozeBackend，权威引擎，覆盖全部 test）。
     未显式指定后端时，coze 可用即走 coze；coze 不可达则报错并提示配置，
     绝不静默回退到本地计算。
  2. **本地分析（本地 R / 本地 Python 兜底）仅当用户明确要求时才启用**，
     三种显式方式：CLI `--local`、环境变量 `CTSS_BACKEND=local-r`（或 r）、
     或 `CTSS_FORCE_R=1`（坚持用 R 真相源）。
  3. 本地 R 后端（LocalRBackend）位于 adapters/r-assets/，发布包剔除；仅开发/过渡期或
     用户显式请求本地时使用，非默认路径。
  4. R 永远是真相源：用户可经环境变量要求「完全用 R 实现」(CTSS_FORCE_R) 或
     「返回完整 R 代码 + R 结果」(CTSS_RETURN_R_CODE)。

向后端统一的契约：
  - 入参：test(str), args(argparse.Namespace), ctx(dict)
        ctx = {
          "confirmed": bool,        # --yes 显式确认执行（否则安全预览）
          "solve_for_power": bool,  # True=给定 n 求 power；False=给定 power 求 n
          "alt": str,               # "greater" | "two.sided"
          "d_val": float,           # 折算后的效应量（Cohen's d 等）
          "return_r_code": bool,    # 是否随结果返回 R 源码 + R 数值
        }
  - 出参：Result 同构体（数值 + 可选 R 代码/结果 + 可选可视化产物 figures）
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── 出站调用收口（ct-base §16.9）：统一从 adapters/ 导入，确保 adapters 包可被解析 ──
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)


# ── 本地 Python 兜底覆盖的 test 集合（仅单/两样本优效性基础检验）──
# 这些 test 在 R 端同样完整实现（保留于 adapters/r-assets/），本地 Python 只是 coze 不可达时的应急。
PY_FALLBACK_SET = {
    "ttest_ind", "ttest_one", "ttest_paired",
    "proportion_one", "proportion_two",
}


@dataclass
class Figure:
    """coze 返回的可视化产物（SVG / HTML / PNG 等）。"""
    format: str           # "svg" | "html" | "png" | ...
    content: str          # 图形标记本身（SVG 源码 / HTML 片段 / base64…）
    caption: str = ""     # 图注


@dataclass
class Result:
    """跨后端统一的返回同构体。编排层据此渲染文本与图形。"""
    text: str = ""                                  # 已本地化的人类可读叙述
    figures: List[Figure] = field(default_factory=list)
    r_code: Optional[str] = None                    # R 源码（return_r_code 或 coze 提供）
    r_result: Optional[Dict[str, Any]] = None       # R 端算出的数值结果
    meta: Dict[str, Any] = field(default_factory=dict)  # 机器可读字段（n/power/...），供 QA
    backend: str = ""                               # 实际产出后端名


class ComputeBackend:
    """所有计算后端的抽象基类。"""

    name = "base"

    #: 是否需要 --yes 显式确认才执行。
    #: 本地 R 会在本机启动 Rscript 进程 → True（沿用 v3.x 的安全预览语义）；
    #: coze 远程纯计算、本地 Python 闭式解均无本地副作用 → False。
    requires_confirmation = False

    def preview(self, test: str, args, ctx: dict):
        """返回「将要执行 / 发送的载荷」文本，供 --dry-run / --show-code 展示。

        无可展示载荷的后端返回 None。
        """
        return None

    def compute(self, test: str, args, ctx: dict) -> Result:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# 后端可用性探测
# ─────────────────────────────────────────────────────────────────────────────

def _coze_endpoint() -> Optional[str]:
    return os.environ.get("CTSS_COZE_ENDPOINT") or os.environ.get("COZE_ENDPOINT")


def coze_available() -> bool:
    """coze 端是否可调用。

    判定顺序（2026-08-19 修复：必须与 coze_client._resolve_endpoint 一致，
    否则内嵌公共端点存在时 CLI 层误判"coze 不可达"）：
      - coze_client._resolve_endpoint()（env CTSS_COZE_ENDPOINT/COZE_ENDPOINT
        优先，其次随技能发布的内嵌公共端点）非空 → 可用（真实模式）
      - 否则若 CTSS_COZE_MOCK=1 → 启用本地 mock 模式（演示/测试用，返回样例信封）
      - 否则不可用（CLI 报错提示配置，绝不静默回退）
    """
    try:
        from adapters.coze_client import _resolve_endpoint
        if _resolve_endpoint():
            return True
    except Exception:
        # 内嵌凭据缺失等异常 → 继续按 env/mock 判定，不阻塞
        if _coze_endpoint():
            return True
    return os.environ.get("CTSS_COZE_MOCK") in ("1", "true", "yes")


def _force_r() -> bool:
    return os.environ.get("CTSS_FORCE_R") in ("1", "true", "yes")


def _return_r_code() -> bool:
    return os.environ.get("CTSS_RETURN_R_CODE") in ("1", "true", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# 后端懒加载（避免发布包导入 adapters/r-assets 中的 R 代码）
# ─────────────────────────────────────────────────────────────────────────────

_LOCAL_R_BACKEND = None
_LOCAL_R_TRIED = False


def _load_local_r_backend() -> ComputeBackend:
    """从 adapters/r-assets/ 懒加载本地 R 后端（发布包中不存在，故用懒加载）。"""
    global _LOCAL_R_BACKEND, _LOCAL_R_TRIED
    if _LOCAL_R_TRIED:
        if _LOCAL_R_BACKEND is None:
            raise RuntimeError("local R backend unavailable (adapters/r-assets not present)")
        return _LOCAL_R_BACKEND
    _LOCAL_R_TRIED = True
    here = os.path.dirname(os.path.abspath(__file__))
    r_assets = os.path.join(os.path.dirname(here), "adapters/r-assets")
    if not os.path.isdir(r_assets):
        raise RuntimeError("adapters/r-assets directory not found (published skill has no local R)")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "local_r_backend", os.path.join(r_assets, "local_r_backend.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _LOCAL_R_BACKEND = mod.LocalRBackend()
    return _LOCAL_R_BACKEND


# ─────────────────────────────────────────────────────────────────────────────
# 后端选择（迁移缝隙）
# ─────────────────────────────────────────────────────────────────────────────

def select_backend(test: str, prefer_local: bool = False) -> ComputeBackend:
    """选择后端（重构 v5：本地不再提供 R/Python 分析，唯一后端 = coze）。

    架构原则（v5.0.0，2026-08-19 重构）：
      - 所有数值计算全部由 coze 端 R 引擎完成；
      - 本地不安装 R、不做分析；本地 LLM 只做需求标准化与结果呈现；
      - 因此本函数**只返回 CozeBackend**；coze 不可达时报错，绝不静默回退。

    兼容性：
      - CTSS_COZE_MOCK=1 → mock 演示信封（不联网，仅演示呈现管线）
      - --local / CTSS_BACKEND / CTSS_FORCE_R 等旧本地开关不再产生本地分析，
        全部等价于「走 coze」（忽略），避免旧习惯造成"本地算"的误解。
    """
    from adapters.coze_client import CozeBackend  # 延迟导入，避免循环

    # 唯一后端：coze（真实端点或 mock）
    if coze_available():
        return CozeBackend()

    try:
        from i18n import t as _t  # 延迟导入，避免循环依赖
        _msg = _t("error.coze_unreachable")
    except Exception:  # noqa: BLE001 - i18n 不可用时的英文兜底（单语，不双显）
        _msg = ("coze endpoint unreachable — set CTSS_COZE_ENDPOINT=<service url> "
                "or CTSS_COZE_MOCK=1 (v5: all computation runs server-side via coze)")
    raise RuntimeError(_msg)

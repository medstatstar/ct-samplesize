#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coze_client.py — ct-samplesize v4.0 coze 后端（权威计算引擎）

职责：
  - 将本地解析好的参数打包成请求信封，调用 coze 端 R 服务。
  - 解析 coze 返回的多部件信封（数值 + 可选 R 代码/结果 + 可选可视化产物）。
  - 端点与 Bearer token 默认取自 `coze_token_embedded`（随技能发布的公共凭据，
    XOR+base64 混淆内嵌）；可用 env(CTSS_COZE_ENDPOINT / CTSS_COZE_TOKEN) 覆盖。
  - mock 模式（CTSS_COZE_MOCK=1）仍保留，用于无网络/演示场景返回样例信封。

出站授权（ct-base §5 安全模型 / docs/02-governance-redlines.md，2026-08-19 应用）：
  - 任何发往外部端点的请求在真正发送前经 `_check_outbound_authorization` 门控：
    命中 config/config.json 的 auto_approve_endpoints 白名单（公共端点已由作者预置，
    永不弹确认）或本会话内存已授权 → 放行；否则 stderr 输出 AUTH-BLOCK + 全库统一
    确认提示，**不发送**（授权不阻断流程：返回 None，由调用方提示用户）。
  - 发往端点的 payload 经 `sanitize()` 剥离 PII（身份证 / 手机号 / 邮箱）。
  - Windows 系统代理残留（WinError 10061）→ 绕过代理直连重试一次。
  - 异常与日志绝不回显 token / payload 明文（只打异常类型与端点）。

信封契约见 adapters/r-assets/coze_contract.md。
"""
import hashlib
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

from compute_backend import ComputeBackend, Figure, Result

# 自举 sys.path（2026-08-19 修复）：本文件通过 `adapters.coze_client` 方式导入时
# （CLI 主路径 samplesize_power.py → compute_backend → adapters.coze_client），
# sys.path 通常不含 adapters/ 目录 → 裸 `from coze_token_embedded import` 失败 →
# 内嵌端点/token 静默丢失 → coze_available() 误判"coze 不可达"。
# 这里把本文件所在目录加入 sys.path（幂等），保证两种导入方式行为一致。
_HERE_DIR = str(Path(__file__).resolve().parent)
if _HERE_DIR not in sys.path:
    sys.path.insert(0, _HERE_DIR)

try:
    from coze_token_embedded import (
        get_token as _embedded_get_token,
        get_endpoint as _embedded_get_endpoint,
    )
except Exception:  # pragma: no cover - 内嵌凭据缺失时退化为仅 env/mock
    _embedded_get_token = None
    _embedded_get_endpoint = None

# ---------------------------------------------------------------------------
# 出站授权确认提示（ct-base language_policy：一次性提示强制走 i18n，禁止硬编码）
# ---------------------------------------------------------------------------
try:
    from i18n import t as _i18n_t  # 单一事实来源：scripts/i18n.py _MESSAGES
    _HAS_I18N = True
except Exception:  # pragma: no cover - 测试环境缺 scripts 路径时退化
    _HAS_I18N = False
    _i18n_t = None


# ---------------------------------------------------------------------------
# §8.6 query_origin：调用来源标识（全库统一，审计 / 归因 / 限流）
# ---------------------------------------------------------------------------
def _compute_query_origin() -> str:
    """§8.6 query_origin：按本机 hostname 计算稳定标识，由客户端（技能安装设备）生成。

    - 格式 `sha256:<64 hex>`；同一台机器每次返回完全相同的值（便于按机器审计/限流）。
    - SHA256 单向不可逆，不含明文 hostname / IP / 任何 PII。
    - **必须由客户端生成随请求发出**，禁止由 coze 服务器兜底生成（服务器容器重建即漂移）。
    """
    return "sha256:" + hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# 出站授权门控（ct-base 全库统一范式，对齐 ct-advisor scripts/refine_answer.py）
# ---------------------------------------------------------------------------
# 本会话内存已授权端点（随进程重置：同一次脚本运行内多次出站只确认一次）。
_SESSION_AUTHORIZED_ENDPOINTS = set()


def _default_config_path() -> str:
    """config.json 默认路径（技能根 config/）。"""
    here = Path(__file__).resolve().parent.parent  # adapters/ -> 技能根
    return str(here / "config" / "config.json")


def _load_auto_approve_endpoints(config_path: str) -> set:
    """从 config.json 加载 auto_approve_endpoints 白名单。"""
    try:
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return set(cfg.get("auto_approve_endpoints", []) or [])
    except Exception:
        return set()


def _check_outbound_authorization(endpoint: str, config_path: str = None) -> bool:
    """出站授权检查：返回 True 放行，False 拦截（不发送）。

    语义（ct-base）：
      - 命中本会话内存 / config.json 白名单（作者预置公共端点）→ True，永不弹确认；
      - 否则 stderr 输出 AUTH-BLOCK + 全库统一确认提示，返回 False。
    白名单写入须由用户确认触发（agent 引导、不代写 config.json）。
    """
    if endpoint in _SESSION_AUTHORIZED_ENDPOINTS:
        return True
    cfg_path = config_path or _default_config_path()
    if endpoint in _load_auto_approve_endpoints(cfg_path):
        return True
    # 一次性出站授权确认：强制走 i18n 单语输出（ct-base language_policy §首次使用与一次性运行期提示）。
    # 主路径经 t("auth.coze_outbound") 取词（单一事实来源 scripts/i18n.py），
    # 仅在 i18n 不可导入（测试环境缺 scripts 路径）时退化为英文安全提示，绝不中英双显/硬编码。
    if _HAS_I18N:
        prompt = _i18n_t("auth.coze_outbound", endpoint=endpoint)
    else:
        prompt = (
            "[ct-samplesize] outbound to %s requires user confirmation. "
            "Only trial-design parameters (no personal data) are sent; "
            "declining disables cloud computation." % endpoint
        )
    sys.stderr.write(
        "[ct-samplesize][AUTH-BLOCK] outbound to %s requires user confirmation.\n"
        "%s\n" % (endpoint, prompt)
    )
    return False


def _authorize_endpoint(endpoint: str, config_path: str = None) -> None:
    """（供 agent 引导用户确认后调用）把端点加入会话内存授权。"""
    _SESSION_AUTHORIZED_ENDPOINTS.add(endpoint)


# ---------------------------------------------------------------------------
# payload 脱敏（ct-base：出站 payload 发送前剥离 PII；日志绝不回显明文）
# ---------------------------------------------------------------------------
# 注意（2026-08-19 修复）：原实现用 \b 边界，Python 把中文字符视为 \w，
# "身份证<18位>" 中 "证" 与数字之间无 \b → 身份证/手机号永不匹配。
# 改为数字/字母数字负向断言（对中文相邻文本同样生效）：
#   ID    18位（17数字+X/x）；先于 PHONE 匹配，防止手机号模式吞身份证子串
#   PHONE 大陆手机号
#   EMAIL 邮箱（ASCII 边界，避免吞并相邻中文）
_PII_PATTERNS = [
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "<ID>"),               # 身份证号
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "<PHONE>"),             # 大陆手机号
    (re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+(?![A-Za-z0-9])"), "<EMAIL>"),  # 邮箱
]


def sanitize(obj):
    """递归剥离 PII（身份证 / 手机号 / 邮箱），返回脱敏副本（不修改原对象）。"""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, str):
        for pat, repl in _PII_PATTERNS:
            obj = pat.sub(repl, obj)
        return obj
    return obj


# ---------------------------------------------------------------------------
# 端点 / token / locale 解析
# ---------------------------------------------------------------------------
def _resolve_token() -> str:
    """取 coze Bearer token：env(CTSS_COZE_TOKEN) > 内嵌公共 blob。"""
    env = os.environ.get("CTSS_COZE_TOKEN")
    if env:
        return env
    if _embedded_get_token is not None:
        return _embedded_get_token()
    return ""


def _resolve_endpoint() -> str:
    """取 coze 端点：env(CTSS_COZE_ENDPOINT/COZE_ENDPOINT) > 内嵌公共常量。"""
    env = os.environ.get("CTSS_COZE_ENDPOINT") or os.environ.get("COZE_ENDPOINT")
    if env:
        return env
    if _embedded_get_endpoint is not None:
        return _embedded_get_endpoint()
    return ""


def _current_locale() -> str:
    """推导当前界面语言（zh / en），供 coze 端本地化 narrative 与授权提示。

    优先级：
      1. CTSS_LOCALE 环境变量（zh/en，显式强制切换——中文 Windows 上
         is_chinese_os 恒为 True 无法靠 LANG 覆盖，此为 CLI 层强制手段）
      2. i18n.is_chinese_os()（系统 locale 检测）
    失败回退 en，避免阻塞主流程（i18n 不可导入多为测试环境缺 scripts 路径）。
    """
    _v = os.environ.get("CTSS_LOCALE", "").strip().lower()
    if _v in ("zh", "zh_cn", "zh-cn", "cn"):
        return "zh"
    if _v in ("en", "en_us", "en-us"):
        return "en"
    try:
        from i18n import is_chinese_os
        return "zh" if is_chinese_os() else "en"
    except Exception:
        return "en"


# 本地编排控制字段，不进入发往 coze 的请求参数
_PARAM_EXCLUDE = frozenset({
    "yes", "dry_run", "show_code", "install_all_packages", "test",
    # 曲线序列/效应量列表走 curve_* 协议（R 端 run_task.R 曲线分支消费）
    "n_seq", "power_seq", "plot_effects",
})


def build_params(test, args, ctx):
    """把 args + ctx 序列化为 JSON 友好的请求参数。

    仅包含计算相关 CLI 参数（本地控制标志 --yes/--dry-run/--show_code/
    --install-all-packages 与顶层字段 test 不进入 params）；并附三个派生量
    solve_for_power / alt / d_val（见 adapters/r-assets/coze_contract.md §2）。
    return_r_code 为信封顶层字段，不重复塞入 params。
    """
    params = {}
    for k, v in vars(args).items():
        if k in _PARAM_EXCLUDE:
            continue
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool, list)):
            params[k] = v
    params.update({
        "solve_for_power": ctx.get("solve_for_power", False),
        "alt": ctx.get("alt", "two.sided"),
        "d_val": ctx.get("d_val"),
    })
    # 曲线参数映射（CLI 名 → coze 端 curve_* 协议，R 端 .run_curve 消费）
    for cli_key, coze_key in (("n_seq", "curve_n_seq"),
                              ("power_seq", "curve_power_seq"),
                              ("plot_effects", "curve_effects")):
        val = getattr(args, cli_key, None)
        if val:
            params[coze_key] = val
    return params


def _mock_envelope(test, params, mode, return_r_code):
    """本地 mock：演示用样例信封（v5 结构：status/stats/narrative/figures）。"""
    sample_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="160">'
        '<rect width="100%%" height="100%%" fill="#fafafa"/>'
        '<text x="10" y="30" font-family="sans-serif" font-size="14">'
        'MOCK power curve (%s)</text>'
        '<polyline points="20,140 120,80 300,30" fill="none" stroke="#c0392b" stroke-width="2"/>'
        '</svg>' % test
    )
    env = {
        "status": "ok",
        "stats": {"test": test, "mode": mode, "note": "mock"},
        "narrative": (
            "MOCK coze response for test=%s (mode=%s).\n"
            "真实端点就绪后此处返回 R 端算出的数值与叙述。" % (test, mode)),
        "figures": [
            {"format": "svg", "content": sample_svg,
             "caption": "Mock power curve (%s)" % test}
        ],
        "warnings": ["MOCK 响应，非真实计算"],
        "notes": "",
        "repro": {"r": "# MOCK R code for %s" % test, "r_version": "mock",
                  "packages": {}},
    }
    return env


def _urlopen_with_proxy_fallback(req, timeout):
    """urllib 请求 + Windows 系统代理残留直连重试（ct-base 出站容错）。

    系统代理残留（指向无监听端口 → WinError 10061）时，绕过代理
    （ProxyHandler({})）直连重试一次；直连仍不可达照常上抛。
    """
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", None)
        winerr = getattr(reason, "winerror", None)
        errno = getattr(reason, "errno", None)
        if winerr == 10061 or errno in (10061, 10060, 11004):
            # 系统代理残留 → 直连重试一次（计算请求幂等，重试无副作用）
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            return opener.open(req, timeout=timeout)
        raise


def call(test, params, mode, return_r_code, locale=None):
    """调用 coze 服务，返回 R 引擎信封 dict（重构 v5 协议）。

    模式（优先级从高到低）：
      - CTSS_COZE_MOCK=1 → 本地 mock 信封（演示/测试；无出站、不走授权门控）
      - CTSS_COZE_ENDPOINT / COZE_ENDPOINT 或内嵌端点 → 真实 HTTP POST（urllib，无第三方依赖）
      - 均未设置 → 抛错提示配置端点

    出站授权（ct-base §5）：真实发送前经 _check_outbound_authorization 门控；
    未授权 → stderr AUTH-BLOCK + 确认提示，**不发送**、返回 None（授权不阻断流程，
    由调用方提示用户）。发往端点的 payload 经 sanitize() 剥离 PII。
    """
    # mock 显式优先：设置了 mock 绝不联网、不走授权门控（2026-08-19 修复：
    # 原实现把 mock 分支放在 endpoint 之后，内嵌端点恒非空导致 mock 成为死代码）
    if os.environ.get("CTSS_COZE_MOCK") in ("1", "true", "yes"):
        return _mock_envelope(test, params, mode, return_r_code)
    endpoint = _resolve_endpoint()
    if endpoint:
        # ── 出站授权门控（ct-base 全库统一）──────────────────────────────
        if not _check_outbound_authorization(endpoint):
            return None  # AUTH-BLOCK：不发送，调用方提示用户
        token = _resolve_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer %s" % token
        # 发送前脱敏（剥离 PII）；脱敏副本用于发送，原 params 不受影响
        payload = json.dumps({
            "test": test, "params": sanitize(params), "mode": mode,
            "return_r_code": return_r_code,
            "locale": locale or _current_locale(),
            "query_origin": _compute_query_origin(),
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=payload, headers=headers, method="POST")
        try:
            with _urlopen_with_proxy_fallback(req, timeout=180) as resp:
                outer = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            # 只打异常类型 + 端点（绝不回显 token / payload）
            raise RuntimeError("coze 调用失败（%s）: %s" % (endpoint, e))
        # v5：解析外层 result（R 引擎信封 JSON 字符串）；兼容旧直接信封
        result_str = outer.get("result") if isinstance(outer, dict) else None
        if isinstance(result_str, str) and result_str.strip().startswith("{"):
            try:
                return json.loads(result_str)
            except ValueError:
                return outer
        return outer if isinstance(outer, dict) else {
            "status": "error", "notes": "coze 返回空/非对象响应"}
    raise RuntimeError(
        "coze 端点未配置：请设置 CTSS_COZE_ENDPOINT（真实），"
        "或 CTSS_COZE_MOCK=1（本地演示）。")


class CozeBackend(ComputeBackend):
    name = "coze"
    # coze 为远程纯计算、无本地副作用 → 不强制 --yes；--dry-run 仍只预览不发送。
    requires_confirmation = False

    def preview(self, test, args, ctx):
        """--dry-run / --show-code 时展示将要发往 coze 的请求信封（脱敏后）。"""
        if not (ctx.get("dry_run") or ctx.get("show_code")):
            return None
        return json.dumps({
            "endpoint": _resolve_endpoint() or "(mock)",
            "test": test,
            "mode": "power" if ctx.get("solve_for_power") else "n",
            "return_r_code": ctx.get("return_r_code", False),
            "locale": ctx.get("locale") or _current_locale(),
            "query_origin": _compute_query_origin(),
            "params": sanitize(build_params(test, args, ctx)),
        }, ensure_ascii=False, indent=2)

    def compute(self, test, args, ctx):
        params = build_params(test, args, ctx)
        mode = "power" if ctx.get("solve_for_power") else "n"
        env = call(test, params, mode, ctx.get("return_r_code", False),
                   locale=ctx.get("locale") or _current_locale())
        # AUTH-BLOCK：未授权不发送，提示用户（授权不阻断流程）
        if env is None:
            raise RuntimeError(
                "出站未授权：本次未发送到云端计算。"
                "若同意发送，请确认后将端点加入 config/config.json 的 "
                "auto_approve_endpoints（或重跑本命令）。")
        # v5 信封：status/stats/narrative/warnings/notes/repro
        if not isinstance(env, dict):
            raise RuntimeError("coze 返回非对象响应")
        # 契约 §5：coze 出错可返回 {"error": {...}}；原样呈现 message
        err = env.get("error")
        if err:
            msg = err.get("message") or err.get("code") or "coze 端返回未知错误"
            raise RuntimeError("coze 计算失败: %s" % msg)
        status = env.get("status")
        if status in ("error", "unknown_task"):
            raise RuntimeError("coze 计算失败: %s" % (env.get("notes") or status))
        stats = env.get("stats") or {}
        repro = env.get("repro") or {}
        return Result(
            text=env.get("narrative", ""),
            figures=[Figure(f.get("format", "svg"), f.get("content", ""),
                            f.get("caption", "")) for f in env.get("figures", [])],
            r_code=repro.get("r") if ctx.get("return_r_code") else None,
            r_result=stats,
            meta=stats,
            backend=self.name,
        )

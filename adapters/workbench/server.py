#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — ct-samplesize 工作台 HTTP 后端（stdlib-only，不引入 FastAPI）

架构约束
--------
ct-samplesize 是 **stdlib-only**（零第三方依赖），因此不能引入 FastAPI / flask。
本后端用 `http.server.ThreadingHTTPServer` 实现 REST + 静态资源服务。

复用关系（避免重复造轮子 / 守住家族红线）
-----------------------------------------
- **form_schema.get_schema()**      : 49 检验 / 178 参数的动态表单 schema（零维护）
- **session_store.SessionStore**    : 「追加提问」会话线程 + 确定性合并（复用 ct-base merge_spec）
- **coze_client.CozeBackend**       : 计算引擎（默认 coze 远端；CTSS_COZE_MOCK=1 离线演示）
- **samplesize_power.build_parser**: argparse 反射，统一参数校验 / choices / 类型转换

ctx 构造严格复刻 scripts/samplesize_power.py::main 的语义
（solve_for_power / alt / d_val / curve / user_language），确保与 CLI 行为一致。

端点
----
GET  /api/health                      健康检查 + 引擎/模式信息
GET  /api/schema                      动态表单 schema（前端渲染输入区）
POST /api/compute                     {test, params, options, session_id?, note?}
POST /api/nl                         {nl, locale?} → 自然语言路由（默认本地大模型 Ollama 识别，不可达降级 classify_test 规则）
POST /api/preview                     {test, params, options}  → 仅返回 coze 请求信封（dry-run）
GET  /api/session/list                列出会话线程
POST /api/session/create              {title?} → 新建线程
GET  /api/session/<id>                线程当前设定 + 历史回合
POST /api/session/<id>/follow         {cur, required?, note?} → 确定性合并审计
POST /api/session/<id>/reset          清空线程设定
DEL  /api/session/<id>                删除线程
POST /api/bugreport                   {desc, test?, params?, session_id?, result_summary?, ua?, url?, locale?} → 默认提交至 ct-base 统一 coze 端点（§20.3.5）；不可达时降级本地 md 兜底
GET  /                              工作台首页（workbench.html）
"""

import os
import sys
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import re

# ──────────────────────────────────────────────────────────────────────────
# 路径 & 导入
# ──────────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL = os.path.normpath(os.path.join(_HERE, "..", ".."))   # ct-samplesize/
_SCRIPTS = os.path.join(_SKILL, "scripts")
_ADAPTERS = os.path.join(_SKILL, "adapters")
for _p in (_HERE, _ADAPTERS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import form_schema                 # noqa: E402  (本地反射层)
import session_store               # noqa: E402  (会话线程)
from coze_client import CozeBackend  # noqa: E402  (计算后端)
import rendering                   # noqa: E402  (复用技能的 canonical HTML 报告生成器)
import bug_report                  # noqa: E402  (ct-base §20.3.5 统一 bug-report coze 端点客户端)
import nl_llm                      # noqa: E402  (NL 识别：本地默认大模型客户端，规则降级)
import tempfile                    # noqa: E402  (导出报告临时目录)

# argparse 反射（构造命名空间 / 校验 choices / 类型转换）
import samplesize_power            # noqa: E402
PARSER = samplesize_power.build_parser()

# 动态表单目录（模块级缓存；反射 49 检验 / 178 参数，零维护）
CATALOG = form_schema.get_catalog()
TEST_NAMES = {t["test"] for t in CATALOG["tests"]}
TEST_REQUIRED = {t["test"]: t["required"] for t in CATALOG["tests"]}

# ── 多值参数检测（确定性层，零 LLM）────────────────────────────────────────────
# 用于「power 0.85 0.9 0.95 都算一下」这类追问：同一参数被给出多个数值 → 分别计算多组。
_MULTI_KEYWORDS = {
    "power":  [r"把握度", r"检验效能", r"检验功效", r"power"],
    "alpha":  [r"显著性水平", r"α", r"alpha"],
    "effect": [r"效应量", r"效应大小", r"标准均差", r"cohen\s*d", r"均差", r"均值差"],
    "margin": [r"非劣效界值", r"等效界值", r"界值", r"margin"],
}
def _detect_multi_values(nl):
    """检测 NL 中同一参数被给出多个数值（如「power 0.85 0.9 0.95」）。

    返回 {param: [v1, v2, ...]}，仅当某参数数值个数 ≥ 2 才收录。
    与 extract_parameters 的单值抽取互补：单值仍进 params（作默认），多值进 route["multi"]。
    """
    out = {}
    for name, kws in _MULTI_KEYWORDS.items():
        for kw in kws:
            pat = r"(?:%s)\s*[:=]?\s*(\d+(?:\.\d+)?(?:\s*[/,、]\s*\d+(?:\.\d+)?)*)" % kw
            m = re.search(pat, nl, flags=re.IGNORECASE)
            if not m:
                continue
            nums = re.findall(r"\d+(?:\.\d+)?", m.group(1))
            vals = [float(x) for x in nums]
            if len(vals) >= 2:
                out[name] = vals
            break  # 该参数已处理，跳到下一个 name
    return out

# ── 咨询路由闸门（ct-base 路由闸门：仅「显式计算意图」才发 coze；
#    设计/方法学咨询句必须留在本地，绝不触发真实计算）──────────────────────────
# 命中下列任一设计/方法学表述 → 判定 intent=advisory，前端据此**不**自动点火 coze，
# 与对话 agent 的路由闸门对齐（vague/advisory 不往外发）。
# 注意：不含「怎么算/如何计算」等显式计算表述（它们属计算意图，应放行）。
_ADVISORY_MARKERS = [
    r"怎么设计", r"如何设计", r"应该用什么(检验|方法|模型|分析)?",
    r"该怎么(选|用|分析)", r"建议(用|采用|选择)", r"推荐(用|采用|选择)",
    r"区别", r"对比", r"如何(分析|解读|评价|选择)", r"怎么(分析|解读|选)",
    r"not sure which test", r"help me figure", r"which test should",
    r"how (to|should|do) (i|we) (design|choose|select|analyze|interpret)",
    r"difference between", r"recommend", r"suggest", r"what test",
]
def _detect_advisory(nl):
    """NL 是否属咨询类（设计/方法学问题，非显式计算意图）。"""
    for m in _ADVISORY_MARKERS:
        if re.search(m, nl, flags=re.IGNORECASE):
            return True
    return False

# 计算后端（默认 coze 远端；CTSS_COZE_MOCK=1 → 离线演示）
BACKEND = CozeBackend()

# 会话仓库（持久化到 <workbench>/sessions.json）
STORE = session_store.SessionStore()

# 技能版本（bug-report 信封的 skill_version 字段；从 SKILL.md frontmatter 读取一次）
def _read_skill_version():
    p = os.path.join(_SKILL, "SKILL.md")
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^version:\s*(\S+)\s*$", line)
                if m:
                    return m.group(1)
    except Exception:
        pass
    return "unknown"
SKILL_VERSION = _read_skill_version()

# Bug 反馈持久化（持久化到 <workbench>/bugreports.json，与 sessions.json 同模式）
BUGREPORTS_FILE = os.path.join(_HERE, "bugreports.json")
_BUGREPORT_LOCK = threading.Lock()
def append_bugreport(entry):
    """追加一条 bug 反馈到 bugreports.json（线程安全、容错）。"""
    with _BUGREPORT_LOCK:
        data = []
        if os.path.exists(BUGREPORTS_FILE):
            try:
                with open(BUGREPORTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f) or []
                if not isinstance(data, list):
                    data = []
            except Exception:
                data = []
        entry = dict(entry or {})
        entry.setdefault("id", "BUG-%d" % (len(data) + 1))
        entry.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        data.append(entry)
        with open(BUGREPORTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return entry

# dest → 选项 flag 映射（用于把前端 JSON 键值还原成 argv 交给 argparse 校验）
_FLAG_BY_DEST = {}
for _act in PARSER._actions:
    for _opt in _act.option_strings:
        if _opt.startswith("--"):
            _FLAG_BY_DEST.setdefault(_act.dest, _opt)

# user_language 解析（尽量复用 CLI 的 i18n 三级优先级）
try:
    from i18n import resolve_user_language as _resolve_lang
except Exception:  # pragma: no cover
    def _resolve_lang(query=None, override=None):
        return override or os.environ.get("CTSS_LOCALE") or "zh"


# ──────────────────────────────────────────────────────────────────────────
# 参数空间构建（dest 键值 → argparse Namespace，自动处理类型/choices/列表）
# ──────────────────────────────────────────────────────────────────────────
def build_namespace(test, params):
    """把前端 JSON 参数（dest 键）还原成 argparse 校验过的 Namespace。"""
    argv = ["--test", str(test)]
    for k, v in (params or {}).items():
        if v is None or v == "":
            continue
        flag = _FLAG_BY_DEST.get(k)
        if flag is None:
            continue  # schema 未登记的字段直接忽略，保护后端
        if isinstance(v, bool):
            if v:
                argv.append(flag)
        elif isinstance(v, list):
            argv += [flag] + [str(x) for x in v]
        else:
            argv.append(flag)
            argv.append(str(v))
    return PARSER.parse_args(argv)


def make_ctx(ns, options):
    """复刻 samplesize_power::main 的 ctx 构造语义。"""
    # 求解方向：给定 nobs → 反求 power
    solve_for_power = bool(ns.nobs is not None and ns.nobs > 0)
    if not solve_for_power:
        ns.nobs = None
    # 检验方向
    alt = "greater" if getattr(ns, "side", "two") == "one" else "two.sided"
    # Cohen's d 折算
    sd = getattr(ns, "sd", None)
    eff = getattr(ns, "effect", None)
    if sd is not None and sd > 0:
        d_val = (eff if eff is not None else 0.5) / sd
    else:
        d_val = eff if eff is not None else 0.5
    curve = bool(ns.n_seq or ns.power_seq or ns.effect_seq
                 or ns.dist_plot or ns.power_time_seq or ns.heatmap)
    dry_run = bool(options.get("dry_run"))
    return {
        "solve_for_power": solve_for_power,
        "alt": alt,
        "d_val": d_val,
        "curve": curve,
        "dry_run": dry_run,
        "return_r_code": True,
        "user_language": _resolve_lang(
            override=options.get("language")
            or os.environ.get("CTSS_LOCALE") or os.environ.get("CTSS_LANG")),
    }


def serialize_result(result):
    """把 coze_client.Result 规整为前端友好的 dict。"""
    return {
        "text": result.text or "",
        "figures": [
            {"format": f.format, "caption": f.caption, "content": f.content}
            for f in (result.figures or [])
        ],
        "r_code": result.r_code,
        "r_result": result.r_result,
        "meta": result.meta,
    }


def extract_summary(merged, result_dict):
    """从历史回放提取简短结果摘要（数值卡核心字段）。"""
    s = {"test": merged.get("test")}
    stats = (result_dict or {}).get("r_result") or {}
    # 常见字段：n / power / n1 / n2 / events ...
    for key in ("n", "n1", "n2", "power", "events", "power_achieved"):
        if key in stats:
            s[key] = stats[key]
    return s


# ──────────────────────────────────────────────────────────────────────────
# 请求分发
# ──────────────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    server_version = "ct-samplesize-workbench/1.0"

    # 工具
    def _send(self, code, obj, ctype="application/json; charset=utf-8"):
        body = obj if isinstance(obj, (bytes, str)) else json.dumps(obj, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            self._send(404, {"error": "not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def _check_auth(self):
        """Token 鉴权：若设置了 CTSS_WB_TOKEN，POST/DELETE 请求必须携带匹配的 token。
        支持 Authorization: Bearer <token> 或 ?token=<token>（便于 curl / 简单链接分享）。
        GET 端点（schema/health/静态资源）不做鉴权，便于嵌入与监控。"""
        if not os.environ.get("CTSS_WB_TOKEN"):
            return True  # 未设 token = 不鉴权（向后兼容，但公开部署强烈建议设置）
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and auth[7:] == os.environ["CTSS_WB_TOKEN"]:
            return True
        qs = parse_qs(urlparse(self.path).query)
        if qs.get("token", [None])[0] == os.environ["CTSS_WB_TOKEN"]:
            return True
        return False

    def log_message(self, *args):  # 静默默认访问日志
        pass

    # GET
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            return self._health()
        if path == "/api/schema":
            qs = parse_qs(parsed.query)
            lang = (qs.get("lang") or ["zh"])[0]
            if lang not in ("zh", "en"):
                lang = "zh"
            # 启动时 CATALOG 固定为 zh；lang=en 时实时生成英文目录
            cat = CATALOG if lang == "zh" else form_schema.get_catalog("en")
            return self._send(200, cat)
        if path.startswith("/api/schema/") and path.count("/") == 3:
            tid = path.rsplit("/", 1)[-1]
            qs = parse_qs(parsed.query)
            lang = (qs.get("lang") or ["zh"])[0]
            if lang not in ("zh", "en"):
                lang = "zh"
            sch = form_schema.schema_for(tid, lang)
            if not sch:
                return self._send(404, {"error": "未知检验类型: %s" % tid})
            return self._send(200, sch)
        if path == "/api/session/list":
            return self._send(200, {"sessions": STORE.list()})
        if path.startswith("/api/session/") and path.count("/") == 3:
            sid = path.rsplit("/", 1)[-1]
            t = STORE.get(sid)
            if not t:
                return self._send(404, {"error": "session not found"})
            return self._send(200, t.to_dict())
        if path == "/" or path == "/index.html":
            return self._send_file(os.path.join(_HERE, "workbench.html"),
                                   "text/html; charset=utf-8")
        if path.startswith("/static/"):
            fp = os.path.normpath(os.path.join(_HERE, path[1:]))
            # 防路径穿越：落点必须仍在 _HERE 内（_HERE 加 os.sep 避免前缀误匹配）
            if not fp.startswith(_HERE + os.sep) and fp != _HERE:
                return self._send(403, {"error": "forbidden"})
            if fp.endswith(".css"):
                return self._send_file(fp, "text/css; charset=utf-8")
            if fp.endswith(".js"):
                return self._send_file(fp, "application/javascript; charset=utf-8")
            return self._send_file(fp, "application/octet-stream")
        return self._send(404, {"error": "not found"})

    def do_OPTIONS(self):
        self._send(204, "")

    # POST
    def do_POST(self):
        if not self._check_auth():
            return self._send(401, {"error": "鉴权失败：缺失或无效的 token（设置 CTSS_WB_TOKEN 环境变量并在请求中携带）"})
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/compute":
            return self._compute()
        if path == "/api/preview":
            return self._preview()
        if path == "/api/nl":
            return self._nl()
        if path == "/api/export":
            return self._export()
        if path == "/api/bugreport":
            return self._bugreport()
        if path == "/api/batch":
            return self._batch()
        if path == "/api/session/create":
            body = self._body_json()
            t = STORE.create(body.get("title"))
            return self._send(200, {"id": t.id, "title": t.title})
        if path.startswith("/api/session/") and path.endswith("/follow"):
            sid = path.split("/")[-2]
            return self._follow(sid)
        if path.startswith("/api/session/") and path.endswith("/reset"):
            sid = path.split("/")[-2]
            t = STORE.reset(sid)
            if not t:
                return self._send(404, {"error": "session not found"})
            return self._send(200, {"id": sid, "current": t.current})
        return self._send(404, {"error": "not found"})

    def do_DELETE(self):
        if not self._check_auth():
            return self._send(401, {"error": "鉴权失败：缺失或无效的 token"})
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/session/") and path.count("/") == 3:
            sid = path.rsplit("/", 1)[-1]
            ok = STORE.delete(sid)
            return self._send(200, {"deleted": ok})
        return self._send(404, {"error": "not found"})

    # ── 端点实现 ──
    def _health(self):
        return self._send(200, {
            "ok": True,
            "skill": "ct-samplesize",
            "backend": BACKEND.__class__.__name__,
            "mock": bool(os.environ.get("CTSS_COZE_MOCK")),
            "tests": len(TEST_NAMES),
            "sessions": len(STORE.list()),
            "time": time.time(),
        })

    def _compute(self):
        body = self._body_json()
        test = body.get("test")
        params = body.get("params") or {}
        options = body.get("options") or {}
        session_id = body.get("session_id")
        note = body.get("note")

        if not test:
            return self._send(400, {"error": "缺少 test 字段"})
        if test not in TEST_NAMES:
            return self._send(400, {"error": "未知检验类型: %s" % test})

        required = TEST_REQUIRED.get(test, [])

        # ── 合并全量 spec（先算 compute_params，再持久化，避免默认值污染会话）──
        # 会话模式：base = 会话当前继承设定；merged = base 覆盖用户本轮 params。
        # 注意：自动补「有默认值」的 required 字段（alpha/side/ratio 等）只进
        # compute_params，**不写回** session.current，避免污染跨轮继承（家族红线）。
        base = {}
        if session_id:
            t = STORE.get(session_id)
            if not t:
                return self._send(404, {"error": "session not found: %s" % session_id})
            base = dict(t.current)
        merged = dict(base)
        merged.update(params)
        merged["test"] = test
        compute_params = dict(merged)
        # 自动补「有默认值」的 required 字段（alpha/side/ratio 等常见值），缺失即填；
        # 不扩到全部 CATALOG——前端 fieldHTML 已按 p.default 预填并发送当前检验的常用值，
        # 服务端仅作兜底，避免把无关参数（margin/accrual_time 等）强塞进计算信封。
        # 真必填且无默认者（effect/p1/p2 等效应量类）保持缺失 → 仍报 400。
        for k in required:
            if k not in compute_params and k in CATALOG["params"]:
                dflt = CATALOG["params"][k]["default"]
                if dflt is not None:
                    compute_params[k] = dflt
        missing = [k for k in required
                   if k not in compute_params
                   and CATALOG["params"].get(k, {}).get("default") is None]

        if missing and not options.get("dry_run"):
            return self._send(400, {
                "error": "必填参数缺失",
                "missing_required": missing,
                "settings_block": session_store.render_settings_block(merged),
            })

        # 会话持久化（仅用户提供的 params + test，确定性合并；默认值不入库）
        audit = None
        if session_id:
            audit = STORE.follow_up(session_id, {**params, "test": test}, required,
                                    note=note or "工作台计算")

        try:
            ns = build_namespace(test, compute_params)
            ctx = make_ctx(ns, options)
        except SystemExit as e:   # argparse 校验失败（choices / 解析）
            return self._send(400, {"error": "参数校验失败: argparse 拒绝该输入 (%s)" % e})
        except Exception as e:
            return self._send(400, {"error": "参数构建失败: %s" % e})

        # dry-run：仅返回 coze 请求信封
        if options.get("dry_run"):
            try:
                env = BACKEND.preview(test, ns, ctx)
            except Exception as e:
                return self._send(500, {"error": "预览失败: %s" % e})
            return self._send(200, {"dry_run": True, "envelope": env,
                                    "settings_block": session_store.render_settings_block(merged)})

        # 真正计算
        try:
            result = BACKEND.compute(test, ns, ctx)
        except RuntimeError as e:
            return self._send(502, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": "计算失败: %s" % e})

        rd = serialize_result(result)
        if session_id:
            STORE.attach_result_summary(session_id, extract_summary(merged, rd))
        resp = {
            "ok": True,
            "test": test,
            "result": rd,
            "solve_for_power": ctx["solve_for_power"],
            "settings_block": session_store.render_settings_block(merged),
        }
        # 会话线程：附上合并审计（inherited/overridden）+ 当前设定，供前端 diff 展示
        if session_id:
            t = STORE.get(session_id)
            resp["session"] = {
                "id": session_id,
                "settings_block": session_store.render_settings_block(t.current),
                "turns": len(t.turns),
                "audit": {
                    "inherited": (audit or {}).get("inherited", []),
                    "overridden": (audit or {}).get("overridden", []),
                    "missing_required": (audit or {}).get("missing_required", []),
                },
            }
        return self._send(200, resp)

    def _nl(self):
        """自然语言 → 路由（选检验）+ 参数抽取，供前端自动填表。

        对齐技能主路径：先走确定性代码（classify_test 规则）识别检验类型并抽取参数；
        规则完全未命中（test=None）时，再调用本地默认大模型（Ollama / CTSS_NL_ENDPOINT
        可配）兜底识别。大模型不可达或仍识别失败 → 退回规则结果（test=None，由前端提示
        手动选择），不静默错参、不阻断流程。
        """
        body = self._body_json()
        nl = body.get("nl", "")
        if not nl:
            return self._send(400, {"error": "缺少 nl 字段"})
        locale = body.get("locale") or "zh"
        try:
            import classify_test          # noqa
            import param_aliases          # noqa
        except Exception as e:            # pragma: no cover
            return self._send(500, {"error": "NL 模块不可用: %s" % e})

        # ① 先走确定性代码（与技能主路径对齐——规则优先，大模型仅兜底）
        route = classify_test.classify(nl)
        route["engine"] = "rule"
        extracted = {}
        try:
            extracted = param_aliases.extract_parameters(nl, route.get("test")) or {}
        except Exception as e:
            route.setdefault("notes", []).append("参数抽取失败: %s" % e)
        # extract_parameters 返回 {params, side, solve_for_power, needs_llm_fallback, missing, notes}
        # —— 须取其内部 params 子字典；side 已并入 params（最新版）
        params = dict(extracted.get("params") or {})
        if extracted.get("side"):
            params["side"] = extracted["side"]
        # 仅保留前端表单认识的 dest 键（CLI 参数白名单，来自 build_parser 反射）
        params = {k: v for k, v in params.items() if k in CATALOG["params"]}

        # 会话上下文继承：追问类 NL 往往只给参数、不重复检验类型
        # → 继承前端传来的 current_test（用户已选定 / 会话中的检验），避免「未识别检验类型」
        current_test = body.get("current_test")
        if not route.get("test") and current_test and current_test in TEST_NAMES:
            route["test"] = current_test
            route["inherited"] = True

        # 多值参数检测：如「power 0.85 0.9 0.95 都算一下」→ 分别计算多组
        multi = _detect_multi_values(nl)
        if multi:
            route["multi"] = multi

        # 咨询路由闸门：设计/方法学咨询句 → 标记 advisory（前端据此不点火 coze，
        # 与对话 agent 路由闸门对齐：vague/advisory 表述不往外发计算）。
        if _detect_advisory(nl):
            route["advisory"] = True
            route["intent"] = "advisory"

        # 透传参数级信号（对齐 samplesize_power.py 新语义：参数不全时本地向用户追问，
        # 原始 NL 不入 coze；绝不对缺失参数静默补默认）
        route["solve_for_power"] = bool(extracted.get("solve_for_power"))
        if extracted.get("needs_llm_fallback"):
            route["needs_params_fallback"] = True
        if extracted.get("missing"):
            route["params_missing"] = list(extracted["missing"])
        if extracted.get("notes"):
            route.setdefault("notes", []).extend(extracted["notes"])

        # ── 确定性结果优先（与对话模式完全一致：classify_test + param_aliases 为权威路径）──
        # 对话模式里 Agent 用强 LLM 驱动同一套确定性检测器；工作台沿用同一套检测器作为主路径，
        # 规则一旦识别出检验即直接采用 —— **绝不**调用弱本地 LLM 去覆写/纠偏已识别的检验
        # （历史上弱 Ollama 曾把「两组率比较卡方」误判为 ttest_ind 并覆盖正确结果）。
        # 缺参时与对话模式一致：返回结构化缺失清单交由前端追问用户（绝不静默错参 / 弱 LLM 猜测）。
        # LLM 仅作为「规则完全失败（test=None）时的提议」，见下方 ②。
        if route.get("test"):
            return self._send(200, {"route": route, "params": params,
                                    "advisory": bool(route.get("advisory"))})

        # ② 规则未命中（test=None）→ 本地默认大模型兜底识别
        try:
            llm = nl_llm.nl_resolve(nl, locale, TEST_NAMES, CATALOG["params"])
        except Exception:
            llm = None
        if llm and llm.get("route", {}).get("test"):
            # 规则抽到的通用参数（alpha/power 等）保留；大模型补充检验类型与相关参数
            merged = dict(params)
            merged.update(llm["params"])
            return self._send(200, {"route": llm["route"], "params": merged,
                                    "advisory": bool(route.get("advisory"))})

        # ③ 规则与大模型均未识别 → 退回规则结果（test=None），前端提示手动选择
        return self._send(200, {"route": route, "params": params,
                                "advisory": bool(route.get("advisory"))})

    def _export(self):
        """把已算出的结果固化成可离线打开的单文件 HTML 报告。

        复用技能的 canonical render_html_report（与 CLI 报告完全一致），
        避免前端自行拼 HTML 导致与 CLI 报告割裂。

        请求体：{test, result, options?}
          - result  : /api/compute 返回的 result 对象（已序列化的 text/figures/r_code/r_result）
          - options.show_alloc : 是否展示 coze 默认返回的「分配比四图」（默认 False）
        返回：text/html 报告正文（前端以 Blob 触发下载）
        """
        body = self._body_json()
        test = body.get("test")
        result = body.get("result") or {}
        options = body.get("options") or {}
        if not test:
            return self._send(400, {"error": "缺少 test 字段"})
        if not isinstance(result, dict) or not (result.get("text") or result.get("r_result") or result.get("figures")):
            return self._send(400, {"error": "缺少有效 result（请先完成一次计算）"})

        # 重组成 coze 信封（render_html_report 消费结构）
        out = {
            "status": "ok",
            "stats": result.get("r_result"),
            "narrative": result.get("text") or "",
            "figures": result.get("figures") or [],
            "repro": ({"r": result["r_code"]} if result.get("r_code") else None),
            "warnings": result.get("meta", {}).get("warnings") or [],
            "notes": "",
        }
        show_alloc = bool(options.get("show_alloc"))
        try:
            d = tempfile.mkdtemp(prefix="ctss_rpt_")
            path = rendering.render_html_report(out, out_dir=d, test=test,
                                                 show_alloc=show_alloc)
        except Exception as e:
            return self._send(500, {"error": "报告生成失败: %s" % e})
        if not path or not os.path.exists(path):
            return self._send(500, {"error": "报告生成失败：无内容可渲染"})
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
        except OSError as e:
            return self._send(500, {"error": "读取报告失败: %s" % e})
        finally:
            try:
                os.remove(path)
                os.rmdir(d)
            except OSError:
                pass
        fname = "ctss_report_%s.html" % test
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html.encode("utf-8"))))
        self.send_header("Content-Disposition",
                         "attachment; filename=\"%s\"" % fname)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "Content-Disposition")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _bugreport(self):
        """前端 Bug 反馈入口（ct-base §20.3.5）。

        默认提交到 **统一 bug-report coze 端点**（bug_report.send_to_endpoint，
        信封为硬白名单脱敏、仅带 skill/version/test/error_type/description 等元数据，
        不含用户原始数据）；仅当端点不可达时降级到本地 md 兜底（bug_report.save_local_report，
        §20.3.4 / §13.2 作者邮箱）。"""
        body = self._body_json()
        desc = (body.get("desc") or "").strip()
        if not desc:
            return self._send(400, {"error": "请填写问题描述"})
        test = body.get("test") or "unknown"
        locale = body.get("locale") or bug_report._current_locale()
        # 引擎状态：MOCK 演示模式标记（便于作者区分线上/演示环境）
        engine_status = "mock (offline demo)" if os.environ.get("CTSS_COZE_MOCK") else "workbench"
        report = bug_report.build_report(
            skill="ct-samplesize", skill_version=SKILL_VERSION, test=test,
            error_type="error", error_code="", engine_status=engine_status,
            description=desc, locale=locale, attempts=1,
        )
        # ① 默认：提交至统一 coze 端点（action=report）
        res = bug_report.send_to_endpoint(report)
        if res.get("status") == "ok":
            return self._send(200, {
                "ok": True, "channel": "coze",
                "history": res.get("history", ""),
                "note": res.get("note", ""),
            })
        # ② 兜底：端点不可达 → 本地 md（数据不出域，仅作者邮箱可见）
        local_path = None
        try:
            local_path = bug_report.save_local_report(report, outdir=_HERE)
        except Exception:
            local_path = None
        # 额外本地备份（不阻塞主流程；仅作最后安全网，非主通道）
        try:
            append_bugreport({
                "desc": desc, "test": test, "session_id": body.get("session_id"),
                "engine_status": engine_status, "channel": "local-fallback",
            })
        except Exception:
            pass
        return self._send(200, {
            "ok": True, "channel": "local",
            "path": (local_path.split("\n")[0] if local_path else None),
            "note": res.get("note", "coze 端点不可达，已转本地保存"),
        })

    def _preview(self):
        body = self._body_json()
        test = body.get("test")
        params = body.get("params") or {}
        options = body.get("options") or {}
        if not test:
            return self._send(400, {"error": "缺少 test 字段"})
        if test not in TEST_NAMES:
            return self._send(400, {"error": "未知检验类型: %s" % test})
        try:
            ns = build_namespace(test, params)
            ctx = make_ctx(ns, {**options, "dry_run": True})
            env = BACKEND.preview(test, ns, ctx)
        except SystemExit as e:
            return self._send(400, {"error": "参数校验失败: %s" % e})
        except Exception as e:
            return self._send(500, {"error": "预览失败: %s" % e})
        return self._send(200, {"envelope": env})

    def _follow(self, sid):
        body = self._body_json()
        cur = body.get("cur") or {}
        required = body.get("required") or []
        note = body.get("note")
        audit = STORE.follow_up(sid, cur, required, note=note)
        if not audit:
            return self._send(404, {"error": "session not found: %s" % sid})
        return self._send(200, audit)

    def _batch(self):
        """批量计算端点（v5.7 批处理治理：把「逐格串行 N 次」压成「1 次批量」）。

        请求体：{ items: [ {test, params, options} ] }
          - 每项与 /api/compute 同构（test + dest 键值 params + options）；
          - **不创建会话线程**：批量扫描是一次性敏感性分析，不应每格开独立回合
            （否则既污染会话继承、又退化成飞书实证「逐格 54 次」同构问题）。
        返回：{ ok, summary:{count,ok,errors,tests,modes}, items:[ {ok, test?, result?|error?} ] }
          - items 与入参 items 一一对应（含失败项，便于前端逐组定位）。
        """
        body = self._body_json()
        items = body.get("items")
        if not isinstance(items, list) or not items:
            return self._send(400, {"error": "缺少 items 列表"})

        specs = []            # (test, ns, ctx) —— 传给 compute_batch
        valid_idx = []        # 每个有效项在 items 中的原始下标（用于回写对齐）
        per_status = [None] * len(items)   # None=有效；否则 {"ok":False,"error":...}
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                per_status[i] = {"ok": False, "error": "items[%d] 不是对象" % i}
                continue
            test = it.get("test")
            params = it.get("params") or {}
            options = it.get("options") or {}
            if not test or test not in TEST_NAMES:
                per_status[i] = {"ok": False, "error": "未知检验类型: %s" % test}
                continue
            required = TEST_REQUIRED.get(test, [])
            merged = dict(params)
            merged["test"] = test
            # 自动补「有默认值」的 required 字段（与 _compute 一致，仅兜底）
            for k in required:
                if k not in merged and k in CATALOG["params"]:
                    dflt = CATALOG["params"][k]["default"]
                    if dflt is not None:
                        merged[k] = dflt
            try:
                ns = build_namespace(test, merged)
                ctx = make_ctx(ns, options)
            except SystemExit as e:
                per_status[i] = {"ok": False, "error": "参数校验失败: %s" % e}
                continue
            except Exception as e:
                per_status[i] = {"ok": False, "error": "参数构建失败: %s" % e}
                continue
            specs.append((test, ns, ctx))
            valid_idx.append(i)

        if not specs:
            return self._send(400, {
                "error": "无有效计算项",
                "items": [s for s in per_status if s is not None],
            })

        try:
            batch_result = BACKEND.compute_batch(specs)
        except RuntimeError as e:
            return self._send(502, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": "批量计算失败: %s" % e})

        br_items = getattr(batch_result, "items", None) or []
        out = []
        for i in range(len(items)):
            if per_status[i] is not None:
                out.append(per_status[i])
                continue
            pos = valid_idx.index(i)
            br = br_items[pos] if pos < len(br_items) else None
            if br is None:
                out.append({"ok": False, "error": "批量响应缺失该项"})
                continue
            if br.status in ("ok", "warn") and br.result is not None:
                out.append({
                    "ok": True,
                    "test": br.test,
                    "solve_for_power": br.mode == "power",
                    "result": serialize_result(br.result),
                })
            else:
                out.append({"ok": False,
                            "error": getattr(br, "error", "计算失败")})

        summary = {
            "count": len(out),
            "ok": sum(1 for o in out if o.get("ok")),
            "errors": sum(1 for o in out if not o.get("ok")),
            "tests": getattr(batch_result, "tests", []) or [],
            "modes": getattr(batch_result, "modes", []) or [],
        }
        return self._send(200, {"ok": True, "summary": summary, "items": out})


# ──────────────────────────────────────────────────────────────────────────
# 启动
# ──────────────────────────────────────────────────────────────────────────
def _port_free(host, port):
    """预检端口是否空闲——避免静默复用旧实例（旧进程可能是旧版本，会让 /api/schema 返回 404）。"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main():
    # WorkBuddy 发布通道通过 $PORT 注入端口；命令行参数回退
    port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8765))
    # 发布通道（有 PORT 环境变量）绑定 0.0.0.0；本地默认 127.0.0.1
    default_host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    host = os.environ.get("HOST") or (sys.argv[2] if len(sys.argv) > 2 else default_host)

    # 发布通道跳过端口检查（沙箱分配端口保证可用）
    if "PORT" not in os.environ and not _port_free(host, port):
        sys.stderr.write(
            "\n!!! 端口 %d 已被占用 —— 可能已有旧工作台实例在运行\n"
            "!!! （旧版本会令 /api/schema 返回 404，正是你刚遇到的报错）。\n"
            "!!! 解决（二选一）：\n"
            "!!!   1) 换用干净端口：  python server.py 8890\n"
            "!!!   2) 先停掉旧实例（结束占用该端口的 python 进程）：\n"
            "!!!        netstat -ano | findstr :%d\n"
            "!!!        taskkill /PID <上面查到的PID> /F\n"
            "!!! 本次未启动。\n\n" % (port, port)
        )
        sys.exit(1)

    httpd = ThreadingHTTPServer((host, port), Handler)
    auth_hint = "鉴权: 已启用（CTSS_WB_TOKEN）" if os.environ.get("CTSS_WB_TOKEN") else "鉴权: 未设置（公开部署强烈建议设置 CTSS_WB_TOKEN）"
    print("=" * 64)
    print("ct-samplesize 工作台已启动: http://%s:%d/" % (host, port))
    print("  后端: %s | mock=%s" % (BACKEND.__class__.__name__,
                                    bool(os.environ.get("CTSS_COZE_MOCK"))))
    print("  %s" % auth_hint)
    print("  Ctrl+C 退出")
    print("=" * 64)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        httpd.shutdown()


if __name__ == "__main__":
    main()

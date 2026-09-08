#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nl_llm.py — 工作台自然语言识别的「可选 LLM 兜底」客户端（OpenAI 兼容，stdlib-only）。

定位与红线（务必先读）
---------------------
⚠️ **本模块只是「规则完全失败（test=None）时的提议器」，绝不做权威路由。**
工作台的主路径与对话模式完全一致：classify_test + param_aliases 确定性检测器为权威，
规则一旦识别到检验即直接采用（server._nl 不再回退调用本模块去覆写已识别的检验）。
本模块只在「确定性规则完全没命中任何检验」时，被 server._nl 调用一次，用于**提议**一个
检验候选 + 抽取参数；任何失败 → 返回 None → 上层退回让用户手动选（与对话模式 grill-me 一致）。
它对已识别的检验结果**零覆写权**，从根上杜绝「弱 LLM 把 proportion_two 误判成 ttest_ind 并覆盖」。

默认端点（重要更正）
-------------------
- 历史 docstring 称「设 CTSS_NL_ENDPOINT=coze 工作流 /v1/chat/completions 即可与计算端对齐 coze LLM」。
  **该说法不成立**：coze 的 /v1/chat/completions 是带 session_id 的有状态工作流接口，
  非标准 OpenAI 兼容的即调即回 NL 解析端点（直调会报 `session_id is required`），不能作兜底。
- 因此**默认不启用任何 LLM 兜底**：CTSS_NL_ENDPOINT 未设置时 _endpoint() 返回 None，
  nl_resolve 直接返回 None → 上层退回规则结果 / 让用户手动选。这恰好等于对话模式的
  「确定性优先 + 缺失追问」纪律，不会因弱模型拉低质量。
- 若用户确有一个**强** OpenAI 兼容端点（自有部署的强模型，质量可比对话模式的 Agent LLM），
  用 CTSS_NL_ENDPOINT 指向它即可恢复「真·LLM 兜底」；此时本模块才真正参与提议。
  默认本地 Ollama（http://localhost:11434/v1/chat/completions）仅作离线/私有可选，
  且需用户显式设置 CTSS_NL_ENDPOINT 才会启用，不再作为隐式默认。

- 通过白名单约束 system prompt（test / param 列表注入），要求模型只输出受限 JSON，
  从根本上抑制幻觉：test 必须是已知检验之一，params 键必须是已知参数之一。
- 任何失败（端点不可达 / 超时 / 非 JSON / 校验不过 / 模型给出未知 test）→ 返回 None。

安全 / 红线
----------
- 仅 stdlib（urllib / json / re / socket），不引入任何第三方依赖，守住 ct-samplesize stdlib-only 红线。
- localhost 走 ProxyHandler({}) 绕过系统代理（Windows WinError 10061 残代理坑），避免 11434 被代理吞。
- token 取 env(CTSS_NL_TOKEN / CTSS_COZE_TOKEN)；绝不回显明文。
"""
import json
import os
import re
import socket
import urllib.error
import urllib.request


def _endpoint() -> str:
    """NL 大模型端点：仅当显式设置 CTSS_NL_ENDPOINT 才启用 LLM 兜底。

    未设置时返回 None —— nl_resolve 直接返回 None，上层退回确定性结果 / 让用户手动选。
    这是有意设计：coze /run 计算端无 NL 路径、coze /v1/chat/completions 需 session_id 不可用，
    本地 Ollama 又普遍弱于对话模式的 Agent LLM；故默认不拿弱模型拉低质量，
    确定性检测器（与对话模式同源）即为权威路径。
    """
    return os.environ.get("CTSS_NL_ENDPOINT") or ""


def _model() -> str:
    """模型名：默认 qwen3.5:27b（本机 Ollama），可经 CTSS_NL_MODEL 覆盖（如 qwen3.5:9b）。"""
    return os.environ.get("CTSS_NL_MODEL") or "qwen3.5:27b"


def _token() -> str:
    """Bearer token：Ollama 不需要；coze chat 需要。取 env 不回显。"""
    return os.environ.get("CTSS_NL_TOKEN") or os.environ.get("CTSS_COZE_TOKEN") or ""


def _system_prompt(tests, params) -> str:
    tlist = "\n".join("- %s" % t for t in sorted(tests))
    plist = "\n".join("- %s" % p for p in sorted(params))
    return (
        "你是一个临床试验样本量/功效计算的自然语言需求解析器。只做结构化抽取，不做计算。\n\n"
        "可用检验类型（test，必须是以下之一；无法识别则 test=null）：\n%s\n\n"
        "可抽取的参数名（params 的键，必须是以下之一；未提及则不输出）：\n%s\n\n"
        "请从用户需求中识别检验类型、抽取已知参数。\n"
        "输出**严格 JSON**（不要 markdown 代码块、不要任何解释文字）：\n"
        '{"test": "<白名单之一或 null>", "params": {"<参数名>": <数值或字符串>}, '
        '"side": "two"|"one"|null, "confidence": "high"|"medium"|"low", '
        '"missing": ["未明确给出的关键参数名"]}\n\n'
        "注意：\n"
        "- effect 是效应量（如 Cohen's d）；p1/p2 是两组率；ratio 是组间样本量比。\n"
        "- side：用户说『双侧/双尾』→\"two\"，『单侧/单尾』→\"one\"，未说明→null。\n"
        "- alpha 通常用小数（如 0.05）；power/把握度用小数（如 0.8）或百分数（如 80%%→0.8）。\n"
        "- 只输出 JSON。" % (tlist, plist)
    )


def _extract_json(text: str):
    """从 LLM 输出里提取第一个 JSON 对象（容忍 ```json 围栏 / 前后废话）。"""
    if not text:
        return None
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
    if m:
        s = m.group(1)
    else:
        m = re.search(r"\{.*\}", s, re.DOTALL)
        if m:
            s = m.group(0)
    try:
        return json.loads(s)
    except Exception:
        return None


def nl_resolve(nl: str, locale: str, available_tests, available_params):
    """调本地默认大模型解析 NL → 返回 {route, params} 或 None（降级信号）。

    route : {test, confidence, missing, engine:"llm"}
    params: {<白名单参数>: 值, side?}
    """
    tests = set(available_tests or [])
    params_whitelist = set(available_params or [])
    if not _endpoint():
        return None
    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": _system_prompt(tests, params_whitelist)},
            {"role": "user", "content": nl},
        ],
        "temperature": 0.0,
        "max_tokens": 800,
    }
    req = urllib.request.Request(
        _endpoint(),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    tok = _token()
    if tok:
        req.add_header("Authorization", "Bearer %s" % tok)
    try:
        # localhost 绕过系统代理；连接/读取超时偏短，快速降级到规则
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=25) as r:
            body = json.loads(r.read().decode("utf-8"))
        content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        data = _extract_json(content)
        if not isinstance(data, dict):
            return None
        test = data.get("test")
        if test is not None and test not in tests:
            test = None  # 模型幻觉出未知检验 → 置空，交规则/用户手动选
        params = {}
        for k, v in (data.get("params") or {}).items():
            if k in params_whitelist:
                params[k] = v
        if data.get("side") in ("two", "one"):
            params["side"] = data["side"]
        return {
            "route": {
                "test": test,
                "confidence": data.get("confidence") or "medium",
                "missing": data.get("missing") or [],
                "engine": "llm",
            },
            "params": params,
        }
    except Exception:
        # 任何失败（URLError / HTTPError / timeout / ValueError / 解析失败）→ 降级信号
        return None

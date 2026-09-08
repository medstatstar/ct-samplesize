#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_store.py — 工作台「追加提问」会话线程层（ct-samplesize 工作台）

职责
----
1. 维护每条会话线程的「当前分析设定 (current spec)」，跨轮无损继承。
2. 追加提问时，复用 **ct-base/scripts/merge_spec.py** 的确定性合并
   （家族红线 4：跨轮参数继承必须走代码级确定性合并，禁止 LLM 从记忆拼装），
   输出 inherited / overridden / missing_required 审计。
3. 支持会话持久化（sessions.json），便于服务重启后历史回放。

合并语义严格对齐 ct-base/references/continuity.md Mode A §5.1：
   - 每轮 follow-up 只改变化的字段，其余字段 verbatim 继承；
   - merge_spec 是本地确定性合并器（code-fixed, LLM-executed），非脆弱分类器。

本文件在 ct-base 可用时直接 import 其权威副本；若环境未挂载 ct-base，
降级为内嵌的「逐字等价」实现（逻辑与 ct-base 副本一致）并打 warning，
保证工作台自包含、不硬失败。
"""

import os
import sys
import json
import time
import uuid
import threading

# ──────────────────────────────────────────────────────────────────────────
# 1. 确定性合并器：优先用 ct-base 权威副本，否则内嵌等价实现
# ──────────────────────────────────────────────────────────────────────────
def _import_canonical_merge():
    """试着从 ct-base 加载权威 merge(); 失败返回 (None, fallback_fn, note)。"""
    here = os.path.dirname(os.path.abspath(__file__))
    # ct-base 位置：<skills>/ct-base/scripts/merge_spec.py
    # workbench 路径：ct-samplesize/adapters/workbench/  →  上溯三级到 <skills>
    cand = os.path.normpath(os.path.join(here, "..", "..", "..", "ct-base", "scripts"))
    if os.path.isdir(cand) and cand not in sys.path:
        sys.path.insert(0, cand)
    try:
        import merge_spec  # noqa
        return merge_spec.merge, "ct-base/scripts/merge_spec.py"
    except Exception:
        return None, None


def _embedded_merge(prev, cur, required):
    """逐字等价于 ct-base/scripts/merge_spec.py::merge（仅当权威副本不可用时启用）。"""
    merged = dict(prev) if prev else {}
    inherited = []
    overridden = []

    for k, v in (cur or {}).items():
        if k in merged and merged[k] != v:
            overridden.append(k)
        merged[k] = v

    inherited = [k for k in (prev or {}) if k not in (cur or {})]
    missing = [
        k for k in (required or [])
        if k not in merged or (merged.get(k) is None or merged.get(k) == "")
    ]
    return {
        "merged": merged,
        "inherited": inherited,
        "overridden": overridden,
        "missing_required": missing,
    }


_CANON, _CANON_NOTE = _import_canonical_merge()
if _CANON is None:
    _CANON = _embedded_merge
    print("[session_store] WARNING: ct-base merge_spec 不可用，已降级为内嵌等价实现",
          file=sys.stderr)


def merge_spec(prev, cur, required):
    """对外统一入口：确定性合并。始终走权威（或等价）实现。"""
    return _CANON(prev or {}, cur or {}, required or [])


# ──────────────────────────────────────────────────────────────────────────
# 2. 会话线程
# ──────────────────────────────────────────────────────────────────────────
class SessionThread:
    """单条追问线程。current = 下一轮合并时要继承的 prev spec。"""

    def __init__(self, sid, title="未命名会话"):
        self.id = sid
        self.title = title
        self.created_at = time.time()
        self.updated_at = time.time()
        self.current = {}            # 当前继承中的分析设定
        self.last_test = None        # 最近一次锁定的 test（便于 required 推断）
        self.turns = []             # 历史回合（含合并审计 + 结果摘要）

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current": self.current,
            "last_test": self.last_test,
            "turns": self.turns,
        }

    @classmethod
    def from_dict(cls, d):
        t = cls(d["id"], d.get("title", "未命名会话"))
        t.created_at = d.get("created_at", time.time())
        t.updated_at = d.get("updated_at", time.time())
        t.current = d.get("current", {})
        t.last_test = d.get("last_test")
        t.turns = d.get("turns", [])
        return t


def render_settings_block(spec):
    """
    渲染 SKILL.md 规范的「## 当前分析设定：」块，供前端 diff 展示。

    字段顺序对齐家族规范的最小单元：
        {test, effect, alpha, power, solve, side, sd, n, ratio}
    缺失字段用 '—' 占位。
    """
    order = ["test", "effect", "alpha", "power", "solve", "side", "sd", "n", "ratio"]
    # 兜底：spec 中若有不在 order 内的键，也一并带出（保持无损）
    extra = [k for k in spec.keys() if k not in order]
    parts = []
    for k in order + extra:
        v = spec.get(k, "—")
        parts.append("%s=%s" % (k, "—" if v in (None, "", []) else v))
    return " | ".join(parts)


class SessionStore:
    """线程安全的会话仓库，带 JSON 持久化。"""

    def __init__(self, persist_path=None):
        here = os.path.dirname(os.path.abspath(__file__))
        self.persist_path = persist_path or os.path.join(here, "sessions.json")
        self._lock = threading.RLock()
        self._sessions = {}
        self._load()

    # —— 持久化 ——
    def _load(self):
        if not os.path.exists(self.persist_path):
            return
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data.get("sessions", []):
                self._sessions[d["id"]] = SessionThread.from_dict(d)
        except Exception as e:
            print("[session_store] 加载会话失败: %s" % e, file=sys.stderr)

    def _save(self):
        if self.persist_path in (None, ":memory:"):
            return
        try:
            data = {"sessions": [t.to_dict() for t in self._sessions.values()]}
            tmp = self.persist_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.persist_path)
        except Exception as e:
            print("[session_store] 保存会话失败: %s" % e, file=sys.stderr)

    # —— CRUD ——
    def create(self, title=None):
        sid = uuid.uuid4().hex[:12]
        with self._lock:
            t = SessionThread(sid, title or ("会话-%s" % sid[:6]))
            self._sessions[sid] = t
            self._save()
        return t

    def get(self, sid):
        with self._lock:
            return self._sessions.get(sid)

    def list(self):
        with self._lock:
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "updated_at": t.updated_at,
                    "turns": len(t.turns),
                    "test": t.last_test,
                }
                for t in sorted(self._sessions.values(),
                                key=lambda x: x.updated_at, reverse=True)
            ]

    def delete(self, sid):
        with self._lock:
            if sid in self._sessions:
                del self._sessions[sid]
                self._save()
                return True
        return False

    def reset(self, sid):
        """清空线程的当前设定与圆点历史（保留线程本身）。"""
        with self._lock:
            t = self._sessions.get(sid)
            if not t:
                return None
            t.current = {}
            t.last_test = None
            t.turns = []
            t.updated_at = time.time()
            self._save()
            return t

    def attach_result_summary(self, sid, summary):
        """把最近一次计算的结果摘要追加到当前回合（供历史回放）。"""
        with self._lock:
            t = self._sessions.get(sid)
            if not t or not t.turns:
                return
            t.turns[-1]["result_summary"] = summary
            t.updated_at = time.time()
            self._save()

    # —— 核心：确定性追加合并 ——
    def follow_up(self, sid, cur, required=None, note=None, result_summary=None):
        """
        对会话线程做追加提问合并。

        参数
        ----
        sid         : 会话 ID
        cur         : 本轮解析的 partial / full spec（只含变化字段即可）
        required    : 该 test 的必填字段，用于缺失校验
        note        : 本轮人类可读说明（如 "把 power 从 0.8 提到 0.9"）
        result_summary : 若本轮触发了计算，附带结果摘要（用于历史回放）

        返回
        ----
        {
          "session_id", "prev", "cur", "merged",
          "inherited", "overridden", "missing_required",
          "settings_block", "turn_index", "title"
        }
        """
        with self._lock:
            t = self._sessions.get(sid)
            if not t:
                return None

            prev = dict(t.current)
            audit = merge_spec(prev, cur, required or [])

            # 命中 test 时记录，便于前端/服务端推断 required
            if "test" in cur and cur["test"]:
                t.last_test = cur["test"]

            t.current = audit["merged"]
            t.updated_at = time.time()

            turn = {
                "ts": time.time(),
                "prev": prev,
                "cur": dict(cur),
                "merged": audit["merged"],
                "inherited": audit["inherited"],
                "overridden": audit["overridden"],
                "missing_required": audit["missing_required"],
                "note": note,
                "result_summary": result_summary,
            }
            t.turns.append(turn)
            self._save()

            return {
                "session_id": sid,
                "title": t.title,
                "turn_index": len(t.turns),
                "prev": prev,
                "cur": cur,
                "merged": audit["merged"],
                "inherited": audit["inherited"],
                "overridden": audit["overridden"],
                "missing_required": audit["missing_required"],
                "settings_block": render_settings_block(audit["merged"]),
            }


# ──────────────────────────────────────────────────────────────────────────
# 3. 模块自测
# ──────────────────────────────────────────────────────────────────────────
def _self_test():
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "ctss_sessions_selftest.json")
    store = SessionStore(persist_path=tmp)
    t = store.create("测试线程")
    sid = t.id

    # 首轮：锁定 test + 主要参数
    r1 = store.follow_up(
        sid,
        {"test": "ttest_ind", "effect": 0.5, "alpha": 0.05, "power": 0.8, "side": "two", "sd": 1.0},
        required=["test", "effect", "alpha", "power", "side"],
        note="首轮：两组连续型 t 检验",
    )
    assert r1["merged"]["test"] == "ttest_ind", r1
    assert r1["inherited"] == [], r1["inherited"]

    # 二轮：只改 power
    r2 = store.follow_up(sid, {"power": 0.9}, note="把把握度提到 0.9")
    assert r2["merged"]["power"] == 0.9, r2
    assert r2["merged"]["effect"] == 0.5, "effect 应被继承"
    assert "effect" in r2["inherited"], r2["inherited"]
    assert r2["overridden"] == ["power"], r2["overridden"]

    # 三轮：缺必填（构造 missing 校验）
    r3 = store.follow_up(sid, {"test": "proportion_two"},
                         required=["test", "p1", "p2", "alpha", "power"],
                         note="切换到两组率检验（未给 p1/p2）")
    assert "p1" in r3["missing_required"], r3["missing_required"]
    assert "p2" in r3["missing_required"], r3["missing_required"]

    print("✓ session_store 自测通过")
    print("  首轮设定:", r1["settings_block"])
    print("  三轮后设定:", r3["settings_block"])
    print("  继承字段(二轮):", r2["inherited"])
    print("  覆盖字段(二轮):", r2["overridden"])
    print("  缺失必填(三轮):", r3["missing_required"])


if __name__ == "__main__":
    _self_test()

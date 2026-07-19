#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive Clinical Trial Simulator / 自适应临床试验蒙特卡洛仿真器
================================================================

Pure-Python Monte-Carlo engine for adaptive / group-sequential trial designs.
Ported into ct-samplesize from the ClawHub skill `adaptive-trial-simulator`
(aipoch-ai) and re-implemented from scratch to fit this skill's conventions.

Faithfully reproduces the 6 capabilities of the source skill:
  1. Design Simulation          - Monte-Carlo validation of a design
  2. Sample Size Re-estimation  - promising-zone SSR (Cui-Hung-Wang statistic)
  3. Early Stopping Rules       - efficacy / futility boundaries via spending
  4. Type I Error Control       - alpha-spending calibration + H0 verification
  5. Multi-Arm Designs          - drop-the-loser arm selection
  6. Power Optimization         - grid search over sample size / looks

Design types      : group_sequential | adaptive_reestimate | drop_the_loser
Spending functions: obrien_fleming | pocock | power_family (rho configurable)
SSR methods       : promising_zone

100% offline, no shell, no eval, no R. Only numpy / scipy (matplotlib optional
for --visualize). Safe to run directly: it is a numeric computation with no
code-injection surface.

纯 Python 蒙特卡洛引擎，用于自适应 / 成组序贯试验设计。由 ClawHub 技能
`adaptive-trial-simulator` 移植并按本技能规范重写，完整复刻其 6 大功能：
设计仿真、样本量再估计（promising zone / CHW 统计量）、早停边界（
efficacy/futility，基于 alpha spending）、I 类错误控制校验、多臂 drop-the-loser、
以及功效优化。完全离线，无 shell / eval / R，仅依赖 numpy / scipy（--visualize
需 matplotlib）。属纯数值计算，无代码注入面，可直接运行。
"""

import sys
import json
import math
import argparse

import numpy as np
from scipy.stats import norm

from i18n import t


# ═══════════════════════════════════════════════════════════════════════════
# Alpha / beta spending functions  /  alpha、beta 消耗函数
# ═══════════════════════════════════════════════════════════════════════════

SPENDING_FUNCTIONS = ("obrien_fleming", "pocock", "power_family")


def cumulative_spend(t, total, func, rho=3.0):
    """Cumulative error spent by information fraction t in (0, 1].

    obrien_fleming : Lan-DeMets O'Brien-Fleming approximation (conservative early)
    pocock         : Lan-DeMets Pocock approximation (aggressive early)
    power_family   : total * t**rho  (rho=1 ~ Pocock-like, large rho ~ OBF-like)

    到信息比例 t 时累计消耗的错误率。三种族均在 t=1 处精确等于 total。
    """
    t = float(np.clip(t, 1e-9, 1.0))
    if func == "obrien_fleming":
        z = norm.ppf(1.0 - total / 2.0)
        return 2.0 * (1.0 - norm.cdf(z / math.sqrt(t)))
    if func == "pocock":
        return total * math.log(1.0 + (math.e - 1.0) * t)
    if func == "power_family":
        return total * (t ** float(rho))
    raise ValueError("unknown spending function: %r" % (func,))


def _incremental(times, total, func, rho):
    """Per-look incremental error spent (strictly positive)."""
    cum = [cumulative_spend(t, total, func, rho) for t in times]
    inc, prev = [], 0.0
    for c in cum:
        inc.append(max(c - prev, 1e-12))
        prev = c
    return inc


# ═══════════════════════════════════════════════════════════════════════════
# Sequential boundary computation (Armitage-McPherson-Rowe recursion)
# 成组序贯边界数值递推（B-value / 布朗运动尺度）
# ═══════════════════════════════════════════════════════════════════════════

def _make_grid(times, ngrid, span=6.0):
    xmax = span * math.sqrt(times[-1])
    x = np.linspace(-xmax, xmax, ngrid)
    return x, x[1] - x[0], xmax


def efficacy_boundaries(times, alpha, func="obrien_fleming", rho=3.0, ngrid=1200):
    """Upper (efficacy) Z-boundaries under H0 via exact recursion.

    Returns one Z boundary per interim/final look. Reproduces gsDesign-style
    boundaries for OBF / Pocock / power spending (one-sided total alpha).
    在 H0 下用精确递推求每次分析的上侧（efficacy）Z 边界。
    """
    times = [float(t) for t in times]
    K = len(times)
    inc = _incremental(times, alpha, func, rho)
    x, dx, xmax = _make_grid(times, ngrid)

    bounds = []
    # ── first look ──
    v1 = times[0]
    b1 = math.sqrt(v1) * norm.ppf(1.0 - inc[0])
    bounds.append(b1 / math.sqrt(v1))
    f = norm.pdf(x, 0.0, math.sqrt(v1))
    f[x > b1] = 0.0

    for k in range(1, K):
        vk = times[k] - times[k - 1]
        kern = norm.pdf(x[:, None] - x[None, :], 0.0, math.sqrt(vk))
        g = (kern * f[None, :]).sum(axis=1) * dx
        # bisection for boundary b s.t. upper-tail mass == inc[k]
        lo, hi = -xmax, xmax
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if (g[x > mid].sum() * dx) > inc[k]:
                lo = mid
            else:
                hi = mid
        bk = 0.5 * (lo + hi)
        bounds.append(bk / math.sqrt(times[k]))
        f = g.copy()
        f[x > bk] = 0.0
    return bounds


def futility_boundaries(times, beta, drift, func="power_family", rho=2.0, ngrid=1200):
    """Lower (futility) Z-boundaries under H1 (non-binding beta-spending).

    Computed under the alternative drift so that the cumulative probability of
    crossing the lower boundary equals the beta spent. Non-binding: efficacy
    boundaries are computed independently. Only looks < K are applied.
    在 H1 漂移下用 beta-spending 求下侧（futility）Z 边界（非绑定型）。
    """
    times = [float(t) for t in times]
    K = len(times)
    inc = _incremental(times, beta, func, rho)
    x, dx, xmax = _make_grid(times, ngrid)

    bounds = []
    v1 = times[0]
    a1 = drift * v1 + math.sqrt(v1) * norm.ppf(inc[0])
    bounds.append(a1 / math.sqrt(times[0]))
    f = norm.pdf(x, drift * v1, math.sqrt(v1))
    f[x < a1] = 0.0

    for k in range(1, K):
        vk = times[k] - times[k - 1]
        kern = norm.pdf(x[:, None] - x[None, :], drift * vk, math.sqrt(vk))
        g = (kern * f[None, :]).sum(axis=1) * dx
        lo, hi = -xmax, xmax
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if (g[x < mid].sum() * dx) < inc[k]:
                lo = mid
            else:
                hi = mid
        ak = 0.5 * (lo + hi)
        bounds.append(ak / math.sqrt(times[k]))
        f = g.copy()
        f[x < ak] = 0.0
    return bounds


# ═══════════════════════════════════════════════════════════════════════════
# Effect-size / drift helpers  /  效应量与漂移换算
# ═══════════════════════════════════════════════════════════════════════════

def _drift(effect_size, n_per_arm):
    """Non-centrality (drift at t=1) for a two-arm mean comparison.

    E[Z_final] = d * sqrt(n/2) for per-arm n and Cohen's d.
    两组均值比较的最终 Z 非中心参数：d*sqrt(n/2)。
    """
    return float(effect_size) * math.sqrt(n_per_arm / 2.0)


# ═══════════════════════════════════════════════════════════════════════════
# 1 + 3 + 4. Group-sequential design simulation
#            成组序贯设计仿真（含早停 + I 类错误校验）
# ═══════════════════════════════════════════════════════════════════════════

def simulate_group_sequential(effect_size, n_per_arm, interim_looks=2,
                              alpha=0.025, spending="obrien_fleming", rho=3.0,
                              futility=False, beta=0.2, n_simulations=10000,
                              seed=None, times=None):
    rng = np.random.default_rng(seed)
    K = int(interim_looks)
    if times is None:
        times = [(i + 1) / K for i in range(K)]
    times = [float(t) for t in times]

    eff_b = efficacy_boundaries(times, alpha, spending, rho)
    theta = _drift(effect_size, n_per_arm)
    fut_b = futility_boundaries(times, beta, theta, "power_family", 2.0) if futility else None

    dt = np.diff([0.0] + times)
    tarr = np.array(times)

    def _run(drift, n_sim):
        Bcur = np.zeros(n_sim)
        stopped = np.zeros(n_sim, dtype=bool)
        reject = np.zeros(n_sim, dtype=bool)
        stop_look = np.full(n_sim, K, dtype=int)      # 1-indexed
        stop_kind = np.zeros(n_sim, dtype=np.int8)    # 0 none/final-fail, 1 eff, 2 fut
        for k in range(K):
            Bcur = Bcur + rng.normal(drift * dt[k], math.sqrt(dt[k]), n_sim)
            Zk = Bcur / math.sqrt(times[k])
            active = ~stopped
            eff = active & (Zk > eff_b[k])
            reject[eff] = True
            stopped[eff] = True
            stop_look[eff] = k + 1
            stop_kind[eff] = 1
            if fut_b is not None and k < K - 1:
                fut = active & (~eff) & (Zk < fut_b[k])
                stopped[fut] = True
                stop_look[fut] = k + 1
                stop_kind[fut] = 2
        return reject, stop_look, stop_kind

    rej1, look1, kind1 = _run(theta, n_simulations)
    rej0, look0, kind0 = _run(0.0, n_simulations)

    frac1 = tarr[look1 - 1]
    exp_n_per_arm = float((frac1 * n_per_arm).mean())
    early = look1 < K
    return {
        "design": "group_sequential",
        "power": float(rej1.mean()),
        "type_i_error": float(rej0.mean()),
        "expected_sample_size": round(exp_n_per_arm * 2.0, 2),
        "expected_sample_size_per_arm": round(exp_n_per_arm, 2),
        "max_sample_size": int(n_per_arm * 2),
        "early_stop_rate": {
            "efficacy": float((early & (kind1 == 1)).mean()),
            "futility": float((early & (kind1 == 2)).mean()),
        },
        "design_config": {
            "effect_size": effect_size, "n_per_arm": n_per_arm,
            "interim_looks": K, "information_times": [round(t, 4) for t in times],
            "alpha": alpha, "spending_function": spending, "rho": rho,
            "futility": bool(futility), "beta": beta if futility else None,
            "efficacy_boundaries_Z": [round(b, 4) for b in eff_b],
            "futility_boundaries_Z": ([round(b, 4) for b in fut_b] if fut_b else None),
            "n_simulations": n_simulations,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. Sample-size re-estimation (promising zone, Cui-Hung-Wang statistic)
#    样本量再估计（promising zone + CHW 加权统计量，保持 I 类错误）
# ═══════════════════════════════════════════════════════════════════════════

def simulate_adaptive_reestimate(effect_size, n_per_arm, alpha=0.025,
                                 interim_fraction=0.5, cp_min=0.365, cp_max=0.9,
                                 target_cp=0.9, max_inflation=2.0,
                                 n_simulations=10000, seed=None, reestimate_method="promising_zone"):
    """Promising-zone SSR with the Cui-Hung-Wang weighted final statistic.

    Stage 1 uses n1 = interim_fraction * n_per_arm per arm. Conditional power
    (CP) is evaluated on the interim estimate. If CP falls in the promising
    zone [cp_min, cp_max], the second-stage sample size is inflated (capped by
    max_inflation) to reach target_cp. The final decision uses the CHW
    weighted statistic Zw = w1*Z1 + w2*Z2 with fixed pre-planned weights, which
    preserves the type I error regardless of the data-dependent re-estimation.
    """
    if reestimate_method != "promising_zone":
        raise ValueError("only 'promising_zone' is supported, got %r" % reestimate_method)
    rng = np.random.default_rng(seed)
    z_alpha = norm.ppf(1.0 - alpha)

    n1 = max(int(round(interim_fraction * n_per_arm)), 2)
    n2_plan = n_per_arm - n1
    n2_max = int(round(n2_plan * max_inflation))
    # CHW fixed weights based on the ORIGINAL planned information split.
    w1 = math.sqrt(n1 / float(n_per_arm))
    w2 = math.sqrt(1.0 - w1 * w1)

    def _run(true_d, n_sim):
        # stage-1 per-arm mean difference estimate ~ N(d, 2/n1)
        d1 = rng.normal(true_d, math.sqrt(2.0 / n1), n_sim)
        z1 = d1 / math.sqrt(2.0 / n1)
        # conditional power under the interim (current-trend) estimate at planned n
        # CP = 1 - Phi( (z_alpha - Zplan)/... ) ; use planned final info
        theta_hat = np.maximum(d1, 0.0)
        # conditional power assuming the interim trend continues to planned n
        info2_plan = n2_plan / 2.0
        cp = 1.0 - norm.cdf((z_alpha - (w1 * z1 + w2 * (theta_hat * math.sqrt(info2_plan)))) / w2)
        cp = np.clip(cp, 0.0, 1.0)

        promising = (cp >= cp_min) & (cp <= cp_max)
        # target n2 to reach target_cp given interim trend
        with np.errstate(divide="ignore", invalid="ignore"):
            need = ((norm.ppf(target_cp) + z_alpha) / np.maximum(theta_hat, 1e-6)) ** 2 * 2.0
        n2_new = np.where(promising, np.clip(np.round(need), n2_plan, n2_max), n2_plan).astype(int)
        n2_new = np.maximum(n2_new, 1)

        # stage-2 estimate with the (possibly inflated) n2
        d2 = rng.normal(true_d, np.sqrt(2.0 / n2_new), n_sim)
        z2 = d2 / np.sqrt(2.0 / n2_new)
        zw = w1 * z1 + w2 * z2
        reject = zw > z_alpha
        total_n = (n1 + n2_new)  # per arm
        return reject, total_n, promising

    rej1, n1tot, prom1 = _run(effect_size, n_simulations)
    rej0, _n0, _p0 = _run(0.0, n_simulations)
    return {
        "design": "adaptive_reestimate",
        "power": float(rej1.mean()),
        "type_i_error": float(rej0.mean()),
        "expected_sample_size": round(float(n1tot.mean()) * 2.0, 2),
        "expected_sample_size_per_arm": round(float(n1tot.mean()), 2),
        "max_sample_size": int((n1 + n2_max) * 2),
        "prob_sample_size_increase": float(prom1.mean()),
        "design_config": {
            "effect_size": effect_size, "planned_n_per_arm": n_per_arm,
            "n1_per_arm": n1, "n2_planned_per_arm": n2_plan, "n2_max_per_arm": n2_max,
            "interim_fraction": interim_fraction, "alpha": alpha,
            "promising_zone": [cp_min, cp_max], "target_cp": target_cp,
            "max_inflation": max_inflation, "chw_weights": [round(w1, 4), round(w2, 4)],
            "reestimate_method": reestimate_method, "n_simulations": n_simulations,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. Multi-arm drop-the-loser design
#    多臂 drop-the-loser（interim 选臂 + 最终检验，Dunnett/Bonferroni 校正）
# ═══════════════════════════════════════════════════════════════════════════

def simulate_drop_the_loser(effect_sizes, n_per_arm, n_arms=None, alpha=0.025,
                            selection_fraction=0.5, n_simulations=10000, seed=None,
                            correction="dunnett"):
    """Drop-the-loser: at an interim look, keep the best treatment arm vs a
    shared control, drop the rest, and continue the winner to the final analysis.

    effect_sizes: list of Cohen's d for each treatment arm vs control. If a
    scalar is given together with n_arms, all arms share it.
    Multiplicity handled by a Bonferroni (n_arms) or Dunnett-style adjusted
    alpha for the initial selection among arms.
    多臂淘汰劣臂：interim 选出与对照相比最优的处理臂，淘汰其余，赢家进入最终分析。
    """
    rng = np.random.default_rng(seed)
    if np.isscalar(effect_sizes):
        if n_arms is None:
            raise ValueError("provide n_arms when effect_sizes is scalar")
        effects = np.full(int(n_arms), float(effect_sizes))
    else:
        effects = np.asarray(effect_sizes, dtype=float)
    K = len(effects)

    # adjusted alpha for selecting among K arms
    if correction == "bonferroni":
        z_final = norm.ppf(1.0 - alpha / K)
    else:  # dunnett-style approximation (accounts for shared control correlation ~0.5)
        z_final = norm.ppf((1.0 - alpha) ** (1.0 / K))

    f1 = float(selection_fraction)
    n1 = max(int(round(f1 * n_per_arm)), 2)      # interim per-arm n
    info1 = n1 / 2.0
    info_full = n_per_arm / 2.0

    def _run(effs, n_sim):
        # interim Z for each arm vs control
        Z1 = rng.normal(effs[None, :] * math.sqrt(info1), 1.0, size=(n_sim, K))
        winner = np.argmax(Z1, axis=1)
        win_eff = effs[winner]
        win_z1 = Z1[np.arange(n_sim), winner]
        # accumulate additional independent information from n1 -> n_per_arm
        extra_info = info_full - info1
        z_extra = rng.normal(win_eff * math.sqrt(max(extra_info, 0.0)), 1.0, n_sim)
        # combined final Z on full information
        zf = (win_z1 * math.sqrt(info1) + z_extra * math.sqrt(max(extra_info, 0.0))) / math.sqrt(info_full)
        reject = zf > z_final
        # sample size: all K arms + control run to interim, winner + control to final
        n_used = (K + 1) * n1 + 2 * (n_per_arm - n1)
        return reject, winner, n_used

    rej1, win1, n_used = _run(effects, n_simulations)
    rej0, _w0, _n0 = _run(np.zeros(K), n_simulations)
    best_arm = int(np.argmax(effects))
    return {
        "design": "drop_the_loser",
        "power_any": float(rej1.mean()),
        "power_correct_selection": float(((win1 == best_arm) & rej1).mean()),
        "prob_correct_selection": float((win1 == best_arm).mean()),
        "type_i_error": float(rej0.mean()),
        "expected_sample_size": int(n_used),
        "max_sample_size": int((K + 1) * n_per_arm),
        "design_config": {
            "effect_sizes": [round(float(e), 4) for e in effects],
            "n_arms": K, "n_per_arm": n_per_arm, "alpha": alpha,
            "selection_fraction": f1, "correction": correction,
            "adjusted_final_Z": round(float(z_final), 4),
            "n_simulations": n_simulations,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# 6. Power optimization (grid search over sample size)
#    功效优化（对每组样本量做网格搜索，找达到目标功效的最小样本量）
# ═══════════════════════════════════════════════════════════════════════════

def optimize_power(effect_size, target_power=0.9, alpha=0.025, interim_looks=2,
                   spending="obrien_fleming", rho=3.0, futility=False,
                   n_min=10, n_max=1000, step=None, n_simulations=4000, seed=None):
    """Search the smallest per-arm sample size reaching target_power for a
    group-sequential design. Returns the chosen design + a scan trace.
    在成组序贯设计下搜索达到目标功效的最小每组样本量，返回最优设计与扫描轨迹。
    """
    if step is None:
        step = max(int((n_max - n_min) / 40), 1)
    trace = []
    chosen = None
    for n in range(int(n_min), int(n_max) + 1, int(step)):
        res = simulate_group_sequential(
            effect_size, n, interim_looks=interim_looks, alpha=alpha,
            spending=spending, rho=rho, futility=futility,
            n_simulations=n_simulations, seed=seed)
        trace.append({"n_per_arm": n, "power": res["power"],
                      "expected_sample_size": res["expected_sample_size"]})
        if chosen is None and res["power"] >= target_power:
            chosen = res
            chosen["design_config"]["n_per_arm"] = n
            break
    return {
        "design": "power_optimization",
        "target_power": target_power,
        "recommended": (None if chosen is None else {
            "n_per_arm": chosen["design_config"]["n_per_arm"],
            "power": chosen["power"],
            "expected_sample_size": chosen["expected_sample_size"],
            "type_i_error": chosen["type_i_error"],
        }),
        "scan": trace,
        "design_config": {
            "effect_size": effect_size, "alpha": alpha,
            "interim_looks": interim_looks, "spending_function": spending,
            "rho": rho, "futility": bool(futility),
            "n_range": [n_min, n_max], "step": step, "n_simulations": n_simulations,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Visualization (optional matplotlib)  /  可视化（可选 matplotlib）
# ═══════════════════════════════════════════════════════════════════════════

def visualize(result, out_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:   # noqa: BLE001
        return t("error.matplotlib_unavailable", msg=e)

    design = result.get("design")
    fig, ax = plt.subplots(figsize=(8, 5))

    if design == "power_optimization":
        ns = [p["n_per_arm"] for p in result["scan"]]
        pw = [p["power"] for p in result["scan"]]
        ax.plot(ns, pw, "o-", color="#c0392b")
        ax.axhline(result["target_power"], ls="--", color="#7f8c8d",
                   label="target power = %.2f" % result["target_power"])
        ax.set_xlabel("Sample size per arm")
        ax.set_ylabel("Power")
        ax.set_title("Power vs sample size (group sequential)")
        ax.legend()
    else:
        cfg = result.get("design_config", {})
        eb = cfg.get("efficacy_boundaries_Z")
        if eb:
            looks = list(range(1, len(eb) + 1))
            ax.plot(looks, eb, "s-", color="#c0392b", label="efficacy boundary (Z)")
            fb = cfg.get("futility_boundaries_Z")
            if fb:
                ax.plot(looks[:-1], fb[:-1], "^--", color="#2980b9",
                        label="futility boundary (Z)")
            ax.set_xlabel("Interim look")
            ax.set_ylabel("Z boundary")
            ax.set_title("Group-sequential stopping boundaries")
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No boundary data to plot", ha="center")

    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return t("info.png_saved", path=out_path)


# ═══════════════════════════════════════════════════════════════════════════
# Dispatcher + CLI  /  分发器与命令行
# ═══════════════════════════════════════════════════════════════════════════

def run(config):
    """Dispatch a simulation from a plain dict config. Returns a result dict."""
    design = config.get("design", "group_sequential")
    if design == "group_sequential":
        return simulate_group_sequential(
            config["effect_size"], config["n_per_arm"],
            interim_looks=config.get("interim_looks", 2),
            alpha=config.get("alpha", 0.025),
            spending=config.get("spending", "obrien_fleming"),
            rho=config.get("rho", 3.0),
            futility=config.get("futility", False),
            beta=config.get("beta", 0.2),
            n_simulations=config.get("n_simulations", 10000),
            seed=config.get("seed"))
    if design == "adaptive_reestimate":
        return simulate_adaptive_reestimate(
            config["effect_size"], config["n_per_arm"],
            alpha=config.get("alpha", 0.025),
            interim_fraction=config.get("interim_fraction", 0.5),
            target_cp=config.get("target_cp", 0.9),
            max_inflation=config.get("max_inflation", 2.0),
            n_simulations=config.get("n_simulations", 10000),
            reestimate_method=config.get("reestimate_method", "promising_zone"),
            seed=config.get("seed"))
    if design == "drop_the_loser":
        eff = config.get("effect_sizes", config.get("effect_size"))
        return simulate_drop_the_loser(
            eff, config["n_per_arm"], n_arms=config.get("n_arms"),
            alpha=config.get("alpha", 0.025),
            selection_fraction=config.get("selection_fraction", 0.5),
            correction=config.get("correction", "dunnett"),
            n_simulations=config.get("n_simulations", 10000),
            seed=config.get("seed"))
    raise ValueError("unknown design: %r" % (design,))


def _fmt_result(res):
    lines = ["=" * 60, t("header.adaptive_sim"), "=" * 60]
    lines.append(json.dumps(res, indent=2, ensure_ascii=False))
    lines.append("=" * 60)
    return "\n".join(lines)


def build_parser():
    p = argparse.ArgumentParser(
        description="Adaptive clinical trial Monte-Carlo simulator / 自适应临床试验蒙特卡洛仿真器")
    p.add_argument("--design", default="group_sequential",
                   choices=["group_sequential", "adaptive_reestimate", "drop_the_loser"])
    p.add_argument("--n-simulations", type=int, default=10000)
    p.add_argument("--sample-size", type=int, default=100, help="per-arm sample size / 每组样本量")
    p.add_argument("--effect-size", type=float, default=0.3, help="Cohen's d")
    p.add_argument("--effect-sizes", type=str, default=None,
                   help="comma list of per-arm Cohen's d for drop_the_loser, e.g. '0.3,0.4,0.5'")
    p.add_argument("--alpha", type=float, default=0.025, help="one-sided alpha")
    p.add_argument("--power", type=float, default=0.9, help="target power for --optimize")
    # group sequential
    p.add_argument("--interim-looks", type=int, default=2)
    p.add_argument("--spending-function", default="obrien_fleming", choices=list(SPENDING_FUNCTIONS))
    p.add_argument("--rho", type=float, default=3.0, help="power_family shape (rho)")
    p.add_argument("--futility", action="store_true", help="add non-binding futility boundary")
    p.add_argument("--beta", type=float, default=0.2)
    # SSR
    p.add_argument("--reestimate-method", default="promising_zone", choices=["promising_zone"])
    p.add_argument("--interim-fraction", type=float, default=0.5)
    p.add_argument("--target-cp", type=float, default=0.9)
    p.add_argument("--max-inflation", type=float, default=2.0)
    # multi-arm
    p.add_argument("--n-arms", type=int, default=3)
    p.add_argument("--selection-fraction", type=float, default=0.5)
    p.add_argument("--correction", default="dunnett", choices=["dunnett", "bonferroni"])
    # utilities
    p.add_argument("--optimize", action="store_true", help="grid-search min sample size for --power")
    p.add_argument("--n-min", type=int, default=10)
    p.add_argument("--n-max", type=int, default=1000)
    p.add_argument("--visualize", action="store_true")
    p.add_argument("--output", type=str, default=None, help="write result JSON to this path")
    p.add_argument("--png", type=str, default=None, help="visualization PNG path (with --visualize)")
    p.add_argument("--seed", type=int, default=None)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.optimize:
        res = optimize_power(
            args.effect_size, target_power=args.power, alpha=args.alpha,
            interim_looks=args.interim_looks, spending=args.spending_function,
            rho=args.rho, futility=args.futility, n_min=args.n_min,
            n_max=args.n_max, n_simulations=max(args.n_simulations // 2, 1000),
            seed=args.seed)
    elif args.design == "group_sequential":
        res = simulate_group_sequential(
            args.effect_size, args.sample_size, interim_looks=args.interim_looks,
            alpha=args.alpha, spending=args.spending_function, rho=args.rho,
            futility=args.futility, beta=args.beta,
            n_simulations=args.n_simulations, seed=args.seed)
    elif args.design == "adaptive_reestimate":
        res = simulate_adaptive_reestimate(
            args.effect_size, args.sample_size, alpha=args.alpha,
            interim_fraction=args.interim_fraction, target_cp=args.target_cp,
            max_inflation=args.max_inflation, n_simulations=args.n_simulations,
            reestimate_method=args.reestimate_method, seed=args.seed)
    else:  # drop_the_loser
        if args.effect_sizes:
            effs = [float(x) for x in args.effect_sizes.split(",") if x.strip()]
        else:
            effs = args.effect_size
        res = simulate_drop_the_loser(
            effs, args.sample_size, n_arms=args.n_arms, alpha=args.alpha,
            selection_fraction=args.selection_fraction, correction=args.correction,
            n_simulations=args.n_simulations, seed=args.seed)

    print(_fmt_result(res))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(t("info.result_saved", path=args.output))

    if args.visualize:
        import os
        import tempfile
        png = args.png or os.path.join(tempfile.gettempdir(), "adaptive_sim_%s.png" % args.design)
        print(visualize(res, png))

    return res


if __name__ == "__main__":
    main()

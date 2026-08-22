#!/usr/bin/env python3
"""
Clinical Trial Sample Size & Power Calculator — v5.0.2

Architecture (v5):
- Default authoritative engine = remote coze R compute service (CozeBackend).
  Only trial-design params are sent (HTTP POST, no shell, no local R).
- v5 removed the local pure-Python fallback (LocalPythonBackend) and all
  third-party compute deps (statsmodels / numpy / scipy no longer required).
  select_backend() returns ONLY CozeBackend; coze unreachable → error, no fallback.
- Local R backend (LocalRBackend, in adapters/r-assets/) is dev/transition only and is
  NOT shipped in the published package.
- Safe by default: --dry-run previews the exact coze request envelope; coze is
  a stateless compute service, so no local code is ever executed. The legacy
  --yes gate applies only to the optional local-R backend.
- Every user string that reaches server-side R is validated against a strict
  allowlist, so it can NEVER break out of an R string literal.
- Input args validated against strict allowlists regardless of backend.

Test types (49 total):
  Core: ttest_ind, ttest_paired, anova, proportion_one, proportion_two,
        non_inferiority, equivalence, be_tost, mixed_model, roc, poisson,
        bland_altman, cluster, vaccine_efficacy, multiple_endpoints,
        bayesian, dose_escalation
  New in v3.3: win_ratio, must_win, historical_controls, mams,
        conditional_power, ni_survival, superiority_margin, assurance,
        dunnett, mediation, group_sequential, adaptive, survival_exact
  New in v3.5 (PASS-survival): survival_equivalence, survival_superiority,
        cox_covariate, survival_one_sample, competing_risks,
        recurrent_events, survival_historical
  New in v3.6 (PASS Group-Sequential, rpact-backed): group_sequential
        (upgraded to rpact exact two-sample means), gsd_proportion,
        gsd_survival, gsd_hazard, gsd_poisson; real spending functions
        (OF/Pocock/WT/HSD-gamma/Kim-DeMets) + non-binding futility bounds
"""
import argparse, sys, os, io, tempfile, re, json, time
from i18n import t
from compute_backend import select_backend, Result, Figure


# ═════════════════════════════════════════════════════════════════════════════
# 图形产物落盘与展示（coze 可能回传 SVG / HTML / PNG）
# ═════════════════════════════════════════════════════════════════════════════

# ── 输入白名单校验（编排层职责：无论送往 coze 还是本地 R，都先卡死危险字符）──
_SAFE_TOKEN_RE = re.compile(r'^[A-Za-z0-9_\-]+$')
_SAFE_PATH_RE = re.compile(r'^[A-Za-z0-9_.\- /\\:一-鿿]+$')


def _validate_token(name, value):
    """Reject categorical string args that could break out into generated code."""
    if value is None:
        return value
    if not _SAFE_TOKEN_RE.match(value):
        raise ValueError(
            "Invalid %s=%r: only [A-Za-z0-9_-] allowed "
            "(no quotes, semicolons or parentheses)." % (name, value)
        )
    return value


def _validate_path(path):
    """Reject output paths containing characters that could escape a string literal."""
    if path is None:
        return None
    if not _SAFE_PATH_RE.match(path):
        raise ValueError(
            "Unsafe output path %r: only letters, digits, spaces and ._-:/\\ "
            "are allowed (no quotes, semicolons or parentheses)." % path
        )
    return path


_FIG_EXT = {"svg": ".svg", "html": ".html", "png": ".png"}

# ── 渲染计时与超阈值提示（ct-base §19.10，全库统一）──
# 界面浏览器渲染无法在 agent 侧精确计时，用 SVG 体量作代理；超阈值生成 render_hint
RENDER_SVG_THRESHOLD = 30.0       # 本地渲染处理耗时上限（秒）
RENDER_SVG_KB_THRESHOLD = 200.0   # 单图/合计 SVG 体量上限（KB）


def _outputs_dir() -> str:
    """图形落盘目录：优先 CTSS_OUTPUT_DIR，其次当前工作目录下的 outputs/。"""
    d = os.environ.get("CTSS_OUTPUT_DIR") or os.path.join(os.getcwd(), "outputs")
    os.makedirs(d, exist_ok=True)
    return d


def _resolve_figure_mode(explicit=None) -> str:
    """出图模式（ct-base §19.9）：svg_inline 默认；png_file 用 cairosvg 转位图。

    优先级：显式参数 > 环境变量 CTSS_FIGURE_MODE > 默认 svg_inline。
    """
    mode = (explicit or os.environ.get("CTSS_FIGURE_MODE") or "svg_inline").lower()
    return mode if mode in ("svg_inline", "png_file") else "svg_inline"


def render_figures(figures, test: str, figure_mode=None):
    """把后端回传的图形写入磁盘，并打印标记供宿主渲染。

    标记格式（宿主 agent 据此调用可视化 / 文件展示能力）：
        __FIGURE__ <format> <abs_path> caption="..."
        __SVG_WIDGET__ <html fragment>   # SVG 图：ct-base §19 内联渲染（宿主直接内嵌对话流）
        __RENDER_HINT__ <text>           # 超阈值提醒（ct-base §19.10），agent 必须在回复中体现

    出图模式（figure_mode，ct-base §19.9）：
        - svg_inline（默认）：__SVG_WIDGET__ 内联 + 落盘 .svg
        - png_file：cairosvg 转 PNG 落盘，emit __FIGURE__ png（不内联 SVG；需 cairosvg，
          未安装时优雅降级回 svg_inline 并提示）

    渲染计时与超阈值提示（ct-base §19.10）：
        - render_elapsed_seconds：本地渲染阶段耗时（拿到 SVG → widget/PNG 就绪）
        - render_svg_kb：所有 SVG 字节合计（KB），界面渲染无法精确计时，用此作代理
        - 任一超阈值（>30s / >200KB）生成 __RENDER_HINT__，建议切换 png_file
    """
    if not figures:
        return
    outdir = _outputs_dir()
    mode = _resolve_figure_mode(figure_mode)
    svg_figs = []
    _svg_paths = []
    _svg_kb = 0.0
    _t0 = time.time()
    for i, fig in enumerate(figures, 1):
        fmt = (fig.format or "svg").lower()
        ext = _FIG_EXT.get(fmt, ".txt")
        path = os.path.join(outdir, "ctss_%s_%d%s" % (test, i, ext))
        content = fig.content or ""
        if fmt == "png" and not content.lstrip().startswith("<"):
            import base64
            with open(path, "wb") as f:
                f.write(base64.b64decode(content))
        else:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(content)
        if fmt == "svg":
            svg_figs.append({"svg": content, "type": fig.caption or "ct-samplesize 图"})
            _svg_paths.append(path)
            _svg_kb += len(content.encode("utf-8")) / 1024.0
        print('__FIGURE__ %s %s caption="%s"' % (fmt, path, (fig.caption or "").replace('"', "'")))
    # ct-base §19：SVG 内联渲染（复用统一 adapters/rendering.py 管线）
    if svg_figs:
        try:
            _skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            _adapters_dir = os.path.join(_skill_root, "adapters")
            for _p in (_skill_root, _adapters_dir):
                if _p not in sys.path:
                    sys.path.insert(0, _p)
            from rendering import build_figure_widget, svg_to_png  # type: ignore  # adapters/rendering.py

            if mode == "png_file":
                # 本地 cairosvg 转 PNG（同一处理链：strip clip → fix xml → bbox → viewBox → 光栅化）
                for j, f in enumerate(svg_figs, 1):
                    try:
                        png_path = os.path.join(outdir, "ctss_%s_%d.png" % (test, j))
                        svg_to_png(f["svg"], png_path, scale=2.0)
                        print('__FIGURE__ png %s caption="%s"' % (png_path, (f.get("type") or "").replace('"', "'")))
                    except Exception as e:  # noqa: BLE001 - cairosvg 缺失/失败 → 优雅降级
                        print("# png_file 转换失败，降级 svg_inline: %s" % e)
                        mode = "svg_inline"
                        break
            if mode == "svg_inline":
                titles = [f.get("type") or "图 %d" % (j + 1) for j, f in enumerate(svg_figs)]
                html = build_figure_widget(svg_figs, titles)
                print("__SVG_WIDGET__ " + html)
                # SVG 无法内联预览时的降级指引（2026-08-20 用户反馈修订：双语——中文用户 + 英文研究者）
                if _svg_paths:
                    print("# 若界面无法直接预览内联 SVG：请在回复中用自然语言提示词引导用户切换图片格式"
                          "（中文用户：『图形无法预览，请改用 PNG 图片格式重新出图』/『把图转成 PNG 文件』；"
                          "English users: \"The figure can't be previewed, please re-render it as a PNG "
                          "image\" / \"Convert the figure to PNG\"）。技能将自动以 PNG 位图重新输出"
                          "（等价 --figure-mode png_file，本地 cairosvg 转换）。"
                          "SVG 源文件可直接打开查看: %s" % ", ".join(_svg_paths))
        except Exception as e:  # noqa: BLE001 - 渲染失败不阻断主流程
            print("# __SVG_WIDGET__ 生成失败: %s" % e)

    # ── 渲染计时与超阈值提示（ct-base §19.10）──
    _elapsed = round(time.time() - _t0, 3)
    _hint = None
    if mode == "svg_inline":
        reasons = []
        if _elapsed > RENDER_SVG_THRESHOLD:
            reasons.append("本地渲染处理耗时 %.0fs（> %.0fs 阈值）" % (_elapsed, RENDER_SVG_THRESHOLD))
        if _svg_kb > RENDER_SVG_KB_THRESHOLD:
            reasons.append("SVG 体量 %.0fKB（> %.0fKB，界面渲染/滚动可能明显变慢）" % (_svg_kb, RENDER_SVG_KB_THRESHOLD))
        if reasons:
            _hint = "；".join(reasons) + "。可切换图片文件模式（figure_mode='png_file' / 环境变量 CTSS_FIGURE_MODE=png_file）：本地 cairosvg 转 PNG，界面渲染更快、不占上下文（但变位图）。"
            print("__RENDER_HINT__ " + _hint)
    # 诊断信息（不参与提示，仅供排查）
    print("# render_elapsed_seconds=%.3f render_svg_kb=%.1f figure_mode=%s" % (_elapsed, _svg_kb, mode))


def _curve_svg_from_stats(stats: dict, test: str, target_power: float = None) -> str:
    """coze 端无图时（svglite/cairo 缺失），用曲线数值 stats{x,y,series} 纯 Python 生成 SVG。

    对齐 ct-base §19 内联渲染：700x500、网格线、多系列折线 + 图例、动态轴标签。
    仅标准库，无第三方依赖。
    ★ Power 参考线（2026-08-20）：当 y 轴语义为 Power 且传入 target_power 时，绘制
    红色虚线参考线（与 coze 权威版 svglite 一致），坐标用与数据点相同的 sy() 映射——
    保证参考线、刻度、数据点三者在同一坐标系统内，杜绝错位。
    """
    xs = stats.get("x") or []
    ys = stats.get("y") or []
    series = stats.get("series") or ["curve"]
    if not xs or not ys or len(xs) != len(ys):
        return ""
    xs = [float(v) for v in xs]
    ys = [float(v) for v in ys]
    # 轴语义启发式：x 全在 [0,1] 且 y 远超 1 → x=目标功效、y=样本量；否则 x=样本量、y=功效
    x_is_power = all(0.0 <= v <= 1.0 for v in xs) and max(ys) > 1.0
    xlab = "Power (target)" if x_is_power else "N"
    ylab = "N" if x_is_power else "Power"
    W, H, PAD_L, PAD_R, PAD_T, PAD_B = 700, 500, 70, 30, 30, 55
    PW, PH = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin:
        xmax = xmin + 1
    if ymax == ymin:
        ymax = ymin + 1
    ymin, ymax = ymin - (ymax - ymin) * 0.05, ymax + (ymax - ymin) * 0.05

    # ★ Power 参考线判定：y 轴语义为 Power（非 x_is_power）且 target_power 在 y 范围内
    ref_power = None
    if not x_is_power and target_power is not None:
        tp = float(target_power)
        if ymin - 1e-9 <= tp <= ymax + 1e-9:
            ref_power = tp

    def sx(v):
        return PAD_L + (v - xmin) / (xmax - xmin) * PW

    def sy(v):
        return PAD_T + (ymax - v) / (ymax - ymin) * PH

    colors = ["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#d35400", "#16a085"]
    # 系列分组（series 与点一一对应；若 series 为标量则整条单系列）
    groups = {}
    for i in range(len(xs)):
        s = str(series[i] if isinstance(series, list) and i < len(series) else (series if not isinstance(series, list) else "curve"))
        groups.setdefault(s, []).append(i)
    paths = []
    legend = []
    for j, (name, idxs) in enumerate(groups.items()):
        col = colors[j % len(colors)]
        pts = " ".join("%.1f,%.1f" % (sx(xs[i]), sy(ys[i])) for i in idxs)
        paths.append(
            '<polyline points="%s" fill="none" stroke="%s" stroke-width="2" '
            'stroke-linejoin="round" stroke-linecap="round"/>' % (pts, col))
        cx, cy = sx(xs[idxs[-1]]), sy(ys[idxs[-1]])
        legend.append(
            '<rect x="%.1f" y="%.1f" width="14" height="4" fill="%s"/>'
            '<text x="%.1f" y="%.1f" font-size="11" fill="#333">%s</text>'
            % (cx + 8, cy - 2, col, cx + 26, cy + 3, name))
    grid = []
    for g in range(5):
        gy = PAD_T + PH * g / 4
        grid.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e0e0e0" stroke-width="1"/>'
                    % (PAD_L, gy, W - PAD_R, gy))
        grid.append('<text x="%d" y="%.1f" font-size="10" fill="#888" text-anchor="end">%.2f</text>'
                    % (PAD_L - 6, gy + 3, ymax - (ymax - ymin) * g / 4))
        gx = PAD_L + PW * g / 4
        grid.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#e0e0e0" stroke-width="1"/>'
                    % (gx, PAD_T, gx, H - PAD_B))
        grid.append('<text x="%.1f" y="%d" font-size="10" fill="#888" text-anchor="middle">%.2f</text>'
                    % (gx, H - PAD_B + 14, xmin + (xmax - xmin) * g / 4))
    ref = ""
    if ref_power is not None:
        ry = sy(ref_power)
        ref = (
            '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#c0392b" '
            'stroke-width="1.2" stroke-dasharray="6,4"/>' % (PAD_L, ry, W - PAD_R, ry)
            + '<text x="%d" y="%.1f" font-size="10" fill="#c0392b" text-anchor="end" '
              'font-weight="bold">power = %s</text>' % (W - PAD_R, ry - 4, format(ref_power, "g"))
        )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d">' % (W, H, W, H)
        + '<rect width="100%%" height="100%%" fill="#ffffff"/>'
        + "".join(grid)
        + ref
        + '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999" stroke-width="1"/>'
          % (PAD_L, H - PAD_B, W - PAD_R, H - PAD_B)
        + '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#999" stroke-width="1"/>'
          % (PAD_L, PAD_T, PAD_L, H - PAD_B)
        + "".join(paths)
        + "".join(legend)
        + '<text x="%d" y="%d" font-size="13" fill="#333" font-weight="bold">Curve: %s</text>'
          % (PAD_L, PAD_T - 8, test)
        + '<text x="%d" y="%d" font-size="12" fill="#555" text-anchor="middle">%s</text>'
          % (PAD_L + PW / 2, H - 12, xlab)
        + '<text x="18" y="%d" font-size="12" fill="#555" text-anchor="middle" '
          'transform="rotate(-90 18 %d)">%s</text>'
          % (PAD_T + PH / 2, PAD_T + PH / 2, ylab)
        + "</svg>"
    )
    return svg


def render_curve_fallback(meta: dict, test: str, target_power: float = None):
    """coze 端无图但返回曲线数值时，本地生成 SVG 并输出内联标记（ct-base §19）。

    target_power：Power 参考线目标值（默认 None 不画；reverse 场景传 0.8 或用户 --power）。
    """
    stats = (meta or {}).get("stats") if isinstance(meta, dict) else None
    if not isinstance(stats, dict):
        stats = meta if isinstance(meta, dict) and ("x" in meta or "series" in meta) else None
    if not stats:
        return
    xs = stats.get("x")
    ys = stats.get("y")
    if not xs or not ys:
        return
    svg = _curve_svg_from_stats(stats, test, target_power=target_power)
    if not svg:
        return
    outdir = _outputs_dir()
    path = os.path.join(outdir, "ctss_%s_curve.svg" % test)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print('__FIGURE__ svg %s caption="Curve %s"' % (path, test))
    try:
        _skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _adapters_dir = os.path.join(_skill_root, "adapters")
        for _p in (_skill_root, _adapters_dir):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        from rendering import build_figure_widget  # type: ignore  # adapters/rendering.py
        html = build_figure_widget([{"svg": svg, "type": "Curve %s" % test}],
                                   ["Curve %s" % test])
        print("__SVG_WIDGET__ " + html)
        # SVG 无法内联预览时的降级指引（2026-08-20 用户反馈修订：双语——中文用户 + 英文研究者）
        print("# 若界面无法直接预览内联 SVG：请在回复中用自然语言提示词引导用户切换图片格式"
              "（中文用户：『图形无法预览，请改用 PNG 图片格式重新出图』/『把图转成 PNG 文件』；"
              "English users: \"The figure can't be previewed, please re-render it as a PNG "
              "image\" / \"Convert the figure to PNG\"）。技能将自动以 PNG 位图重新输出"
              "（等价 --figure-mode png_file，本地 cairosvg 转换）。"
              "SVG 源文件可直接打开查看: %s" % path)
    except Exception as e:  # noqa: BLE001
        print("# __SVG_WIDGET__ 生成失败: %s" % e)


def build_parser():
    p = argparse.ArgumentParser(description="Clinical Trial Sample Size Calculator v4.0.1")
    p.add_argument("--test", required=False, default=None,
        choices=["ttest_ind","ttest_paired","ttest_one","anova","proportion_one","proportion_two",
                 "proportion_paired","odds_ratio","risk_ratio",
                 "non_inferiority","survival","mixed_model","roc","poisson",
                 "bland_altman","equivalence","be_tost","cluster",
                 "vaccine_efficacy","multiple_endpoints","bayesian","dose_escalation",
                 "win_ratio","must_win","historical_controls","mams",
                 "conditional_power","ni_survival","superiority_margin","assurance",
                 "dunnett","mediation","group_sequential","gsd_proportion","gsd_survival","gsd_hazard","gsd_poisson","gsd_survival_sim","gsd_hazard_sim","adaptive","survival_exact",
                 "survival_equivalence","survival_superiority","cox_covariate",
                 "survival_one_sample","competing_risks","recurrent_events",
                 "survival_historical",
                 "adaptive_simulate"])
    p.add_argument("--yes", "-y", action="store_true",
                   help="显式确认执行 R 代码（默认 dry-run 安全预览，仅展示代码、不执行）")
    p.add_argument("--dry-run", action="store_true",
                   help="安全预览：仅生成并展示 R 代码、不执行（默认即此模式）")
    p.add_argument("--show-code", action="store_true", default=False,
                   help="执行并展示生成的 R 代码（默认不展示，仅按需提供）")
    # ── Common ──
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8, help="目标检验效能 (与 --nobs 互斥)")
    p.add_argument("--nobs", type=int, default=None, help="给定样本量求效能 (与 --power 互斥)")
    # ── t-test / ANOVA ──
    p.add_argument("--effect", type=float)
    p.add_argument("--k_groups", type=int, default=2)
    p.add_argument("--side", choices=["one", "two"], default="two",
                   help="检验方向: one=单侧, two=双侧(默认)")
    p.add_argument("--sd", type=float, default=None,
                   help="标准差。提供时 --effect 视为原始均差(Δ), 自动折算 Cohen's d = effect/sd; 否则 --effect 直接作为 d")
    # ── Proportion ──
    p.add_argument("--p1", type=float, default=0.7,
                   help="gsd_proportion 治疗组比例 (difference 模式必填, 默认 0.7)")
    p.add_argument("--p2", type=float, default=0.5,
                   help="gsd_proportion 对照组比例 (difference 模式必填, 默认 0.5)")
    # ── Non-inferiority / Equivalence ──
    p.add_argument("--margin", type=float)
    # ── Survival ──
    p.add_argument("--hazard_ratio", "--hr", type=float)
    # ── Mixed model ──
    p.add_argument("--effect_name", type=str)
    p.add_argument("--varcorr", type=float, default=0.5)
    p.add_argument("--sigma", type=float, default=1.0)
    p.add_argument("--nsim", type=int, default=500)
    # ── ROC ──
    p.add_argument("--auc0", type=float, default=0.5)
    p.add_argument("--auc1", type=float)
    # ── Poisson ──
    p.add_argument("--lambda1", type=float)
    p.add_argument("--lambda2", type=float)
    p.add_argument("--t1", type=float, default=1.0)
    p.add_argument("--t2", type=float, default=1.0)
    # ── Cluster ──
    p.add_argument("--icc", type=float)
    p.add_argument("--m", type=float)
    p.add_argument("--n_indiv", type=float)
    # ── Bland-Altman ──
    p.add_argument("--sd_diff", type=float)
    p.add_argument("--w", type=float)
    # ── Bioequivalence ──
    p.add_argument("--theta0", type=float, default=0.95)
    p.add_argument("--theta1", type=float, default=None,
                   help="BE 等效下界（默认 0.8；与 --theta2 同给；或单给 --margin 自动 1/margin）")
    p.add_argument("--theta2", type=float, default=None,
                   help="BE 等效上界（默认 1.25；与 --theta1 同给；或单给 --margin 自动 margin）")
    p.add_argument("--cv", type=float, default=0.25)
    p.add_argument("--design", type=str, default="2x2")
    # ── Vaccine, Bayesian, multiple endpoints, dose escalation ──
    p.add_argument("--ve_control", type=float, default=0.02)
    p.add_argument("--ve_treatment", type=float, default=0.005)
    p.add_argument("--prior_a0", type=float, default=0.5)
    p.add_argument("--prob_control", type=float, default=0.3)
    p.add_argument("--prob_treatment", type=float, default=0.15)
    p.add_argument("--correlation", type=float, default=0.5)
    p.add_argument("--n_doses", type=int, default=5)
    p.add_argument("--target_dlt", type=float, default=0.33)

    # ═══ NEW v3.3 arguments ═══
    # Win-Ratio
    p.add_argument("--win_ratio_theta", type=float, default=1.5)
    p.add_argument("--n_sim_initial", type=int, default=100)
    p.add_argument("--se_approx", type=float, default=0.0625)
    p.add_argument("--n_sim", type=int, default=1000)
    # Must-Win / Co-Primary
    p.add_argument("--n_endpoints_must", type=int, default=2)
    p.add_argument("--effect_must", type=float, default=0.3)
    p.add_argument("--correlation_must", type=float, default=0.5)
    # Historical Controls
    p.add_argument("--p_control_current", type=float, default=0.3)
    p.add_argument("--historical_response", type=int, default=15)
    p.add_argument("--historical_n", type=int, default=100)
    p.add_argument("--a0_borrowing", type=float, default=0.5)
    # MAMS
    p.add_argument("--n_arms_mams", type=int, default=3)
    p.add_argument("--n_stages_mams", type=int, default=2)
    p.add_argument("--delta_effect", type=float, default=0.3)
    # Conditional Power / SSR
    p.add_argument("--timing", type=float, default=0.5)
    p.add_argument("--observed_effect", type=float, default=0.2)
    p.add_argument("--planned_effect", type=float, default=0.3)
    p.add_argument("--n_completed", type=int, default=100)
    p.add_argument("--n_planned", type=int, default=200)
    # NI Survival
    p.add_argument("--ni_margin_surv", type=float, default=1.25)
    p.add_argument("--hr_expected", type=float, default=1.0)
    p.add_argument("--accrual_time", type=float, default=12)
    p.add_argument("--followup_time", type=float, default=12)
    p.add_argument("--dropout_rate", type=float, default=0.05)
    p.add_argument("--event_rate", type=float, default=0)
    # Superiority Margin
    p.add_argument("--sup_margin", type=float, default=0.05)
    p.add_argument("--sigma_ratio", type=float, default=1.0)
    p.add_argument("--p_control_sup", type=float, default=0.3)
    p.add_argument("--delta_sup", type=float, default=0.15)
    # Assurance
    p.add_argument("--n_sim_assurance", type=int, default=5000)
    # 2026-08-20 统一为先验 Beta(2,2)：默认 None 不发送，R 端 %||% 2 生效（原 CLI 3/7 覆盖了 R 端默认）
    p.add_argument("--shape1_trt", type=float, default=None)
    p.add_argument("--shape2_trt", type=float, default=None)
    p.add_argument("--shape1_ctrl", type=float, default=None)
    p.add_argument("--shape2_ctrl", type=float, default=None)
    p.add_argument("--n_assurance", type=int, default=100)
    # 2026-08-20 修复：默认 0.0 会被 build_params 发送并覆盖 R 端 %||% 0.05 → margin=0 计算错误；
    # 改为 None 不发送，R 端回落 0.05（另有 <=0 防御）
    p.add_argument("--margin_assurance", type=float, default=None)
    # Dunnett
    p.add_argument("--n_groups_dunnett", type=int, default=3)
    p.add_argument("--n_control_dunnett", type=int, default=50)
    p.add_argument("--effect_dunnett", type=float, default=0.4)
    # Mediation
    p.add_argument("--a_path", type=float, default=0.3)
    p.add_argument("--b_path", type=float, default=0.3)
    p.add_argument("--sigma2_m", type=float, default=1.0)
    p.add_argument("--sigma2_y", type=float, default=1.0)
    p.add_argument("--cprime", type=float, default=0.0)
    p.add_argument("--n_sim_mediation", type=int, default=1000)
    # Group Sequential
    p.add_argument("--n_interim", type=int, default=1,
                   help="中期分析次数 (k-1)；总分析次数 kMax = n_interim + 1")
    p.add_argument("--effect_gs", type=float, default=0.4,
                   help="group_sequential 的标准化效应量 (Cohen's d)")
    p.add_argument("--spending_func", type=str, default="OF",
                   choices=["OF", "Pocock", "WT", "HSD", "KimDeMets"],
                   help="alpha 消耗函数: OF=O'Brien-Fleming, Pocock, WT=Wang-Tsiatis, "
                        "HSD=Hwang-Shih-DeCani(gamma, 经 --rho), KimDeMets(asOF)")
    # Adaptive
    p.add_argument("--n_stages_adapt", type=int, default=2)
    p.add_argument("--effect_adaptive", type=float, default=0.4)
    p.add_argument("--adaptive_type", type=str, default="SSR")
    # Survival Exact
    p.add_argument("--alpha_exact", type=float, default=0.05)
    p.add_argument("--power_exact", type=float, default=0.8)
    p.add_argument("--hr_exact", type=float, default=0.75)
    p.add_argument("--accrual_exact", type=float, default=12)
    p.add_argument("--followup_exact", type=float, default=12)
    p.add_argument("--dropout_exact", type=float, default=0.05)
    p.add_argument("--event_rate_exact", type=float, default=0.3)
    p.add_argument("--n_stages_exact", type=int, default=1)
    # ═══ NEW v3.5: PASS-survival extensions (7) ═══
    # Survival Equivalence (TOST on HR)
    p.add_argument("--eq_margin_surv", type=float, default=1.25)
    # Survival Superiority by a margin (HR)
    p.add_argument("--sup_margin_surv", type=float, default=0.8)
    p.add_argument("--sup_hr", type=float, default=0.67)
    # Cox covariate power (Vittinghoff)
    p.add_argument("--cox_hr", type=float, default=2.0)
    p.add_argument("--cox_r2", type=float, default=0.3)
    p.add_argument("--cox_prev", type=float, default=0.5)
    p.add_argument("--cox_event_prop", type=float, default=0.3)
    # One-sample exponential
    p.add_argument("--median0", type=float, default=12.0)
    p.add_argument("--median1", type=float, default=18.0)
    # Competing risks (cumulative incidence)
    p.add_argument("--ci_control", type=float, default=0.2)
    p.add_argument("--ci_treatment", type=float, default=0.1)
    # Recurrent events (Andersen-Gill)
    p.add_argument("--rate_control", type=float, default=1.0)
    p.add_argument("--rate_ratio", type=float, default=0.6)
    p.add_argument("--recur_followup", type=float, default=2.0)
    # Historical control log-rank
    p.add_argument("--new_median", type=float, default=18.0)
    p.add_argument("--hist_n", type=float, default=100.0)
    # ═══ NEW v3.6: PASS Group-Sequential extensions (rpact-backed) ═══
    # Two proportions (difference / ratio / odds-ratio)
    p.add_argument("--gs_proportion_metric", type=str, default="difference",
                   choices=["difference", "ratio", "or"],
                   help="gsd_proportion 的效应度量: difference(默认)/ratio/or")
    p.add_argument("--gs_ratio", type=float, default=0.8,
                   help="gsd_proportion ratio 模式: 治疗组比例 = 对照组 × ratio")
    p.add_argument("--gs_or", type=float, default=0.5,
                   help="gsd_proportion OR 模式: 治疗组比值比")
    # Two survival / hazard-rate (control median -> lambda2)
    p.add_argument("--gs_median_control", type=float, default=12.0,
                   help="gsd_survival/gsd_hazard 对照中位生存(月), 推导 lambda2")
    # Two Poisson rates
    p.add_argument("--gs_rate1", type=float, default=0.6,
                   help="gsd_poisson 治疗组发生率 (lambda1, /人年)")
    p.add_argument("--gs_rate2", type=float, default=1.0,
                   help="gsd_poisson 对照组发生率 (lambda2, /人年)")
    p.add_argument("--gs_poisson_time", type=float, default=2.0,
                   help="gsd_poisson 每人随访时间(年)")
    # ── Adaptive Monte-Carlo simulator (test=adaptive_simulate) ──
    # 纯 Python 蒙特卡洛自适应/成组序贯仿真器 (无 R, 无 shell, 直接运行)
    p.add_argument("--sim_design", type=str, default="group_sequential",
                   choices=["group_sequential", "adaptive_reestimate", "drop_the_loser"],
                   help="仿真设计类型 / simulation design")
    p.add_argument("--n_simulations", type=int, default=10000,
                   help="蒙特卡洛重复次数 / Monte-Carlo replications")
    p.add_argument("--sim_n", type=int, default=100,
                   help="每组样本量 (仿真用) / per-arm sample size for simulation")
    p.add_argument("--effect_size", type=float, default=0.3,
                   help="Cohen's d (仿真效应量)")
    p.add_argument("--effect_sizes", type=str, default=None,
                   help="drop_the_loser 各臂 d 逗号列表, 如 '0.2,0.35,0.5'")
    p.add_argument("--interim_looks", type=int, default=2,
                   help="分析次数 (含最终) / number of looks incl. final")
    p.add_argument("--spending_function", type=str, default="obrien_fleming",
                   choices=["obrien_fleming", "pocock", "power_family"],
                   help="alpha 消耗函数 / alpha spending function")
    p.add_argument("--rho", type=float, default=3.0,
                   help="HSD / Kim-DeMets 消耗函数的 gammaA (Hwang-Shih-DeCani γ, 默认 3.0)")
    p.add_argument("--wt_delta", type=float, default=0.25,
                   help="Wang-Tsiatis 参数 Δ (仅 --spending_func WT 生效, 默认 0.25)")
    p.add_argument("--futility", action="store_true", help="加入非绑定 futility 边界")
    p.add_argument("--beta", type=float, default=0.2, help="futility beta-spending")
    p.add_argument("--reestimate_method", type=str, default="promising_zone",
                   choices=["promising_zone"], help="样本量再估计方法")
    p.add_argument("--interim_fraction", type=float, default=0.5,
                   help="SSR/选臂 interim 信息比例")
    p.add_argument("--target_cp", type=float, default=0.9, help="SSR 目标条件功效")
    p.add_argument("--max_inflation", type=float, default=2.0, help="SSR 二阶段样本量上限倍数")
    p.add_argument("--n_arms", type=int, default=3, help="drop_the_loser 处理臂数")
    p.add_argument("--selection_fraction", type=float, default=0.5, help="选臂 interim 比例")
    p.add_argument("--correction", type=str, default="dunnett",
                   choices=["dunnett", "bonferroni"], help="多臂多重性校正")
    p.add_argument("--optimize", action="store_true",
                   help="网格搜索达到 --power 的最小每组样本量")
    p.add_argument("--n_min", type=int, default=10, help="--optimize 样本量下界")
    p.add_argument("--n_max", type=int, default=1000, help="--optimize 样本量上界")
    p.add_argument("--visualize", action="store_true", help="生成仿真结果 PNG")
    p.add_argument("--sim_output", type=str, default=None, help="仿真结果 JSON 输出路径")
    p.add_argument("--sim_seed", type=int, default=None, help="随机种子")
    # ── Curve mode (power / sample-size curves) ──
    p.add_argument("--n_seq", type=str, default=None,
                   help="样本量序列: 显式 '20,40,200' 或自动 '20:20:200'(起:步:止) → 绘制 power 曲线")
    p.add_argument("--power_seq", type=str, default=None,
                   help="效能序列: 显式 '0.6,0.7,0.95' 或自动 '0.6:0.05:0.95' → 绘制样本量曲线")
    p.add_argument("--plot_effects", type=str, default=None,
                   help="多效应量叠加(可选): '0.3,0.5,0.8' 画多条曲线做敏感性分析")
    p.add_argument("--out", type=str, default=None,
                   help="曲线 PNG 输出路径 (默认系统临时目录)")

    # ── 出图模式（ct-base §19.9）──
    p.add_argument("--figure-mode", dest="figure_mode", choices=["svg_inline", "png_file"],
                   default=None,
                   help="图形呈现模式: svg_inline(默认,内联对话流) / png_file(本地 cairosvg 转 PNG)。"
                        "也可经环境变量 CTSS_FIGURE_MODE 设置。")

    return p


def main():
    p = build_parser()
    args = p.parse_args()

    # ── Security: validate every user string that reaches generated R code ──
    # These are interpolated into R string literals; enforce strict allowlists so
    # they can never inject arbitrary R code. Fail fast with a clear message.
    try:
        _validate_token("--adaptive_type", args.adaptive_type)
        _validate_token("--design", args.design)
        _validate_token("--spending_func", args.spending_func)
        _validate_token("--effect_name", args.effect_name)
        if args.test == "adaptive_simulate":
            _validate_token("--sim_design", args.sim_design)
            _validate_token("--spending_function", args.spending_function)
            _validate_token("--reestimate_method", args.reestimate_method)
            _validate_token("--correction", args.correction)
            if args.effect_sizes is not None:
                if not re.match(r'^[0-9.,\- ]+$', args.effect_sizes):
                    raise ValueError(
                        t("error.effect_sizes_invalid", value=args.effect_sizes))
            if args.sim_output is not None:
                _validate_path(args.sim_output)
        if args.out is not None:
            _validate_path(args.out)  # raises ValueError if unsafe
    except ValueError as e:
        p.error(str(e))

    # SECURITY: dry-run is the SAFE DEFAULT. Execution requires an explicit
    # opt-in (--yes / -y) so generated R code is never run silently.
    confirmed = args.yes and not args.dry_run

    # ── Solve direction: --nobs given → solve for power; else solve for n ──
    if args.nobs is not None and args.nobs > 0:
        solve_for_power = True
    else:
        solve_for_power = False
        args.nobs = None

    # ── Numeric range validation ──
    _RANGE_RULES = {
        "alpha": (0, 0.5), "power": (0, 1),
        "auc0": (0, 1), "auc1": (0, 1),
        "correlation": (-1, 1), "icc": (0, 1),
        "margin": (0, None), "hazard_ratio": (0, None),
        "ni_margin_surv": (0, None), "sup_margin": (0, None),
        "delta_sup": (0, None),
        "ve_control": (0, 1), "ve_treatment": (0, 1),
        "prob_control": (0, 1), "prob_treatment": (0, 1),
        "p_control_sup": (0, 1), "p_control_current": (0, 1),
        "event_rate_exact": (0, 1), "dropout_exact": (0, 1),
        "p1": (0, 1), "p2": (0, 1),
        "eq_margin_surv": (0, None), "sup_margin_surv": (0, None), "sup_hr": (0, None),
        "cox_hr": (0, None), "cox_r2": (0, 1), "cox_prev": (0, 1),
        "cox_event_prop": (0, 1), "median0": (0, None), "median1": (0, None),
        "ci_control": (0, 1), "ci_treatment": (0, 1),
        "rate_control": (0, None), "rate_ratio": (0, None),
        "recur_followup": (0, None), "new_median": (0, None), "hist_n": (0, None),
        "gs_ratio": (0, 1), "gs_or": (0, None), "gs_median_control": (0, None),
        "gs_rate1": (0, None), "gs_rate2": (0, None), "gs_poisson_time": (0, None),
        "nobs": (0, None),
    }
    _range_errors = []
    for label, (lo, hi) in _RANGE_RULES.items():
        val = getattr(args, label, None)
        if val is None:
            continue
        if lo is not None and val <= lo:
            _range_errors.append(t("validation.range_error_gt", label=label, bound=lo, val=val))
        if hi is not None and val >= hi:
            _range_errors.append(t("validation.range_error_lt", label=label, bound=hi, val=val))
    if _range_errors:
        print(t("validation.failed"))
        for e in _range_errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    # ── 效应量 / 检验方向统一处理 (--side / --sd) ──
    # alt: one-sided -> "greater" (预期处理组更优); two-sided -> "two.sided"
    alt = "greater" if args.side == "one" else "two.sided"
    # d_val: 提供 --sd 时 --effect 视为原始均差 Δ, 自动折算 d = Δ/sd; 否则 --effect 直接为 d
    if args.sd is not None and args.sd > 0:
        d_val = (args.effect if args.effect is not None else 0.5) / args.sd
    else:
        d_val = args.effect if args.effect is not None else 0.5

    if not args.test:
        p.error(t("error.test_required"))

    # ═════════════════════════════════════════════════════════════════════════
    # 统一后端调度（coze 权威 / 本地 Python 兜底 / 本地 R 开发后端）
    # ═════════════════════════════════════════════════════════════════════════
    ctx = {
        "confirmed": confirmed,
        "solve_for_power": solve_for_power,
        "alt": alt,
        "d_val": d_val,
        "curve": bool(args.n_seq or args.power_seq),
        "show_code": bool(args.show_code),
        "dry_run": bool(args.dry_run),
        # R 真相源开关：要求随结果回传完整 R 源码 + R 数值（repro.r）
        "return_r_code": (bool(args.show_code)
                          or os.environ.get("CTSS_RETURN_R_CODE") in ("1", "true", "yes")),
    }

    try:
        backend = select_backend(args.test)  # v5: 唯一后端 = coze（无本地回退）
    except RuntimeError as exc:
        print(str(exc))
        sys.exit(1)

    # ── 待执行载荷预览（local-r → R 源码；coze → 请求信封；python → 无）──
    gated = backend.requires_confirmation          # 本地 R 需 --yes；coze / Python 不需要
    payload = backend.preview(args.test, args, ctx)
    if payload is not None and (args.show_code or args.dry_run or (gated and not confirmed)):
        _hdr = t("header.r_code") if gated else t("header.coze_request")
        print("=" * 60)
        print(_hdr)
        print("=" * 60)
        print(payload)
        print("=" * 60)

    if gated and not confirmed:
        print(t("safe_preview.not_executed_curve") if ctx["curve"]
              else t("safe_preview.not_executed"))
        return
    if args.dry_run:
        return

    if gated:
        print(t("exec.running"))
        sys.stdout.flush()

    try:
        res = backend.compute(args.test, args, ctx)
    except RuntimeError as exc:
        print(str(exc))
        sys.exit(1)

    if res.text:
        print(res.text)

    # ── 图形产物（coze 返回 SVG/HTML；本地 R 直接写 PNG）──
    render_figures(res.figures, args.test, figure_mode=args.figure_mode)
    # coze 端无图（svglite/cairo 缺失）但返回曲线数值 → 本地生成 SVG 兜底（ct-base §19）。
    # 仅在 coze 未返回任何图形时才兜底——否则同一曲线会被处理两遍（coze SVG + 本地
    # fallback 两份输出），且持久化文件可能被无参考线的 fallback 版覆盖（2026-08-20 修复）。
    if not res.figures:
        render_curve_fallback(res.meta, args.test,
                              target_power=getattr(args, "power", None) or 0.8)

    # ── 自动附带曲线（简单单/两组问题默认出图，用户设定 2026-08-20）──
    # 规则: forward（求 n）→ 自动补「样本量随把握度」曲线；reverse（求 power）→
    # 自动补「把握度随样本量」曲线。仅当：① 检验属简单单/两组集合；② 用户未显式
    # 指定曲线（--n_seq / --power_seq）；③ 非 dry-run；④ coze 路径（非本地 R）。
    # 关闭方式：显式指定 --n_seq / --power_seq（走用户自己的曲线），或 --dry-run。
    _AUTO_CURVE_TESTS = {"ttest_ind", "ttest_paired", "ttest_one",
                         "proportion_one", "proportion_two"}
    if (not ctx["curve"] and args.test in _AUTO_CURVE_TESTS
            and not args.dry_run and not gated):
        try:
            args2 = argparse.Namespace(**vars(args))
            args2.n_seq = None
            args2.power_seq = None
            args2.plot_effects = None
            ctx2 = dict(ctx)
            ctx2["curve"] = True
            _what = ""
            if solve_for_power and args.nobs:
                _n = args.nobs
                _n_min = max(5, int(_n * 0.5))
                _n_max = max(_n_min + 8, int(_n * 1.5))
                _step = max(1, round((_n_max - _n_min) / 8))
                args2.n_seq = "%d:%d:%d" % (_n_min, _step, _n_max)
                _what = "把握度随样本量（以 n=%d 为中心 ±50%%）" % _n
            else:
                args2.power_seq = "0.6:0.05:0.95"
                _what = "样本量随把握度（power 0.60~0.95）"
            res2 = backend.compute(args.test, args2, ctx2)
            if res2 and getattr(res2, "figures", None):
                render_figures(res2.figures, args.test, figure_mode=args.figure_mode)
            else:
                # coze 无图 → 本地兜底（★ 参考线目标 = 用户 --power 或默认 0.8）
                render_curve_fallback(getattr(res2, "meta", None), args.test,
                                      target_power=getattr(args2, "power", None) or 0.8)
            print("# 已自动附带%s曲线（简单单/两组问题默认出图；如需关闭请显式指定 "
                  "--n_seq / --power_seq 或 --dry-run）" % _what)
        except Exception as _e:  # noqa: BLE001 - 自动曲线失败不阻断主结果
            print("# 自动曲线生成跳过: %s" % _e)
    # coze 返回未填充 meta 时（无 __CTSS_RESULT__ 标记）res.meta 可为 None，防御性取空字典
    _png = (res.meta or {}).get("png_path")
    if _png:
        print(t("info.png_saved", path=_png))

    # ── R 源码 / R 数值（CTSS_RETURN_R_CODE=1 或 coze 主动回传）──
    _want_r = args.show_code or os.environ.get("CTSS_RETURN_R_CODE") in ("1", "true", "yes")
    if res.r_code and not gated and _want_r:
        print("=" * 60)
        print(t("header.r_code"))
        print("=" * 60)
        print(res.r_code)
    if res.r_result and _want_r:
        print("-" * 60)
        print(json.dumps(res.r_result, ensure_ascii=False, indent=2))
    if gated and not args.show_code:
        print(t("info.r_code_shown_default"))
    print("=" * 60)

if __name__ == "__main__":
    main()

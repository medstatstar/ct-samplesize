#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
justify_text.py — IRB/SAP-ready 样本量论证段落生成（中英对照）
（ct-update upgrade J2，对标 calc-sample-size 的 IRB-ready justification +
 medsyniq-lite 的"监管感知"叙事，2026-09-29）

措辞骨架逐句锚定两套权威结构（非抄第三方模板）：
  * CONSORT-SPIRIT Item 14 / DELTA2 Box 4（sample size 报告清单：主终点 → α/power →
    目标差值按终点类型 → 分配比 → 公式/软件 + 脱落校正 → 敏感性；依据声明）
  * CDE《药物临床试验样本量估计指导原则（试行）》（2024-12-23 施行）：试验设计 →
    检验水准与效能 → 统计方法假设 → 预期治疗效应及变异的参数依据 → 样本量调整沟通
  输出为**双栏对照段落 + 〔占位符〕**：可粘贴进方案 14 节 / SAP 后由研究者补全
  引用文献与机构信息。本模块只产措辞骨架，不替研究者做临床判断——所有"依据"句
  都强制暴露来源占位，防『伪造精确』（anti fake-precision）。

用法：
  独立预览：python scripts/justify_text.py --test ttest_ind --mcid 5 --sd 15 ...
  主流程附加：samplesize_power.py ... --justify（计算后自动填充 n/参数）
纯标准库、零联网、不调 coze。
"""
import argparse
import sys

# 每个设计变体 = 一组 (EN 句, ZH 句) 对；句内 {key} 由 _ctx 填充，
# 未知值渲染为 [__ ] 占位提醒（黄框级醒目，防误粘贴未填段落）。
_PLACEHOLDER = "[__填写]"


def _fmt(v, suffix=""):
    return ("%s%s" % (v, suffix)) if v is not None else _PLACEHOLDER


def _engine_str(meta=None):
    """引擎声明（用户口径 2026-09-29：只给 R 版本号 + 包版本号，**不标注云端/本地**）。

    版本来自信封 repro.r_version / repro.packages（_envelope_to_result 已透传进
    meta）；拿不到的版本渲染为占位（可复现性要求版本必须实，不可留空粘贴）。
    形如：R 4.3.1 + rpact 3.5.1 + TrialSize 0.3.2。
    """
    meta = meta or {}
    rv = meta.get("r_version") or ""
    if rv.lower() in ("", "mock"):      # mock 信封版本不渲染进正式段落
        rv = _PLACEHOLDER
    pk = meta.get("packages") or {}
    pk_bits = []
    for name in ("rpact", "TrialSize", "PowerTOST"):
        ver = pk.get(name) or pk.get(name.lower())
        if ver:
            pk_bits.append("%s %s" % (name, ver))
    if not pk_bits:
        pk_bits.append("rpact/TrialSize " + _PLACEHOLDER)
    return "R %s + %s" % (rv, " + ".join(pk_bits))


def _ctx(test, args, d_val, n_total, mcid_mode, meta=None):
    g = lambda k, default=None: getattr(args, k, default)
    # MCID 模式下目标差值即 MCID（主流程中 args.effect 已被赋值为 mcid；
    # 独立预览只给了 --mcid 时同样以 MCID 为目标差值）
    _effect = g("effect")
    if _effect is None and g("mcid") is not None:
        _effect = g("mcid")
    return {
        "test": test or _PLACEHOLDER,
        "engine": _engine_str(meta),
        "alpha": _fmt(g("alpha")),
        "power": _fmt(g("power")),
        "side_zh": "单侧" if g("side") == "one" else "双侧",
        "side_en": "one-sided" if g("side") == "one" else "two-sided",
        "effect": _fmt(_effect),
        "d": _fmt(round(d_val, 4) if d_val is not None else None),
        "sd": _fmt(g("sd")),
        "ratio": _fmt(g("ratio") if g("ratio") is not None else 1),
        "n": _fmt(n_total),
        "dropout": _fmt(g("dropout_rate")),
        "margin": _fmt(g("margin")),
        "hr": _fmt(g("hazard_ratio")),
        "p1": _fmt(g("p1")),
        "p2": _fmt(g("p2")),
        "mcid": _fmt(g("mcid")),
        "mcid_src": g("mcid_source") or _PLACEHOLDER,
        "p1_note": "",
    }


# ---------------------------------------------------------------------------
# 变体一：两组连续终点 优效性（ttest_ind 系；MCID 叙事最常用承载）
# ---------------------------------------------------------------------------
SUPERIORITY_CONT = {
    "en": [
        # Item 1: primary outcome + framework (SPIRIT 12/8)
        "The sample size is based on the primary endpoint of {test} comparing "
        "{p1_note}two parallel groups under a {side_en} superiority framework.",
        # Item 2: alpha & power (SPIRIT 14; CDE §二(二))
        "A {alpha} {side_en} significance level and {power} statistical power "
        "were selected, consistent with ICH E9 conventions for confirmatory "
        "trials.",
        # Item 3: target difference by outcome type (DELTA2 Box4-3b)
        "The target difference is expressed on the natural scale as {effect} "
        "(MCID = {mcid}, justified as: {mcid_src}), with a common standard "
        "deviation of {sd}, yielding a standardized effect size d = {d}.",
        # Item 4: allocation ratio (DELTA2 Box4-4)
        "Participants will be allocated in a {ratio}:1 ratio "
        "[rationale if unequal: ___].",
        # Item 5: computation + inflation (DELTA2 Box4-5; CDE §二(四))
        "The unadjusted required sample size computed with the {test} formula "
        "(software: {engine}), inflated to allow a "
        "{dropout} dropout rate, is {n}.",
        # Item 6: sensitivity (DELTA2 Box4-5d; CDE §五(三))
        "Sensitivity of the sample size to the assumed target difference and "
        "variance was assessed (power/sample-size curves provided); a [__X]% "
        "reduction in the assumed difference raises the requirement to [__] "
        "participants.",
    ],
    "zh": [
        "本试验样本量基于主要终点，采用两平行组{side_zh}优效性设计，检验方法为 {test}。",
        "检验水准取 {alpha}（{side_zh}）、检验效能取 {power}，符合 ICH E9 对确证性试"
        "验的常规设定，亦与《药物临床试验样本量估计指导原则（试行）》对参数设置的基"
        "本考虑一致。",
        "目标差值以终点的自然尺度表述为 {effect}（最小重要差值 MCID = {mcid}，其确定"
        "依据为：{mcid_src}，即锚定法/分布法/专家共识之〔填写并引用文献〕），共同标准"
        "差为 {sd}，折算标准化效应量 d = {d}。",
        "受试者按 {ratio}:1 分配〔若不等，说明理由：___〕。",
        "按 {test} 公式（软件环境：{engine}，方法细节见统计附录与随"
        "附 R 代码）计算并计入 {dropout} 脱落率后，所需样本量为{n_zh}。",
        "已对样本量关于目标差值与方差假设进行敏感性分析（提供把握度/样本量曲线）：若"
        "预设差值下减 [__X]%，所需例数升至 [__]，本设计可接受／需调整（择其一）。",
    ],
}

# ---------------------------------------------------------------------------
# 变体二：非劣效 / 等效（non_inferiority / equivalence / ni_survival 系）
# ---------------------------------------------------------------------------
NONINFERIORITY = {
    "en": [
        "The trial is designed as a {side_en} non-inferiority comparison with "
        "a prespecified margin of {margin} on the primary endpoint scale.",
        "The non-inferiority margin was judged clinically relevant and "
        "internally consistent with regulatory convention [preservation of at "
        "least [__]% control effect, or absolute margin accepted with ___ "
        "agency; cite: ___].",
        "Assuming an active-control effect consistent with prior evidence "
        "[cite: ___] and an experimental effect [__] relative to the control, "
        "a {alpha} {side_en} test with {power} power requires {n} "
        "(allocation {ratio}:1; dropout allowance {dropout}).",
        "The sample size computation follows the {test} procedure "
        "({engine}; R code provided) and its sensitivity to the margin and effect "
        "assumptions is reported in the appendix curves.",
    ],
    "zh": [
        "本试验为{side_zh}非劣效设计，预先设定主要终点尺度上的非劣效界值 δ = {margin}。",
        "该界值经临床相关性判断并与监管惯例保持一致〔通常为『保留对照疗效不少于 "
        "[__]%』的类推导，或已有沟通纪要支持：___，引用：___〕。界值是临床—监管假设，"
        "不来源于统计惯例。",
        "在阳性对照疗效与既往证据一致〔引用：___〕、试验药相对对照效应为 [__] 的假设"
        "下，取 {alpha}（{side_zh}）检验水准与 {power} 检验效能，按 {test} 程序计算所"
        "需样本量为{n_zh}（分配比 {ratio}:1，已计入 {dropout} 脱落）。",
        "样本量计算采用 {engine}（方法见统计附录与随附 R 代码），"
        "其对界值与效应假设的敏感性分析见曲线附录。",
    ],
}

# ---------------------------------------------------------------------------
# 变体三：生存 / 事件驱动（survival 系；HR + 事件数叙事）
# ---------------------------------------------------------------------------
SURVIVAL = {
    "en": [
        "For the time-to-event primary endpoint, sample size is driven by the "
        "required number of events rather than participants alone: under an "
        "assumed hazard ratio of {hr} with a {alpha} {side_en} log-rank test "
        "and {power} power, [__] events are required (Schoenfeld formula; "
        "{engine}; R code attached).",
        "The assumed control-group event rate / survival distribution and "
        "accrual-follow-up schedule [specify: ___ ; cite source: ___] imply a "
        "maximum sample size of {n}, enrolled over [__] months "
        "with [__] months minimum follow-up.",
        "Event-count sensitivity: if the pooled event rate is lower than "
        "assumed by [__]%, the analysis is powered at [__]% or follow-up is "
        "extended accordingly (prespecified rule in the SAP).",
    ],
    "zh": [
        "主要终点为时间-事件型，样本量由所需事件数驱动：预设风险比 HR = {hr}，取 "
        "{alpha}（{side_zh}）log-rank 检验与 {power} 检验效能，按 Schoenfeld 公式需"
        "观察事件数 [__] 例次（计算软件：{engine}，随附 R 代码）。",
        "对照组事件率/生存分布假设与入组-随访计划〔列明：___；来源引用：___〕共同决定"
        "最大样本量为{n_zh}，预计 [__] 个月入组、最低随访 [__] 个月。",
        "事件数敏感性（SAP 预设规则）：若合并事件率较假设低 [__]%，则把握度降为 "
        "[__]%，或按预设规则相应延长随访。",
    ],
}

# ---------------------------------------------------------------------------
# 通用回退（其他 test：比例/BE/序贯等给最小骨架）
# ---------------------------------------------------------------------------
GENERIC = {
    "en": [
        "Sample size for the {test} design: {alpha} {side_en} significance, "
        "{power} power, target effect {effect} (standardized: {d}), allocation "
        "{ratio}:1, dropout allowance {dropout}; required sample size = {n} "
        "(software: {engine}; formula/R code in appendix). [Primary-outcome rationale and "
        "effect-source citation: ___]",
    ],
    "zh": [
        "{test} 设计样本量：{alpha}（{side_zh}）检验水准、{power} 检验效能、目标效应 "
        "{effect}（标准化 {d}）、分配比 {ratio}:1、脱落 {dropout}，需样本量{n_zh}"
        "（软件环境：{engine}；公式与 R 代码见附录）。〔主要终点选取理由与效应量依据引用：___〕",
    ],
}

_VARIANTS = [
    (("non_inferiority", "equivalence", "ni_survival", "be_tost",
      "superiority_margin", "survival_equivalence"), NONINFERIORITY),
    (("survival", "survival_exact", "survival_superiority", "cox_covariate",
      "survival_one_sample", "survival_historical", "competing_risks",
      "recurrent_events", "gsd_survival", "gsd_survival_sim", "gsd_hazard",
      "gsd_hazard_sim"), SURVIVAL),
    (("ttest_ind", "ttest_paired", "ttest_one", "anova", "dunnett",
      "mixed_model", "proportion_two", "proportion_one", "proportion_paired",
      "odds_ratio", "risk_ratio", "poisson", "roc", "vaccine_efficacity",
      "vaccine_efficacy", "bland_altman", "multiple_endpoints",
      "historical_controls"), SUPERIORITY_CONT),
]


def _pick(test):
    for keys, block in _VARIANTS:
        if test in keys:
            return block
    return GENERIC


def render(test, args, d_val, n_total=None, mcid_mode=False, n_note="总", meta=None):
    """返回中英对照论证段落文本（主流程 --justify 与独立运行共用）。

    n_note: "总"=n_total 为总例数；"每组"=按组例数（主流程按引擎返回字段判定）。
    meta  : 计算结果 meta（透传 r_version/packages → 引擎声明 "R <ver> + rpact <ver>"；
            独立预览无 meta 时版本渲染为占位，由研究者按随附 R sessionInfo 填实）。
    """
    ctx = _ctx(test, args, d_val, n_total, mcid_mode, meta=meta)
    if n_total is not None:
        _u_en = "%s per group" % n_total if n_note == "每组" else "%s in total" % n_total
        _u_zh = "%s 例/组" % n_total if n_note == "每组" else "%s 例" % n_total
        ctx["n"] = _u_en          # EN 句使用；ZH 句通过 n_zh
        ctx["n_zh"] = _u_zh
    else:
        ctx["n"] = ctx["n_zh"] = _PLACEHOLDER
    block = _pick(test or "")
    out = []
    out.append("\n\n" + "=" * 60)
    out.append("样本量论证段落 / Sample-Size Justification (IRB/SAP-ready)")
    out.append("=" * 60)
    out.append("> 骨架：CONSORT-SPIRIT Item 14 + DELTA2 Box 4（英文可审计语序）；CDE《药物临床试验样本量估计指导原则（试行）》2024-12-23（中文口径）。")
    out.append("> 用法：粘贴至方案『样本量』小节 / SAP；所有 [__ ] 与 ___ 占位必须由研究者填实（依据引用、机构信息），不得留白提交。本段落不替代监管沟通。\n")
    out.append("【EN】")
    for i, s in enumerate(block["en"], 1):
        out.append("%d. " % i + s.format(**ctx))
    out.append("")
    out.append("【中文】")
    for i, s in enumerate(block["zh"], 1):
        out.append("%d. " % i + s.format(**ctx))
    if mcid_mode:
        out.append("")
        out.append("[MCID] 本文段落已注入 MCID 叙事：MCID=%s（原始单位）、SD=%s、d=%s；"
                   "依据声明：%s" % (_fmt(args.mcid), _fmt(getattr(args, "sd", None)),
                                    ctx["d"], getattr(args, "mcid_source", None) or _PLACEHOLDER))
    return "\n".join(out)


def _main():
    ap = argparse.ArgumentParser(description="样本量论证段落独立预览（规划层，不做计算）")
    ap.add_argument("--test", default="ttest_ind")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--power", type=float, default=0.8)
    ap.add_argument("--side", choices=["one", "two"], default="two")
    ap.add_argument("--effect", type=float, default=None)
    ap.add_argument("--sd", type=float, default=None)
    ap.add_argument("--mcid", type=float, default=None)
    ap.add_argument("--mcid-source", default=None)
    ap.add_argument("--ratio", type=float, default=None)
    ap.add_argument("--dropout-rate", dest="dropout_rate", type=float, default=0.05)
    ap.add_argument("--margin", type=float, default=None)
    ap.add_argument("--hazard-ratio", dest="hazard_ratio", type=float, default=None)
    ap.add_argument("--p1", type=float, default=None)
    ap.add_argument("--p2", type=float, default=None)
    ap.add_argument("--n", dest="n", type=float, default=None,
                     help="仅预览用：手动指定已求得的总样本量（主流程 --justify 自动填充）")
    a = ap.parse_args()
    d = (a.effect if a.effect is not None else
         (a.mcid / a.sd if a.mcid is not None and a.sd else None))
    print(render(a.test, a, d, n_total=a.n, mcid_mode=a.mcid is not None))
    return 0


if __name__ == "__main__":
    sys.exit(_main())

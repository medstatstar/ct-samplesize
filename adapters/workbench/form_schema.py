#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""form_schema.py — 工作台表单 schema 运行时反射层（零维护）。

设计原则
--------
工作台的表单**绝不手写**：全部字段的类型 / 默认值 / choices / 说明都从
`scripts/samplesize_power.py` 的 argparse 运行时反射得到，检验方法的必填参数
与家族归属从 `tests/coze_cases/_contract_index.json` 读取。这样上游新增参数或
检验方法时，工作台**自动同步**，不存在"表单忘了更新"这类漂移。

反射不到的只有一件事：argparse help 为空的 107 个统计参数的**人类可读标签**。
这些由 `PARAM_META` 字典补充（双语）。它不是字段清单，只是文案层——
新增参数时缺失标签只会退化为显示参数名，不会导致表单缺字段（退化安全）。

输出契约
--------
get_catalog(lang) -> {
    "version", "skill_version", "generated_at",
    "tests":   [{test, family, label, required, output, notes, curve, figures}],
    "families":[{id, label, tests:[test_id...]}],
    "groups":  [{id, label, params:[name...]}],
    "params":  {name: {flag, type, default, choices, label, help, group, unit}},
    "curve_solvers": [test_id...],
}

用法：
    python form_schema.py [--lang zh] [--test ttest_ind] [--json]
"""
import os
import sys
import json
import time
import re
import argparse
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))   # .../ct-samplesize/adapters/workbench
_ADAPTERS = os.path.dirname(_HERE)                   # .../ct-samplesize/adapters
_SKILL = os.path.dirname(_ADAPTERS)                  # .../ct-samplesize
_SCRIPTS = os.path.join(_SKILL, "scripts")
_CONTRACT = os.path.join(_SKILL, "tests", "coze_cases", "_contract_index.json")
for _p in (_SCRIPTS, _ADAPTERS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# 参数分组（前端据此分栏渲染）
# ---------------------------------------------------------------------------
COMMON_PARAMS = {
    "alpha", "power", "nobs", "side", "sd", "ratio", "language", "effect",
}
CURVE_PARAMS = {
    "n_seq", "power_seq", "plot_effects", "effect_seq",
    "dist_plot", "power_time_seq", "heatmap",
}
FIGURE_PARAMS = {"figure_mode"}
VERIFY_PARAMS = {"verify", "verify_design", "verify_n", "verify_side",
                 "verify_looks", "verify_spending"}
# 不进表单（CLI 运行控制位，非统计参数）
HIDDEN_PARAMS = {
    "test", "nl", "dry_run", "show_code", "show_assumptions", "yes",
    "batch_file", "help",
}

# argparse 默认 None、或需在前端显式呈现的「临床试验常规默认值」。
# 注入后：① 表单 schema 携带该 default，前端 fieldHTML 直接预填对话框选项；
# ② 服务端 _compute 缺失即补填，前后端默认值一致、不与「coze 自有缺省」冲突。
# 仅收录经契约确认、有公认常用值、缺失时 coze 必填自身默认、不影响结果正确性的字段。
# 真必填且无公认默认者（effect / p1 / p2 等效应量类）不在此列——仍报错要求用户给出。
UI_DEFAULTS = {
    "ratio": 1.0,    # 等比例分配（argparse 默认 None，必须注入）
    "alpha": 0.05,   # 双侧显著性水平（argparse 已默认 0.05，显式列出作文档/兜底）
    "power": 0.8,    # 目标检验效能 80%（argparse 已默认 0.8，同上）
    "side": "two",   # 双侧检验（argparse 已默认 two，同上）
}

# 下拉选项双语显示标签：{param: {value: (zh, en)}}。
# 未映射的 choices 原样显示（多为国际通用专业名词，如 Dunnett/Pocock/OF，无需翻译）。
CHOICE_LABELS = {
    "side": {"one": ("单侧", "one-sided"), "two": ("双侧", "two-sided")},
    "figure_mode": {"svg_inline": ("内嵌 SVG", "inline SVG"), "png_file": ("PNG 文件", "PNG file")},
    "language": {"zh": ("中文", "Chinese"), "en": ("英文", "English")},
    "gs_proportion_metric": {
        "difference": ("率差", "risk difference"),
        "ratio": ("率比", "risk ratio"),
        "or": ("比值比", "odds ratio"),
    },
    "sim_design": {
        "group_sequential": ("成组序贯", "group sequential"),
        "adaptive_reestimate": ("自适应再估计", "adaptive re-estimation"),
        "drop_the_loser": ("淘汰设计", "drop-the-loser"),
    },
    "spending_function": {
        "obrien_fleming": ("O'Brien-Fleming", "O'Brien-Fleming"),
        "pocock": ("Pocock", "Pocock"),
        "power_family": ("幂族", "power family"),
    },
    "correction": {"dunnett": ("Dunnett", "Dunnett"), "bonferroni": ("Bonferroni", "Bonferroni")},
}

# 常用参数中文说明（覆盖 argparse 英文 help；未映射参数保留英文原 help）。
HELP_ZH = {
    "effect": "效应量：连续型检验填 Cohen's d；若同时填 σ（标准差），则视为原始均差 Δ，自动折算 d = Δ/σ。",
    "sd": "两组合并标准差 σ。提供时 effect 视为原始均差 Δ，自动 d = Δ/σ。",
    "alpha": "双侧 I 类错误 α（显著性水平），常用 0.05。",
    "power": "目标把握度（1−β），常用 0.8 / 0.9。",
    "side": "检验方向：双侧（two）或单侧（one）。",
    "ratio": "分配比 n2/n1，1.0 表示两组等比例。",
    "nobs": "已知总样本量（反求效能时必填）。",
    "language": "结果报告语言：中文（zh）或英文（en）。",
    "k_groups": "组数 k（ANOVA 多组比较，≥2）。",
    "margin": "非劣效/优效界值。",
    "p1": "试验组率（0~1）。",
    "p2": "对照组率（0~1）。",
    "accrual_time": "入组期时长（月）。",
    "followup_time": "随访期时长（月）。",
    "hr_expected": "期望风险比 HR。",
    "win_ratio_theta": "win ratio 零假设界值 θ。",
}

# 与 HELP_ZH 对称的英文说明（EN 界面单击切换后显示；argparse help 为中文时兜底）。
# 缺失时前端退回 argparse 原 help（英文原样 / 中文则不理想，故常见参数尽量齐全）。
HELP_EN = {
    "effect": "Effect size: Cohen's d for continuous endpoints; if σ (SD) is also given it is treated as raw mean difference Δ, auto-converted to d = Δ/σ.",
    "sd": "Pooled SD σ. If given, effect is treated as raw mean difference Δ, auto d = Δ/σ.",
    "alpha": "Two-sided type I error α (significance level), commonly 0.05.",
    "power": "Target power (1−β), commonly 0.8 / 0.9.",
    "side": "Test direction: two-sided (two) or one-sided (one).",
    "ratio": "Allocation ratio n2/n1; 1.0 means equal group sizes.",
    "nobs": "Given total sample size (required when solving for power).",
    "language": "Result report language: Chinese (zh) or English (en).",
    "k_groups": "Number of groups k (ANOVA multi-group comparison, ≥2).",
    "margin": "Non-inferiority / superiority margin.",
    "p1": "Event rate in treatment arm (0–1).",
    "p2": "Event rate in control arm (0–1).",
    "accrual_time": "Accrual period (months).",
    "followup_time": "Follow-up period (months).",
    "hr_expected": "Expected hazard ratio HR.",
    "win_ratio_theta": "Win-ratio null hypothesis margin θ.",
    # argparse help 为纯中文的少量冷门参数（其余中英混合保留原 help）
    "reestimate_method": "Sample-size re-estimation method (SSR).",
    "correction": "Multiplicity correction (Dunnett / Bonferroni).",
    "sim_seed": "Random seed for simulation reproducibility.",
}

# ---------------------------------------------------------------------------
# 人类可读标签（双语）。仅补充 argparse help 为空或过长的参数。
# 这是文案层，不是字段清单 —— 缺失只会退化显示参数名，不会丢字段。
# ---------------------------------------------------------------------------
PARAM_META = {
    # ── 公共 / 通用 ──────────────────────────────────────────────────
    "alpha":            ("显著性水平 α", "Significance level α"),
    "power":            ("目标检验效能", "Target power"),
    "nobs":             ("给定样本量（反求效能）", "Given sample size (solve power)"),
    "side":             ("检验方向", "Test side"),
    "sd":               ("标准差 SD（提供时 effect 视为均差Δ）", "SD (if given, effect = mean diff Δ)"),
    "ratio":            ("分配比 n2/n1", "Allocation ratio n2/n1"),
    "effect":           ("效应量（Cohen's d；提供 σ 时也可直接填均差 Δ）", "Effect size (Cohen's d; or raw Δ if σ given)"),
    "language":         ("输出语言", "Output language"),
    "k_groups":         ("组别数 k", "Number of groups k"),
    "margin":           ("非劣效界值", "Non-inferiority margin"),
    "hazard_ratio":     ("风险比 HR", "Hazard ratio HR"),
    # ── 生存 ─────────────────────────────────────────────────────────
    "accrual_time":     ("入组时长", "Accrual period"),
    "followup_time":    ("随访时长", "Follow-up period"),
    "dropout_rate":     ("脱落率", "Dropout rate"),
    "event_rate":       ("事件率", "Event rate"),
    "hr_expected":      ("期望 HR", "Expected HR"),
    "ni_margin_surv":   ("非劣效界值（HR）", "Non-inferiority margin (HR)"),
    "eq_margin_surv":   ("等效界值（HR）", "Equivalence margin (HR)"),
    "sup_margin_surv":  ("优效界值（HR）", "Superiority margin (HR)"),
    "sup_hr":           ("优效 HR", "Superiority HR"),
    "median0":          ("对照组中位生存（月）", "Control median survival (months)"),
    "median1":          ("治疗组中位生存（月）", "Treatment median survival (months)"),
    "new_median":       ("新药组中位生存（月）", "New treatment median survival (months)"),
    "hist_n":           ("历史对照样本量", "Historical control N"),
    "cox_hr":           ("Cox 风险比 HR", "Cox hazard ratio"),
    "cox_r2":           ("协变量 R²（解释度）", "Covariate R²"),
    "cox_prev":         ("协变量患病率", "Covariate prevalence"),
    "cox_event_prop":   ("事件比例", "Event proportion"),
    "ci_control":       ("对照组累积发生率", "Control cumulative incidence"),
    "ci_treatment":     ("治疗组累积发生率", "Treatment cumulative incidence"),
    "rate_control":     ("对照组复发率", "Control recurrence rate"),
    "rate_ratio":       ("复发率比 RR", "Recurrence rate ratio"),
    "recur_followup":   ("随访时长", "Follow-up period"),
    # ── 率 / 比例 ────────────────────────────────────────────────────
    "p1":               ("组 1 率（治疗组）", "Group 1 rate (treatment)"),
    "p2":               ("组 2 率（对照组）", "Group 2 rate (control)"),
    "sup_margin":       ("优效界值", "Superiority margin"),
    "sigma_ratio":      ("标准差比 σ2/σ1", "SD ratio σ2/σ1"),
    "p_control_sup":    ("对照组率", "Control rate"),
    "delta_sup":        ("优效差值 Δ", "Superiority difference Δ"),
    "p_control_current": ("当前对照事件率", "Current control event rate"),
    "prob_control":     ("对照组事件率", "Control event rate"),
    "prob_treatment":   ("治疗组事件率", "Treatment event rate"),
    "ve_control":       ("对照组感染率", "Control infection rate"),
    "ve_treatment":     ("治疗组感染率", "Treatment infection rate"),
    # ── 等效 / BE ────────────────────────────────────────────────────
    "theta0":           ("等效界值下限 θ0（T/R 比）", "Equivalence lower bound θ0 (T/R)"),
    "theta1":           ("等效界值下限 θ1", "Equivalence bound θ1"),
    "theta2":           ("等效界值上限 θ2", "Equivalence bound θ2"),
    "cv":               ("个体内变异系数 CV", "Intra-subject CV"),
    "design":           ("BE 试验设计", "BE study design"),
    # ── 计数 ─────────────────────────────────────────────────────────
    "lambda1":          ("对照组事件率 λ1", "Control event rate λ1"),
    "lambda2":          ("治疗组事件率 λ2", "Treatment event rate λ2"),
    "t1":               ("对照组暴露时间 t1", "Control exposure time t1"),
    "t2":               ("治疗组暴露时间 t2", "Treatment exposure time t2"),
    # ── 诊断 / 一致性 ────────────────────────────────────────────────
    "auc0":             ("H0 下 AUC", "AUC under H0"),
    "auc1":             ("H1 下 AUC", "AUC under H1"),
    "sd_diff":          ("差值标准差 SD(diff)", "SD of differences"),
    "w":                ("临床可接受一致性界值 w", "Clinical agreement limit w"),
    # ── 聚类 ─────────────────────────────────────────────────────────
    "icc":              ("组内相关系数 ICC", "Intraclass correlation ICC"),
    "m":                ("每簇个体数 m", "Cluster size m"),
    "n_indiv":          ("目标个体总数", "Target total individuals"),
    # ── 贝叶斯 /  Assurance ──────────────────────────────────────────
    "prior_a0":         ("先验权重 a0", "Prior weight a0"),
    "n_assurance":      ("每组样本量", "N per group"),
    "n_sim_assurance":  ("模拟次数", "Simulation replicates"),
    "margin_assurance": ("目标差值界值", "Target difference margin"),
    "shape1_trt":       ("治疗组先验 Beta α", "Treatment prior Beta α"),
    "shape2_trt":       ("治疗组先验 Beta β", "Treatment prior Beta β"),
    "shape1_ctrl":      ("对照组先验 Beta α", "Control prior Beta α"),
    "shape2_ctrl":      ("对照组先验 Beta β", "Control prior Beta β"),
    "a0_borrowing":     ("历史信息借用权重 a0", "Historical borrowing weight a0"),
    "historical_response": ("历史对照应答数", "Historical responders"),
    "historical_n":     ("历史对照样本量", "Historical control N"),
    # ── 剂量 / Win-Ratio / 多终点 ────────────────────────────────────
    "n_doses":          ("剂量水平数", "Number of dose levels"),
    "target_dlt":       ("目标 DLT 率", "Target DLT rate"),
    "win_ratio_theta":  ("胜率 θ (Win Ratio)", "Win ratio θ"),
    "se_approx":        ("log(胜率) 标准误", "SE of log(win ratio)"),
    "n_sim_initial":    ("初始模拟次数", "Initial simulation replicates"),
    "n_sim":            ("模拟次数", "Simulation replicates"),
    "correlation":      ("终点间相关系数", "Correlation between endpoints"),
    "n_endpoints_must": ("共同主要终点数", "Number of co-primary endpoints"),
    "effect_must":      ("每终点效应量", "Effect size per endpoint"),
    "correlation_must": ("终点间相关系数", "Correlation between endpoints"),
    # ── MAMS / Dunnett / 中介 / 混合模型 ─────────────────────────────
    "n_arms_mams":      ("试验臂数", "Number of arms"),
    "n_stages_mams":    ("阶段数", "Number of stages"),
    "delta_effect":     ("目标效应量 Δ", "Target effect size Δ"),
    "n_groups_dunnett": ("总组数", "Total groups"),
    "n_control_dunnett": ("对照组数", "Number of controls"),
    "effect_dunnett":   ("效应量", "Effect size"),
    "a_path":           ("中介 a 路径系数", "Mediation path a"),
    "b_path":           ("中介 b 路径系数", "Mediation path b"),
    "sigma2_m":         ("中介变量残差方差", "Mediator residual variance"),
    "sigma2_y":         ("结局残差方差", "Outcome residual variance"),
    "cprime":           ("直接效应 c'", "Direct effect c'"),
    "n_sim_mediation":  ("模拟次数", "Simulation replicates"),
    "varcorr":          ("随机效应方差", "Random-effect variance"),
    "sigma":            ("残差标准差 σ", "Residual SD σ"),
    "nsim":             ("模拟次数", "Simulation replicates"),
    "effect_name":      ("效应名称标签", "Effect label"),
    # ── 成组序贯 / 适应性 / 条件效能 ─────────────────────────────────
    "n_stages_adapt":   ("阶段数", "Number of stages"),
    "effect_adaptive":  ("效应量", "Effect size"),
    "adaptive_type":    ("适应性设计类型", "Adaptive design type"),
    "timing":           ("期中分析信息分数", "Interim information fraction"),
    "observed_effect":  ("观测效应量", "Observed effect size"),
    "planned_effect":   ("计划效应量", "Planned effect size"),
    "n_completed":      ("已完成例数", "Completed N"),
    "n_planned":        ("计划总例数", "Planned total N"),
    # ── 图形 ─────────────────────────────────────────────────────────
    "figure_mode":      ("图形呈现模式", "Figure mode"),
    "n_seq":            ("样本量序列（power 曲线）", "Sample-size sequence (power curve)"),
    "power_seq":        ("效能序列（样本量曲线）", "Power sequence (sample-size curve)"),
    "effect_seq":       ("效应量序列（效应轴曲线）", "Effect-size sequence"),
    "plot_effects":     ("多效应量叠加", "Overlay multiple effect sizes"),
    "dist_plot":        ("H0/H1 分布重叠图", "H0/H1 distribution overlap"),
    "power_time_seq":   ("随访时长序列（生存）", "Follow-up sequence (survival)"),
    "heatmap":          ("效能热力图", "Power heatmap"),
    # ── 验证 ─────────────────────────────────────────────────────────
    "verify":           ("Monte-Carlo 验证闭环", "Monte-Carlo verification"),
    "verify_design":    ("验证设计类型", "Verification design"),
    "verify_n":         ("待验证样本量", "N to verify"),
    "verify_side":      ("验证检验方向", "Verification side"),
    "verify_looks":     ("验证期中次数", "Verification looks"),
    "verify_spending":  ("验证 α 消耗函数", "Verification spending function"),
    # ── exact 系列（生存精确法）──────────────────────────────────────
    "alpha_exact":      ("显著性水平 α", "Significance level α"),
    "power_exact":      ("目标效能", "Target power"),
    "hr_exact":         ("风险比 HR", "Hazard ratio HR"),
    "accrual_exact":    ("入组时长", "Accrual period"),
    "followup_exact":   ("随访时长", "Follow-up period"),
    "dropout_exact":    ("脱落率", "Dropout rate"),
    "event_rate_exact": ("事件率", "Event rate"),
    "n_stages_exact":   ("阶段数", "Number of stages"),
}

# 检验方法中英名称（contract index 只给 family，不给人类可读方法名）
TEST_LABELS = {
    "ttest_ind": ("两独立样本 t 检验", "Two-sample t-test"),
    "ttest_paired": ("配对 t 检验", "Paired t-test"),
    "ttest_one": ("单样本 t 检验", "One-sample t-test"),
    "anova": ("单因素方差分析", "One-way ANOVA"),
    "proportion_one": ("单组率检验", "One proportion"),
    "proportion_two": ("两独立率检验", "Two proportions"),
    "proportion_paired": ("配对率检验（McNemar）", "Paired proportions (McNemar)"),
    "odds_ratio": ("比值比 OR", "Odds ratio"),
    "risk_ratio": ("风险比 RR", "Risk ratio"),
    "non_inferiority": ("非劣效（率）", "Non-inferiority (proportion)"),
    "superiority_margin": ("优效性界值（率）", "Superiority margin (proportion)"),
    "equivalence": ("等效性（均值）", "Equivalence (mean)"),
    "be_tost": ("生物等效性 TOST", "Bioequivalence TOST"),
    "survival": ("生存分析（log-rank）", "Survival (log-rank)"),
    "survival_exact": ("生存精确法", "Exact survival"),
    "ni_survival": ("生存非劣效", "Survival non-inferiority"),
    "survival_equivalence": ("生存等效性", "Survival equivalence"),
    "survival_superiority": ("生存优效性", "Survival superiority"),
    "cox_covariate": ("Cox 协变量调整", "Cox with covariate"),
    "survival_one_sample": ("单组生存", "One-sample survival"),
    "competing_risks": ("竞争风险", "Competing risks"),
    "recurrent_events": ("复发事件", "Recurrent events"),
    "survival_historical": ("生存-历史对照", "Survival vs historical control"),
    "poisson": ("Poisson 计数", "Poisson counts"),
    "roc": ("ROC 曲线下面积", "ROC AUC"),
    "bland_altman": ("Bland-Altman 一致性", "Bland-Altman agreement"),
    "cluster": ("整群随机设计", "Cluster randomized"),
    "vaccine_efficacy": ("疫苗保护效力", "Vaccine efficacy"),
    "multiple_endpoints": ("多重终点校正", "Multiple endpoints"),
    "bayesian": ("贝叶斯设计", "Bayesian design"),
    "dose_escalation": ("剂量递增（3+3/CRM）", "Dose escalation"),
    "win_ratio": ("Win Ratio 胜率", "Win ratio"),
    "must_win": ("共同主要终点", "Co-primary (must-win)"),
    "historical_controls": ("历史对照借用", "Historical controls"),
    "mams": ("多臂多阶段 MAMS", "Multi-arm multi-stage"),
    "dunnett": ("Dunnett 多组比较", "Dunnett many-to-one"),
    "mediation": ("中介分析", "Mediation analysis"),
    "mixed_model": ("纵向 / MMRM", "Longitudinal / MMRM"),
    "group_sequential": ("成组序贯（均值）", "Group sequential (mean)"),
    "gsd_proportion": ("成组序贯（率）", "Group sequential (proportion)"),
    "gsd_survival": ("成组序贯（生存）", "Group sequential (survival)"),
    "gsd_hazard": ("成组序贯（HR）", "Group sequential (HR)"),
    "gsd_poisson": ("成组序贯（计数）", "Group sequential (count)"),
    "gsd_survival_sim": ("成组序贯仿真（生存）", "Group sequential sim (survival)"),
    "gsd_hazard_sim": ("成组序贯仿真（HR）", "Group sequential sim (HR)"),
    "adaptive": ("适应性设计", "Adaptive design"),
    "adaptive_simulate": ("适应性设计仿真", "Adaptive simulation"),
    "conditional_power": ("条件效能 / 期中再估计", "Conditional power"),
    "assurance": ("贝叶斯保证度", "Bayesian assurance"),
}

# 家族中英名（contract index 的 family 字段为中文，此处补英文）
FAMILY_LABELS = {
    "连续均值": ("连续型结局（均值）", "Continuous (means)"),
    "率": ("二分类结局（率）", "Binary (proportions)"),
    "率-非劣效": ("率 · 非劣效", "Proportion · non-inferiority"),
    "率-优效": ("率 · 优效", "Proportion · superiority"),
    "均值-等效": ("均值 · 等效", "Mean · equivalence"),
    "生物等效": ("生物等效性", "Bioequivalence"),
    "生存": ("生存 / 时间-事件", "Survival / time-to-event"),
    "生存-非劣效": ("生存 · 非劣效", "Survival · non-inferiority"),
    "生存-等效": ("生存 · 等效", "Survival · equivalence"),
    "生存-优效": ("生存 · 优效", "Survival · superiority"),
    "生存-协变量": ("生存 · 协变量调整", "Survival · covariate"),
    "生存-单组": ("生存 · 单组", "Survival · one-sample"),
    "生存-竞争风险": ("生存 · 竞争风险", "Survival · competing risks"),
    "生存-复发": ("生存 · 复发事件", "Survival · recurrent events"),
    "生存-历史对照": ("生存 · 历史对照", "Survival · historical control"),
    "计数": ("计数 / 率（Poisson）", "Counts (Poisson)"),
    "诊断": ("诊断试验", "Diagnostic accuracy"),
    "一致性": ("方法一致性", "Method agreement"),
    "聚类": ("整群随机", "Cluster randomized"),
    "疫苗": ("疫苗效力", "Vaccine efficacy"),
    "多重终点": ("多重终点", "Multiple endpoints"),
    "贝叶斯": ("贝叶斯", "Bayesian"),
    "剂量": ("剂量探索", "Dose-finding"),
    "Win-Ratio": ("Win Ratio", "Win ratio"),
    "共同主要": ("共同主要终点", "Co-primary endpoints"),
    "历史对照": ("历史对照", "Historical controls"),
    "多臂多阶段": ("多臂多阶段", "Multi-arm multi-stage"),
    "多组比较": ("多组比较", "Multiple comparisons"),
    "中介": ("中介分析", "Mediation"),
    "纵向/MMRM": ("纵向 / MMRM", "Longitudinal / MMRM"),
    "成组序贯": ("成组序贯设计", "Group sequential"),
    "成组序贯-仿真": ("成组序贯 · 仿真", "Group sequential · simulation"),
    "适应性": ("适应性设计", "Adaptive design"),
    "适应性-仿真": ("适应性 · 仿真", "Adaptive · simulation"),
    "期中/再估计": ("期中 / 再估计", "Interim / re-estimation"),
    "贝叶斯保证": ("贝叶斯保证度", "Bayesian assurance"),
}

# 界面文案（双语）
I18N = {
    "zh": {
        "group_common": "公共参数",
        "group_method": "方法参数",
        "group_curve": "曲线与敏感性",
        "group_figure": "图形选项",
        "group_verify": "Monte-Carlo 验证",
        "group_advanced": "高级参数",
        "solve_n": "求样本量（给定效能）",
        "solve_power": "求效能（给定样本量）",
    },
    "en": {
        "group_common": "Common",
        "group_method": "Method",
        "group_curve": "Curves & sensitivity",
        "group_figure": "Figures",
        "group_verify": "Monte-Carlo verification",
        "group_advanced": "Advanced",
        "solve_n": "Solve N (given power)",
        "solve_power": "Solve power (given N)",
    },
}


# ---------------------------------------------------------------------------
# 反射：从 argparse 抽取全部参数元数据
# ---------------------------------------------------------------------------
def _load_parser():
    """动态加载 samplesize_power.py 并取其 argparse parser。

    不去 exec 其 main()（module 级只定义函数，安全）。
    """
    path = os.path.join(_SCRIPTS, "samplesize_power.py")
    spec = importlib.util.spec_from_file_location("_ssp_cli", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_parser()


def _reflect_params(parser):
    """把 argparse actions 反射成 {name: meta}。"""
    out = {}
    for a in parser._actions:
        if not a.option_strings:
            continue
        name = a.dest
        if name in HIDDEN_PARAMS:
            continue
        is_flag = a.__class__.__name__ == "_StoreTrueAction"
        if is_flag:
            ptype = "bool"
        else:
            ptype = getattr(a.type, "__name__", None) or "str"
        default = a.default
        if default == argparse.SUPPRESS:
            default = None
        out[name] = {
            "name": name,
            "flag": a.option_strings[0],
            "type": ptype,
            "default": default,
            "choices": list(a.choices) if a.choices else None,
            "help": (a.help or "").strip(),
        }
    # 注入 coze 已知缺省值（argparse 默认 None 的字段）
    for n, v in UI_DEFAULTS.items():
        if n in out and out[n]["default"] is None:
            out[n]["default"] = v
    return out


def _group_of(name):
    if name in COMMON_PARAMS:
        return "common"
    if name in CURVE_PARAMS:
        return "curve"
    if name in FIGURE_PARAMS:
        return "figure"
    if name in VERIFY_PARAMS:
        return "verify"
    return "method"


def _load_contract():
    with open(_CONTRACT, "r", encoding="utf-8") as f:
        return json.load(f)


def _label_for(name, meta, lang):
    """标签优先级：PARAM_META（双语）> argparse help > 参数名。"""
    idx = 0 if lang == "zh" else 1
    if name in PARAM_META:
        return PARAM_META[name][idx]
    if meta.get("help"):
        # help 有时很长（含括号补充），取首句做标签，完整 help 另存 description
        return meta["help"].split("（")[0].split("(")[0].strip() or name
    return name


def _looks_chinese(text):
    """粗略判断一段 help 是否以中文为主（含 CJK 字符比例 >15%）。"""
    if not text:
        return False
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk > 0 and cjk * 100 // max(1, len(text)) > 15


def get_catalog(lang="zh"):
    """反射生成完整目录（前端据此渲染全部表单）。"""
    params = _reflect_params(_load_parser())
    contract = _load_contract()

    for name, meta in params.items():
        meta["group"] = _group_of(name)
        meta["label"] = _label_for(name, meta, lang)
        meta["label_zh"] = _label_for(name, meta, "zh")
        meta["label_en"] = _label_for(name, meta, "en")
        # 下拉选项双语显示标签（未映射的 choices 前端原样显示裸值）
        if meta.get("choices"):
            meta["choice_labels"] = CHOICE_LABELS.get(name)
        # 常用参数中文说明（help_zh），英文说明即 argparse 原 help
        if name in HELP_ZH:
            meta["help_zh"] = HELP_ZH[name]
        # EN 界面说明：HELP_EN 显式英文优先；argparse help 为空或为中文时，
        # 用 PARAM_META 英文标签兜底（避免 EN 界面露出中文 help）
        if name in HELP_EN:
            meta["help_en"] = HELP_EN[name]
        elif not meta.get("help") and name in PARAM_META:
            meta["help_en"] = PARAM_META[name][1]
        elif meta.get("help") and _looks_chinese(meta["help"]) and name in PARAM_META:
            meta["help_en"] = PARAM_META[name][1]

    tests = []
    families = {}
    for t in contract["tests"]:
        tid = t["test"]
        fam = t.get("family") or "其他"
        fam_label = (FAMILY_LABELS.get(fam) or (fam, fam))[0 if lang == "zh" else 1]
        required = [r for r in t.get("required", []) if r in params]
        # required 里可能有未反射到的（如 solve_for_power），单独记录
        required_extra = [r for r in t.get("required", []) if r not in params]
        tests.append({
            "test": tid,
            "family": fam,
            "family_label": fam_label,
            "label": (TEST_LABELS.get(tid) or (tid, tid))[0 if lang == "zh" else 1],
            "label_zh": (TEST_LABELS.get(tid) or (tid, tid))[0],
            "label_en": (TEST_LABELS.get(tid) or (tid, tid))[1],
            "required": required,
            "required_extra": required_extra,
            "output": t.get("output", []),
            "notes": t.get("notes", ""),
            "curve": bool(t.get("default_curve")),
            "figures": t.get("default_figure") or {},
            "r_function": t.get("r_function", ""),
        })
        fl = FAMILY_LABELS.get(fam) or (fam, fam)
        families.setdefault(fam, {"id": fam, "label": fl[0 if lang == "zh" else 1],
                                  "label_zh": fl[0], "label_en": fl[1], "tests": []})
        families[fam]["tests"].append(tid)

    groups = []
    for gid in ("common", "method", "curve", "figure", "verify"):
        groups.append({
            "id": gid,
            "label": I18N[lang]["group_" + gid],
            "params": sorted([n for n, m in params.items() if m["group"] == gid]),
        })

    try:
        sys.path.insert(0, _SCRIPTS)
        import importlib
        _ssp = importlib.import_module("samplesize_power")
        curve_solvers = sorted(_ssp._auto_curve_tests())
    except Exception:
        curve_solvers = sorted([t["test"] for t in tests if t["curve"]])

    return {
        "version": "1.0",
        "skill_version": _skill_version(),
        "lang": lang,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": tests,
        "families": list(families.values()),
        "groups": groups,
        "params": params,
        "curve_solvers": curve_solvers,
        "i18n": I18N[lang],
    }


def _skill_version():
    """从 SKILL.md frontmatter 读版本（与 coze_client._skill_version 同源）。"""
    path = os.path.join(_SKILL, "SKILL.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("version:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "unknown"


def schema_for(test, lang="zh"):
    """单检验方法的表单：required 字段 + 公共字段 + 图形字段（带默认值）。

    去重规则：通用参数（common）剔除「该检验必填清单」中已含的参数，
    避免 ratio/alpha/side/effect 等既在「必填参数」又在「通用参数」重复渲染。
    必填的公共参数只出现一次（在「必填参数」区，带 *）；只有可选的公共参数
    留在「通用参数」区（如 power/nobs/sd/language）。
    """
    cat = get_catalog(lang)
    entry = next((t for t in cat["tests"] if t["test"] == test), None)
    if not entry:
        return None
    required_set = set(entry["required"])
    common = [n for n in cat["groups"][0]["params"] if n not in required_set]
    curve = cat["groups"][2]["params"]
    figure = cat["groups"][3]["params"]
    return {
        "test": entry,
        "fields": {
            "required": [cat["params"][n] for n in entry["required"]],
            "common": [cat["params"][n] for n in common],
            "curve": [cat["params"][n] for n in curve] if entry["curve"] else [],
            "figure": [cat["params"][n] for n in figure],
        },
    }


def main():
    ap = argparse.ArgumentParser(description="ct-samplesize 工作台表单 schema 反射")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--test", default=None, help="只看某个检验方法的表单")
    ap.add_argument("--json", action="store_true", help="输出 JSON（默认人类可读摘要）")
    args = ap.parse_args()

    if args.test:
        out = schema_for(args.test, args.lang)
        if not out:
            sys.exit("✗ 未知检验方法：%s" % args.test)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    cat = get_catalog(args.lang)
    if args.json:
        print(json.dumps(cat, ensure_ascii=False, indent=2))
        return
    print("ct-samplesize 工作台 · 表单 schema 反射")
    print("  技能版本 : %s" % cat["skill_version"])
    print("  参数总数 : %d" % len(cat["params"]))
    print("  检验方法 : %d" % len(cat["tests"]))
    print("  家族分组 : %d" % len(cat["families"]))
    print("  曲线支持 : %s" % ", ".join(cat["curve_solvers"]))
    print()
    for g in cat["groups"]:
        print("  [%-8s] %-22s %d 个参数" % (g["id"], g["label"], len(g["params"])))
    print()
    missing = [t["test"] for t in cat["tests"]
               if not (t["label"] and t["label"] != t["test"])]
    if missing:
        print("  ⚠ 缺人类可读名称的检验方法：%s" % ", ".join(missing))
    else:
        print("  ✓ 全部 %d 个检验方法均有双语名称" % len(cat["tests"]))
    # 标签覆盖检查：help 为空且 PARAM_META 未覆盖的参数会退化为显示参数名
    bare = [n for n, m in cat["params"].items() if m["label"] == n]
    if bare:
        print("  ⚠ %d 个参数缺中文标签（退化为参数名）：%s%s" % (
            len(bare), ", ".join(bare[:12]), " …" if len(bare) > 12 else ""))
    else:
        print("  ✓ 全部 %d 个参数均有标签" % len(cat["params"]))


if __name__ == "__main__":
    main()

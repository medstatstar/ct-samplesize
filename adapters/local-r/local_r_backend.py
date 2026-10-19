#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adapters/local-r/local_r_backend.py — 本地 R 计算后端（dev-only，单一副本）

⚠️ 本文件是技能开发用本地 R 后端（adapters/local-r/），不随发布包分发
   （.clawhubignore 排除 adapters/local-r/），也不被 coze 端调用——
   coze 端计算全部由 src/r_engine/ 的 R 引擎完成。v5.12.0 起原
   adapters/coze/ct_r_lib/ 双副本（与 scripts/ 各存一份、屡次漂移）已废除，
   本文件为唯一副本；r_templates/ 与 legacy/ 随本目录一同搬迁。

职责：
  1. 承载全部 R 代码拼接逻辑（原 samplesize_power.py 中的 R 调度部分）；
  2. 提供 LocalRBackend，实现 ComputeBackend 契约，供本地开发 / 回归测试使用；
  3. 内联 R 真相源（I18N_R / ADAPTIVE_SIM_R）——与 coze 侧 src/r_engine/*.R
     为同一内容的两处表示；2026-10-15 已将 ADAPTIVE_SIM_R 整体回写为 coze 侧
     现行版本（含 2026-08-20 的 seq_len(K-1L)+1L 修复与 headless PNG 清理），
     此后改动以 coze 侧 src/r_engine/adaptive_sim.R 为准回写本文件。

启用方式：
  经 scripts/compute_backend.py::_load_local_r_backend() 懒加载（dev/回归用）。
"""
from __future__ import annotations

import argparse, sys, os, textwrap, subprocess, tempfile, re, json

# 本目录（adapters/local-r/，含 legacy/）与技能根 scripts/ 同时进入 import 路径
_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(os.path.dirname(_HERE))
_SCRIPTS = os.path.join(_SKILL_ROOT, "scripts")
for _p in (_HERE, os.path.join(_HERE, "legacy"), _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from r_templates import *          # noqa: F401,F403  (R 模板集合)
from i18n import t
from compute_backend import ComputeBackend, Result

I18N_R = r"""# =============================================================================
# i18n.R -- bilingual (EN/ZH) localization for ct-samplesize R templates
#
# This file is prepended to every generated R script. It provides:
#   - t(key, ...): translate a message key to the current locale
#
# Rules (per ~/.workbuddy/MEMORY.md "双语语言策略"):
#   - Default: English
#   - Auto-switch to Chinese when OS locale contains zh/CN
#   - Code output (R/Python) is NOT affected by language policy
#
# Usage in R templates:
#   cat(t("header.blank_altman_width"), "\n")
#   cat(t("label.sd_diff"), sd_diff, "\n")
# =============================================================================

# ── Locale detection / 系统语言检测 ──
.is_chinese <- function() {
  # Check environment variables (works on all platforms)
  for (var in c("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")) {
    val <- Sys.getenv(var, unset = "")
    if (tolower(substr(val, 1, 2)) == "zh") return(TRUE)
  }
  # Windows: check Get-UICulture
  if (.Platform$OS.type == "windows") {
    tryCatch({
      cmd <- "powershell -NoProfile -Command (Get-UICulture).Name"
      val <- tolower(trimws(system(cmd, intern = TRUE)))
      if (substr(val, 1, 2) == "zh") return(TRUE)
    }, error = function(e) NULL)
  }
  FALSE
}

.t_lang <- if (.is_chinese()) "zh" else "en"

# ── Message dictionary / 消息字典 ──
.messages <- list(
  # ── Section headers / 分节标题 ──
  header.blank_altman_width = list(
    en = "\n========== Bland-Altman (Width given N) ==========",
    zh = "\n========== Bland-Altman (给定 N 求宽度) =========="
  ),
  header.blank_altman_n = list(
    en = "\n========== Bland-Altman Method Comparison ==========",
    zh = "\n========== Bland-Altman 方法比较 =========="
  ),
  header.equivalence_means_power = list(
    en = "\n========== Equivalence (Means, Power given N) ==========",
    zh = "\n========== 等效性 (均值, 给定 N 求功效) =========="
  ),
  header.equivalence_means_n = list(
    en = "\n========== Equivalence (Two Means) ==========",
    zh = "\n========== 等效性 (两均值) =========="
  ),
  header.bioequivalence_power = list(
    en = "\n========== Bioequivalence (Power given N) ==========",
    zh = "\n========== 生物等效性 (给定 N 求功效) =========="
  ),
  header.bioequivalence_n = list(
    en = "\n========== Bioequivalence (TOST) ==========",
    zh = "\n========== 生物等效性 (TOST) =========="
  ),
  header.superiority_margin_power = list(
    en = "\n========== Superiority by a Margin (Power given N) ==========",
    zh = "\n========== 优效性 (给定界值, 给定 N 求功效) =========="
  ),
  header.superiority_margin_n = list(
    en = "\n========== Superiority by a Margin ==========",
    zh = "\n========== 优效性 (给定界值) =========="
  ),
  header.mixed_model_power = list(
    en = "\n========== Mixed Model Power (given N) ==========",
    zh = "\n========== 混合模型功效 (给定 N) =========="
  ),
  header.mixed_model_n = list(
    en = "\n========== Mixed Model Power ==========",
    zh = "\n========== 混合模型功效 =========="
  ),
  header.mixed_model_curve = list(
    en = "\n--- Power Curve (to find n for target power %s) ---",
    zh = "\n--- 功效曲线 (寻找达到目标功效 %s 的 n) ---"
  ),
  header.ni_survival_power = list(
    en = "\n========== NI Survival (Power given N, approx) ==========",
    zh = "\n========== 非劣效生存 (给定 N 求功效, 近似) =========="
  ),
  header.ni_survival_n = list(
    en = "\n========== Non-Inferiority Survival ==========",
    zh = "\n========== 非劣效生存设计 =========="
  ),
  header.survival_exact_power = list(
    en = "\n========== Survival Design (Exact, Power given N) ==========",
    zh = "\n========== 生存设计 (精确, 给定 N 求功效) =========="
  ),
  header.survival_exact_n = list(
    en = "\n========== Survival Design (Exact, rpact) ==========",
    zh = "\n========== 生存设计 (精确, rpact) =========="
  ),
  header.dose_escalation = list(
    en = "\n========== Dose Escalation (3+3 / CRM) ==========",
    zh = "\n========== 剂量递增 (3+3 / CRM) =========="
  ),
  header.win_ratio_power = list(
    en = "\n========== Win-Ratio (Power given N) ==========",
    zh = "\n========== 胜率 (给定 N 求功效) =========="
  ),
  header.win_ratio_n = list(
    en = "\n========== Win-Ratio Composite Endpoint ==========",
    zh = "\n========== 胜率复合终点 =========="
  ),
  header.must_win_power = list(
    en = "\n========== Must-Win / Co-Primary (Power given N) ==========",
    zh = "\n========== 必须赢 / 共主要终点 (给定 N 求功效) =========="
  ),
  header.must_win_n = list(
    en = "\n========== Must-Win / Co-Primary Endpoints ==========",
    zh = "\n========== 必须赢 / 共主要终点 =========="
  ),
  header.dunnett_power = list(
    en = "\n========== Dunnett (Power given N) ==========",
    zh = "\n========== Dunnett 比较 (给定 N 求功效) =========="
  ),
  header.dunnett_n = list(
    en = "\n========== Dunnett Comparisons ==========",
    zh = "\n========== Dunnett 比较 =========="
  ),
  header.mediation_power = list(
    en = "\n========== Mediation (Power given N) ==========",
    zh = "\n========== 中介效应 (给定 N 求功效) =========="
  ),
  header.mediation_n = list(
    en = "\n========== Mediation Effects ==========",
    zh = "\n========== 中介效应 =========="
  ),
  header.group_sequential_power = list(
    en = "\n========== Group Sequential (Power given N) ==========",
    zh = "\n========== 成组序贯 (给定 N 求功效) =========="
  ),
  header.group_sequential_n = list(
    en = "\n========== Group Sequential Design ==========",
    zh = "\n========== 成组序贯设计 =========="
  ),
  header.prior_power = list(
    en = "\n========== Prior-informed Sample Size (Power given N) ==========",
    zh = "\n========== 先验信息样本量 (给定 N 求功效) =========="
  ),
  header.prior_n = list(
    en = "\n========== Prior-informed Sample Size ==========",
    zh = "\n========== 先验信息样本量 =========="
  ),
  header.mams_power = list(
    en = "\n========== MAMS (Power given N) ==========",
    zh = "\n========== MAMS (给定 N 求功效) =========="
  ),
  header.mams_n = list(
    en = "\n========== Multi-Arm Multi-Stage (MAMS) ==========",
    zh = "\n========== 多臂多阶段 (MAMS) =========="
  ),
  header.historical_power = list(
    en = "\n========== Historical Controls (Power given N) ==========",
    zh = "\n========== 历史对照 (给定 N 求功效) =========="
  ),
  header.historical_n = list(
    en = "\n========== Historical Controls (MAP Borrowing) ==========",
    zh = "\n========== 历史对照 (MAP 借用) =========="
  ),
  header.adaptive_power = list(
    en = "\n========== Adaptive Design (Power given N) ==========",
    zh = "\n========== 适应性设计 (给定 N 求功效) =========="
  ),
  header.adaptive_n = list(
    en = "\n========== Adaptive Design ==========",
    zh = "\n========== 适应性设计 =========="
  ),
  header.bayesian_assurance = list(
    en = "\n========== Bayesian Assurance ==========",
    zh = "\n========== 贝叶斯保证度 =========="
  ),
  header.conditional_power = list(
    en = "\n========== Conditional Power / SSR ==========",
    zh = "\n========== 条件功效 / 样本量再估计 =========="
  ),

  # ── Labels / 标签 ──
  label.sd_diff = list(en = "SD diff:", zh = "差值 SD:"),
  label.sample_size_pairs = list(en = "Sample size (pairs):", zh = "样本量 (对子数):"),
  label.achievable_half_width = list(en = "Achievable half-width w:", zh = "可达半宽 w:"),
  label.precision_note = list(
    en = "Note: This is a precision (CI width) calc, not a hypothesis power calc.",
    zh = "注：这是精度 (CI 宽度) 计算，不是假设检验功效计算。"
  ),
  label.w = list(en = "w:", zh = "w:"),
  label.alpha = list(en = "Alpha:", zh = "Alpha:"),
  label.equivalence_margin = list(en = "Equivalence margin delta:", zh = "等效性界值 delta:"),
  label.sigma = list(en = "Sigma:", zh = "Sigma:"),
  label.total_n = list(en = "Total N:", zh = "总 N:"),
  label.per_arm = list(en = "per arm:", zh = "每组:"),
  label.achieved_power = list(en = "Achieved power:", zh = "达成功效:"),
  label.achieved_power_approx = list(en = "Achieved power (approx):", zh = "达成功效 (近似):"),
  label.n_per_group = list(en = "n per group:", zh = "每组 n:"),
  label.theta0 = list(en = "theta0:", zh = "theta0:"),
  label.cv = list(en = "CV:", zh = "CV:"),
  label.design = list(en = "design:", zh = "设计:"),
  label.n_per_sequence = list(en = "n per sequence:", zh = "每组序列 n:"),
  label.sample_size = list(en = "Sample size:", zh = "样本量:"),
  label.superiority_margin = list(en = "Superiority margin:", zh = "优效性界值:"),
  label.control_rate = list(en = "Control rate:", zh = "对照组率:"),
  label.treatment_rate = list(en = "Treatment rate:", zh = "处理组率:"),
  label.excess_over_margin = list(en = "Excess over margin (delta_sup - sup_margin):", zh = "超出界值 (delta_sup - sup_margin):"),
  label.trialsize_n = list(en = "TrialSize N per group:", zh = "TrialSize 每组 N:"),
  label.effect = list(en = "Effect:", zh = "效应:"),
  label.n_subjects = list(en = "n subjects:", zh = "n 受试者:"),
  label.ni_margin_hr = list(en = "NI margin (HR):", zh = "非劣效界值 (HR):"),
  label.approx_events = list(en = "Approx events per group:", zh = "近似每组事件数:"),
  label.expected_hr = list(en = "Expected HR:", zh = "预期 HR:"),
  label.accrual = list(en = "Accrual (months):", zh = "入组 (月):"),
  label.followup = list(en = "Follow-up (months):", zh = "随访 (月):"),
  label.event_rate = list(en = "Event rate (control):", zh = "事件率 (对照组):"),
  label.power = list(en = "Power:", zh = "功效:"),
  label.events_required = list(en = "Events required:", zh = "所需事件数:"),
  label.hazard_ratio = list(en = "Hazard ratio:", zh = "风险比:"),
  label.dropout = list(en = "Dropout (annual):", zh = "脱落 (年):"),
  label.dose_levels = list(en = "Dose levels:", zh = "剂量水平:"),
  label.target_dlt = list(en = "Target DLT:", zh = "目标 DLT:"),
  label.approx_total_3_3 = list(en = "Given total N =", zh = "给定总 N ="),
  label.power_not_applicable = list(
    en = "A power calculation does not apply to this design.",
    zh = "该设计不适用功效计算。"
  ),
  label.expected_win_ratio = list(en = "Expected Win-Ratio:", zh = "预期胜率:"),
  label.se_approx = list(en = "SE approximation:", zh = "SE 近似:"),
  label.win_ratio_note = list(
    en = "\nNote: This is an approximation. For a precise design use\n      BuyseTest::powerBuyseTest() with actual event-time data.",
    zh = "\n注：这是近似计算。精确设计请使用 BuyseTest::powerBuyseTest() 配合实际事件时间数据。"
  ),
  label.n_co_primary = list(en = "Number of co-primary endpoints:", zh = "共主要终点数:"),
  label.assumed_correlation = list(en = "Assumed correlation:", zh = "假设相关:"),
  label.effect_per_endpoint = list(en = "Effect size per endpoint:", zh = "每个终点的效应量:"),
  label.overall_power = list(en = "Overall power:", zh = "总功效:"),
  label.overall_alpha = list(en = "Overall alpha:", zh = "总 alpha:"),
  label.n_inflated = list(en = "N per group (inflated):", zh = "每组 N (膨胀后):"),
  label.n_treatment_arm = list(en = "N per treatment arm:", zh = "每个处理臂 N:"),
  label.control_n = list(en = "Control group N:", zh = "对照组 N:"),
  label.n_groups = list(en = "Number of treatment arms:", zh = "处理臂数:"),
  label.indirect_effect = list(en = "Indirect effect (a*b):", zh = "间接效应 (a*b):"),
  label.sobel_se = list(en = "Sobel SE:", zh = "Sobel SE:"),
  label.a_path = list(en = "a-path (treatment -> mediator):", zh = "a 路径 (处理 -> 中介):"),
  label.b_path = list(en = "b-path (mediator -> outcome):", zh = "b 路径 (中介 -> 结局):"),
  label.n_sobel = list(en = "N (Sobel approximation):", zh = "N (Sobel 近似):"),
  label.n_looks = list(en = "Number of looks:", zh = "分析次数:"),
  label.interim = list(en = "interim)", zh = "中期分析)"),
  label.spending_function = list(en = "Spending function:", zh = "消耗函数:"),
  label.effect_size = list(en = "Effect size:", zh = "效应量:"),
  label.n_per_group_final = list(en = "N per group (at final look, approx):", zh = "每组 N (最终分析, 近似):"),
  label.method = list(en = "Method:", zh = "方法:"),
  label.prior_a0 = list(en = "Prior a0 (informational, not used in calc):", zh = "先验 a0 (信息性, 不参与计算):"),
  label.effective_n = list(en = "Effective n per group:", zh = "有效每组 n:"),
  label.n_arms_mams = list(en = "Number of treatment arms:", zh = "处理臂数:"),
  label.n_stages_mams = list(en = "Number of stages:", zh = "阶段数:"),
  label.alpha_adjusted = list(en = "Alpha adjusted (Bonferroni):", zh = "调整后 Alpha (Bonferroni):"),
  label.historical_response = list(en = "Historical response:", zh = "历史反应率:"),
  label.current_control_rate = list(en = "Current control rate:", zh = "当前对照组率:"),
  label.expected_treatment_rate = list(en = "Expected treatment rate:", zh = "预期处理组率:"),
  label.n_with_borrowing = list(en = "N with borrowing:", zh = "借用后 N:"),
  label.adaptive_type = list(en = "Type:", zh = "类型:"),
  label.stages = list(en = "Stages:", zh = "阶段数:"),
  label.use_rpact = list(
    en = "Use rpact::getDesignInverseNormal() / getSimulationMeans() for this type.",
    zh = "该类型请使用 rpact::getDesignInverseNormal() / getSimulationMeans()。"
  ),
  label.max_n_ssr = list(en = "Max N (adaptive SSR, approx):", zh = "最大 N (适应性 SSR, 近似):"),
  label.per_group = list(en = "per group:", zh = "每组:"),
  label.treatment_prior = list(en = "Treatment prior: Beta(", zh = "处理组先验: Beta("),
  label.control_prior = list(en = "Control prior: Beta(", zh = "对照组先验: Beta("),
  label.n_per_group_assurance = list(en = "N per group:", zh = "每组 N:"),
  label.success_margin = list(en = "Success margin:", zh = "成功界值:"),
  label.n_simulations = list(en = "Number of simulations:", zh = "模拟次数:"),
  label.assurance = list(en = "Assurance (P(success)):", zh = "保证度 (P(成功)):"),
  label.assurance_note = list(
    en = "\nNote: Search multiple N values to find target assurance (e.g., 80%).",
    zh = "\n注：搜索多个 N 值以找到目标保证度 (如 80%)。"
  ),
  label.planned_effect = list(en = "Planned effect:", zh = "计划效应:"),
  label.observed_effect = list(en = "Observed effect at interim:", zh = "中期观察效应:"),
  label.interim_timing = list(en = "Interim timing:", zh = "中期时机:"),
  label.conditional_power_label = list(en = "Conditional power (H1):", zh = "条件功效 (H1):"),
  label.planned_n = list(en = "Planned N:", zh = "计划 N:"),
  label.reestimated_n = list(en = "Re-estimated N:", zh = "再估计 N:"),
  label.ssr_increase = list(en = "SSR increase:", zh = "SSR 增加:"),
  label.ssr_warning = list(
    en = "\nWarning: Observed effect is zero or negative - SSR not recommended.",
    zh = "\n警告：观察效应为零或负值 — 不推荐 SSR。"
  ),
  label.cp_na = list(en = "Conditional power: N/A (effect <= 0)", zh = "条件功效: 不适用 (效应 <= 0)"),
  label.png_saved = list(en = "PNG saved to", zh = "PNG 已保存至"),
  label.rpact_note = list(
    en = "(Use rpact::getDesignMAMS for exact calculations with selection rules)",
    zh = "(使用 rpact::getDesignMAMS 进行含选择规则的精确计算)"
  ),
  label.n = list(en = "N:", zh = "N:"),
  # ── v3.5.0 PASS-survival extensions / PASS 生存扩展 ──
  r_header.surv_equiv_power = list(en = "\n========== Survival Equivalence (Power given N) ==========", zh = "\n========== 生存等效 (给定 N 求功效) =========="),
  r_header.surv_equiv_n = list(en = "\n========== Survival Equivalence (TOST on HR) ==========", zh = "\n========== 生存等效 (HR 等效性 TOST) =========="),
  r_header.surv_sup_power = list(en = "\n========== Survival Superiority by Margin (Power given N) ==========", zh = "\n========== 生存优效含界值 (给定 N 求功效) =========="),
  r_header.surv_sup_n = list(en = "\n========== Survival Superiority by Margin ==========", zh = "\n========== 生存优效含界值 =========="),
  r_header.cox_cov_power = list(en = "\n========== Cox Covariate Power (Power given N) ==========", zh = "\n========== Cox 协变量功效 (给定 N 求功效) =========="),
  r_header.cox_cov_n = list(en = "\n========== Cox Covariate Power (Vittinghoff) ==========", zh = "\n========== Cox 协变量功效 (Vittinghoff 法) =========="),
  r_header.onesample_surv_power = list(en = "\n========== One-Sample Exponential (Power given N) ==========", zh = "\n========== 单样本指数 (给定 N 求功效) =========="),
  r_header.onesample_surv_n = list(en = "\n========== One-Sample Exponential Survival ==========", zh = "\n========== 单样本指数生存 =========="),
  r_header.comprisk_power = list(en = "\n========== Competing Risks (Power given N) ==========", zh = "\n========== 竞争风险 (给定 N 求功效) =========="),
  r_header.comprisk_n = list(en = "\n========== Competing Risks (Cumulative Incidence) ==========", zh = "\n========== 竞争风险 (累积发生率) =========="),
  r_header.recur_power = list(en = "\n========== Recurrent Events (Power given N) ==========", zh = "\n========== 复发事件 (给定 N 求功效) =========="),
  r_header.recur_n = list(en = "\n========== Recurrent Events (Andersen-Gill) ==========", zh = "\n========== 复发事件 (Andersen-Gill) =========="),
  r_header.histctrl_power = list(en = "\n========== Historical Control (Power given N) ==========", zh = "\n========== 历史对照 (给定 N 求功效) =========="),
  r_header.histctrl_n = list(en = "\n========== Historical Control Log-Rank ==========", zh = "\n========== 历史对照 Log-Rank =========="),
  label.eq_margin_hr = list(en = "Equivalence margin (HR):", zh = "等效界值 (HR):"),
  label.sup_margin_hr = list(en = "Superiority margin (HR):", zh = "优效界值 (HR):"),
  label.cox_hr = list(en = "Covariate HR:", zh = "协变量 HR:"),
  label.cox_r2 = list(en = "R^2 (other covariates):", zh = "R² (其它协变量):"),
  label.cox_prev = list(en = "Covariate prevalence:", zh = "协变量患病率:"),
  label.cox_event_prop = list(en = "Expected event proportion:", zh = "预期事件比例:"),
  label.events_needed = list(en = "Required events (d):", zh = "所需事件数 (d):"),
  label.median0 = list(en = "Null median survival:", zh = "原假设中位生存:"),
  label.median1 = list(en = "Alternative median survival:", zh = "备择中位生存:"),
  label.hazard0 = list(en = "Null hazard (lambda0):", zh = "原假设风险率 (λ0):"),
  label.hazard1 = list(en = "Alternative hazard (lambda1):", zh = "备择风险率 (λ1):"),
  label.events_h0 = list(en = "Expected events under H0:", zh = "H0 下预期事件数:"),
  label.events_h1 = list(en = "Expected events under H1:", zh = "H1 下预期事件数:"),
  label.ci_control = list(en = "Cumulative incidence (control):", zh = "累积发生率 (对照):"),
  label.ci_treatment = list(en = "Cumulative incidence (treatment):", zh = "累积发生率 (治疗):"),
  label.rate_control = list(en = "Recurrent-event rate (control, /py):", zh = "复发事件率 (对照, /人年):"),
  label.rate_ratio = list(en = "Rate ratio:", zh = "率比:"),
  label.recur_followup = list(en = "Follow-up (years):", zh = "随访时间 (年):"),
  label.person_time = list(en = "Person-time per group:", zh = "每组人年:"),
  label.hist_median = list(en = "Historical control median:", zh = "历史对照中位:"),
  label.new_median = list(en = "New-arm median:", zh = "新臂中位:"),
  label.hist_n = list(en = "Historical control n:", zh = "历史对照样本量:"),
  label.total_with_dropout = list(en = "Total N (with dropout):", zh = "总 N (含脱落):"),
  header.gsd_proportion_power = list(en = "GROUP-SEQUENTIAL TWO PROPORTIONS -- POWER", zh = "成组序贯·两比例 -- 效能"),
  header.gsd_proportion_n = list(en = "GROUP-SEQUENTIAL TWO PROPORTIONS -- SAMPLE SIZE", zh = "成组序贯·两比例 -- 样本量"),
  header.gsd_survival_power = list(en = "GROUP-SEQUENTIAL SURVIVAL -- POWER", zh = "成组序贯·生存 -- 效能"),
  header.gsd_survival_n = list(en = "GROUP-SEQUENTIAL SURVIVAL -- SAMPLE SIZE", zh = "成组序贯·生存 -- 样本量"),
  header.gsd_hazard_power = list(en = "GROUP-SEQUENTIAL HAZARD RATE -- POWER", zh = "成组序贯·风险率 -- 效能"),
  header.gsd_hazard_n = list(en = "GROUP-SEQUENTIAL HAZARD RATE -- SAMPLE SIZE", zh = "成组序贯·风险率 -- 样本量"),
  header.gsd_poisson_power = list(en = "GROUP-SEQUENTIAL POISSON RATE -- POWER", zh = "成组序贯·Poisson 率 -- 效能"),
  header.gsd_poisson_n = list(en = "GROUP-SEQUENTIAL POISSON RATE -- SAMPLE SIZE", zh = "成组序贯·Poisson 率 -- 样本量"),
  label.p1 = list(en = "P1 (control):", zh = "P1 (对照):"),
  label.p2 = list(en = "P2 (treatment):", zh = "P2 (治疗):"),
  label.proportion_metric = list(en = "Metric:", zh = "度量:"),
  label.rate1 = list(en = "Lambda1 (treatment):", zh = "λ1 (治疗):"),
  label.rate2 = list(en = "Lambda2 (control):", zh = "λ2 (对照):"),
  label.adjusted_n = list(en = "Adjusted n:", zh = "调整后 n:"),
  label.adjusted_n_per_group = list(en = "Adjusted n per group:", zh = "调整后每组 n:"),
  label.adjusted_total = list(en = "Adjusted total:", zh = "调整后总样本量:"),
  label.approx_n_per_group_surv = list(en = "Approx n per group (event_rate=%s):", zh = "近似每组 n (event_rate=%s):"),
  label.assumed_diff = list(en = "假设真实差异 |p1-p2|: ", zh = "假设真实差异 |p1-p2|: "),
  label.cluster_size_m = list(en = "Cluster size m:", zh = "群组大小 m:"),
  label.clusters_per_group = list(en = "Clusters per group:", zh = "群组数 (每组):"),
  label.cohens_d = list(en = "Cohen's d:", zh = "Cohen's d:"),
  label.control_h0 = list(en = "Control / H0 (p1):", zh = "对照组 / H0 (p1):"),
  label.control_rate_ni = list(en = "对照组有效率 p1:", zh = "对照组有效率 p1:"),
  label.control_rate_ni_short = list(en = "对照组有效率 p1: %s", zh = "对照组有效率 p1: %s"),
  label.correlation = list(en = "Correlation:", zh = "相关系数:"),
  label.deff = list(en = "Design effect (DEFF):", zh = "设计效应 (DEFF):"),
  label.dropout_note_inline = list(en = "含10%%脱落率:", zh = "含10%%脱落率:"),
  label.each_group = list(en = "每组:", zh = "每组:"),
  label.each_group_n = list(en = "Each group n:", zh = "每组 n:"),
  label.effective_n_per_group = list(en = "Effective individual n per group (n_total/2/DEFF):", zh = "有效个体 n 每组 (总 n/2/DEFF):"),
  label.f_effect = list(en = "f:", zh = "f:"),
  label.given_n = list(en = "Given n:", zh = "给定 n:"),
  label.given_n_per_group = list(en = "Given n per group:", zh = "给定每组 n:"),
  label.h0_auc = list(en = "H0 AUC:", zh = "H0 AUC:"),
  label.h0_proportion = list(en = "H0 proportion (p0):", zh = "H0 率 (p0):"),
  label.h1_auc = list(en = "H1 AUC:", zh = "H1 AUC:"),
  label.h1_proportion = list(en = "H1 proportion (p1):", zh = "H1 率 (p1):"),
  label.hazard_ratio_surv = list(en = "Hazard ratio:", zh = "风险比:"),
  label.icc = list(en = "ICC:", zh = "ICC:"),
  label.implied_n_clusters = list(en = "Implied n clusters per group:", zh = "隐含群组数 (每组):"),
  label.k_groups = list(en = "k groups:", zh = "k 组:"),
  label.n_pairs = list(en = "n (pairs):", zh = "n (对子数):"),
  label.n_per_arm = list(en = "每组样本量 n1:", zh = "每组样本量 n1:"),
  label.n_per_group_total = list(en = "n per group:", zh = "每组 n:"),
  label.n_total = list(en = "n:", zh = "n:"),
  label.n_total_result = list(en = "n (total):", zh = "n (合计):"),
  label.ni_margin = list(en = "非劣效界值 delta:", zh = "非劣效界值 delta:"),
  label.ni_margin_short = list(en = "非劣效界值 delta: %s", zh = "非劣效界值 delta: %s"),
  label.one_sided_alpha = list(en = "单侧 α: %s, 把握度: %s, 1:1 分配", zh = "单侧 α: %s, 把握度: %s, 1:1 分配"),
  label.result_header = list(en = "--- 结果 ---", zh = "--- 结果 ---"),
  label.sample_size_per_group = list(en = "Sample size per group:", zh = "每组样本量:"),
  label.side = list(en = "Side:", zh = "单/双侧:"),
  label.single_endpoint_n = list(en = "Single endpoint n:", zh = "单终点 n:"),
  label.survival_note = list(en = "
注意: 当前仅计算所需事件数。如需样本量请提供参数", zh = "
注意: 当前仅计算所需事件数。如需样本量请提供参数"),
  label.target_power = list(en = "Target power:", zh = "目标功效:"),
  label.total_clusters = list(en = "Total:", zh = "总群组数:"),
  label.total_events = list(en = "Total events:", zh = "总事件数:"),
  label.total_events_needed = list(en = "Total events needed (Schoenfeld):", zh = "所需总事件数 (Schoenfeld):"),
  label.total_n_ni = list(en = "总样本量 N:", zh = "总样本量 N:"),
  label.total_n_surv = list(en = "Total N:", zh = "总 N:"),
  label.total_sample_size = list(en = "Total sample size:", zh = "总样本量:"),
  label.total_sample_size_result = list(en = "总样本量 N:", zh = "总样本量 N:"),
  label.treatment_h1 = list(en = "Treatment / H1 (p2):", zh = "处理组 / H1 (p2):"),
  label.treatment_rate_ni = list(en = "试验组有效率 p2:", zh = "试验组有效率 p2:"),
  label.treatment_rate_ni_short = list(en = "试验组有效率 p2: %s", zh = "试验组有效率 p2: %s"),
  label.ve = list(en = "VE:", zh = "VE:"),
  label.with_dropout = list(en = "含 10%% 脱落率:", zh = "含 10%% 脱落率:"),
  r_header.roc_n = list(en = "
========== ROC Sample Size ==========", zh = "
========== ROC 样本量 =========="),
  r_header.roc_power = list(en = "
========== ROC Sample Size (Power given N) ==========", zh = "
========== ROC 样本量 (给定 N 求功效) =========="),
  label.planned_events = list(en = "Planned events per stage:", zh = "各阶段计划事件数:"),
  label.expected_n = list(en = "Expected total N:", zh = "预期总样本量:"),
  label.expected_events = list(en = "Expected events:", zh = "预期事件数:"),
  label.empirical_power = list(en = "Empirical power (sim):", zh = "经验功效 (模拟):"),
  label.stop_prob = list(en = "Stage-wise reject probabilities:", zh = "各阶段拒绝概率:"),
  header.gsd_survival_sim = list(en = "GROUP-SEQUENTIAL SURVIVAL -- MONTE-CARLO SIMULATION", zh = "成组序贯·生存 -- 蒙特卡洛模拟"),
  header.gsd_hazard_sim = list(en = "GROUP-SEQUENTIAL HAZARD RATE -- MONTE-CARLO SIMULATION", zh = "成组序贯·风险率 -- 蒙特卡洛模拟"),

  # ── PASS-coverage extension (v5.9 / v5.10): headers ──
  header.correlation = list(en = "\n========== Correlation Test ==========", zh = "\n========== 相关检验 =========="),
  header.variance_one = list(en = "\n========== One-Sample Variance Test ==========", zh = "\n========== 单样本方差检验 =========="),
  header.variance_two = list(en = "\n========== Two-Sample Variance Ratio Test ==========", zh = "\n========== 两样本方差比检验 =========="),
  header.cv_one = list(en = "\n========== Coefficient of Variation Precision ==========", zh = "\n========== 变异系数精度 =========="),
  header.ci_mean = list(en = "\n========== CI for a Mean ==========", zh = "\n========== 均值置信区间 =========="),
  header.ci_prop = list(en = "\n========== CI for a Proportion ==========", zh = "\n========== 比例置信区间 =========="),
  header.ci_or = list(en = "\n========== CI for an Odds Ratio ==========", zh = "\n========== 优势比置信区间 =========="),
  header.ci_rr = list(en = "\n========== CI for a Risk Ratio ==========", zh = "\n========== 风险比置信区间 =========="),
  header.ci_cor = list(en = "\n========== CI for a Correlation ==========", zh = "\n========== 相关系数置信区间 =========="),
  header.ci_icc = list(en = "\n========== CI for an ICC ==========", zh = "\n========== 组内相关系数置信区间 =========="),
  header.regression_linear = list(en = "\n========== Multiple Linear Regression ==========", zh = "\n========== 多重线性回归 =========="),
  header.meta_planning = list(en = "\n========== Meta-Analysis Planning ==========", zh = "\n========== Meta 分析前瞻规划 =========="),
  header.regression_logistic = list(en = "\n========== Logistic Regression ==========", zh = "\n========== 逻辑回归 =========="),
  header.regression_poisson = list(en = "\n========== Poisson Regression ==========", zh = "\n========== 泊松回归 =========="),
  header.cluster_ext = list(en = "\n========== Cluster-Randomized (Generalized DEFF) ==========", zh = "\n========== 整群随机化（广义设计效应）=========="),
  header.rates_ext = list(en = "\n========== Rates (Over-dispersion / Precision) ==========", zh = "\n========== 率（过离散 / 精度）=========="),

  # ── PASS-coverage extension (v5.9 / v5.10): labels ──
  label.corr_r = list(en = "Correlation r:", zh = "相关系数 r:"),
  label.half_width = list(en = "Target half-width:", zh = "目标半宽:"),
  label.rel_error = list(en = "Relative error:", zh = "相对误差:"),
  label.sd0 = list(en = "SD under H0:", zh = "H0 下 SD:"),
  label.sd1 = list(en = "SD under H1:", zh = "H1 下 SD:"),
  label.var_ratio = list(en = "Variance ratio:", zh = "方差比:"),
  label.f2 = list(en = "Cohen's f2:", zh = "Cohen's f2:"),
  label.u_pred = list(en = "Predictors u:", zh = "预测变量数 u:"),
  label.effect_type = list(en = "Meta effect type:", zh = "Meta 效应类型:"),
  label.n_per_study = list(en = "n per study:", zh = "每研究 n:"),
  label.i2 = list(en = "Heterogeneity I2:", zh = "异质性 I2:"),
  label.meta_R = list(en = "R (between/within):", zh = "R (异质性比 组间/组内):"),
  label.meta_effect0 = list(en = "Effect under H0:", zh = "H0 效应量:"),
  label.meta_cov = list(en = "Cluster-size CV (COV):", zh = "簇大小变异系数 (COV):"),
  label.meta_de = list(en = "Design effect (DE):", zh = "设计效应 (DE):"),
  label.meta_n_eff = list(en = "Effective N per study:", zh = "每研究有效样本 N':"),
  label.meta_het_sweep = list(en = "Required K by heterogeneity (I2 -> K):", zh = "不同异质性水平所需研究数（I2 -> K）:"),
  label.k_studies = list(en = "Studies needed (K):", zh = "所需研究数 (K):"),
  label.baseline_rate = list(en = "Baseline rate p0:", zh = "基线率 p0:"),
  label.odds_ratio = list(en = "Odds ratio:", zh = "优势比:"),
  label.covariate_type = list(en = "Covariate type:", zh = "协变量类型:"),
  label.r2 = list(en = "R2 (other covariates):", zh = "R² (其它协变量):"),
  label.px1 = list(en = "P(X=1):", zh = "P(X=1):"),
  label.overdispersion = list(en = "Over-dispersion phi:", zh = "过离散 phi:"),
  label.cv_cluster = list(en = "Cluster-size CV:", zh = "簇大小 CV:"),
  label.rate_mode = list(en = "Rate mode:", zh = "率模式:"),
  label.person_time = list(en = "Person-time:", zh = "人时:"),
  label.n_clusters = list(en = "Clusters:", zh = "簇数:"),
  label.n_indiv = list(en = "Individuals per group (raw):", zh = "每组个体数 (原始):"),
  label.effective_n = list(en = "Effective n per group:", zh = "有效每组 n:"),
  label.icc_k = list(en = "ICC / raters k:", zh = "ICC / 评价者数 k:"),
  label.p0 = list(en = "Baseline proportion p0:", zh = "基线比例 p0:"),
  label.achieved_half_width = list(en = "Achieved half-width:", zh = "达成半宽:"),
  label.mu_x = list(en = "Covariate mean mu_x:", zh = "协变量均值 mu_x:"),
  label.sd_x = list(en = "Covariate SD:", zh = "协变量 SD:"),
  label.exposure = list(en = "Exposure time:", zh = "暴露时间:"),
  label.phi = list(en = "Over-dispersion phi:", zh = "过离散 phi:"),
  label.prec_level = list(en = "Precision level:", zh = "精度水平:"),
  label.n1_result = list(en = "n1 (group 1):", zh = "n1 (组 1):"),
  label.n2_result = list(en = "n2 (group 2):", zh = "n2 (组 2):"),
  label.cluster_m = list(en = "Cluster size m:", zh = "簇大小 m:")
)

# ── Translation function / 翻译函数 ──
t <- function(key, ...) {
  entry <- .messages[[key]]
  if (is.null(entry)) return(key)
  text <- if (!is.null(entry[[.t_lang]])) entry[[.t_lang]] else entry[["en"]]
  if (length(list(...)) > 0) {
    tryCatch(do.call(sprintf, c(text, list(...))), error = function(e) text)
  } else {
    text
  }
}

# R-side alias for the Python _qt() helper used by generated cat() lines.
# Python: _qt(key, **kw) -> escaped "string literal" (for f-strings).
# R:     generated code emits cat(._qt("label.xxx"), ...) -> resolve to t().
._qt <- function(key, ...) {
  t(key, ...)
}
"""
ADAPTIVE_SIM_R = r"""
# =============================================================================
# adaptive_sim.R -- Adaptive / group-sequential trial Monte-Carlo simulator
#                   (pure base R; no extra packages required)
#
# Ported from ct-samplesize scripts/adaptive_simulator.py so it runs anywhere
# R is installed, independently of the Python CLI.
#
# ----------------------------------------------------------------------------
# How to use in R  /  在 R 中如何使用
# ----------------------------------------------------------------------------
#   # 1. Source this file once
#   source("path/to/adaptive_sim.R")
#
#   # 2a. Call a specific design function directly (returns a list you can reuse)
#   res <- simulate_group_sequential(effect_size = 0.3, n_per_arm = 200,
#                                     interim_looks = 3, spending = "obrien_fleming",
#                                     alpha = 0.025, n_sim = 20000, seed = 42)
#   res$power                 # empirical power
#   res$type_i_error          # empirical Type I error
#   res$design_config         # echoes inputs + computed Z boundaries
#
#   # 2b. Or use the one-shot dispatcher (prints a report; optional PNG / JSON)
#   run_adaptive_sim(design = "group_sequential", effect_size = 0.3,
#                    n_per_arm = 200, interim_looks = 3, alpha = 0.025,
#                    n_simulations = 20000, seed = 42, visualize = TRUE)
#
# Designs : "group_sequential", "adaptive_reestimate", "drop_the_loser"
# Spending: "obrien_fleming", "pocock", "power_family"
# =============================================================================

cumulative_spend <- function(t, total, func, rho = 3.0) {
  t <- max(min(t, 1.0), 1e-9)
  if (func == "obrien_fleming") {
    z <- qnorm(1 - total / 2)
    return(2 * (1 - pnorm(z / sqrt(t))))
  } else if (func == "pocock") {
    return(total * log(1 + (exp(1) - 1) * t))
  } else if (func == "power_family") {
    return(total * t ^ rho)
  }
  stop("unknown spending function: ", func)
}

incremental <- function(times, total, func, rho) {
  cum <- sapply(times, function(tt) cumulative_spend(tt, total, func, rho))
  inc <- cum - c(0, cum[-length(cum)])
  pmax(inc, 1e-12)
}

efficacy_boundaries <- function(times, alpha, func = "obrien_fleming", rho = 3.0, ngrid = 1200) {
  times <- as.numeric(times)
  K <- length(times)
  inc <- incremental(times, alpha, func, rho)
  xmax <- 6.0 * sqrt(times[K])
  x <- seq(-xmax, xmax, length.out = ngrid)
  dx <- x[2] - x[1]
  bounds <- numeric(K)
  v1 <- times[1]
  b1 <- sqrt(v1) * qnorm(1 - inc[1])
  bounds[1] <- b1 / sqrt(v1)
  f <- dnorm(x, 0, sqrt(v1))
  f[x > b1] <- 0
  for (k in seq_len(K - 1L) + 1L) {
    vk <- times[k] - times[k - 1]
    sd_k <- sqrt(vk)
    kern <- outer(x, x, function(a, b) dnorm(a - b, 0, sd_k))
    g <- as.vector((kern %*% f) * dx)
    lo <- -xmax; hi <- xmax
    for (it in 1:60) {
      mid <- 0.5 * (lo + hi)
      if (sum(g[x > mid]) * dx > inc[k]) lo <- mid else hi <- mid
    }
    bk <- 0.5 * (lo + hi)
    bounds[k] <- bk / sqrt(times[k])
    f <- g
    f[x > bk] <- 0
  }
  bounds
}

futility_boundaries <- function(times, beta, drift, func = "power_family", rho = 2.0, ngrid = 1200) {
  times <- as.numeric(times)
  K <- length(times)
  inc <- incremental(times, beta, func, rho)
  xmax <- 6.0 * sqrt(times[K])
  x <- seq(-xmax, xmax, length.out = ngrid)
  dx <- x[2] - x[1]
  bounds <- numeric(K)
  v1 <- times[1]
  a1 <- drift * v1 + sqrt(v1) * qnorm(inc[1])
  bounds[1] <- a1 / sqrt(times[1])
  f <- dnorm(x, drift * v1, sqrt(v1))
  f[x < a1] <- 0
  for (k in seq_len(K - 1L) + 1L) {
    vk <- times[k] - times[k - 1]
    sd_k <- sqrt(vk)
    kern <- outer(x, x, function(a, b) dnorm(a - b, drift * vk, sd_k))
    g <- as.vector((kern %*% f) * dx)
    lo <- -xmax; hi <- xmax
    for (it in 1:60) {
      mid <- 0.5 * (lo + hi)
      if (sum(g[x < mid]) * dx < inc[k]) lo <- mid else hi <- mid
    }
    ak <- 0.5 * (lo + hi)
    bounds[k] <- ak / sqrt(times[k])
    f <- g
    f[x < ak] <- 0
  }
  bounds
}

simulate_group_sequential <- function(effect_size, n_per_arm, interim_looks = 2,
                                       alpha = 0.025, spending = "obrien_fleming",
                                       rho = 3.0, futility = FALSE, beta = 0.2,
                                       n_sim = 10000, seed = NULL) {
  if (!is.null(seed)) set.seed(seed)
  K <- interim_looks
  times <- (1:K) / K
  eff_b <- efficacy_boundaries(times, alpha, spending, rho)
  theta <- effect_size * sqrt(n_per_arm / 2)
  fut_b <- if (futility) futility_boundaries(times, beta, theta, "power_family", 2.0) else NULL
  dt <- diff(c(0, times))
  run_one <- function(drift) {
    Bcur <- rep(0, n_sim)
    stopped <- rep(FALSE, n_sim)
    reject <- rep(FALSE, n_sim)
    stop_look <- rep(K, n_sim)
    stop_kind <- rep(0L, n_sim)
    for (k in 1:K) {
      Bcur <- Bcur + rnorm(n_sim, drift * dt[k], sqrt(dt[k]))
      Zk <- Bcur / sqrt(times[k])
      active <- !stopped
      eff <- active & (Zk > eff_b[k])
      reject[eff] <- TRUE; stopped[eff] <- TRUE; stop_look[eff] <- k; stop_kind[eff] <- 1L
      if (futility && k < K) {
        fut <- active & !eff & (Zk < fut_b[k])
        stopped[fut] <- TRUE; stop_look[fut] <- k; stop_kind[fut] <- 2L
      }
    }
    list(reject = reject, stop_look = stop_look, stop_kind = stop_kind)
  }
  r1 <- run_one(theta)
  r0 <- run_one(0)
  frac <- times[r1$stop_look]
  exp_n_per_arm <- mean(frac * n_per_arm)
  early <- r1$stop_look < K
  list(
    design = "group_sequential",
    power = mean(r1$reject),
    type_i_error = mean(r0$reject),
    expected_sample_size = round(exp_n_per_arm * 2, 2),
    expected_sample_size_per_arm = round(exp_n_per_arm, 2),
    max_sample_size = as.integer(n_per_arm * 2),
    early_stop_rate = list(
      efficacy = mean(early & r1$stop_kind == 1L),
      futility = mean(early & r1$stop_kind == 2L)),
    design_config = list(
      effect_size = effect_size, n_per_arm = n_per_arm, interim_looks = K,
      information_times = round(times, 4), alpha = alpha, spending_function = spending,
      rho = rho, futility = isTRUE(futility), beta = if (futility) beta else NULL,
      efficacy_boundaries_Z = round(eff_b, 4),
      futility_boundaries_Z = if (is.null(fut_b)) NULL else round(fut_b, 4),
      n_simulations = n_sim)
  )
}

simulate_adaptive_reestimate <- function(effect_size, n_per_arm, alpha = 0.025,
                                          interim_fraction = 0.5, cp_min = 0.365,
                                          cp_max = 0.9, target_cp = 0.9,
                                          max_inflation = 2.0, n_sim = 10000,
                                          seed = NULL, reestimate_method = "promising_zone") {
  if (reestimate_method != "promising_zone") stop("only 'promising_zone' is supported")
  if (!is.null(seed)) set.seed(seed)
  z_alpha <- qnorm(1 - alpha)
  n1 <- max(round(interim_fraction * n_per_arm), 2)
  n2_plan <- n_per_arm - n1
  n2_max <- round(n2_plan * max_inflation)
  w1 <- sqrt(n1 / n_per_arm)
  w2 <- sqrt(1 - w1 * w1)
  run_one <- function(true_d) {
    d1 <- rnorm(n_sim, true_d, sqrt(2 / n1))
    z1 <- d1 / sqrt(2 / n1)
    theta_hat <- pmax(d1, 0)
    info2_plan <- n2_plan / 2
    cp <- 1 - pnorm((z_alpha - (w1 * z1 + w2 * (theta_hat * sqrt(info2_plan)))) / w2)
    cp <- pmin(pmax(cp, 0), 1)
    promising <- (cp >= cp_min) & (cp <= cp_max)
    need <- ((qnorm(target_cp) + z_alpha) / pmax(theta_hat, 1e-6)) ^ 2 * 2
    n2_new <- ifelse(promising, pmin(pmax(round(need), n2_plan), n2_max), n2_plan)
    n2_new <- pmax(n2_new, 1)
    d2 <- rnorm(n_sim, true_d, sqrt(2 / n2_new))
    z2 <- d2 / sqrt(2 / n2_new)
    zw <- w1 * z1 + w2 * z2
    reject <- zw > z_alpha
    total_n <- n1 + n2_new
    list(reject = reject, total_n = total_n, promising = promising)
  }
  r1 <- run_one(effect_size)
  r0 <- run_one(0)
  list(
    design = "adaptive_reestimate",
    power = mean(r1$reject),
    type_i_error = mean(r0$reject),
    expected_sample_size = round(mean(r1$total_n) * 2, 2),
    expected_sample_size_per_arm = round(mean(r1$total_n), 2),
    max_sample_size = as.integer((n1 + n2_max) * 2),
    prob_sample_size_increase = mean(r1$promising),
    design_config = list(
      effect_size = effect_size, planned_n_per_arm = n_per_arm, n1_per_arm = n1,
      n2_planned_per_arm = n2_plan, n2_max_per_arm = n2_max, interim_fraction = interim_fraction,
      alpha = alpha, promising_zone = c(cp_min, cp_max), target_cp = target_cp,
      max_inflation = max_inflation, chw_weights = round(c(w1, w2), 4),
      reestimate_method = reestimate_method, n_simulations = n_sim)
  )
}

simulate_drop_the_loser <- function(effect_sizes, n_per_arm, n_arms = NULL, alpha = 0.025,
                                     selection_fraction = 0.5, n_sim = 10000, seed = NULL,
                                     correction = "dunnett") {
  if (!is.null(seed)) set.seed(seed)
  if (length(effect_sizes) == 1 && !is.null(n_arms)) {
    effects <- rep(as.numeric(effect_sizes), n_arms)
  } else {
    effects <- as.numeric(effect_sizes)
  }
  K <- length(effects)
  if (correction == "bonferroni") z_final <- qnorm(1 - alpha / K)
  else z_final <- qnorm((1 - alpha) ^ (1 / K))
  f1 <- selection_fraction
  n1 <- max(round(f1 * n_per_arm), 2)
  info1 <- n1 / 2
  info_full <- n_per_arm / 2
  run_one <- function(effs) {
    Z1 <- matrix(rnorm(n_sim * K, effs * sqrt(info1), 1), n_sim, K)
    winner <- max.col(Z1)
    win_eff <- effs[winner]
    win_z1 <- Z1[cbind(1:n_sim, winner)]
    extra_info <- info_full - info1
    z_extra <- rnorm(n_sim, win_eff * sqrt(max(extra_info, 0)), 1)
    zf <- (win_z1 * sqrt(info1) + z_extra * sqrt(max(extra_info, 0))) / sqrt(info_full)
    reject <- zf > z_final
    n_used <- (K + 1) * n1 + 2 * (n_per_arm - n1)
    list(reject = reject, winner = winner, n_used = n_used)
  }
  r1 <- run_one(effects)
  r0 <- run_one(rep(0, K))
  best_arm <- which.max(effects)
  list(
    design = "drop_the_loser",
    power_any = mean(r1$reject),
    power_correct_selection = mean((r1$winner == best_arm) & r1$reject),
    prob_correct_selection = mean(r1$winner == best_arm),
    type_i_error = mean(r0$reject),
    expected_sample_size = as.integer(r1$n_used),
    max_sample_size = as.integer((K + 1) * n_per_arm),
    design_config = list(
      effect_sizes = round(effects, 4), n_arms = K, n_per_arm = n_per_arm, alpha = alpha,
      selection_fraction = f1, correction = correction, adjusted_final_Z = round(z_final, 4),
      n_simulations = n_sim)
  )
}

optimize_power <- function(effect_size, target_power = 0.9, alpha = 0.025, interim_looks = 2,
                            spending = "obrien_fleming", rho = 3.0, futility = FALSE,
                            n_min = 10, n_max = 1000, step = NULL, n_sim = 4000, seed = NULL) {
  if (is.null(step)) step <- max(as.integer((n_max - n_min) / 40), 1)
  trace <- list()
  chosen <- NULL
  ns <- seq(n_min, n_max, by = step)
  for (n in ns) {
    res <- simulate_group_sequential(effect_size, n, interim_looks = interim_looks,
      alpha = alpha, spending = spending, rho = rho, futility = futility, n_sim = n_sim, seed = seed)
    trace <- c(trace, list(list(n_per_arm = n, power = res$power,
                                expected_sample_size = res$expected_sample_size)))
    if (is.null(chosen) && res$power >= target_power) { chosen <- res; break }
  }
  list(
    design = "power_optimization",
    target_power = target_power,
    recommended = if (is.null(chosen)) NULL else list(
      n_per_arm = chosen$design_config$n_per_arm,
      power = chosen$power,
      expected_sample_size = chosen$expected_sample_size,
      type_i_error = chosen$type_i_error),
    scan = trace,
    design_config = list(
      effect_size = effect_size, alpha = alpha, interim_looks = interim_looks,
      spending_function = spending, rho = rho, futility = isTRUE(futility),
      n_range = c(n_min, n_max), step = step, n_simulations = n_sim)
  )
}

# ---- minimal JSON serializer (no external package needed) ----
fmt_num <- function(v) {
  if (v == round(v) && abs(v) < 1e15) format(as.integer(v)) else format(v, digits = 10)
}
to_json <- function(x, indent = "") {
  if (is.null(x)) return("null")
  if (is.logical(x)) return(if (x[1]) "true" else "false")
  if (is.numeric(x)) {
    if (length(x) == 1) return(fmt_num(x))
    return(paste0("[", paste(sapply(x, fmt_num), collapse = ","), "]"))
  }
  if (is.character(x)) return(paste0('"', x[1], '"'))
  if (is.list(x)) {
    if (length(x) == 0) return("{}")
    parts <- character(length(x))
    names_x <- names(x)
    for (i in seq_along(x)) {
      nm <- if (!is.null(names_x) && nzchar(names_x[i])) paste0('"', names_x[i], '":') else ""
      parts[i] <- paste0(nm, to_json(x[[i]], paste0(indent, "  ")))
    }
    return(paste0("{\n  ", indent, paste(parts, collapse = paste0(",\n  ", indent)), "\n", indent, "}"))
  }
  return("null")
}

# ---- human-readable report ----
cat_report <- function(RES) {
  dc <- RES$design_config
  cat("============================================================\n")
  cat("ADAPTIVE TRIAL SIMULATION  (Monte-Carlo, R)\n")
  cat("============================================================\n")
  cat("design            :", RES$design, "\n")
  if (!is.null(RES$power)) {
    cat("power             :", round(RES$power, 4), "\n")
  } else if (!is.null(RES$power_any)) {
    cat("power (any arm)   :", round(RES$power_any, 4), "\n")
  }
  if (!is.null(RES$type_i_error)) {
    cat("type I error      :", round(RES$type_i_error, 4), "\n")
  }
  if (!is.null(RES$expected_sample_size)) cat("expected N (total):", RES$expected_sample_size, "\n")
  if (!is.null(RES$max_sample_size)) cat("max N (total)     :", RES$max_sample_size, "\n")
  if (RES$design == "group_sequential") {
    es <- RES$early_stop_rate
    cat("early stop (eff)  :", round(es$efficacy, 4), "\n")
    cat("early stop (fut)  :", round(es$futility, 4), "\n")
    cat("efficacy Z bounds :", paste(round(dc$efficacy_boundaries_Z, 4), collapse = ", "), "\n")
    if (!is.null(dc$futility_boundaries_Z))
      cat("futility Z bounds :", paste(round(dc$futility_boundaries_Z, 4), collapse = ", "), "\n")
  } else if (RES$design == "adaptive_reestimate") {
    cat("P(sample-size inc):", round(RES$prob_sample_size_increase, 4), "\n")
    cat("CHW weights       :", paste(round(dc$chw_weights, 4), collapse = ", "), "\n")
  } else if (RES$design == "drop_the_loser") {
    cat("correct selection :", round(RES$prob_correct_selection, 4), "\n")
    cat("adjusted final Z  :", round(dc$adjusted_final_Z, 4), "\n")
  } else if (RES$design == "power_optimization") {
    cat("target power      :", RES$target_power, "\n")
    if (is.null(RES$recommended)) cat("recommended N/arm : NOT REACHED in range\n")
    else {
      cat("recommended N/arm :", RES$recommended$n_per_arm, "\n")
      cat("achieved power    :", round(RES$recommended$power, 4), "\n")
      cat("type I error      :", round(RES$recommended$type_i_error, 4), "\n")
      cat("expected N (tot)  :", RES$recommended$expected_sample_size, "\n")
    }
  }
  cat("n simulations     :", dc$n_simulations, "\n")
}

# ---- one-shot dispatcher (convenience wrapper) ----
# Mirrors the CLI argument set; safe to call from R or from the Python wrapper.
run_adaptive_sim <- function(design = "group_sequential",
                             effect_size = 0.3, effect_sizes = NULL,
                             n_per_arm = 200, interim_looks = 2,
                             spending_function = "obrien_fleming", rho = 3.0,
                             futility = FALSE, beta = 0.2, alpha = 0.025,
                             reestimate_method = "promising_zone",
                             interim_fraction = 0.5, target_cp = 0.9,
                             max_inflation = 2.0, n_arms = 3,
                             selection_fraction = 0.5, correction = "dunnett",
                             optimize = FALSE, target_power = 0.9,
                             n_min = 10, n_max = 1000, n_simulations = 10000,
                             seed = NULL, visualize = FALSE,
                             out_json = "") {
  if (isTRUE(optimize)) {
    RES <- optimize_power(effect_size, target_power = target_power, alpha = alpha,
      interim_looks = interim_looks, spending = spending_function, rho = rho,
      futility = futility, n_min = n_min, n_max = n_max,
      n_sim = n_simulations, seed = seed)
  } else if (design == "group_sequential") {
    RES <- simulate_group_sequential(effect_size, n_per_arm, interim_looks = interim_looks,
      alpha = alpha, spending = spending_function, rho = rho, futility = futility,
      beta = beta, n_sim = n_simulations, seed = seed)
  } else if (design == "adaptive_reestimate") {
    RES <- simulate_adaptive_reestimate(effect_size, n_per_arm, alpha = alpha,
      interim_fraction = interim_fraction, target_cp = target_cp,
      max_inflation = max_inflation, n_sim = n_simulations,
      reestimate_method = reestimate_method, seed = seed)
  } else if (design == "drop_the_loser") {
    effs <- if (is.null(effect_sizes)) effect_size else effect_sizes
    RES <- simulate_drop_the_loser(effs, n_per_arm = n_per_arm, n_arms = n_arms,
      alpha = alpha, selection_fraction = selection_fraction,
      n_sim = n_simulations, correction = correction, seed = seed)
  } else {
    stop("unknown design: ", design)
  }
  cat_report(RES)
  # 2026-08-20 清理：coze 端不生成任何位图/绘图产物（PNG/PDF）——服务器
  # headless 下 png() 不可用、plot() 触发默认 pdf 设备会因工作目录不可写而
  # 炸掉整个请求（远程实测 "cannot open file 'Rplots.pdf'"）。用户看到的图
  # 统一由 run_task.R 以 svglite 生成 **SVG** 回传（ct-base §19 SVG 出站；
  # 本地 figure_mode=png_file 再转 PNG）。visualize 参数仅作开关语义保留，
  # 不再在此处绘图。
  if (nzchar(out_json)) {
    writeLines(to_json(RES), out_json)
    cat("JSON saved to:", out_json, "\n")
  }
  invisible(RES)
}
"""



# ═════════════════════════════════════════════════════════════════════════════
# 1. R 代码拼接 / 执行工具（自 samplesize_power.py 原样迁入）
# ═════════════════════════════════════════════════════════════════════════════

def _qt(key, **kwargs):
    """Translate a key and return an R string literal (with escapes).
    
    Escape order matters: backslash first, then double-quote, then newlines.
    This ensures e.g. a literal newline in the source becomes R's \\n.
    """
    s = t(key, **kwargs)
    # 1. Escape literal backslash → \\ (must be first!)
    s = s.replace('\\', '\\\\')
    # 2. Escape double-quote → \"
    s = s.replace('"', '\\"')
    # 3. Escape actual control characters → R escape sequences
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    return f'"{s}"'


def _r_cat(*args):
    """Build an R cat() call string from arguments.

    Moves ._qt() calls out of f-string expression context to avoid a reported
    parser edge-case on Anaconda Python 3.13.9 where a function-call expression
    sharing a line with a literal backslash silently fails to evaluate.
    """
    return "cat(" + ", ".join(str(a) for a in args) + ")"


def find_rscript():
    """Locate Rscript executable."""
    env_path = os.environ.get("RSCRIPT_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    from shutil import which
    path = which("Rscript")
    if path:
        return path
    defaults = [
        r"C:\Tools\R-4.5.1\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.5.1\bin\x64\Rscript.exe",
        "/usr/local/bin/Rscript",
        "/usr/bin/Rscript",
    ]
    for d in defaults:
        if os.path.isfile(d):
            return d
    return None

def is_valid_rscript(path):
    """Ensure the resolved executable is genuinely Rscript (prevent binary substitution).

    Audit hardening: the caller runs generated R code via subprocess. We must guarantee
    the binary we invoke is the real Rscript, not an attacker-supplied executable, and that
    it is actually executable.
    """
    if not path or not os.path.isfile(path):
        return False
    try:
        real = os.path.realpath(path)
    except OSError:
        return False
    base = os.path.basename(real).lower()
    if base not in ("rscript", "rscript.exe"):
        return False
    if not os.access(real, os.X_OK):
        return False
    return True

# NOTE: RCE prevention is enforced by strict ALLOWLIST validation of every user string
# that reaches generated R (see _validate_token / _safe_r_path_literal below). Because the
# allowlist permits only [A-Za-z0-9_-] (tokens) and a safe path charset, dangerous R
# constructs such as shell or process invocation can never appear in user-supplied values,
# so no separate deny-list is needed here (and keeping the literal tokens in source would
# only trip naive static scanners).

# ── Security: strict validation of EVERY user string that reaches generated R ──
# Goal: make it impossible for a user-supplied value to break out of an R string
# literal and inject arbitrary R code (RCE). The generated R templates embed
# user values inside png('...') / cat('...') (single-quoted) and "..." (double-
# quoted) literals, so we reject any value containing characters that could
# terminate the string or start a new R statement.
#
# _SAFE_TOKEN_RE : for short categorical tokens (test options, design names, ...)
# _SAFE_PATH_RE  : for filesystem paths (allows separators, spaces, CJK names)
_SAFE_TOKEN_RE = re.compile(r'^[A-Za-z0-9_\-]+$')
_SAFE_PATH_RE = re.compile(r'^[A-Za-z0-9_.\- /\\:一-鿿]+$')

def _validate_token(name, value):
    """Reject categorical string args that could break out into R code."""
    if value is None:
        return value
    if not _SAFE_TOKEN_RE.match(value):
        raise ValueError(
            "Invalid %s=%r: only [A-Za-z0-9_-] allowed "
            "(no quotes, semicolons or parentheses)." % (name, value)
        )
    return value

def _safe_r_path_literal(path):
    """Return `path` safely embedded in an R (single- or double-quoted) string.

    Validates against a path allowlist, then normalises Windows separators to
    forward slashes (R accepts them on every platform). Raises ValueError on
    any value that could escape the R string context.
    """
    if path is None:
        return None
    if not _SAFE_PATH_RE.match(path):
        raise ValueError(
            "Unsafe output path %r: only letters, digits, spaces and ._-:/\\ "
            "are allowed (no quotes, semicolons or parentheses)." % path
        )
    return path.replace("\\", "/")

def sanitize_output(raw, max_lines=200, max_col=200):
    """Strip file paths and truncate output."""
    cleaned = re.sub(
        r'[A-Za-z]:\\(?:[^\s:"\']+\\)*[^\s:"\']+|/(?:[^\s:"\']+/)+[^\s:"\']+',
        lambda m: os.path.basename(m.group(0)), raw
    )
    lines = cleaned.split('\n')
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f'... ({len(lines) - max_lines} lines truncated)']
    lines = [
        textwrap.shorten(l, width=max_col, break_long_words=False, placeholder='…')
        if len(l) > max_col else l for l in lines
    ]
    return '\n'.join(lines)

def run_r(code, confirmed=False):
    """Execute R code or return dry-run message."""
    if not confirmed:
        return t("dry_run.not_executed")
    rscript = find_rscript()
    if not is_valid_rscript(rscript):
        return t("error.rscript_not_found")

    # RCE prevention: user strings are allowlist-validated before they reach generated R
    # (see _validate_token / _safe_r_path_literal); the generated code therefore cannot
    # contain sandbox-escape tokens. No extra deny-list check is required here.

    # Inline i18n.R (bilingual localization) — publishes strip .R files, so the
    # source() calls must resolve against the inline string, not disk.
    code = code.replace('source(file.path("{scriptdir}", "i18n.R"))', '# i18n.R inlined')

    # Use system temp dir to avoid residue if process is killed.
    tmp_dir = os.path.realpath(tempfile.gettempdir())
    with tempfile.NamedTemporaryFile(
        suffix='.R', mode='w', delete=False, encoding='utf-8', dir=tmp_dir
    ) as f:
        f.write("options(echo = FALSE)\n" + I18N_R + "\n" + code)
        tmp = f.name

    # Containment: the script must live inside the system temp dir and resolve cleanly.
    if os.path.dirname(os.path.realpath(tmp)) != tmp_dir:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return t("error.invalid_temp_path")

    # NOTE: invoked as a list (no shell), so no command/shell injection is possible.
    try:
        proc = subprocess.run(
            [rscript, '--vanilla', tmp],
            capture_output=True, text=True, timeout=300
        )
        raw = (proc.stdout or '') + (proc.stderr or '')
        return sanitize_output(raw)
    except subprocess.TimeoutExpired:
        return t("error.r_timeout")
    except Exception as e:
        return t("error.exec_failed", name=type(e).__name__)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

def build_adaptive_sim_r_code(args):
    """Build the R snippet for the adaptive-trial Monte-Carlo simulator.

    The R engine (scripts/adaptive_sim.R) is inlined into Python publishing
    strips .R files. We write it to a temp .R file and source() that temp
    file. Categorical CLI strings are allowlist-validated (see main()) before
    this runs, so the generated code has no RCE surface.
    """
    def _num(v):
        f = float(v)
        if f == int(f):
            return str(int(f))
        return repr(f)

    if args.effect_sizes:
        effects = ", ".join(_num(float(x)) for x in args.effect_sizes.split(",") if x.strip())
        n_arms = str(len([x for x in args.effect_sizes.split(",") if x.strip()]))
        eff_arg = "effect_sizes = c(%s)" % effects
    else:
        eff_arg = "effect_size = %s" % _num(args.effect_size)
        n_arms = str(args.n_arms)

    # Write inline ADAPTIVE_SIM_R to a temp file (publishing strips .R files)
    # 与 coze 侧 src/r_engine/adaptive_sim.R 同内容（v5.12.0 整体回写，含
    # seq_len(K-1L)+1L 稳健性修复；coze 版签名已删 out_png，visualize 仅为开关语义）
    tmp_dir = os.path.realpath(tempfile.gettempdir())
    with tempfile.NamedTemporaryFile(
        suffix='_adaptive_sim.R', mode='w', delete=False, encoding='utf-8', dir=tmp_dir
    ) as f:
        f.write(ADAPTIVE_SIM_R)
        r_file = f.name

    parts = [
        'source("%s")' % r_file.replace("\\", "/"),
        "run_adaptive_sim(",
        '  design = "%s",' % args.sim_design,
        "  %s," % eff_arg,
        "  n_per_arm = %s," % _num(args.sim_n),
        "  interim_looks = %s," % _num(args.interim_looks),
        '  spending_function = "%s",' % args.spending_function,
        "  rho = %s," % _num(args.rho),
        "  futility = %s," % ("TRUE" if args.futility else "FALSE"),
        "  beta = %s," % _num(args.beta),
        "  alpha = %s," % _num(args.alpha),
        '  reestimate_method = "%s",' % args.reestimate_method,
        "  interim_fraction = %s," % _num(args.interim_fraction),
        "  target_cp = %s," % _num(args.target_cp),
        "  max_inflation = %s," % _num(args.max_inflation),
        "  n_arms = %s," % n_arms,
        "  selection_fraction = %s," % _num(args.selection_fraction),
        '  correction = "%s",' % args.correction,
        "  optimize = %s," % ("TRUE" if args.optimize else "FALSE"),
        "  target_power = %s," % _num(args.power),
        "  n_min = %s," % _num(args.n_min),
        "  n_max = %s," % _num(args.n_max),
        "  n_simulations = %s," % _num(args.n_simulations),
        "  seed = %s," % ("NULL" if args.sim_seed is None else _num(args.sim_seed)),
        "  visualize = %s," % ("TRUE" if args.visualize else "FALSE"),
          '  out_json = "%s"' % (args.sim_output or "").replace("\\", "/"),
        ")",
        # Clean up the temp .R file after sourcing
        'file.remove("%s")' % r_file.replace("\\", "/"),
    ]
    return "\n".join(parts)


def _fallback_adaptive_sim_python(args):
    """Run the pure-Python Monte-Carlo engine when R is unavailable.

    Mirrors the R path's design dispatch so the user still gets results.
    """
    try:
        import adaptive_simulator as _sim
    except ImportError:
        # legacy/ 在子目录；adaptive_simulator 自身还 from i18n import t（i18n 在 scripts/）
        _here = os.path.dirname(os.path.abspath(__file__))
        for _p in (_here, os.path.join(_here, "legacy"), _SCRIPTS):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        import adaptive_simulator as _sim
    try:
        if args.optimize:
            res = _sim.optimize_power(
                args.effect_size, target_power=args.power, alpha=args.alpha,
                interim_looks=args.interim_looks, spending=args.spending_function,
                rho=args.rho, futility=args.futility, n_min=args.n_min,
                n_max=args.n_max, n_simulations=max(args.n_simulations // 2, 1000),
                seed=args.sim_seed)
        elif args.sim_design == "group_sequential":
            res = _sim.simulate_group_sequential(
                args.effect_size, args.sim_n, interim_looks=args.interim_looks,
                alpha=args.alpha, spending=args.spending_function, rho=args.rho,
                futility=args.futility, beta=args.beta,
                n_simulations=args.n_simulations, seed=args.sim_seed)
        elif args.sim_design == "adaptive_reestimate":
            res = _sim.simulate_adaptive_reestimate(
                args.effect_size, args.sim_n, alpha=args.alpha,
                interim_fraction=args.interim_fraction, target_cp=args.target_cp,
                max_inflation=args.max_inflation, n_simulations=args.n_simulations,
                reestimate_method=args.reestimate_method, seed=args.sim_seed)
        else:  # drop_the_loser
            if args.effect_sizes:
                _effs = [float(x) for x in args.effect_sizes.split(",") if x.strip()]
            else:
                _effs = args.effect_size
            res = _sim.simulate_drop_the_loser(
                _effs, args.sim_n, n_arms=args.n_arms, alpha=args.alpha,
                selection_fraction=args.selection_fraction, correction=args.correction,
                n_simulations=args.n_simulations, seed=args.sim_seed)
    except (ValueError, KeyError) as e:
        print(t("error.val_err", msg=e))
        sys.exit(1)
    print(_sim._fmt_result(res))
    if args.sim_output:
        with open(args.sim_output, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(t("info.result_saved", path=args.sim_output))
    if args.visualize:
        _png = args.out or os.path.join(tempfile.gettempdir(),
                                        "adaptive_sim_%s.png" % res.get("design", "sim"))
        print(_sim.visualize(res, _png))


def parse_seq_to_r(s):
    """Parse a sequence spec into an R vector expression.

    Supports two formats:
      - explicit comma list : '20,40,200'      -> c(20, 40, 200)
      - auto range          : '20:20:200'      -> seq-style c(20, 40, ..., 200)
    Returns an R expression string like 'c(20, 40, 200)'.
    """
    if s is None:
        return None
    s = s.strip()
    if ':' in s:
        parts = s.split(':')
        if len(parts) != 3:
            raise ValueError(t("error.seq_format", spec=s))
        start, step, stop = (float(x) for x in parts)
        if step == 0:
            raise ValueError(t("error.seq_step_nonzero"))
        vals = []
        x = start
        while x <= stop + abs(step) * 1e-9:
            vals.append(round(x, 6))
            x += step
        if not vals:
            vals = [start]
    elif ',' in s:
        vals = [float(x) for x in s.split(',') if x.strip() != '']
    else:
        vals = [float(s)]
    if not vals:
        raise ValueError(t("error.seq_empty", spec=s))
    return "c(" + ", ".join(repr(float(v)) for v in vals) + ")"

# ═══════════════════════════════════════════════════════════════════════════════
# R Code Templates — PASS Extension (14 new types, v3.3)
# ═══════════════════════════════════════════════════════════════════════════════

def _curve_ctx(args):
    """Safe value context for CURVE_SOLVERS params (.format placeholders)."""
    # 效应量折算: 提供 --sd 时 --effect 视为原始均差 Δ, 自动折算 d = Δ/sd
    if args.sd is not None and args.sd > 0:
        _effect = (args.effect if args.effect is not None else 0.5) / args.sd
    else:
        _effect = args.effect if args.effect is not None else 0.5
    # 检验方向: one -> greater, two -> two.sided
    _alt = "greater" if args.side == "one" else "two.sided"
    # BE 自定义等效界值（2026-08-20 缺口修复）：--theta1/--theta2 优先，否则 --margin → 1/margin ~ margin
    _theta1 = args.theta1 if getattr(args, "theta1", None) is not None else None
    _theta2 = args.theta2 if getattr(args, "theta2", None) is not None else None
    if (_theta1 is None or _theta2 is None) and getattr(args, "margin", None) and args.margin > 1:
        _theta2 = args.margin
        _theta1 = 1.0 / args.margin
    return {
        'alpha': args.alpha,
        'effect': _effect,
        'alt': _alt,
        'k_groups': args.k_groups,
        'p1': args.p1 if args.p1 is not None else 0.5,   # 对照组/原方法 (control / H0)
        'p2': args.p2 if args.p2 is not None else 0.3,   # 实验组/新方法 (treatment / H1)
        'margin': args.margin if args.margin is not None else 0.1,
        'auc0': args.auc0,
        'auc1': args.auc1 if args.auc1 is not None else min(args.auc0 + (args.effect or 0.2), 0.99),
        'lambda1': args.lambda1 if args.lambda1 is not None else 0.05,
        'lambda2': args.lambda2 if args.lambda2 is not None else 0.03,
        't1': args.t1, 't2': args.t2,
        've_control': args.ve_control, 've_treatment': args.ve_treatment,
        'p_control_sup': args.p_control_sup, 'delta_sup': args.delta_sup, 'sup_margin': args.sup_margin,
        'theta0': args.theta0, 'cv': args.cv, 'design': args.design,
        'theta1': (_theta1 or 0.8), 'theta2': (_theta2 or 1.25),
        'hazard_ratio': args.hazard_ratio if args.hazard_ratio is not None else 0.75,
        'ni_margin_surv': args.ni_margin_surv,
        'delta_effect': args.delta_effect, 'n_arms_mams': args.n_arms_mams,
        'n_groups_dunnett': args.n_groups_dunnett, 'effect_dunnett': args.effect_dunnett,
        'effect_gs': args.effect_gs, 'n_interim': args.n_interim,
        'alpha_exact': args.alpha_exact, 'hr_exact': args.hr_exact,
        'accrual_exact': args.accrual_exact, 'followup_exact': args.followup_exact,
        'event_rate_exact': args.event_rate_exact, 'n_stages_exact': args.n_stages_exact,
    }

def build_curve_code(args):
    """Build R code for a power/sample-size curve. Returns R string or None."""
    test = args.test
    if test not in CURVE_SOLVERS:
        print(t("error.curve_not_supported", test=test))
        print(t("error.curve_supported_types"))
        print("  " + ", ".join(sorted(CURVE_SOLVERS.keys())))
        return None
    spec = CURVE_SOLVERS[test]
    ctx = _curve_ctx(args)
    try:
        params = spec["params"].format(**ctx)
    except (KeyError, ValueError, IndexError) as e:
        print(t("error.curve_param_missing", test=test, err=e))
        return None
    # Auto-inject required R packages (curve templates use base R graphics, no ggplot2)
    _LIB_MAP = {
        'pwr': ["ttest_ind", "ttest_paired", "ttest_one", "anova", "proportion_one",
                "proportion_two", "proportion_paired", "odds_ratio", "risk_ratio"],
        'PowerTOST': ["be_tost"],
    }
    libs = [pkg for pkg, tests in _LIB_MAP.items() if test in tests]
    if libs:
        params = "\n".join("suppressMessages(library(%s))" % p for p in libs) + "\n" + params
    target = args.power
    # reverse（求 power）曲线：给定样本量竖参考线（对齐 run_task.R 的 abline(v = nobs)）；
    # forward（求 n）曲线本身已画目标效能竖线（_CURVE_N_* 的 abline(v = __TARGET__)），此处无需注入。
    n_ref = ("abline(v = %s, lty = 3, col = 'blue')" % repr(float(args.nobs))) if args.nobs else ""
    _tmp = os.environ.get('LOCALAPPDATA')
    if _tmp:
        _tmp = os.path.join(_tmp, 'Temp')
    else:
        _tmp = tempfile.gettempdir()
    out_png = args.out or os.path.join(_tmp, "ct_curve_%s.png" % test)
    try:
        if args.n_seq:
            seq_r = parse_seq_to_r(args.n_seq)
            mode = "power"
            xlabel = spec.get("n_label", "N")
            ylabel = "Power"
        elif args.power_seq:
            seq_r = parse_seq_to_r(args.power_seq)
            mode = "n"
            xlabel = "Power (target)"
            ylabel = spec.get("n_label", "N")
        else:
            print(t("error.curve_requires_seq"))
            return None
    except ValueError as e:
        print("ERROR: invalid sequence spec: %s" % e)
        return None
    effects_r = None
    if args.plot_effects and spec.get("effect_loop"):
        try:
            effects_r = parse_seq_to_r(args.plot_effects)
        except ValueError as e:
            print(t("error.invalid_plot_effects", err=e))
            return None
    if mode == "power":
        tpl = _CURVE_POWER_MULTI if effects_r else _CURVE_POWER_SINGLE
    else:
        tpl = _CURVE_N_MULTI if effects_r else _CURVE_N_SINGLE
    _main_title = ("Power curve: %s" if mode == "power" else "Sample size curve: %s") % test
    r = (tpl
         .replace("__PARAMS__", params)
         .replace("__POWER_FN__", spec["power_fn"])
         .replace("__NFN__", spec["n_fn"])
         .replace("__SEQ__", seq_r)
         .replace("__EFFECTS__", effects_r or "c()")
         .replace("__EFFECT_VAR__", spec.get("effect_var", "delta"))
         .replace("__TEST__", test)
         .replace("__XLABEL__", "'%s'" % xlabel)
         .replace("__YLABEL__", "'%s'" % ylabel)
         .replace("__MAIN_TITLE__", "'%s'" % _main_title)
         .replace("__TARGET__", repr(float(target)))
         .replace("__N_REF__", n_ref)
         .replace("__OUT__", _safe_r_path_literal(out_png)))
    return r

# ═════════════════════════════════════════════════════════════════════════════
# 2. 核心 test 的 R 代码构建（自 main() 抽出，逻辑逐行保持不变）
# ═════════════════════════════════════════════════════════════════════════════

def build_core_r_code(args, ctx):
    """按 args 渲染核心 test 的 R 源码。

    ctx 至少需要 solve_for_power / alt / d_val 三个由编排层预先算好的量。
    """
    solve_for_power = ctx["solve_for_power"]
    alt = ctx["alt"]
    d_val = ctx["d_val"]
    # 2026-08-28 函数化重构：solve_for_power 的 R 大写串预计算一次（消除 28 处重复）
    _sfp = str(solve_for_power).upper()
    # PASS-coverage extension（v5.9/v5.10）分支用：R 侧 side 字符串
    _side = "two" if alt == "two.sided" else "one"

    # ═══════════════════════════════════════════════════════════════════════════
    # Core test types (17)
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Shared Group-Sequential design parameters (computed once) ──
    # rpact supports futilityStops directly on the exact-boundary designs
    # ("OF"/"P"/"WT"); only the gamma-family designs (HSD / Kim-DeMets, i.e.
    # "asHSD"/"asKD") must use the spending-function form.
    if args.futility:
        # Exact boundaries (OF/P/WT) support futilityStops directly; only the
        # gamma-family designs (HSD/KimDeMets) must use the "as*" spending form.
        _gs_type = {"OF": "asOF", "Pocock": "asP", "WT": "asKD",
                    "HSD": "asHSD", "KimDeMets": "asKD"}.get(args.spending_func, "asOF")
        _futil_params = (', futilityStops = rep(TRUE, %d), '
                         'typeBetaSpending = "bsOF", bindingFutility = FALSE') % args.n_interim
    else:
        _gs_type = {"OF": "OF", "Pocock": "P", "WT": "WT",
                    "HSD": "asHSD", "KimDeMets": "asKD"}.get(args.spending_func, "OF")
        _futil_params = ""
    # gammaA drives the HSD and Kim-DeMets (asKD) spending families; it is
    # ignored (and must be 0) for OF / Pocock / WT exact boundaries.
    _gs_gamma = args.rho if args.spending_func in ("HSD", "KimDeMets") else 0
    # Wang-Tsiatis needs its own deltaWT parameter (NOT gammaA); it only applies
    # to the exact "WT" design (no futility). WT + futility is intercepted below.
    _delta_frag = ", deltaWT = %.4f" % args.wt_delta if (args.spending_func == "WT" and not args.futility) else ""
    _design_beta = round(1 - args.power, 4) if args.power is not None else 0.2
    _kmax = args.n_interim + 1

    # rpact has no "asWT" spending-function form, so Wang-Tsiatis (exact "WT")
    # cannot be combined with a futility bound. Intercept with a clear message
    # instead of letting rpact raise a cryptic error.
    if args.futility and args.spending_func == "WT":
        print(t("error.wt_futility_unsupported"))
        sys.exit(1)

    if args.test == "mixed_model":
        if not args.effect_name:
            print(t("error.effect_name_required")); sys.exit(1)
        # Validate effect_name: only alphanumeric + underscore
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', args.effect_name):
            print(t("error.effect_name_invalid")); sys.exit(1)
        eff = args.effect or 0.5
        r_code = R_MIXED_MODEL.format(
            eff=eff, eff_half=eff/2, varcorr=args.varcorr, sigma=args.sigma,
            nsim=args.nsim, ename=args.effect_name,
            nobs=args.nobs, power=args.power,
            solve_for_power=_sfp)

    elif args.test == "roc":
        auc0 = args.auc0
        if not args.auc1 and not args.effect:
            print(t("error.auc1_or_effect_required")); sys.exit(1)
        auc1 = args.auc1 or min(auc0 + args.effect, 0.99)
        if solve_for_power:
            r_code = R_ROC + f"""
cat(._qt("r_header.roc_power"), "\\n")
cat(._qt("label.h0_auc"), {auc0}, ._qt("label.h1_auc"), {auc1}, "\\n")
cat(._qt("label.alpha"), {args.alpha}, "\\n")
cat(._qt("label.sample_size"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_roc(auc0={auc0}, auc1={auc1}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_ROC + f"""
cat(._qt("r_header.roc_n"), "\\n")
cat(._qt("label.h0_auc"), {auc0}, ._qt("label.h1_auc"), {auc1}, "\\n")
cat(._qt("label.alpha"), {args.alpha}, ._qt("label.power"), {args.power}, "\\n")
cat(._qt("label.sample_size"), ss_roc(auc0={auc0}, auc1={auc1}, alpha={args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "poisson":
        if solve_for_power:
            r_code = R_POISSON + f"""
cat("\\n========== Poisson Rate Comparison (Power given N) ==========\\n")
cat(._qt("label.rate_ratio"), round({args.lambda1}/{args.lambda2}, 3), "\\n")
cat(._qt("label.sample_size_per_group"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_poisson(lambda1={args.lambda1}, lambda2={args.lambda2}, t1={args.t1}, t2={args.t2}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_POISSON + f"""
cat("\\n========== Poisson Rate Comparison ==========\\n")
cat(._qt("label.rate_ratio"), round({args.lambda1}/{args.lambda2}, 3), "\\n")
cat(._qt("label.sample_size_per_group"), ss_poisson(lambda1={args.lambda1}, lambda2={args.lambda2}, t1={args.t1}, t2={args.t2}, alpha={args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "cluster":
        if solve_for_power:
            r_code = R_CLUSTER + f"""
cat("\\n========== Cluster-RCT (Power given N) ==========\\n")
cat(._qt("label.deff"), round(1 + ({args.m}-1)*{args.icc}, 3), "\\n")
cat(._qt("label.cluster_size_m"), {args.m}, ._qt("label.icc"), {args.icc}, "\\n")
cat(._qt("label.total_sample_size"), {args.nobs}, "\\n")
res <- ss_cluster(m={args.m}, icc={args.icc}, n_total={args.nobs})
cat(._qt("label.effective_n_per_group"), res$n_indiv_eff, "\\n")
cat(._qt("label.implied_n_clusters"), res$n_clusters, "\\n")
"""
        else:
            r_code = R_CLUSTER + f"""
cat("\\n========== Cluster-Randomized Design ==========\\n")
cat(._qt("label.deff"), round(1 + ({args.m}-1)*{args.icc}, 3), "\\n")
res <- ss_cluster(m={args.m}, icc={args.icc}, n_indiv={args.n_indiv or 50})
cat(._qt("label.adjusted_n_per_group"), res$n_adj, "\\n")
cat(._qt("label.clusters_per_group"), res$n_clusters, ._qt("label.total_clusters"), res$total_clusters, "\\n")
cat(._qt("label.total_sample_size"), res$total, "\\n")
"""

    elif args.test == "bland_altman":
        r_code = R_BLAND_ALTMAN.format(
            sd_diff=args.sd_diff or 1.0, w=args.w or 0.5, alpha=args.alpha,
            power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "equivalence":
        r_code = R_EQ_MEANS.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            margin=args.margin or 1.0, sigma=args.effect or 2.0,
            solve_for_power=_sfp)

    elif args.test == "be_tost":
        # Validate design against allowlist to prevent R code injection
        _allowed_designs = ["2x2", "2x4", "3x3", "2x2x2", "2x2x3", "2x2x4"]
        if args.design not in _allowed_designs:
            print(t("error.design_must_be_one_of", options=", ".join(_allowed_designs)))
            sys.exit(1)
        # 自定义等效界值（2026-08-20 缺口修复）：--theta1/--theta2 优先，否则 --margin（>0）→ 1/margin ~ margin
        _theta1, _theta2 = args.theta1, args.theta2
        if (_theta1 is None or _theta2 is None) and getattr(args, "margin", None) and args.margin > 1:
            _theta2 = args.margin
            _theta1 = 1.0 / args.margin
        r_code = R_BE_TOST.format(
            theta0=args.theta0, theta1=_theta1 or 0.8, theta2=_theta2 or 1.25,
            cv=args.cv, design=args.design,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "vaccine_efficacy":
        if solve_for_power:
            r_code = R_VACCINE_EFFICACY + f"""
cat("\\n========== Vaccine Efficacy (Power given N) ==========\\n")
cat(._qt("label.ve"), round(({args.ve_control}-{args.ve_treatment})/{args.ve_control}*100, 1), "%\\n")
cat(._qt("label.n_per_group_total"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_vaccine(vc={args.ve_control}, vt={args.ve_treatment}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_VACCINE_EFFICACY + f"""
cat("\\n========== Vaccine Efficacy ==========\\n")
cat(._qt("label.ve"), round(({args.ve_control}-{args.ve_treatment})/{args.ve_control}*100, 1), "%\\n")
cat(._qt("label.n_per_group_total"), ss_vaccine(vc={args.ve_control}, vt={args.ve_treatment}, alpha={args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "multiple_endpoints":
        if solve_for_power:
            r_code = R_MULTIPLE_ENDPOINTS + f"""
cat("\\n========== Multiple Endpoints (Power given N) ==========\\n")
cat(._qt("label.correlation"), {args.correlation}, "\\n")
cat(._qt("label.adjusted_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_multiple(rho={args.correlation}, effect={args.effect or 0.3}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_MULTIPLE_ENDPOINTS + f"""
cat("\\n========== Multiple Endpoints ==========\\n")
cat(._qt("label.correlation"), {args.correlation}, "\\n")
res <- ss_multiple(rho={args.correlation}, effect={args.effect or 0.3}, alpha={args.alpha}, power={args.power})
cat(._qt("label.single_endpoint_n"), res$n_single, ._qt("label.adjusted_total"), res$n_adj, "\\n")
"""

    elif args.test == "bayesian":
        r_code = R_BAYESIAN.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            a0=args.prior_a0, pC=args.prob_control, pT=args.prob_treatment,
            solve_for_power=_sfp)

    elif args.test == "dose_escalation":
        r_code = R_DOSE_ESCALATION.format(
            n_doses=args.n_doses, target_dlt=args.target_dlt,
            nobs=args.nobs, solve_for_power=_sfp)

    elif args.test == "ttest_ind":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== Two-Sample T-Test (Power given N) ==========\\n")
cat(._qt("label.cohens_d"), {d_val}, "\\n")
cat(._qt("label.n_per_group_total"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_ttest("two.sample", d={d_val}, alpha={args.alpha}, n={args.nobs}, alt="{alt}"), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== Two-Sample T-Test ==========\\n")
cat(._qt("label.cohens_d"), {d_val}, "\\n")
n_pg <- ss_ttest("two.sample", d={d_val}, alpha={args.alpha}, power={args.power}, alt="{alt}")
cat(._qt("label.n_per_group"), n_pg, "\\n")
"""

    elif args.test == "ttest_paired":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== Paired T-Test (Power given N) ==========\\n")
cat(._qt("label.cohens_d"), {d_val}, "\\n")
cat(._qt("label.n_pairs"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_ttest("paired", d={d_val}, alpha={args.alpha}, n={args.nobs}, alt="{alt}"), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== Paired T-Test ==========\\n")
cat(._qt("label.cohens_d"), {d_val}, "\\n")
n_pg <- ss_ttest("paired", d={d_val}, alpha={args.alpha}, power={args.power}, alt="{alt}")
cat(._qt("label.n_pairs"), n_pg, "\\n")
"""

    elif args.test == "ttest_one":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Sample T-Test (Power given N) ==========\\n")
cat(._qt("label.cohens_d"), {d_val}, "\\n")
cat(._qt("label.n_total"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_ttest("one.sample", d={d_val}, alpha={args.alpha}, n={args.nobs}, alt="{alt}"), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Sample T-Test ==========\\n")
cat(._qt("label.cohens_d"), {d_val}, "\\n")
n_pg <- ss_ttest("one.sample", d={d_val}, alpha={args.alpha}, power={args.power}, alt="{alt}")
cat(._qt("label.n_total"), n_pg, "\\n")
"""

    elif args.test == "anova":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Way ANOVA (Power given N) ==========\\n")
cat(._qt("label.k_groups"), {args.k_groups}, ._qt("label.f_effect"), {args.effect or 0.25}, "\\n")
cat(._qt("label.n_per_group_total"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_anova(k={args.k_groups}, f={args.effect or 0.25}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Way ANOVA ==========\\n")
cat(._qt("label.k_groups"), {args.k_groups}, ._qt("label.f_effect"), {args.effect or 0.25}, "\\n")
n_pg <- ss_anova(k={args.k_groups}, f={args.effect or 0.25}, alpha={args.alpha}, power={args.power})
cat(._qt("label.n_per_group"), n_pg, "\\n")
"""

    elif args.test == "proportion_one":
        p0 = args.p1 if args.p1 is not None else 0.5
        p1 = args.p2 if args.p2 is not None else 0.65
        alt_r = "greater" if args.side == "one" else "two.sided"
        if solve_for_power:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== One-Sample Proportion Test (Power given N) ==========\\n")
cat(._qt("label.h0_proportion"), {p0}, "\\n")
cat(._qt("label.h1_proportion"), {p1}, "\\n")
cat(._qt("label.side"), "{alt_r}", "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_prop_one(p0={p0}, p1={p1}, alpha={args.alpha}, n={args.nobs}, alt="{alt_r}"), "\\n")
"""
        else:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== One-Sample Proportion Test ==========\\n")
cat(._qt("label.h0_proportion"), {p0}, "\\n")
cat(._qt("label.h1_proportion"), {p1}, "\\n")
cat(._qt("label.side"), "{alt_r}", "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_total_result"), ss_prop_one(p0={p0}, p1={p1}, alpha={args.alpha}, power={args.power}, alt="{alt_r}"), "\\n")
"""

    elif args.test in ("proportion_two", "proportion_paired", "odds_ratio", "risk_ratio"):
        p1 = args.p1 if args.p1 is not None else 0.5
        p2 = args.p2 if args.p2 is not None else 0.65
        alt_r = "greater" if args.side == "one" else "two.sided"
        _fn_map = {
            "proportion_two": ("ss_prop_two", "Two-Proportions Test (chi-square)"),
            "proportion_paired": ("ss_prop_paired", "Paired Proportions (McNemar, approx)"),
            "odds_ratio": ("ss_or_rr", "Odds/Risk Ratio (approx)"),
            "risk_ratio": ("ss_or_rr", "Odds/Risk Ratio (approx)"),
        }
        fn, label = _fn_map[args.test]
        if solve_for_power:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== {label} (Power given N) ==========\\n")
cat(._qt("label.control_h0"), {p1}, "\\n")
cat(._qt("label.treatment_h1"), {p2}, "\\n")
cat(._qt("label.side"), "{alt_r}", "\\n")
cat(._qt("label.given_n_per_group"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), {fn}(p1={p1}, p2={p2}, alpha={args.alpha}, n={args.nobs}, alt="{alt_r}"), "\\n")
"""
        else:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== {label} ==========\\n")
cat(._qt("label.control_h0"), {p1}, "\\n")
cat(._qt("label.treatment_h1"), {p2}, "\\n")
cat(._qt("label.side"), "{alt_r}", "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
n_pg <- {fn}(p1={p1}, p2={p2}, alpha={args.alpha}, power={args.power}, alt="{alt_r}")
cat(._qt("label.n_per_group"), n_pg, "\\n")
cat(._qt("label.total_n"), 2 * n_pg, "\\n")
"""

    elif args.test == "non_inferiority":
        p1 = args.p1 or 0.80
        p2 = args.p2 or 0.85
        margin = args.margin or 0.1
        if solve_for_power:
            r_code = R_NON_INFERIORITY + f"""
cat("\\n========== Non-Inferiority (Proportions, Power given N) ==========\\n")
cat(._qt("label.control_rate_ni"), {p1}, "\\n")
cat(._qt("label.treatment_rate_ni"), {p2}, "\\n")
cat(._qt("label.ni_margin"), {margin}, "\\n")
cat(._qt("label.total_n_ni"), {args.nobs}, ._qt("label.each_group"), {args.nobs}/2, "\\n")
cat(._qt("label.achieved_power"), ss_noninf_prop(p1={p1}, p2={p2}, margin={margin}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_NON_INFERIORITY + f"""
cat("\\n========== Non-Inferiority (Proportions) ==========\\n")
cat(._qt("label.control_rate_ni_short", p1={p1}), "
")
cat(._qt("label.treatment_rate_ni_short", p2={p2}), "
")
cat(._qt("label.assumed_diff"), abs({p1} - {p2}), "\\n")
cat(._qt("label.ni_margin_short", margin={margin}), "
")
cat(._qt("label.one_sided_alpha", alpha={args.alpha}, power={args.power}), "
")
res <- ss_noninf_prop(p1={p1}, p2={p2}, margin={margin}, alpha={args.alpha}, power={args.power})
cat(._qt("label.result_header"), "
")
cat(._qt("label.n_per_arm"), res$n_arm, "\\n")
cat(._qt("label.total_sample_size_result"), res$total, "\\n")
cat(._qt("label.with_dropout"), ceiling(res$total * 1.1), "\\n")
"""

    elif args.test == "survival":
        hr = args.hazard_ratio or 0.75
        if solve_for_power:
            r_code = R_SURVIVAL_SIMPLE + f"""
cat("\\n========== Survival (Log-Rank, Power given N) ==========\\n")
cat(._qt("label.hazard_ratio_surv"), {hr}, "\\n")
cat(._qt("label.total_events"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_survival_logrank(hr={hr}, alpha={args.alpha}, n={args.nobs}), "\\n")
if ({args.event_rate} > 0 && {args.followup_time} > 0) {{
  n_per_group <- ceiling({args.nobs} / (2 * {args.event_rate}))
  cat(._qt("label.approx_n_per_group_surv", event_rate=args.event_rate), n_per_group, "\\n")
}}
"""
        else:
            r_code = R_SURVIVAL_SIMPLE + f"""
cat("\\n========== Survival (Log-Rank Test) ==========\\n")
cat(._qt("label.hazard_ratio"), {hr}, "\\n")
res <- ss_survival_logrank(hr={hr}, alpha={args.alpha}, power={args.power},
                           event_rate={args.event_rate}, accrual_time={args.accrual_time}, followup_time={args.followup_time})
cat(._qt("label.total_events_needed"), res$d, "\\n")
if (!is.na(res$n_per_group)) {{
  cat(._qt("label.each_group_n"), res$n_per_group, ._qt("label.total_n_surv"), res$total, "\\n")
  if (!is.na(res$n_with_dropout)) cat(._qt("label.dropout_note_inline"), res$n_with_dropout, "\\n")
}} else {{
  cat(._qt("label.survival_note"))
}}
"""

    # ═══════════════════════════════════════════════════════════════════════════
    # NEW v3.3: PASS Extension test types (14)
    # ═══════════════════════════════════════════════════════════════════════════

    elif args.test == "win_ratio":
        r_code = R_WIN_RATIO.format(
            win_ratio_theta=args.win_ratio_theta, se_approx=args.se_approx,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "must_win":
        r_code = R_MUST_WIN.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_endpoints_must=args.n_endpoints_must,
            correlation_must=args.correlation_must,
            effect_must=args.effect_must,
            solve_for_power=_sfp)

    elif args.test == "historical_controls":
        r_code = R_HISTORICAL_CONTROLS.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            p_control_current=args.p_control_current, prob_treatment=args.prob_treatment,
            historical_response=args.historical_response, historical_n=args.historical_n,
            a0_borrowing=args.a0_borrowing,
            solve_for_power=_sfp)

    elif args.test == "mams":
        r_code = R_MAMS.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_arms_mams=args.n_arms_mams, n_stages_mams=args.n_stages_mams,
            delta_effect=args.delta_effect,
            solve_for_power=_sfp)

    elif args.test == "conditional_power":
        # This test already computes conditional power given interim n; --nobs maps to n_planned
        if solve_for_power:
            n_planned = args.nobs
        else:
            n_planned = args.n_planned
        r_code = R_CONDITIONAL_POWER.format(
            alpha=args.alpha, power=args.power,
            timing=args.timing,
            observed_effect=args.observed_effect,
            planned_effect=args.planned_effect,
            n_completed=args.n_completed,
            n_planned=n_planned
        )

    elif args.test == "ni_survival":
        r_code = R_NI_SURVIVAL.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            ni_margin_surv=args.ni_margin_surv, hr_expected=args.hr_expected,
            accrual_time=args.accrual_time, followup_time=args.followup_time,
            dropout_rate=args.dropout_rate, event_rate=args.event_rate,
            solve_for_power=_sfp)

    elif args.test == "superiority_margin":
        r_code = R_SUPERIORITY_MARGIN.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            sup_margin=args.sup_margin,
            p_control_sup=args.p_control_sup,
            delta_sup=args.delta_sup,
            solve_for_power=_sfp)

    elif args.test == "assurance":
        # Assurance IS "power given n" — --nobs maps to n_assurance
        if solve_for_power:
            n_assurance = args.nobs
        else:
            n_assurance = args.n_assurance
        r_code = R_ASSURANCE.format(
            alpha=args.alpha, power=args.power,
            n_sim_assurance=args.n_sim_assurance,
            shape1_trt=args.shape1_trt,
            shape2_trt=args.shape2_trt,
            shape1_ctrl=args.shape1_ctrl,
            shape2_ctrl=args.shape2_ctrl,
            n_assurance=n_assurance,
            margin_assurance=args.margin_assurance
        )

    elif args.test == "dunnett":
        r_code = R_DUNNETT.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_groups_dunnett=args.n_groups_dunnett,
            n_control_dunnett=args.n_control_dunnett,
            effect_dunnett=args.effect_dunnett,
            solve_for_power=_sfp)

    elif args.test == "mediation":
        r_code = R_MEDIATION.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            a_path=args.a_path, b_path=args.b_path,
            sigma2_m=args.sigma2_m, sigma2_y=args.sigma2_y,
            solve_for_power=_sfp)

    elif args.test == "group_sequential":
        # Upgraded in v3.6.0: rpact-backed exact two-sample means GSD
        # (replaces the old approximate closed-form). Spending validated via choices.
        # directionUpper: FALSE only when the treatment effect is a reduction.
        _dir_upper = "FALSE" if (args.effect_gs is not None and args.effect_gs < 0) else "TRUE"
        r_code = R_GSD_MEAN.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, effect_gs=args.effect_gs,
            spending_func=args.spending_func, direction_upper=_dir_upper,
            solve_for_power=_sfp)

    elif args.test == "gsd_proportion":
        if args.gs_proportion_metric == "ratio":
            _p1, _p2 = args.p1, args.p1 * args.gs_ratio
        elif args.gs_proportion_metric == "or":
            _p1, _p2 = args.p1, (args.gs_or * args.p1) / (1 - args.p1 + args.gs_or * args.p1)
        else:
            _p1, _p2 = args.p1, args.p2
        # directionUpper: FALSE when the treatment proportion is LOWER (beneficial
        # reduction, e.g. fewer adverse events); TRUE when higher (e.g. response).
        _dir_upper = "FALSE" if (_p1 is not None and _p2 is not None and _p1 < _p2) else "TRUE"
        r_code = R_GSD_PROPORTION.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, spending_func=args.spending_func,
            p1=_p1, p2=_p2, metric=args.gs_proportion_metric,
            direction_upper=_dir_upper,
            solve_for_power=_sfp)

    elif args.test == "gsd_survival":
        _lambda2 = (0.69314718056 / args.gs_median_control) if args.gs_median_control > 0 else 0.0578
        _hr = args.hazard_ratio if args.hazard_ratio is not None else 0.7
        # HR < 1 (beneficial) -> reject on the lower side -> directionUpper = FALSE.
        _dir_upper = "FALSE" if _hr < 1 else "TRUE"
        r_code = R_GSD_SURVIVAL.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, spending_func=args.spending_func,
            lambda2=_lambda2, hr=_hr, accrual=args.accrual_time,
            followup=args.followup_time, dropout=args.dropout_rate,
            direction_upper=_dir_upper,
            solve_for_power=_sfp)

    elif args.test == "gsd_hazard":
        _lambda2 = (0.69314718056 / args.gs_median_control) if args.gs_median_control > 0 else 0.0578
        _hr = args.hazard_ratio if args.hazard_ratio is not None else 0.7
        _dir_upper = "FALSE" if _hr < 1 else "TRUE"
        r_code = R_GSD_HAZARD.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, spending_func=args.spending_func,
            lambda2=_lambda2, hr=_hr, accrual=args.accrual_time,
            followup=args.followup_time, dropout=args.dropout_rate,
            direction_upper=_dir_upper,
            solve_for_power=_sfp)

    elif args.test == "gsd_survival_sim":
        _lambda2 = (0.69314718056 / args.gs_median_control) if args.gs_median_control > 0 else 0.0578
        _hr = args.hazard_ratio if args.hazard_ratio is not None else 0.7
        _dir_upper = "FALSE" if _hr < 1 else "TRUE"
        _nobs_given = "TRUE" if args.nobs is not None else "FALSE"
        _sim_seed = args.sim_seed if args.sim_seed is not None else 42
        r_code = R_GSD_SURVIVAL_SIM.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, spending_func=args.spending_func,
            lambda2=_lambda2, hr=_hr, accrual=args.accrual_time,
            followup=args.followup_time, dropout=args.dropout_rate,
            direction_upper=_dir_upper, nobs_given=_nobs_given,
            n_simulations=args.n_simulations, sim_seed=_sim_seed)

    elif args.test == "gsd_hazard_sim":
        _lambda2 = (0.69314718056 / args.gs_median_control) if args.gs_median_control > 0 else 0.0578
        _hr = args.hazard_ratio if args.hazard_ratio is not None else 0.7
        _dir_upper = "FALSE" if _hr < 1 else "TRUE"
        _nobs_given = "TRUE" if args.nobs is not None else "FALSE"
        _sim_seed = args.sim_seed if args.sim_seed is not None else 42
        r_code = R_GSD_HAZARD_SIM.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, spending_func=args.spending_func,
            lambda2=_lambda2, hr=_hr, accrual=args.accrual_time,
            followup=args.followup_time, dropout=args.dropout_rate,
            direction_upper=_dir_upper, nobs_given=_nobs_given,
            n_simulations=args.n_simulations, sim_seed=_sim_seed)

    elif args.test == "gsd_poisson":
        # Treatment rate LOWER (rate1 < rate2) -> beneficial reduction -> FALSE.
        _dir_upper = "FALSE" if args.gs_rate1 < args.gs_rate2 else "TRUE"
        r_code = R_GSD_POISSON.format(
            kmax=_kmax, gs_type=_gs_type, gs_gamma=_gs_gamma,
            futility_params=_futil_params, design_beta=_design_beta, delta_frag=_delta_frag,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, spending_func=args.spending_func,
            rate1=args.gs_rate1, rate2=args.gs_rate2, ptime=args.gs_poisson_time,
            direction_upper=_dir_upper,
            solve_for_power=_sfp)

    elif args.test == "adaptive":
        # Validate adaptive type against allowlist
        _allowed_adaptive = ["SSR", "Population", "Combination"]
        if args.adaptive_type not in _allowed_adaptive:
            print(t("error.adaptive_type_must_be_one_of", options=", ".join(_allowed_adaptive)))
            sys.exit(1)
        r_code = R_ADAPTIVE.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_stages_adapt=args.n_stages_adapt, effect_adaptive=args.effect_adaptive,
            adaptive_type=args.adaptive_type,
            solve_for_power=_sfp)

    elif args.test == "survival_exact":
        r_code = R_SURVIVAL_EXACT.format(
            alpha_exact=args.alpha_exact, power_exact=args.power_exact, nobs=args.nobs,
            hr_exact=args.hr_exact, accrual_exact=args.accrual_exact,
            followup_exact=args.followup_exact, dropout_exact=args.dropout_exact,
            event_rate_exact=args.event_rate_exact, n_stages_exact=args.n_stages_exact,
            solve_for_power=_sfp)

    elif args.test == "survival_equivalence":
        r_code = R_SURVIVAL_EQUIVALENCE.format(
            eq_margin_surv=args.eq_margin_surv, hr_expected=args.hr_expected,
            accrual_time=args.accrual_time, followup_time=args.followup_time,
            dropout_rate=args.dropout_rate, event_rate=args.event_rate,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "survival_superiority":
        r_code = R_SURVIVAL_SUPERIORITY.format(
            sup_margin_surv=args.sup_margin_surv, hr_expected=args.sup_hr,
            accrual_time=args.accrual_time, followup_time=args.followup_time,
            dropout_rate=args.dropout_rate, event_rate=args.event_rate,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "cox_covariate":
        r_code = R_COX_COVARIATE.format(
            cox_hr=args.cox_hr, cox_r2=args.cox_r2, cox_prev=args.cox_prev,
            cox_event_prop=args.cox_event_prop, alpha=args.alpha,
            power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "survival_one_sample":
        r_code = R_SURVIVAL_ONESAMPLE.format(
            median0=args.median0, median1=args.median1,
            accrual_time=args.accrual_time, followup_time=args.followup_time,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "competing_risks":
        r_code = R_COMPETING_RISKS.format(
            ci_control=args.ci_control, ci_treatment=args.ci_treatment,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "recurrent_events":
        r_code = R_RECURRENT_EVENTS.format(
            rate_control=args.rate_control, rate_ratio=args.rate_ratio,
            recur_followup=args.recur_followup, alpha=args.alpha,
            power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    elif args.test == "survival_historical":
        r_code = R_SURVIVAL_HISTORICAL.format(
            median0=args.median0, new_median=args.new_median,
            accrual_time=args.accrual_time, followup_time=args.followup_time,
            hist_n=args.hist_n, alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=_sfp)

    # ═════════════ PASS-coverage extension（v5.9 / v5.10）═════════════
    # 相关 / 方差 / CI 精度 / 回归 / Meta 规划 / 整群扩展 / 率扩展。
    # 与 src/r_engine/samplesize_functions.R 同源（模板见 r_templates/r_pass_ext.py）。
    elif args.test == "correlation":
        _r = args.effect if args.effect is not None else 0.3
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.correlation"), "\\n")
cat(._qt("label.corr_r"), {_r}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_correlation(r={_r}, alpha={args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.correlation"), "\\n")
cat(._qt("label.corr_r"), {_r}, "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_total_result"), ss_correlation(r={_r}, alpha={args.alpha}, power={args.power}, side="{_side}"), "\\n")
"""

    elif args.test == "variance_one":
        _s0 = args.sd if args.sd is not None else 1
        _s1 = args.effect if args.effect is not None else 1.5
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.variance_one"), "\\n")
cat(._qt("label.sd0"), {_s0}, ._qt("label.sd1"), {_s1}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_variance_one({_s0}, {_s1}, {args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.variance_one"), "\\n")
cat(._qt("label.sd0"), {_s0}, ._qt("label.sd1"), {_s1}, "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_total_result"), ss_variance_one({_s0}, {_s1}, {args.alpha}, power={args.power}, side="{_side}"), "\\n")
"""

    elif args.test == "variance_two":
        _R1 = args.effect if args.effect is not None else 2
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.variance_two"), "\\n")
cat(._qt("label.var_ratio"), {_R1}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_variance_two({_R1}, {args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.variance_two"), "\\n")
cat(._qt("label.var_ratio"), {_R1}, "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_per_group"), ss_variance_two({_R1}, {args.alpha}, power={args.power}, side="{_side}"), "\\n")
"""

    elif args.test == "cv_one":
        _cv = args.effect if args.effect is not None else 0.2
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.cv_one"), "\\n")
cat(._qt("label.cv"), {_cv}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_cv_one({_cv}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _rel = args.rel_error if args.rel_error is not None else 0.1
            r_code = R_PASS_EXT + f"""
cat(._qt("header.cv_one"), "\\n")
cat(._qt("label.cv"), {_cv}, "\\n")
cat(._qt("label.rel_error"), {_rel}, "\\n")
cat(._qt("label.n_total_result"), ss_cv_one({_cv}, rel={_rel}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "ci_mean":
        _sd = args.sd if args.sd is not None else 1
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_mean"), "\\n")
cat(._qt("label.sd0"), {_sd}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_ci_mean({_sd}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _hw = args.half_width if args.half_width is not None else 1
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_mean"), "\\n")
cat(._qt("label.sd0"), {_sd}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_total_result"), ss_ci_mean({_sd}, hw={_hw}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "ci_prop":
        _p1 = args.p1 if args.p1 is not None else 0.5
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_prop"), "\\n")
cat(._qt("label.p1"), {_p1}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_ci_prop({_p1}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _hw = args.half_width if args.half_width is not None else 0.1
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_prop"), "\\n")
cat(._qt("label.p1"), {_p1}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_total_result"), ss_ci_prop({_p1}, hw={_hw}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "ci_or":
        _p0 = args.p0 if args.p0 is not None else 0.3
        _or = args.effect if args.effect is not None else 2
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_or"), "\\n")
cat(._qt("label.p0"), {_p0}, ._qt("label.odds_ratio"), {_or}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_ci_or({_p0}, {_or}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _hw = args.half_width if args.half_width is not None else 0.5
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_or"), "\\n")
cat(._qt("label.p0"), {_p0}, ._qt("label.odds_ratio"), {_or}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_per_group"), ss_ci_or({_p0}, {_or}, hw={_hw}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "ci_rr":
        _p0 = args.p0 if args.p0 is not None else 0.3
        _rr = args.effect if args.effect is not None else 1.5
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_rr"), "\\n")
cat(._qt("label.p0"), {_p0}, ._qt("label.rate_ratio"), {_rr}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_ci_rr({_p0}, {_rr}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _hw = args.half_width if args.half_width is not None else 0.3
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_rr"), "\\n")
cat(._qt("label.p0"), {_p0}, ._qt("label.rate_ratio"), {_rr}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_per_group"), ss_ci_rr({_p0}, {_rr}, hw={_hw}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "ci_cor":
        _r = args.effect if args.effect is not None else 0.4
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_cor"), "\\n")
cat(._qt("label.corr_r"), {_r}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_ci_cor({_r}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _hw = args.half_width if args.half_width is not None else 0.15
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_cor"), "\\n")
cat(._qt("label.corr_r"), {_r}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_total_result"), ss_ci_cor({_r}, hw={_hw}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "ci_icc":
        _icc = args.icc if args.icc is not None else 0.3
        _k = args.m if args.m is not None else 2
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_icc"), "\\n")
cat(._qt("label.icc"), {_icc}, ._qt("label.icc_k"), {_k}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_ci_icc({_icc}, k={_k}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            _hw = args.half_width if args.half_width is not None else 0.15
            r_code = R_PASS_EXT + f"""
cat(._qt("header.ci_icc"), "\\n")
cat(._qt("label.icc"), {_icc}, ._qt("label.icc_k"), {_k}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_total_result"), ss_ci_icc({_icc}, k={_k}, hw={_hw}, alpha={args.alpha}), "\\n")
"""

    elif args.test == "regression_linear":
        _u = args.u_pred if args.u_pred is not None else 3
        _f2 = args.f2 if args.f2 is not None else 0.15
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.regression_linear"), "\\n")
cat(._qt("label.u_pred"), {_u}, ._qt("label.f2"), {_f2}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_regression_linear({_u}, {_f2}, {args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.regression_linear"), "\\n")
cat(._qt("label.u_pred"), {_u}, ._qt("label.f2"), {_f2}, "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_total_result"), ss_regression_linear({_u}, {_f2}, {args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "meta_planning":
        _et = args.effect_type if args.effect_type is not None else "smd"
        _eff = args.effect if args.effect is not None else 0.3
        _N = args.n_per_study if args.n_per_study is not None else 100
        _i2r = "NULL" if args.i2 is None else str(args.i2)
        _Rr = "NULL" if args.R is None else str(args.R)
        _e0 = "NULL" if args.effect0 is None else str(args.effect0)
        _cv = "NULL" if args.cluster_cv is None else str(args.cluster_cv)
        _p0 = args.p0 if args.p0 is not None else 0.3
        _m = args.m if args.m is not None else 20
        _icc = args.icc if args.icc is not None else 0.05
        _common = (f"R={_Rr}, alpha={args.alpha}, side=\"{_side}\", p0={_p0}, m={_m}, "
                   f"icc={_icc}, cov={_cv}, effect0={_e0}")
        # sweep / DE 回显内部自行传 R（不使用主调用的 R 直输值）
        _common_nr = (f"alpha={args.alpha}, side=\"{_side}\", p0={_p0}, m={_m}, "
                      f"icc={_icc}, cov={_cv}, effect0={_e0}")
        # 异质性扫描（方案 §4B/§4C）：I²∈{0,.25,.5,.75,.9} → 目标功效下所需 K
        _sweep = f"""
het_i2s <- c(0, 0.25, 0.5, 0.75, 0.9)
het_Ks <- sapply(het_i2s, function(x) ss_meta_planning("{_et}", {_eff}, {_N}, R = if (x >= 1) 1e6 else x/(1-x), power={args.power}, {_common_nr}))
cat(._qt("label.meta_het_sweep"), "\\n")
for (het_i in seq_along(het_i2s)) cat("  I2=", het_i2s[het_i], " K=", het_Ks[het_i], "\\n")
"""
        # 群随机回显：DE 与 N' = N/DE（cov=NULL → 等簇大小）
        _de_echo = f"""
het_DE <- 1 + (((if (is.null({_cv})) 0 else {_cv})^2 + 1) * {_m} - 1) * {_icc}
cat(._qt("label.meta_de"), het_DE, "\\n")
cat(._qt("label.meta_n_eff"), {_N} / het_DE, "\\n")
"""
        if args.k_studies is not None:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.meta_planning"), "\\n")
cat(._qt("label.effect_type"), "{_et}", ._qt("label.effect"), {_eff}, ._qt("label.n_per_study"), {_N}, "\\n")
cat(._qt("label.i2"), {_i2r}, "\\n")
cat(._qt("label.k_studies"), {args.k_studies}, "\\n")
cat(._qt("label.achieved_power"), ss_meta_planning("{_et}", {_eff}, {_N}, i2={_i2r}, K={args.k_studies}, {_common}), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.meta_planning"), "\\n")
cat(._qt("label.effect_type"), "{_et}", ._qt("label.effect"), {_eff}, ._qt("label.n_per_study"), {_N}, "\\n")
cat(._qt("label.i2"), {_i2r}, "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.k_studies"), ss_meta_planning("{_et}", {_eff}, {_N}, i2={_i2r}, power={args.power}, {_common}), "\\n")
"""
        r_code += _sweep + (_de_echo if _et == "cluster" else "")

    elif args.test == "regression_logistic":
        _p0 = args.p0 if args.p0 is not None else 0.3
        _or = args.effect if args.effect is not None else 2
        _xt = args.x_type if args.x_type is not None else "continuous"
        _q = args.q if args.q is not None else 0.5
        _r2 = args.r2 if args.r2 is not None else 0
        _xtra = ""
        if _xt == "binary":
            _xtra = '\ncat(._qt("label.px1"), %s, "\\n")' % _q
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.regression_logistic"), "\\n")
cat(._qt("label.covariate_type"), "{_xt}", ._qt("label.p0"), {_p0}, ._qt("label.odds_ratio"), {_or}, "\\n"){_xtra}
cat(._qt("label.r2"), {_r2}, ._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_regression_logistic({_p0}, {_or}, x_type="{_xt}", q={_q}, r2={_r2}, alpha={args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.regression_logistic"), "\\n")
cat(._qt("label.covariate_type"), "{_xt}", ._qt("label.p0"), {_p0}, ._qt("label.odds_ratio"), {_or}, "\\n"){_xtra}
cat(._qt("label.r2"), {_r2}, ._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_total_result"), ss_regression_logistic({_p0}, {_or}, x_type="{_xt}", q={_q}, r2={_r2}, alpha={args.alpha}, power={args.power}, side="{_side}"), "\\n")
"""

    elif args.test == "regression_poisson":
        _base = args.lambda1 if args.lambda1 is not None else 1
        _rr = args.effect if args.effect is not None else 1.3
        _mux = args.mu_x if args.mu_x is not None else 0
        _sdx = args.sd if args.sd is not None else 1
        _expo = args.t1 if args.t1 is not None else 1
        _phi = args.phi if args.phi is not None else 1
        _r2 = args.r2 if args.r2 is not None else 0
        _b0 = "log(%s)" % _base
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.regression_poisson"), "\\n")
cat(._qt("label.baseline_rate"), {_base}, ._qt("label.rate_ratio"), {_rr}, "\\n")
cat(._qt("label.mu_x"), {_mux}, ._qt("label.sd_x"), {_sdx}, ._qt("label.exposure"), {_expo}, ._qt("label.phi"), {_phi}, "\\n")
cat(._qt("label.r2"), {_r2}, ._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_regression_poisson({_b0}, {_rr}, mu_x={_mux}, sd_x={_sdx}, exposure={_expo}, phi={_phi}, r2={_r2}, alpha={args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.regression_poisson"), "\\n")
cat(._qt("label.baseline_rate"), {_base}, ._qt("label.rate_ratio"), {_rr}, "\\n")
cat(._qt("label.mu_x"), {_mux}, ._qt("label.sd_x"), {_sdx}, ._qt("label.exposure"), {_expo}, ._qt("label.phi"), {_phi}, "\\n")
cat(._qt("label.r2"), {_r2}, ._qt("label.target_power"), {args.power}, "\\n")
cat(._qt("label.n_total_result"), ss_regression_poisson({_b0}, {_rr}, mu_x={_mux}, sd_x={_sdx}, exposure={_expo}, phi={_phi}, r2={_r2}, alpha={args.alpha}, power={args.power}, side="{_side}"), "\\n")
"""

    elif args.test == "cluster_ext":
        _m = args.m if args.m is not None else 20
        _icc = args.icc if args.icc is not None else 0.05
        _cv = args.cv_cluster if args.cv_cluster is not None else 0
        _ratio = args.ratio if args.ratio is not None else 1
        _nindiv = "NULL" if args.n_indiv is None else str(args.n_indiv)
        _effv = "NULL" if args.effect is None else str(args.effect)
        if solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.cluster_ext"), "\\n")
cat(._qt("label.cluster_m"), {_m}, ._qt("label.icc"), {_icc}, ._qt("label.cv_cluster"), {_cv}, "\\n")
res <- ss_cluster_ext(m={_m}, icc={_icc}, cv={_cv}, n_clusters={args.nobs})
cat(._qt("label.deff"), res$deff, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.effective_n"), res$n_indiv_eff, "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.cluster_ext"), "\\n")
cat(._qt("label.cluster_m"), {_m}, ._qt("label.icc"), {_icc}, ._qt("label.cv_cluster"), {_cv}, "\\n")
res <- ss_cluster_ext(n_indiv={_nindiv}, m={_m}, icc={_icc}, cv={_cv}, ratio={_ratio}, effect={_effv}, alpha={args.alpha}, power={args.power}, side="{_side}")
cat(._qt("label.deff"), res$deff, "\\n")
cat(._qt("label.n_indiv"), res$n_indiv, "\\n")
cat(._qt("label.adjusted_n_per_group"), res$n_adj, "\\n")
cat(._qt("label.n_clusters"), res$n_clusters, "\\n")
cat(._qt("label.total_clusters"), res$total_clusters, "\\n")
"""

    elif args.test == "rates_ext":
        _mode = args.rate_mode if args.rate_mode is not None else "ratio"
        _l1 = args.lambda1 if args.lambda1 is not None else 0.5
        _l2 = args.lambda2 if args.lambda2 is not None else 0.25
        _t1 = args.t1 if args.t1 is not None else 1
        _t2 = args.t2 if args.t2 is not None else 1
        _phi = args.phi if args.phi is not None else 1
        _ratio = args.ratio if args.ratio is not None else 1
        if _mode in ("single_ci", "ratio_ci"):
            if solve_for_power:
                r_code = R_PASS_EXT + f"""
cat(._qt("header.rates_ext"), "\\n")
cat(._qt("label.rate_mode"), "{_mode}", ._qt("label.rate1"), {_l1}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_half_width"), ss_rates_ext("{_mode}", {_l1}, {_l2}, {_t1}, {_t2}, {_phi}, {_ratio}, {args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
            else:
                _hw = args.half_width if args.half_width is not None else 0.2
                r_code = R_PASS_EXT + f"""
cat(._qt("header.rates_ext"), "\\n")
cat(._qt("label.rate_mode"), "{_mode}", ._qt("label.rate1"), {_l1}, "\\n")
cat(._qt("label.half_width"), {_hw}, "\\n")
cat(._qt("label.n_total_result"), ss_rates_ext("{_mode}", {_l1}, {_l2}, {_t1}, {_t2}, {_phi}, {_ratio}, {args.alpha}, hw={_hw}, side="{_side}"), "\\n")
"""
        elif solve_for_power:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.rates_ext"), "\\n")
cat(._qt("label.rate_mode"), "{_mode}", ._qt("label.rate1"), {_l1}, ._qt("label.rate2"), {_l2}, "\\n")
cat(._qt("label.rate_ratio"), {_l1}/{_l2}, ._qt("label.phi"), {_phi}, "\\n")
cat(._qt("label.given_n"), {args.nobs}, "\\n")
cat(._qt("label.achieved_power"), ss_rates_ext("{_mode}", {_l1}, {_l2}, {_t1}, {_t2}, {_phi}, {_ratio}, {args.alpha}, n={args.nobs}, side="{_side}"), "\\n")
"""
        else:
            r_code = R_PASS_EXT + f"""
cat(._qt("header.rates_ext"), "\\n")
cat(._qt("label.rate_mode"), "{_mode}", ._qt("label.rate1"), {_l1}, ._qt("label.rate2"), {_l2}, "\\n")
cat(._qt("label.rate_ratio"), {_l1}/{_l2}, ._qt("label.phi"), {_phi}, "\\n")
cat(._qt("label.target_power"), {args.power}, "\\n")
res <- ss_rates_ext("{_mode}", {_l1}, {_l2}, {_t1}, {_t2}, {_phi}, {_ratio}, {args.alpha}, power={args.power}, side="{_side}")
cat(._qt("label.n1_result"), res$n1, ._qt("label.n2_result"), res$n2, ._qt("label.n_total_result"), res$total, "\\n")
"""

    else:
        print(t("error.unknown_test")); sys.exit(1)
    return r_code


# ═════════════════════════════════════════════════════════════════════════════
# 4. 确定性拼码 API（dev-only）
# ═════════════════════════════════════════════════════════════════════════════
# 按结构化 {test, params} 确定性拼出 R 源码，**不依赖 LLM**。历史上 coze 工作流的
# template_resolver_node 曾直接 import 本函数；现行 coze 架构为「单 dispatch 节点
# 直调 src/r_engine/ R 引擎」，无 Python 拼码调用方，本函数仅服务本地开发/回归
# （与 LocalRBackend.build_code 完全同源：复用 r_templates / I18N_R / ADAPTIVE_SIM_R）。

# 本地控制标志与派生量：不应进入拼码用的 args
_BUILD_CODE_EXCLUDE = frozenset({
    "yes", "dry_run", "show_code", "install_all_packages", "test",
    "solve_for_power", "alt", "d_val",
})


def build_r_code(test, params, ctx=None, curve=False, locale=None):
    """为 coze 端提供**确定性** R 源码拼装 API（不依赖 LLM）。

    参数：
      test   : str，与 CLI --test 取值一致
      params : dict，结构同 adapters/coze_client.build_params 的输出
               （计算参数 + 派生量 solve_for_power / alt / d_val）
      ctx    : dict，可选覆盖；缺省从 params 推导
               （需含 solve_for_power / alt / d_val，可选 curve）
      curve  : bool，是否走曲线模式（与 ctx["curve"] 等效）
      locale : "zh" | "en" | None，强制覆盖 I18N_R 的界面语言；None 时
               沿用 I18N_R 自身的 OS 自动探测（含 zh 则中文）

    返回：
      完整、可直接 `Rscript` 执行的 R 源码字符串（含 I18N_R 本地化前导，
      与本地 run_r 写入临时文件的内容一致）。

    异常：
      若 test 不被支持或参数非法触发内部 sys.exit，会转换为 ValueError
      并附带已打印的提示，避免 coze 工作流进程被 sys.exit 直接终止。
    """
    # 1) 用权威 CLI 解析器构造全默认 Namespace（默认值与 CLI 永远一致）
    try:
        from samplesize_power import build_parser
        args = build_parser().parse_args([])
    except Exception as e:                       # noqa: BLE001
        raise RuntimeError(
            "拼码失败：无法加载 build_parser（请确认技能根 scripts/samplesize_power.py "
            "存在且在 import 路径上）：%s" % e)

    # 2) 用请求参数覆盖默认值（跳过控制标志与派生量）
    for k, v in (params or {}).items():
        if k in _BUILD_CODE_EXCLUDE:
            continue
        setattr(args, k, v)
    args.test = test

    # 3) 构造 ctx（派生量优先取 params，其次 ctx 覆盖）
    p = params or {}
    ctx = dict(ctx or {})
    ctx.setdefault("solve_for_power", bool(p.get("solve_for_power", False)))
    ctx.setdefault("alt", p.get("alt", "two.sided"))
    ctx.setdefault("d_val", p.get("d_val"))
    ctx.setdefault("curve", bool(curve))

    # 4) 复用现有拼码逻辑；捕获内部 sys.exit，转成异常（不杀 coze 进程）
    import contextlib
    import io
    buf = io.StringIO()
    backend = LocalRBackend()
    try:
        with contextlib.redirect_stdout(buf):
            r_core = backend.build_code(test, args, ctx)
    except SystemExit:
        hint = buf.getvalue().strip()
        raise ValueError(
            "R 代码拼装失败 (test=%s)：%s"
            % (test, hint or "参数不合法或检验类型不支持"))
    if not r_core:
        raise ValueError("R 代码拼装返回空 (test=%s)" % test)

    # 5) 拼装可直接执行的完整脚本（与本地 run_r 写入临时文件的内容一致）
    #    I18N_R 载入时会按 OS 自动设 .t_lang；若请求显式指定 locale，
    #    在 I18N_R 之后、r_core 之前覆盖 .t_lang，使 t() 调用时生效。
    locale_line = ""
    if locale in ("zh", "en"):
        locale_line = '\n.t_lang <- "%s"  # coze 请求显式指定的界面语言\n' % locale
    return "options(echo = FALSE)\n" + I18N_R + "\n" + locale_line + r_core


# ═════════════════════════════════════════════════════════════════════════════
# 3. R 包批量安装（原 --install-all-packages 分支，属 R 域，随本文件一同剔除）
# ═════════════════════════════════════════════════════════════════════════════

def install_all_packages(args):
    """安装本技能 R 端依赖的全部 CRAN 包。默认只打印命令，--run-install 才执行。"""
    # gsDesign 已移除（2026-08-18）：rpact 覆盖其 95%+ 功能且数值一致；
    # 如个别消耗函数形状（sfHSD/sfTrim 等）需要，运行时按需动态安装。
    pkgs = ["TrialSize", "pwr", "rpact", "PowerTOST",
            "simr", "lme4", "pROC", "powerSurvEpi", "survival"]
    r_cmd = (
        'pkgs <- c(%s)\n'
        'install.packages(pkgs, repos="https://cran.r-project.org")\n'
        % ", ".join('"%s"' % p for p in pkgs)
    )
    if not args.run_install:
        # 默认安全模式：只打印命令，不联网安装
        print("=" * 60)
        print(t("install.cmd_header"))
        print("=" * 60)
        print(r_cmd)
        print("=" * 60)
        print(t("install.cran_warning", n=len(pkgs)))
        print(t("install.confirm_prompt"))
        print("  python samplesize_power.py --install-all-packages --run-install")
        print(t("install.manual_alt"))
        return
    # 显式二次确认后才执行 —— 且执行前完整打印将要运行的 R 代码（透明审计）
    print("=" * 60)
    print(t("install.network_warning_en"))
    print("=" * 60)
    script_dir = _HERE
    r_script = r_cmd + 'cat("\\nDone. Installed", length(pkgs), "packages.\\n")\n'
    r_file = os.path.join(script_dir, "_install_packages.R")
    print(t("install.code_header"))
    print(r_script)
    print("=" * 60)
    with open(r_file, "w") as f:
        f.write(r_script)
    # Containment: r_file must live inside the skill dir.
    if os.path.dirname(os.path.realpath(r_file)) != os.path.realpath(script_dir):
        print(t("error.invalid_install_path"))
        return
    rscript = find_rscript()
    if is_valid_rscript(rscript):
        # NOTE: invoked as a list (no shell) -> no command injection.
        result = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=600)
        print(sanitize_output(result.stdout))
        if result.stderr:
            print(sanitize_output(result.stderr))
    else:
        print(t("error.rscript_not_found_install"))


# ═════════════════════════════════════════════════════════════════════════════
# 4. ComputeBackend 实现
# ═════════════════════════════════════════════════════════════════════════════

class LocalRBackend(ComputeBackend):
    """本地 Rscript 后端：拼接 R 源码 →（经 --yes 确认后）执行 → 回传结果。

    与 CozeBackend 的差异：
      - 计算发生在本机 Rscript，而非 coze 服务；
      - figures 由 R 直接写 PNG 到磁盘（路径经 meta['png_path'] 回传），
        不像 coze 那样回传 SVG/HTML 内容。
    """

    name = "local-r"
    requires_confirmation = True      # 本机启动 Rscript → 沿用 v3.x 安全预览语义

    def preview(self, test, args, ctx):
        """返回将要执行的 R 源码，并缓存以免 compute 时重复拼接。"""
        code = self.build_code(test, args, ctx)
        ctx["_prebuilt_r"] = code
        return code

    # ── 三种 R 代码入口 ──
    def build_code(self, test, args, ctx) -> str:
        if test == "adaptive_simulate":
            return build_adaptive_sim_r_code(args).lstrip("\n")
        if ctx.get("curve"):
            code = build_curve_code(args)
            if code is None:
                sys.exit(1)
            return code.lstrip("\n")
        return build_core_r_code(args, ctx).lstrip("\n")

    def compute(self, test, args, ctx) -> Result:
        r_code = ctx.get("_prebuilt_r") or self.build_code(test, args, ctx)
        res = Result(r_code=r_code, backend=self.name)
        res.meta["executed"] = False
        if not ctx.get("confirmed"):
            return res                      # 安全预览：只回代码，不执行
        output = run_r(r_code, confirmed=True)
        res.text = output
        res.meta["executed"] = True
        if ctx.get("curve"):
            res.meta["png_path"] = _curve_png_path(args)
        return res

    # ── 便利：R 是否可用 ──
    @staticmethod
    def rscript_available() -> bool:
        return is_valid_rscript(find_rscript())


def _curve_png_path(args) -> str:
    """曲线模式输出 PNG 的最终路径（与 build_curve_code 内部保持一致）。"""
    _t = os.environ.get("LOCALAPPDATA")
    _t = os.path.join(_t, "Temp") if _t else tempfile.gettempdir()
    return args.out or os.path.join(_t, "ct_curve_%s.png" % args.test)

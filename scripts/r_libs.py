#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r_libs.py -- inline R library strings for ct-samplesize

Holds the contents of the two standalone .R files as Python string constants
so they survive skill publishing (which strips .R files). At runtime the Python
layer writes them to temp files and sources them, or prepends them directly.

Contents:
  I18N_R : scripts/i18n.R  (bilingual localization for R templates)
  ADAPTIVE_SIM_R : scripts/adaptive_sim.R  (Monte-Carlo adaptive trial engine)
"""

# =============================================================================
# i18n.R -- bilingual (EN/ZH) localization for ct-samplesize R templates
# =============================================================================
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
  label.n = list(en = "N:", zh = "N:")
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
"""

# =============================================================================
# adaptive_sim.R -- Adaptive / group-sequential trial Monte-Carlo simulator
# =============================================================================
ADAPTIVE_SIM_R = r"""# =============================================================================
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
  for (k in 2:K) {
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
  for (k in 2:K) {
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
                             out_png = "", out_json = "") {
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
  if (isTRUE(visualize)) {
    p <- if (nzchar(out_png)) out_png else file.path(tempdir(), paste0("adaptive_sim_", RES$design, ".png"))
    png(p, width = 800, height = 500)
    if (RES$design == "power_optimization") {
      ns <- sapply(RES$scan, function(q) q$n_per_arm)
      pw <- sapply(RES$scan, function(q) q$power)
      plot(ns, pw, type = "o", col = "red", xlab = "Sample size per arm",
           ylab = "Power", main = "Power vs sample size (group sequential)")
      abline(h = RES$target_power, lty = 2, col = "gray")
    } else {
      eb <- RES$design_config$efficacy_boundaries_Z
      if (!is.null(eb)) {
        looks <- 1:length(eb)
        plot(looks, eb, type = "b", col = "red", xlab = "Interim look",
             ylab = "Z boundary", main = "Group-sequential stopping boundaries")
        fb <- RES$design_config$futility_boundaries_Z
        if (!is.null(fb)) lines(looks[-length(looks)], fb[-length(looks)], type = "b", col = "blue", lty = 2)
      } else {
        plot(0, 0, type = "n", xlab = "", ylab = "", main = "No boundary data to plot")
      }
    }
    dev.off()
    cat("PNG saved to:", p, "\n")
  }
  if (nzchar(out_json)) {
    writeLines(to_json(RES), out_json)
    cat("JSON saved to:", out_json, "\n")
  }
  invisible(RES)
}
"""

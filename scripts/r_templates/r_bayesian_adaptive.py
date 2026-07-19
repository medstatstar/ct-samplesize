# r_bayesian_adaptive.py -- R function templates for ct-samplesize
# All algorithms are pre-written R functions (ss_*) where a power<->n relation exists.
# Assurance / Conditional Power are pre-written simulation/SSR templates (no simple inverse).
# NOTE: R_BAYESIAN is a prior-informed CLOSED-FORM FREQUENTIST approximation (the
# prior is informational only, not used in the formula). True Bayesian assurance
# is provided by R_ASSURANCE (posterior simulation).

__all__ = [
    "R_BAYESIAN",
    "R_ASSURANCE",
    "R_MAMS",
    "R_CONDITIONAL_POWER",
    "R_ADAPTIVE",
    "R_HISTORICAL_CONTROLS",
]

R_BAYESIAN = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Prior-informed sample size (CLOSED-FORM FREQUENTIST APPROXIMATION).
# NOTE: This is NOT a full Bayesian computation. The prior (a0) is informational
# only and is NOT incorporated into the sample-size formula below, which is the
# standard two-proportion z-test closed form. For true Bayesian assurance
# (posterior simulation), use the assurance template (R_ASSURANCE).
ss_prior_informed <- function(pC, pT, alpha, power=NULL, n=NULL) {{
  eff <- pC - pT
  denom <- pC*(1-pC) + pT*(1-pT)
  if (!is.null(power)) {{
    return(ceiling(((qnorm(1-alpha) + qnorm(power))^2 * denom) / eff^2))
  }} else {{
    z_b <- sqrt(n * eff^2 / denom) - qnorm(alpha)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_prior_informed(pC={pC}, pT={pT}, alpha={alpha}, n={nobs})
  cat(t("header.prior_power"), "\\n")
  cat(t("label.method"), "\\n")
  cat(t("label.prior_a0"), {a0}, "\\n")
  cat(t("label.effective_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_prior_informed(pC={pC}, pT={pT}, alpha={alpha}, power={power})
  cat(t("header.prior_n"), "\\n")
  cat(t("label.method"), "\\n")
  cat(t("label.prior_a0"), {a0}, "\\n")
  cat(t("label.effective_n"), n_val, "\\n")
}}
"""

R_MAMS = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Multi-Arm Multi-Stage (MAMS) — Bonferroni-adjusted closed form.
ss_mams <- function(n_arms, delta, alpha, power=NULL, n=NULL) {{
  if (!is.null(power)) {{
    return(ceiling(((qnorm(1-alpha/(2*n_arms)) + qnorm(power))^2) / delta^2))
  }} else {{
    z_b <- sqrt(n * delta^2) - qnorm(1 - alpha/(2*n_arms))
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_mams(n_arms={n_arms_mams}, delta={delta_effect}, alpha={alpha}, n={nobs})
  cat(t("header.mams_power"), "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  cat(t("label.alpha_adjusted"), round({alpha}/(2*{n_arms_mams}), 5), "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_mams(n_arms={n_arms_mams}, delta={delta_effect}, alpha={alpha}, power={power})
  cat(t("header.mams_n"), "\\n")
  cat(t("label.n_arms_mams"), {n_arms_mams}, "\\n")
  cat(t("label.n_stages_mams"), {n_stages_mams}, "\\n")
  cat(t("label.effect_size"), {delta_effect}, "\\n")
  cat(t("label.alpha_adjusted"), round({alpha}/(2*{n_arms_mams}), 5), "\\n")
  cat(t("label.n_per_group"), n_val, "\\n")
  cat(t("label.rpact_note"), "\\n")
}}
"""

R_HISTORICAL_CONTROLS = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Historical control borrowing via MAP prior (RBesT).
ss_hist_controls <- function(p_control_cur, p_treatment, historical_response,
                             historical_n, a0_borrowing, alpha, power=NULL, n=NULL) {{
  eff <- p_treatment - p_control_cur
  denom <- p_control_cur*(1-p_control_cur) + p_treatment*(1-p_treatment)
  ess <- historical_n * a0_borrowing
  if (!is.null(power)) {{
    n_no_borrow <- ceiling(((qnorm(1-alpha) + qnorm(power))^2 * denom) / eff^2)
    return(ceiling(n_no_borrow * (1 - ess / (ess + n_no_borrow))))
  }} else {{
    n_no_borrow <- n * ess / (ess - n)
    z_b <- sqrt(n_no_borrow * eff^2 / denom) - qnorm(alpha)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_hist_controls(p_control_cur={p_control_current}, p_treatment={prob_treatment},
                          historical_response={historical_response}, historical_n={historical_n},
                          a0_borrowing={a0_borrowing}, alpha={alpha}, n={nobs})
  cat(t("header.historical_power"), "\\n")
  cat(t("label.n_with_borrowing"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_hist_controls(p_control_cur={p_control_current}, p_treatment={prob_treatment},
                            historical_response={historical_response}, historical_n={historical_n},
                            a0_borrowing={a0_borrowing}, alpha={alpha}, power={power})
  cat(t("header.historical_n"), "\\n")
  cat(t("label.historical_response"), {historical_response}, "/", {historical_n}, "\\n")
  cat(t("label.current_control_rate"), {p_control_current}, "\\n")
  cat(t("label.expected_treatment_rate"), {prob_treatment}, "\\n")
  cat(t("label.n_with_borrowing"), n_val, "\\n")
}}
"""

R_ADAPTIVE = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Adaptive design (SSR) -- closed-form approximation.
# SSR target sample size ~ fixed-sample n (re-estimation preserves power at ~ fixed n).
# Population / Combination: no simple closed-form inverse.
ss_adaptive <- function(n_stages, effect, adaptive_type, alpha, power=NULL, n=NULL) {{
  z_a <- qnorm(1 - alpha/2)
  if (adaptive_type == "SSR") {{
    if (!is.null(power)) {{
      return(ceiling(((z_a + qnorm(power))^2 * 2) / effect^2))
    }} else {{
      z_b <- effect * sqrt(n/2) - z_a
      return(round(pnorm(z_b), 4))
    }}
  }}
  return(NA)  # Population / Combination: no closed-form n
}}
if ({solve_for_power}) {{
  pwr <- ss_adaptive(n_stages={n_stages_adapt}, effect={effect_adaptive},
                     adaptive_type="{adaptive_type}", alpha={alpha}, n={nobs})
  cat(t("header.adaptive_power"), "\\n")
  cat(t("label.adaptive_type"), "{adaptive_type}", "\\n")
  cat(t("label.stages"), {n_stages_adapt}, "\\n")
  cat(t("label.effect_size"), {effect_adaptive}, "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  if (is.na(pwr)) {{
    cat(t("label.use_rpact"), "\\n")
  }} else {{
    cat(t("label.achieved_power"), pwr, "\\n")
  }}
}} else {{
  n_val <- ss_adaptive(n_stages={n_stages_adapt}, effect={effect_adaptive},
                       adaptive_type="{adaptive_type}", alpha={alpha}, power={power})
  cat(t("header.adaptive_n"), "\\n")
  cat(t("label.adaptive_type"), "{adaptive_type}", "\\n")
  cat(t("label.stages"), {n_stages_adapt}, "\\n")
  cat(t("label.effect_size"), {effect_adaptive}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  if (is.na(n_val)) {{
    cat(t("label.use_rpact"), "\\n")
  }} else {{
    cat(t("label.max_n_ssr"), n_val, t("label.per_group"), "\\n")
  }}
}}
"""

R_ASSURANCE = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Bayesian Assurance (probability of successful trial)
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
n_sim <- {n_sim_assurance}
shape1_trt <- {shape1_trt}; shape2_trt <- {shape2_trt}
shape1_ctrl <- {shape1_ctrl}; shape2_ctrl <- {shape2_ctrl}
n_per_group <- {n_assurance}
margin <- {margin_assurance}
success_count <- 0
for (i in 1:n_sim) {{
  p_t <- rbeta(1, shape1_trt, shape2_trt)
  p_c <- rbeta(1, shape1_ctrl, shape2_ctrl)
  x_t <- rbinom(1, n_per_group, p_t)
  x_c <- rbinom(1, n_per_group, p_c)
  post_t <- x_t + shape1_trt
  post_c <- x_c + shape1_ctrl
  diff_samples <- rbeta(10000, post_t, n_per_group - x_t + shape2_trt) -
                  rbeta(10000, post_c, n_per_group - x_c + shape2_ctrl)
  if (mean(diff_samples > margin) > 0.95) {{
    success_count <- success_count + 1
  }}
}}
assurance <- success_count / n_sim
cat(t("header.bayesian_assurance"), "\\n")
cat(t("label.treatment_prior"), shape1_trt, ",", shape2_trt, ")\\n")
cat(t("label.control_prior"), shape1_ctrl, ",", shape2_ctrl, ")\\n")
cat(t("label.n_per_group_assurance"), n_per_group, "\\n")
cat(t("label.success_margin"), margin, "\\n")
cat(t("label.n_simulations"), n_sim, "\\n")
cat(t("label.assurance"), round(assurance * 100, 1), "%\\n")
cat(t("label.assurance_note"), "\\n")
"""

R_CONDITIONAL_POWER = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Conditional Power & Sample Size Re-estimation (SSR) - analytic closed-form
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
timing <- {timing}
observed_effect <- {observed_effect}
planned_effect <- {planned_effect}
n_completed <- {n_completed}
z_crit <- qnorm(1 - alpha_val / 2)
n_remaining <- max({n_planned} - n_completed, 1)
Z_obs <- observed_effect * sqrt(n_completed / 2)
mu_future <- planned_effect * sqrt(n_remaining / 2)
cp <- 1 - pnorm((z_crit - sqrt(timing) * Z_obs - sqrt(1 - timing) * mu_future) / sqrt(1 - timing))
if (observed_effect > 0) {{
  ssr_factor <- (planned_effect / observed_effect)^2
  n_reestimated <- ceiling({n_planned} * ssr_factor)
  cat(t("header.conditional_power"), "\\n")
  cat(t("label.planned_effect"), planned_effect, "\\n")
  cat(t("label.observed_effect"), round(observed_effect, 3), "\\n")
  cat(t("label.interim_timing"), timing * 100, "%\\n")
  cat(t("label.conditional_power_label"), round(cp * 100, 1), "%\\n")
  cat(t("label.planned_n"), {n_planned}, "\\n")
  cat(t("label.reestimated_n"), n_reestimated, "\\n")
  cat(t("label.ssr_increase"), round((ssr_factor - 1)*100, 1), "%\\n")
}} else {{
  cat(t("label.ssr_warning"), "\\n")
  cat(t("label.cp_na"), "\\n")
}}
"""

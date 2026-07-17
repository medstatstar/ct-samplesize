# r_design_special.py -- R function templates for ct-samplesize
# All algorithms are pre-written R functions (ss_*). Branches only call them.

__all__ = [
    "R_DOSE_ESCALATION",
    "R_WIN_RATIO",
    "R_MUST_WIN",
    "R_DUNNETT",
    "R_MEDIATION",
    "R_GROUP_SEQUENTIAL",
]

R_DOSE_ESCALATION = """
# Dose escalation (3+3 / CRM): heuristic design, not a power-based sample size.
ss_dose <- function(n_doses, target_dlt) {{
  lo <- n_doses * 4
  hi <- n_doses * 4 + 6
  return(c(lo, hi))
}}
rng <- ss_dose(n_doses={n_doses}, target_dlt={target_dlt})
if ({solve_for_power}) {{
  cat("\\n========== Dose Escalation (3+3 / CRM) ==========\\n")
  cat("Note: Dose-escalation is a heuristic design, not a power-based sample size.\\n")
  cat("Dose levels:", {n_doses}, "Target DLT:", "{target_dlt}", "\\n")
  cat("Given total N =", {nobs}, "approx total (3+3):", rng[1], "-", rng[2], "\\n")
  cat("A power calculation does not apply to this design.\\n")
}} else {{
  cat("\\n========== Dose Escalation (3+3 / CRM) ==========\\n")
  cat("Dose levels:", {n_doses}, "Target DLT:", "{target_dlt}", "\\n")
  cat("Approximate total (3+3):", rng[1], "-", rng[2], "\\n")
}}
"""

R_WIN_RATIO = """
# Win-Ratio (composite endpoint): closed-form log(WR) normal approximation.
ss_win_ratio <- function(win_ratio_theta, se_approx, alpha, power=NULL, n=NULL) {{
  log_wr <- log(win_ratio_theta)
  if (!is.null(power)) {{
    n_req <- ceiling(((qnorm(1-alpha/2) + qnorm(power)) / log_wr)^2 / se_approx^2)
    return(n_req)
  }} else {{
    z_b <- sqrt(n * log_wr^2 * se_approx^2) - qnorm(1-alpha/2)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_win_ratio(win_ratio_theta={win_ratio_theta}, se_approx={se_approx},
                      alpha={alpha}, n={nobs})
  cat("\\n========== Win-Ratio (Power given N) ==========\\n")
  cat("Expected Win-Ratio:", {win_ratio_theta}, "\\n")
  cat("N per group:", {nobs}, "\\n")
  cat("Achieved power:", pwr, "\\n")
}} else {{
  n_val <- ss_win_ratio(win_ratio_theta={win_ratio_theta}, se_approx={se_approx},
                        alpha={alpha}, power={power})
  cat("\\n========== Win-Ratio Composite Endpoint ==========\\n")
  cat("Method: closed-form log(WR) normal approximation\\n")
  cat("Expected Win-Ratio:", {win_ratio_theta}, "\\n")
  cat("SE approximation:", {se_approx}, "\\n")
  cat("Alpha:", {alpha}, "Power:", {power}, "\\n")
  cat("N per group:", n_val, "Total:", 2 * n_val, "\\n")
  cat("\\nNote: This is an approximation. For a precise design use\\n")
  cat("      BuyseTest::powerBuyseTest() with actual event-time data.\\n")
}}
"""

R_MUST_WIN = """
# Must-Win / Co-Primary Endpoints (all must be significant).
ss_must_win <- function(n_endpoints, corr, effect, alpha, power=NULL, n=NULL) {{
  if (!is.null(power)) {{
    power_per <- 1 - (1 - power)^(1/n_endpoints)
    inflation <- 1 + (n_endpoints - 1) * corr * 0.5
    n_per <- ceiling(((qnorm(1-alpha/2) + qnorm(power_per))^2) / effect^2)
    return(ceiling(n_per * inflation))
  }} else {{
    inflation <- 1 + (n_endpoints - 1) * corr * 0.5
    n_per <- n / inflation
    z_b_per <- sqrt(n_per * effect^2) - qnorm(1-alpha/2)
    power_per <- pnorm(z_b_per)
    return(round(1 - (1 - power_per)^n_endpoints, 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_must_win(n_endpoints={n_endpoints_must}, corr={correlation_must},
                     effect={effect_must}, alpha={alpha}, n={nobs})
  cat("\\n========== Must-Win / Co-Primary (Power given N) ==========\\n")
  cat("Number of co-primary endpoints:", {n_endpoints_must}, "\\n")
  cat("Assumed correlation:", {correlation_must}, "\\n")
  cat("Effect size per endpoint:", {effect_must}, "\\n")
  cat("N per group (total):", {nobs}, "\\n")
  cat("Overall power:", pwr, "\\n")
}} else {{
  n_val <- ss_must_win(n_endpoints={n_endpoints_must}, corr={correlation_must},
                       effect={effect_must}, alpha={alpha}, power={power})
  cat("\\n========== Must-Win / Co-Primary Endpoints ==========\\n")
  cat("Number of co-primary endpoints:", {n_endpoints_must}, "\\n")
  cat("Assumed correlation:", {correlation_must}, "\\n")
  cat("Effect size per endpoint:", {effect_must}, "\\n")
  cat("Overall alpha:", {alpha}, "Overall power:", {power}, "\\n")
  cat("N per group (inflated):", n_val, "\\n")
}}
"""

R_DUNNETT = """
# Dunnett comparisons (multiple treatments vs single control).
ss_dunnett <- function(k, n_control, eff, alpha, power=NULL, n=NULL) {{
  z_alpha <- qnorm(1 - alpha/2)
  if (k <= 10) dunnett_crit <- z_alpha + 0.5 * log(k)
  else dunnett_crit <- qnorm(1 - alpha/(2*k))
  if (!is.null(power)) {{
    n_per_arm <- ceiling(((dunnett_crit + qnorm(power))^2 * 2) / eff^2)
    return(n_control + k * n_per_arm)
  }} else {{
    n_per_arm <- (n - n_control) / k
    z_b <- sqrt(n_per_arm * eff^2 / 2) - dunnett_crit
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_dunnett(k={n_groups_dunnett}, n_control={n_control_dunnett},
                   eff={effect_dunnett}, alpha={alpha}, n={nobs})
  cat("\\n========== Dunnett (Power given N) ==========\\n")
  cat("N per treatment arm:", round(({nobs}-{n_control_dunnett})/{n_groups_dunnett}, 1), "\\n")
  cat("Total N:", {nobs}, "\\n")
  cat("Achieved power:", pwr, "\\n")
}} else {{
  total_n <- ss_dunnett(k={n_groups_dunnett}, n_control={n_control_dunnett},
                        eff={effect_dunnett}, alpha={alpha}, power={power})
  cat("\\n========== Dunnett Comparisons ==========\\n")
  cat("Number of treatment arms:", {n_groups_dunnett}, "\\n")
  cat("Control group N:", {n_control_dunnett}, "\\n")
  cat("Effect size:", {effect_dunnett}, "\\n")
  cat("Alpha:", {alpha}, "Power:", {power}, "\\n")
  cat("Total N:", total_n, "\\n")
}}
"""

R_MEDIATION = """
# Mediation effects (Sobel-test closed-form approximation).
ss_mediation <- function(a, b, sigma2_m, sigma2_y, alpha, power=NULL, n=NULL) {{
  indirect <- a * b
  se_sobel <- sqrt(a^2 * (sigma2_y/b^2) + b^2 * sigma2_m)
  if (!is.null(power)) {{
    return(ceiling(((qnorm(1-alpha/2) + qnorm(power))^2 * se_sobel^2) / indirect^2))
  }} else {{
    z_b <- sqrt(n * indirect^2 / se_sobel^2) - qnorm(1-alpha/2)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_mediation(a={a_path}, b={b_path}, sigma2_m={sigma2_m},
                      sigma2_y={sigma2_y}, alpha={alpha}, n={nobs})
  cat("\\n========== Mediation (Power given N) ==========\\n")
  cat("Indirect effect (a*b):", round({a_path}*{b_path}, 4), "\\n")
  cat("Sobel SE:", round(sqrt({a_path}^2*({sigma2_y}/{b_path}^2)+{b_path}^2*{sigma2_m}), 4), "\\n")
  cat("N:", {nobs}, "\\n")
  cat("Achieved power:", pwr, "\\n")
}} else {{
  n_val <- ss_mediation(a={a_path}, b={b_path}, sigma2_m={sigma2_m},
                        sigma2_y={sigma2_y}, alpha={alpha}, power={power})
  cat("\\n========== Mediation Effects ==========\\n")
  cat("a-path (treatment -> mediator):", {a_path}, "\\n")
  cat("b-path (mediator -> outcome):", {b_path}, "\\n")
  cat("Indirect effect (a*b):", round({a_path}*{b_path}, 4), "\\n")
  cat("Sobel SE:", round(sqrt({a_path}^2*({sigma2_y}/{b_path}^2)+{b_path}^2*{sigma2_m}), 4), "\\n")
  cat("Alpha:", {alpha}, "Power:", {power}, "\\n")
  cat("N (Sobel approximation):", n_val, "\\n")
}}
"""

R_GROUP_SEQUENTIAL = """
# Group Sequential Design (O'Brien-Fleming / Pocock) -- closed-form approximation.
# OF: final critical value ~ z_{{1-alpha/2}} (sample size ~ fixed). Pocock: mild inflation.
ss_group_seq <- function(n_interim, effect_gs, spending, alpha, power=NULL, n=NULL) {{
  k <- n_interim + 1
  z_a <- qnorm(1 - alpha/2)
  if (!is.null(power)) {{
    n_fixed <- ((z_a + qnorm(power))^2 * 2) / effect_gs^2
    # GS sample-size inflation relative to a fixed (single-stage) design
    infl <- if (spending == "Pocock") (1 + 0.03*(k-1)) else 1.0
    return(ceiling(n_fixed * infl))
  }} else {{
    # Reverse: power given n per group (OF critical value approximation)
    z_b <- effect_gs * sqrt(n/2) - z_a
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_group_seq(n_interim={n_interim}, effect_gs={effect_gs},
                      spending="{spending_func}", alpha={alpha}, n={nobs})
  cat("\\n========== Group Sequential (Power given N) ==========\\n")
  cat("Number of looks:", {n_interim} + 1, "(", {n_interim}, "interim)\\n")
  cat("Spending function:", "{spending_func}", "\\n")
  cat("Effect size:", {effect_gs}, "\\n")
  cat("N per group:", {nobs}, "\\n")
  cat("Achieved power (approx):", pwr, "\\n")
}} else {{
  n_val <- ss_group_seq(n_interim={n_interim}, effect_gs={effect_gs},
                        spending="{spending_func}", alpha={alpha}, power={power})
  cat("\\n========== Group Sequential Design ==========\\n")
  cat("Number of looks:", {n_interim} + 1, "(", {n_interim}, "interim)\\n")
  cat("Spending function:", "{spending_func}", "\\n")
  cat("Effect size:", {effect_gs}, "\\n")
  cat("Alpha:", {alpha}, "Power:", {power}, "\\n")
  cat("N per group (at final look, approx):", n_val, "\\n")
}}
"""

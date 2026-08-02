# r_survival_ext.py -- R function templates for ct-samplesize PASS-survival extensions
# All algorithms are pre-written R functions (ss_*). Branches only call them.
#
# Seven PASS-style survival designs added in v3.5.0:
#   1. survival_equivalence   -- TOST on log-HR (equivalence of two survival curves)
#   2. survival_superiority   -- superiority by a margin on log-HR
#   3. cox_covariate          -- Cox regression covariate power (Vittinghoff & McCulloch)
#   4. survival_one_sample    -- one-sample exponential (test a single arm vs null median)
#   5. competing_risks        -- compare cumulative incidence (Gray-type) of event of interest
#   6. recurrent_events       -- Andersen-Gill marginal recurrent-event rate ratio
#   7. survival_historical    -- single arm vs external historical control (log-rank)
#
# All use base-R closed-form formulas (Schoenfeld / Poisson / exponential), so they
# need NO extra R packages and are fully reproducible. Packages (rpact/powerSurvEpi)
# are intentionally NOT required here to keep the designs dependency-free and stable.

__all__ = [
    "R_SURVIVAL_EQUIVALENCE",
    "R_SURVIVAL_SUPERIORITY",
    "R_COX_COVARIATE",
    "R_SURVIVAL_ONESAMPLE",
    "R_COMPETING_RISKS",
    "R_RECURRENT_EVENTS",
    "R_SURVIVAL_HISTORICAL",
]

# ─────────────────────────────────────────────────────────────────────────────
# 1. Survival equivalence (TOST on log-HR)
# ─────────────────────────────────────────────────────────────────────────────
R_SURVIVAL_EQUIVALENCE = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# Equivalence of two survival curves via two one-sided log-rank tests (TOST).
# H0 (not equivalent): |log HR| >= log(margin); reject iff both OSTs reject at alpha.
ss_surv_equiv <- function(eq_margin, hr_expected, accrual, followup, dropout,
                          event_rate, alpha, power=NULL, n=NULL) {{
  if (eq_margin <= 1) stop("Equivalence margin (HR) must be > 1.")
  delta <- log(eq_margin)
  ev_rate <- if (event_rate > 0) event_rate else 1
  if (!is.null(power)) {{
    z_a <- qnorm(1 - alpha)
    z_b <- qnorm((1 + power) / 2)
    D <- ((2 * (z_a + z_b)) / delta) ^ 2
    ev_pg <- D / 2
    n_pg <- if (event_rate > 0) ceiling(ev_pg / event_rate) else ceiling(ev_pg)
    tot <- 2 * n_pg
    tot_drop <- if (dropout < 1) ceiling(tot / (1 - dropout)) else tot
    return(list(d=D, n_pg=n_pg, total=tot, total_drop=tot_drop))
  }} else {{
    D <- n * ev_rate
    se <- 2 / sqrt(D)
    w <- delta / se - qnorm(1 - alpha)
    return(round(2 * pnorm(w) - 1, 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_surv_equiv(eq_margin={eq_margin_surv}, hr_expected={hr_expected},
                       accrual={accrual_time}, followup={followup_time}, dropout={dropout_rate},
                       event_rate={event_rate}, alpha={alpha}, n={nobs})
  cat(t("r_header.surv_equiv_power"), "\\n")
  cat(t("label.eq_margin_hr"), {eq_margin_surv}, "\\n")
  cat(t("label.expected_hr"), {hr_expected}, "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  res <- ss_surv_equiv(eq_margin={eq_margin_surv}, hr_expected={hr_expected},
                        accrual={accrual_time}, followup={followup_time}, dropout={dropout_rate},
                        event_rate={event_rate}, alpha={alpha}, power={power})
  cat(t("r_header.surv_equiv_n"), "\\n")
  cat(t("label.eq_margin_hr"), {eq_margin_surv}, "\\n")
  cat(t("label.expected_hr"), {hr_expected}, "\\n")
  cat(t("label.accrual"), {accrual_time}, "\\n")
  cat(t("label.followup"), {followup_time}, "\\n")
  cat(t("label.event_rate"), {event_rate}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.events_required"), ceiling(res$d), "\\n")
  cat(t("label.n_per_group"), res$n_pg, "\\n")
  cat(t("label.total_n"), res$total, "\\n")
  cat(t("label.total_with_dropout"), res$total_drop, "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Survival superiority by a margin (log-HR)
# ─────────────────────────────────────────────────────────────────────────────
R_SURVIVAL_SUPERIORITY = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# Superiority by a margin on the hazard-ratio scale (log-HR).
# H0: HR >= margin  vs  H1: HR = hr_expected (< margin). One-sided alpha.
ss_surv_sup <- function(sup_margin, hr_expected, accrual, followup, dropout,
                        event_rate, alpha, power=NULL, n=NULL) {{
  if (hr_expected >= sup_margin) stop("Expected HR must be < superiority margin.")
  delta <- log(sup_margin) - log(hr_expected)
  ev_rate <- if (event_rate > 0) event_rate else 1
  if (!is.null(power)) {{
    D <- ((2 * (qnorm(1 - alpha) + qnorm(power))) ^ 2) / delta ^ 2
    ev_pg <- D / 2
    n_pg <- if (event_rate > 0) ceiling(ev_pg / event_rate) else ceiling(ev_pg)
    tot <- 2 * n_pg
    tot_drop <- if (dropout < 1) ceiling(tot / (1 - dropout)) else tot
    return(list(d=D, n_pg=n_pg, total=tot, total_drop=tot_drop))
  }} else {{
    D <- n * ev_rate
    se <- 2 / sqrt(D)
    return(round(pnorm(delta / se - qnorm(1 - alpha)), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_surv_sup(sup_margin={sup_margin_surv}, hr_expected={hr_expected},
                     accrual={accrual_time}, followup={followup_time}, dropout={dropout_rate},
                     event_rate={event_rate}, alpha={alpha}, n={nobs})
  cat(t("r_header.surv_sup_power"), "\\n")
  cat(t("label.sup_margin_hr"), {sup_margin_surv}, "\\n")
  cat(t("label.expected_hr"), {hr_expected}, "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  res <- ss_surv_sup(sup_margin={sup_margin_surv}, hr_expected={hr_expected},
                      accrual={accrual_time}, followup={followup_time}, dropout={dropout_rate},
                      event_rate={event_rate}, alpha={alpha}, power={power})
  cat(t("r_header.surv_sup_n"), "\\n")
  cat(t("label.sup_margin_hr"), {sup_margin_surv}, "\\n")
  cat(t("label.expected_hr"), {hr_expected}, "\\n")
  cat(t("label.accrual"), {accrual_time}, "\\n")
  cat(t("label.followup"), {followup_time}, "\\n")
  cat(t("label.event_rate"), {event_rate}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.events_required"), ceiling(res$d), "\\n")
  cat(t("label.n_per_group"), res$n_pg, "\\n")
  cat(t("label.total_n"), res$total, "\\n")
  cat(t("label.total_with_dropout"), res$total_drop, "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. Cox regression covariate power (Vittinghoff & McCulloch 2007, binary covariate)
# ─────────────────────────────────────────────────────────────────────────────
R_COX_COVARIATE = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# Power for a Cox-model covariate, adjusting for correlation R^2 with other covariates.
# Binary covariate (prevalence p): required EVENTS d = (z_a + z_b)^2 / ((1-R^2)*p(1-p)*beta^2),
# then n = d / pi (pi = expected event proportion). beta = log(covariate HR).
ss_cox_cov <- function(cox_hr, r2, prev, event_prop, alpha, power=NULL, n=NULL) {{
  if (r2 < 0 || r2 >= 1) stop("R^2 must be in [0, 1).")
  if (prev <= 0 || prev >= 1) stop("Covariate prevalence must be in (0, 1).")
  if (event_prop <= 0 || event_prop >= 1) stop("Event proportion must be in (0, 1).")
  beta <- log(cox_hr)
  if (!is.null(power)) {{
    d <- ((qnorm(1 - alpha / 2) + qnorm(power)) ^ 2) /
         ((1 - r2) * prev * (1 - prev) * beta ^ 2)
    return(list(d=d, n=ceiling(d / event_prop)))
  }} else {{
    d <- n * event_prop
    return(round(pnorm(sqrt(d * (1 - r2) * prev * (1 - prev) * beta ^ 2) -
                      qnorm(1 - alpha / 2)), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_cox_cov(cox_hr={cox_hr}, r2={cox_r2}, prev={cox_prev},
                    event_prop={cox_event_prop}, alpha={alpha}, n={nobs})
  cat(t("r_header.cox_cov_power"), "\\n")
  cat(t("label.cox_hr"), {cox_hr}, "\\n")
  cat(t("label.cox_r2"), {cox_r2}, "\\n")
  cat(t("label.cox_prev"), {cox_prev}, "\\n")
  cat(t("label.cox_event_prop"), {cox_event_prop}, "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  res <- ss_cox_cov(cox_hr={cox_hr}, r2={cox_r2}, prev={cox_prev},
                    event_prop={cox_event_prop}, alpha={alpha}, power={power})
  cat(t("r_header.cox_cov_n"), "\\n")
  cat(t("label.cox_hr"), {cox_hr}, "\\n")
  cat(t("label.cox_r2"), {cox_r2}, "\\n")
  cat(t("label.cox_prev"), {cox_prev}, "\\n")
  cat(t("label.cox_event_prop"), {cox_event_prop}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.events_needed"), ceiling(res$d), "\\n")
  cat(t("label.total_n"), res$n, "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 4. One-sample exponential (test a single arm vs a fixed null median)
# ─────────────────────────────────────────────────────────────────────────────
R_SURVIVAL_ONESAMPLE = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# One-sample exponential survival test: H0 median = median0 vs H1 median = median1,
# with uniform accrual (a) and fixed follow-up (f). One-sided (H1: longer survival).
ss_onesample_surv <- function(median0, median1, accrual, followup, alpha, power=NULL, n=NULL) {{
  if (median1 <= median0) stop("Alternative median must be > null median (H1: better survival).")
  lam0 <- log(2) / median0
  lam1 <- log(2) / median1
  avgf <- followup + accrual / 2
  e0 <- 1 - exp(-lam0 * avgf)
  e1 <- 1 - exp(-lam1 * avgf)
  r <- e0 / e1
  if (!is.null(power)) {{
    mu1 <- ((qnorm(1 - alpha) * sqrt(r) + qnorm(power)) / (r - 1)) ^ 2
    return(list(n=ceiling(mu1 / e1), mu0=nobs0 <- mu1 * r, mu1=mu1, lam0=lam0, lam1=lam1,
                e0=e0, e1=e1))
  }} else {{
    mu1 <- n * e1
    mu0 <- n * e0
    pw <- pnorm((r - 1) * sqrt(mu1) - qnorm(1 - alpha) * sqrt(r))
    return(list(power=round(pw, 4), mu0=mu0, mu1=mu1, lam0=lam0, lam1=lam1, e0=e0, e1=e1))
  }}
}}
if ({solve_for_power}) {{
  res <- ss_onesample_surv(median0={median0}, median1={median1},
                           accrual={accrual_time}, followup={followup_time},
                           alpha={alpha}, n={nobs})
  cat(t("r_header.onesample_surv_power"), "\\n")
  cat(t("label.median0"), {median0}, "\\n")
  cat(t("label.median1"), {median1}, "\\n")
  cat(t("label.hazard0"), round(res$lam0, 4), "\\n")
  cat(t("label.hazard1"), round(res$lam1, 4), "\\n")
  cat(t("label.events_h0"), round(res$mu0, 1), "\\n")
  cat(t("label.events_h1"), round(res$mu1, 1), "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), res$power, "\\n")
}} else {{
  res <- ss_onesample_surv(median0={median0}, median1={median1},
                           accrual={accrual_time}, followup={followup_time},
                           alpha={alpha}, power={power})
  cat(t("r_header.onesample_surv_n"), "\\n")
  cat(t("label.median0"), {median0}, "\\n")
  cat(t("label.median1"), {median1}, "\\n")
  cat(t("label.accrual"), {accrual_time}, "\\n")
  cat(t("label.followup"), {followup_time}, "\\n")
  cat(t("label.hazard0"), round(res$lam0, 4), "\\n")
  cat(t("label.hazard1"), round(res$lam1, 4), "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.events_needed"), ceiling(res$n * res$e1), "\\n")
  cat(t("label.total_n"), res$n, "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 5. Competing risks -- compare cumulative incidence of event of interest (Gray-type)
# ─────────────────────────────────────────────────────────────────────────────
R_COMPETING_RISKS = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# Compare cumulative incidence of the event of interest at time tau between two groups
# (Gray's test approximated by the two-sample proportion test on cumulative incidence).
ss_comprisk <- function(ci_control, ci_treatment, alpha, power=NULL, n=NULL) {{
  if (ci_control == ci_treatment) stop("Cumulative incidences must differ.")
  if (ci_control <= 0 || ci_control >= 1 || ci_treatment <= 0 || ci_treatment >= 1)
    stop("Cumulative incidence must be in (0, 1).")
  if (!is.null(power)) {{
    n_pg <- ceiling(((qnorm(1 - alpha / 2) + qnorm(power)) ^ 2) *
                    (ci_control * (1 - ci_control) + ci_treatment * (1 - ci_treatment)) /
                    (ci_control - ci_treatment) ^ 2)
    return(list(n_pg=n_pg, total=2 * n_pg))
  }} else {{
    n_pg <- n / 2
    z <- sqrt(n_pg * (ci_control - ci_treatment) ^ 2 /
              (ci_control * (1 - ci_control) + ci_treatment * (1 - ci_treatment))) -
          qnorm(1 - alpha / 2)
    return(round(pnorm(z), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_comprisk(ci_control={ci_control}, ci_treatment={ci_treatment},
                     alpha={alpha}, n={nobs})
  cat(t("r_header.comprisk_power"), "\\n")
  cat(t("label.ci_control"), {ci_control}, "\\n")
  cat(t("label.ci_treatment"), {ci_treatment}, "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  res <- ss_comprisk(ci_control={ci_control}, ci_treatment={ci_treatment},
                     alpha={alpha}, power={power})
  cat(t("r_header.comprisk_n"), "\\n")
  cat(t("label.ci_control"), {ci_control}, "\\n")
  cat(t("label.ci_treatment"), {ci_treatment}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.n_per_group"), res$n_pg, "\\n")
  cat(t("label.total_n"), res$total, "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 6. Recurrent events -- Andersen-Gill marginal recurrent-event rate ratio
# ─────────────────────────────────────────────────────────────────────────────
R_RECURRENT_EVENTS = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# Sample size for comparing recurrent-event rates (Poisson/Andersen-Gill marginal model).
# lambda2 = control rate (/person-year), RR = treatment/control rate ratio (< 1 better).
ss_recur <- function(rate_control, rate_ratio, followup, alpha, power=NULL, n=NULL) {{
  if (rate_ratio <= 0 || rate_ratio == 1) stop("Rate ratio must be > 0 and != 1.")
  lam2 <- rate_control
  lam1 <- rate_ratio * rate_control
  if (!is.null(power)) {{
    n_pg <- ceiling(((qnorm(1 - alpha / 2) + qnorm(power)) ^ 2) *
                    (lam1 + lam2) / (followup * (lam1 - lam2) ^ 2))
    return(list(n_pg=n_pg, total=2 * n_pg, pt=n_pg * followup))
  }} else {{
    mu1 <- (n / 2) * lam1 * followup
    mu2 <- (n / 2) * lam2 * followup
    z <- (mu2 - mu1) / sqrt(mu1 + mu2) - qnorm(1 - alpha / 2)
    return(round(pnorm(z), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_recur(rate_control={rate_control}, rate_ratio={rate_ratio},
                  followup={recur_followup}, alpha={alpha}, n={nobs})
  cat(t("r_header.recur_power"), "\\n")
  cat(t("label.rate_control"), {rate_control}, "\\n")
  cat(t("label.rate_ratio"), {rate_ratio}, "\\n")
  cat(t("label.recur_followup"), {recur_followup}, "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  res <- ss_recur(rate_control={rate_control}, rate_ratio={rate_ratio},
                  followup={recur_followup}, alpha={alpha}, power={power})
  cat(t("r_header.recur_n"), "\\n")
  cat(t("label.rate_control"), {rate_control}, "\\n")
  cat(t("label.rate_ratio"), {rate_ratio}, "\\n")
  cat(t("label.recur_followup"), {recur_followup}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.person_time"), round(res$pt, 1), "\\n")
  cat(t("label.n_per_group"), res$n_pg, "\\n")
  cat(t("label.total_n"), res$total, "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 7. Single arm vs external historical control (log-rank, one-sample style)
# ─────────────────────────────────────────────────────────────────────────────
R_SURVIVAL_HISTORICAL = """
# Source i18n translations
# i18n.R (I18N_R) is prepended by run_r() at execution time; t() is available.

# Single treatment arm compared to an external historical control.
# H0: new-arm median = historical median (worse/equal) vs H1: longer survival.
# One-sample exponential structure with uniform accrual + fixed follow-up.
ss_histctrl <- function(hist_median, new_median, accrual, followup, hist_n, alpha, power=NULL, n=NULL) {{
  if (new_median <= hist_median) stop("New-arm median must be > historical control median.")
  lam0 <- log(2) / hist_median
  lam1 <- log(2) / new_median
  avgf <- followup + accrual / 2
  e0 <- 1 - exp(-lam0 * avgf)
  e1 <- 1 - exp(-lam1 * avgf)
  r <- e0 / e1
  if (!is.null(power)) {{
    mu1 <- ((qnorm(1 - alpha) * sqrt(r) + qnorm(power)) / (r - 1)) ^ 2
    return(list(n=ceiling(mu1 / e1), mu0=mu1 * r, mu1=mu1, lam0=lam0, lam1=lam1, e0=e0, e1=e1))
  }} else {{
    mu1 <- n * e1
    mu0 <- n * e0
    pw <- pnorm((r - 1) * sqrt(mu1) - qnorm(1 - alpha) * sqrt(r))
    return(list(power=round(pw, 4), mu0=mu0, mu1=mu1, lam0=lam0, lam1=lam1, e0=e0, e1=e1))
  }}
}}
if ({solve_for_power}) {{
  res <- ss_histctrl(hist_median={median0}, new_median={new_median},
                     accrual={accrual_time}, followup={followup_time}, hist_n={hist_n},
                     alpha={alpha}, n={nobs})
  cat(t("r_header.histctrl_power"), "\\n")
  cat(t("label.hist_median"), {median0}, "\\n")
  cat(t("label.new_median"), {new_median}, "\\n")
  cat(t("label.hist_n"), {hist_n}, "\\n")
  cat(t("label.hazard0"), round(res$lam0, 4), "\\n")
  cat(t("label.hazard1"), round(res$lam1, 4), "\\n")
  cat(t("label.events_h0"), round(res$mu0, 1), "\\n")
  cat(t("label.events_h1"), round(res$mu1, 1), "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), res$power, "\\n")
}} else {{
  res <- ss_histctrl(hist_median={median0}, new_median={new_median},
                     accrual={accrual_time}, followup={followup_time}, hist_n={hist_n},
                     alpha={alpha}, power={power})
  cat(t("r_header.histctrl_n"), "\\n")
  cat(t("label.hist_median"), {median0}, "\\n")
  cat(t("label.new_median"), {new_median}, "\\n")
  cat(t("label.hist_n"), {hist_n}, "\\n")
  cat(t("label.accrual"), {accrual_time}, "\\n")
  cat(t("label.followup"), {followup_time}, "\\n")
  cat(t("label.hazard0"), round(res$lam0, 4), "\\n")
  cat(t("label.hazard1"), round(res$lam1, 4), "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.events_needed"), ceiling(res$n * res$e1), "\\n")
  cat(t("label.total_n"), res$n, "\\n")
}}
"""

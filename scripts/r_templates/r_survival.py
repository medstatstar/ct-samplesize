# r_survival.py -- R function templates for ct-samplesize
# All algorithms are pre-written R functions (ss_*). Branches only call them.

__all__ = [
    "R_NI_SURVIVAL",
    "R_SURVIVAL_EXACT",
]

R_NI_SURVIVAL = """
library(powerSurvEpi)

# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Non-inferiority survival design. Forward via powerAnsi (fallback closed-form log-rank);
# reverse uses approx log-rank power formula.
ss_ni_survival <- function(ni_margin, hr_expected, accrual, followup, dropout,
                           event_rate, alpha, power=NULL, n=NULL) {{
  if (!is.null(power)) {{
    result <- tryCatch(powerAnsi(ratio=1, alpha=alpha, power=power, p=event_rate,
                        q=event_rate*hr_expected, delta=ni_margin,
                        T=accrual+followup, Ta=accrual, f=followup,
                        gam=dropout, TiO=ni_margin), error = function(e) NULL)
    if (!is.null(result) && !is.null(result$n) && is.finite(result$n) && result$n > 0) {{
      return(ceiling(result$n))
    }}
    D <- (qnorm(1 - alpha/2) + qnorm(power))^2 / (log(ni_margin))^2
    ev_rate <- if (event_rate > 0) event_rate else 1
    return(ceiling((D/2) / ev_rate))
  }} else {{
    events_per_group <- n/2 * event_rate
    d <- 2 * events_per_group
    z_b <- sqrt(d) * abs(log(ni_margin)) - qnorm(1-alpha/2)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_ni_survival(ni_margin={ni_margin_surv}, hr_expected={hr_expected},
                        accrual={accrual_time}, followup={followup_time}, dropout={dropout_rate},
                        event_rate={event_rate}, alpha={alpha}, n={nobs})
  cat(t("header.ni_survival_power"), "\\n")
  cat(t("label.ni_margin_hr"), {ni_margin_surv}, "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.approx_events"), round({nobs}/2*{event_rate}, 1), "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_ni_survival(ni_margin={ni_margin_surv}, hr_expected={hr_expected},
                          accrual={accrual_time}, followup={followup_time}, dropout={dropout_rate},
                          event_rate={event_rate}, alpha={alpha}, power={power})
  ev <- tryCatch(powerAnsi(ratio=1, alpha={alpha}, power={power}, p={event_rate},
                        q={event_rate}*{hr_expected}, delta={ni_margin_surv},
                        T={accrual_time}+{followup_time}, Ta={accrual_time}, f={followup_time},
                        gam={dropout_rate}, TiO={ni_margin_surv})$nEvents, error=function(e) NULL)
  cat(t("header.ni_survival_n"), "\\n")
  cat(t("label.ni_margin_hr"), {ni_margin_surv}, "\\n")
  cat(t("label.expected_hr"), {hr_expected}, "\\n")
  cat(t("label.accrual"), {accrual_time}, "\\n")
  cat(t("label.followup"), {followup_time}, "\\n")
  cat(t("label.event_rate"), {event_rate}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  if (!is.null(ev) && is.finite(ev)) cat(t("label.events_required"), ceiling(ev), "\\n")
  cat(t("label.n_per_group"), n_val, "\\n")
  cat(t("label.total_n"), 2 * n_val, "\\n")
}}
"""

R_SURVIVAL_EXACT = """
library(rpact)

# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Exact survival design via rpact. Forward getSampleSizeSurvival (fallback Schoenfeld);
# reverse getPowerSurvival (fallback Schoenfeld log-rank).
ss_survival_exact <- function(hr, accrual, followup, dropout, event_rate, n_stages,
                              alpha, power=NULL, n=NULL) {{
  design <- getDesignGroupSequential(kMax=n_stages, typeOfDesign="OF",
                                     alpha=alpha, beta=1-ifelse(is.null(power),0.1,power))
  lambda2 <- -log(1 - event_rate) / (accrual + followup)
  ev_rate <- if (event_rate > 0) event_rate else 1
  if (!is.null(power)) {{
    sv <- tryCatch(getSampleSizeSurvival(design=design, lambda2=lambda2, hazardRatio=hr,
                                accrualTime=c(0, accrual), followUpTime=followup,
                                dropoutRate1=dropout, dropoutRate2=dropout),
                   error = function(e) NULL)
    if (!is.null(sv) && !is.null(sv$numberOfSubjects1) && is.finite(sv$numberOfSubjects1) && sv$numberOfSubjects1 > 0) {{
      return(ceiling(sv$numberOfSubjects1))
    }}
    D <- (qnorm(1-alpha/2) + qnorm(power))^2 / (log(hr))^2
    return(ceiling(D / (2*ev_rate)))
  }} else {{
    max_ev <- 2 * n * ev_rate
    pw <- tryCatch(getPowerSurvival(design=design, thetaH0=hr, pi1=event_rate, pi2=event_rate*hr,
                       maxNumberOfSubjects=2*n, maxNumberOfEvents=max_ev,
                       accrualTime=accrual, dropoutRate1=dropout, dropoutRate2=dropout,
                       eventTime=accrual+followup)$overallReject,
                   error = function(e) NULL)
    if (!is.null(pw) && is.finite(pw)) return(round(pw, 4))
    D <- 2 * n * ev_rate
    z_b <- sqrt(D) * abs(log(hr)) / 2 - qnorm(1-alpha/2)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_survival_exact(hr={hr_exact}, accrual={accrual_exact}, followup={followup_exact},
                           dropout={dropout_exact}, event_rate={event_rate_exact},
                           n_stages={n_stages_exact}, alpha={alpha_exact}, n={nobs})
  cat(t("header.survival_exact_power"), "\\n")
  cat(t("label.hazard_ratio"), {hr_exact}, "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_survival_exact(hr={hr_exact}, accrual={accrual_exact}, followup={followup_exact},
                             dropout={dropout_exact}, event_rate={event_rate_exact},
                             n_stages={n_stages_exact}, alpha={alpha_exact}, power={power_exact})
  cat(t("header.survival_exact_n"), "\\n")
  cat(t("label.hazard_ratio"), {hr_exact}, "\\n")
  cat(t("label.event_rate"), {event_rate_exact}, "\\n")
  cat(t("label.accrual"), {accrual_exact}, "\\n")
  cat(t("label.followup"), {followup_exact}, "\\n")
  cat(t("label.dropout"), {dropout_exact}, "\\n")
  cat(t("label.alpha"), {alpha_exact}, t("label.power"), {power_exact}, "\\n")
  cat(t("label.n_per_group"), n_val, "\\n")
  cat(t("label.total_n"), 2 * n_val, "\\n")
}}
"""

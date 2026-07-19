# r_equivalence.py -- R function templates for ct-samplesize
# All algorithms are pre-written R functions (ss_*). Branches only call them.

__all__ = [
    "R_BLAND_ALTMAN",
    "R_EQ_MEANS",
    "R_BE_TOST",
    "R_SUPERIORITY_MARGIN",
]

R_BLAND_ALTMAN = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Bland-Altman: precision (CI half-width) calc, not a power calc.
ss_bland_altman <- function(sd_diff, w, alpha, n=NULL) {{
  z <- qnorm(1 - alpha/2)
  if (!is.null(n)) {{
    return(z * sd_diff * sqrt(2 / n))
  }} else {{
    return(ceiling(2 * (z * sd_diff / w)^2))
  }}
}}
if ({solve_for_power}) {{
  w_achieved <- ss_bland_altman(sd_diff={sd_diff}, w={w}, alpha={alpha}, n={nobs})
  cat(t("header.blank_altman_width"), "\\n")
  cat(t("label.sd_diff"), {sd_diff}, "\\n")
  cat(t("label.sample_size_pairs"), {nobs}, "\\n")
  cat(t("label.achievable_half_width"), round(w_achieved, 4), "\\n")
  cat(t("label.precision_note"), "\\n")
}} else {{
  n_val <- ss_bland_altman(sd_diff={sd_diff}, w={w}, alpha={alpha})
  cat(t("header.blank_altman_n"), "\\n")
  cat(t("label.sd_diff"), {sd_diff}, t("label.w"), {w}, "\\n")
  cat(t("label.alpha"), {alpha}, "\\n")
  cat(t("label.sample_size_pairs"), n_val, "\\n")
}}
"""

R_EQ_MEANS = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Equivalence of two means (TOST). Forward via TrialSize; reverse approx.
ss_eq_means <- function(delta, sigma, alpha, power=NULL, n=NULL) {{
  if (!is.null(power)) {{
    library(TrialSize)
    result <- tryCatch(TwoMeans.Equivalence(alpha=alpha, beta=1-power, delta=delta, sigma=sigma),
                       error = function(e) NULL)
    if (!is.null(result)) return(ceiling(result$`Total Sample Size`/2))
    return(ceiling(((qnorm(1-alpha) + qnorm(power))^2 * 2 * sigma^2) / delta^2))
  }} else {{
    n_arm <- n / 2
    se <- sigma * sqrt(2/n_arm)
    tcrit <- qnorm(1 - alpha)
    power_val <- pnorm((delta - tcrit*se)/se) - pnorm((-delta - tcrit*se)/se)
    return(round(power_val, 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_eq_means(delta={margin}, sigma={sigma}, alpha={alpha}, n={nobs})
  cat(t("header.equivalence_means_power"), "\\n")
  cat(t("label.equivalence_margin"), {margin}, "\\n")
  cat(t("label.sigma"), {sigma}, "\\n")
  cat(t("label.total_n"), {nobs}, t("label.per_arm"), {nobs}/2, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_eq_means(delta={margin}, sigma={sigma}, alpha={alpha}, power={power})
  cat(t("header.equivalence_means_n"), "\\n")
  cat(t("label.n_per_group"), n_val, "\\n")
}}
"""

R_BE_TOST = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Bioequivalence (TOST) via PowerTOST. Forward sampleN.TOST; reverse power.TOST.
ss_be_tost <- function(theta0, cv, design, alpha, power=NULL, n=NULL) {{
  library(PowerTOST)
  if (!is.null(power)) {{
    result <- sampleN.TOST(theta0=theta0, CV=cv, design=design,
                           alpha=alpha, targetpower=power, logscale=TRUE)
    n_out <- as.numeric(result[which(names(result) == "Sample size")])
    return(n_out)
  }} else {{
    result <- power.TOST(theta0=theta0, CV=cv, design=design,
                         alpha=alpha, n=n)
    return(round(result, 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_be_tost(theta0={theta0}, cv={cv}, design="{design}", alpha={alpha}, n={nobs})
  cat(t("header.bioequivalence_power"), "\\n")
  cat(t("label.theta0"), {theta0}, t("label.cv"), {cv}, t("label.design"), "{design}", "\\n")
  cat(t("label.n_per_sequence"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_be_tost(theta0={theta0}, cv={cv}, design="{design}", alpha={alpha}, power={power})
  cat(t("header.bioequivalence_n"), "\\n")
  cat(t("label.sample_size"), n_val, "\\n")
}}
"""

R_SUPERIORITY_MARGIN = """
# Source i18n translations
source(file.path("{scriptdir}", "i18n.R"))

# Superiority by a Margin: TrialSize::TwoSampleProportion.Equality + fallback.
ss_sup_margin <- function(p_control, delta_sup, sup_margin, alpha, power=NULL, n=NULL) {{
  delta <- sup_margin
  p_treatment <- p_control + delta_sup
  eff <- (p_treatment - p_control) - delta
  if (!is.null(power)) {{
    library(TrialSize)
    result <- tryCatch(
      TwoSampleProportion.Equality(alpha=alpha, beta=1-power,
                                   p1=p_treatment, p2=p_control, k=1),
      error = function(e) NA_real_)
    if (!is.na(result)) return(ceiling(result))
    n_fb <- ceiling(((qnorm(1-alpha) + qnorm(power))^2 *
      (p_control*(1-p_control) + p_treatment*(1-p_treatment))) / eff^2)
    return(n_fb)
  }} else {{
    events_per_grp <- n/2
    se <- sqrt((p_control*(1-p_control) + p_treatment*(1-p_treatment)) / (2*events_per_grp))
    z_b <- (eff/se) - qnorm(1-alpha)
    return(round(pnorm(z_b), 4))
  }}
}}
if ({solve_for_power}) {{
  pwr <- ss_sup_margin(p_control={p_control_sup}, delta_sup={delta_sup},
                       sup_margin={sup_margin}, alpha={alpha}, n={nobs})
  cat(t("header.superiority_margin_power"), "\\n")
  cat(t("label.superiority_margin"), {sup_margin}, "\\n")
  cat(t("label.control_rate"), {p_control_sup}, "\\n")
  cat(t("label.treatment_rate"), round({p_control_sup}+{delta_sup}, 3), "\\n")
  cat(t("label.total_n"), {nobs}, "\\n")
  cat(t("label.achieved_power"), pwr, "\\n")
}} else {{
  n_val <- ss_sup_margin(p_control={p_control_sup}, delta_sup={delta_sup},
                         sup_margin={sup_margin}, alpha={alpha}, power={power})
  cat(t("header.superiority_margin_n"), "\\n")
  cat(t("label.superiority_margin"), {sup_margin}, "\\n")
  cat(t("label.control_rate"), {p_control_sup}, "\\n")
  cat(t("label.treatment_rate"), round({p_control_sup}+{delta_sup}, 3), "\\n")
  cat(t("label.excess_over_margin"), round(({delta_sup}) - {sup_margin}, 3), "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.trialsize_n"), n_val, "\\n")
  cat(t("label.total_n"), 2 * n_val, "\\n")
}}
"""

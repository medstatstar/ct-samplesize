# r_equivalence.py -- R function templates for ct-samplesize
# All algorithms are pre-written R functions (ss_*). Branches only call them.

__all__ = [
    "R_BLAND_ALTMAN",
    "R_EQ_MEANS",
    "R_BE_TOST",
    "R_SUPERIORITY_MARGIN",
]

R_BLAND_ALTMAN = """
# Bland-Altman: precision (CI half-width) calc, not a power calc.
ss_bland_altman <- function(sd_diff, w, alpha, n=NULL) {{
  z <- qnorm(1 - alpha/2)
  if (!is.null(n)) {{
    # Given total N -> achievable half-width w
    return(z * sd_diff * sqrt(2 / n))
  }} else {{
    # Given target half-width w -> required n (pairs)
    return(ceiling(2 * (z * sd_diff / w)^2))
  }}
}}
if ({solve_for_power}) {{
  w_achieved <- ss_bland_altman(sd_diff={sd_diff}, w={w}, alpha={alpha}, n={nobs})
  cat("\\n========== Bland-Altman (Width given N) ==========\\n")
  cat("SD diff:", {sd_diff}, "\\n")
  cat("Sample size (pairs):", {nobs}, "\\n")
  cat("Achievable half-width w:", round(w_achieved, 4), "\\n")
  cat("Note: This is a precision (CI width) calc, not a hypothesis power calc.\\n")
}} else {{
  n_val <- ss_bland_altman(sd_diff={sd_diff}, w={w}, alpha={alpha})
  cat("\\n========== Bland-Altman Method Comparison ==========\\n")
  cat("SD diff:", {sd_diff}, "w:", {w}, "\\n")
  cat("Alpha:", {alpha}, "\\n")
  cat("Sample size (pairs):", n_val, "\\n")
}}
"""

R_EQ_MEANS = """
# Equivalence of two means (TOST). Forward via TrialSize; reverse approx.
ss_eq_means <- function(delta, sigma, alpha, power=NULL, n=NULL) {{
  if (!is.null(power)) {{
    library(TrialSize)
    result <- tryCatch(TTwoMeans.Equivalence(alpha=alpha, beta=1-power, delta=delta, sigma=sigma),
                       error = function(e) NULL)
    if (!is.null(result)) return(ceiling(result$`Total Sample Size`/2))
    # Fallback: conservative two-sample z approximation for equivalence
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
  cat("\\n========== Equivalence (Means, Power given N) ==========\\n")
  cat("Equivalence margin delta:", {margin}, "\\n")
  cat("Sigma:", {sigma}, "\\n")
  cat("Total N:", {nobs}, "per arm:", {nobs}/2, "\\n")
  cat("Achieved power (approx):", pwr, "\\n")
}} else {{
  n_val <- ss_eq_means(delta={margin}, sigma={sigma}, alpha={alpha}, power={power})
  cat("\\n========== Equivalence (Two Means) ==========\\n")
  cat("n per group:", n_val, "\\n")
}}
"""

R_BE_TOST = """
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
  cat("\\n========== Bioequivalence (Power given N) ==========\\n")
  cat("theta0:", {theta0}, "CV:", {cv}, "design:", "{design}", "\\n")
  cat("n per sequence:", {nobs}, "\\n")
  cat("Achieved power:", pwr, "\\n")
}} else {{
  n_val <- ss_be_tost(theta0={theta0}, cv={cv}, design="{design}", alpha={alpha}, power={power})
  cat("\\n========== Bioequivalence (TOST) ==========\\n")
  cat("Sample size:", n_val, "\\n")
}}
"""

R_SUPERIORITY_MARGIN = """
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
  cat("\\n========== Superiority by a Margin (Power given N) ==========\\n")
  cat("Superiority margin:", {sup_margin}, "\\n")
  cat("Control rate:", {p_control_sup}, "\\n")
  cat("Treatment rate:", round({p_control_sup}+{delta_sup}, 3), "\\n")
  cat("Total N:", {nobs}, "\\n")
  cat("Achieved power (approx):", pwr, "\\n")
}} else {{
  n_val <- ss_sup_margin(p_control={p_control_sup}, delta_sup={delta_sup},
                         sup_margin={sup_margin}, alpha={alpha}, power={power})
  cat("\\n========== Superiority by a Margin ==========\\n")
  cat("Superiority margin:", {sup_margin}, "\\n")
  cat("Control rate:", {p_control_sup}, "\\n")
  cat("Treatment rate:", round({p_control_sup}+{delta_sup}, 3), "\\n")
  cat("Excess over margin (delta_sup - sup_margin):", round(({delta_sup}) - {sup_margin}, 3), "\\n")
  cat("Alpha:", {alpha}, "Power:", {power}, "\\n")
  cat("TrialSize N per group:", n_val, "\\n")
  cat("Total N:", 2 * n_val, "\\n")
}}
"""

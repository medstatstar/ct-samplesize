# r_equivalence.py -- R code templates for ct-samplesize

__all__ = [
    "R_EQ_MEANS",
    "R_BE_TOST",
    "R_BLAND_ALTMAN",
    "R_SUPERIORITY_MARGIN",
]

R_EQ_MEANS = """
library(TrialSize)
result <- TTwoMeans.Equivalence(alpha={alpha}, beta={beta}, delta={margin}, sigma={sigma})
n <- ceiling(result$`Total Sample Size`/2)
cat("\\n========== Equivalence (Two Means) ==========\\n")
cat("n per group:", n, "\\n")
"""

R_BE_TOST = """
library(PowerTOST)
result <- sampleN.TOST(theta0={theta0}, CV={cv}, design="{design}", alpha={alpha}, targetpower={power}, logscale=TRUE)
cat("\\n========== Bioequivalence (TOST) ==========\\n")
cat("Sample size:", result[2], "\\n")
"""

R_BLAND_ALTMAN = """
sd_diff <- {sd_diff}; w <- {w}; alpha_val <- {alpha}
n <- ceiling(2 * (qnorm(1-alpha_val/2) * sd_diff / w)^2)
cat("\\n========== Bland-Altman Method Comparison ==========\\n")
cat("SD diff:", sd_diff, "w:", w, "\\n")
cat("Alpha:", "{alpha}", "\\n")
cat("Sample size (pairs):", n, "\\n")
"""

R_SUPERIORITY_MARGIN = """
# Superiority by a Margin design — via TrialSize::TwoSampleProportion.Equality
library(TrialSize)
alpha_val <- {alpha}; power_val <- {power}
delta <- {sup_margin}               # Superiority margin
p_control <- {p_control_sup}        # Control rate
p_treatment <- p_control + {delta_sup}  # Treatment rate
# TwoSampleProportion.Equality: alpha, beta, p1, p2, k
result <- tryCatch(
  TwoSampleProportion.Equality(alpha=alpha_val, beta=1-power_val,
                                p1=p_treatment, p2=p_control, k=1),
  error = function(e) NA_real_
)
eff <- (p_treatment - p_control) - delta  # Excess over margin
# Fallback: 自编两比例 Z 检验
n_fallback <- ceiling(((qnorm(1-alpha_val) + qnorm(power_val))^2 *
  (p_control*(1-p_control) + p_treatment*(1-p_treatment))) / eff^2)
cat("\\n========== Superiority by a Margin ==========\\n")
cat("Superiority margin:", delta, "\\n")
cat("Control rate:", p_control, "\\n")
cat("Treatment rate:", round(p_treatment, 3), "\\n")
cat("Excess over margin (delta_sup - sup_margin):", round(eff, 3), "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
if (!is.na(result)) {{
  cat("TrialSize::TwoSampleProportion.Equality N per group:", ceiling(result), "\\n")
  cat("Total N:", ceiling(result)*2, "\\n")
}} else {{
  cat("TrialSize 调用失败，回退至 Z 检验近似 N per group:", n_fallback, "\\n")
}}
"""


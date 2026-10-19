# r_non_inferiority.py -- R function template for non-inferiority (proportions)
# Exposed as a real R function so the Python layer only injects the definition
# and calls it (no scattered inline f-string R code).

R_NON_INFERIORITY = """
# ===== ct-samplesize: non-inferiority (two proportions) (R function) =====
# power = NULL -> solve n (return list: n_arm per group, total = 2*n_arm)
# n     = NULL -> solve power (return rounded power) given total n
ss_noninf_prop <- function(p1, p2, margin, alpha, power = NULL, n = NULL) {
  real_diff <- abs(p1 - p2)
  if (!is.null(power)) {
    # Forward: solve required n per group
    if (requireNamespace("TrialSize", quietly = TRUE)) {
      suppressMessages(library(TrialSize))
      total <- tryCatch(
        TwoSampleProportion.NIS(alpha = alpha, beta = 1 - power, p1 = p1, p2 = p2,
                                k = 1, delta = margin, margin = real_diff),
        error = function(e) NA_real_
      )
      if (!is.na(total)) {
        n_arm <- ceiling(total)
        return(list(n_arm = n_arm, total = n_arm * 2))
      }
    }
    n_approx <- ceiling(((qnorm(1 - alpha) + qnorm(power))^2 *
                         (p1 * (1 - p1) + p2 * (1 - p2))) / (margin - real_diff)^2)
    return(list(n_arm = n_approx, total = n_approx * 2))
  } else {
    # Reverse: solve power given total n
    z_b <- sqrt(n / 2 * (margin - real_diff)^2 / (p1 * (1 - p1) + p2 * (1 - p2))) - qnorm(alpha)
    return(round(pnorm(z_b), 4))
  }
}
"""

__all__ = ["R_NON_INFERIORITY"]

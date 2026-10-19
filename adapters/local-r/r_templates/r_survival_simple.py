# r_survival_simple.py -- R function template for log-rank survival sample size
# Exposed as a real R function so the Python layer only injects the definition
# and calls it (no scattered inline f-string R code).

R_SURVIVAL_SIMPLE = """
# ===== ct-samplesize: survival (log-rank) (R function) =====
# Schoenfeld-based. power = NULL -> solve events n (and per-group n if rates given)
#                    n     = NULL -> solve power given total events
ss_survival_logrank <- function(hr, alpha, power = NULL, n = NULL,
                                event_rate = NULL, accrual_time = NULL, followup_time = NULL) {
  if (!is.null(power)) {
    d <- ceiling((qnorm(1 - alpha/2) + qnorm(power))^2 / (log(hr)^2))
    if (!is.null(event_rate) && !is.na(event_rate) && event_rate > 0 &&
        !is.null(accrual_time) && !is.na(accrual_time) && !is.null(followup_time) && !is.na(followup_time) &&
        accrual_time > 0 && followup_time > 0 &&
        requireNamespace("TrialSize", quietly = TRUE)) {
      suppressMessages(library(TrialSize))
      lam1 <- -log(1 - event_rate) / followup_time
      lam2 <- lam1 * hr
      r <- tryCatch(
        TwoSampleSurvival.Equality(alpha = alpha, beta = 1 - power, lam1 = lam1, lam2 = lam2,
                                   k = 1, ttotal = accrual_time + followup_time,
                                   taccrual = accrual_time, gamma = 0),
        error = function(e) NA_real_
      )
      if (!is.na(r)) {
        return(list(d = d, n_per_group = ceiling(r), total = ceiling(r) * 2,
                    n_with_dropout = ceiling(ceiling(r) * 2 * 1.1)))
      }
    }
    n_pg <- if (!is.null(event_rate) && !is.na(event_rate) && event_rate > 0) ceiling(d / (2 * event_rate)) else NA
    return(list(d = d, n_per_group = n_pg, total = ifelse(is.na(n_pg), NA, n_pg * 2), n_with_dropout = NA))
  } else {
    z_b <- sqrt(n) * abs(log(hr)) - qnorm(1 - alpha/2)
    return(round(pnorm(z_b), 4))
  }
}
"""

__all__ = ["R_SURVIVAL_SIMPLE"]

# r_t_tests.py -- R function templates for t-tests and one-way ANOVA
# All algorithms are exposed as real R functions so the Python layer only
# injects the definition and calls it (no scattered inline f-string R code).

R_T_TESTS = """
# ===== ct-samplesize: t-tests & one-way ANOVA (R functions) =====
suppressMessages(library(pwr))

# t-test: two.sample / paired / one.sample
# power = NULL -> solve n (return per-group n)
# n     = NULL -> solve power (return rounded power)
ss_ttest <- function(type = c("two.sample", "paired", "one.sample"), d, alpha,
                     power = NULL, n = NULL, alt = "two.sided") {
  type <- match.arg(type)
  if (!is.null(power)) {
    r <- pwr.t.test(d = d, sig.level = alpha, power = power, type = type, alternative = alt)
    return(ceiling(r$n))
  } else {
    r <- pwr.t.test(d = d, sig.level = alpha, n = n, type = type, alternative = alt)
    return(round(r$power, 4))
  }
}

# One-way ANOVA (balanced design)
# power = NULL -> solve n per group
# n     = NULL -> solve power
ss_anova <- function(k, f, alpha, power = NULL, n = NULL) {
  if (!is.null(power)) {
    r <- pwr.anova.test(k = k, f = f, sig.level = alpha, power = power)
    return(ceiling(r$n))
  } else {
    r <- pwr.anova.test(k = k, f = f, sig.level = alpha, n = n)
    return(round(r$power, 4))
  }
}
"""

__all__ = ["R_T_TESTS"]

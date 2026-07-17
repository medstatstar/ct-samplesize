# r_proportions_rates.py -- R function templates for rates / ROC / cluster / etc.
# All algorithms are exposed as real R functions (bidirectional: power=NULL -> n,
# n=NULL -> power) so the Python layer only injects the definition and calls it.

R_POISSON = """
# Poisson rate comparison (two groups). power=NULL -> n/group; n=NULL -> power.
ss_poisson <- function(lambda1, lambda2, t1, t2, alpha, power = NULL, n = NULL) {
  RR <- lambda1 / lambda2
  if (!is.null(power)) {
    n <- ceiling(((qnorm(1 - alpha/2) + qnorm(power))^2 *
                  (1/(lambda1*t1) + 1/(lambda2*t2))) / (log(RR))^2)
    return(n)
  } else {
    z_b <- sqrt(n * (log(RR))^2 / (1/(lambda1*t1) + 1/(lambda2*t2))) - qnorm(1 - alpha/2)
    return(round(pnorm(z_b), 4))
  }
}
"""

R_ROC = """
# ROC sample size (two AUCs). power=NULL -> n; n=NULL -> power.
ss_roc <- function(auc0, auc1, alpha, power = NULL, n = NULL) {
  if (!is.null(power)) {
    n <- ceiling(((qnorm(1 - alpha/2) + qnorm(power))^2) /
                 (2 * (asin(sqrt(auc1)) - asin(sqrt(auc0)))^2))
    return(n)
  } else {
    z_b <- sqrt(n * 2 * (asin(sqrt(auc1)) - asin(sqrt(auc0)))^2) - qnorm(1 - alpha/2)
    return(round(pnorm(z_b), 4))
  }
}
"""

R_CLUSTER = """
# Cluster-RCT design effect. n_indiv given -> solve adjusted n & clusters;
# n_total given -> solve effective individual n per group.
ss_cluster <- function(m, icc, n_indiv = NULL, n_total = NULL) {
  deff <- 1 + (m - 1) * icc
  if (!is.null(n_indiv)) {
    n_adj <- ceiling(n_indiv * deff)
    n_clusters <- ceiling(n_adj / m)
    return(list(n_adj = n_adj, n_clusters = n_clusters,
                total = n_adj * 2, total_clusters = n_clusters * 2))
  } else {
    n_indiv_eff <- n_total / 2 / deff
    return(list(n_indiv_eff = round(n_indiv_eff, 1), n_clusters = ceiling(n_indiv_eff / m)))
  }
}
"""

R_VACCINE_EFFICACY = """
# Vaccine efficacy. power=NULL -> n/group; n=NULL -> power.
ss_vaccine <- function(vc, vt, alpha, power = NULL, n = NULL) {
  VE <- (vc - vt) / vc
  if (!is.null(power)) {
    n <- ceiling(((qnorm(1 - alpha/2) + qnorm(power))^2 * (1/vc + 1/vt)) / (log(1 - VE))^2)
    return(n)
  } else {
    z_b <- sqrt(n * (log(1 - VE))^2 / (1/vc + 1/vt)) - qnorm(1 - alpha/2)
    return(round(pnorm(z_b), 4))
  }
}
"""

R_MULTIPLE_ENDPOINTS = """
# Multiple endpoints (adjusted sample size). power=NULL -> n_adj; n=NULL -> power.
ss_multiple <- function(rho, effect, alpha, power = NULL, n = NULL) {
  if (!is.null(power)) {
    n_single <- ceiling((qnorm(1 - alpha/2) + qnorm(power))^2 / effect^2)
    n_adj <- ceiling(n_single / (1 - rho))
    return(list(n_single = n_single, n_adj = n_adj))
  } else {
    n_single <- n * (1 - rho)
    z_b <- sqrt(n_single * effect^2) - qnorm(1 - alpha/2)
    return(round(pnorm(z_b), 4))
  }
}
"""

__all__ = ["R_POISSON", "R_ROC", "R_CLUSTER", "R_VACCINE_EFFICACY", "R_MULTIPLE_ENDPOINTS"]

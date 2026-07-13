# r_proportions_rates.py -- R code templates for ct-samplesize

__all__ = [
    "R_POISSON",
    "R_ROC",
    "R_CLUSTER",
    "R_VACCINE_EFFICACY",
    "R_MULTIPLE_ENDPOINTS",
]

R_POISSON = """
lambda1 <- {lambda1}; lambda2 <- {lambda2}
t1 <- {t1}; t2 <- {t2}
alpha_val <- {alpha}; power_val <- {power}
RR <- lambda1 / lambda2
n <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_val))^2 * (1/(lambda1*t1) + 1/(lambda2*t2))) / (log(RR))^2)
cat("\\n========== Poisson Rate Comparison ==========\\n")
cat("Rate Ratio:", round(RR, 3), "\\n")
cat("Sample size per group:", n, "Total:", 2*n, "\\n")
"""

R_ROC = """
library(pROC)
auc0 <- {auc0}; auc1 <- {auc1}
n <- ceiling(((qnorm(1-{alpha}/2) + qnorm({power}))^2) / (2*(asin(sqrt(auc1)) - asin(sqrt(auc0)))^2))
cat("\\n========== ROC Sample Size ==========\\n")
cat("H0 AUC:", auc0, "H1 AUC:", auc1, "\\n")
cat("Alpha:", "{alpha}", "Power:", "{power}", "\\n")
cat("Sample size:", n, "\\n")
"""

R_CLUSTER = """
m <- {m}; icc <- {icc}
deff <- 1 + (m - 1) * icc
n_indiv <- {n_indiv}; n_adj <- ceiling(n_indiv * deff)
n_clusters_per_group <- ceiling(n_adj / m)
n_total <- n_adj * 2; n_clusters_total <- n_clusters_per_group * 2
cat("\\n========== Cluster-Randomized Design ==========\\n")
cat("DEFF:", round(deff, 3), "\\n")
cat("Adjusted n per group:", n_adj, "\\n")
cat("Clusters per group:", n_clusters_per_group, "Total:", n_clusters_total, "\\n")
cat("Total sample size:", n_total, "\\n")
"""

R_VACCINE_EFFICACY = """
ARU <- {vc}; ARV <- {vt}
VE <- (ARU - ARV) / ARU
n <- ceiling(((qnorm(1-{alpha}/2) + qnorm({power}))^2 * (1/ARU + 1/ARV)) / (log(1-VE))^2)
cat("\\n========== Vaccine Efficacy ==========\\n")
cat("VE:", round(VE*100, 1), "%\\n")
cat("n per group:", n, "Total:", 2*n, "\\n")
"""

R_MULTIPLE_ENDPOINTS = """
rho <- {rho}; effect <- {effect}; alpha_val <- {alpha}; power_val <- {power}
n_single <- ceiling((qnorm(1-alpha_val/2) + qnorm(power_val))^2 / effect^2)
n_adj <- ceiling(n_single / (1 - rho))
cat("\\n========== Multiple Endpoints ==========\\n")
cat("Correlation:", rho, "\\n")
cat("Single endpoint n:", n_single, "Adjusted:", n_adj, "\\n")
"""


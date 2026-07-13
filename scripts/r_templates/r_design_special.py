# r_design_special.py -- R code templates for ct-samplesize

__all__ = [
    "R_DOSE_ESCALATION",
    "R_WIN_RATIO",
    "R_MUST_WIN",
    "R_DUNNETT",
    "R_MEDIATION",
    "R_GROUP_SEQUENTIAL",
]

R_DOSE_ESCALATION = """
cat("\\n========== Dose Escalation (3+3 / CRM) ==========\\n")
cat("Dose levels:", {n_doses}, "Target DLT:", "{target_dlt}", "\\n")
cat("Approximate total (3+3):", {n_doses} * 4, "-", {n_doses} * 4 + 6, "\\n")
"""

R_WIN_RATIO = """
library(BuyseTest)
# Win-Ratio sample size via BuyseTest power simulation
set.seed(42)
# Parameters
win_ratio <- {win_ratio_theta}     # Expected win-ratio
alpha_val <- {alpha}; power_val <- {power}
n_per_group <- {n_sim_initial}     # Initial guess for simulation
n_sim <- {n_sim}                   # Number of simulations
# Effect size approximation (log scale)
log_wr <- log(win_ratio)
se_approx <- {se_approx}           # Standard error approximation
n_required <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_val)) / log_wr)^2 / se_approx^2)
cat("\\n========== Win-Ratio Composite Endpoint ==========\\n")
cat("Expected Win-Ratio:", win_ratio, "\\n")
cat("SE approximation:", se_approx, "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
cat("N per group:", n_required, "Total:", 2 * n_required, "\\n")
cat("\\nNote: For precise calculation, use BuyseTest::powerBuyseTest() with\\n")
cat("      actual event time data and prioritization rules.\\n")
"""

R_MUST_WIN = """
# Must-Win / Co-Primary Endpoints (2-5 endpoints)
# All endpoints must be statistically significant
set.seed(42)
alpha_val <- {alpha}
n_endpoints <- {n_endpoints_must}    # Number of co-primary endpoints
corr <- {correlation_must}           # Assumed correlation between endpoints
effect <- {effect_must}              # Standardized effect size per endpoint
# Bonferroni-adjusted power per endpoint to achieve overall power
# Using Dunnett-type correction for correlated endpoints
power_per_endpoint <- 1 - (1 - {power})^(1/n_endpoints)
# Inflation factor for correlations
inflation <- 1 + (n_endpoints - 1) * corr * 0.5
n_per_endpoint <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_per_endpoint))^2) / effect^2)
n_required <- ceiling(n_per_endpoint * inflation)
cat("\\n========== Must-Win / Co-Primary Endpoints ==========\\n")
cat("Number of co-primary endpoints:", n_endpoints, "\\n")
cat("Assumed correlation:", corr, "\\n")
cat("Effect size per endpoint:", effect, "\\n")
cat("Overall alpha:", alpha_val, "Overall power:", {power}, "\\n")
cat("Power per endpoint:", round(power_per_endpoint, 3), "\\n")
cat("N per endpoint (individual):", n_per_endpoint, "\\n")
cat("N per group (inflated):", n_required, "\\n")
"""

R_DUNNETT = """
library(MCPAN)
# Dunnett comparisons (multiple treatments vs. single control)
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
k <- {n_groups_dunnett}          # Number of treatment groups (excl. control)
n_control <- {n_control_dunnett}   # N in control group
eff <- {effect_dunnett}           # Effect size
# Dunnett adjusted sample size
# Using critical value approximation for k comparisons
z_alpha <- qnorm(1 - alpha_val/2)  # Conservative Bonferroni
if (k <= 10) {{
  # Dunnett critical values (tabulated, approximate)
  dunnett_crit <- z_alpha + 0.5 * log(k)  # Rough approximation
}} else {{
  dunnett_crit <- qnorm(1 - alpha_val/(2*k))  # Bonferroni fallback
}}
n_per_arm <- ceiling(((dunnett_crit + qnorm(power_val))^2 * 2) / eff^2)
total_n <- n_control + k * n_per_arm
cat("\\n========== Dunnett Comparisons ==========\\n")
cat("Number of treatment arms:", k, "\\n")
cat("Control group N:", n_control, "\\n")
cat("Effect size:", eff, "\\n")
cat("Dunnett critical value (approx):", round(dunnett_crit, 3), "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
cat("N per treatment arm:", n_per_arm, "\\n")
cat("Total N:", total_n, "\\n")
"""

R_MEDIATION = """
library(powerMediation)
# Mediation effects sample size
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
a <- {a_path}                # a-path (treatment -> mediator)
b <- {b_path}                # b-path (mediator -> outcome)
sigma2_m <- {sigma2_m}       # Variance of mediator
sigma2_y <- {sigma2_y}       # Variance of outcome
cprime <- {cprime}           # c' (direct effect)
n_sim <- {n_sim_mediation}   # Simulations
# Sobel test approximation for mediation
# Product-of-coefficients: a*b
indirect_effect <- a * b
se_sobel <- sqrt(a^2 * (sigma2_y/b^2) + b^2 * sigma2_m)
n_sobel <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_val))^2 * se_sobel^2) / indirect_effect^2)
# Monte Carlo approach (more accurate)
cat("\\n========== Mediation Effects ==========\\n")
cat("a-path (treatment -> mediator):", a, "\\n")
cat("b-path (mediator -> outcome):", b, "\\n")
cat("Indirect effect (a*b):", round(indirect_effect, 4), "\\n")
cat("Sobel SE:", round(se_sobel, 4), "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
cat("N (Sobel approximation):", n_sobel, "\\n")
cat("\\nNote: Use powerMediation::power.powerMediation.v2() for\\n")
cat("      exact Monte Carlo-based sample size.\\n")
"""

R_GROUP_SEQUENTIAL = """
library(gsDesign)
# Group Sequential Design with interim analyses
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
n_interim <- {n_interim}    # Number of interim looks
effect_gs <- {effect_gs}    # Expected effect size
spending <- "{spending_func}"  # Spending function: "OF", "Pocock", "WT"
# gsDesign
if (spending == "OF") {{
  design <- gsDesign(k = n_interim + 1, test.type = 2,
                     alpha = alpha_val, beta = 1 - power_val,
                     sfu = sfHsd, sfupar = 0)
}} else if (spending == "Pocock") {{
  design <- gsDesign(k = n_interim + 1, test.type = 2,
                     alpha = alpha_val, beta = 1 - power_val,
                     sfu = sfPocock)
}} else {{
  design <- gsDesign(k = n_interim + 1, test.type = 2,
                     alpha = alpha_val, beta = 1 - power_val,
                     sfu = sfHsd, sfupar = -4)
}}
# Effect size based sample size
n_fixed <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_val))^2 * 2) / effect_gs^2)
# Maximum sample size (inflation due to multiple looks)
n_max <- ceiling(design$n.I[n_interim + 1])
n_per_group <- ceiling(n_max / 2)
cat("\\n========== Group Sequential Design ==========\\n")
cat("Number of looks:", n_interim + 1, "(", n_interim, "interim)\\n")
cat("Spending function:", spending, "\\n")
cat("Effect size:", effect_gs, "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
cat("Fixed design N per group:", n_fixed, "\\n")
cat("Inflation factor:", round(design$gamma[2], 3), "\\n")
cat("Maximum sample size (total):", n_max, "\\n")
cat("N per group (at max):", n_per_group, "\\n")
cat("Efficacy boundaries (Z):", paste(round(design$upper$bound[1:(n_interim+1)], 2), collapse=", "), "\\n")
"""


# r_bayesian_adaptive.py -- R code templates for ct-samplesize

__all__ = [
    "R_BAYESIAN",
    "R_ASSURANCE",
    "R_MAMS",
    "R_CONDITIONAL_POWER",
    "R_ADAPTIVE",
    "R_HISTORICAL_CONTROLS",
]

R_BAYESIAN = """
a0 <- {a0}; pC <- {pC}; pT <- {pT}; alpha_val <- {alpha}; power_val <- {power}
eff <- pC - pT
n_min <- ceiling(((qnorm(1-alpha_val) + qnorm(power_val))^2 * (pC*(1-pC) + pT*(1-pT))) / eff^2)
cat("\\n========== Bayesian Design ==========\\n")
cat("Prior a0:", a0, "\\n")
cat("Effective n per group:", n_min, "\\n")
"""

R_ASSURANCE = """
# Bayesian Assurance (probability of successful trial)
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
n_sim <- {n_sim_assurance}           # Number of assurance simulations
shape1_trt <- {shape1_trt}; shape2_trt <- {shape2_trt}  # Treatment prior Beta
shape1_ctrl <- {shape1_ctrl}; shape2_ctrl <- {shape2_ctrl}  # Control prior Beta
n_per_group <- {n_assurance}         # Sample size to evaluate
margin <- {margin_assurance}         # Margin for success criterion
success_count <- 0
for (i in 1:n_sim) {{
  # Draw from prior
  p_t <- rbeta(1, shape1_trt, shape2_trt)
  p_c <- rbeta(1, shape1_ctrl, shape2_ctrl)
  # Generate trial data
  x_t <- rbinom(1, n_per_group, p_t)
  x_c <- rbinom(1, n_per_group, p_c)
  # Test: P(p_t - p_c > margin | data) > 0.95
  post_t <- x_t + shape1_trt
  post_c <- x_c + shape1_ctrl
  # Probability that treatment > control + margin
  diff_samples <- rbeta(10000, post_t, n_per_group - x_t + shape2_trt) -
                  rbeta(10000, post_c, n_per_group - x_c + shape2_ctrl)
  if (mean(diff_samples > margin) > 0.95) {{
    success_count <- success_count + 1
  }}
}}
assurance <- success_count / n_sim
cat("\\n========== Bayesian Assurance ==========\\n")
cat("Treatment prior: Beta(", shape1_trt, ",", shape2_trt, ")\\n")
cat("Control prior: Beta(", shape1_ctrl, ",", shape2_ctrl, ")\\n")
cat("N per group:", n_per_group, "\\n")
cat("Success margin:", margin, "\\n")
cat("Number of simulations:", n_sim, "\\n")
cat("Assurance (P(success)):", round(assurance * 100, 1), "%\\n")
cat("\\nNote: Search multiple N values to find target assurance (e.g., 80%).\\n")
"""

R_MAMS = """
library(rpact)
# Multi-Arm Multi-Stage Design
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
n_arms <- {n_arms_mams}          # Number of treatment arms (excl. control)
n_stages <- {n_stages_mams}      # Number of stages
delta <- {delta_effect}           # Standardized difference per arm
# rpact MAMS design
design <- getDesignGroupSequential(
  kMax = n_stages,
  typeOfDesign = "OF",  # O'Brien-Fleming
  alpha = alpha_val,
  beta = 1 - power_val
)
# Multi-arm adjustment (Bonferroni for n_arms comparisons)
overall_n <- ceiling(((qnorm(1-alpha_val/(2*n_arms)) + qnorm(power_val))^2) / delta^2)
n_per_stage <- ceiling(overall_n / n_stages)
cat("\\n========== Multi-Arm Multi-Stage (MAMS) ==========\\n")
cat("Number of treatment arms:", n_arms, "\\n")
cat("Number of stages:", n_stages, "\\n")
cat("Effect size per arm:", delta, "\\n")
cat("Alpha adjusted (Bonferroni):", round(alpha_val/(2*n_arms), 5), "\\n")
cat("N per group:", overall_n, "\\n")
cat("N per group per stage:", n_per_stage, "\\n")
cat("(Use rpact::getDesignMAMS for exact calculations with selection rules)\\n")
"""

R_CONDITIONAL_POWER = """
# Conditional Power & Sample Size Re-estimation (SSR) — analytic closed-form
# (rpact 4.4.0 getConditionalPower requires real trial dataInput; a design
#  calculator has none, so we use the Z-decomposition conditional power formula.)
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
timing <- {timing}                     # Timing of interim (proportion)
observed_effect <- {observed_effect}    # Observed effect at interim
planned_effect <- {planned_effect}      # Planned effect
n_completed <- {n_completed}           # N completed at interim
# Conditional power (analytic closed-form) — Z-decomposition
# rpact 4.4.0 getConditionalPower needs real trial dataInput; not available here.
z_crit <- qnorm(1 - alpha_val / 2)      # two-sided critical value
n_remaining <- max({n_planned} - n_completed, 1)
Z_obs <- observed_effect * sqrt(n_completed / 2)      # observed interim statistic (sigma=1)
mu_future <- planned_effect * sqrt(n_remaining / 2)   # H1 mean of future increment
cp <- 1 - pnorm((z_crit - sqrt(timing) * Z_obs - sqrt(1 - timing) * mu_future) / sqrt(1 - timing))
# Sample size re-estimation to achieve target conditional power
# Using inverse normal method
if (observed_effect > 0) {{
  ssr_factor <- (planned_effect / observed_effect)^2
  n_reestimated <- ceiling({n_planned} * ssr_factor)
  cat("\\n========== Conditional Power / SSR ==========\\n")
  cat("Planned effect:", planned_effect, "\\n")
  cat("Observed effect at interim:", round(observed_effect, 3), "\\n")
  cat("Interim timing:", timing * 100, "%\\n")
  cat("Conditional power (H1):", round(cp * 100, 1), "%\\n")
  cat("Planned N:", {n_planned}, "\\n")
  cat("Re-estimated N:", n_reestimated, "\\n")
  cat("SSR increase:", round((ssr_factor - 1)*100, 1), "%\\n")
}} else {{
  cat("\\nWarning: Observed effect is zero or negative — SSR not recommended.\\n")
  cat("Conditional power: N/A (effect <= 0)\\n")
}}
"""

R_ADAPTIVE = """
library(rpact)
# Adaptive design (population/sample size adaptation)
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
n_stages_adapt <- {n_stages_adapt}
effect_adaptive <- {effect_adaptive}
adaptive_type <- "{adaptive_type}"  # "SSR", "Population", "Combination"
# Using rpact for adaptive design
if (adaptive_type == "SSR") {{
  # Sample size reassessment
  design <- getDesignGroupSequential(
    kMax = n_stages_adapt,
    typeOfDesign = "asKD",
    gammaA = 1,
    alpha = alpha_val,
    beta = 1 - power_val
  )
  n_fixed <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_val))^2 * 2) / effect_adaptive^2)
  n_max <- ceiling(getSampleSizeMeans(design, means = effect_adaptive)$nSubjects[2, n_stages_adapt])
  cat("\\n========== Adaptive Design (SSR) ==========\\n")
  cat("Type: Sample Size Re-estimation\\n")
  cat("Stages:", n_stages_adapt, "\\n")
  cat("Effect size:", effect_adaptive, "\\n")
  cat("Fixed N:", n_fixed, "\\n")
  cat("Max N (adaptive):", ceiling(n_max/2), "per group\\n")
}} else if (adaptive_type == "Population") {{
  # Population enrichment
  cat("\\n========== Adaptive Design (Population) ==========\\n")
  cat("Type: Population Enrichment\\n")
  cat("Stages:", n_stages_adapt, "\\n")
  cat("Effect size:", effect_adaptive, "\\n")
  cat("Use rpact::getDesignInverseNormal() for combination test.\\n")
  cat("Requires pre-specified subgroup prevalence and effect sizes.\\n")
}} else {{
  # Combination test (inverse normal)
  cat("\\n========== Adaptive Design (Combination Test) ==========\\n")
  cat("Type: Combination Test (Inverse Normal)\\n")
  cat("Stages:", n_stages_adapt, "\\n")
  cat("Effect size:", effect_adaptive, "\\n")
  cat("See rpact documentation for stage-wise weights and bounds.\\n")
}}
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
"""

R_HISTORICAL_CONTROLS = """
library(RBesT)
# Historical control borrowing via MAP prior
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
p_control_cur <- {p_control_current}     # Current control success rate
p_treatment <- {p_treatment}             # Expected treatment rate
# Historical data
historical_response <- {historical_response}   # Historical responders
historical_n <- {historical_n}                 # Historical sample size
# MAP prior: weighted mixture of_beta components
map_prior <- mixbeta(
  comp1 = c(1, historical_response, historical_n - historical_response),
  comp2 = c(1, 1, 1)
)
# Sample size without borrowing
eff <- p_treatment - p_control_cur
n_no_borrow <- ceiling(((qnorm(1-alpha_val) + qnorm(power_val))^2 *
  (p_control_cur*(1-p_control_cur) + p_treatment*(1-p_treatment))) / eff^2)
# Effective sample size from historical borrowing
# Using a0 as weight for historical data
ess <- historical_n * {a0_borrowing}
n_with_borrow <- ceiling(n_no_borrow * (1 - ess / (ess + n_no_borrow)))
cat("\\n========== Historical Controls (MAP Borrowing) ==========\\n")
cat("Historical response:", historical_response, "/", historical_n, "\\n")
cat("MAP prior (mixture of beta):\\n")
print(map_prior)
cat("Prior ESS:", round(ess, 1), "\\n")
cat("Current control rate:", p_control_cur, "\\n")
cat("Expected treatment rate:", p_treatment, "\\n")
cat("N without borrowing:", n_no_borrow, "\\n")
cat("N with borrowing:", n_with_borrow, "\\n")
cat("Borrowing reduction:", round((1 - n_with_borrow/n_no_borrow)*100, 1), "%\\n")
"""


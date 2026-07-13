# r_survival.py -- R code templates for ct-samplesize

__all__ = [
    "R_NI_SURVIVAL",
    "R_SURVIVAL_EXACT",
]

R_NI_SURVIVAL = """
library(powerSurvEpi)
# Non-inferiority survival design
set.seed(42)
alpha_val <- {alpha}; power_val <- {power}
ni_margin <- {ni_margin_surv}        # Non-inferiority margin (HR)
hr_expected <- {hr_expected}         # Expected true HR (usually 1.0)
accrual <- {accrual_time}            # Accrual time (months)
followup <- {followup_time}          # Follow-up time (months)
dropout <- {dropout_rate}            # Annual dropout rate
# powerSurvEpi::powerAnsi
result <- powerAnsi(
  ratio = 1,
  alpha = alpha_val,
  power = power_val,
  p = {event_rate},                # Event rate in control
  q = {event_rate} * hr_expected,  # Event rate in treatment
  delta = ni_margin,
  T = accrual + followup,
  Ta = accrual,
  f = followup,
  gam = dropout,
  TiO = ni_margin                  # Non-inferiority margin
)
cat("\\n========== Non-Inferiority Survival ==========\\n")
cat("NI margin (HR):", ni_margin, "\\n")
cat("Expected HR:", hr_expected, "\\n")
cat("Accrual (months):", accrual, "\\n")
cat("Follow-up (months):", followup, "\\n")
cat("Event rate (control):", {event_rate}, "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
cat("Events required:", ceiling(result$nEvents), "\\n")
cat("N per group:", ceiling(result$n), "\\n")
cat("Total N:", ceiling(result$n) * 2, "\\n")
"""

R_SURVIVAL_EXACT = """
library(rpact)
# Exact survival design via rpact
set.seed(42)
alpha_val <- {alpha_exact}; power_val <- {power_exact}
hr_val <- {hr_exact}             # Hazard ratio
accrual_val <- {accrual_exact}   # Accrual time
followup_val <- {followup_exact} # Follow-up time
dropout_val <- {dropout_exact}   # Annual dropout rate
event_rate_val <- {event_rate_exact}  # Event rate
# rpact survival design
design <- getDesignGroupSequential(
  kMax = {n_stages_exact},
  typeOfDesign = "OF",
  alpha = alpha_val,
  beta = 1 - power_val
)
# Control hazard rate from event probability (exponential), rpact 4.4.0 HR convention
ref_period <- accrual_val + followup_val
lambda2 <- -log(1 - event_rate_val) / ref_period
# Survival sample size (lambda2 + hazardRatio; equal allocation)
sv_result <- getSampleSizeSurvival(
  design = design,
  lambda2 = lambda2,
  hazardRatio = hr_val,
  accrualTime = c(0, accrual_val),
  followUpTime = followup_val,
  dropoutRate1 = dropout_val,
  dropoutRate2 = dropout_val
)
cat("\\n========== Survival Design (Exact, rpact) ==========\\n")
cat("Hazard ratio:", hr_val, "\\n")
cat("Event rate (control):", event_rate_val, "\\n")
cat("Accrual (months):", accrual_val, "\\n")
cat("Follow-up (months):", followup_val, "\\n")
cat("Dropout (annual):", dropout_val, "\\n")
cat("Alpha:", alpha_val, "Power:", power_val, "\\n")
cat("Events required:", ceiling(sv_result$maxNumberOfEvents), "\\n")
cat("N per group:", ceiling(sv_result$numberOfSubjects1), "\\n")
cat("Total N:", ceiling(sv_result$maxNumberOfSubjects), "\\n")
"""


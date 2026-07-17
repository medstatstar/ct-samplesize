# r_mixed_model.py -- R function template for ct-samplesize
# Mixed-model power via simr simulation (wrapped in a pre-written function).

__all__ = [
    "R_MIXED_MODEL",
]

R_MIXED_MODEL = """
library(simr); library(lme4)
# Power of a mixed model given n (simulation). Returns achieved power.
ss_mixed_model <- function(n_subjects, eff, varcorr, sigma, nsim, effect_name) {{
  set.seed(42)
  n_treatment <- ceiling(n_subjects/2)
  df <- expand.grid(time = c(0, 1, 2, 3), subject = seq_len(n_subjects))
  df$treatment <- ifelse(df$subject <= n_treatment, "active", "placebo")
  model <- makeLmer(y ~ treatment * time + (1|subject),
                    fixef = c(0, eff, 0, eff/2),
                    VarCorr = {varcorr}, sigma = {sigma}, data = df)
  result <- powerSim(model, nsim = nsim, test = fcompare(y ~ time + (1|subject)))
  pwr <- summary(result)$mean
  return(round(as.numeric(pwr), 4))
}}
if ({solve_for_power}) {{
  pwr <- ss_mixed_model(n_subjects={nobs}, eff={eff}, varcorr={varcorr},
                        sigma={sigma}, nsim={nsim}, effect_name="{ename}")
  cat("\\n========== Mixed Model Power (given N) ==========\\n")
  cat("Effect:", "{ename}", "=", {eff}, "\\n")
  cat("n subjects:", {nobs}, "\\n")
  cat("Achieved power:", pwr, "\\n")
}} else {{
  set.seed(42)
  n_subjects <- 20; n_treatment <- 10
  df <- expand.grid(time = c(0, 1, 2, 3), subject = seq_len(n_subjects))
  df$treatment <- ifelse(df$subject <= n_treatment, "active", "placebo")
  model <- makeLmer(y ~ treatment * time + (1|subject),
                    fixef = c(0, {eff}, 0, {eff_half}),
                    VarCorr = {varcorr}, sigma = {sigma}, data = df)
  result <- powerSim(model, nsim = {nsim}, test = fcompare(y ~ time + (1|subject)))
  cat("\\n========== Mixed Model Power ==========\\n")
  cat("Effect:", "{ename}", "=", {eff}, "\\n")
  print(result)
  pc <- powerCurve(model, test = fcompare(y ~ time + (1|subject)),
                   along = "subject", breaks = c(10, 20, 30, 40, 50))
  cat("\\n--- Power Curve (to find n for target power ", {power}, ") ---\\n")
  print(summary(pc))
}}
"""

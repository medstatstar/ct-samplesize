# r_gsd.py -- R function templates for ct-samplesize Group-Sequential (GSD) designs
# All designs are backed by the `rpact` package (already a dependency of this skill).
#
# Five PASS-style group-sequential procedures added in v3.6.0:
#   1. group_sequential  (UPGRADED) -- two-sample means (rpact getSampleSizeMeans)
#   2. gsd_proportion    -- two proportions (rpact getSampleSizeRates)
#   3. gsd_survival      -- two survival curves / log-rank (rpact getSampleSizeSurvival)
#   4. gsd_hazard        -- two hazard rates (rpact getSampleSizeSurvival, hazard scale)
#   5. gsd_poisson       -- two Poisson rates (rpact getSampleSizeCounts)
#
# Shared design features (item 8 of the P0 plan):
#   * Spending functions: O'Brien-Fleming (OF), Pocock (P), Wang-Tsiatis (WT),
#     Hwang-Shih-DeCani gamma family (asHSD, via --rho), Kim-DeMets (asKD).
#   * Optional non-binding futility bounds (--futility, beta-spending bsOF).
#   * Bidirectional solving: given power -> n; given n -> power.
#
# rpact API notes (validated against rpact 4.x):
#   * Design: getDesignGroupSequential(kMax, typeOfDesign, gammaA, alpha, beta, ...).
#     - typeOfDesign uses the exact boundaries "OF"/"P"/"WT" (no futility) or the
#       spending-function family "asOF"/"asP"/"asKD"/"asHSD" (required when a
#       beta-spending / futility is specified). gammaA drives asHSD.
#     - Futility: futilityStops = rep(TRUE, kMax-1), typeBetaSpending = "bsOF",
#       bindingFutility = FALSE (non-binding).
#   * Power objects expose overallReject (NOT overallPower).
#   * Sample-size objects expose maxNumberOfSubjects1 (per group) and
#     maxNumberOfSubjects (total); survival also maxNumberOfEvents.
#   * Means use `alternative=` (effect size); Rates use pi1/pi2; Counts use
#     fixedExposureTime (avoids requiring accrualTime).
#
# The design parameters are pre-computed in Python (samplesize_power.py) and
# injected, so the R templates stay clean. I18N_R is prepended by run_r() at
# execution time; t() is available.

__all__ = [
    "R_GSD_MEAN",
    "R_GSD_PROPORTION",
    "R_GSD_SURVIVAL",
    "R_GSD_HAZARD",
    "R_GSD_POISSON",
    "R_GSD_SURVIVAL_SIM",
    "R_GSD_HAZARD_SIM",
]

# ─────────────────────────────────────────────────────────────────────────────
# Shared R design block.
#   gs_type          : rpact typeOfDesign string (OF / P / WT / asHSD / asKD / asOF / ...)
#   gs_gamma         : HSD gammaA (0 unless spending == HSD); ignored otherwise
#   design_beta      : 1 - power when solving for n, else 0.2
#   futility_params  : "" when no futility; otherwise the rpact futility args
#                      (futilityStops + typeBetaSpending + bindingFutility)
# ─────────────────────────────────────────────────────────────────────────────
_GSD_DESIGN = """
suppressMessages(library(rpact))
design <- getDesignGroupSequential(
  kMax = {kmax}, typeOfDesign = "{gs_type}", gammaA = {gs_gamma}{delta_frag},
  alpha = {alpha}, beta = {design_beta}{futility_params})
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. Group-sequential two-sample means (UPGRADES the legacy `group_sequential`)
#    effect = standardized effect size (Cohen's d); stDev fixed at 1.
# ─────────────────────────────────────────────────────────────────────────────
R_GSD_MEAN = _GSD_DESIGN + """
if ({solve_for_power}) {{
  # directionUpper = FALSE only when the treatment effect is a reduction
  # (negative standardized effect size).
  pw <- getPowerMeans(design = design, alternative = {effect_gs}, stDev = 1,
       maxNumberOfSubjects = 2 * {nobs}, directionUpper = {direction_upper})$overallReject
  cat(t("header.group_sequential_power"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.effect_size"), {effect_gs}, "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  cat(t("label.achieved_power"), round(pw, 4), "\\n")
}} else {{
  ss <- getSampleSizeMeans(design = design, alternative = {effect_gs}, stDev = 1)
  n_pg <- ceiling(ss$maxNumberOfSubjects1)
  cat(t("header.group_sequential_n"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.effect_size"), {effect_gs}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.n_per_group"), n_pg, "\\n")
  cat(t("label.total_n"), ceiling(ss$maxNumberOfSubjects), "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Group-sequential two proportions (difference / ratio / odds-ratio)
#    metric & resolved p1/p2 are computed in Python and injected.
# ─────────────────────────────────────────────────────────────────────────────
R_GSD_PROPORTION = _GSD_DESIGN + """
if ({solve_for_power}) {{
  # directionUpper = FALSE when the treatment proportion is LOWER (p1 < p2),
  # i.e. the beneficial effect is a reduction.
  pw <- getPowerRates(design = design, groups = 2, pi1 = {p1}, pi2 = {p2},
       maxNumberOfSubjects = 2 * {nobs}, directionUpper = {direction_upper})$overallReject
  cat(t("header.gsd_proportion_power"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.proportion_metric"), "{metric}", "\\n")
  cat(t("label.p1"), {p1}, "\\n")
  cat(t("label.p2"), {p2}, "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  cat(t("label.achieved_power"), round(pw, 4), "\\n")
}} else {{
  ss <- getSampleSizeRates(design = design, groups = 2, pi1 = {p1}, pi2 = {p2})
  n_pg <- ceiling(ss$maxNumberOfSubjects1)
  cat(t("header.gsd_proportion_n"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.proportion_metric"), "{metric}", "\\n")
  cat(t("label.p1"), {p1}, "\\n")
  cat(t("label.p2"), {p2}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.n_per_group"), n_pg, "\\n")
  cat(t("label.total_n"), ceiling(ss$maxNumberOfSubjects), "\\n")
}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3 & 4. Group-sequential survival / hazard (exponential assumption).
#    lambda2 derived from control median; hazardRatio = treatment / control.
#    For power-given-n we estimate the expected number of events from the
#    exponential model (uniform accrual over `accrual`, then `followup`).
# ─────────────────────────────────────────────────────────────────────────────
_GSD_SURV_BODY = """
if ({solve_for_power}) {{
  lambda1 <- {lambda2} * {hr}
  # Expected events from the exponential model: each subject is followed on
  # average (accrual/2 + followup) time; per-subject event prob = 1 - exp(-lambda*T)
  # (NOT lambda*T, which can exceed 1 and over-counts events).
  expo <- {accrual} / 2 + {followup}
  events_est <- {nobs} * ((1 - exp(-{lambda2} * expo)) + (1 - exp(-lambda1 * expo)))
  # getPowerSurvival has NO followUpTime arg (only getSampleSizeSurvival does);
  # the follow-up is implied by maxNumberOfEvents. We encode accrual via
  # accrualIntensity = 2*nobs/accrual (subjects per time unit) and set
  # directionUpper = FALSE when HR < 1 (beneficial effect is on the LOWER side).
  pw <- getPowerSurvival(design = design, lambda2 = {lambda2}, hazardRatio = {hr},
       accrualTime = c(0, {accrual}), accrualIntensity = 2 * {nobs} / {accrual},
       dropoutRate1 = {dropout}, dropoutRate2 = {dropout},
       maxNumberOfSubjects = 2 * {nobs}, maxNumberOfEvents = events_est,
       directionUpper = {direction_upper})$overallReject
  cat(t("header.{surv_header}_power"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.hazard_ratio"), {hr}, "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  cat(t("label.achieved_power"), round(pw, 4), "\\n")
}} else {{
  ss <- getSampleSizeSurvival(design = design, lambda2 = {lambda2}, hazardRatio = {hr},
       accrualTime = c(0, {accrual}), followUpTime = {followup},
       dropoutRate1 = {dropout}, dropoutRate2 = {dropout})
  n_pg <- ceiling(ss$maxNumberOfSubjects1)
  events <- ceiling(ss$maxNumberOfEvents)
  cat(t("header.{surv_header}_n"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.hazard_ratio"), {hr}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.n_per_group"), n_pg, "\\n")
  cat(t("label.total_n"), ceiling(ss$maxNumberOfSubjects), "\\n")
  cat(t("label.events_needed"), events, "\\n")
}}
"""

# Swap only the header name; the remaining {placeholders} stay literal for the
# dispatch's later .format() call (a full .format() here would choke on them).
R_GSD_SURVIVAL = _GSD_DESIGN + _GSD_SURV_BODY.replace("{surv_header}", "gsd_survival")
R_GSD_HAZARD = _GSD_DESIGN + _GSD_SURV_BODY.replace("{surv_header}", "gsd_hazard")

# ─────────────────────────────────────────────────────────────────────────────
# 3b & 4b. Group-sequential survival / hazard SIMULATION (Monte-Carlo).
#    Backed by rpact getSimulationSurvival. The interim-event plan is anchored
#    on rpact's analytic maxNumberOfEvents (internally consistent). We do NOT
#    pass maxNumberOfSubjects: rpact derives it from accrualTime x
#    accrualIntensity, which the API requires to agree. longTimeSimulationAllowed
#    lets follow-up extend so the planned events actually accrue.
# ─────────────────────────────────────────────────────────────────────────────
_GSD_SURV_SIM_BODY = """
# Anchor the event plan on rpact's analytic design (maxNumberOfEvents), then
# validate empirical power via Monte-Carlo.
ss0 <- getSampleSizeSurvival(design = design, lambda2 = {lambda2}, hazardRatio = {hr},
     accrualTime = c(0, {accrual}), followUpTime = {followup},
     dropoutRate1 = {dropout}, dropoutRate2 = {dropout})
events_tot <- ceiling(ss0$maxNumberOfEvents)
if ({nobs_given}) {{
  n_pg <- {nobs}
}} else {{
  n_pg <- ceiling(ss0$maxNumberOfSubjects1)
}}
total_n <- 2 * n_pg
accrual_int <- total_n / {accrual}
planned_events <- round(pmin(events_tot, total_n) * (1:{kmax}) / {kmax})
sim <- getSimulationSurvival(design = design,
  hazardRatio = {hr}, lambda2 = {lambda2},
  accrualTime = c(0, {accrual}), accrualIntensity = accrual_int,
  dropoutRate1 = {dropout}, dropoutRate2 = {dropout},
  plannedEvents = planned_events,
  directionUpper = {direction_upper},
  maxNumberOfIterations = {n_simulations}, seed = {sim_seed},
  longTimeSimulationAllowed = TRUE)
safe <- function(x) if (is.null(x) || length(x) == 0 || is.na(x)) "NA" else round(x, 1)
cat(t("header.{surv_header}"), "\\n")
cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
cat(t("label.spending_function"), "{spending_func}", "\\n")
cat(t("label.hazard_ratio"), {hr}, "\\n")
cat(t("label.n_per_group"), n_pg, "\\n")
cat(t("label.total_n"), total_n, "\\n")
cat(t("label.planned_events"), paste(planned_events, collapse = ","), "\\n")
cat(t("label.empirical_power"), round(sim$overallReject, 4), "\\n")
cat(t("label.expected_n"), safe(sim$expectedNumberOfSubjects), "\\n")
cat(t("label.expected_events"), safe(sim$expectedNumberOfEvents), "\\n")
cat(t("label.stop_prob"), paste(round(sim$rejectPerStage, 3), collapse = ","), "\\n")
"""

R_GSD_SURVIVAL_SIM = _GSD_DESIGN + _GSD_SURV_SIM_BODY.replace("{surv_header}", "gsd_survival_sim")
R_GSD_HAZARD_SIM = _GSD_DESIGN + _GSD_SURV_SIM_BODY.replace("{surv_header}", "gsd_hazard_sim")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Group-sequential two Poisson rates (rpact getSampleSizeCounts)
#    fixedExposureTime is used (per-subject exposure), so accrualTime is not
#    required by rpact.
# ─────────────────────────────────────────────────────────────────────────────
R_GSD_POISSON = _GSD_DESIGN + """
if ({solve_for_power}) {{
  # directionUpper = FALSE when the treatment rate is LOWER (rate1 < rate2),
  # i.e. the beneficial effect is on the lower side.
  pw <- getPowerCounts(design = design, groups = 2, lambda1 = {rate1}, lambda2 = {rate2},
       fixedExposureTime = {ptime}, maxNumberOfSubjects = 2 * {nobs},
       directionUpper = {direction_upper})$overallReject
  cat(t("header.gsd_poisson_power"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.rate1"), {rate1}, "\\n")
  cat(t("label.rate2"), {rate2}, "\\n")
  cat(t("label.n_per_group"), {nobs}, "\\n")
  cat(t("label.achieved_power"), round(pw, 4), "\\n")
}} else {{
  ss <- getSampleSizeCounts(design = design, groups = 2, lambda1 = {rate1}, lambda2 = {rate2},
       fixedExposureTime = {ptime})
  n_pg <- ceiling(ss$maxNumberOfSubjects1)
  cat(t("header.gsd_poisson_n"), "\\n")
  cat(t("label.n_looks"), {kmax}, "(", {n_interim}, t("label.interim"), "\\n")
  cat(t("label.spending_function"), "{spending_func}", "\\n")
  cat(t("label.rate1"), {rate1}, "\\n")
  cat(t("label.rate2"), {rate2}, "\\n")
  cat(t("label.alpha"), {alpha}, t("label.power"), {power}, "\\n")
  cat(t("label.n_per_group"), n_pg, "\\n")
  cat(t("label.total_n"), ceiling(ss$maxNumberOfSubjects), "\\n")
}}
"""

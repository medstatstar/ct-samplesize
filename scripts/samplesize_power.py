#!/usr/bin/env python3
"""
Clinical Trial Sample Size & Power Calculator — Extended v2.0
Supports: t-test, ANOVA, proportion, non-inferiority, survival,
          mixed models (simr), ROC, Poisson rates, cluster randomized,
          Bland-Altman (method comparison), bioequivalence (PowerTOST)
"""
import argparse, json, sys, os, textwrap, subprocess, tempfile, math

def run_r(code: str) -> str:
    """Execute R code and return stdout."""
    with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as f:
        f.write(code)
        tmp = f.name
    try:
        rscript = r"C:\Tools\R-4.5.1\bin\x64\Rscript.exe"
        r = subprocess.run([rscript, '--vanilla', tmp], capture_output=True, text=True, timeout=300)
        return r.stdout + r.stderr
    finally:
        os.unlink(tmp)

# ─── R code templates ───

R_MIXED_MODEL = """
# Mixed Model Power Analysis (simr)
library(simr); library(lme4)
{data_setup}
model <- makeLmer({formula}, fixef={fixef}, VarCorr={varcorr}, sigma={sigma}, data=df)
# Power for fixed effect '{effect}'
result <- powerSim(model, nsim={nsim}, test=fcompare({reduced_formula}))
cat("\\n========== Mixed Model Power ==========\\n")
cat("Formula:", deparse({formula_qq}), "\\n")
cat("Effect:", "{effect}", "\\n")
print(result)
pc <- powerCurve(model, test=fcompare({reduced_formula}), along="{along_var}", breaks={breaks})
cat("\\n--- Power Curve ---\\n")
print(summary(pc))
"""

R_ROC = """
# ROC Curve Sample Size (Obuchowski formula)
library(pROC)
auc0 <- {auc0}
auc1 <- {auc1}
n <- ceiling(((qnorm(1-{alpha}/2) + qnorm({power}))^2) / (2*(asin(sqrt(auc1)) - asin(sqrt(auc0)))^2))
cat("\\n========== ROC Sample Size ==========\\n")
cat("H0 AUC:", auc0, "\\n")
cat("H1 AUC:", auc1, "\\n")
cat("Alpha:", "{alpha}", "  Power:", "{power}", "\\n")
cat("Sample size:", n, "\\n")
"""

R_POISSON = """
# Poisson Rate Comparison (Wald test, normal approximation)
# H0: lambda1 = lambda2 vs H1: lambda1 != lambda2
lambda1 <- {lambda1}
lambda2 <- {lambda2}
t1 <- {t1}
t2 <- {t2}
alpha_val <- {alpha}
power_val <- {power}
# Rate ratio
RR <- lambda1 / lambda2
# Wald test sample size (per group)
n <- ceiling(((qnorm(1-alpha_val/2) + qnorm(power_val))^2 * (1/(lambda1*t1) + 1/(lambda2*t2))) / (log(RR))^2)
cat("\\n========== Poisson Rate Comparison ==========\\n")
cat("Rate 1:", lambda1, "/ unit time, follow-up:", t1, "\\n")
cat("Rate 2:", lambda2, "/ unit time, follow-up:", t2, "\\n")
cat("Rate Ratio:", round(RR, 3), "\\n")
cat("Alpha:", alpha_val, "  Power:", power_val, "\\n")
cat("Sample size per group:", n, "\\n")
cat("Total sample size:", 2*n, "\\n")

# Events expected
events1 <- n * lambda1 * t1
events2 <- n * lambda2 * t2
cat("Expected events (group 1):", round(events1, 1), "\\n")
cat("Expected events (group 2):", round(events2, 1), "\\n")
"""

R_CLUSTER = """
# Cluster-Randomized Trial Sample Size (Design Effect method)
m <- {m}      # subjects per cluster
icc <- {icc}  # ICC
deff <- 1 + (m - 1) * icc
n_indiv <- {n_indiv}     # individual-level n per group
n_adj <- ceiling(n_indiv * deff)
n_clusters_per_group <- ceiling(n_adj / m)
n_total <- n_adj * 2
n_clusters_total <- n_clusters_per_group * 2
cat("\\n========== Cluster-Randomized Design ==========\\n")
cat("ICC:", "{icc}", "\\n")
cat("Subjects/cluster:", "{m}", "\\n")
cat("Design effect (DEFF):", round(deff, 3), "\\n")
cat("Individual-level n (per group):", "{n_indiv}", "\\n")
cat("Adjusted n (per group):", n_adj, "\\n")
cat("Number of clusters (per group):", n_clusters_per_group, "\\n")
cat("Total clusters:", n_clusters_total, "\\n")
cat("Total sample size:", n_total, "\\n")
"""

R_BLAND_ALTMAN = """
# Bland-Altman Method Comparison Sample Size (Lu et al. 2016)
sd_diff <- {sd_diff}
w <- {w}
alpha_val <- {alpha}
n <- ceiling(2 * (qnorm(1-alpha_val/2) * sd_diff / w)^2)
cat("\\n========== Bland-Altman Method Comparison ==========\\n")
cat("SD of differences:", "{sd_diff}", "\\n")
cat("Desired CI half-width (W):", "{w}", "\\n")
cat("Alpha:", "{alpha}", "\\n")
cat("Sample size (pairs):", n, "\\n")
"""

R_EQ_MEANS = """
# Equivalence Test for Two Means (TrialSize)
library(TrialSize)
result <- TTwoMeans.Equivalence(alpha={alpha}, beta={beta}, delta={margin}, sigma={sigma})
n <- ceiling(result$`Total Sample Size`/2)
cat("\\n========== Equivalence (Two Means) ==========\\n")
cat("Margin (delta):", "{margin}", "\\n")
cat("Sigma:", "{sigma}", "\\n")
cat("n per group:", n, "\\n")
"""

R_BE_TOST = """
# Bioequivalence (PowerTOST)
library(PowerTOST)
result <- sampleN.TOST(theta0={theta0}, CV={cv}, design="{design}", alpha={alpha}, targetpower={power}, logscale=TRUE)
cat("\\n========== Bioequivalence (TOST) ==========\\n")
cat("Design:", "{design}", "\\n")
cat("theta0:", "{theta0}", "\\n")
cat("CV:", "{cv}", "\\n")
cat("Sample size:", result[2], "\\n")
"""

def main():
    p = argparse.ArgumentParser(description="Clinical Trial Sample Size Calculator (Extended)")
    p.add_argument("--test", required=True,
        choices=["ttest_ind","ttest_paired","anova","proportion_one","proportion_two",
                 "non_inferiority","survival","mixed_model","roc","poisson",
                 "bland_altman","equivalence","be_tost","cluster",
                 "vaccine_efficacy","multiple_endpoints","bayesian","dose_escalation"])
    # Common
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8)
    # t-test / ANOVA
    p.add_argument("--effect", type=float, help="Cohen's d or f")
    p.add_argument("--k_groups", type=int, default=2)
    # Proportion
    p.add_argument("--p1", type=float)
    p.add_argument("--p2", type=float)
    # Non-inferiority / Equivalence
    p.add_argument("--margin", type=float)
    # Survival
    p.add_argument("--hazard_ratio", type=float)
    # Mixed model
    p.add_argument("--formula", type=str)
    p.add_argument("--effect_name", type=str)
    p.add_argument("--fixef", type=str, default="c(0, 0.5)")
    p.add_argument("--varcorr", type=float, default=0.5)
    p.add_argument("--sigma", type=float, default=1.0)
    p.add_argument("--along_var", type=str, default="subject")
    # ROC
    p.add_argument("--auc0", type=float, default=0.5)
    p.add_argument("--auc1", type=float)
    # Poisson
    p.add_argument("--lambda1", type=float)
    p.add_argument("--lambda2", type=float)
    p.add_argument("--t1", type=float, default=1.0)
    p.add_argument("--t2", type=float, default=1.0)
    # Cluster
    p.add_argument("--icc", type=float)
    p.add_argument("--m", type=float)
    p.add_argument("--n_indiv", type=float)
    # Bland-Altman
    p.add_argument("--sd_diff", type=float)
    p.add_argument("--w", type=float)
    # Bioequivalence
    p.add_argument("--theta0", type=float, default=0.95)
    p.add_argument("--cv", type=float, default=0.25)
    p.add_argument("--design", type=str, default="2x2")
    p.add_argument("--nsim", type=int, default=1000)
    # Vaccine efficacy, Bayesian, multiple endpoints, dose escalation
    p.add_argument("--ve_control", type=float, default=0.02)
    p.add_argument("--ve_treatment", type=float, default=0.005)
    p.add_argument("--prior_a0", type=float, default=0.5)
    p.add_argument("--prob_control", type=float, default=0.3)
    p.add_argument("--prob_treatment", type=float, default=0.15)
    p.add_argument("--endpoint_type", type=str, default="means")
    p.add_argument("--correlation", type=float, default=0.5)
    p.add_argument("--n_doses", type=int, default=5)
    p.add_argument("--target_dlt", type=float, default=0.33)

    args = p.parse_args()
    r_code = ""

    if args.test == "mixed_model":
        if not args.effect_name:
            print("ERROR: --effect_name required"); sys.exit(1)
        eff = args.effect or 0.5
        # Build R code without f-string to avoid interpolation issues
        r_code = """
library(simr); library(lme4)
set.seed(42)
n_subjects <- 20
n_treatment <- 10
df <- expand.grid(time = c(0, 1, 2, 3), subject = seq_len(n_subjects))
df$treatment <- ifelse(df$subject <= n_treatment, "active", "placebo")
model <- makeLmer(y ~ treatment * time + (1|subject),
                  fixef = c(0, {eff}, 0, {eff_half}),
                  VarCorr = {varcorr},
                  sigma = {sigma},
                  data = df)
result <- powerSim(model, nsim={nsim}, test = fcompare(y ~ time + (1|subject)))
cat("\\n========== Mixed Model Power ==========\\n")
cat("Effect: {ename} = {eff}\\n")
cat("Sample size:", n_subjects, "subjects\\n")
print(result)
pc <- powerCurve(model, test = fcompare(y ~ time + (1|subject)),
                 along = "subject", breaks = c(10, 20, 30, 40, 50))
cat("\\n--- Power Curve ---\\n")
print(summary(pc))
""".format(eff=eff, eff_half=eff/2, varcorr=args.varcorr, sigma=args.sigma, nsim=args.nsim, ename=args.effect_name)

    elif args.test == "roc":
        auc0 = args.auc0
        if not args.auc1 and not args.effect:
            print("ERROR: --auc1 or --effect required"); sys.exit(1)
        auc1 = args.auc1 or min(auc0 + args.effect, 0.99)
        r_code = R_ROC.format(alpha=args.alpha, power=args.power, auc0=auc0, auc1=auc1)

    elif args.test == "poisson":
        if not args.lambda1 or not args.lambda2:
            print("ERROR: --lambda1 and --lambda2 required"); sys.exit(1)
        r_code = R_POISSON.format(
            alpha=args.alpha, power=args.power,
            lambda1=args.lambda1, lambda2=args.lambda2,
            t1=args.t1, t2=args.t2
        )

    elif args.test == "cluster":
        if args.icc is None or not args.m or not args.n_indiv:
            print("ERROR: --icc, --m, --n_indiv required"); sys.exit(1)
        r_code = R_CLUSTER.format(m=args.m, icc=args.icc, n_indiv=args.n_indiv)

    elif args.test == "bland_altman":
        if not args.sd_diff or not args.w:
            print("ERROR: --sd_diff and --w required"); sys.exit(1)
        r_code = R_BLAND_ALTMAN.format(sd_diff=args.sd_diff, w=args.w, alpha=args.alpha)

    elif args.test == "equivalence":
        r_code = R_EQ_MEANS.format(
            alpha=args.alpha, beta=1-args.power,
            margin=args.margin or 1.0, sigma=args.effect or 2.0
        )

    elif args.test == "be_tost":
        r_code = R_BE_TOST.format(
            theta0=args.theta0, cv=args.cv, design=args.design,
            alpha=args.alpha, power=args.power
        )

    elif args.test == "ttest_ind":
        r_code = f"""
library(pwr)
d <- {args.effect or 0.5}
result <- pwr.t.test(d=d, sig.level={args.alpha}, power={{args.power}}, type="two.sample", alternative="two.sided")
cat("\\n========== Two-Sample T-Test ==========\\n")
cat("Cohen's d:", d, "\\n")
cat("n per group:", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "ttest_paired":
        r_code = f"""
library(pwr)
d <- {args.effect or 0.5}
result <- pwr.t.test(d=d, sig.level={args.alpha}, power={{args.power}}, type="paired", alternative="two.sided")
cat("\\n========== Paired T-Test ==========\\n")
cat("Cohen's d:", d, "\\n")
cat("n (pairs):", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "anova":
        r_code = f"""
library(pwr)
result <- pwr.anova.test(k={args.k_groups}, f={args.effect or 0.25}, sig.level={args.alpha}, power={{args.power}})
print(result)
"""

    elif args.test == "proportion_two":
        p1 = args.p1 if args.p1 else 0.5
        p2 = args.p2 if args.p2 else 0.65
        r_code = f"""
library(pwr)
h <- 2*asin(sqrt({p1})) - 2*asin(sqrt({p2}))
result <- pwr.2p.test(h=h, sig.level={args.alpha}, power={args.power})
cat("\\n========== Two Proportions Test ==========\\n")
cat("P1: {p1}, P2: {p2}\\n")
cat("h effect size:", h, "\\n")
cat("n per group:", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "non_inferiority":
        p1 = args.p1 or 0.80
        p2 = args.p2 or 0.85
        margin = args.margin or 0.1
        r_code = f"""
cat("\\n========== Non-Inferiority (Proportions) ==========\\n")
cat("P1 (control): {p1}\\n")
cat("P2 (treatment): {p2}\\n")
cat("Margin (d): {margin}\\n")
cat("Note: Use TrialSize::NPropTwoSidedNonInferiority() for exact calculation\\n")
# Approximate using prop.test power
n_approx <- ceiling(((qnorm(1-{args.alpha}) + qnorm({args.power}))^2 * ({p1}*(1-{p1}) + {p2}*(1-{p2}))) / ({margin} - abs({p1}-{p2}))^2)
cat("Approximate n per group:", n_approx, "\\n")
"""

    elif args.test == "survival":
        hr = args.hazard_ratio or 0.75
        r_code = f"""
# Schoenfeld formula for survival
# d = (Z_alpha/2 + Z_beta)^2 / (log HR)^2
d <- ceiling((qnorm(1-{args.alpha}/2) + qnorm({args.power}))^2 / (log({hr})^2))
n_adj <- ceiling(d / 0.75)
cat("\\n========== Survival (Log-Rank Test) ==========\\n")
cat("Hazard ratio: {hr}\\n")
cat("Alpha: {args.alpha}, Power: {args.power}\\n")
cat("Total events needed (Schoenfeld):", d, "\\n")
cat("Approx. total sample (75% event rate):", n_adj, "\\n")
cat("Use rpact::getSampleSizeSurvival() for full analysis\\n")
"""

    elif args.test == "vaccine_efficacy":
        vc = args.ve_control
        vt = args.ve_treatment
        ve = (vc - vt) / vc if vc > 0 else 0
        r_code = f"""
# Vaccine Efficacy Sample Size (Halloran et al.)
# VE = (ARU - ARV) / ARU
# ARU = attack rate in unvaccinated (control) = {vc}
# ARV = attack rate in vaccinated (treatment) = {vt}
# VE = {ve:.3f}
# Based on person-time Poisson incidence
# n per group = (Z_alpha + Z_beta)^2 * (1/ARU + 1/ARV) / (log(1-VE))^2
ARU <- {vc}
ARV <- {vt}
VE <- (ARU - ARV) / ARU
n <- ceiling(((qnorm(1-{args.alpha}/2) + qnorm({args.power}))^2 * (1/ARU + 1/ARV)) / (log(1-VE))^2)
cat("\\n========== Vaccine Efficacy Sample Size ==========\\n")
cat("Control attack rate:", ARU, "\\n")
cat("Treatment attack rate:", ARV, "\\n")
cat("Vaccine efficacy (VE):", round(VE*100, 1), "%\\n")
cat("Alpha:", "{args.alpha}", "  Power:", "{args.power}", "\\n")
cat("n per group:", n, "\\n")
cat("Total:", 2*n, "\\n")
"""

    elif args.test == "multiple_endpoints":
        r_code = f"""
# Multiple Endpoints (Composite / Co-primary)
# Based on rpact / Bagiella &海地 (composite endpoint)
# For co-primary endpoints with correlation rho:
# n = n_single / (1 - rho) for each endpoint
rho <- {args.correlation}
n_single <- ceiling((qnorm(1-{args.alpha}/2) + qnorm({args.power}))^2 / ({args.effect or 0.3})^2)
n_adj <- ceiling(n_single / (1 - rho))
cat("\\n========== Multiple Endpoints ==========\\n")
cat("Type:", "{args.endpoint_type}", "\\n")
cat("Endpoint correlation (rho):", rho, "\\n")
cat("Single endpoint n (per group):", n_single, "\\n")
cat("Adjusted n per group (co-primary):", n_adj, "\\n")
cat("\\nNote: For composite endpoints, use rpact for event-count based calculation\\n")
"""

    elif args.test == "bayesian":
        a0 = args.prior_a0
        pC = args.prob_control
        pT = args.prob_treatment
        r_code = f"""
# Bayesian Clinical Trial Design (BayesCTDesign)
library(BayesCTDesign)
# Historical control weight a0 = {a0}
a0 <- {a0}
pC <- {pC}     # control probability
pT <- {pT}     # treatment probability
n <- 100
cat("\\n========== Bayesian Design ==========\\n")
cat("Prior a0 (historical weight):", a0, "\\n")
cat("Control prob:", pC, "\\n")
cat("Treatment prob:", pT, "\\n")
cat("Note: Run BayesCTDesign::simple_sim() for full simulation\\n")
# Approximate Bayesian power via posterior probability
# P(pC - pT > margin | data) > 0.95
eff <- pC - pT
n_min <- ceiling(((qnorm(1-{args.alpha}) + qnorm({args.power}))^2 * (pC*(1-pC) + pT*(1-pT))) / eff^2)
cat("Classical n (per group) for comparison:", n_min, "\\n")
cat("Effective sample size with historical prior:", ceiling(n_min * (1 + a0)), "\\n")
"""

    elif args.test == "dose_escalation":
        r_code = f"""
# Dose Escalation Sample Size (CRM / 3+3)
library(escalation)
# Target DLT rate: {args.target_dlt}
# Number of dose levels: {args.n_doses}
cat("\\n========== Dose Escalation Design ==========\\n")
cat("Dose levels:", "{args.n_doses}", "\\n")
cat("Target DLT rate:", "{args.target_dlt}", "\\n")
cat("\\n--- 3+3 Design ---\\n")
cat("Cohort size: 3-6 patients per dose level\\n")
cat("Starting dose: lowest level\\n")
cat("Escalation rules:\\n")
cat("  0/3 DLT → escalate\\n")
cat("  1/3 DLT → enroll 3 more (total 6)\\n")
cat("  1/6 DLT → escalate\\n")
cat("  ≥2/6 DLT → de-escalate/stop\\n")
cat("MTD: highest dose with ≤1/6 DLT\\n")
n_3plus3 <- {args.n_doses} * 4  # rough estimate
cat("Approximate total sample (3+3):", n_3plus3, "-", n_3plus3 + 6, "\\n")
cat("\\n--- CRM (Bayesian) Design ---\\n")
cat("Recommended sample size: 20-40 patients total\\n")
cat("Use escalation::get_design('crmloc') for simulation\\n")
"""

    py_script = textwrap.dedent(r_code)
    print("=" * 60)
    print("R Code:")
    print("=" * 60)
    print(py_script)
    print("=" * 60)
    print("=" * 60)
    print("R Output:")
    print("=" * 60)
    sys.stdout.flush()
    output = run_r(py_script)
    print(output)
    print("=" * 60)

if __name__ == "__main__":
    main()

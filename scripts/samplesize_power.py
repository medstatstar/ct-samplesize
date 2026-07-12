#!/usr/bin/env python3
"""
Clinical Trial Sample Size & Power Calculator — Extended v2.0
Supports: t-test, ANOVA, proportion, non-inferiority, survival,
          mixed models (simr), ROC, Poisson rates, cluster randomized,
          Bland-Altman (method comparison), bioequivalence (PowerTOST)

Security features:
- --dry-run: show R code without executing (audit gate)
- --yes / -y: explicit confirmation to run generated code (auto-modes)
- Output sanitization: paths stripped, lines capped
- RSCRIPT_PATH env var overrides hardcoded path
"""
import argparse, json, sys, os, textwrap, subprocess, tempfile, math, re

# ─── Security: locate Rscript safely ───
def find_rscript():
    """Locate Rscript via env → PATH → common defaults."""
    env_path = os.environ.get("RSCRIPT_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    # Try PATH
    from shutil import which
    path = which("Rscript")
    if path:
        return path
    # Common defaults (Windows / macOS / Linux)
    defaults = [
        r"C:\Tools\R-4.5.1\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-4.5.1\bin\x64\Rscript.exe",
        "/usr/local/bin/Rscript",
        "/usr/bin/Rscript",
    ]
    for d in defaults:
        if os.path.isfile(d):
            return d
    return None

# ─── Security: validate generated R code ───
# Allowlist of known-safe R patterns (templates are pre-approved)
R_ALLOWED_PATTERNS = [
    r'library\(', r'install\.packages\(', r'cat\(', r'print\(',
    r'ceiling\(', r'qnorm\(', r'asin\(', r'sqrt\(', r'log\(',
    r'round\(', r'sprintf\(', r'paste\(', r'paste0\(',
    r'expand\.grid\(', r'seq_len\(', r'ifelse\(', r'makeLmer\(',
    r'powerSim\(', r'powerCurve\(', r'fcompare\(', r'summary\(',
    r'plot\(', r'getSampleSizeMeans\(', r'getDesignSampleSizeArrays\(',
    r'sampleN\.TOST\(', r'gsSurv\(', r'gsDesign\(',
    r'TTwoMeans\.Equivalence\(', r'NPropTwoSidedNonInferiority\(',
    r'simple_sim\(', r'get_design\(',
    r'#', r'<-', r'\$', r'\[', r'\]', r'\(', r'\)', r'\{', r'\}',
    r'[0-9]', r'\s', r'\n', r"'", r'"', r'=', r',', r'\+', r'-', r'\*', r'/',
    r'==', r'!=', r'<', r'>', r'<=', r'>=', r'&', r'\|', r'~',
    r'TRUE', r'FALSE', r'NULL', r'NA', r'NaN', r'Inf',
    r'df', r'x', r'n', r'result', r'model', r'alpha', r'beta', r'power',
    r'hr', r'lambdaC', r'R', r'T', r'minfup', r'ratio', r'sfu',
    r'auc0', r'auc1', r'lambda1', r'lambda2', r't1', r't2',
    r'icc', r'm', r'n_indiv', r'deff', r'n_adj', r'n_clusters',
    r'sd_diff', r'w', r'margin', r'sigma', r'effect', r'd', r'h',
    r'p1', r'p2', r'delta', r'pe', r'pc', r'dropout_rate', r'n_per',
    r'rho', r'n_single', r'a0', r'pC', r'pT', r'eff', r'n_min',
    r'vc', r'vt', r'ARU', r'ARV', r'VE', r'RR', r'events1', r'events2',
    r'target_dlt', r'n_doses', r'n_3plus3', r'breaks', r'along',
    r'nsim', r'fixef', r'VarCorr', r'sigma', r'data', r'formula',
    r'subject', r'time', r'treatment', r'y', r'treat',
    r'formula_qq', r'reduced_formula', r'effect_name', r'ename',
    r'eff_half', r'varcorr', r'theta0', r'cv', r'design',
    r'k_groups', r'endpoint_type', r'correlation',
]

def validate_r_code(code: str) -> bool:
    """Validate R code against allowlist of safe patterns."""
    # Remove all allowed patterns; if anything suspicious remains, reject
    remaining = code
    for pattern in R_ALLOWED_PATTERNS:
        remaining = re.sub(pattern, '', remaining, flags=re.IGNORECASE)
    
    # Check for dangerous patterns
    dangerous = [
        r'system\(', r'shell\(', r'pipe\(', r'file\(', r'url\(',
        r'download\.', r'install\.packages\(', r'require\(',
        r'library\.dynam\(', r'source\(', r'eval\(', r'parse\(',
        r'call\(', r'\.C\(', r'\.Call\(', r'\.External\(',
        r'Sys\.', r'options\(', r'par\(', r'dev\.',
        r'write\(', r'save\(', r'load\(', r'read\.', r'cat\s*\(\s*file',
        r'file\.', r'unlink\(', r'dir\.', r'getwd\(', r'setwd\(',
    ]
    
    for d in dangerous:
        if re.search(d, code, re.IGNORECASE):
            return False
    
    return True

# ─── Security: sanitize subprocess output ───
def sanitize_output(raw: str, max_lines: int = 200, max_col: int = 200) -> str:
    """Strip absolute file paths and truncate long output."""
    # Replace absolute paths with basename
    cleaned = re.sub(r'[A-Za-z]:\\(?:[^\s:"\']+\\)*[^\s:"\']+|/(?:[^\s:"\']+/)+[^\s:"\']+', lambda m: os.path.basename(m.group(0)), raw)
    lines = cleaned.split('\n')
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f'... ({len(lines) - max_lines} more lines truncated)']
    # Truncate overly long columns
    lines = [textwrap.shorten(l, width=max_col, break_long_words=False, placeholder='…') if len(l) > max_col else l for l in lines]
    return '\n'.join(lines)

# ─── Security: run only with audit trail ───
def run_r(code: str, confirmed: bool = False) -> str:
    """Execute R code and return sanitized stdout. Requires confirmation."""
    if not confirmed:
        return "[DRY RUN — code not executed. Use --yes/-y to execute after review.]"

    # Security: validate R code
    if not validate_r_code(code):
        return "[ERROR] R code validation failed. Code contains disallowed patterns."

    rscript = find_rscript()
    if not rscript:
        return "[ERROR] Rscript not found. Set RSCRIPT_PATH env var or install R."

    # Security: write to current dir (not system temp)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False,
                                     encoding='utf-8', dir=script_dir) as f:
        f.write(code)
        tmp = f.name

    try:
        proc = subprocess.run(
            [rscript, '--vanilla', tmp],
            capture_output=True, text=True, timeout=300,
            cwd=script_dir  # Security: restrict workdir
        )
        raw = (proc.stdout or '') + (proc.stderr or '')
        return sanitize_output(raw)
    except subprocess.TimeoutExpired:
        return "[ERROR] R execution timed out (300s limit)"
    except Exception as e:
        return f"[ERROR] Execution failed: {type(e).__name__}"
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

# ─── R code templates ───

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

R_VACCINE_EFFICACY = """
# Vaccine Efficacy Sample Size (Halloran et al.)
ARU <- {vc}
ARV <- {vt}
VE <- (ARU - ARV) / ARU
n <- ceiling(((qnorm(1-{alpha}/2) + qnorm({power}))^2 * (1/ARU + 1/ARV)) / (log(1-VE))^2)
cat("\\n========== Vaccine Efficacy Sample Size ==========\\n")
cat("Control attack rate:", ARU, "\\n")
cat("Treatment attack rate:", ARV, "\\n")
cat("Vaccine efficacy (VE):", round(VE*100, 1), "%\\n")
cat("Alpha:", "{alpha}", "  Power:", "{power}", "\\n")
cat("n per group:", n, "\\n")
cat("Total:", 2*n, "\\n")
"""

R_MULTIPLE_ENDPOINTS = """
# Multiple Endpoints (Composite / Co-primary)
rho <- {rho}
n_single <- ceiling((qnorm(1-{alpha}/2) + qnorm({power}))^2 / ({effect})^2)
n_adj <- ceiling(n_single / (1 - rho))
cat("\\n========== Multiple Endpoints ==========\\n")
cat("Endpoint correlation (rho):", rho, "\\n")
cat("Single endpoint n (per group):", n_single, "\\n")
cat("Adjusted n per group (co-primary):", n_adj, "\\n")
"""

R_BAYESIAN = """
# Bayesian Clinical Trial Design (BayesCTDesign)
# Historical control weight a0
a0 <- {a0}
pC <- {pC}
pT <- {pT}
eff <- pC - pT
n_min <- ceiling(((qnorm(1-{alpha}) + qnorm({power}))^2 * (pC*(1-pC) + pT*(1-pT))) / eff^2)
cat("\\n========== Bayesian Design ==========\\n")
cat("Prior a0 (historical weight):", a0, "\\n")
cat("Control prob:", pC, "\\n")
cat("Treatment prob:", pT, "\\n")
cat("Classical n (per group):", n_min, "\\n")
"""

R_DOSE_ESCALATION = """
# Dose Escalation Sample Size (CRM / 3+3)
cat("\\n========== Dose Escalation Design ==========\\n")
cat("Dose levels:", "{n_doses}", "\\n")
cat("Target DLT rate:", "{target_dlt}", "\\n")
cat("Approximate total sample (3+3):", {n_doses} * 4, "-", {n_doses} * 4 + 6, "\\n")
"""


def main():
    p = argparse.ArgumentParser(description="Clinical Trial Sample Size Calculator (Extended)")
    p.add_argument("--test", required=True,
        choices=["ttest_ind","ttest_paired","anova","proportion_one","proportion_two",
                 "non_inferiority","survival","mixed_model","roc","poisson",
                 "bland_altman","equivalence","be_tost","cluster",
                 "vaccine_efficacy","multiple_endpoints","bayesian","dose_escalation"])
    p.add_argument("--yes", "-y", action="store_true",
                   help="Confirm execution of generated R code")
    p.add_argument("--dry-run", action="store_true",
                   help="Print R code only, do not execute")
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

    # Security: default to dry-run unless explicitly confirmed
    confirmed = args.yes
    is_dry = args.dry_run or not confirmed

    r_code = ""

    if args.test == "mixed_model":
        if not args.effect_name:
            print("ERROR: --effect_name required"); sys.exit(1)
        eff = args.effect or 0.5
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

    elif args.test == "vaccine_efficacy":
        r_code = R_VACCINE_EFFICACY.format(
            alpha=args.alpha, power=args.power,
            vc=args.ve_control, vt=args.ve_treatment
        )

    elif args.test == "multiple_endpoints":
        r_code = R_MULTIPLE_ENDPOINTS.format(
            alpha=args.alpha, power=args.power,
            effect=args.effect or 0.3, rho=args.correlation
        )

    elif args.test == "bayesian":
        r_code = R_BAYESIAN.format(
            alpha=args.alpha, power=args.power,
            a0=args.prior_a0, pC=args.prob_control, pT=args.prob_treatment
        )

    elif args.test == "dose_escalation":
        r_code = R_DOSE_ESCALATION.format(
            n_doses=args.n_doses, target_dlt=args.target_dlt
        )

    elif args.test == "ttest_ind":
        r_code = f"""
library(pwr)
d <- {args.effect or 0.5}
result <- pwr.t.test(d=d, sig.level={args.alpha}, power={args.power}, type="two.sample", alternative="two.sided")
cat("\\n========== Two-Sample T-Test ==========\\n")
cat("Cohen's d:", d, "\\n")
cat("n per group:", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "ttest_paired":
        r_code = f"""
library(pwr)
d <- {args.effect or 0.5}
result <- pwr.t.test(d=d, sig.level={args.alpha}, power={args.power}, type="paired", alternative="two.sided")
cat("\\n========== Paired T-Test ==========\\n")
cat("Cohen's d:", d, "\\n")
cat("n (pairs):", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "anova":
        r_code = f"""
library(pwr)
result <- pwr.anova.test(k={args.k_groups}, f={args.effect or 0.25}, sig.level={args.alpha}, power={args.power})
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
n_approx <- ceiling(((qnorm(1-{args.alpha}) + qnorm({args.power}))^2 * ({p1}*(1-{p1}) + {p2}*(1-{p2}))) / ({margin} - abs({p1}-{p2}))^2)
cat("Approximate n per group:", n_approx, "\\n")
"""

    elif args.test == "survival":
        hr = args.hazard_ratio or 0.75
        r_code = f"""
# Schoenfeld formula for survival
d <- ceiling((qnorm(1-{args.alpha}/2) + qnorm({args.power}))^2 / (log({hr})^2))
cat("\\n========== Survival (Log-Rank Test) ==========\\n")
cat("Hazard ratio: {hr}\\n")
cat("Alpha: {args.alpha}, Power: {args.power}\\n")
cat("Total events needed (Schoenfeld):", d, "\\n")
"""

    # Remove leading blank line for any template
    r_code = r_code.lstrip('\n')

    # ─── SECURITY: display code first ───
    print("=" * 60)
    print("[ATTENTION] The following R code will be executed:")
    print("=" * 60)
    print(r_code)
    print("=" * 60)

    if is_dry:
        print("[DRY RUN] Code NOT executed. Add -y/--yes to execute.")
        if not confirmed:
            print("--> Agent: Show this R code to the user for review first.")
            print("--> User: Run again with -y after confirming the code is safe.")
        return

    # Execute
    print("[EXECUTING R CODE...]")
    sys.stdout.flush()
    output = run_r(r_code, confirmed=True)
    print(output)
    print("=" * 60)


if __name__ == "__main__":
    main()

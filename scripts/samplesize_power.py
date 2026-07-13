#!/usr/bin/env python3
"""
Clinical Trial Sample Size & Power Calculator — v3.3.0

Security model:
- All R code comes from pre-defined templates (validated str args only)
- Generated R code is ALWAYS shown to user (default: executed + code shown)
- Default executes and returns results; --dry-run previews code only (safety)
- R script path auto-detected (RSCRIPT_PATH env or PATH lookup)
- Output is sanitized (paths stripped, length-capped)
- String args validated against strict allowlists

Test types (31 total):
  Core: ttest_ind, ttest_paired, anova, proportion_one, proportion_two,
        non_inferiority, equivalence, be_tost, mixed_model, roc, poisson,
        bland_altman, cluster, vaccine_efficacy, multiple_endpoints,
        bayesian, dose_escalation
  New in v3.3: win_ratio, must_win, historical_controls, mams,
        conditional_power, ni_survival, superiority_margin, assurance,
        dunnett, mediation, group_sequential, adaptive, survival_exact
"""
import argparse, sys, os, textwrap, subprocess, tempfile, re
from r_templates import *

def find_rscript():
    """Locate Rscript executable."""
    env_path = os.environ.get("RSCRIPT_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    from shutil import which
    path = which("Rscript")
    if path:
        return path
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

def sanitize_output(raw, max_lines=200, max_col=200):
    """Strip file paths and truncate output."""
    cleaned = re.sub(
        r'[A-Za-z]:\\(?:[^\s:"\']+\\)*[^\s:"\']+|/(?:[^\s:"\']+/)+[^\s:"\']+',
        lambda m: os.path.basename(m.group(0)), raw
    )
    lines = cleaned.split('\n')
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f'... ({len(lines) - max_lines} lines truncated)']
    lines = [
        textwrap.shorten(l, width=max_col, break_long_words=False, placeholder='…')
        if len(l) > max_col else l for l in lines
    ]
    return '\n'.join(lines)

def run_r(code, confirmed=False):
    """Execute R code or return dry-run message."""
    if not confirmed:
        return "[DRY RUN — code not executed. Remove --dry-run to execute.]"
    rscript = find_rscript()
    if not rscript:
        return "[ERROR] Rscript not found. Set RSCRIPT_PATH env or install R."

    # Use system temp dir to avoid residue if process is killed
    with tempfile.NamedTemporaryFile(
        suffix='.R', mode='w', delete=False, encoding='utf-8', dir=tempfile.gettempdir()
    ) as f:
        f.write(code)
        tmp = f.name

    try:
        proc = subprocess.run(
            [rscript, '--vanilla', tmp],
            capture_output=True, text=True, timeout=300
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

def parse_seq_to_r(s):
    """Parse a sequence spec into an R vector expression.

    Supports two formats:
      - explicit comma list : '20,40,200'      -> c(20, 40, 200)
      - auto range          : '20:20:200'      -> seq-style c(20, 40, ..., 200)
    Returns an R expression string like 'c(20, 40, 200)'.
    """
    if s is None:
        return None
    s = s.strip()
    if ':' in s:
        parts = s.split(':')
        if len(parts) != 3:
            raise ValueError("auto sequence needs start:step:stop, got %r" % s)
        start, step, stop = (float(x) for x in parts)
        if step == 0:
            raise ValueError("step must be non-zero in auto sequence")
        vals = []
        x = start
        while x <= stop + abs(step) * 1e-9:
            vals.append(round(x, 6))
            x += step
        if not vals:
            vals = [start]
    elif ',' in s:
        vals = [float(x) for x in s.split(',') if x.strip() != '']
    else:
        vals = [float(s)]
    if not vals:
        raise ValueError("empty sequence: %r" % s)
    return "c(" + ", ".join(repr(float(v)) for v in vals) + ")"

# ═══════════════════════════════════════════════════════════════════════════════
# R Code Templates — PASS Extension (14 new types, v3.3)
# ═══════════════════════════════════════════════════════════════════════════════

def _curve_ctx(args):
    """Safe value context for CURVE_SOLVERS params (.format placeholders)."""
    return {
        'alpha': args.alpha,
        'effect': args.effect if args.effect is not None else 0.5,
        'k_groups': args.k_groups,
        'p1': args.p1 if args.p1 is not None else 0.5,
        'p2': args.p2 if args.p2 is not None else 0.3,
        'p0': args.p2 if args.p2 is not None else 0.5,
        'margin': args.margin if args.margin is not None else 0.1,
        'auc0': args.auc0,
        'auc1': args.auc1 if args.auc1 is not None else min(args.auc0 + (args.effect or 0.2), 0.99),
        'lambda1': args.lambda1 if args.lambda1 is not None else 0.05,
        'lambda2': args.lambda2 if args.lambda2 is not None else 0.03,
        't1': args.t1, 't2': args.t2,
        've_control': args.ve_control, 've_treatment': args.ve_treatment,
        'p_control_sup': args.p_control_sup, 'delta_sup': args.delta_sup, 'sup_margin': args.sup_margin,
        'theta0': args.theta0, 'cv': args.cv, 'design': args.design,
        'hazard_ratio': args.hazard_ratio if args.hazard_ratio is not None else 0.75,
        'ni_margin_surv': args.ni_margin_surv,
        'delta_effect': args.delta_effect, 'n_arms_mams': args.n_arms_mams,
        'n_groups_dunnett': args.n_groups_dunnett, 'effect_dunnett': args.effect_dunnett,
        'effect_gs': args.effect_gs, 'n_interim': args.n_interim,
        'alpha_exact': args.alpha_exact, 'hr_exact': args.hr_exact,
        'accrual_exact': args.accrual_exact, 'followup_exact': args.followup_exact,
        'event_rate_exact': args.event_rate_exact, 'n_stages_exact': args.n_stages_exact,
    }

def build_curve_code(args):
    """Build R code for a power/sample-size curve. Returns R string or None."""
    test = args.test
    if test not in CURVE_SOLVERS:
        print("ERROR: curve mode (--n_seq / --power_seq) is not yet supported for --test '%s'." % test)
        print("Supported test types for curves:")
        print("  " + ", ".join(sorted(CURVE_SOLVERS.keys())))
        return None
    spec = CURVE_SOLVERS[test]
    ctx = _curve_ctx(args)
    try:
        params = spec["params"].format(**ctx)
    except (KeyError, ValueError, IndexError) as e:
        print("ERROR: parameter missing/invalid for curve of '%s': %s" % (test, e))
        return None
    # Auto-inject required R packages (curve templates only load ggplot2)
    _LIB_MAP = {
        'pwr': ["ttest_ind", "ttest_paired", "ttest_one", "anova", "proportion_one",
                "proportion_two", "proportion_paired", "odds_ratio", "risk_ratio"],
        'PowerTOST': ["be_tost"],
    }
    libs = [pkg for pkg, tests in _LIB_MAP.items() if test in tests]
    if libs:
        params = "\n".join("suppressMessages(library(%s))" % p for p in libs) + "\n" + params
    target = args.power
    _tmp = os.environ.get('LOCALAPPDATA')
    if _tmp:
        _tmp = os.path.join(_tmp, 'Temp')
    else:
        _tmp = tempfile.gettempdir()
    out_png = args.out or os.path.join(_tmp, "ct_curve_%s.png" % test)
    try:
        if args.n_seq:
            seq_r = parse_seq_to_r(args.n_seq)
            mode = "power"
            xlabel = spec.get("n_label", "N")
            ylabel = "Power"
        elif args.power_seq:
            seq_r = parse_seq_to_r(args.power_seq)
            mode = "n"
            xlabel = "Power (target)"
            ylabel = spec.get("n_label", "N")
        else:
            print("ERROR: curve mode requires --n_seq or --power_seq")
            return None
    except ValueError as e:
        print("ERROR: invalid sequence spec: %s" % e)
        return None
    effects_r = None
    if args.plot_effects and spec.get("effect_loop"):
        try:
            effects_r = parse_seq_to_r(args.plot_effects)
        except ValueError as e:
            print("ERROR: invalid --plot_effects: %s" % e)
            return None
    if mode == "power":
        tpl = _CURVE_POWER_MULTI if effects_r else _CURVE_POWER_SINGLE
    else:
        tpl = _CURVE_N_MULTI if effects_r else _CURVE_N_SINGLE
    r = (tpl
         .replace("__PARAMS__", params)
         .replace("__POWER_FN__", spec["power_fn"])
         .replace("__NFN__", spec["n_fn"])
         .replace("__SEQ__", seq_r)
         .replace("__EFFECTS__", effects_r or "c()")
         .replace("__EFFECT_VAR__", spec.get("effect_var", "delta"))
         .replace("__TEST__", test)
         .replace("__XLABEL__", xlabel)
         .replace("__YLABEL__", ylabel)
         .replace("__TARGET__", repr(float(target)))
         .replace("__OUT__", out_png.replace("\\", "/")))
    return r

def main():
    p = argparse.ArgumentParser(description="Clinical Trial Sample Size Calculator v3.3.0")
    p.add_argument("--test", required=False, default=None,
        choices=["ttest_ind","ttest_paired","anova","proportion_one","proportion_two",
                 "non_inferiority","survival","mixed_model","roc","poisson",
                 "bland_altman","equivalence","be_tost","cluster",
                 "vaccine_efficacy","multiple_endpoints","bayesian","dose_escalation",
                 "win_ratio","must_win","historical_controls","mams",
                 "conditional_power","ni_survival","superiority_margin","assurance",
                 "dunnett","mediation","group_sequential","adaptive","survival_exact"])
    p.add_argument("--yes", "-y", action="store_true",
                   help="(默认即执行)显式执行 R 代码，保留以兼容旧命令")
    p.add_argument("--dry-run", action="store_true",
                   help="只展示生成的 R 代码、不执行（安全预览模式）")
    p.add_argument("--install-all-packages", action="store_true", help="Install all R packages used by this skill")
    # ── Common ──
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8, help="目标检验效能 (与 --nobs 互斥)")
    p.add_argument("--nobs", type=int, default=None, help="给定样本量求效能 (与 --power 互斥)")
    # ── t-test / ANOVA ──
    p.add_argument("--effect", type=float)
    p.add_argument("--k_groups", type=int, default=2)
    # ── Proportion ──
    p.add_argument("--p1", type=float)
    p.add_argument("--p2", type=float)
    # ── Non-inferiority / Equivalence ──
    p.add_argument("--margin", type=float)
    # ── Survival ──
    p.add_argument("--hazard_ratio", type=float)
    # ── Mixed model ──
    p.add_argument("--effect_name", type=str)
    p.add_argument("--varcorr", type=float, default=0.5)
    p.add_argument("--sigma", type=float, default=1.0)
    p.add_argument("--nsim", type=int, default=500)
    # ── ROC ──
    p.add_argument("--auc0", type=float, default=0.5)
    p.add_argument("--auc1", type=float)
    # ── Poisson ──
    p.add_argument("--lambda1", type=float)
    p.add_argument("--lambda2", type=float)
    p.add_argument("--t1", type=float, default=1.0)
    p.add_argument("--t2", type=float, default=1.0)
    # ── Cluster ──
    p.add_argument("--icc", type=float)
    p.add_argument("--m", type=float)
    p.add_argument("--n_indiv", type=float)
    # ── Bland-Altman ──
    p.add_argument("--sd_diff", type=float)
    p.add_argument("--w", type=float)
    # ── Bioequivalence ──
    p.add_argument("--theta0", type=float, default=0.95)
    p.add_argument("--cv", type=float, default=0.25)
    p.add_argument("--design", type=str, default="2x2")
    # ── Vaccine, Bayesian, multiple endpoints, dose escalation ──
    p.add_argument("--ve_control", type=float, default=0.02)
    p.add_argument("--ve_treatment", type=float, default=0.005)
    p.add_argument("--prior_a0", type=float, default=0.5)
    p.add_argument("--prob_control", type=float, default=0.3)
    p.add_argument("--prob_treatment", type=float, default=0.15)
    p.add_argument("--correlation", type=float, default=0.5)
    p.add_argument("--n_doses", type=int, default=5)
    p.add_argument("--target_dlt", type=float, default=0.33)

    # ═══ NEW v3.3 arguments ═══
    # Win-Ratio
    p.add_argument("--win_ratio_theta", type=float, default=1.5)
    p.add_argument("--n_sim_initial", type=int, default=100)
    p.add_argument("--se_approx", type=float, default=0.0625)
    p.add_argument("--n_sim", type=int, default=1000)
    # Must-Win / Co-Primary
    p.add_argument("--n_endpoints_must", type=int, default=2)
    p.add_argument("--effect_must", type=float, default=0.3)
    p.add_argument("--correlation_must", type=float, default=0.5)
    # Historical Controls
    p.add_argument("--p_control_current", type=float, default=0.3)
    p.add_argument("--historical_response", type=int, default=15)
    p.add_argument("--historical_n", type=int, default=100)
    p.add_argument("--a0_borrowing", type=float, default=0.5)
    # MAMS
    p.add_argument("--n_arms_mams", type=int, default=3)
    p.add_argument("--n_stages_mams", type=int, default=2)
    p.add_argument("--delta_effect", type=float, default=0.3)
    # Conditional Power / SSR
    p.add_argument("--timing", type=float, default=0.5)
    p.add_argument("--observed_effect", type=float, default=0.2)
    p.add_argument("--planned_effect", type=float, default=0.3)
    p.add_argument("--n_completed", type=int, default=100)
    p.add_argument("--n_planned", type=int, default=200)
    # NI Survival
    p.add_argument("--ni_margin_surv", type=float, default=1.25)
    p.add_argument("--hr_expected", type=float, default=1.0)
    p.add_argument("--accrual_time", type=float, default=12)
    p.add_argument("--followup_time", type=float, default=12)
    p.add_argument("--dropout_rate", type=float, default=0.05)
    p.add_argument("--event_rate", type=float, default=0)
    # Superiority Margin
    p.add_argument("--sup_margin", type=float, default=0.05)
    p.add_argument("--sigma_ratio", type=float, default=1.0)
    p.add_argument("--p_control_sup", type=float, default=0.3)
    p.add_argument("--delta_sup", type=float, default=0.15)
    # Assurance
    p.add_argument("--n_sim_assurance", type=int, default=5000)
    p.add_argument("--shape1_trt", type=float, default=3)
    p.add_argument("--shape2_trt", type=float, default=7)
    p.add_argument("--shape1_ctrl", type=float, default=3)
    p.add_argument("--shape2_ctrl", type=float, default=7)
    p.add_argument("--n_assurance", type=int, default=100)
    p.add_argument("--margin_assurance", type=float, default=0.0)
    # Dunnett
    p.add_argument("--n_groups_dunnett", type=int, default=3)
    p.add_argument("--n_control_dunnett", type=int, default=50)
    p.add_argument("--effect_dunnett", type=float, default=0.4)
    # Mediation
    p.add_argument("--a_path", type=float, default=0.3)
    p.add_argument("--b_path", type=float, default=0.3)
    p.add_argument("--sigma2_m", type=float, default=1.0)
    p.add_argument("--sigma2_y", type=float, default=1.0)
    p.add_argument("--cprime", type=float, default=0.0)
    p.add_argument("--n_sim_mediation", type=int, default=1000)
    # Group Sequential
    p.add_argument("--n_interim", type=int, default=1)
    p.add_argument("--effect_gs", type=float, default=0.4)
    p.add_argument("--spending_func", type=str, default="OF")
    # Adaptive
    p.add_argument("--n_stages_adapt", type=int, default=2)
    p.add_argument("--effect_adaptive", type=float, default=0.4)
    p.add_argument("--adaptive_type", type=str, default="SSR")
    # Survival Exact
    p.add_argument("--alpha_exact", type=float, default=0.05)
    p.add_argument("--power_exact", type=float, default=0.8)
    p.add_argument("--hr_exact", type=float, default=0.75)
    p.add_argument("--accrual_exact", type=float, default=12)
    p.add_argument("--followup_exact", type=float, default=12)
    p.add_argument("--dropout_exact", type=float, default=0.05)
    p.add_argument("--event_rate_exact", type=float, default=0.3)
    p.add_argument("--n_stages_exact", type=int, default=1)
    # ── Curve mode (power / sample-size curves) ──
    p.add_argument("--n_seq", type=str, default=None,
                   help="样本量序列: 显式 '20,40,200' 或自动 '20:20:200'(起:步:止) → 绘制 power 曲线")
    p.add_argument("--power_seq", type=str, default=None,
                   help="效能序列: 显式 '0.6,0.7,0.95' 或自动 '0.6:0.05:0.95' → 绘制样本量曲线")
    p.add_argument("--plot_effects", type=str, default=None,
                   help="多效应量叠加(可选): '0.3,0.5,0.8' 画多条曲线做敏感性分析")
    p.add_argument("--out", type=str, default=None,
                   help="曲线 PNG 输出路径 (默认系统临时目录)")

    args = p.parse_args()
    # 默认执行并返回结果；--dry-run 仅预览 R 代码（安全兜底，优先级最高）
    confirmed = not args.dry_run

    # ── Solve direction: --nobs given → solve for power; else solve for n ──
    if args.nobs is not None and args.nobs > 0:
        solve_for_power = True
    else:
        solve_for_power = False
        args.nobs = None

    # ── Numeric range validation ──
    _RANGE_RULES = {
        "alpha": (0, 1), "power": (0, 1),
        "auc0": (0, 1), "auc1": (0, 1),
        "correlation": (-1, 1), "icc": (0, 1),
        "margin": (0, None), "hazard_ratio": (0, None),
        "ni_margin_surv": (0, None), "sup_margin": (0, None),
        "delta_sup": (0, None),
        "ve_control": (0, 1), "ve_treatment": (0, 1),
        "prob_control": (0, 1), "prob_treatment": (0, 1),
        "p_control_sup": (0, 1), "p_control_current": (0, 1),
        "event_rate_exact": (0, 1), "dropout_exact": (0, 1),
        "p1": (0, 1), "p2": (0, 1),
        "nobs": (0, None),
    }
    _range_errors = []
    for label, (lo, hi) in _RANGE_RULES.items():
        val = getattr(args, label, None)
        if val is None:
            continue
        if lo is not None and val <= lo:
            _range_errors.append(f"--{label} must be > {lo} (got {val})")
        if hi is not None and val >= hi:
            _range_errors.append(f"--{label} must be < {hi} (got {val})")
    if _range_errors:
        print("Parameter validation failed:")
        for e in _range_errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    if args.install_all_packages:
        print("Installing all R packages used by ct-samplesize...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        r_script = """
pkgs <- c("TrialSize", "pwr", "rpact", "gsDesign", "PowerTOST",
          "simr", "lme4", "pROC", "powerSurvEpi", "survival")
install.packages(pkgs, repos="https://cran.r-project.org")
cat("\nDone. Installed", length(pkgs), "packages.\n")
"""
        r_file = os.path.join(script_dir, "_install_packages.R")
        with open(r_file, "w") as f:
            f.write(r_script)
        rscript = find_rscript()
        if rscript:
            import subprocess
            result = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=600)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        else:
            print("[ERROR] Rscript not found. Is R installed?")
        return

    if not args.test:
        p.error("--test is required (unless using --install-all-packages)")

    # ══ Curve mode (power / sample-size curves) ══
    if args.n_seq or args.power_seq:
        r_code = build_curve_code(args)
        if r_code is None:
            sys.exit(1)
        r_code = r_code.lstrip('\n')
        print("=" * 60)
        print("[R CODE — generated for this analysis (always shown for review)]")
        print("=" * 60)
        print(r_code)
        print("=" * 60)
        if not confirmed:
            print("[DRY RUN] R code NOT executed. Remove --dry-run to execute.")
            return
        print("[EXECUTING R CODE...]")
        sys.stdout.flush()
        output = run_r(r_code, confirmed=True)
        print(output)
        # Echo output path from Python side (R may mangle backslash display)
        _t = os.environ.get('LOCALAPPDATA')
        if _t:
            _t = os.path.join(_t, 'Temp')
        else:
            _t = tempfile.gettempdir()
        _out = args.out or os.path.join(_t, "ct_curve_%s.png" % args.test)
        print("PNG saved to: %s" % _out)
        print("=" * 60)
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # Core test types (17)
    # ═══════════════════════════════════════════════════════════════════════════

    if args.test == "mixed_model":
        if not args.effect_name:
            print("ERROR: --effect_name required"); sys.exit(1)
        # Validate effect_name: only alphanumeric + underscore
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', args.effect_name):
            print("ERROR: --effect_name must be a valid R identifier"); sys.exit(1)
        eff = args.effect or 0.5
        if solve_for_power:
            n_subj = args.nobs
            r_code = f"""
library(simr); library(lme4)
set.seed(42)
n_subjects <- {n_subj}; n_treatment <- ceiling({n_subj}/2)
df <- expand.grid(time = c(0, 1, 2, 3), subject = seq_len(n_subjects))
df$treatment <- ifelse(df$subject <= n_treatment, "active", "placebo")
model <- makeLmer(y ~ treatment * time + (1|subject),
                  fixef = c(0, {eff}, 0, {eff/2}),
                  VarCorr = {args.varcorr}, sigma = {args.sigma}, data = df)
result <- powerSim(model, nsim={args.nsim}, test = fcompare(y ~ time + (1|subject)))
cat("\\n========== Mixed Model Power (given N) ==========\\n")
cat("Effect: {args.effect_name} = {eff}\\n")
cat("n subjects:", n_subjects, "\\n")
print(result)
"""
        else:
            r_code = """
library(simr); library(lme4)
set.seed(42)
n_subjects <- 20; n_treatment <- 10
df <- expand.grid(time = c(0, 1, 2, 3), subject = seq_len(n_subjects))
df$treatment <- ifelse(df$subject <= n_treatment, "active", "placebo")
model <- makeLmer(y ~ treatment * time + (1|subject),
                  fixef = c(0, {eff}, 0, {eff_half}),
                  VarCorr = {varcorr}, sigma = {sigma}, data = df)
result <- powerSim(model, nsim={nsim}, test = fcompare(y ~ time + (1|subject)))
cat("\\n========== Mixed Model Power ==========\\n")
cat("Effect: {ename} = {eff}\\n")
print(result)
pc <- powerCurve(model, test = fcompare(y ~ time + (1|subject)),
                 along = "subject", breaks = c(10, 20, 30, 40, 50))
cat("\\n--- Power Curve ---\\n")
print(summary(pc))
""".format(eff=eff, eff_half=eff/2, varcorr=args.varcorr,
           sigma=args.sigma, nsim=args.nsim, ename=args.effect_name)

    elif args.test == "roc":
        auc0 = args.auc0
        if not args.auc1 and not args.effect:
            print("ERROR: --auc1 or --effect required"); sys.exit(1)
        auc1 = args.auc1 or min(auc0 + args.effect, 0.99)
        if solve_for_power:
            r_code = f"""
library(pROC)
auc0 <- {auc0}; auc1 <- {auc1}
n <- {args.nobs}
# Inverse of n = ceil((z_a/2 + z_b)^2 / (2*(asin(sqrt(auc1))-asin(sqrt(auc0)))^2))
z_b <- sqrt(n * 2 * (asin(sqrt(auc1)) - asin(sqrt(auc0)))^2) - qnorm(1-{args.alpha}/2)
power <- pnorm(z_b)
cat("\\n========== ROC Sample Size (Power given N) ==========\\n")
cat("H0 AUC:", auc0, "H1 AUC:", auc1, "\\n")
cat("Alpha:", {args.alpha}, "\\n")
cat("Sample size:", n, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_ROC.format(alpha=args.alpha, power=args.power, auc0=auc0, auc1=auc1)

    elif args.test == "poisson":
        if solve_for_power:
            r_code = f"""
lambda1 <- {args.lambda1}; lambda2 <- {args.lambda2}
t1 <- {args.t1}; t2 <- {args.t2}
RR <- lambda1 / lambda2
n <- {args.nobs}
# Inverse of n = ceil((z_a/2+z_b)^2 * (1/(lam1*t1)+1/(lam2*t2)) / log(RR)^2)
z_b <- sqrt(n * (log(RR))^2 / (1/(lambda1*t1) + 1/(lambda2*t2))) - qnorm(1-{args.alpha}/2)
power <- pnorm(z_b)
cat("\\n========== Poisson Rate Comparison (Power given N) ==========\\n")
cat("Rate Ratio:", round(RR, 3), "\\n")
cat("Sample size per group:", n, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_POISSON.format(alpha=args.alpha, power=args.power,
                lambda1=args.lambda1, lambda2=args.lambda2, t1=args.t1, t2=args.t2)

    elif args.test == "cluster":
        if solve_for_power:
            r_code = f"""
m <- {args.m}; icc <- {args.icc}
deff <- 1 + (m - 1) * icc
# Given total sample size, solve for effective individual n per group
n_total <- {args.nobs}
n_indiv_eff <- n_total / 2 / deff
cat("\\n========== Cluster-RCT (Power given N) ==========\\n")
cat("Design effect (DEFF):", round(deff, 3), "\\n")
cat("Cluster size m:", m, "ICC:", icc, "\\n")
cat("Total sample size:", n_total, "\\n")
cat("Effective individual n per group (n_total/2/DEFF):", round(n_indiv_eff, 1), "\\n")
cat("Implied n clusters per group:", ceiling(n_indiv_eff / m), "\\n")
cat("Note: To obtain exact power, combine n_indiv_eff with the\\n")
cat("      corresponding individual-level test's power formula.\\n")
"""
        else:
            r_code = R_CLUSTER.format(m=args.m, icc=args.icc, n_indiv=args.n_indiv)

    elif args.test == "bland_altman":
        if solve_for_power:
            r_code = f"""
sd_diff <- {args.sd_diff}; alpha_val <- {args.alpha}
n <- {args.nobs}
# Bland-Altman is a CI-width (precision) calc, not a power calc.
# Given n, report the achievable half-width w = z_a/2 * sd_diff * sqrt(2/n)
w_achieved <- qnorm(1-alpha_val/2) * sd_diff * sqrt(2/n)
cat("\\n========== Bland-Altman (Width given N) ==========\\n")
cat("SD diff:", sd_diff, "\\n")
cat("Sample size (pairs):", n, "\\n")
cat("Achievable half-width w:", round(w_achieved, 4), "\\n")
cat("Note: This is a precision (CI width) calc, not a hypothesis power calc.\\n")
"""
        else:
            r_code = R_BLAND_ALTMAN.format(sd_diff=args.sd_diff, w=args.w, alpha=args.alpha)

    elif args.test == "equivalence":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}; delta <- {args.margin or 1.0}; sigma <- {args.effect or 2.0}
n_total <- {args.nobs}
# Two-means equivalence (TOST). Per arm n = n_total/2.
# Approx power via TOST inversion (each one-sided test at alpha).
n_arm <- n_total / 2
se <- sigma * sqrt(2/n_arm)
# z for each bound
z1 <- (delta - 0) / se  # crude; use qnorm(1-alpha) threshold
tcrit <- qnorm(1 - alpha_val)
# Power approx = Phi((delta - tcrit*se)/se) - Phi((-delta - tcrit*se)/se)  (symmetric)
power <- pnorm((delta - tcrit*se)/se) - pnorm((-delta - tcrit*se)/se)
cat("\\n========== Equivalence (Means, Power given N) ==========\\n")
cat("Equivalence margin delta:", delta, "\\n")
cat("Sigma:", sigma, "\\n")
cat("Total N:", n_total, "per arm:", n_arm, "\\n")
cat("Achieved power (approx):", round(power, 4), "\\n")
"""
        else:
            r_code = R_EQ_MEANS.format(alpha=args.alpha, beta=1-args.power,
                margin=args.margin or 1.0, sigma=args.effect or 2.0)

    elif args.test == "be_tost":
        # Validate design against allowlist to prevent R code injection
        _allowed_designs = ["2x2", "2x4", "3x3", "2x2x2", "2x2x3", "2x2x4"]
        if args.design not in _allowed_designs:
            print("ERROR: --design must be one of:", ", ".join(_allowed_designs))
            sys.exit(1)
        if solve_for_power:
            r_code = f"""
library(PowerTOST)
# power.TOST solves power given n (per sequence)
result <- power.TOST(theta0={args.theta0}, CV={args.cv}, design="{args.design}",
                     alpha={args.alpha}, n={args.nobs})
cat("\\n========== Bioequivalence (Power given N) ==========\\n")
cat("theta0:", {args.theta0}, "CV:", {args.cv}, "design:", "{args.design}", "\\n")
cat("n per sequence:", {args.nobs}, "\\n")
cat("Achieved power:", round(result, 4), "\\n")
"""
        else:
            r_code = R_BE_TOST.format(theta0=args.theta0, cv=args.cv,
                design=args.design, alpha=args.alpha, power=args.power)

    elif args.test == "vaccine_efficacy":
        if solve_for_power:
            r_code = f"""
ARU <- {args.ve_control}; ARV <- {args.ve_treatment}
VE <- (ARU - ARV) / ARU
n <- {args.nobs}
# Inverse of n = ceil((z_a/2+z_b)^2 * (1/ARU+1/ARV) / log(1-VE)^2)
z_b <- sqrt(n * (log(1-VE))^2 / (1/ARU + 1/ARV)) - qnorm(1-{args.alpha}/2)
power <- pnorm(z_b)
cat("\\n========== Vaccine Efficacy (Power given N) ==========\\n")
cat("VE:", round(VE*100, 1), "%\\n")
cat("n per group:", n, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_VACCINE_EFFICACY.format(alpha=args.alpha, power=args.power,
                vc=args.ve_control, vt=args.ve_treatment)

    elif args.test == "multiple_endpoints":
        if solve_for_power:
            r_code = f"""
rho <- {args.correlation}; effect <- {args.effect or 0.3}; alpha_val <- {args.alpha}
n_adj <- {args.nobs}
# Inverse: n_single = n_adj*(1-rho); z_b = sqrt(n_single*effect^2) - z_a/2
n_single <- n_adj * (1 - rho)
z_b <- sqrt(n_single * effect^2) - qnorm(1-alpha_val/2)
power <- pnorm(z_b)
cat("\\n========== Multiple Endpoints (Power given N) ==========\\n")
cat("Correlation:", rho, "\\n")
cat("Adjusted n:", n_adj, "\\n")
cat("Effective single-endpoint n:", round(n_single, 1), "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_MULTIPLE_ENDPOINTS.format(alpha=args.alpha, power=args.power,
                effect=args.effect or 0.3, rho=args.correlation)

    elif args.test == "bayesian":
        if solve_for_power:
            r_code = f"""
a0 <- {args.prior_a0}; pC <- {args.prob_control}; pT <- {args.prob_treatment}; alpha_val <- {args.alpha}
eff <- pC - pT
n_min <- {args.nobs}
# One-sided: z_b = sqrt(n*eff^2/(pC(1-pC)+pT(1-pT))) - z_alpha
z_b <- sqrt(n_min * eff^2 / (pC*(1-pC) + pT*(1-pT))) - qnorm(alpha_val)
power <- pnorm(z_b)
cat("\\n========== Bayesian Design (Power given N) ==========\\n")
cat("Prior a0:", a0, "\\n")
cat("Effective n per group:", n_min, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_BAYESIAN.format(alpha=args.alpha, power=args.power,
                a0=args.prior_a0, pC=args.prob_control, pT=args.prob_treatment)

    elif args.test == "dose_escalation":
        if solve_for_power:
            r_code = f"""
cat("\\n========== Dose Escalation (3+3 / CRM) ==========\\n")
cat("Note: Dose-escalation is a heuristic design, not a power-based sample size.\\n")
cat("Dose levels:", {args.n_doses}, "Target DLT:", "{args.target_dlt}", "\\n")
cat("Given total N = {args.nobs}, approximate total (3+3):", {args.n_doses} * 4, "-", {args.n_doses} * 4 + 6, "\\n")
cat("A power calculation does not apply to this design.\\n")
"""
        else:
            r_code = R_DOSE_ESCALATION.format(n_doses=args.n_doses, target_dlt=args.target_dlt)

    elif args.test == "ttest_ind":
        if solve_for_power:
            r_code = f"""
library(pwr)
d <- {args.effect or 0.5}
result <- pwr.t.test(d=d, sig.level={args.alpha}, n={args.nobs}, type="two.sample", alternative="two.sided")
cat("\\n========== Two-Sample T-Test (Power given N) ==========\\n")
cat("Cohen's d:", d, "\\n")
cat("n per group:", {args.nobs}, "\\n")
cat("Achieved power:", round(result$power, 4), "\\n")
print(result)
"""
        else:
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
        if solve_for_power:
            r_code = f"""
library(pwr)
d <- {args.effect or 0.5}
result <- pwr.t.test(d=d, sig.level={args.alpha}, n={args.nobs}, type="paired", alternative="two.sided")
cat("\\n========== Paired T-Test (Power given N) ==========\\n")
cat("Cohen's d:", d, "\\n")
cat("n (pairs):", {args.nobs}, "\\n")
cat("Achieved power:", round(result$power, 4), "\\n")
print(result)
"""
        else:
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
        if solve_for_power:
            r_code = f"""
library(pwr)
result <- pwr.anova.test(k={args.k_groups}, f={args.effect or 0.25}, sig.level={args.alpha}, n={args.nobs})
cat("\\n========== One-Way ANOVA (Power given N) ==========\\n")
cat("k groups:", {args.k_groups}, "f:", {args.effect or 0.25}, "\\n")
cat("n per group:", {args.nobs}, "\\n")
cat("Achieved power:", round(result$power, 4), "\\n")
print(result)
"""
        else:
            r_code = f"""
library(pwr)
result <- pwr.anova.test(k={args.k_groups}, f={args.effect or 0.25}, sig.level={args.alpha}, power={args.power})
print(result)
"""

    elif args.test == "proportion_one":
        p0 = args.p1 if args.p1 else 0.5
        p1 = args.p2 if args.p2 else 0.65
        if solve_for_power:
            r_code = f"""
library(pwr)
p0 <- {p0}; p1 <- {p1}
h <- 2*asin(sqrt(p1)) - 2*asin(sqrt(p0))
result <- pwr.1p.test(h=h, sig.level={args.alpha}, n={args.nobs})
cat("\\n========== One-Sample Proportion Test (Power given N) ==========\\n")
cat("H0 proportion:", p0, "\\n")
cat("H1 proportion:", p1, "\\n")
cat("n:", {args.nobs}, "\\n")
cat("Achieved power:", round(result$power, 4), "\\n")
print(result)
"""
        else:
            r_code = f"""
library(pwr)
# One-sample proportion test
p0 <- {p0}; p1 <- {p1}
h <- 2*asin(sqrt(p1)) - 2*asin(sqrt(p0))
result <- pwr.1p.test(h=h, sig.level={args.alpha}, power={args.power})
cat("\\n========== One-Sample Proportion Test ==========\\n")
cat("H0 proportion:", p0, "\\n")
cat("H1 proportion:", p1, "\\n")
cat("n:", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "proportion_two":
        p1 = args.p1 if args.p1 else 0.5
        p2 = args.p2 if args.p2 else 0.65
        if solve_for_power:
            r_code = f"""
library(pwr)
h <- 2*asin(sqrt({p1})) - 2*asin(sqrt({p2}))
result <- pwr.2p.test(h=h, sig.level={args.alpha}, n={args.nobs})
cat("\\n========== Two Proportions Test (Power given N) ==========\\n")
cat("P1: {p1}, P2: {p2}\\n")
cat("n per group:", {args.nobs}, "\\n")
cat("Achieved power:", round(result$power, 4), "\\n")
print(result)
"""
        else:
            r_code = f"""
library(pwr)
h <- 2*asin(sqrt({p1})) - 2*asin(sqrt({p2}))
result <- pwr.2p.test(h=h, sig.level={args.alpha}, power={args.power})
cat("\\n========== Two Proportions Test ==========\\n")
cat("P1: {p1}, P2: {p2}\\n")
cat("n per group:", ceiling(result$n), "\\n")
print(result)
"""

    elif args.test == "non_inferiority":
        p1 = args.p1 or 0.80
        p2 = args.p2 or 0.85
        margin = args.margin or 0.1
        if solve_for_power:
            r_code = f"""
cat("\\n========== Non-Inferiority (Proportions, Power given N) ==========\\n")
p1 <- {p1}; p2 <- {p2}; margin <- {margin}; alpha_val <- {args.alpha}
n_total <- {args.nobs}
# Two-proportion z-test (one-sided), non-inferiority margin
# Inverse of n = ceil((z_alpha + z_beta)^2 * (p1(1-p1)+p2(1-p2)) / (margin - |p1-p2|)^2)
z_b <- sqrt(n_total/2 * (margin - abs(p1-p2))^2 / (p1*(1-p1) + p2*(1-p2))) - qnorm(alpha_val)
power <- pnorm(z_b)
cat("对照组有效率 p1:", p1, "\\n")
cat("试验组有效率 p2:", p2, "\\n")
cat("非劣效界值 delta:", margin, "\\n")
cat("总样本量 N:", n_total, "每组:", n_total/2, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = f"""
cat("\\n========== Non-Inferiority (Proportions) ==========\\n")
cat("TrialSize 包::TwoSampleProportion.NIS\\n\\n")
if (requireNamespace("TrialSize", quietly=TRUE)) {{
  library(TrialSize)
  real_diff <- abs({p1} - {p2})
  total_n <- tryCatch(
    TwoSampleProportion.NIS(alpha={args.alpha}, beta=1-{args.power},
                             p1={p1}, p2={p2}, k=1,
                             delta={margin}, margin=real_diff),
    error = function(e) NA_real_
  )
  n_arm <- ceiling(total_n)
  n_total <- n_arm * 2
  cat("对照组有效率 p1: {p1}\\n")
  cat("试验组有效率 p2: {p2}\\n")
  cat("假设真实差异 |p1-p2|: ", real_diff, "\\n")
  cat("非劣效界值 delta: {margin}\\n")
  cat("单侧 α: {args.alpha}, 把握度: {args.power}, 1:1 分配\\n\\n")
  cat("--- 结果 ---\\n")
  cat("每组样本量 n1:", n_arm, "\\n")
  cat("每组样本量 n2:", ceiling(total_n * 1), "\\n")
  cat("总样本量 N:", n_total, "\\n")
  cat("含 10% 脱落率:", ceiling(n_total * 1.1), "\\n")
}} else {{
  n_approx <- ceiling(((qnorm(1-{args.alpha}) + qnorm({args.power}))^2 * ({p1}*(1-{p1}) + {p2}*(1-{p2}))) / ({margin} - abs({p1}-{p2}))^2)
  cat("P1={p1}, P2={p2}, Margin={margin}, 近似公式.\\n")
  cat("每组样本量:", n_approx, "\\n")
  cat("总样本量:", n_approx*2, "\\n")
}}
"""

    elif args.test == "survival":
        hr = args.hazard_ratio or 0.75
        if solve_for_power:
            r_code = f"""
cat("\\n========== Survival (Log-Rank, Power given N) ==========\\n")
cat("Hazard ratio:", {hr}, "\\n")
# Schoenfeld: d = ceil((z_a/2 + z_b)^2 / log(hr)^2)
# Given events d -> z_b = sqrt(d)*|log(hr)| - z_a/2; power = Phi(z_b)
d_events <- {args.nobs}
z_b <- sqrt(d_events) * abs(log({hr})) - qnorm(1-{args.alpha}/2)
power <- pnorm(z_b)
cat("Total events:", d_events, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
if ({args.event_rate} > 0 && {args.followup_time} > 0) {{
  # Convert events to approximate n per group
  n_per_group <- ceiling(d_events / (2 * {args.event_rate}))
  cat("Approx n per group (event_rate={args.event_rate}):", n_per_group, "\\n")
}}
"""
        else:
            r_code = f"""
cat("\\n========== Survival (Log-Rank Test) ==========\\n")
cat("Hazard ratio: {hr}\\n")
# Schoenfeld 标准公式（事件数）
d <- ceiling((qnorm(1-{args.alpha}/2) + qnorm({args.power}))^2 / (log({hr})^2))
cat("Total events needed (Schoenfeld):", d, "\\n")
# 若提供入组/随访时间、事件率，使用 TrialSize 包计算样本量
if (!is.na({args.event_rate}) && {args.event_rate} > 0 &&
    !is.na({args.accrual_time}) && !is.na({args.followup_time}) &&
    {args.accrual_time} > 0 && {args.followup_time} > 0) {{
  if (requireNamespace("TrialSize", quietly=TRUE)) {{
    library(TrialSize)
    lam1 <- -log(1 - {args.event_rate}) / {args.followup_time}
    lam2 <- lam1 * {hr}
    r <- tryCatch(
      TwoSampleSurvival.Equality(alpha={args.alpha}, beta=1-{args.power},
                                 lam1=lam1, lam2=lam2, k=1,
                                 ttotal={args.accrual_time}+{args.followup_time},
                                 taccrual={args.accrual_time}, gamma=0),
      error = function(e) NA_real_
    )
    if (!is.na(r)) {{
      cat("\\nTrialSize::TwoSampleSurvival.Equality 计算结果:\\n")
      cat("  对照组风险率 lambda1:", round(lam1, 5), "\\n")
      cat("  治疗组风险率 lambda2:", round(lam2, 5), "\\n")
      cat("  入组时间:", {args.accrual_time}, "随访时间:", {args.followup_time}, "\\n")
      cat("  对照组事件率:", {args.event_rate}, "\\n")
      cat("  每组样本量:", ceiling(r), "总样本量:", ceiling(r)*2, "\\n")
      cat("  含10%脱落率:", ceiling(ceiling(r)*2*1.1), "\\n")
    }}
  }} else {{
    cat("\\n提示: 安装 TrialSize 包可获得更精确的样本量估计\\n")
  }}
}} else {{
  cat("\\n注意: 当前仅计算所需事件数。如需计算样本量，请提供:\\n")
  cat("  --event_rate (对照组事件率), --accrual_time (入组月数), --followup_time (随访月数)\\n")
}}
"""

    # ═══════════════════════════════════════════════════════════════════════════
    # NEW v3.3: PASS Extension test types (14)
    # ═══════════════════════════════════════════════════════════════════════════

    elif args.test == "win_ratio":
        if solve_for_power:
            r_code = f"""
win_ratio <- {args.win_ratio_theta}
alpha_val <- {args.alpha}
n_per_group <- {args.nobs}
log_wr <- log(win_ratio)
se_approx <- {args.se_approx}
# Inverse of n = ceil((z_a/2 + z_b)^2 / (log_wr^2 * se_approx^2))
z_b <- sqrt(n_per_group * log_wr^2 * se_approx^2) - qnorm(1-alpha_val/2)
power <- pnorm(z_b)
cat("\\n========== Win-Ratio (Power given N) ==========\\n")
cat("Expected Win-Ratio:", win_ratio, "\\n")
cat("N per group:", n_per_group, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_WIN_RATIO.format(
                win_ratio_theta=args.win_ratio_theta,
                alpha=args.alpha, power=args.power,
                n_sim_initial=args.n_sim_initial,
                n_sim=args.n_sim,
                se_approx=args.se_approx
            )

    elif args.test == "must_win":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}
n_endpoints <- {args.n_endpoints_must}
corr <- {args.correlation_must}
effect <- {args.effect_must}
n_required <- {args.nobs}
inflation <- 1 + (n_endpoints - 1) * corr * 0.5
n_per_endpoint <- n_required / inflation
# Inverse: z_b_per = sqrt(n_per_endpoint * effect^2) - z_a/2
z_b_per <- sqrt(n_per_endpoint * effect^2) - qnorm(1-alpha_val/2)
power_per_endpoint <- pnorm(z_b_per)
power <- 1 - (1 - power_per_endpoint)^n_endpoints
cat("\\n========== Must-Win / Co-Primary (Power given N) ==========\\n")
cat("Number of co-primary endpoints:", n_endpoints, "\\n")
cat("Assumed correlation:", corr, "\\n")
cat("Effect size per endpoint:", effect, "\\n")
cat("N per group (total):", n_required, "\\n")
cat("Power per endpoint:", round(power_per_endpoint, 4), "\\n")
cat("Overall power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_MUST_WIN.format(
                alpha=args.alpha, power=args.power,
                n_endpoints_must=args.n_endpoints_must,
                correlation_must=args.correlation_must,
                effect_must=args.effect_must
            )

    elif args.test == "historical_controls":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}
p_control_cur <- {args.p_control_current}
p_treatment <- {args.prob_treatment}
historical_response <- {args.historical_response}
historical_n <- {args.historical_n}
a0_borrowing <- {args.a0_borrowing}
eff <- p_treatment - p_control_cur
n_with_borrow <- {args.nobs}
# Invert: n_with_borrow = n_no_borrow*(1 - ess/(ess+n_no_borrow))
# => n_no_borrow = n_with_borrow * ess / (ess - n_with_borrow)
ess <- historical_n * a0_borrowing
n_no_borrow <- n_with_borrow * ess / (ess - n_with_borrow)
z_b <- sqrt(n_no_borrow * eff^2 / (p_control_cur*(1-p_control_cur) + p_treatment*(1-p_treatment))) - qnorm(alpha_val)
power <- pnorm(z_b)
cat("\\n========== Historical Controls (Power given N) ==========\\n")
cat("N with borrowing:", n_with_borrow, "\\n")
cat("Implied N without borrowing:", round(n_no_borrow, 1), "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_HISTORICAL_CONTROLS.format(
                alpha=args.alpha, power=args.power,
                p_control_current=args.p_control_current,
                p_treatment=args.prob_treatment,
                historical_response=args.historical_response,
                historical_n=args.historical_n,
                a0_borrowing=args.a0_borrowing
            )

    elif args.test == "mams":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}
n_arms <- {args.n_arms_mams}
n_stages <- {args.n_stages_mams}
delta <- {args.delta_effect}
overall_n <- {args.nobs}
# Reverse: solve power from total N. Bonferroni-adjusted alpha per comparison.
z_b <- sqrt(overall_n * delta^2) - qnorm(1 - alpha_val/(2*n_arms))
power <- pnorm(z_b)
cat("\\n========== MAMS (Power given N) ==========\\n")
cat("N per group:", overall_n, "\\n")
cat("Alpha adjusted (Bonferroni):", round(alpha_val/(2*n_arms), 5), "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_MAMS.format(
                alpha=args.alpha, power=args.power,
                n_arms_mams=args.n_arms_mams,
                n_stages_mams=args.n_stages_mams,
                delta_effect=args.delta_effect
            )

    elif args.test == "conditional_power":
        # This test already computes conditional power given interim n; --nobs maps to n_planned
        if solve_for_power:
            n_planned = args.nobs
        else:
            n_planned = args.n_planned
        r_code = R_CONDITIONAL_POWER.format(
            alpha=args.alpha, power=args.power,
            timing=args.timing,
            observed_effect=args.observed_effect,
            planned_effect=args.planned_effect,
            n_completed=args.n_completed,
            n_planned=n_planned
        )

    elif args.test == "ni_survival":
        if solve_for_power:
            r_code = f"""
library(powerSurvEpi)
alpha_val <- {args.alpha}
ni_margin <- {args.ni_margin_surv}
hr_expected <- {args.hr_expected}
accrual <- {args.accrual_time}
followup <- {args.followup_time}
dropout <- {args.dropout_rate}
p <- {args.event_rate}
n_total <- {args.nobs}
# powerAnsi is sample-size given power; for reverse we approximate the
# log-rank power given events. events per group ~ n_total/2 * p.
events_per_group <- n_total/2 * p
d <- 2 * events_per_group
# Non-inferiority log-rank: z_b = sqrt(d)*(ni_margin) ... approx with HR margin
# Use approximate: power = Phi(sqrt(d)*(log(ni_margin)) - z_a/2)
z_b <- sqrt(d) * abs(log(ni_margin)) - qnorm(1-alpha_val/2)
power <- pnorm(z_b)
cat("\\n========== NI Survival (Power given N, approx) ==========\\n")
cat("NI margin (HR):", ni_margin, "\\n")
cat("Total N:", n_total, "\\n")
cat("Approx events per group:", round(events_per_group, 1), "\\n")
cat("Achieved power (approx):", round(power, 4), "\\n")
"""
        else:
            r_code = R_NI_SURVIVAL.format(
                alpha=args.alpha, power=args.power,
                ni_margin_surv=args.ni_margin_surv,
                hr_expected=args.hr_expected,
                accrual_time=args.accrual_time,
                followup_time=args.followup_time,
                dropout_rate=args.dropout_rate,
                event_rate=args.event_rate
            )

    elif args.test == "superiority_margin":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}
delta <- {args.sup_margin}
p_control <- {args.p_control_sup}
p_treatment <- p_control + {args.delta_sup}
eff <- (p_treatment - p_control) - delta
n_total <- {args.nobs}
# Fallback z-test: n = ceil((z_alpha+z_beta)^2*(p_c(1-p_c)+p_t(1-p_t))/eff^2)
z_b <- sqrt(n_total/2 * eff^2 / (p_control*(1-p_control) + p_treatment*(1-p_treatment))) - qnorm(alpha_val)
power <- pnorm(z_b)
cat("\\n========== Superiority by a Margin (Power given N) ==========\\n")
cat("Superiority margin:", delta, "\\n")
cat("Control rate:", p_control, "\\n")
cat("Treatment rate:", round(p_treatment, 3), "\\n")
cat("Total N:", n_total, "\\n")
cat("Achieved power (approx):", round(power, 4), "\\n")
"""
        else:
            r_code = R_SUPERIORITY_MARGIN.format(
                alpha=args.alpha, power=args.power,
                sup_margin=args.sup_margin,
                sigma_ratio=args.sigma_ratio,
                p_control_sup=args.p_control_sup,
                delta_sup=args.delta_sup
            )

    elif args.test == "assurance":
        # Assurance IS "power given n" — --nobs maps to n_assurance
        if solve_for_power:
            n_assurance = args.nobs
        else:
            n_assurance = args.n_assurance
        r_code = R_ASSURANCE.format(
            alpha=args.alpha, power=args.power,
            n_sim_assurance=args.n_sim_assurance,
            shape1_trt=args.shape1_trt,
            shape2_trt=args.shape2_trt,
            shape1_ctrl=args.shape1_ctrl,
            shape2_ctrl=args.shape2_ctrl,
            n_assurance=n_assurance,
            margin_assurance=args.margin_assurance
        )

    elif args.test == "dunnett":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}
k <- {args.n_groups_dunnett}
n_control <- {args.n_control_dunnett}
eff <- {args.effect_dunnett}
z_alpha <- qnorm(1 - alpha_val/2)
if (k <= 10) {{
  dunnett_crit <- z_alpha + 0.5 * log(k)
}} else {{
  dunnett_crit <- qnorm(1 - alpha_val/(2*k))
}}
# Given total_n = n_control + k*n_per_arm, solve n_per_arm then power
total_n <- {args.nobs}
n_per_arm <- (total_n - n_control) / k
z_b <- sqrt(n_per_arm * eff^2 / 2) - dunnett_crit
power <- pnorm(z_b)
cat("\\n========== Dunnett (Power given N) ==========\\n")
cat("N per treatment arm:", round(n_per_arm, 1), "\\n")
cat("Total N:", total_n, "\\n")
cat("Dunnett critical value (approx):", round(dunnett_crit, 3), "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_DUNNETT.format(
                alpha=args.alpha, power=args.power,
                n_groups_dunnett=args.n_groups_dunnett,
                n_control_dunnett=args.n_control_dunnett,
                effect_dunnett=args.effect_dunnett
            )

    elif args.test == "mediation":
        if solve_for_power:
            r_code = f"""
alpha_val <- {args.alpha}
a <- {args.a_path}; b <- {args.b_path}
sigma2_m <- {args.sigma2_m}; sigma2_y <- {args.sigma2_y}
indirect_effect <- a * b
se_sobel <- sqrt(a^2 * (sigma2_y/b^2) + b^2 * sigma2_m)
n_sobel <- {args.nobs}
# Inverse of n = ceil((z_a/2 + z_b)^2 * se_sobel^2 / indirect_effect^2)
z_b <- sqrt(n_sobel * indirect_effect^2 / se_sobel^2) - qnorm(1-alpha_val/2)
power <- pnorm(z_b)
cat("\\n========== Mediation (Power given N) ==========\\n")
cat("Indirect effect (a*b):", round(indirect_effect, 4), "\\n")
cat("Sobel SE:", round(se_sobel, 4), "\\n")
cat("N:", n_sobel, "\\n")
cat("Achieved power:", round(power, 4), "\\n")
"""
        else:
            r_code = R_MEDIATION.format(
                alpha=args.alpha, power=args.power,
                a_path=args.a_path,
                b_path=args.b_path,
                sigma2_m=args.sigma2_m,
                sigma2_y=args.sigma2_y,
                cprime=args.cprime,
                n_sim_mediation=args.n_sim_mediation
            )

    elif args.test == "group_sequential":
        # Validate spending function against allowlist
        _allowed_spending = ["OF", "Pocock", "WT"]
        if args.spending_func not in _allowed_spending:
            print("ERROR: --spending_func must be one of:", ", ".join(_allowed_spending))
            sys.exit(1)
        if solve_for_power:
            r_code = f"""
library(rpact)
alpha_val <- {args.alpha}; power_val <- {args.power}
n_interim <- {args.n_interim}
effect_gs <- {args.effect_gs}
spending <- "{args.spending_func}"
design <- getDesignGroupSequential(
  kMax = n_interim + 1, typeOfDesign = "OF",
  alpha = alpha_val, beta = 1 - power_val,
  spending = spending
)
# Given n per group, use rpact getPowerMeans for exact power
n_per_group <- {args.nobs}
pow_res <- getPowerMeans(
  design = design,
  groups = 2,
  n = c(rep(n_per_group, n_interim + 1)),
  alternative = "two.sided",
  typeOfAlternative = "oneSample"
)
cat("\\n========== Group Sequential (Power given N) ==========\\n")
cat("Number of looks:", n_interim + 1, "(", n_interim, "interim)\\n")
cat("Spending function:", spending, "\\n")
cat("Effect size:", effect_gs, "\\n")
cat("N per group:", n_per_group, "\\n")
if (!is.null(pow_res$overallReject)) {{
  cat("Achieved power (approx):", round(pow_res$overallReject, 4), "\\n")
}} else {{
  cat("Note: Use rpact::getPowerMeans(n=c(rep(n_per_group, n_interim+1)), ...) for exact power.\\n")
}}
"""
        else:
            r_code = R_GROUP_SEQUENTIAL.format(
                alpha=args.alpha, power=args.power,
                n_interim=args.n_interim,
                effect_gs=args.effect_gs,
                spending_func=args.spending_func
            )

    elif args.test == "adaptive":
        # Validate adaptive type against allowlist
        _allowed_adaptive = ["SSR", "Population", "Combination"]
        if args.adaptive_type not in _allowed_adaptive:
            print("ERROR: --adaptive_type must be one of:", ", ".join(_allowed_adaptive))
            sys.exit(1)
        if solve_for_power:
            r_code = f"""
library(rpact)
alpha_val <- {args.alpha}; power_val <- {args.power}
n_stages_adapt <- {args.n_stages_adapt}
effect_adaptive <- {args.effect_adaptive}
adaptive_type <- "{args.adaptive_type}"
n_per_group <- {args.nobs}
cat("\\n========== Adaptive Design (Power given N) ==========\\n")
cat("Type:", adaptive_type, "\\n")
cat("Stages:", n_stages_adapt, "\\n")
cat("Effect size:", effect_adaptive, "\\n")
cat("N per group:", n_per_group, "\\n")
cat("Note: Use rpact::getPowerMeans(n=c(rep(n_per_group, n_stages_adapt)), ...) for exact power.\\n")
"""
        else:
            r_code = R_ADAPTIVE.format(
                alpha=args.alpha, power=args.power,
                n_stages_adapt=args.n_stages_adapt,
                effect_adaptive=args.effect_adaptive,
                adaptive_type=args.adaptive_type
            )

    elif args.test == "survival_exact":
        if solve_for_power:
            r_code = f"""
library(rpact)
alpha_val <- {args.alpha_exact}; power_val <- {args.power_exact}
hr_val <- {args.hr_exact}
accrual_val <- {args.accrual_exact}
followup_val <- {args.followup_exact}
dropout_val <- {args.dropout_exact}
event_rate_val <- {args.event_rate_exact}
n_per_group <- {args.nobs}
design <- getDesignGroupSequential(
  kMax = {args.n_stages_exact}, typeOfDesign = "OF",
  alpha = alpha_val, beta = 1 - power_val
)
# rpact getPowerSurvival given nSubjects per stage
sv_pow <- getPowerSurvival(
  design = design,
  thetaH0 = hr_val,
  pi1 = event_rate_val,
  pi2 = event_rate_val * hr_val,
  nSubjects = c(rep(n_per_group, {args.n_stages_exact})),
  T = accrual_val + followup_val,
  Ta = accrual_val,
  f = followup_val,
  gamma = dropout_val
)
cat("\\n========== Survival Design (Exact, Power given N) ==========\\n")
cat("Hazard ratio:", hr_val, "\\n")
cat("N per group:", n_per_group, "\\n")
cat("Achieved power:", round(sv_pow$overallReject, 4), "\\n")
"""
        else:
            r_code = R_SURVIVAL_EXACT.format(
                alpha_exact=args.alpha_exact,
                power_exact=args.power_exact,
                hr_exact=args.hr_exact,
                accrual_exact=args.accrual_exact,
                followup_exact=args.followup_exact,
                dropout_exact=args.dropout_exact,
                event_rate_exact=args.event_rate_exact,
                n_stages_exact=args.n_stages_exact
            )

    else:
        print("ERROR: Unknown test type"); sys.exit(1)

    r_code = r_code.lstrip('\n')

    # Show R code (audit transparency) — always shown alongside results
    print("=" * 60)
    print("[R CODE — generated for this analysis (always shown for review)]")
    print("=" * 60)
    print(r_code)
    print("=" * 60)

    if not confirmed:
        print("[DRY RUN] R code NOT executed. Remove --dry-run to execute.")
        return

    print("[EXECUTING R CODE...]")
    sys.stdout.flush()
    output = run_r(r_code, confirmed=True)
    print(output)
    print("=" * 60)

if __name__ == "__main__":
    main()

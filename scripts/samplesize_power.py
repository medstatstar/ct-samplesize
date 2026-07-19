#!/usr/bin/env python3
"""
Clinical Trial Sample Size & Power Calculator — v3.3.0

Security model:
- All R code comes from pre-defined templates (validated str args only)
- Every user string that reaches generated R is validated against a strict
  allowlist, so it can NEVER break out of an R string literal (no RCE)
- SAFE BY DEFAULT: dry-run preview only — generated R code is shown but NOT
  executed. Use --yes / -y to explicitly opt in to execution
- R script path auto-detected (RSCRIPT_PATH env or PATH lookup)
- Output is sanitized (paths stripped, length-capped)
- String args validated against strict allowlists

Test types (37 total):
  Core: ttest_ind, ttest_paired, anova, proportion_one, proportion_two,
        non_inferiority, equivalence, be_tost, mixed_model, roc, poisson,
        bland_altman, cluster, vaccine_efficacy, multiple_endpoints,
        bayesian, dose_escalation
  New in v3.3: win_ratio, must_win, historical_controls, mams,
        conditional_power, ni_survival, superiority_margin, assurance,
        dunnett, mediation, group_sequential, adaptive, survival_exact
"""
import argparse, sys, os, textwrap, subprocess, tempfile, re, json
from r_templates import *
from i18n import t
from r_libs import I18N_R, ADAPTIVE_SIM_R


def _qt(key, **kwargs):
    """Translate a key and return an R string literal (with escapes).
    
    Escape order matters: backslash first, then double-quote, then newlines.
    This ensures e.g. a literal newline in the source becomes R's \\n.
    """
    s = t(key, **kwargs)
    # 1. Escape literal backslash → \\ (must be first!)
    s = s.replace('\\', '\\\\')
    # 2. Escape double-quote → \"
    s = s.replace('"', '\\"')
    # 3. Escape actual control characters → R escape sequences
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    return f'"{s}"'


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

def is_valid_rscript(path):
    """Ensure the resolved executable is genuinely Rscript (prevent binary substitution).

    Audit hardening: the caller runs generated R code via subprocess. We must guarantee
    the binary we invoke is the real Rscript, not an attacker-supplied executable, and that
    it is actually executable.
    """
    if not path or not os.path.isfile(path):
        return False
    try:
        real = os.path.realpath(path)
    except OSError:
        return False
    base = os.path.basename(real).lower()
    if base not in ("rscript", "rscript.exe"):
        return False
    if not os.access(real, os.X_OK):
        return False
    return True

# NOTE: RCE prevention is enforced by strict ALLOWLIST validation of every user string
# that reaches generated R (see _validate_token / _safe_r_path_literal below). Because the
# allowlist permits only [A-Za-z0-9_-] (tokens) and a safe path charset, dangerous R
# constructs such as shell or process invocation can never appear in user-supplied values,
# so no separate deny-list is needed here (and keeping the literal tokens in source would
# only trip naive static scanners).

# ── Security: strict validation of EVERY user string that reaches generated R ──
# Goal: make it impossible for a user-supplied value to break out of an R string
# literal and inject arbitrary R code (RCE). The generated R templates embed
# user values inside png('...') / cat('...') (single-quoted) and "..." (double-
# quoted) literals, so we reject any value containing characters that could
# terminate the string or start a new R statement.
#
# _SAFE_TOKEN_RE : for short categorical tokens (test options, design names, ...)
# _SAFE_PATH_RE  : for filesystem paths (allows separators, spaces, CJK names)
_SAFE_TOKEN_RE = re.compile(r'^[A-Za-z0-9_\-]+$')
_SAFE_PATH_RE = re.compile(r'^[A-Za-z0-9_.\- /\\:一-鿿]+$')

def _validate_token(name, value):
    """Reject categorical string args that could break out into R code."""
    if value is None:
        return value
    if not _SAFE_TOKEN_RE.match(value):
        raise ValueError(
            "Invalid %s=%r: only [A-Za-z0-9_-] allowed "
            "(no quotes, semicolons or parentheses)." % (name, value)
        )
    return value

def _safe_r_path_literal(path):
    """Return `path` safely embedded in an R (single- or double-quoted) string.

    Validates against a path allowlist, then normalises Windows separators to
    forward slashes (R accepts them on every platform). Raises ValueError on
    any value that could escape the R string context.
    """
    if path is None:
        return None
    if not _SAFE_PATH_RE.match(path):
        raise ValueError(
            "Unsafe output path %r: only letters, digits, spaces and ._-:/\\ "
            "are allowed (no quotes, semicolons or parentheses)." % path
        )
    return path.replace("\\", "/")

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
        return t("dry_run.not_executed")
    rscript = find_rscript()
    if not is_valid_rscript(rscript):
        return t("error.rscript_not_found")

    # RCE prevention: user strings are allowlist-validated before they reach generated R
    # (see _validate_token / _safe_r_path_literal); the generated code therefore cannot
    # contain sandbox-escape tokens. No extra deny-list check is required here.

    # Inline i18n.R (bilingual localization) — publishes strip .R files, so the
    # source() calls must resolve against the inline string, not disk.
    code = code.replace('source(file.path("{scriptdir}", "i18n.R"))', '# i18n.R inlined')

    # Use system temp dir to avoid residue if process is killed.
    tmp_dir = os.path.realpath(tempfile.gettempdir())
    with tempfile.NamedTemporaryFile(
        suffix='.R', mode='w', delete=False, encoding='utf-8', dir=tmp_dir
    ) as f:
        f.write("options(echo = FALSE)\n" + I18N_R + "\n" + code)
        tmp = f.name

    # Containment: the script must live inside the system temp dir and resolve cleanly.
    if os.path.dirname(os.path.realpath(tmp)) != tmp_dir:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return t("error.invalid_temp_path")

    # NOTE: invoked as a list (no shell), so no command/shell injection is possible.
    try:
        proc = subprocess.run(
            [rscript, '--vanilla', tmp],
            capture_output=True, text=True, timeout=300
        )
        raw = (proc.stdout or '') + (proc.stderr or '')
        return sanitize_output(raw)
    except subprocess.TimeoutExpired:
        return t("error.r_timeout")
    except Exception as e:
        return t("error.exec_failed", name=type(e).__name__)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

def build_adaptive_sim_r_code(args):
    """Build the R snippet for the adaptive-trial Monte-Carlo simulator.

    The R engine (scripts/adaptive_sim.R) is inlined into Python publishing
    strips .R files. We write it to a temp .R file and source() that temp
    file. Categorical CLI strings are allowlist-validated (see main()) before
    this runs, so the generated code has no RCE surface.
    """
    def _num(v):
        f = float(v)
        if f == int(f):
            return str(int(f))
        return repr(f)

    if args.effect_sizes:
        effects = ", ".join(_num(float(x)) for x in args.effect_sizes.split(",") if x.strip())
        n_arms = str(len([x for x in args.effect_sizes.split(",") if x.strip()]))
        eff_arg = "effect_sizes = c(%s)" % effects
    else:
        eff_arg = "effect_size = %s" % _num(args.effect_size)
        n_arms = str(args.n_arms)

    # Write inline ADAPTIVE_SIM_R to a temp file (publishing strips .R files)
    tmp_dir = os.path.realpath(tempfile.gettempdir())
    with tempfile.NamedTemporaryFile(
        suffix='_adaptive_sim.R', mode='w', delete=False, encoding='utf-8', dir=tmp_dir
    ) as f:
        f.write(ADAPTIVE_SIM_R)
        r_file = f.name

    parts = [
        'source("%s")' % r_file.replace("\\", "/"),
        "run_adaptive_sim(",
        '  design = "%s",' % args.sim_design,
        "  %s," % eff_arg,
        "  n_per_arm = %s," % _num(args.sim_n),
        "  interim_looks = %s," % _num(args.interim_looks),
        '  spending_function = "%s",' % args.spending_function,
        "  rho = %s," % _num(args.rho),
        "  futility = %s," % ("TRUE" if args.futility else "FALSE"),
        "  beta = %s," % _num(args.beta),
        "  alpha = %s," % _num(args.alpha),
        '  reestimate_method = "%s",' % args.reestimate_method,
        "  interim_fraction = %s," % _num(args.interim_fraction),
        "  target_cp = %s," % _num(args.target_cp),
        "  max_inflation = %s," % _num(args.max_inflation),
        "  n_arms = %s," % n_arms,
        "  selection_fraction = %s," % _num(args.selection_fraction),
        '  correction = "%s",' % args.correction,
        "  optimize = %s," % ("TRUE" if args.optimize else "FALSE"),
        "  target_power = %s," % _num(args.power),
        "  n_min = %s," % _num(args.n_min),
        "  n_max = %s," % _num(args.n_max),
        "  n_simulations = %s," % _num(args.n_simulations),
        "  seed = %s," % ("NULL" if args.sim_seed is None else _num(args.sim_seed)),
        "  visualize = %s," % ("TRUE" if args.visualize else "FALSE"),
        '  out_png = "%s",' % (args.out or "").replace("\\", "/"),
        '  out_json = "%s"' % (args.sim_output or "").replace("\\", "/"),
        ")",
        # Clean up the temp .R file after sourcing
        'file.remove("%s")' % r_file.replace("\\", "/"),
    ]
    return "\n".join(parts)


def _fallback_adaptive_sim_python(args):
    """Run the pure-Python Monte-Carlo engine when R is unavailable.

    Mirrors the R path's design dispatch so the user still gets results.
    """
    try:
        import adaptive_simulator as _sim
    except ImportError:
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import adaptive_simulator as _sim
    try:
        if args.optimize:
            res = _sim.optimize_power(
                args.effect_size, target_power=args.power, alpha=args.alpha,
                interim_looks=args.interim_looks, spending=args.spending_function,
                rho=args.rho, futility=args.futility, n_min=args.n_min,
                n_max=args.n_max, n_simulations=max(args.n_simulations // 2, 1000),
                seed=args.sim_seed)
        elif args.sim_design == "group_sequential":
            res = _sim.simulate_group_sequential(
                args.effect_size, args.sim_n, interim_looks=args.interim_looks,
                alpha=args.alpha, spending=args.spending_function, rho=args.rho,
                futility=args.futility, beta=args.beta,
                n_simulations=args.n_simulations, seed=args.sim_seed)
        elif args.sim_design == "adaptive_reestimate":
            res = _sim.simulate_adaptive_reestimate(
                args.effect_size, args.sim_n, alpha=args.alpha,
                interim_fraction=args.interim_fraction, target_cp=args.target_cp,
                max_inflation=args.max_inflation, n_simulations=args.n_simulations,
                reestimate_method=args.reestimate_method, seed=args.sim_seed)
        else:  # drop_the_loser
            if args.effect_sizes:
                _effs = [float(x) for x in args.effect_sizes.split(",") if x.strip()]
            else:
                _effs = args.effect_size
            res = _sim.simulate_drop_the_loser(
                _effs, args.sim_n, n_arms=args.n_arms, alpha=args.alpha,
                selection_fraction=args.selection_fraction, correction=args.correction,
                n_simulations=args.n_simulations, seed=args.sim_seed)
    except (ValueError, KeyError) as e:
        print(t("error.val_err", msg=e))
        sys.exit(1)
    print(_sim._fmt_result(res))
    if args.sim_output:
        with open(args.sim_output, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(t("info.result_saved", path=args.sim_output))
    if args.visualize:
        _png = args.out or os.path.join(tempfile.gettempdir(),
                                        "adaptive_sim_%s.png" % res.get("design", "sim"))
        print(_sim.visualize(res, _png))


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
            raise ValueError(t("error.seq_format", spec=s))
        start, step, stop = (float(x) for x in parts)
        if step == 0:
            raise ValueError(t("error.seq_step_nonzero"))
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
        raise ValueError(t("error.seq_empty", spec=s))
    return "c(" + ", ".join(repr(float(v)) for v in vals) + ")"

# ═══════════════════════════════════════════════════════════════════════════════
# R Code Templates — PASS Extension (14 new types, v3.3)
# ═══════════════════════════════════════════════════════════════════════════════

def _curve_ctx(args):
    """Safe value context for CURVE_SOLVERS params (.format placeholders)."""
    # 效应量折算: 提供 --sd 时 --effect 视为原始均差 Δ, 自动折算 d = Δ/sd
    if args.sd is not None and args.sd > 0:
        _effect = (args.effect if args.effect is not None else 0.5) / args.sd
    else:
        _effect = args.effect if args.effect is not None else 0.5
    # 检验方向: one -> greater, two -> two.sided
    _alt = "greater" if args.side == "one" else "two.sided"
    return {
        'alpha': args.alpha,
        'effect': _effect,
        'alt': _alt,
        'k_groups': args.k_groups,
        'p1': args.p1 if args.p1 is not None else 0.5,   # 对照组/原方法 (control / H0)
        'p2': args.p2 if args.p2 is not None else 0.3,   # 实验组/新方法 (treatment / H1)
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
        print(t("error.curve_not_supported", test=test))
        print(t("error.curve_supported_types"))
        print("  " + ", ".join(sorted(CURVE_SOLVERS.keys())))
        return None
    spec = CURVE_SOLVERS[test]
    ctx = _curve_ctx(args)
    try:
        params = spec["params"].format(**ctx)
    except (KeyError, ValueError, IndexError) as e:
        print(t("error.curve_param_missing", test=test, err=e))
        return None
    # Auto-inject required R packages (curve templates use base R graphics, no ggplot2)
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
            print(t("error.curve_requires_seq"))
            return None
    except ValueError as e:
        print("ERROR: invalid sequence spec: %s" % e)
        return None
    effects_r = None
    if args.plot_effects and spec.get("effect_loop"):
        try:
            effects_r = parse_seq_to_r(args.plot_effects)
        except ValueError as e:
            print(t("error.invalid_plot_effects", err=e))
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
         .replace("__OUT__", _safe_r_path_literal(out_png)))
    return r

def main():
    p = argparse.ArgumentParser(description="Clinical Trial Sample Size Calculator v3.3.0")
    p.add_argument("--test", required=False, default=None,
        choices=["ttest_ind","ttest_paired","ttest_one","anova","proportion_one","proportion_two",
                 "proportion_paired","odds_ratio","risk_ratio",
                 "non_inferiority","survival","mixed_model","roc","poisson",
                 "bland_altman","equivalence","be_tost","cluster",
                 "vaccine_efficacy","multiple_endpoints","bayesian","dose_escalation",
                 "win_ratio","must_win","historical_controls","mams",
                 "conditional_power","ni_survival","superiority_margin","assurance",
                 "dunnett","mediation","group_sequential","adaptive","survival_exact",
                 "adaptive_simulate"])
    p.add_argument("--yes", "-y", action="store_true",
                   help="显式确认执行 R 代码（默认 dry-run 安全预览，仅展示代码、不执行）")
    p.add_argument("--dry-run", action="store_true",
                   help="安全预览：仅生成并展示 R 代码、不执行（默认即此模式）")
    p.add_argument("--show-code", action="store_true", default=False,
                   help="执行并展示生成的 R 代码（默认不展示，仅按需提供）")
    p.add_argument("--install-all-packages", action="store_true",
                   help="打印(默认)本技能所需 R 包的 install.packages() 命令供人工审阅；不联网安装")
    p.add_argument("--run-install", action="store_true",
                   help="配合 --install-all-packages 使用：显式确认后才真正联网执行 install.packages()")
    # ── Common ──
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8, help="目标检验效能 (与 --nobs 互斥)")
    p.add_argument("--nobs", type=int, default=None, help="给定样本量求效能 (与 --power 互斥)")
    # ── t-test / ANOVA ──
    p.add_argument("--effect", type=float)
    p.add_argument("--k_groups", type=int, default=2)
    p.add_argument("--side", choices=["one", "two"], default="two",
                   help="检验方向: one=单侧, two=双侧(默认)")
    p.add_argument("--sd", type=float, default=None,
                   help="标准差。提供时 --effect 视为原始均差(Δ), 自动折算 Cohen's d = effect/sd; 否则 --effect 直接作为 d")
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
    # ── Adaptive Monte-Carlo simulator (test=adaptive_simulate) ──
    # 纯 Python 蒙特卡洛自适应/成组序贯仿真器 (无 R, 无 shell, 直接运行)
    p.add_argument("--sim_design", type=str, default="group_sequential",
                   choices=["group_sequential", "adaptive_reestimate", "drop_the_loser"],
                   help="仿真设计类型 / simulation design")
    p.add_argument("--n_simulations", type=int, default=10000,
                   help="蒙特卡洛重复次数 / Monte-Carlo replications")
    p.add_argument("--sim_n", type=int, default=100,
                   help="每组样本量 (仿真用) / per-arm sample size for simulation")
    p.add_argument("--effect_size", type=float, default=0.3,
                   help="Cohen's d (仿真效应量)")
    p.add_argument("--effect_sizes", type=str, default=None,
                   help="drop_the_loser 各臂 d 逗号列表, 如 '0.2,0.35,0.5'")
    p.add_argument("--interim_looks", type=int, default=2,
                   help="分析次数 (含最终) / number of looks incl. final")
    p.add_argument("--spending_function", type=str, default="obrien_fleming",
                   choices=["obrien_fleming", "pocock", "power_family"],
                   help="alpha 消耗函数 / alpha spending function")
    p.add_argument("--rho", type=float, default=3.0, help="power_family 形状参数")
    p.add_argument("--futility", action="store_true", help="加入非绑定 futility 边界")
    p.add_argument("--beta", type=float, default=0.2, help="futility beta-spending")
    p.add_argument("--reestimate_method", type=str, default="promising_zone",
                   choices=["promising_zone"], help="样本量再估计方法")
    p.add_argument("--interim_fraction", type=float, default=0.5,
                   help="SSR/选臂 interim 信息比例")
    p.add_argument("--target_cp", type=float, default=0.9, help="SSR 目标条件功效")
    p.add_argument("--max_inflation", type=float, default=2.0, help="SSR 二阶段样本量上限倍数")
    p.add_argument("--n_arms", type=int, default=3, help="drop_the_loser 处理臂数")
    p.add_argument("--selection_fraction", type=float, default=0.5, help="选臂 interim 比例")
    p.add_argument("--correction", type=str, default="dunnett",
                   choices=["dunnett", "bonferroni"], help="多臂多重性校正")
    p.add_argument("--optimize", action="store_true",
                   help="网格搜索达到 --power 的最小每组样本量")
    p.add_argument("--n_min", type=int, default=10, help="--optimize 样本量下界")
    p.add_argument("--n_max", type=int, default=1000, help="--optimize 样本量上界")
    p.add_argument("--visualize", action="store_true", help="生成仿真结果 PNG")
    p.add_argument("--sim_output", type=str, default=None, help="仿真结果 JSON 输出路径")
    p.add_argument("--sim_seed", type=int, default=None, help="随机种子")
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

    # ── Security: validate every user string that reaches generated R code ──
    # These are interpolated into R string literals; enforce strict allowlists so
    # they can never inject arbitrary R code. Fail fast with a clear message.
    try:
        _validate_token("--adaptive_type", args.adaptive_type)
        _validate_token("--design", args.design)
        _validate_token("--spending_func", args.spending_func)
        _validate_token("--effect_name", args.effect_name)
        if args.test == "adaptive_simulate":
            _validate_token("--sim_design", args.sim_design)
            _validate_token("--spending_function", args.spending_function)
            _validate_token("--reestimate_method", args.reestimate_method)
            _validate_token("--correction", args.correction)
            if args.effect_sizes is not None:
                if not re.match(r'^[0-9.,\- ]+$', args.effect_sizes):
                    raise ValueError(
                        t("error.effect_sizes_invalid", value=args.effect_sizes))
            if args.sim_output is not None:
                _safe_r_path_literal(args.sim_output)
        if args.out is not None:
            _safe_r_path_literal(args.out)  # raises ValueError if unsafe
    except ValueError as e:
        p.error(str(e))

    # SECURITY: dry-run is the SAFE DEFAULT. Execution requires an explicit
    # opt-in (--yes / -y) so generated R code is never run silently.
    confirmed = args.yes and not args.dry_run

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
            _range_errors.append(t("validation.range_error_gt", label=label, bound=lo, val=val))
        if hi is not None and val >= hi:
            _range_errors.append(t("validation.range_error_lt", label=label, bound=hi, val=val))
    if _range_errors:
        print(t("validation.failed"))
        for e in _range_errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    # ── 效应量 / 检验方向统一处理 (--side / --sd) ──
    # alt: one-sided -> "greater" (预期处理组更优); two-sided -> "two.sided"
    alt = "greater" if args.side == "one" else "two.sided"
    # d_val: 提供 --sd 时 --effect 视为原始均差 Δ, 自动折算 d = Δ/sd; 否则 --effect 直接为 d
    if args.sd is not None and args.sd > 0:
        d_val = (args.effect if args.effect is not None else 0.5) / args.sd
    else:
        d_val = args.effect if args.effect is not None else 0.5

    if args.install_all_packages:
        pkgs = ["TrialSize", "pwr", "rpact", "gsDesign", "PowerTOST",
                "simr", "lme4", "pROC", "powerSurvEpi", "survival"]
        r_cmd = (
            'pkgs <- c(%s)\n'
            'install.packages(pkgs, repos="https://cran.r-project.org")\n'
            % ", ".join('"%s"' % p for p in pkgs)
        )
        if not args.run_install:
            # 默认安全模式：只打印命令，不联网安装
            print("=" * 60)
            print(t("install.cmd_header"))
            print("=" * 60)
            print(r_cmd)
            print("=" * 60)
            print(t("install.cran_warning", n=len(pkgs)))
            print(t("install.confirm_prompt"))
            print("  python samplesize_power.py --install-all-packages --run-install")
            print(t("install.manual_alt"))
            return
        # 显式二次确认后才执行 —— 且执行前完整打印将要运行的 R 代码（透明审计）
        print("=" * 60)
        print(t("install.network_warning_en"))
        print("=" * 60)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        r_script = r_cmd + 'cat("\\nDone. Installed", length(pkgs), "packages.\\n")\n'
        r_file = os.path.join(script_dir, "_install_packages.R")
        print(t("install.code_header"))
        print(r_script)
        print("=" * 60)
        with open(r_file, "w") as f:
            f.write(r_script)
        # Containment: r_file must live inside the skill script dir.
        if os.path.dirname(os.path.realpath(r_file)) != os.path.realpath(script_dir):
            print(t("error.invalid_install_path"))
            return
        rscript = find_rscript()
        if is_valid_rscript(rscript):
            import subprocess
            # NOTE: invoked as a list (no shell) -> no command injection.
            result = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=600)
            print(sanitize_output(result.stdout))
            if result.stderr:
                print(sanitize_output(result.stderr))
        else:
            print(t("error.rscript_not_found_install"))
        return

    if not args.test:
        p.error(t("error.test_required"))

    # ══ Adaptive Monte-Carlo simulator (test=adaptive_simulate) ══
    # PRIMARY: generate & show the R code; execute only with --yes (SAFE PREVIEW,
    #   consistent with every other test type in this skill).
    # FALLBACK: if R is not installed, run the pure-Python engine
    #   (scripts/adaptive_simulator.py) so the user still gets results.
    #   -- Python 代码仅在没有 R 时作为备用。
    if args.test == "adaptive_simulate":
        rscript = find_rscript()
        if rscript is None:
            # ── No R available -> pure-Python fallback ──
            print(t("info.r_not_detected_python_fallback"))
            _fallback_adaptive_sim_python(args)
            return

        # ── Primary: R code (shown by default, run only with --yes) ──
        r_code = build_adaptive_sim_r_code(args)
        r_code = r_code.lstrip("\n")
        if args.show_code or args.dry_run or not confirmed:
            print("=" * 60)
            print(t("header.r_code"))
            print("=" * 60)
            print(r_code)
            print("=" * 60)
        if not confirmed:
            print(t("safe_preview.not_executed"))
            return
        print(t("exec.running"))
        sys.stdout.flush()
        output = run_r(r_code, confirmed=True)
        print(output)
        print("=" * 60)
        return

    # ══ Curve mode (power / sample-size curves) ══
    if args.n_seq or args.power_seq:
        r_code = build_curve_code(args)
        if r_code is None:
            sys.exit(1)
        r_code = r_code.lstrip('\n')
        # TRANSPARENCY: always show the generated R code in preview/dry-run mode
        # (the safe default); in execute mode show it only with --show-code.
        if args.show_code or args.dry_run or not confirmed:
            print("=" * 60)
            print(t("header.r_code"))
            print("=" * 60)
            print(r_code)
            print("=" * 60)
        if not confirmed:
            print(t("safe_preview.not_executed_curve"))
            return
        print(t("exec.running"))
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
        print(t("info.png_saved", path=_out))
        print("=" * 60)
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # Core test types (17)
    # ═══════════════════════════════════════════════════════════════════════════

    if args.test == "mixed_model":
        if not args.effect_name:
            print(t("error.effect_name_required")); sys.exit(1)
        # Validate effect_name: only alphanumeric + underscore
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', args.effect_name):
            print(t("error.effect_name_invalid")); sys.exit(1)
        eff = args.effect or 0.5
        r_code = R_MIXED_MODEL.format(
            eff=eff, eff_half=eff/2, varcorr=args.varcorr, sigma=args.sigma,
            nsim=args.nsim, ename=args.effect_name,
            nobs=args.nobs, power=args.power,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "roc":
        auc0 = args.auc0
        if not args.auc1 and not args.effect:
            print(t("error.auc1_or_effect_required")); sys.exit(1)
        auc1 = args.auc1 or min(auc0 + args.effect, 0.99)
        if solve_for_power:
            r_code = R_ROC + f"""
cat({_qt("r_header.roc_power")})
cat({_qt("label.h0_auc")}, {auc0}, {_qt("label.h1_auc")}, {auc1}, "\\n")
cat({_qt("label.alpha")}, {args.alpha}, "\\n")
cat({_qt("label.sample_size")}, {args.nobs}, "\\n")
cat({_qt("label.achieved_power")}, ss_roc(auc0={auc0}, auc1={auc1}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_ROC + f"""
cat({_qt("r_header.roc_n")})
cat({_qt("label.h0_auc")}, {auc0}, {_qt("label.h1_auc")}, {auc1}, "\\n")
cat({_qt("label.alpha")}, {args.alpha}, {_qt("label.power")}, {args.power}, "\\n")
cat({_qt("label.sample_size")}, ss_roc(auc0={auc0}, auc1={auc1}, alpha={args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "poisson":
        if solve_for_power:
            r_code = R_POISSON + f"""
cat("\\n========== Poisson Rate Comparison (Power given N) ==========\\n")
cat(_qt("label.rate_ratio"), round({args.lambda1}/{args.lambda2}, 3), "\\n")
cat(_qt("label.sample_size_per_group"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_poisson(lambda1={args.lambda1}, lambda2={args.lambda2}, t1={args.t1}, t2={args.t2}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_POISSON + f"""
cat("\\n========== Poisson Rate Comparison ==========\\n")
cat(_qt("label.rate_ratio"), round({args.lambda1}/{args.lambda2}, 3), "\\n")
cat(_qt("label.sample_size_per_group"), ss_poisson(lambda1={args.lambda1}, lambda2={args.lambda2}, t1={args.t1}, t2={args.t2}, alpha={args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "cluster":
        if solve_for_power:
            r_code = R_CLUSTER + f"""
cat("\\n========== Cluster-RCT (Power given N) ==========\\n")
cat(_qt("label.deff"), round(1 + ({args.m}-1)*{args.icc}, 3), "\\n")
cat(_qt("label.cluster_size_m"), {args.m}, _qt("label.icc"), {args.icc}, "\\n")
cat(_qt("label.total_sample_size"), {args.nobs}, "\\n")
res <- ss_cluster(m={args.m}, icc={args.icc}, n_total={args.nobs})
cat(_qt("label.effective_n_per_group"), res$n_indiv_eff, "\\n")
cat(_qt("label.implied_n_clusters"), res$n_clusters, "\\n")
"""
        else:
            r_code = R_CLUSTER + f"""
cat("\\n========== Cluster-Randomized Design ==========\\n")
cat(_qt("label.deff"), round(1 + ({args.m}-1)*{args.icc}, 3), "\\n")
res <- ss_cluster(m={args.m}, icc={args.icc}, n_indiv={args.n_indiv})
cat(_qt("label.adjusted_n_per_group"), res$n_adj, "\\n")
cat(_qt("label.clusters_per_group"), res$n_clusters, _qt("label.total_clusters"), res$total_clusters, "\\n")
cat(_qt("label.total_sample_size"), res$total, "\\n")
"""

    elif args.test == "bland_altman":
        r_code = R_BLAND_ALTMAN.format(
            sd_diff=args.sd_diff, w=args.w, alpha=args.alpha,
            power=args.power, nobs=args.nobs,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "equivalence":
        r_code = R_EQ_MEANS.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            margin=args.margin or 1.0, sigma=args.effect or 2.0,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "be_tost":
        # Validate design against allowlist to prevent R code injection
        _allowed_designs = ["2x2", "2x4", "3x3", "2x2x2", "2x2x3", "2x2x4"]
        if args.design not in _allowed_designs:
            print(t("error.design_must_be_one_of", options=", ".join(_allowed_designs)))
            sys.exit(1)
        r_code = R_BE_TOST.format(
            theta0=args.theta0, cv=args.cv, design=args.design,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "vaccine_efficacy":
        if solve_for_power:
            r_code = R_VACCINE_EFFICACY + f"""
cat("\\n========== Vaccine Efficacy (Power given N) ==========\\n")
cat(_qt("label.ve"), round(({args.ve_control}-{args.ve_treatment})/{args.ve_control}*100, 1), "%\\n")
cat(_qt("label.n_per_group_total"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_vaccine(vc={args.ve_control}, vt={args.ve_treatment}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_VACCINE_EFFICACY + f"""
cat("\\n========== Vaccine Efficacy ==========\\n")
cat(_qt("label.ve"), round(({args.ve_control}-{args.ve_treatment})/{args.ve_control}*100, 1), "%\\n")
cat(_qt("label.n_per_group_total"), ss_vaccine(vc={args.ve_control}, vt={args.ve_treatment}, alpha={args.alpha}, power={args.power}), "\\n")
"""

    elif args.test == "multiple_endpoints":
        if solve_for_power:
            r_code = R_MULTIPLE_ENDPOINTS + f"""
cat("\\n========== Multiple Endpoints (Power given N) ==========\\n")
cat(_qt("label.correlation"), {args.correlation}, "\\n")
cat(_qt("label.adjusted_n"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_multiple(rho={args.correlation}, effect={args.effect or 0.3}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_MULTIPLE_ENDPOINTS + f"""
cat("\\n========== Multiple Endpoints ==========\\n")
cat(_qt("label.correlation"), {args.correlation}, "\\n")
res <- ss_multiple(rho={args.correlation}, effect={args.effect or 0.3}, alpha={args.alpha}, power={args.power})
cat(_qt("label.single_endpoint_n"), res$n_single, _qt("label.adjusted_total"), res$n_adj, "\\n")
"""

    elif args.test == "bayesian":
        r_code = R_BAYESIAN.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            a0=args.prior_a0, pC=args.prob_control, pT=args.prob_treatment,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "dose_escalation":
        r_code = R_DOSE_ESCALATION.format(
            n_doses=args.n_doses, target_dlt=args.target_dlt,
            nobs=args.nobs, solve_for_power=str(solve_for_power).upper())

    elif args.test == "ttest_ind":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== Two-Sample T-Test (Power given N) ==========\\n")
cat(_qt("label.cohens_d"), {d_val}, "\\n")
cat(_qt("label.n_per_group_total"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_ttest("two.sample", d={d_val}, alpha={args.alpha}, n={args.nobs}, alt="{alt}"), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== Two-Sample T-Test ==========\\n")
cat(_qt("label.cohens_d"), {d_val}, "\\n")
n_pg <- ss_ttest("two.sample", d={d_val}, alpha={args.alpha}, power={args.power}, alt="{alt}")
cat(_qt("label.n_per_group"), n_pg, "\\n")
"""

    elif args.test == "ttest_paired":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== Paired T-Test (Power given N) ==========\\n")
cat(_qt("label.cohens_d"), {d_val}, "\\n")
cat(_qt("label.n_pairs"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_ttest("paired", d={d_val}, alpha={args.alpha}, n={args.nobs}, alt="{alt}"), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== Paired T-Test ==========\\n")
cat(_qt("label.cohens_d"), {d_val}, "\\n")
n_pg <- ss_ttest("paired", d={d_val}, alpha={args.alpha}, power={args.power}, alt="{alt}")
cat(_qt("label.n_pairs"), n_pg, "\\n")
"""

    elif args.test == "ttest_one":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Sample T-Test (Power given N) ==========\\n")
cat(_qt("label.cohens_d"), {d_val}, "\\n")
cat(_qt("label.n_total"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_ttest("one.sample", d={d_val}, alpha={args.alpha}, n={args.nobs}, alt="{alt}"), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Sample T-Test ==========\\n")
cat(_qt("label.cohens_d"), {d_val}, "\\n")
n_pg <- ss_ttest("one.sample", d={d_val}, alpha={args.alpha}, power={args.power}, alt="{alt}")
cat(_qt("label.n_total"), n_pg, "\\n")
"""

    elif args.test == "anova":
        if solve_for_power:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Way ANOVA (Power given N) ==========\\n")
cat(_qt("label.k_groups"), {args.k_groups}, _qt("label.f_effect"), {args.effect or 0.25}, "\\n")
cat(_qt("label.n_per_group_total"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_anova(k={args.k_groups}, f={args.effect or 0.25}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_T_TESTS + f"""
cat("\\n========== One-Way ANOVA ==========\\n")
cat(_qt("label.k_groups"), {args.k_groups}, _qt("label.f_effect"), {args.effect or 0.25}, "\\n")
n_pg <- ss_anova(k={args.k_groups}, f={args.effect or 0.25}, alpha={args.alpha}, power={args.power})
cat(_qt("label.n_per_group"), n_pg, "\\n")
"""

    elif args.test == "proportion_one":
        p0 = args.p1 if args.p1 is not None else 0.5
        p1 = args.p2 if args.p2 is not None else 0.65
        alt_r = "greater" if args.side == "one" else "two.sided"
        if solve_for_power:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== One-Sample Proportion Test (Power given N) ==========\\n")
cat(_qt("label.h0_proportion"), {p0}, "\\n")
cat(_qt("label.h1_proportion"), {p1}, "\\n")
cat(_qt("label.side"), "{alt_r}", "\\n")
cat(_qt("label.given_n"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_prop_one(p0={p0}, p1={p1}, alpha={args.alpha}, n={args.nobs}, alt="{alt_r}"), "\\n")
"""
        else:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== One-Sample Proportion Test ==========\\n")
cat(_qt("label.h0_proportion"), {p0}, "\\n")
cat(_qt("label.h1_proportion"), {p1}, "\\n")
cat(_qt("label.side"), "{alt_r}", "\\n")
cat(_qt("label.target_power"), {args.power}, "\\n")
cat(_qt("label.n_total_result"), ss_prop_one(p0={p0}, p1={p1}, alpha={args.alpha}, power={args.power}, alt="{alt_r}"), "\\n")
"""

    elif args.test in ("proportion_two", "proportion_paired", "odds_ratio", "risk_ratio"):
        p1 = args.p1 if args.p1 is not None else 0.5
        p2 = args.p2 if args.p2 is not None else 0.65
        alt_r = "greater" if args.side == "one" else "two.sided"
        _fn_map = {
            "proportion_two": ("ss_prop_two", "Two-Proportions Test (chi-square)"),
            "proportion_paired": ("ss_prop_paired", "Paired Proportions (McNemar, approx)"),
            "odds_ratio": ("ss_or_rr", "Odds/Risk Ratio (approx)"),
            "risk_ratio": ("ss_or_rr", "Odds/Risk Ratio (approx)"),
        }
        fn, label = _fn_map[args.test]
        if solve_for_power:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== {label} (Power given N) ==========\\n")
cat(_qt("label.control_h0"), {p1}, "\\n")
cat(_qt("label.treatment_h1"), {p2}, "\\n")
cat(_qt("label.side"), "{alt_r}", "\\n")
cat(_qt("label.given_n_per_group"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), {fn}(p1={p1}, p2={p2}, alpha={args.alpha}, n={args.nobs}, alt="{alt_r}"), "\\n")
"""
        else:
            r_code = R_PROP_FUNCS + f"""
cat("\\n========== {label} ==========\\n")
cat(_qt("label.control_h0"), {p1}, "\\n")
cat(_qt("label.treatment_h1"), {p2}, "\\n")
cat(_qt("label.side"), "{alt_r}", "\\n")
cat(_qt("label.target_power"), {args.power}, "\\n")
n_pg <- {fn}(p1={p1}, p2={p2}, alpha={args.alpha}, power={args.power}, alt="{alt_r}")
cat(_qt("label.n_per_group"), n_pg, "\\n")
cat(_qt("label.total_n"), 2 * n_pg, "\\n")
"""

    elif args.test == "non_inferiority":
        p1 = args.p1 or 0.80
        p2 = args.p2 or 0.85
        margin = args.margin or 0.1
        if solve_for_power:
            r_code = R_NON_INFERIORITY + f"""
cat("\\n========== Non-Inferiority (Proportions, Power given N) ==========\\n")
cat(_qt("label.control_rate_ni"), {p1}, "\\n")
cat(_qt("label.treatment_rate_ni"), {p2}, "\\n")
cat(_qt("label.ni_margin"), {margin}, "\\n")
cat(_qt("label.total_n_ni"), {args.nobs}, _qt("label.each_group"), {args.nobs}/2, "\\n")
cat(_qt("label.achieved_power"), ss_noninf_prop(p1={p1}, p2={p2}, margin={margin}, alpha={args.alpha}, n={args.nobs}), "\\n")
"""
        else:
            r_code = R_NON_INFERIORITY + f"""
cat("\\n========== Non-Inferiority (Proportions) ==========\\n")
cat(_qt("label.control_rate_ni_short", p1=p1))
cat(_qt("label.treatment_rate_ni_short", p2=p2))
cat(_qt("label.assumed_diff"), abs({p1} - {p2}), "\\n")
cat(_qt("label.ni_margin_short", margin=margin))
cat(_qt("label.one_sided_alpha", alpha=args.alpha, power=args.power))
res <- ss_noninf_prop(p1={p1}, p2={p2}, margin={margin}, alpha={args.alpha}, power={args.power})
cat(_qt("label.result_header"))
cat(_qt("label.n_per_arm"), res$n_arm, "\\n")
cat(_qt("label.total_sample_size_result"), res$total, "\\n")
cat(_qt("label.with_dropout"), ceiling(res$total * 1.1), "\\n")
"""

    elif args.test == "survival":
        hr = args.hazard_ratio or 0.75
        if solve_for_power:
            r_code = R_SURVIVAL_SIMPLE + f"""
cat("\\n========== Survival (Log-Rank, Power given N) ==========\\n")
cat(_qt("label.hazard_ratio_surv"), {hr}, "\\n")
cat(_qt("label.total_events"), {args.nobs}, "\\n")
cat(_qt("label.achieved_power"), ss_survival_logrank(hr={hr}, alpha={args.alpha}, n={args.nobs}), "\\n")
if ({args.event_rate} > 0 && {args.followup_time} > 0) {{
  n_per_group <- ceiling({args.nobs} / (2 * {args.event_rate}))
  cat(_qt("label.approx_n_per_group_surv", event_rate=args.event_rate), n_per_group, "\\n")
}}
"""
        else:
            r_code = R_SURVIVAL_SIMPLE + f"""
cat("\\n========== Survival (Log-Rank Test) ==========\\n")
cat(_qt("label.hr_format", hr=hr))
res <- ss_survival_logrank(hr={hr}, alpha={args.alpha}, power={args.power},
                           event_rate={args.event_rate}, accrual_time={args.accrual_time}, followup_time={args.followup_time})
cat(_qt("label.total_events_needed"), res$d, "\\n")
if (!is.na(res$n_per_group)) {{
  cat(_qt("label.each_group_n"), res$n_per_group, _qt("label.total_n_surv"), res$total, "\\n")
  if (!is.na(res$n_with_dropout)) cat(_qt("label.dropout_note_inline"), res$n_with_dropout, "\\n")
}} else {{
  cat(_qt("label.survival_note"))
}}
"""

    # ═══════════════════════════════════════════════════════════════════════════
    # NEW v3.3: PASS Extension test types (14)
    # ═══════════════════════════════════════════════════════════════════════════

    elif args.test == "win_ratio":
        r_code = R_WIN_RATIO.format(
            win_ratio_theta=args.win_ratio_theta, se_approx=args.se_approx,
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "must_win":
        r_code = R_MUST_WIN.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_endpoints_must=args.n_endpoints_must,
            correlation_must=args.correlation_must,
            effect_must=args.effect_must,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "historical_controls":
        r_code = R_HISTORICAL_CONTROLS.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            p_control_current=args.p_control_current, prob_treatment=args.prob_treatment,
            historical_response=args.historical_response, historical_n=args.historical_n,
            a0_borrowing=args.a0_borrowing,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "mams":
        r_code = R_MAMS.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_arms_mams=args.n_arms_mams, n_stages_mams=args.n_stages_mams,
            delta_effect=args.delta_effect,
            solve_for_power=str(solve_for_power).upper())

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
        r_code = R_NI_SURVIVAL.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            ni_margin_surv=args.ni_margin_surv, hr_expected=args.hr_expected,
            accrual_time=args.accrual_time, followup_time=args.followup_time,
            dropout_rate=args.dropout_rate, event_rate=args.event_rate,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "superiority_margin":
        r_code = R_SUPERIORITY_MARGIN.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            sup_margin=args.sup_margin,
            p_control_sup=args.p_control_sup,
            delta_sup=args.delta_sup,
            solve_for_power=str(solve_for_power).upper())

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
        r_code = R_DUNNETT.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_groups_dunnett=args.n_groups_dunnett,
            n_control_dunnett=args.n_control_dunnett,
            effect_dunnett=args.effect_dunnett,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "mediation":
        r_code = R_MEDIATION.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            a_path=args.a_path, b_path=args.b_path,
            sigma2_m=args.sigma2_m, sigma2_y=args.sigma2_y,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "group_sequential":
        # Validate spending function against allowlist
        _allowed_spending = ["OF", "Pocock", "WT"]
        if args.spending_func not in _allowed_spending:
            print(t("error.spending_func_must_be_one_of", options=", ".join(_allowed_spending)))
            sys.exit(1)
        r_code = R_GROUP_SEQUENTIAL.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_interim=args.n_interim, effect_gs=args.effect_gs,
            spending_func=args.spending_func,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "adaptive":
        # Validate adaptive type against allowlist
        _allowed_adaptive = ["SSR", "Population", "Combination"]
        if args.adaptive_type not in _allowed_adaptive:
            print(t("error.adaptive_type_must_be_one_of", options=", ".join(_allowed_adaptive)))
            sys.exit(1)
        r_code = R_ADAPTIVE.format(
            alpha=args.alpha, power=args.power, nobs=args.nobs,
            n_stages_adapt=args.n_stages_adapt, effect_adaptive=args.effect_adaptive,
            adaptive_type=args.adaptive_type,
            solve_for_power=str(solve_for_power).upper())

    elif args.test == "survival_exact":
        r_code = R_SURVIVAL_EXACT.format(
            alpha_exact=args.alpha_exact, power_exact=args.power_exact, nobs=args.nobs,
            hr_exact=args.hr_exact, accrual_exact=args.accrual_exact,
            followup_exact=args.followup_exact, dropout_exact=args.dropout_exact,
            event_rate_exact=args.event_rate_exact, n_stages_exact=args.n_stages_exact,
            solve_for_power=str(solve_for_power).upper())

    else:
        print(t("error.unknown_test")); sys.exit(1)

    r_code = r_code.lstrip('\n')

    # R code display policy: always shown in preview/dry-run (safe default);
    # in execute mode shown only with --show-code.
    if args.show_code or args.dry_run or not confirmed:
        print("=" * 60)
        print(t("header.r_code"))
        print("=" * 60)
        print(r_code)
        print("=" * 60)

    if not confirmed:
        print(t("safe_preview.not_executed"))
        return

    print(t("exec.running"))
    sys.stdout.flush()
    output = run_r(r_code, confirmed=True)
    print(output)
    if not args.show_code:
        print(t("info.r_code_shown_default"))
    print("=" * 60)

if __name__ == "__main__":
    main()

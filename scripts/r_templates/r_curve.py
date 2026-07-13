# r_curve.py -- R code templates for ct-samplesize

__all__ = [
    "CURVE_SOLVERS",
    "_CURVE_POWER_SINGLE",
    "_CURVE_POWER_MULTI",
    "_CURVE_N_SINGLE",
    "_CURVE_N_MULTI",
]

CURVE_SOLVERS = {
    # ── t-tests (pwr) ──
    "ttest_ind": {
        "params": "alpha <- {alpha}; delta <- {effect}; alt <- 'two.sided'",
        "power_fn": "pwr.t.test(n=n, d=delta, sig.level=alpha, alternative=alt)$power",
        "n_fn": "ceiling(pwr.t.test(d=delta, power=p, sig.level=alpha, alternative=alt)$n)",
        "n_label": "N per group", "effect_loop": True, "effect_var": "delta",
    },
    "ttest_paired": {
        "params": "alpha <- {alpha}; delta <- {effect}",
        "power_fn": "pwr.t.test(n=n, d=delta, type='paired', sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.t.test(d=delta, power=p, type='paired', sig.level=alpha)$n)",
        "n_label": "N (paired)", "effect_loop": True, "effect_var": "delta",
    },
    "ttest_one": {
        "params": "alpha <- {alpha}; delta <- {effect}; alt <- 'two.sided'",
        "power_fn": "pwr.t.test(n=n, d=delta, type='one.sample', sig.level=alpha, alternative=alt)$power",
        "n_fn": "ceiling(pwr.t.test(d=delta, power=p, type='one.sample', sig.level=alpha, alternative=alt)$n)",
        "n_label": "N", "effect_loop": True, "effect_var": "delta",
    },
    "anova": {
        "params": "alpha <- {alpha}; f <- {effect}; k <- {k_groups}",
        "power_fn": "pwr.anova.test(n=n, f=f, k=k, sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.anova.test(f=f, k=k, power=p, sig.level=alpha)$n)",
        "n_label": "N per group", "effect_loop": True, "effect_var": "f",
    },
    # ── Proportions (pwr) ──
    "proportion_one": {
        "params": "alpha <- {alpha}; p1 <- {p1}; p0 <- {p0}",
        "power_fn": "pwr.p.test(n=n, h=ES.h(p1, p0), sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.p.test(h=ES.h(p1, p0), power=p, sig.level=alpha)$n)",
        "n_label": "N", "effect_loop": False,
    },
    "proportion_two": {
        "params": "alpha <- {alpha}; p1 <- {p1}; p2 <- {p2}",
        "power_fn": "pwr.2p.test(n=n, h=ES.h(p1, p2), sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.2p.test(h=ES.h(p1, p2), power=p, sig.level=alpha)$n)",
        "n_label": "N per group", "effect_loop": False,
    },
    "proportion_paired": {
        "params": "alpha <- {alpha}; p1 <- {p1}; p2 <- {p2}",
        "power_fn": "pwr.2p.test(n=n, h=ES.h(p1, p2), sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.2p.test(h=ES.h(p1, p2), power=p, sig.level=alpha)$n)",
        "n_label": "N (paired)", "effect_loop": False,
    },
    "odds_ratio": {
        "params": "alpha <- {alpha}; p1 <- {p1}; p2 <- {p2}",
        "power_fn": "pwr.2p.test(n=n, h=ES.h(p1, p2), sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.2p.test(h=ES.h(p1, p2), power=p, sig.level=alpha)$n)",
        "n_label": "N per group", "effect_loop": False,
    },
    "risk_ratio": {
        "params": "alpha <- {alpha}; p1 <- {p1}; p2 <- {p2}",
        "power_fn": "pwr.2p.test(n=n, h=ES.h(p1, p2), sig.level=alpha)$power",
        "n_fn": "ceiling(pwr.2p.test(h=ES.h(p1, p2), power=p, sig.level=alpha)$n)",
        "n_label": "N per group", "effect_loop": False,
    },
    # ── ROC ──
    "roc": {
        "params": "alpha <- {alpha}; auc0 <- {auc0}; auc1 <- {auc1}",
        "power_fn": "pnorm(sqrt(2*n) * abs(asin(sqrt(auc1)) - asin(sqrt(auc0))) - qnorm(1-alpha/2))",
        "n_fn": "ceiling(((qnorm(1-alpha/2) + qnorm(p))^2) / (2*(asin(sqrt(auc1)) - asin(sqrt(auc0)))^2))",
        "n_label": "N", "effect_loop": False,
    },
    # ── Poisson ──
    "poisson": {
        "params": "alpha <- {alpha}; lambda1 <- {lambda1}; lambda2 <- {lambda2}; t1 <- {t1}; t2 <- {t2}",
        "power_fn": "pnorm(sqrt(n / (1/(lambda1*t1) + 1/(lambda2*t2))) * abs(log(lambda1/lambda2)) - qnorm(1-alpha/2))",
        "n_fn": "ceiling(((qnorm(1-alpha/2)+qnorm(p))^2 * (1/(lambda1*t1)+1/(lambda2*t2))) / (log(lambda1/lambda2))^2)",
        "n_label": "N per group", "effect_loop": False,
    },
    # ── Non-inferiority / superiority (proportions) ──
    "non_inferiority": {
        "params": "alpha <- {alpha}; p1 <- {p1}; p2 <- {p2}; margin <- {margin}",
        "power_fn": "pnorm(sqrt((n/2) * (margin - abs(p1-p2))^2 / (p1*(1-p1)+p2*(1-p2))) - qnorm(alpha))",
        "n_fn": "ceiling(2*(qnorm(alpha)+qnorm(p))^2 * (p1*(1-p1)+p2*(1-p2)) / (margin-abs(p1-p2))^2)",
        "n_label": "N per group", "effect_loop": False,
    },
    "superiority_margin": {
        "params": "alpha <- {alpha}; p_c <- {p_control_sup}; delta <- {delta_sup}; margin <- {sup_margin}; p_t <- {p_control_sup} - {delta_sup}",
        "power_fn": "pnorm(sqrt((n/2)*(delta-margin)^2/(p_c*(1-p_c)+p_t*(1-p_t))) - qnorm(alpha))",
        "n_fn": "ceiling(2*(qnorm(alpha)+qnorm(p))^2*(p_c*(1-p_c)+p_t*(1-p_t))/(delta-margin)^2)",
        "n_label": "N per group", "effect_loop": False,
    },
    # ── Bioequivalence (PowerTOST) ──
    "be_tost": {
        "params": "alpha <- {alpha}; theta0 <- {theta0}; cv <- {cv}; design <- '{design}'",
        "power_fn": "power.TOST(theta0=theta0, CV=cv, design=design, alpha=alpha, n=n)",
        "n_fn": "sampleN.TOST(theta0=theta0, CV=cv, design=design, alpha=alpha, targetpower=p)$n",
        "n_label": "N per sequence", "effect_loop": False,
    },
    # ── Survival (Schoenfeld) ──
    "survival": {
        "params": "alpha <- {alpha}; hr <- {hazard_ratio}",
        "power_fn": "pnorm(sqrt(n)*abs(log(hr)) - qnorm(1-alpha/2))",
        "n_fn": "ceiling((qnorm(1-alpha/2)+qnorm(p))^2 / (log(hr))^2)",
        "n_label": "Events (d)", "effect_loop": True, "effect_var": "hr",
    },
    "ni_survival": {
        "params": "alpha <- {alpha}; ni_margin <- {ni_margin_surv}",
        "power_fn": "pnorm(sqrt(n)*abs(log(ni_margin)) - qnorm(1-alpha/2))",
        "n_fn": "ceiling((qnorm(1-alpha/2)+qnorm(p))^2 / (log(ni_margin))^2)",
        "n_label": "Events (d)", "effect_loop": True, "effect_var": "ni_margin",
    },
    # ── MAMS ──
    "mams": {
        "params": "alpha <- {alpha}; delta <- {delta_effect}; n_arms <- {n_arms_mams}",
        "power_fn": "pnorm(sqrt(n * delta^2) - qnorm(1 - alpha/(2*n_arms)))",
        "n_fn": "ceiling(((qnorm(1-alpha/(2*n_arms)) + qnorm(p))^2) / delta^2)",
        "n_label": "N per group", "effect_loop": True, "effect_var": "delta",
    },
    # ── Dunnett ──
    "dunnett": {
        "params": "alpha <- {alpha}; delta <- {effect_dunnett}; k <- {n_groups_dunnett}",
        "power_fn": "pnorm(sqrt(n/2)*abs(delta) - qnorm(1-alpha/2))",
        "n_fn": "ceiling(2*(qnorm(1-alpha/2)+qnorm(p))^2 / delta^2)",
        "n_label": "N per group", "effect_loop": True, "effect_var": "delta",
    },
    # ── Group sequential (approximate: fixed-design z-test w/ OF-style alpha) ──
    "group_sequential": {
        "params": "alpha <- {alpha}; delta <- {effect_gs}",
        "power_fn": "pnorm(sqrt(n/2)*abs(delta) - qnorm(1-alpha/2))",
        "n_fn": "ceiling(2*(qnorm(1-alpha/2)+qnorm(p))^2 / delta^2)",
        "n_label": "N per group (fixed approx)", "effect_loop": True, "effect_var": "delta",
    },
    # ── Survival exact (approximate: Schoenfeld) ──
    "survival_exact": {
        "params": "alpha <- {alpha_exact}; hr <- {hr_exact}",
        "power_fn": "pnorm(sqrt(n)*abs(log(hr)) - qnorm(1-alpha/2))",
        "n_fn": "ceiling((qnorm(1-alpha/2)+qnorm(p))^2 / (log(hr))^2)",
        "n_label": "Events (d) (Schoenfeld approx)", "effect_loop": True, "effect_var": "hr",
    },
    # ── Equivalence (TOST, approximate) ──
    "equivalence": {
        "params": "alpha <- {alpha}; delta <- {effect}; margin <- {margin}",
        "power_fn": "pnorm(sqrt(n/2)*(margin - abs(delta)) - qnorm(1-alpha/2))",
        "n_fn": "ceiling(2*(qnorm(1-alpha/2)+qnorm(p))^2 / (margin-abs(delta))^2)",
        "n_label": "N per group", "effect_loop": True, "effect_var": "delta",
    },
    # ── Vaccine efficacy (approx two-rate) ──
    "vaccine_efficacy": {
        "params": "alpha <- {alpha}; ve_c <- {ve_control}; ve_t <- {ve_treatment}",
        "power_fn": "pnorm(sqrt(n/(1/(1-ve_t)+1/(1-ve_c))) * abs(log((1-ve_t)/(1-ve_c))) - qnorm(1-alpha/2))",
        "n_fn": "ceiling(((qnorm(1-alpha/2)+qnorm(p))^2 * (1/(1-ve_t)+1/(1-ve_c))) / (log((1-ve_t)/(1-ve_c)))^2)",
        "n_label": "N per group", "effect_loop": False,
    },
}

_CURVE_POWER_SINGLE = """\
__PARAMS__
power_given_n <- function(n) { __POWER_FN__ }
n_seq <- __SEQ__
pw <- sapply(n_seq, power_given_n)
df <- data.frame(n = n_seq, power = pw)
library(ggplot2)
p <- ggplot(df, aes(x = n, y = power)) +
  geom_line(color = '#2c7fb8', size = 1.3) +
  geom_point(color = '#2c7fb8', size = 2) +
  geom_hline(yintercept = __TARGET__, linetype = 'dashed', color = 'red') +
  labs(title = 'Power vs Sample Size (__TEST__)', x = '__XLABEL__', y = 'Power') +
  ylim(0, 1) + theme_minimal()
ggsave('__OUT__', p, width = 7, height = 5, dpi = 120)
print(df)
cat('PNG saved to __OUT__', '\\n')
"""

_CURVE_POWER_MULTI = """\
__PARAMS__
effects <- __EFFECTS__
__EFFECT_VAR__ <- effects[1]
power_given_n <- function(n) { __POWER_FN__ }
res <- data.frame()
for (e in effects) {
  __EFFECT_VAR__ <- e
  pw <- sapply(__SEQ__, power_given_n)
  res <- rbind(res, data.frame(n = __SEQ__, power = pw, effect = rep(e, length(__SEQ__))))
}
library(ggplot2)
p <- ggplot(res, aes(x = n, y = power, color = factor(effect))) +
  geom_line(size = 1.1) + geom_point(size = 1.5) +
  geom_hline(yintercept = __TARGET__, linetype = 'dashed', color = 'red') +
  labs(title = 'Power vs Sample Size (__TEST__, by effect)', x = '__XLABEL__', y = 'Power', color = 'Effect') +
  ylim(0, 1) + theme_minimal()
ggsave('__OUT__', p, width = 7, height = 5, dpi = 120)
print(res)
cat('PNG saved to __OUT__', '\\n')
"""

_CURVE_N_SINGLE = """\
__PARAMS__
n_given_power <- function(p) { __NFN__ }
pw_seq <- __SEQ__
ns <- sapply(pw_seq, n_given_power)
df <- data.frame(power = pw_seq, n = ns)
library(ggplot2)
p <- ggplot(df, aes(x = power, y = n)) +
  geom_line(color = '#d95f0e', size = 1.3) +
  geom_point(color = '#d95f0e', size = 2) +
  geom_vline(xintercept = __TARGET__, linetype = 'dashed', color = 'red') +
  labs(title = 'Sample Size vs Power (__TEST__)', x = 'Power (target)', y = '__YLABEL__') +
  theme_minimal()
ggsave('__OUT__', p, width = 7, height = 5, dpi = 120)
print(df)
cat('PNG saved to __OUT__', '\\n')
"""

_CURVE_N_MULTI = """\
__PARAMS__
effects <- __EFFECTS__
__EFFECT_VAR__ <- effects[1]
n_given_power <- function(p) { __NFN__ }
res <- data.frame()
for (e in effects) {
  __EFFECT_VAR__ <- e
  ns <- sapply(__SEQ__, n_given_power)
  res <- rbind(res, data.frame(power = __SEQ__, n = ns, effect = rep(e, length(__SEQ__))))
}
library(ggplot2)
p <- ggplot(res, aes(x = power, y = n, color = factor(effect))) +
  geom_line(size = 1.1) + geom_point(size = 1.5) +
  geom_vline(xintercept = __TARGET__, linetype = 'dashed', color = 'red') +
  labs(title = 'Sample Size vs Power (__TEST__, by effect)', x = 'Power (target)', y = '__YLABEL__', color = 'Effect') +
  theme_minimal()
ggsave('__OUT__', p, width = 7, height = 5, dpi = 120)
print(res)
cat('PNG saved to __OUT__', '\\n')
"""


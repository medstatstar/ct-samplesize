# r_pass_ext.py -- PASS-coverage extension templates (v5.9 / v5.10)
# 与 src/r_engine/samplesize_functions.R 同源实现（coze 引擎单一真相源）。
# 覆盖：相关 / 方差 / CI 精度 / 回归 / Meta 规划 / 整群扩展 / 率扩展。
# presize 优先（CI 类精确法），缺失时以 base-R 正态近似兜底；
# CI 类为「精度目标 -> n」模型（hw=NULL -> 求 n；n!=NULL -> 求达成精度 hw）。
#
# 全部算法以真实 R 函数暴露（双向：power=NULL -> n；n=NULL -> power），
# 使 Python 层只需注入定义并调用，与既有 r_templates 约定一致。

R_PASS_EXT = r"""
# ============================================================================
# PASS-coverage extension (Tier 1 / Tier 2) -- 单一真相源 = src/r_engine
# ============================================================================
.ss_pre_ok <- function() requireNamespace("presize", quietly = TRUE)
.ss_zcrit <- function(alpha, side = "two") if (side == "one") qnorm(1 - alpha) else qnorm(1 - alpha / 2)

# -- G1 correlation: H0: rho=0 (Fisher-z exact, pwr) --
ss_correlation <- function(r, alpha, power = NULL, n = NULL, side = "two") {
  suppressMessages(library(pwr))
  alt <- if (side == "one") "greater" else "two.sided"
  if (!is.null(power)) ceiling(pwr.r.test(n = NULL, r = r, sig.level = alpha, power = power, alternative = alt)$n)
  else round(pwr.r.test(n = n, r = r, sig.level = alpha, alternative = alt)$power, 4)
}

# -- G2 variance_one: sigma^2 = sigma0^2 vs sigma1^2 (chi-square exact) --
.pow_var1 <- function(n, s0, s1, alpha, side) {
  ratio <- (s1 / s0)^2; df <- n - 1
  if (side == "one") pchisq(qchisq(1 - alpha, df) / ratio, df, lower.tail = FALSE)
  else pchisq(qchisq(alpha / 2, df) / ratio, df) + pchisq(qchisq(1 - alpha / 2, df) / ratio, df, lower.tail = FALSE)
}
ss_variance_one <- function(s0, s1, alpha, power = NULL, n = NULL, side = "two") {
  if (!is.null(power)) {
    f <- function(nn) .pow_var1(nn, s0, s1, alpha, side) - power
    hi <- 2; while (f(hi) < 0 && hi < 1e7) hi <- hi * 2
    ceiling(uniroot(f, c(2, hi), extendInt = "upX")$root)
  } else round(.pow_var1(n, s0, s1, alpha, side), 4)
}

# -- G3 variance_two: sigma1^2/sigma2^2 = 1 vs R1 (F exact) --
.pow_var2 <- function(n, R1, alpha, side) {
  df <- n - 1
  if (side == "one") 1 - pf(qf(1 - alpha, df, df) / R1, df, df)
  else 1 - pf(qf(1 - alpha / 2, df, df) / R1, df, df) + pf(qf(alpha / 2, df, df) / R1, df, df)
}
ss_variance_two <- function(R1, alpha, power = NULL, n = NULL, side = "two") {
  if (!is.null(power)) {
    f <- function(nn) .pow_var2(nn, R1, alpha, side) - power
    hi <- 2; while (f(hi) < 0 && hi < 1e7) hi <- hi * 2
    ceiling(uniroot(f, c(2, hi), extendInt = "upX")$root)
  } else round(.pow_var2(n, R1, alpha, side), 4)
}

# -- G4 cv_one: relative-error precision of an estimated CV (McKay/Vangel) --
ss_cv_one <- function(cv, rel = NULL, alpha = 0.05, n = NULL) {
  z <- .ss_zcrit(alpha)
  if (!is.null(n)) round(z * sqrt(1 + cv^2 / 2) / sqrt(n), 4)
  else ceiling((z * sqrt(1 + cv^2 / 2) / rel)^2)
}

# -- G5 ci_mean: mean CI half-width (normal exact) --
ss_ci_mean <- function(sd, hw = NULL, alpha = 0.05, n = NULL) {
  z <- .ss_zcrit(alpha)
  if (!is.null(n)) round(z * sd / sqrt(n), 4) else ceiling((z * sd / hw)^2)
}

# -- G6 ci_prop: proportion CI (presize wilson, normal fallback) --
ss_ci_prop <- function(p, hw = NULL, alpha = 0.05, n = NULL) {
  z <- .ss_zcrit(alpha)
  if (!is.null(n)) {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_prop(p = p, n = n, conf.level = 1 - alpha, method = "wilson")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(round(out$conf.width, 4))
    round(z * sqrt(p * (1 - p) / n), 4)
  } else {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_prop(p = p, conf.width = hw, conf.level = 1 - alpha, method = "wilson")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(ceiling(out$n))
    ceiling((z^2 * p * (1 - p)) / hw^2)
  }
}

# -- G7 ci_or: CI of an odds ratio (presize indip_smooth, normal fallback) --
ss_ci_or <- function(p0, or, hw = NULL, alpha = 0.05, n = NULL) {
  z <- .ss_zcrit(alpha); p1 <- or * p0 / ((1 - p0) + or * p0)
  if (!is.null(n)) {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_or(p1 = p0, p2 = p1, r = 1, n1 = n, conf.level = 1 - alpha, method = "indip_smooth")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(round(out$conf.width, 4))
    round(z * sqrt(1 / (n * p0) + 1 / (n * (1 - p0)) + 1 / (n * p1) + 1 / (n * (1 - p1))), 4)
  } else {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_or(p1 = p0, p2 = p1, r = 1, conf.width = hw, conf.level = 1 - alpha, method = "indip_smooth")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(ceiling(out$n1))
    ceiling((z^2 * (1 / p0 + 1 / (1 - p0) + 1 / p1 + 1 / (1 - p1))) / hw^2)
  }
}

# -- G8 ci_rr: CI of a risk ratio (presize koopman, normal fallback) --
ss_ci_rr <- function(p0, rr, hw = NULL, alpha = 0.05, n = NULL) {
  z <- .ss_zcrit(alpha); p1 <- rr * p0
  if (!is.null(n)) {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_riskratio(p1 = p0, p2 = p1, r = 1, n1 = n, conf.level = 1 - alpha, method = "koopman")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(round(out$conf.width, 4))
    round(z * sqrt(1 / (n * p0) + 1 / (n * p1)), 4)
  } else {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_riskratio(p1 = p0, p2 = p1, r = 1, conf.width = hw, conf.level = 1 - alpha, method = "koopman")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(ceiling(out$n1))
    ceiling((z^2 * (1 / p0 + 1 / p1)) / hw^2)
  }
}

# -- G9 ci_cor: CI of a correlation (presize pearson, Fisher-z fallback) --
ss_ci_cor <- function(r, hw = NULL, alpha = 0.05, n = NULL) {
  z <- .ss_zcrit(alpha)
  if (!is.null(n)) {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_cor(r = r, n = n, conf.level = 1 - alpha, method = "pearson")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(round(out$conf.width, 4))
    round(z / sqrt(n - 3), 4)
  } else {
    out <- if (.ss_pre_ok()) tryCatch(suppressWarnings(presize::prec_cor(r = r, conf.width = hw, conf.level = 1 - alpha, method = "pearson")), error = function(e) NULL) else NULL
    if (!is.null(out)) return(ceiling(out$n))
    ceiling((z / hw)^2 + 3)
  }
}

# -- G10 ci_icc: CI of an ICC (presize only; first arg is rho) --
ss_ci_icc <- function(icc, k = 2, hw = NULL, alpha = 0.05, n = NULL) {
  if (!.ss_pre_ok()) return(NA_real_)
  out <- tryCatch(suppressWarnings(presize::prec_icc(rho = icc, k = k, n = n,
         conf.width = if (is.null(n)) hw else NULL, conf.level = 1 - alpha)), error = function(e) NULL)
  if (is.null(out)) return(NA_real_)
  if (!is.null(n)) round(out$conf.width, 4) else ceiling(out$n)
}

# -- G11 regression_linear: multiple-regression R^2 test (pwr.f2) --
ss_regression_linear <- function(u, f2, alpha, power = NULL, n = NULL) {
  suppressMessages(library(pwr))
  if (!is.null(power)) {
    r <- pwr.f2.test(u = u, f2 = f2, sig.level = alpha, power = power)
    ceiling(r$v + u + 1)
  } else {
    r <- pwr.f2.test(u = u, v = n - u - 1, f2 = f2, sig.level = alpha)
    round(r$power, 4)
  }
}

# -- G12 meta_planning: prospective power / #studies (Hedges & Pigott 2001) --
.meta_vw <- function(effect_type, effect, N, p0 = NULL, m = NULL, icc = NULL, cov = NULL) {
  if (effect_type %in% c("smd")) return((2 + effect^2 / 4) / N)
  if (effect_type == "paired") return((2 + effect^2 / 2) / N)
  if (effect_type == "or") {
    p1 <- effect * p0 / ((1 - p0) + effect * p0)
    return(1 / (N * p0) + 1 / (N * (1 - p0)) + 1 / (N * p1) + 1 / (N * (1 - p1)))
  }
  if (effect_type == "rr") {
    p1 <- effect * p0
    return((1 - p0) / (N * p0) + (1 - p1) / (N * p1))
  }
  if (effect_type == "cor") return(1 / (N - 3))
  if (effect_type == "cluster") {
    cov_ <- if (is.null(cov)) 0 else cov
    DE <- 1 + ((cov_^2 + 1) * m - 1) * icc
    return(((2 + effect^2 / 4) / N) * DE)
  }
  stop("unknown meta effect_type")
}
.pow_meta <- function(K, core_eff, vw, R, alpha, core0, side) {
  se <- sqrt(vw * (1 + R) / K); lam <- (core_eff - core0) / se; zc <- .ss_zcrit(alpha, side)
  if (side == "one") pnorm(zc, mean = lam, lower.tail = FALSE)
  else 1 - pnorm(zc - lam) + pnorm(-zc - lam)
}
ss_meta_planning <- function(effect_type, effect, n_per_study, i2 = NULL, R = NULL, K = NULL,
                             alpha = 0.05, power = NULL, effect0 = NULL, side = "two",
                             p0 = NULL, m = NULL, icc = NULL, cov = NULL) {
  vw <- .meta_vw(effect_type, effect, n_per_study, p0, m, icc, cov)
  tr <- function(x) switch(effect_type, or = log(x), rr = log(x), cor = atanh(x), x)
  core_eff <- tr(effect)
  if (is.null(effect0)) effect0 <- if (effect_type %in% c("or", "rr")) 1 else 0
  core0 <- tr(effect0)
  if (is.null(R)) R <- if (is.null(i2)) 0 else i2 / (1 - i2)
  if (!is.null(power)) {
    k <- 1
    while (k < 1e6 && .pow_meta(k, core_eff, vw, R, alpha, core0, side) < power) k <- k + 1
    k
  } else round(.pow_meta(K, core_eff, vw, R, alpha, core0, side), 4)
}

# -- G13 regression_logistic: Hsieh 1998 (continuous) / 1989 (binary) --
ss_regression_logistic <- function(p0, or, x_type = "continuous", q = 0.5, r2 = 0,
                                   alpha = 0.05, power = NULL, n = NULL, side = "two") {
  zc <- .ss_zcrit(alpha, side)
  if (identical(x_type, "binary")) {
    p1 <- or * p0 / (1 - p0 + or * p0)
    pE <- (1 - q) * p0 + q * p1
    a <- sqrt(pE * (1 - pE) * (1 / (1 - q) + 1 / q))
    b <- sqrt(p0 * (1 - p0) / (1 - q) + p1 * (1 - p1) / q)
    if (!is.null(power)) {
      n0 <- (zc * a + qnorm(power) * b)^2 / (p1 - p0)^2
      return(ceiling(n0 / (1 - r2)))
    }
    zb <- (sqrt(n * (1 - r2)) * abs(p1 - p0) - zc * a) / b
    return(round(pnorm(zb), 4))
  }
  if (!is.null(power)) {
    n0 <- (zc + qnorm(power))^2 / (p0 * (1 - p0) * log(or)^2)
    return(ceiling(n0 / (1 - r2)))
  }
  zb <- sqrt(n * (1 - r2) * p0 * (1 - p0) * log(or)^2) - zc
  round(pnorm(zb), 4)
}

# -- G14 regression_poisson: Signorini 1991 (normal X) --
ss_regression_poisson <- function(b0, rr, mu_x = 0, sd_x = 1, exposure = 1, phi = 1, r2 = 0,
                                  alpha = 0.05, power = NULL, n = NULL, side = "two") {
  zc <- .ss_zcrit(alpha, side)
  b1 <- log(rr)
  V0 <- 1 / sd_x^2
  V1 <- (1 / sd_x^2) * exp(-(b1 * mu_x + b1^2 * sd_x^2 / 2))
  D <- exposure * exp(b0) * b1^2 * (1 - r2)
  if (!is.null(power)) {
    return(ceiling(phi * (zc * sqrt(V0) + qnorm(power) * sqrt(V1))^2 / D))
  }
  zb <- (sqrt(n * D / phi) - zc * sqrt(V0)) / sqrt(V1)
  round(pnorm(zb), 4)
}

# -- G16 cluster_ext: generalized design effect with unequal-cluster CV --
ss_cluster_ext <- function(n_indiv = NULL, m, icc, cv = 0, ratio = 1,
                           effect = NULL, alpha = 0.05, power = NULL, side = "two",
                           n_clusters = NULL) {
  deff <- 1 + ((1 + cv^2) * m - 1) * icc
  if (!is.null(n_clusters)) {
    return(list(n_indiv_eff = round(n_clusters * m / deff, 1),
                deff = round(deff, 4), n_clusters = n_clusters))
  }
  if (is.null(n_indiv)) {
    zc <- .ss_zcrit(alpha, side); zb <- qnorm(power)
    n_indiv <- 2 * (zc + zb)^2 / effect^2
  }
  n_adj1 <- ceiling(n_indiv * deff); cl1 <- ceiling(n_adj1 / m)
  n_adj2 <- ceiling(n_indiv * ratio * deff); cl2 <- ceiling(n_adj2 / m)
  list(n_indiv = round(n_indiv, 2), deff = round(deff, 4),
       n_adj = n_adj1, n_clusters = cl1,
       n_adj_total = n_adj1 + n_adj2, total_clusters = cl1 + cl2)
}

# -- G17 rates_ext: rate / rate-ratio with over-dispersion phi and CI precision --
ss_rates_ext <- function(rate_mode = "ratio", lambda1, lambda2 = NULL, t1 = 1, t2 = 1,
                         phi = 1, ratio = 1, alpha = 0.05, power = NULL, n = NULL,
                         hw = NULL, side = "two") {
  zc <- .ss_zcrit(alpha, side)
  if (identical(rate_mode, "single_ci")) {
    if (!.ss_pre_ok()) return(NA_real_)
    out <- tryCatch(suppressWarnings(presize::prec_rate(
             r = lambda1, x = if (!is.null(n)) n else NULL,
             conf.width = if (is.null(n)) hw else NULL, conf.level = 1 - alpha)),
           error = function(e) NULL)
    if (is.null(out)) return(NA_real_)
    return(if (!is.null(n)) round(out$conf.width, 4) else ceiling(out$x))
  }
  if (identical(rate_mode, "ratio_ci")) {
    if (!.ss_pre_ok()) return(NA_real_)
    out <- tryCatch(suppressWarnings(presize::prec_rateratio(
             n1 = if (!is.null(n)) n else NULL, rate1 = lambda1, rate2 = lambda2,
             prec.level = if (is.null(n)) hw else NULL, r = ratio, conf.level = 1 - alpha)),
           error = function(e) NULL)
    if (is.null(out)) return(NA_real_)
    return(if (!is.null(n)) round(out$prec.level, 4) else ceiling(out$n1))
  }
  RR <- lambda1 / lambda2
  unequal <- !is.null(ratio) && !is.na(ratio) && ratio > 0 && ratio != 1
  if (!is.null(power)) {
    zb <- qnorm(power)
    if (unequal) {
      n1 <- ceiling(phi * (zc + zb)^2 / log(RR)^2 * (1/(lambda1*t1) + 1/(ratio*lambda2*t2)))
      n2 <- ceiling(n1 * ratio)
    } else {
      n1 <- ceiling(phi * (zc + zb)^2 * (1/(lambda1*t1) + 1/(lambda2*t2)) / log(RR)^2)
      n2 <- n1
    }
    return(list(n1 = n1, n2 = n2, total = n1 + n2))
  }
  n1 <- if (unequal) n / (1 + ratio) else n / 2
  n2 <- if (unequal) n * ratio / (1 + ratio) else n1
  S <- 1/(lambda1*t1) + 1/(ratio*lambda2*t2)
  zb <- abs(log(RR)) * sqrt(n1/(phi * S)) - zc
  round(pnorm(zb), 4)
}
"""

__all__ = ["R_PASS_EXT"]

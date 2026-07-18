# r_adaptive_simulate.py -- R Monte-Carlo template for adaptive / group-sequential
# trial designs. Pure base-R implementation (no extra packages) ported from the
# Python engine in scripts/adaptive_simulator.py so the generated R code is fully
# self-contained and runnable anywhere R is installed.
#
# Parameters are injected with __SENTINEL__ tokens (no str.format brace escaping
# needed); every user string that reaches the code is validated upstream in
# samplesize_power.py before substitution, so no RCE surface exists.

R_ADAPTIVE_SIMULATE = r'''# ============================================================
# Adaptive Trial Monte-Carlo Simulator (pure R, base packages only)
# Ported from ct-samplesize scripts/adaptive_simulator.py.
# Reproduces 6 capabilities: design simulation, sample-size
# re-estimation (promising zone + Cui-Hung-Wang statistic),
# early stopping (efficacy/futility via alpha-spending), Type I
# error control, multi-arm drop-the-loser, power optimization.
# ============================================================

cumulative_spend <- function(t, total, func, rho = 3.0) {
  t <- max(min(t, 1.0), 1e-9)
  if (func == "obrien_fleming") {
    z <- qnorm(1 - total / 2)
    return(2 * (1 - pnorm(z / sqrt(t))))
  } else if (func == "pocock") {
    return(total * log(1 + (exp(1) - 1) * t))
  } else if (func == "power_family") {
    return(total * t ^ rho)
  }
  stop("unknown spending function: ", func)
}

incremental <- function(times, total, func, rho) {
  cum <- sapply(times, function(tt) cumulative_spend(tt, total, func, rho))
  inc <- cum - c(0, cum[-length(cum)])
  pmax(inc, 1e-12)
}

efficacy_boundaries <- function(times, alpha, func = "obrien_fleming", rho = 3.0, ngrid = 1000) {
  times <- as.numeric(times)
  K <- length(times)
  inc <- incremental(times, alpha, func, rho)
  xmax <- 6.0 * sqrt(times[K])
  x <- seq(-xmax, xmax, length.out = ngrid)
  dx <- x[2] - x[1]
  bounds <- numeric(K)
  v1 <- times[1]
  b1 <- sqrt(v1) * qnorm(1 - inc[1])
  bounds[1] <- b1 / sqrt(v1)
  f <- dnorm(x, 0, sqrt(v1))
  f[x > b1] <- 0
  for (k in 2:K) {
    vk <- times[k] - times[k - 1]
    sd_k <- sqrt(vk)
    kern <- outer(x, x, function(a, b) dnorm(a - b, 0, sd_k))
    g <- as.vector((kern %*% f) * dx)
    lo <- -xmax; hi <- xmax
    for (it in 1:60) {
      mid <- 0.5 * (lo + hi)
      if (sum(g[x > mid]) * dx > inc[k]) lo <- mid else hi <- mid
    }
    bk <- 0.5 * (lo + hi)
    bounds[k] <- bk / sqrt(times[k])
    f <- g
    f[x > bk] <- 0
  }
  bounds
}

futility_boundaries <- function(times, beta, drift, func = "power_family", rho = 2.0, ngrid = 1000) {
  times <- as.numeric(times)
  K <- length(times)
  inc <- incremental(times, beta, func, rho)
  xmax <- 6.0 * sqrt(times[K])
  x <- seq(-xmax, xmax, length.out = ngrid)
  dx <- x[2] - x[1]
  bounds <- numeric(K)
  v1 <- times[1]
  a1 <- drift * v1 + sqrt(v1) * qnorm(inc[1])
  bounds[1] <- a1 / sqrt(times[1])
  f <- dnorm(x, drift * v1, sqrt(v1))
  f[x < a1] <- 0
  for (k in 2:K) {
    vk <- times[k] - times[k - 1]
    sd_k <- sqrt(vk)
    kern <- outer(x, x, function(a, b) dnorm(a - b, drift * vk, sd_k))
    g <- as.vector((kern %*% f) * dx)
    lo <- -xmax; hi <- xmax
    for (it in 1:60) {
      mid <- 0.5 * (lo + hi)
      if (sum(g[x < mid]) * dx < inc[k]) lo <- mid else hi <- mid
    }
    ak <- 0.5 * (lo + hi)
    bounds[k] <- ak / sqrt(times[k])
    f <- g
    f[x < ak] <- 0
  }
  bounds
}

simulate_group_sequential <- function(effect_size, n_per_arm, interim_looks = 2,
                                       alpha = 0.025, spending = "obrien_fleming",
                                       rho = 3.0, futility = FALSE, beta = 0.2,
                                       n_sim = 10000, seed = NULL) {
  if (!is.null(seed)) set.seed(seed)
  K <- interim_looks
  times <- (1:K) / K
  eff_b <- efficacy_boundaries(times, alpha, spending, rho)
  theta <- effect_size * sqrt(n_per_arm / 2)
  fut_b <- if (futility) futility_boundaries(times, beta, theta, "power_family", 2.0) else NULL
  dt <- diff(c(0, times))
  run_one <- function(drift) {
    Bcur <- rep(0, n_sim)
    stopped <- rep(FALSE, n_sim)
    reject <- rep(FALSE, n_sim)
    stop_look <- rep(K, n_sim)
    stop_kind <- rep(0L, n_sim)
    for (k in 1:K) {
      Bcur <- Bcur + rnorm(n_sim, drift * dt[k], sqrt(dt[k]))
      Zk <- Bcur / sqrt(times[k])
      active <- !stopped
      eff <- active & (Zk > eff_b[k])
      reject[eff] <- TRUE; stopped[eff] <- TRUE; stop_look[eff] <- k; stop_kind[eff] <- 1L
      if (futility && k < K) {
        fut <- active & !eff & (Zk < fut_b[k])
        stopped[fut] <- TRUE; stop_look[fut] <- k; stop_kind[fut] <- 2L
      }
    }
    list(reject = reject, stop_look = stop_look, stop_kind = stop_kind)
  }
  r1 <- run_one(theta)
  r0 <- run_one(0)
  frac <- times[r1$stop_look]
  exp_n_per_arm <- mean(frac * n_per_arm)
  early <- r1$stop_look < K
  list(
    design = "group_sequential",
    power = mean(r1$reject),
    type_i_error = mean(r0$reject),
    expected_sample_size = round(exp_n_per_arm * 2, 2),
    expected_sample_size_per_arm = round(exp_n_per_arm, 2),
    max_sample_size = as.integer(n_per_arm * 2),
    early_stop_rate = list(
      efficacy = mean(early & r1$stop_kind == 1L),
      futility = mean(early & r1$stop_kind == 2L)),
    design_config = list(
      effect_size = effect_size, n_per_arm = n_per_arm, interim_looks = K,
      information_times = round(times, 4), alpha = alpha, spending_function = spending,
      rho = rho, futility = isTRUE(futility), beta = if (futility) beta else NULL,
      efficacy_boundaries_Z = round(eff_b, 4),
      futility_boundaries_Z = if (is.null(fut_b)) NULL else round(fut_b, 4),
      n_simulations = n_sim)
  )
}

simulate_adaptive_reestimate <- function(effect_size, n_per_arm, alpha = 0.025,
                                          interim_fraction = 0.5, cp_min = 0.365,
                                          cp_max = 0.9, target_cp = 0.9,
                                          max_inflation = 2.0, n_sim = 10000,
                                          seed = NULL, reestimate_method = "promising_zone") {
  if (reestimate_method != "promising_zone") stop("only 'promising_zone' is supported")
  if (!is.null(seed)) set.seed(seed)
  z_alpha <- qnorm(1 - alpha)
  n1 <- max(round(interim_fraction * n_per_arm), 2)
  n2_plan <- n_per_arm - n1
  n2_max <- round(n2_plan * max_inflation)
  w1 <- sqrt(n1 / n_per_arm)
  w2 <- sqrt(1 - w1 * w1)
  run_one <- function(true_d) {
    d1 <- rnorm(n_sim, true_d, sqrt(2 / n1))
    z1 <- d1 / sqrt(2 / n1)
    theta_hat <- pmax(d1, 0)
    info2_plan <- n2_plan / 2
    cp <- 1 - pnorm((z_alpha - (w1 * z1 + w2 * (theta_hat * sqrt(info2_plan)))) / w2)
    cp <- pmin(pmax(cp, 0), 1)
    promising <- (cp >= cp_min) & (cp <= cp_max)
    need <- ((qnorm(target_cp) + z_alpha) / pmax(theta_hat, 1e-6)) ^ 2 * 2
    n2_new <- ifelse(promising, pmin(pmax(round(need), n2_plan), n2_max), n2_plan)
    n2_new <- pmax(n2_new, 1)
    d2 <- rnorm(n_sim, true_d, sqrt(2 / n2_new))
    z2 <- d2 / sqrt(2 / n2_new)
    zw <- w1 * z1 + w2 * z2
    reject <- zw > z_alpha
    total_n <- n1 + n2_new
    list(reject = reject, total_n = total_n, promising = promising)
  }
  r1 <- run_one(effect_size)
  r0 <- run_one(0)
  list(
    design = "adaptive_reestimate",
    power = mean(r1$reject),
    type_i_error = mean(r0$reject),
    expected_sample_size = round(mean(r1$total_n) * 2, 2),
    expected_sample_size_per_arm = round(mean(r1$total_n), 2),
    max_sample_size = as.integer((n1 + n2_max) * 2),
    prob_sample_size_increase = mean(r1$promising),
    design_config = list(
      effect_size = effect_size, planned_n_per_arm = n_per_arm, n1_per_arm = n1,
      n2_planned_per_arm = n2_plan, n2_max_per_arm = n2_max, interim_fraction = interim_fraction,
      alpha = alpha, promising_zone = c(cp_min, cp_max), target_cp = target_cp,
      max_inflation = max_inflation, chw_weights = round(c(w1, w2), 4),
      reestimate_method = reestimate_method, n_simulations = n_sim)
  )
}

simulate_drop_the_loser <- function(effect_sizes, n_per_arm, n_arms = NULL, alpha = 0.025,
                                     selection_fraction = 0.5, n_sim = 10000, seed = NULL,
                                     correction = "dunnett") {
  if (!is.null(seed)) set.seed(seed)
  if (length(effect_sizes) == 1 && !is.null(n_arms)) {
    effects <- rep(as.numeric(effect_sizes), n_arms)
  } else {
    effects <- as.numeric(effect_sizes)
  }
  K <- length(effects)
  if (correction == "bonferroni") z_final <- qnorm(1 - alpha / K)
  else z_final <- qnorm((1 - alpha) ^ (1 / K))
  f1 <- selection_fraction
  n1 <- max(round(f1 * n_per_arm), 2)
  info1 <- n1 / 2
  info_full <- n_per_arm / 2
  run_one <- function(effs) {
    Z1 <- matrix(rnorm(n_sim * K, effs * sqrt(info1), 1), n_sim, K)
    winner <- max.col(Z1)
    win_eff <- effs[winner]
    win_z1 <- Z1[cbind(1:n_sim, winner)]
    extra_info <- info_full - info1
    z_extra <- rnorm(n_sim, win_eff * sqrt(max(extra_info, 0)), 1)
    zf <- (win_z1 * sqrt(info1) + z_extra * sqrt(max(extra_info, 0))) / sqrt(info_full)
    reject <- zf > z_final
    n_used <- (K + 1) * n1 + 2 * (n_per_arm - n1)
    list(reject = reject, winner = winner, n_used = n_used)
  }
  r1 <- run_one(effects)
  r0 <- run_one(rep(0, K))
  best_arm <- which.max(effects)
  list(
    design = "drop_the_loser",
    power_any = mean(r1$reject),
    power_correct_selection = mean((r1$winner == best_arm) & r1$reject),
    prob_correct_selection = mean(r1$winner == best_arm),
    type_i_error = mean(r0$reject),
    expected_sample_size = as.integer(r1$n_used),
    max_sample_size = as.integer((K + 1) * n_per_arm),
    design_config = list(
      effect_sizes = round(effects, 4), n_arms = K, n_per_arm = n_per_arm, alpha = alpha,
      selection_fraction = f1, correction = correction, adjusted_final_Z = round(z_final, 4),
      n_simulations = n_sim)
  )
}

optimize_power <- function(effect_size, target_power = 0.9, alpha = 0.025, interim_looks = 2,
                            spending = "obrien_fleming", rho = 3.0, futility = FALSE,
                            n_min = 10, n_max = 1000, step = NULL, n_sim = 4000, seed = NULL) {
  if (is.null(step)) step <- max(as.integer((n_max - n_min) / 40), 1)
  trace <- list()
  chosen <- NULL
  ns <- seq(n_min, n_max, by = step)
  for (n in ns) {
    res <- simulate_group_sequential(effect_size, n, interim_looks = interim_looks,
      alpha = alpha, spending = spending, rho = rho, futility = futility, n_sim = n_sim, seed = seed)
    trace <- c(trace, list(list(n_per_arm = n, power = res$power,
                                expected_sample_size = res$expected_sample_size)))
    if (is.null(chosen) && res$power >= target_power) { chosen <- res; break }
  }
  list(
    design = "power_optimization",
    target_power = target_power,
    recommended = if (is.null(chosen)) NULL else list(
      n_per_arm = chosen$design_config$n_per_arm,
      power = chosen$power,
      expected_sample_size = chosen$expected_sample_size,
      type_i_error = chosen$type_i_error),
    scan = trace,
    design_config = list(
      effect_size = effect_size, alpha = alpha, interim_looks = interim_looks,
      spending_function = spending, rho = rho, futility = isTRUE(futility),
      n_range = c(n_min, n_max), step = step, n_simulations = n_sim)
  )
}

# ---- minimal JSON serializer (no external package needed) ----
fmt_num <- function(v) {
  if (v == round(v) && abs(v) < 1e15) format(as.integer(v)) else format(v, digits = 10)
}
to_json <- function(x, indent = "") {
  if (is.null(x)) return("null")
  if (is.logical(x)) return(if (x[1]) "true" else "false")
  if (is.numeric(x)) {
    if (length(x) == 1) return(fmt_num(x))
    return(paste0("[", paste(sapply(x, fmt_num), collapse = ","), "]"))
  }
  if (is.character(x)) return(paste0('"', x[1], '"'))
  if (is.list(x)) {
    if (length(x) == 0) return("{}")
    parts <- character(length(x))
    names_x <- names(x)
    for (i in seq_along(x)) {
      nm <- if (!is.null(names_x) && nzchar(names_x[i])) paste0('"', names_x[i], '":') else ""
      parts[i] <- paste0(nm, to_json(x[[i]], paste0(indent, "  ")))
    }
    return(paste0("{\n  ", indent, paste(parts, collapse = paste0(",\n  ", indent)), "\n", indent, "}"))
  }
  return("null")
}

cat_report <- function(RES) {
  dc <- RES$design_config
  cat("============================================================\n")
  cat("ADAPTIVE TRIAL SIMULATION  (Monte-Carlo, R)\n")
  cat("============================================================\n")
  cat("design            :", RES$design, "\n")
  if (!is.null(RES$power)) {
    cat("power             :", round(RES$power, 4), "\n")
  } else if (!is.null(RES$power_any)) {
    cat("power (any arm)   :", round(RES$power_any, 4), "\n")
  }
  if (!is.null(RES$type_i_error)) {
    cat("type I error      :", round(RES$type_i_error, 4), "\n")
  }
  if (!is.null(RES$expected_sample_size)) cat("expected N (total):", RES$expected_sample_size, "\n")
  if (!is.null(RES$max_sample_size)) cat("max N (total)     :", RES$max_sample_size, "\n")
  if (RES$design == "group_sequential") {
    es <- RES$early_stop_rate
    cat("early stop (eff)  :", round(es$efficacy, 4), "\n")
    cat("early stop (fut)  :", round(es$futility, 4), "\n")
    cat("efficacy Z bounds :", paste(round(dc$efficacy_boundaries_Z, 4), collapse = ", "), "\n")
    if (!is.null(dc$futility_boundaries_Z))
      cat("futility Z bounds :", paste(round(dc$futility_boundaries_Z, 4), collapse = ", "), "\n")
  } else if (RES$design == "adaptive_reestimate") {
    cat("P(sample-size inc):", round(RES$prob_sample_size_increase, 4), "\n")
    cat("CHW weights       :", paste(round(dc$chw_weights, 4), collapse = ", "), "\n")
  } else if (RES$design == "drop_the_loser") {
    cat("correct selection :", round(RES$prob_correct_selection, 4), "\n")
    cat("adjusted final Z  :", round(dc$adjusted_final_Z, 4), "\n")
  } else if (RES$design == "power_optimization") {
    cat("target power      :", RES$target_power, "\n")
    if (is.null(RES$recommended)) cat("recommended N/arm : NOT REACHED in range\n")
    else {
      cat("recommended N/arm :", RES$recommended$n_per_arm, "\n")
      cat("achieved power    :", round(RES$recommended$power, 4), "\n")
      cat("type I error      :", round(RES$recommended$type_i_error, 4), "\n")
      cat("expected N (tot)  :", RES$recommended$expected_sample_size, "\n")
    }
  }
  cat("n simulations     :", dc$n_simulations, "\n")
}

# ===================== Parameters (auto-injected) =====================
DESIGN <- "__DESIGN__"
N_SIM <- __N_SIM__
N_PER_ARM <- __N_PER_ARM__
EFFECT <- __EFFECT__
EFFECTS <- c(__EFFECTS__)
N_LOOKS <- __N_LOOKS__
SPENDING <- "__SPENDING__"
RHO <- __RHO__
FUTILITY <- __FUTILITY__
BETA <- __BETA__
REEST <- "__REEST__"
INTERIM_FRAC <- __INTERIM_FRAC__
TARGET_CP <- __TARGET_CP__
MAX_INFL <- __MAX_INFL__
N_ARMS <- __N_ARMS__
N_MIN <- __N_MIN__
N_MAX <- __N_MAX__
SEL_FRAC <- __SEL_FRAC__
CORRECTION <- "__CORRECTION__"
ALPHA <- __ALPHA__
OPTIMIZE <- __OPTIMIZE__
TARGET_POWER <- __TARGET_POWER__
VISUALIZE <- __VISUALIZE__
SEED <- __SEED__
OUT_PNG <- "__OUT_PNG__"
OUT_JSON <- "__OUT_JSON__"

# ===================== Driver =====================
if (OPTIMIZE) {
  RES <- optimize_power(EFFECT, target_power = TARGET_POWER, alpha = ALPHA,
    interim_looks = N_LOOKS, spending = SPENDING, rho = RHO, futility = FUTILITY,
    n_min = N_MIN, n_max = N_MAX, n_sim = N_SIM, seed = SEED)
} else if (DESIGN == "group_sequential") {
  RES <- simulate_group_sequential(EFFECT, N_PER_ARM, interim_looks = N_LOOKS,
    alpha = ALPHA, spending = SPENDING, rho = RHO, futility = FUTILITY, beta = BETA, n_sim = N_SIM)
} else if (DESIGN == "adaptive_reestimate") {
  RES <- simulate_adaptive_reestimate(EFFECT, N_PER_ARM, alpha = ALPHA,
    interim_fraction = INTERIM_FRAC, target_cp = TARGET_CP, max_inflation = MAX_INFL,
    n_sim = N_SIM, reestimate_method = REEST)
} else if (DESIGN == "drop_the_loser") {
  RES <- simulate_drop_the_loser(EFFECTS, n_per_arm = N_PER_ARM, n_arms = N_ARMS, alpha = ALPHA,
    selection_fraction = SEL_FRAC, n_sim = N_SIM, correction = CORRECTION)
} else {
  stop("unknown design: ", DESIGN)
}

cat_report(RES)

if (VISUALIZE) {
  p <- if (nzchar(OUT_PNG)) OUT_PNG else file.path(tempdir(), paste0("adaptive_sim_", RES$design, ".png"))
  png(p, width = 800, height = 500)
  if (RES$design == "power_optimization") {
    ns <- sapply(RES$scan, function(q) q$n_per_arm)
    pw <- sapply(RES$scan, function(q) q$power)
    plot(ns, pw, type = "o", col = "red", xlab = "Sample size per arm",
         ylab = "Power", main = "Power vs sample size (group sequential)")
    abline(h = RES$target_power, lty = 2, col = "gray")
  } else {
    eb <- RES$design_config$efficacy_boundaries_Z
    if (!is.null(eb)) {
      looks <- 1:length(eb)
      plot(looks, eb, type = "b", col = "red", xlab = "Interim look",
           ylab = "Z boundary", main = "Group-sequential stopping boundaries")
      fb <- RES$design_config$futility_boundaries_Z
      if (!is.null(fb)) lines(looks[-length(looks)], fb[-length(fb)], type = "b", col = "blue", lty = 2)
    } else {
      plot(0, 0, type = "n", xlab = "", ylab = "", main = "No boundary data to plot")
    }
  }
  dev.off()
  cat("PNG saved to:", p, "\n")
}

if (nzchar(OUT_JSON)) {
  writeLines(to_json(RES), OUT_JSON)
  cat("JSON saved to:", OUT_JSON, "\n")
}
'''

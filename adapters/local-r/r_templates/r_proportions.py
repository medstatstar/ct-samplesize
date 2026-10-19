# r_proportions.py -- R function-based algorithms for ct-samplesize
#
# 比例 / 率类检验算法统一以"R 函数"形式提供（函数化），Python 端只需
# 注入 R_PROP_FUNCS 定义并在生成代码中调用对应函数，消除 main() 中散落的
# 内联 R 代码，并修复原 proportion_one 调用不存在的 pwr.1p.test 的 bug。
#
# 约定（所有函数一致）：
#   --p1 = 对照组 / 原方法 (baseline)
#   --p2 = 实验组 / 新方法 (treatment)
#   效应量 h = ES.h(p2, p1)  (treatment − control)
#   alt: "two.sided" | "greater"(检验 treatment 更优) | "less"
#   给定 power 求解 n；给定 n 求解 power（通过 power=NULL / n=NULL 区分）

R_PROP_FUNCS = r'''
# ===== ct-samplesize: proportion / rate algorithms (R functions) =====
suppressMessages(library(pwr))

# 单组率检验：H0 = p0 (已知/历史), H1 = p1 (预期)。pwr.p.test 的 n 为单组总数。
ss_prop_one <- function(p0, p1, alpha, power = NULL, n = NULL, alt = "two.sided") {
  h <- ES.h(p1, p0)
  if (!is.null(power)) {
    r <- pwr.p.test(h = h, sig.level = alpha, power = power, alternative = alt)
    return(ceiling(r$n))
  } else {
    r <- pwr.p.test(h = h, sig.level = alpha, n = n, alternative = alt)
    return(round(r$power, 4))
  }
}

# 两组率比较（卡方）：p1 = 对照组/原方法, p2 = 实验组/新方法
# h = ES.h(p2, p1)；--side one 检验 p2 > p1 (优效)。n 为每组量。
ss_prop_two <- function(p1, p2, alpha, power = NULL, n = NULL, alt = "two.sided") {
  h <- ES.h(p2, p1)
  if (!is.null(power)) {
    r <- pwr.2p.test(h = h, sig.level = alpha, power = power, alternative = alt)
    return(ceiling(r$n))
  } else {
    r <- pwr.2p.test(h = h, sig.level = alpha, n = n, alternative = alt)
    return(round(r$power, 4))
  }
}

# 配对比例（McNemar）近似：以两组边际率构造 arcsin 效应量，按两组率框架求解。
# n 为所需配对 (对子) 数。
ss_prop_paired <- function(p1, p2, alpha, power = NULL, n = NULL, alt = "two.sided") {
  h <- ES.h(p2, p1)
  if (!is.null(power)) {
    r <- pwr.2p.test(h = h, sig.level = alpha, power = power, alternative = alt)
    return(ceiling(r$n))
  } else {
    r <- pwr.2p.test(h = h, sig.level = alpha, n = n, alternative = alt)
    return(round(r$power, 4))
  }
}

# 优势比 (OR) / 相对危险度 (RR) 近似：通过两组率 arcsin 效应量估算所需样本量。
# 注意：此为基于两组率的近似，精确 OR/RR 设计请使用专用包 (如 powerMediation / WebPower)。
# n 为每组量。
ss_or_rr <- function(p1, p2, alpha, power = NULL, n = NULL, alt = "two.sided") {
  h <- ES.h(p2, p1)
  if (!is.null(power)) {
    r <- pwr.2p.test(h = h, sig.level = alpha, power = power, alternative = alt)
    return(ceiling(r$n))
  } else {
    r <- pwr.2p.test(h = h, sig.level = alpha, n = n, alternative = alt)
    return(round(r$power, 4))
  }
}
'''

__all__ = ["R_PROP_FUNCS"]

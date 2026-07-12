#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临床实验样本量与检验效能计算工具 (Python后端)
基于 statsmodels 实现，覆盖临床试验常见场景

使用方式:
    python samplesize_power.py --test ttest_ind --effect 0.5 --alpha 0.05 --power 0.9
    python samplesize_power.py --test proportion --p1 0.3 --p2 0.15 --alpha 0.05 --power 0.8
    python samplesize_power.py --test anova --effect 0.25 --alpha 0.05 --power 0.9 --k_groups 3
    python samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80 --alpha 0.05 --power 0.8
"""

import argparse
import sys
import numpy as np
from statsmodels.stats import power as sp


def one_sample_ttest(effect_size, alpha=0.05, power=0.8, alternative='two-sided', nobs=None):
    """单样本/配对样本t检验 样本量或power计算"""
    power_tool = sp.TTestPower()
    if nobs is None:  # 求样本量
        result = power_tool.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            alternative=alternative
        )
        print(f"\n{'='*50}")
        print(f"单样本/配对样本t检验 样本量计算")
        print(f"{'='*50}")
        print(f"效应量 (Cohen's d): {effect_size:.4f}")
        print(f"显著性水平 (α): {alpha}")
        print(f"期望检验效能 (1-β): {power}")
        print(f"检验类型: {'双侧' if alternative=='two-sided' else ('单侧(' + alternative + ')')}")
        print(f"{'─'*50}")
        print(f"所需样本量 (N): {int(np.ceil(result))}")
        print(f"{'='*50}")
        return int(np.ceil(result))
    else:  # 求power
        actual_power = power_tool.power(
            effect_size=effect_size,
            nobs=nobs,
            alpha=alpha,
            alternative=alternative
        )
        print(f"\n{'='*50}")
        print(f"单样本/配对样本t检验 效能计算")
        print(f"{'='*50}")
        print(f"效应量 (Cohen's d): {effect_size}")
        print(f"样本量 (N): {nobs}")
        print(f"显著性水平 (α): {alpha}")
        print(f"检验类型: {'双侧' if alternative=='two-sided' else ('单侧(' + alternative + ')')}")
        print(f"{'─'*50}")
        print(f"实际检验效能 (1-β): {actual_power:.4f}")
        print(f"{'='*50}")
        return actual_power


def two_sample_ttest(effect_size, alpha=0.05, power=0.8, ratio=1.0, alternative='two-sided', nobs1=None):
    """两独立样本t检验 样本量或power计算"""
    power_tool = sp.TTestIndPower()
    if nobs1 is None:  # 求样本量
        result = power_tool.solve_power(
            effect_size=effect_size,
            nobs1=None,
            alpha=alpha,
            power=power,
            ratio=ratio,
            alternative=alternative
        )
        n1 = int(np.ceil(result))
        n2 = int(np.ceil(result * ratio))
        total = n1 + n2
        print(f"\n{'='*50}")
        print(f"两独立样本t检验 样本量计算")
        print(f"{'='*50}")
        print(f"效应量 (Cohen's d): {effect_size:.4f}")
        print(f"显著性水平 (α): {alpha}")
        print(f"期望检验效能 (1-β): {power}")
        print(f"组2/组1样本量之比: {ratio:.1f}")
        print(f"检验类型: {'双侧' if alternative=='two-sided' else ('单侧(' + alternative + ')')}")
        print(f"{'─'*50}")
        print(f"组1所需样本量: {n1}")
        print(f"组2所需样本量: {n2}")
        print(f"总样本量: {total}")
        print(f"{'='*50}")
        return n1, n2
    else:  # 求power
        actual_power = power_tool.power(
            effect_size=effect_size,
            nobs1=nobs1,
            alpha=alpha,
            power=None,
            ratio=ratio,
            alternative=alternative
        )
        print(f"\n{'='*50}")
        print(f"两独立样本t检验 效能计算")
        print(f"{'='*50}")
        print(f"效应量 (Cohen's d): {effect_size}")
        print(f"组1样本量 (N1): {nobs1}")
        print(f"组2/组1之比: {ratio}")
        print(f"显著性水平 (α): {alpha}")
        print(f"{'─'*50}")
        print(f"实际检验效能 (1-β): {actual_power:.4f}")
        print(f"{'='*50}")
        return actual_power


def anova_sample(effect_size, alpha=0.05, power=0.8, k_groups=3, nobs=None):
    """单因素方差分析 样本量或power计算"""
    power_tool = sp.FTestAnovaPower()
    if nobs is None:  # 求样本量（每组）
        result = power_tool.solve_power(
            effect_size=effect_size,
            nobs=None,
            alpha=alpha,
            power=power,
            k_groups=k_groups
        )
        per_group = int(np.ceil(result))
        total = per_group * k_groups
        print(f"\n{'='*50}")
        print(f"单因素方差分析 (ANOVA) 样本量计算")
        print(f"{'='*50}")
        print(f"效应量 (Cohen's f): {effect_size:.4f}")
        print(f"显著性水平 (α): {alpha}")
        print(f"期望检验效能 (1-β): {power}")
        print(f"组数: {k_groups}")
        print(f"{'─'*50}")
        print(f"每组所需样本量: {per_group}")
        print(f"总样本量: {total}")
        print(f"{'='*50}")
        return per_group
    else:
        actual_power = power_tool.power(
            effect_size=effect_size,
            nobs=nobs,
            alpha=alpha,
            k_groups=k_groups
        )
        print(f"\n{'='*50}")
        print(f"ANOVA 效能计算")
        print(f"{'='*50}")
        print(f"效应量 (f): {effect_size}, 组数: {k_groups}, 每组n: {nobs}")
        print(f"实际检验效能 (1-β): {actual_power:.4f}")
        print(f"{'='*50}")
        return actual_power


def proportion_test(p1, p2=None, alpha=0.05, power=0.8, two_sample=True, 
                    alternative='two-sided', nobs=None, ratio=1.0):
    """
    率的比较 样本量计算
    单样本率: 使用 arcsin 变换后调用 ttest
    两样本率: 使用 arcsin 变换后调用独立 ttest
    """
    # arcsin 变换计算效应量 h
    h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
    
    if two_sample:
        return two_sample_ttest(
            effect_size=h, alpha=alpha, power=power,
            ratio=ratio, alternative=alternative, nobs1=nobs
        )
    else:
        return one_sample_ttest(
            effect_size=h, alpha=alpha, power=power,
            alternative=alternative, nobs=nobs
        )


def non_inferiority_proportion(margin, p1, p2, alpha=0.05, power=0.8, 
                                 nobs=None, ratio=1.0):
    """
    非劣效性设计的样本率比较 (率差法)
    margin: 非劣效界值 (如 0.10 表示允许新方法低10%以内)
    p1: 试验组率, p2: 对照组率
    单侧alpha
    """
    se_sq = p1*(1-p1) + p2*(1-p2)/ratio
    from scipy.stats import norm
    z_alpha = norm.ppf(1-alpha)
    z_beta = norm.ppf(power)
    
    if nobs is None:
        # 样本量公式 (假设两组1:1随机)
        # n1 = n2 = (Z_alpha + Z_beta)^2 * (p1(1-p1) + p2(1-p2)) / (p1 - p2 + margin)^2
        # 其中 margin 为正数, p1-p2 如果为正表示试验组更优
        denominator = (p1 - p2 + margin)**2
        if denominator <= 0:
            raise ValueError(f"非劣效界值不成立: 效应量({p1-p2:.3f}) 应 > -界值({-margin:.3f})")
        n_per_group = int(np.ceil((z_alpha + z_beta)**2 * (p1*(1-p1) + p2*(1-p2)) / denominator))
        total = n_per_group * 2
        print(f"\n{'='*50}")
        print(f"非劣效性设计 - 率比较 样本量计算")
        print(f"{'='*50}")
        print(f"非劣效界值 (δ): {margin}")
        print(f"试验组率 (p1): {p1}")
        print(f"对照组率 (p2): {p2}")
        print(f"显著性水平 (单侧α): {alpha}")
        print(f"期望检验效能: {power}")
        print(f"{'─'*50}")
        print(f"每组所需样本量 (1:1随机): {n_per_group}")
        print(f"总样本量: {total}")
        print(f"{'='*50}")
        return n_per_group, n_per_group
    else:
        # 计算实际power
        z = (p1 - p2 + margin) / np.sqrt(se_sq / nobs)
        actual_power = 1 - norm.cdf(z - z_alpha)
        print(f"\n{'='*50}")
        print(f"非劣效性设计 - 效能计算")
        print(f"{'='*50}")
        print(f"每组样本量: {nobs}")
        print(f"试验组率: {p1}, 对照组率: {p2}")
        print(f"非劣效界值: {margin}")
        print(f"实际检验效能: {actual_power:.4f}")
        print(f"{'='*50}")
        return actual_power


def survival_sample(accrual_time, follow_up, hazard_ratio, alpha=0.05, power=0.8,
                    dropout_rate=0, nobs=None):
    """
    生存分析 (log-rank检验) 样本量估算 (Schoenfeld formula)
    hazard_ratio: 风险比 (试验组/对照组)
    accrual_time: 入组时间
    follow_up: 随访时间
    dropout_rate: 失访率
    """
    from scipy.stats import norm
    z_alpha = norm.ppf(1-alpha/2)
    z_beta = norm.ppf(power)
    
    # Schoenfeld formula 计算所需事件数
    if hazard_ratio <= 0 or hazard_ratio == 1:
        raise ValueError("风险比 HR 必须 >0 且 ≠1")
    d = int(np.ceil(((z_alpha + z_beta) / np.log(hazard_ratio))**2 * 4))
    
    if nobs is None:
        # 简化估算：假设总事件率约50%（需根据实际调整）
        # 精确计算需用 rpact/gsDesign 考虑入组时间和删失
        event_rate = 0.5  # 默认事件率，实际应根据入组+随访时间计算
        n_per_group = int(np.ceil(d / (2 * event_rate)))  # 两组均衡
        if dropout_rate > 0:
            n_per_group = int(np.ceil(n_per_group / (1 - dropout_rate)))
        total = n_per_group * 2
        print(f"\n{'='*50}")
        print(f"生存分析 (Log-rank检验) 样本量估算")
        print(f"{'='*50}")
        print(f"风险比 (HR): {hazard_ratio}")
        print(f"显著性水平 (双侧α): {alpha}")
        print(f"期望检验效能: {power}")
        print(f"入组时间: {accrual_time}, 随访: {follow_up}")
        print(f"{'─'*50}")
        print(f"所需事件总数: {d}")
        print(f"假设事件率: ~{event_rate*100:.0f}% (简化)")
        print(f"每组所需样本量: ~{n_per_group}")
        print(f"总样本量: ~{total}")
        if dropout_rate > 0:
            print(f"(已考虑 {dropout_rate*100:.0f}% 脱落率)")
        print(f"⚠️ 此为简化Schoenfeld公式估算。精确计算需用 R 包(rpact/gsDesign)")
        print(f"{'='*50}")
        return n_per_group
    else:
        # 效能计算（简化）
        effective_events = nobs * 0.5  # 简化假设
        z = np.log(hazard_ratio) * np.sqrt(effective_events) / 2 - z_alpha
        actual_power = norm.cdf(z)
        print(f"\n{'='*50}")
        print(f"生存分析 效能计算（简化）")
        print(f"{'='*50}")
        print(f"HR: {hazard_ratio}, 每组N: {nobs}")
        print(f"估计事件数: ~{int(effective_events*2)}")
        print(f"检验效能: {actual_power:.4f}")
        print(f"{'='*50}")
        return actual_power


def kappa_sample(kappa0, kappa1, alpha=0.05, power=0.8, nobs=None):
    """
    Kappa一致性检验的样本量计算（近似公式）
    kappa0: 零假设kappa值
    kappa1: 备择假设kappa值
    """
    from scipy.stats import norm
    z_alpha = norm.ppf(1-alpha)
    z_beta = norm.ppf(power)
    se_diff = np.sqrt(0.074 + 0.056)  # 近似标准误
    kappa_diff = kappa1 - kappa0
    if abs(kappa_diff) < 1e-10:
        raise ValueError("Kappa0 和 Kappa1 不能相等")
    n = int(np.ceil(((z_alpha + z_beta)**2 * se_diff**2) / (kappa_diff**2)))
    print(f"\n{'='*50}")
    print(f"Kappa一致性检验 样本量估算")
    print(f"{'='*50}")
    print(f"Kappa0: {kappa0}, Kappa1: {kappa1}")
    print(f"显著性水平: {alpha}, 效能: {power}")
    print(f"所需样本量: {n}")
    print(f"{'='*50}")
    return n


def correlation_sample(r0, r1, alpha=0.05, power=0.8, nobs=None):
    """
    相关系数比较的样本量计算
    """
    from scipy.stats import norm
    z_alpha = norm.ppf(1-alpha)
    z_beta = norm.ppf(power)
    # Fisher z 变换
    zr0 = np.arctanh(r0)
    zr1 = np.arctanh(r1)
    diff = abs(zr1 - zr0)
    if diff < 1e-10:
        raise ValueError("r0 和 r1 不能相等")
    n = int(np.ceil(((z_alpha + z_beta) / diff)**2 + 3))
    print(f"\n{'='*50}")
    print(f"相关系数检验 样本量计算")
    print(f"{'='*50}")
    print(f"零假设 r0: {r0}, 备择假设 r1: {r1}")
    print(f"Fisher z 变换后差: {diff:.4f}")
    print(f"所需样本量: {n}")
    print(f"{'='*50}")
    return n


# ============================================================
# 🔴 强制 R 代码生成器
#   每次 Python 计算后，自动生成可独立运行的 R 代码
# ============================================================

def generate_r_code(test_type, args, result_summary):
    """
    根据测试类型和参数，生成完整的、可独立运行的 R 脚本
    用户可直接复制到 R Studio 或 Rscript 中运行
    """
    
    # 生成 R 代码头部
    r_script = f'''# ============================================================
# 临床样本量计算 - 可独立运行的 R 脚本
# 由 Python 脚本自动生成 (samplesize_power.py)
# 检验类型: {test_type}
# ============================================================

# ---- 0. 环境准备（首次运行请取消注释） ----
'''
    
    # 根据测试类型决定需要哪些包
    packages_needed = []
    if test_type in ['ttest_one', 'ttest_ind', 'proportion_one', 'proportion_two', 'non_inferiority']:
        packages_needed.extend(['TrialSize', 'pwr'])
    elif test_type == 'anova':
        packages_needed.extend(['pwr', 'TrialSize'])
    elif test_type == 'survival':
        packages_needed.extend(['rpact', 'gsDesign'])
    elif test_type == 'kappa':
        packages_needed.append('pwr')
    elif test_type == 'correlation':
        packages_needed.append('pwr')
    else:
        packages_needed.extend(['TrialSize', 'pwr'])
    
    for pkg in packages_needed:
        r_script += f'# install.packages("{pkg}")\n'
    r_script += '\n'
    
    for pkg in packages_needed:
        r_script += f'library({pkg})\n'
    r_script += '\n'
    
    # 参数部分
    r_script += '# ---- 1. 参数设置 ----\n'
    
    if test_type == 'ttest_one':
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'effect_size <- {args.effect}\n'
        r_script += f'alternative <- "{args.alternative}"\n'
        r_script += f'# 方向映射: two-sided="two.sided", larger="greater", smaller="less"\n'
        r_script += f'r_alternative <- ifelse(alternative=="two-sided", "two.sided", ifelse(alternative=="larger", "greater", "less"))\n'
        r_script += f'\n'
        r_script += f'# ---- 2. 计算 (单样本/配对t) ----\n'
        r_script += f'result <- pwr.t.test(\n'
        r_script += f'  d = effect_size,\n'
        r_script += f'  n = NULL,\n'
        r_script += f'  sig.level = alpha,\n'
        r_script += f'  power = power,\n'
        r_script += f'  type = "one.sample",\n'
        r_script += f'  alternative = r_alternative\n'
        r_script += f')\n'
        r_script += f'n_per_group <- ceiling(result$n)\n'
        r_script += f'\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("效应量 d: %.4f\\n", effect_size))\n'
        r_script += f'cat(sprintf("所需样本量: %d\\n", n_per_group))\n'
        
    elif test_type == 'ttest_ind':
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'effect_size <- {args.effect}\n'
        r_script += f'ratio <- {args.ratio}\n'
        r_script += f'alternative <- "{args.alternative}"\n'
        r_script += f'r_alternative <- ifelse(alternative=="two-sided", "two.sided", ifelse(alternative=="larger", "greater", "less"))\n'
        r_script += f'\n'
        r_script += f'# ---- 2. 计算 (两独立样本t) ----\n'
        r_script += f'result <- pwr.t.test(\n'
        r_script += f'  d = effect_size,\n'
        r_script += f'  n = NULL,\n'
        r_script += f'  sig.level = alpha,\n'
        r_script += f'  power = power,\n'
        r_script += f'  type = "two.sample",\n'
        r_script += f'  alternative = r_alternative\n'
        r_script += f')\n'
        r_script += f'n1 <- ceiling(result$n)\n'
        r_script += f'n2 <- ceiling(result$n * ratio)\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("效应量 d: %.4f\\n", effect_size))\n'
        r_script += f'cat(sprintf("组1样本量: %d\\n", n1))\n'
        r_script += f'cat(sprintf("组2样本量: %d\\n", n2))\n'
        r_script += f'cat(sprintf("总样本量: %d\\n", n1 + n2))\n'
        
    elif test_type == 'anova':
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'eff_f <- {args.effect}\n'
        r_script += f'k <- {args.k_groups}\n'
        r_script += f'\n'
        r_script += f'# ---- 2. 计算 (ANOVA) ----\n'
        r_script += f'result <- pwr.anova.test(\n'
        r_script += f'  k = k,\n'
        r_script += f'  f = eff_f,\n'
        r_script += f'  sig.level = alpha,\n'
        r_script += f'  power = power\n'
        r_script += f')\n'
        r_script += f'n_per_group <- ceiling(result$n)\n'
        r_script += f'total <- n_per_group * k\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("效应量 f: %.4f\\n", eff_f))\n'
        r_script += f'cat(sprintf("组数: %d\\n", k))\n'
        r_script += f'cat(sprintf("每组样本量: %d\\n", n_per_group))\n'
        r_script += f'cat(sprintf("总样本量: %d\\n", total))\n'
        
    elif test_type in ['proportion_one', 'proportion_two']:
        p1 = args.p1 if args.p1 else 0
        p2 = args.p2 if args.p2 else 0
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'p1 <- {p1}\n'
        r_script += f'p2 <- {p2}\n'
        r_script += f'\n'
        r_script += f'# arcsin 变换\n'
        r_script += f'h <- 2 * (asin(sqrt(p1)) - asin(sqrt(p2)))\n'
        
        if test_type == 'proportion_one':
            r_script += f'\n'
            r_script += f'# ---- 单样本率比较 ----\n'
            r_script += f'result <- pwr.p.test(\n'
            r_script += f'  h = h, n = NULL,\n'
            r_script += f'  sig.level = alpha, power = power,\n'
            r_script += f'  alternative = "two.sided"\n'
            r_script += f')\n'
            r_script += f'n_per_group <- ceiling(result$n)\n'
        else:
            r_script += f'\n'
            r_script += f'# ---- 两样本率比较 ----\n'
            r_script += f'result <- pwr.2p.test(\n'
            r_script += f'  h = h, n = NULL,\n'
            r_script += f'  sig.level = alpha, power = power,\n'
            r_script += f'  alternative = "two.sided"\n'
            r_script += f')\n'
            r_script += f'n_per_group <- ceiling(result$n)\n'
            r_script += f'total <- n_per_group * 2\n'
            
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("效应量 h (arcsin): %.4f\\n", h))\n'
        r_script += f'cat(sprintf("每组样本量: %d\\n", n_per_group))\n'
        
    elif test_type == 'non_inferiority':
        margin = args.margin if args.margin else 0.1
        p1 = args.p1 if args.p1 else 0
        p2 = args.p2 if args.p2 else 0
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'pe <- {p1}      # 试验组率\n'
        r_script += f'pc <- {p2}      # 对照组率\n'
        r_script += f'delta <- {margin}   # 非劣效界值\n'
        r_script += f'ratio <- {args.ratio}\n'
        r_script += f'\n'
        r_script += f'# ---- 非劣效性设计率比较 ----\n'
        r_script += f'result <- TrialSize::NPropTwoSidedNonInferiority(\n'
        r_script += f'  alpha = alpha,\n'
        r_script += f'  beta = 1 - power,\n'
        r_script += f'  pe = pe, pc = pc,\n'
        r_script += f'  delta = delta, ratio = ratio\n'
        r_script += f')\n'
        r_script += f'n_per_group <- ceiling(result[2, "n"])\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("非劣效界值: %.3f\\n", delta))\n'
        r_script += f'cat(sprintf("试验组率: %.3f, 对照组率: %.3f\\n", pe, pc))\n'
        r_script += f'cat(sprintf("每组样本量: %d\\n", n_per_group))\n'
        
    elif test_type == 'survival':
        hr = args.hazard_ratio if args.hazard_ratio else 0.7
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'hr <- {hr}     # 风险比\n'
        r_script += f'\n'
        r_script += f'# ---- 生存分析 (Schoenfeld公式) ----\n'
        r_script += f'# 精确计算请使用 rpact::getSampleSizeSurvival()\n'
        r_script += f'z_alpha <- qnorm(1 - alpha/2)\n'
        r_script += f'z_beta <- qnorm(power)\n'
        r_script += f'd <- ceiling((z_alpha + z_beta)^2 / (log(hr))^2 * 4)\n'
        r_script += f'\n'
        r_script += f'# rpact 精确计算\n'
        r_script += f'result <- tryCatch({{\n'
        r_script += f'  rpact::getSampleSizeSurvival(\n'
        r_script += f'    alpha = alpha, beta = 1 - power,\n'
        r_script += f'    hazardRatio = hr,\n'
        r_script += f'    accrualTime = 12,\n'
        r_script += f'    followUpTime = 12\n'
        r_script += f'  )\n'
        r_script += f'}}, error = function(e) NULL)\n'
        r_script += f'\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("风险比 HR: %.3f\\n", hr))\n'
        r_script += f'cat(sprintf("所需事件数: %d\\n", d))\n'
        r_script += f'cat("注意: 此为简化Schoenfeld公式估算\\n")\n'
        r_script += f'cat("精确结果请运行 rpact::getSampleSizeSurvival()\\n")\n'
        
    elif test_type == 'kappa':
        p1 = args.p1 if args.p1 else 0
        p2 = args.p2 if args.p2 else 0
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'kappa0 <- {p1}\n'
        r_script += f'kappa1 <- {p2}\n'
        r_script += f'\n'
        r_script += f'# ---- Kappa一致性检验样本量估算 ----\n'
        r_script += f'se_diff <- sqrt(0.074 + 0.056)  # 近似标准误\n'
        r_script += f'z_alpha <- qnorm(1 - alpha)\n'
        r_script += f'z_beta  <- qnorm(power)\n'
        r_script += f'n <- ceiling((z_alpha + z_beta)^2 * se_diff^2 / (kappa1 - kappa0)^2)\n'
        r_script += f'\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("Kappa0: %.3f, Kappa1: %.3f\\n", kappa0, kappa1))\n'
        r_script += f'cat(sprintf("所需样本量: %d\\n", n))\n'
        
    elif test_type == 'correlation':
        p1 = args.p1 if args.p1 else 0
        p2 = args.p2 if args.p2 else 0
        r_script += f'alpha <- {args.alpha}\n'
        r_script += f'power <- {args.power if args.power else "NULL"}\n'
        r_script += f'r0 <- {p1}\n'
        r_script += f'r1 <- {p2}\n'
        r_script += f'\n'
        r_script += f'# ---- 相关系数Fisher z变换检验 ----\n'
        r_script += f'result <- pwr.r.test(\n'
        r_script += f'  r = abs(r1 - r0),\n'
        r_script += f'  n = NULL,\n'
        r_script += f'  sig.level = alpha,\n'
        r_script += f'  power = power,\n'
        r_script += f'  alternative = "two.sided"\n'
        r_script += f')\n'
        r_script += f'n_per_group <- ceiling(result$n)\n'
        r_script += f'cat("\\n===== 计算结果 =====\\n")\n'
        r_script += f'cat(sprintf("零假设 r0: %.3f, 备择假设 r1: %.3f\\n", r0, r1))\n'
        r_script += f'cat(sprintf("所需样本量: %d\\n", n_per_group))\n'
    
    # 统一添加尾部
    r_script += f'''
# ---- 3. 结果解释 ----
cat("\\n===== 结果解释 =====\\n")
cat("在给定参数下，上述样本量可确保在指定显著性水平和效能下\\n")
cat("检测出预期的效应量差异。\\n")
'''
    
    return r_script


def main():
    parser = argparse.ArgumentParser(
        description='临床实验样本量/检验效能计算 (Python基础版, 自动附R代码)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 两样本t检验求样本量
  python samplesize_power.py --test ttest_ind --effect 0.5 --alpha 0.05 --power 0.9
  
  # 单样本率检验求power
  python samplesize_power.py --test proportion_one --p1 0.5 --p2 0.4 --nobs 60
  
  # 两样本率比较求样本量
  python samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
  
  # ANOVA样本量
  python samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.9
  
  # 非劣效性设计
  python samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80
  
  # 生存分析 (简化)
  python samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8
        """
    )
    
    parser.add_argument('--test', required=True, 
                        choices=['ttest_one', 'ttest_ind', 'anova', 
                                 'proportion_one', 'proportion_two',
                                 'non_inferiority', 'survival', 
                                 'kappa', 'correlation'],
                        help='统计检验类型')
    parser.add_argument('--effect', type=float, help='标准化效应量 (Cohen\'s d 或 f)')
    parser.add_argument('--p1', type=float, help='试验组率 (proportion tests)')
    parser.add_argument('--p2', type=float, help='对照组率或零假设率')
    parser.add_argument('--margin', type=float, help='非劣效界值')
    parser.add_argument('--hazard_ratio', type=float, help='风险比 (survival)')
    parser.add_argument('--alpha', type=float, default=0.05, help='显著性水平 (默认0.05)')
    parser.add_argument('--power', type=float, help='期望检验效能 (如0.8/0.9)')
    parser.add_argument('--nobs', type=int, help='指定样本量求power/效应量时填入')
    parser.add_argument('--nobs1', type=int, help='两样本t检验组1样本量')
    parser.add_argument('--ratio', type=float, default=1.0, help='组2/组1比 (默认1.0)')
    parser.add_argument('--k_groups', type=int, default=3, help='ANOVA组数 (默认3)')
    parser.add_argument('--alternative', default='two-sided',
                        choices=['two-sided', 'larger', 'smaller'],
                        help='检验方向 (默认双侧)')
    
    args = parser.parse_args()
    
    try:
        if args.test == 'ttest_one':
            one_sample_ttest(
                effect_size=args.effect, alpha=args.alpha,
                power=args.power, alternative=args.alternative,
                nobs=args.nobs
            )
        elif args.test == 'ttest_ind':
            two_sample_ttest(
                effect_size=args.effect, alpha=args.alpha,
                power=args.power, ratio=args.ratio,
                alternative=args.alternative, nobs1=args.nobs1 or args.nobs
            )
        elif args.test == 'anova':
            anova_sample(
                effect_size=args.effect, alpha=args.alpha,
                power=args.power, k_groups=args.k_groups,
                nobs=args.nobs
            )
        elif args.test == 'proportion_one':
            if args.nobs is None:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=False,
                    alternative=args.alternative
                )
            else:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=False,
                    alternative=args.alternative, nobs=args.nobs
                )
        elif args.test == 'proportion_two':
            if args.nobs is None:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=True,
                    ratio=args.ratio, alternative=args.alternative
                )
            else:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=True,
                    ratio=args.ratio, alternative=args.alternative,
                    nobs=args.nobs
                )
        elif args.test == 'non_inferiority':
            non_inferiority_proportion(
                margin=args.margin, p1=args.p1, p2=args.p2,
                alpha=args.alpha, power=args.power,
                nobs=args.nobs, ratio=args.ratio
            )
        elif args.test == 'survival':
            if args.nobs is None:
                survival_sample(
                    accrual_time=12, follow_up=12,
                    hazard_ratio=args.hazard_ratio,
                    alpha=args.alpha, power=args.power
                )
            else:
                survival_sample(
                    accrual_time=12, follow_up=12,
                    hazard_ratio=args.hazard_ratio,
                    alpha=args.alpha, power=args.power,
                    nobs=args.nobs
                )
        elif args.test == 'kappa':
            kappa_sample(kappa0=args.p1, kappa1=args.p2, 
                         alpha=args.alpha, power=args.power)
        elif args.test == 'correlation':
            correlation_sample(r0=args.p1, r1=args.p2,
                              alpha=args.alpha, power=args.power)
        
        print("\n⚠️ 注意: 此为基础Python实现。对于复杂设计（如组序贯/适应性设计/多臂平台试验），")
        print("强烈建议安装 R 并使用 rpact / gsDesign 等专业包。")

        # 🔴 强制输出 R 代码
        print("\n\n" + "="*60)
        print("## 📋 可复现的 R 代码 (复制到 R 中直接运行)")
        print("="*60)
        r_code = generate_r_code(args.test, args, result_summary="")
        print(r_code)
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 计算错误: {e}")
        print("请检查参数是否完整合理")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='临床实验样本量/检验效能计算 (Python基础版, 自动附R代码)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 两样本t检验求样本量
  python samplesize_power.py --test ttest_ind --effect 0.5 --alpha 0.05 --power 0.9
  
  # 单样本率检验求power
  python samplesize_power.py --test proportion_one --p1 0.5 --p2 0.4 --nobs 60
  
  # 两样本率比较求样本量
  python samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8
  
  # ANOVA样本量
  python samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.9
  
  # 非劣效性设计
  python samplesize_power.py --test non_inferiority --margin 0.1 --p1 0.85 --p2 0.80
  
  # 生存分析 (简化)
  python samplesize_power.py --test survival --hazard_ratio 0.7 --power 0.8
        """
    )
    
    parser.add_argument('--test', required=True, 
                        choices=['ttest_one', 'ttest_ind', 'anova', 
                                 'proportion_one', 'proportion_two',
                                 'non_inferiority', 'survival', 
                                 'kappa', 'correlation'],
                        help='统计检验类型')
    parser.add_argument('--effect', type=float, help='标准化效应量 (Cohen\'s d 或 f)')
    parser.add_argument('--p1', type=float, help='试验组率 (proportion tests)')
    parser.add_argument('--p2', type=float, help='对照组率或零假设率')
    parser.add_argument('--margin', type=float, help='非劣效界值')
    parser.add_argument('--hazard_ratio', type=float, help='风险比 (survival)')
    parser.add_argument('--alpha', type=float, default=0.05, help='显著性水平 (默认0.05)')
    parser.add_argument('--power', type=float, help='期望检验效能 (如0.8/0.9)')
    parser.add_argument('--nobs', type=int, help='指定样本量求power/效应量时填入')
    parser.add_argument('--nobs1', type=int, help='两样本t检验组1样本量')
    parser.add_argument('--ratio', type=float, default=1.0, help='组2/组1比 (默认1.0)')
    parser.add_argument('--k_groups', type=int, default=3, help='ANOVA组数 (默认3)')
    parser.add_argument('--alternative', default='two-sided',
                        choices=['two-sided', 'larger', 'smaller'],
                        help='检验方向 (默认双侧)')
    
    args = parser.parse_args()
    
    try:
        if args.test == 'ttest_one':
            one_sample_ttest(
                effect_size=args.effect, alpha=args.alpha,
                power=args.power, alternative=args.alternative,
                nobs=args.nobs
            )
        elif args.test == 'ttest_ind':
            two_sample_ttest(
                effect_size=args.effect, alpha=args.alpha,
                power=args.power, ratio=args.ratio,
                alternative=args.alternative, nobs1=args.nobs1 or args.nobs
            )
        elif args.test == 'anova':
            anova_sample(
                effect_size=args.effect, alpha=args.alpha,
                power=args.power, k_groups=args.k_groups,
                nobs=args.nobs
            )
        elif args.test == 'proportion_one':
            if args.nobs is None:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=False,
                    alternative=args.alternative
                )
            else:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=False,
                    alternative=args.alternative, nobs=args.nobs
                )
        elif args.test == 'proportion_two':
            if args.nobs is None:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=True,
                    ratio=args.ratio, alternative=args.alternative
                )
            else:
                proportion_test(
                    p1=args.p1, p2=args.p2, alpha=args.alpha,
                    power=args.power, two_sample=True,
                    ratio=args.ratio, alternative=args.alternative,
                    nobs=args.nobs
                )
        elif args.test == 'non_inferiority':
            non_inferiority_proportion(
                margin=args.margin, p1=args.p1, p2=args.p2,
                alpha=args.alpha, power=args.power,
                nobs=args.nobs, ratio=args.ratio
            )
        elif args.test == 'survival':
            if args.nobs is None:
                survival_sample(
                    accrual_time=12, follow_up=12,
                    hazard_ratio=args.hazard_ratio,
                    alpha=args.alpha, power=args.power
                )
            else:
                survival_sample(
                    accrual_time=12, follow_up=12,
                    hazard_ratio=args.hazard_ratio,
                    alpha=args.alpha, power=args.power,
                    nobs=args.nobs
                )
        elif args.test == 'kappa':
            kappa_sample(kappa0=args.p1, kappa1=args.p2, 
                         alpha=args.alpha, power=args.power)
        elif args.test == 'correlation':
            correlation_sample(r0=args.p1, r1=args.p2,
                              alpha=args.alpha, power=args.power)
        
        print("\n⚠️ 注意: 此为基础Python实现。对于复杂设计（如组序贯/适应性设计/多臂平台试验），")
        print("强烈建议安装 R 并使用 rpact / gsDesign 等专业包。")

        # 🔴 强制输出 R 代码
        print("\n\n" + "="*60)
        print("## 📋 可复现的 R 代码 (复制到 R 中直接运行)")
        print("="*60)
        r_code = generate_r_code(args.test, args, result_summary="")
        print(r_code)
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 计算错误: {e}")
        print("请检查参数是否完整合理")
        sys.exit(1)


if __name__ == '__main__':
    main()

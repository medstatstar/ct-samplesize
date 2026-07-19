#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n.py -- bilingual (EN/ZH) localization for ct-samplesize

Provides:
  - is_chinese_os(): detect if the OS locale is Chinese
  - t(key, **kwargs): translate a message key to the current locale
  - set_lang(locale): manually override the locale (for testing)

Rules (per ~/.workbuddy/MEMORY.md "双语语言策略"):
  - Default: English
  - Auto-switch to Chinese when OS locale contains zh/CN
  - Code output (R/Python) is NOT affected by language policy

Usage:
  from i18n import t
  print(t("error.rscript_not_found"))
  print(t("info.result_saved", path="/tmp/x.json"))
"""

import os
import sys


# ═══════════════════════════════════════════════════════════════════════════
# Locale detection / 系统语言检测
# ═══════════════════════════════════════════════════════════════════════════

_OVERRIDE_LANG = None


def set_lang(locale_code):
    """Manually override language (for testing). Pass None to reset to auto-detect."""
    global _OVERRIDE_LANG
    _OVERRIDE_LANG = locale_code


def is_chinese_os():
    """Detect if the OS is Chinese (zh-CN, zh-TW, zh-HK, etc.).

    Detection order:
      1. Environment variables: LANGUAGE / LC_ALL / LC_MESSAGES / LANG
      2. Windows API: GetLocaleInfoW + registry (LocaleName)
      3. Python locale module: getdefaultlocale()
    """
    global _OVERRIDE_LANG
    if _OVERRIDE_LANG is not None:
        return _OVERRIDE_LANG == "zh"

    # 1. Check environment variables
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val.lower().startswith("zh"):
            return True

    # 2. Windows-specific detection
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(85)
            ctypes.windll.kernel32.GetLocaleInfoW(0x0400, 0x00000005, buf, 85)
            if buf.value.lower().startswith("zh"):
                return True
        except Exception:
            pass

        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Control Panel\International"
            )
            locale_name = winreg.QueryValueEx(key, "LocaleName")[0]
            winreg.CloseKey(key)
            if locale_name.lower().startswith("zh"):
                return True
        except Exception:
            pass

    # 3. Python locale module fallback
    try:
        import locale
        loc = locale.getdefaultlocale()[0]
        if loc and loc.lower().startswith("zh"):
            return True
    except Exception:
        pass

    return False


def _current_lang():
    """Return 'zh' or 'en'."""
    return "zh" if is_chinese_os() else "en"


# ═══════════════════════════════════════════════════════════════════════════
# Message dictionary / 消息字典
# ═══════════════════════════════════════════════════════════════════════════

_MESSAGES = {
    # ── Dry run / 安全预览 ──
    "dry_run.not_executed": {
        "en": "[DRY RUN — code not executed. Remove --dry-run to execute.]",
        "zh": "[DRY RUN — 代码未执行。去掉 --dry-run 以执行。]",
    },
    "safe_preview.not_executed": {
        "en": "[SAFE PREVIEW] R code was NOT executed. Re-run with --yes to compute the result.",
        "zh": "[安全预览] R 代码未执行。追加 --yes 重新运行以计算结果。]",
    },
    "safe_preview.not_executed_curve": {
        "en": "[SAFE PREVIEW] R code was NOT executed. Re-run with --yes to compute and save the curve.",
        "zh": "[安全预览] R 代码未执行。追加 --yes 重新运行以计算并保存曲线。]",
    },
    "exec.running": {
        "en": "[EXECUTING R CODE...]",
        "zh": "[正在执行 R 代码...]",
    },
    "info.r_code_shown_default": {
        "en": "[INFO] R code is shown by default in preview mode. Re-run with --show-code while using --yes to also display it during execution.",
        "zh": "[提示] 预览模式默认展示 R 代码。执行时追加 --show-code 可同时查看代码。]",
    },
    "info.r_not_detected_python_fallback": {
        "en": "[INFO] R not detected -> using built-in pure-Python Monte-Carlo fallback (scripts/adaptive_simulator.py).",
        "zh": "[提示] 未检测到 R → 改用内置纯 Python 蒙特卡洛备用引擎 (scripts/adaptive_simulator.py)。]",
    },
    "info.result_saved": {
        "en": "Result JSON saved to: {path}",
        "zh": "结果 JSON 已保存至：{path}",
    },
    "info.png_saved": {
        "en": "PNG saved to: {path}",
        "zh": "PNG 已保存至：{path}",
    },

    # ── Errors / 错误 ──
    "error.rscript_not_found": {
        "en": "[ERROR] Rscript not found or invalid. Set RSCRIPT_PATH env or install R.",
        "zh": "[错误] 未找到 Rscript 或路径无效。请设置 RSCRIPT_PATH 环境变量或安装 R。",
    },
    "error.invalid_temp_path": {
        "en": "[ERROR] Invalid temp path; execution refused.",
        "zh": "[错误] 临时路径无效；执行已拒绝。]",
    },
    "error.r_timeout": {
        "en": "[ERROR] R execution timed out (300s limit)",
        "zh": "[错误] R 执行超时（300 秒限制）]",
    },
    "error.exec_failed": {
        "en": "[ERROR] Execution failed: {name}",
        "zh": "[错误] 执行失败：{name}",
    },
    "error.invalid_install_path": {
        "en": "[ERROR] Invalid install script path; execution refused.",
        "zh": "[错误] 安装脚本路径无效；执行已拒绝。]",
    },
    "error.rscript_not_found_install": {
        "en": "[ERROR] Rscript not found or invalid. Is R installed?",
        "zh": "[错误] 未找到 Rscript 或路径无效。是否已安装 R？]",
    },
    "error.test_required": {
        "en": "--test is required (unless using --install-all-packages)",
        "zh": "--test 为必选参数（--install-all-packages 除外）",
    },
    "error.generic": {
        "en": "ERROR: {msg}",
        "zh": "错误：{msg}",
    },
    "error.val_err": {
        "en": "ERROR: {msg}",
        "zh": "错误：{msg}",
    },
    "error.unknown_test": {
        "en": "ERROR: Unknown test type",
        "zh": "错误：未知的检验类型",
    },
    "error.effect_name_required": {
        "en": "ERROR: --effect_name required",
        "zh": "错误：--effect_name 为必填参数",
    },
    "error.effect_name_invalid": {
        "en": "ERROR: --effect_name must be a valid R identifier",
        "zh": "错误：--effect_name 必须是合法的 R 标识符",
    },
    "error.auc1_or_effect_required": {
        "en": "ERROR: --auc1 or --effect required",
        "zh": "错误：--auc1 或 --effect 为必填参数",
    },
    "error.design_must_be_one_of": {
        "en": "ERROR: --design must be one of: {options}",
        "zh": "错误：--design 必须是以下之一：{options}",
    },
    "error.spending_func_must_be_one_of": {
        "en": "ERROR: --spending_func must be one of: {options}",
        "zh": "错误：--spending_func 必须是以下之一：{options}",
    },
    "error.adaptive_type_must_be_one_of": {
        "en": "ERROR: --adaptive_type must be one of: {options}",
        "zh": "错误：--adaptive_type 必须是以下之一：{options}",
    },
    "error.curve_not_supported": {
        "en": "ERROR: curve mode (--n_seq / --power_seq) is not yet supported for --test '{test}'.",
        "zh": "错误：曲线模式 (--n_seq / --power_seq) 暂不支持 --test '{test}'。",
    },
    "error.curve_supported_types": {
        "en": "Supported test types for curves:",
        "zh": "曲线模式支持的检验类型：",
    },
    "error.curve_param_missing": {
        "en": "ERROR: parameter missing/invalid for curve of '{test}': {err}",
        "zh": "错误：'{test}' 曲线参数缺失或无效：{err}",
    },
    "error.curve_requires_seq": {
        "en": "ERROR: curve mode requires --n_seq or --power_seq",
        "zh": "错误：曲线模式需要 --n_seq 或 --power_seq",
    },
    "error.invalid_sequence": {
        "en": "ERROR: invalid sequence spec: {err}",
        "zh": "错误：无效的序列规格：{err}",
    },
    "error.invalid_plot_effects": {
        "en": "ERROR: invalid --plot_effects: {err}",
        "zh": "错误：无效的 --plot_effects：{err}",
    },
    "error.effect_sizes_invalid": {
        "en": "Invalid --effect_sizes {value}: only digits, dots, commas, minus and spaces are allowed.",
        "zh": "无效的 --effect_sizes {value}：仅允许数字、点、逗号、减号和空格。",
    },

    # ── Validation messages / 校验消息 ──
    "validation.failed": {
        "en": "Parameter validation failed:",
        "zh": "参数校验失败：",
    },
    "validation.range_error_gt": {
        "en": "--{label} must be > {bound} (got {val})",
        "zh": "--{label} 必须 > {bound}（当前值 {val}）",
    },
    "validation.range_error_lt": {
        "en": "--{label} must be < {bound} (got {val})",
        "zh": "--{label} 必须 < {bound}（当前值 {val}）",
    },

    # ── Install / CRAN 安装 ──
    "install.cmd_header": {
        "en": "[R package commands — for review only, NOT executed]",
        "zh": "[R 包安装命令 — 仅供审阅，未执行]",
    },
    "install.cran_warning": {
        "en": "This command will download and install {n} R packages from CRAN (the ONLY network operation in this skill).",
        "zh": "此命令会**从 CRAN 联网下载并安装** {n} 个 R 包（即本技能唯一会联网的操作）。",
    },
    "install.confirm_prompt": {
        "en": "If confirmed, re-run with --run-install to actually download:",
        "zh": "如确认无误，请重新运行并追加 --run-install 才会真正联网安装：",
    },
    "install.manual_alt": {
        "en": "Or paste the above command into an R console to install manually.",
        "zh": "或在 R 控制台中手动粘贴上述命令自行安装。",
    },
    "install.network_warning_en": {
        "en": "⚠️  NETWORK INSTALL: the following R code will download packages from CRAN",
        "zh": "⚠️  联网安装：以下 R 代码将从 CRAN 下载并安装 R 包（供应链风险由你知情触发）",
    },
    "install.code_header": {
        "en": "[R CODE — will be executed by Rscript]",
        "zh": "[R 代码 — 将由 Rscript 执行]",
    },

    # ── Section headers / 分节标题 ──
    "header.r_code": {
        "en": "[R CODE — generated for this analysis]",
        "zh": "[R 代码 — 本次分析生成]",
    },
    "header.install_cmd": {
        "en": "[R package commands — for review only, NOT executed]",
        "zh": "[R 包安装命令 — 仅供审阅，未执行]",
    },

    # ── Sequence parsing / 序列解析 ──
    "error.seq_format": {
        "en": "auto sequence needs start:step:stop, got {spec}",
        "zh": "自动序列格式为 起始:步长:终止，当前为 {spec}",
    },
    "error.seq_step_nonzero": {
        "en": "step must be non-zero in auto sequence",
        "zh": "步长不能为零",
    },
    "error.seq_empty": {
        "en": "empty sequence: {spec}",
        "zh": "空序列：{spec}",
    },

    # ── Python fallback section headers / 纯 Python 备用引擎分节标题 ──
    "r_header.roc_power": {
        "en": "\n========== ROC Sample Size (Power given N) ==========",
        "zh": "\n========== ROC 样本量 (给定 N 求功效) ==========",
    },
    "r_header.roc_n": {
        "en": "\n========== ROC Sample Size ==========",
        "zh": "\n========== ROC 样本量 ==========",
    },
    "r_header.poisson_power": {
        "en": "\n========== Poisson Rate Comparison (Power given N) ==========",
        "zh": "\n========== Poisson 率比较 (给定 N 求功效) ==========",
    },
    "r_header.poisson_n": {
        "en": "\n========== Poisson Rate Comparison ==========",
        "zh": "\n========== Poisson 率比较 ==========",
    },
    "r_header.cluster_power": {
        "en": "\n========== Cluster-RCT (Power given N) ==========",
        "zh": "\n========== 整群随机对照 (给定 N 求功效) ==========",
    },
    "r_header.cluster_n": {
        "en": "\n========== Cluster-Randomized Design ==========",
        "zh": "\n========== 整群随机设计 ==========",
    },
    "r_header.vaccine_power": {
        "en": "\n========== Vaccine Efficacy (Power given N) ==========",
        "zh": "\n========== 疫苗效力 (给定 N 求功效) ==========",
    },
    "r_header.vaccine_n": {
        "en": "\n========== Vaccine Efficacy ==========",
        "zh": "\n========== 疫苗效力 ==========",
    },
    "r_header.multi_endpoints_power": {
        "en": "\n========== Multiple Endpoints (Power given N) ==========",
        "zh": "\n========== 多终点 (给定 N 求功效) ==========",
    },
    "r_header.multi_endpoints_n": {
        "en": "\n========== Multiple Endpoints ==========",
        "zh": "\n========== 多终点 ==========",
    },
    "r_header.ttest_ind_power": {
        "en": "\n========== Two-Sample T-Test (Power given N) ==========",
        "zh": "\n========== 两样本 T 检验 (给定 N 求功效) ==========",
    },
    "r_header.ttest_ind_n": {
        "en": "\n========== Two-Sample T-Test ==========",
        "zh": "\n========== 两样本 T 检验 ==========",
    },
    "r_header.ttest_paired_power": {
        "en": "\n========== Paired T-Test (Power given N) ==========",
        "zh": "\n========== 配对 T 检验 (给定 N 求功效) ==========",
    },
    "r_header.ttest_paired_n": {
        "en": "\n========== Paired T-Test ==========",
        "zh": "\n========== 配对 T 检验 ==========",
    },
    "r_header.ttest_one_power": {
        "en": "\n========== One-Sample T-Test (Power given N) ==========",
        "zh": "\n========== 单样本 T 检验 (给定 N 求功效) ==========",
    },
    "r_header.ttest_one_n": {
        "en": "\n========== One-Sample T-Test ==========",
        "zh": "\n========== 单样本 T 检验 ==========",
    },
    "r_header.anova_power": {
        "en": "\n========== One-Way ANOVA (Power given N) ==========",
        "zh": "\n========== 单因素方差分析 (给定 N 求功效) ==========",
    },
    "r_header.anova_n": {
        "en": "\n========== One-Way ANOVA ==========",
        "zh": "\n========== 单因素方差分析 ==========",
    },
    "r_header.prop_one_power": {
        "en": "\n========== One-Sample Proportion Test (Power given N) ==========",
        "zh": "\n========== 单组率检验 (给定 N 求功效) ==========",
    },
    "r_header.prop_one_n": {
        "en": "\n========== One-Sample Proportion Test ==========",
        "zh": "\n========== 单组率检验 ==========",
    },
    "r_header.prop_two_power": {
        "en": "\n========== {label} (Power given N) ==========",
        "zh": "\n========== {label} (给定 N 求功效) ==========",
    },
    "r_header.prop_two_n": {
        "en": "\n========== {label} ==========",
        "zh": "\n========== {label} ==========",
    },
    "r_header.ni_prop_power": {
        "en": "\n========== Non-Inferiority (Proportions, Power given N) ==========",
        "zh": "\n========== 非劣效 (率, 给定 N 求功效) ==========",
    },
    "r_header.ni_prop_n": {
        "en": "\n========== Non-Inferiority (Proportions) ==========",
        "zh": "\n========== 非劣效 (率) ==========",
    },
    "r_header.survival_power": {
        "en": "\n========== Survival (Log-Rank, Power given N) ==========",
        "zh": "\n========== 生存分析 (Log-Rank, 给定 N 求功效) ==========",
    },
    "r_header.survival_n": {
        "en": "\n========== Survival (Log-Rank Test) ==========",
        "zh": "\n========== 生存分析 (Log-Rank 检验) ==========",
    },
    "r_header.rank_mantel_power": {
        "en": "\n========== Stratified Log-Rank (Mantel-Cox, Power given N) ==========",
        "zh": "\n=== 分层 Log-Rank (Mantel-Cox, 给定 N 求功效) =========",
    },
    "r_header.rank_mantel_n": {
        "en": "\n========== Stratified Log-Rank Test ==========",
        "zh": "\n========== 分层 Log-Rank 检验 ==========",
    },

    # ── Python fallback labels / 纯 Python 备用引擎标签 ──
    "label.alpha": {"en": "Alpha:", "zh": "Alpha:"},
    "label.power": {"en": "Power:", "zh": "Power:"},
    "label.achieved_power": {"en": "Achieved power:", "zh": "达成功效:"},
    "label.h0_auc": {"en": "H0 AUC:", "zh": "H0 AUC:"},
    "label.h1_auc": {"en": "H1 AUC:", "zh": "H1 AUC:"},
    "label.sample_size": {"en": "Sample size:", "zh": "样本量:"},
    "label.rate_ratio": {"en": "Rate Ratio:", "zh": "率比:"},
    "label.sample_size_per_group": {"en": "Sample size per group:", "zh": "每组样本量:"},
    "label.deff": {"en": "Design effect (DEFF):", "zh": "设计效应 (DEFF):"},
    "label.cluster_size_m": {"en": "Cluster size m:", "zh": "群组大小 m:"},
    "label.icc": {"en": "ICC:", "zh": "ICC:"},
    "label.total_sample_size": {"en": "Total sample size:", "zh": "总样本量:"},
    "label.effective_n_per_group": {"en": "Effective individual n per group (n_total/2/DEFF):", "zh": "有效个体 n 每组 (总 n/2/DEFF):"},
    "label.implied_n_clusters": {"en": "Implied n clusters per group:", "zh": "隐含群组数 (每组):"},
    "label.adjusted_n_per_group": {"en": "Adjusted n per group:", "zh": "调整后每组 n:"},
    "label.clusters_per_group": {"en": "Clusters per group:", "zh": "群组数 (每组):"},
    "label.total_clusters": {"en": "Total:", "zh": "总群组数:"},
    "label.adjusted_total": {"en": "Adjusted total:", "zh": "调整后总样本量:"},
    "label.ve": {"en": "VE:", "zh": "VE:"},
    "label.n_per_group_total": {"en": "n per group:", "zh": "每组 n:"},
    "label.n_per_group": {"en": "n per group:", "zh": "每组 n:"},
    "label.total_n": {"en": "Total N:", "zh": "总 N:"},
    "label.total_n_surv": {"en": "Total N:", "zh": "总 N:"},
    "label.correlation": {"en": "Correlation:", "zh": "相关系数:"},
    "label.adjusted_n": {"en": "Adjusted n:", "zh": "调整后 n:"},
    "label.single_endpoint_n": {"en": "Single endpoint n:", "zh": "单终点 n:"},
    "label.cohens_d": {"en": "Cohen's d:", "zh": "Cohen's d:"},
    "label.n_pairs": {"en": "n (pairs):", "zh": "n (对子数):"},
    "label.n_total": {"en": "n:", "zh": "n:"},
    "label.k_groups": {"en": "k groups:", "zh": "k 组:"},
    "label.f_effect": {"en": "f:", "zh": "f:"},
    "label.h0_proportion": {"en": "H0 proportion (p0):", "zh": "H0 率 (p0):"},
    "label.h1_proportion": {"en": "H1 proportion (p1):", "zh": "H1 率 (p1):"},
    "label.side": {"en": "Side:", "zh": "单/双侧:"},
    "label.given_n": {"en": "Given n:", "zh": "给定 n:"},
    "label.target_power": {"en": "Target power:", "zh": "目标功效:"},
    "label.n_total_result": {"en": "n (total):", "zh": "n (合计):"},
    "label.control_h0": {"en": "Control / H0 (p1):", "zh": "对照组 / H0 (p1):"},
    "label.treatment_h1": {"en": "Treatment / H1 (p2):", "zh": "处理组 / H1 (p2):"},
    "label.given_n_per_group": {"en": "Given n per group:", "zh": "给定每组 n:"},
    "label.control_rate_ni": {"en": "对照组有效率 p1:", "zh": "对照组有效率 p1:"},
    "label.treatment_rate_ni": {"en": "试验组有效率 p2:", "zh": "试验组有效率 p2:"},
    "label.ni_margin": {"en": "非劣效界值 delta:", "zh": "非劣效界值 delta:"},
    "label.total_n_ni": {"en": "总样本量 N:", "zh": "总样本量 N:"},
    "label.each_group": {"en": "每组:", "zh": "每组:"},
    "label.control_rate_ni_short": {"en": "对照组有效率 p1: {p1}", "zh": "对照组有效率 p1: {p1}"},
    "label.treatment_rate_ni_short": {"en": "试验组有效率 p2: {p2}", "zh": "试验组有效率 p2: {p2}"},
    "label.assumed_diff": {"en": "假设真实差异 |p1-p2|: ", "zh": "假设真实差异 |p1-p2|: "},
    "label.ni_margin_short": {"en": "非劣效界值 delta: {margin}", "zh": "非劣效界值 delta: {margin}"},
    "label.one_sided_alpha": {"en": "单侧 α: {alpha}, 把握度: {power}, 1:1 分配", "zh": "单侧 α: {alpha}, 把握度: {power}, 1:1 分配"},
    "label.result_header": {"en": "--- 结果 ---", "zh": "--- 结果 ---"},
    "label.n_per_arm": {"en": "每组样本量 n1:", "zh": "每组样本量 n1:"},
    "label.total_sample_size_result": {"en": "总样本量 N:", "zh": "总样本量 N:"},
    "label.with_dropout": {"en": "含 10% 脱落率:", "zh": "含 10% 脱落率:"},
    "label.hazard_ratio_surv": {"en": "Hazard ratio:", "zh": "风险比:"},
    "label.total_events": {"en": "Total events:", "zh": "总事件数:"},
    "label.approx_n_per_group_surv": {"en": "Approx n per group (event_rate={event_rate}):", "zh": "近似每组 n (event_rate={event_rate}):"},
    "label.hr_format": {"en": "Hazard ratio: {hr}", "zh": "风险比: {hr}"},
    "label.total_events_needed": {"en": "Total events needed (Schoenfeld):", "zh": "所需总事件数 (Schoenfeld):"},
    "label.each_group_n": {"en": "Each group n:", "zh": "每组 n:"},
    "label.dropout_note": {"en": "\n含10%脱落率:", "zh": "\n含10%脱落率:"},
    "label.dropout_note_inline": {"en": "含10%脱落率:", "zh": "含10%脱落率:"},
    "label.survival_note": {"en": "\n注意: 当前仅计算所需事件数。如需样本量请提供参数", "zh": "\n注意: 当前仅计算所需事件数。如需样本量请提供参数"},

    # ── adaptive_simulator.py ──
    "header.adaptive_sim": {
        "en": "ADAPTIVE TRIAL SIMULATION",
        "zh": "自适应试验仿真",
    },
    "error.matplotlib_unavailable": {
        "en": "[WARN] matplotlib unavailable, skipped visualization: {msg}",
        "zh": "[警告] matplotlib 不可用，已跳过可视化：{msg}",
    },
}


def t(key, **kwargs):
    """Translate a message key to the current locale.

    Args:
        key: message identifier in _MESSAGES
        **kwargs: format placeholders (e.g., path="/tmp/x.json")

    Returns:
        Localized string. Falls back to the key itself if not found.
    """
    lang = _current_lang()
    entry = _MESSAGES.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("en", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# Back-compatible alias
_ = t

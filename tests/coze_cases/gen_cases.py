#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/coze_cases 用例库生成器（可复现）。

输出：tests/coze_cases/cases/<id>.json —— 每个文件对应一个（或一组）test 的请求/响应契约基线。
回归脚本 tests/coze_cases_regression.py 读取这些文件，离线断言本地请求信封契约。

字段：
  id                用例唯一 id
  test              对应 --test
  desc              人类可读描述
  nl                （可选）自然语言来源，仅作溯源；显式 cli 才是执行依据
  cli               传给 build_parser 的 CLI 参数列表（同真实调用）
  expect.mode       "n"（求样本量，默认）或 "power"（给定 nobs 求效能）
  expect.must_include_params  必须出现在请求信封 params 中且非 None 的键
  expect.forbidden_params     必须【不】出现在 params 中的键（控制标志/顶层字段不外泄）
"""
from __future__ import annotations
import os, json

CASES = [
    dict(id="ttest_ind_n", test="ttest_ind", desc="两样本t检验求n",
         cli=["--test","ttest_ind","--effect","0.5","--power","0.8"],
         expect=dict(mode="n", must_include_params=["effect","alpha","side"], forbidden_params=["test","yes","dry_run"])),
    dict(id="ttest_ind_reverse", test="ttest_ind", desc="两样本t检验给定n求power",
         cli=["--test","ttest_ind","--effect","0.5","--nobs","30"],
         expect=dict(mode="power", must_include_params=["nobs","effect"], forbidden_params=["test"])),
    dict(id="proportion_two", test="proportion_two", desc="两组率比较求n",
         cli=["--test","proportion_two","--p1","0.7","--p2","0.5","--power","0.8"],
         expect=dict(mode="n", must_include_params=["p1","p2","alpha"], forbidden_params=["test"])),
    dict(id="non_inferiority", test="non_inferiority", desc="率的非劣效检验求n",
         cli=["--test","non_inferiority","--p1","0.6","--p2","0.6","--margin","0.1","--power","0.8"],
         expect=dict(mode="n", must_include_params=["margin","p1","p2"], forbidden_params=["test"])),
    dict(id="ni_survival", test="ni_survival", desc="非劣效生存（NL派生）",
         nl="非劣效生存试验，NI界值1.25，期望HR=1.0，入组12月随访12月",
         cli=["--test","ni_survival","--ni_margin_surv","1.25","--hr_expected","1.0","--accrual_time","12","--followup_time","12"],
         expect=dict(mode="n", must_include_params=["ni_margin_surv","hr_expected","accrual_time","followup_time"], forbidden_params=["test"])),
    dict(id="survival", test="survival", desc="logrank生存分析求n",
         cli=["--test","survival","--hazard_ratio","0.7","--power","0.9"],
         expect=dict(mode="n", must_include_params=["hazard_ratio","alpha"], forbidden_params=["test"])),
    dict(id="be_tost", test="be_tost", desc="生物等效TOST求n",
         cli=["--test","be_tost","--theta0","0.95","--cv","0.25","--design","2x2","--power","0.8"],
         expect=dict(mode="n", must_include_params=["theta0","cv","design"], forbidden_params=["test"])),
    dict(id="roc", test="roc", desc="ROC/AUC诊断试验求n",
         cli=["--test","roc","--auc0","0.5","--auc1","0.7","--power","0.8"],
         expect=dict(mode="n", must_include_params=["auc0","auc1"], forbidden_params=["test"])),
    dict(id="cluster", test="cluster", desc="整群随机求n",
         cli=["--test","cluster","--m","20","--icc","0.05","--n_indiv","30","--power","0.8"],
         expect=dict(mode="n", must_include_params=["m","icc","n_indiv"], forbidden_params=["test"])),
    dict(id="group_sequential", test="group_sequential", desc="成组序贯均值求n",
         cli=["--test","group_sequential","--effect_gs","0.4","--spending_func","OF","--n_interim","1","--power","0.8"],
         expect=dict(mode="n", must_include_params=["effect_gs","spending_func","n_interim"], forbidden_params=["test"])),
    dict(id="bayesian", test="bayesian", desc="贝叶斯先验 informed 求n",
         cli=["--test","bayesian","--prob_control","0.3","--prob_treatment","0.15","--power","0.8"],
         expect=dict(mode="n", must_include_params=["prob_control","prob_treatment"], forbidden_params=["test"])),
    dict(id="vaccine_efficacy", test="vaccine_efficacy", desc="疫苗效力VE求n",
         cli=["--test","vaccine_efficacy","--ve_control","0.02","--ve_treatment","0.005","--power","0.8"],
         expect=dict(mode="n", must_include_params=["ve_control","ve_treatment"], forbidden_params=["test"])),
    dict(id="gsd_proportion", test="gsd_proportion", desc="成组序贯两比例求n",
         cli=["--test","gsd_proportion","--p1","0.7","--p2","0.5","--gs_proportion_metric","difference","--spending_func","OF","--n_interim","1","--power","0.8"],
         expect=dict(mode="n", must_include_params=["p1","p2","gs_proportion_metric","spending_func","n_interim"], forbidden_params=["test"])),
    dict(id="adaptive_simulate", test="adaptive_simulate", desc="适应性蒙特卡洛仿真求n",
         cli=["--test","adaptive_simulate","--sim_design","group_sequential","--effect_size","0.3","--interim_looks","2","--spending_function","obrien_fleming","--sim_n","100","--power","0.8"],
         expect=dict(mode="n", must_include_params=["sim_design","effect_size","interim_looks"], forbidden_params=["test"])),
    dict(id="conditional_power", test="conditional_power", desc="条件功效（给定n求CP）",
         cli=["--test","conditional_power","--observed_effect","0.2","--planned_effect","0.3","--n_completed","100","--n_planned","200","--timing","0.5","--alpha","0.05"],
         expect=dict(mode="n", must_include_params=["observed_effect","planned_effect","n_completed","n_planned","timing"], forbidden_params=["test"])),
    dict(id="proportion_two_nl", test="proportion_two", desc="两组率比较（NL派生,单侧）",
         nl="比较两种药的有效率，试验组70%，对照组50%，把握度80%，单侧",
         cli=["--test","proportion_two","--p1","0.7","--p2","0.5","--power","0.8","--side","one"],
         expect=dict(mode="n", must_include_params=["p1","p2","side"], forbidden_params=["test"])),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "cases")
    os.makedirs(out_dir, exist_ok=True)
    for c in CASES:
        path = os.path.join(out_dir, "%s.json" % c["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=2)
    print("wrote %d case files to %s" % (len(CASES), out_dir))


if __name__ == "__main__":
    main()

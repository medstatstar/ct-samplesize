# Data Format Guide / 数据输入格式指南

> This guide takes the "what data do you need to prepare" angle and gives a friendly input framework for each of the 37 test types. / 本指南按"你需要准备什么数据"的角度，为 37 种检验类型分别给出友好的输入框架。
> Each type includes: a **parameter table to fill in** + **a real example** + **data-source hints**. / 每个类型都包含：**需要填写的参数表** + **实际例子** + **数据来源提示**。

---

## 📌 General Parameters (all types) / 通用参数（所有类型都需要）

| Param 参数 | Description 说明 | Default 默认 | Example 示例 |
|:-----|:-----|:-----|:---------|
| `α` (alpha) | Significance level, two-sided / 显著性水平，双侧 | 0.05 | 0.05 |
| `Power` | Test power / 检验效能 | 0.8 | 0.8 / 0.85 / 0.9 |
| `--show-code` | Execute & show R code / 执行并展示 R 代码 | Execute only by default, code hidden / 默认仅执行不展示 | Hidden by default; add `--show-code` to show / 默认隐藏代码，加 `--show-code` 才展示 |

---

## 一、连续变量 (Continuous)

### 1. `ttest_ind` — 两独立样本 t 检验

**你需要提供：**

| 参数 | 必填 | 说明 | 怎么得来 |
|:-----|:-----|:-----|:---------|
| `--effect` | ✅ | Cohen's d（标准化均值差） | 文献 / 预试验：(μ₁ - μ₂) / σ |
| `--alpha` | 可选 | 显著性水平 | 默认 0.05 |
| `--power` | 可选 | 检验效能 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test ttest_ind --effect 0.5 --power 0.8 -y
```

**数据来源提示：**
- 有预试验数据 → Cohen's d = (Mean₁ - Mean₂) / SD_pooled
- 无预试验 → 参考 Cohen 标准：小=0.2, 中=0.5, 大=0.8
- 有文献 → 直接引用文献报告的 d 值

---

### 2. `ttest_paired` — 配对 t 检验 / 2×2 交叉设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--effect` | ✅ | 配对差异的 Cohen's d = 差值的均值 / 差值的 SD |
| `--alpha` | 可选 | 默认 0.05 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test ttest_paired --effect 0.4 --power 0.85 -y
```

**数据来源提示：**
- 交叉设计：同一个体两次测量的差值
- 配对设计：基线 vs 治疗后

---

### 3. `anova` — 多组比较

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--effect` | ✅ | Cohen's f（方差分析的效应量） |
| `--k_groups` | 可选 | 组数，默认 2 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test anova --effect 0.25 --k_groups 3 --power 0.8 -y
```

**Cohen's f 参考：** 小=0.1, 中=0.25, 大=0.4

---

### 4. `equivalence` — 等效性检验（均数）

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--margin` | ✅ | 等效性界值 δ（两组均值差的最大允许值） |
| `--effect` | ✅ | 标准差 σ |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test equivalence --margin 2.0 --effect 3.0 --power 0.8 -y
```

**数据来源提示：**
- 等效性界值：临床认为无临床意义的最大差异
- 标准差：文献或预试验估计

---

### 5. `mixed_model` — 重复测量 / 纵向数据

**在 R 中直接调用 `simr`，建议提供以下信息让我帮你写脚本：**

| 信息 | 说明 |
|:-----|:-----|
| 固定效应 (β) | 截距、处理效应、时间效应 |
| 随机效应 VarCorr | 随机截距方差 |
| 残差 SD (σ) | |
| 效应量名称 | 如 "treatment_effect" |

**CLI 快速测试：**
```bash
python scripts/samplesize_power.py --test mixed_model --effect 0.5 --nsim 500 -y
```

---

## 二、二分类变量 (Binary)

### 6. `proportion_one` — 单组率检验

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--p1` | ✅ | 对照组率/比例 |
| `--power` | 可选 | 默认 0.8 |

---

### 7. `proportion_two` — 两组率比较

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--p1` | ✅ | 对照组率 |
| `--p2` | ✅ | 试验组率 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test proportion_two --p1 0.3 --p2 0.15 --power 0.8 -y
```

**数据来源提示：**
- 对照组率：历史数据或文献
- 试验组率：预期达到的疗效

---

### 8. `non_inferiority` — 非劣效设计（率）

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--p1` | ✅ | 对照组率 |
| `--p2` | ✅ | 试验组率 |
| `--margin` | ✅ | 非劣效界值 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test non_inferiority --p1 0.85 --p2 0.80 --margin 0.1 --power 0.8 -y
```

---

### 9. `superiority_margin` — 优效界值设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--sup_margin` | ✅ | 优效性界值 δ |
| `--p_control_sup` | ✅ | 对照组率 |
| `--delta_sup` | ✅ | 真实预期差异 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test superiority_margin --sup_margin 0.05 --p_control_sup 0.3 --delta_sup 0.15 -y
```

---

### 10. `be_tost` — 生物等效性 (TOST)

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--theta0` | ✅ | 预期几何均值比（T/R），如 0.95 |
| `--cv` | ✅ | 变异系数（CV），如 0.25 |
| `--design` | 可选 | 设计类型，默认 "2x2" |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test be_tost --theta0 0.95 --cv 0.25 --design "2x2" -y
```

**可选 design:** "2x2", "2x4", "3x3", "2x2x2", "2x2x3", "2x2x4"

---

## 三、计数 / 事件率 (Count)

### 11. `poisson` — Poisson 率比较

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--lambda1` | ✅ | 试验组发生率 |
| `--lambda2` | ✅ | 对照组发生率 |
| `--t1` | 可选 | 试验组随访时间，默认 1.0 |
| `--t2` | 可选 | 对照组随访时间，默认 1.0 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test poisson --lambda1 0.05 --lambda2 0.03 --t1 2 --t2 2 -y
```

---

### 12. `vaccine_efficacy` — 疫苗效力

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--ve_control` | ✅ | 对照组发病率 (ARU) |
| `--ve_treatment` | ✅ | 疫苗组发病率 (ARV) |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test vaccine_efficacy --ve_control 0.02 --ve_treatment 0.005 -y
```

---

## 四、Time-to-Event 生存 (Survival)

### 13. `survival` — 生存分析（简化）

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--hazard_ratio` | ✅ | 风险比 (HR)，如 0.75 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test survival --hazard_ratio 0.75 --power 0.85 -y
```

---

### 14. `survival_exact` — 生存分析（精确建模）

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--hr_exact` | ✅ | 风险比 HR，如 0.75 |
| `--accrual_exact` | ✅ | 招募时间（月） |
| `--followup_exact` | ✅ | 随访时间（月） |
| `--event_rate_exact` | 可选 | 事件率，默认 0.3 |
| `--dropout_exact` | 可选 | 年失访率，默认 0.05 |

**示例：**
```bash
python scripts/samplesize_power.py --test survival_exact --hr_exact 0.75 --accrual_exact 12 --followup_exact 12 -y
```

---

### 15. `ni_survival` — 非劣效生存设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--ni_margin_surv` | ✅ | 非劣效界值（HR），如 1.25 |
| `--hr_expected` | 可选 | 预期真实 HR，默认 1.0 |
| `--accrual_time` | 可选 | 招募时间（月），默认 12 |
| `--followup_time` | 可选 | 随访时间（月），默认 12 |
| `--event_rate` | 可选 | 对照组事件率，默认 0.3 |

**示例：**
```bash
python scripts/samplesize_power.py --test ni_survival --ni_margin_surv 1.25 --accrual_time 12 --followup_time 12 -y
```

---

## 五、诊断 / 方法学 (Diagnostic)

### 16. `roc` — ROC 曲线 / 诊断试验

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--auc1` | ✅ | 预期 AUC（试验组），如 0.75 |
| `--auc0` | 可选 | H0 AUC（默认 0.5） |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test roc --auc0 0.5 --auc1 0.75 -y
```

---

### 17. `bland_altman` — Bland-Altman 方法学比对

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--sd_diff` | ✅ | 差值的标准差 |
| `--w` | ✅ | LoA 置信区间允许的半宽度 |
| `--alpha` | 可选 | 默认 0.05 |

**示例：**
```bash
python scripts/samplesize_power.py --test bland_altman --sd_diff 5 --w 2.5 -y
```

---

## 六、特殊设计 (Special Designs)

### 18. `cluster` — 类随机设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--icc` | ✅ | 组内相关系数 (ICC)，如 0.05 |
| `--m` | ✅ | 每 cluster 人数，如 30 |
| `--n_indiv` | ✅ | 个体样本量（未调整前） |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test cluster --icc 0.05 --m 30 --n_indiv 64 -y
```

---

### 19. `multiple_endpoints` — 多终点 / 复合终点

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--correlation` | ✅ | 终点间相关系数 ρ |
| `--effect` | ✅ | 每个终点的 Cohen's d |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test multiple_endpoints --effect 0.3 --correlation 0.5 -y
```

---

### 20. `bayesian` — 贝叶斯设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--prob_control` | ✅ | 对照组率 |
| `--prob_treatment` | ✅ | 试验组率 |
| `--prior_a0` | 可选 | 历史数据借用权重，默认 0.5 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test bayesian --prob_control 0.3 --prob_treatment 0.15 --prior_a0 0.5 -y
```

---

### 21. `dose_escalation` — 剂量递增 (I期)

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--n_doses` | 可选 | 剂量水平数，默认 5 |
| `--target_dlt` | 可选 | 目标 DLT 率，默认 0.33 |

**示例：**
```bash
python scripts/samplesize_power.py --test dose_escalation --n_doses 5 --target_dlt 0.33 -y
```

---

## 七、高级终点 (Advanced Endpoints, v3.3 新增)

### 22. `win_ratio` — Win-Ratio 复合终点

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--win_ratio_theta` | ✅ | 预期 Win-Ratio，如 1.5 |
| `--n_sim` | 可选 | 模拟次数，默认 1000 |

**示例：**
```bash
python scripts/samplesize_power.py --test win_ratio --win_ratio_theta 1.5 --n_sim 1000 -y
```

---

### 23. `must_win` — Must-Win / 共主要终点

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--n_endpoints_must` | ✅ | 共主要终点数（2-5），如 3 |
| `--effect_must` | ✅ | 每个终点的 Cohen's d |
| `--correlation_must` | ✅ | 终点间相关系数 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test must_win --n_endpoints_must 3 --effect_must 0.3 --correlation_must 0.5 -y
```

---

### 24. `historical_controls` — 历史对照借用

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--historical_response` | ✅ | 历史对照应答人数，如 15 |
| `--historical_n` | ✅ | 历史对照总人数，如 100 |
| `--a0_borrowing` | 可选 | 借用权重（0-1），默认 0.5 |
| `--p_control_current` | 可选 | 当前对照组率，默认 0.3 |
| `--prob_treatment` | ✅ | 试验组率，默认 0.15 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test historical_controls --historical_response 15 --historical_n 100 --a0_borrowing 0.5 --prob_treatment 0.15 -y
```

---

### 25. `mams` — 多臂多阶段 (MAMS)

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--n_arms_mams` | ✅ | 治疗臂数（不含对照），如 3 |
| `--n_stages_mams` | ✅ | 阶段数，如 2 |
| `--delta_effect` | ✅ | 每个臂的效应量 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test mams --n_arms_mams 3 --n_stages_mams 2 --delta_effect 0.3 -y
```

---

### 26. `conditional_power` — 条件效能 / SSR

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--timing` | ✅ | 期中分析时机（0-1），如 0.5 |
| `--observed_effect` | ✅ | 中期观察到的效应量 |
| `--planned_effect` | ✅ | 计划时的预期效应量 |
| `--n_completed` | 当前已完成样本量 | 默认 100 |
| `--n_planned` | ✅ | 计划总样本量，默认 200 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test conditional_power --timing 0.5 --observed_effect 0.2 --planned_effect 0.3 -y
```

---

### 27. `superiority_margin` — 优效界值（已在 Binary 中列出）

---

### 28. `assurance` — 贝叶斯确信度

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--shape1_trt` | ✅ | 试验组先验 Beta 分布参数 α，如 3 |
| `--shape2_trt` | ✅ | 试验组先验 Beta 分布参数 β，如 7 |
| `--shape1_ctrl` | ✅ | 对照组先验 Beta 分布参数 α，如 3 |
| `--shape2_ctrl` | ✅ | 对照组先验 Beta 分布参数 β，如 7 |
| `--n_assurance` | ✅ | 评估的样本量，如 100 |
| `--n_sim_assurance` | 可选 | 模拟次数，默认 5000 |

**示例：**
```bash
python scripts/samplesize_power.py --test assurance --shape1_trt 3 --shape2_trt 7 --shape1_ctrl 3 --shape2_ctrl 7 --n_assurance 100 -y
```

---

### 29. `dunnett` — Dunnett 多重比较

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--n_groups_dunnett` | ✅ | 治疗臂数（不含对照），如 3 |
| `--n_control_dunnett` | ✅ | 对照组样本量，如 50 |
| `--effect_dunnett` | ✅ | 效应量 Cohen's d |

**示例：**
```bash
python scripts/samplesize_power.py --test dunnett --n_groups_dunnett 3 --n_control_dunnett 50 --effect_dunnett 0.4 -y
```

---

### 30. `mediation` — 中介效应

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--a_path` | ✅ | a-path 系数（治疗→中介），如 0.3 |
| `--b_path` | ✅ | b-path 系数（中介→结局），如 0.3 |
| `--sigma2_m` | 可选 | 中介变量方差，默认 1.0 |
| `--sigma2_y` | 可选 | 结局变量方差，默认 1.0 |
| `--power` | 可选 | 默认 0.8 |

**示例：**
```bash
python scripts/samplesize_power.py --test mediation --a_path 0.3 --b_path 0.3 -y
```

---

### 31. `group_sequential` — 组序贯设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--n_interim` | ✅ | 期中分析次数，如 1 |
| `--effect_gs` | ✅ | 效应量 Cohen's d |
| `--spending_func` | 可选 | "OF"(默认) / "Pocock" / "WT" |

**示例：**
```bash
python scripts/samplesize_power.py --test group_sequential --n_interim 1 --effect_gs 0.4 -y
```

---

### 32. `adaptive` — 适应性设计

**你需要提供：**

| 参数 | 必填 | 说明 |
|:-----|:-----|:-----|
| `--n_stages_adapt` | ✅ | 阶段数，如 2 |
| `--effect_adaptive` | ✅ | 效应量 Cohen's d |
| `--adaptive_type` | 可选 | "SSR"(默认) / "Population" / "Combination" |

**示例：**
```bash
python scripts/samplesize_power.py --test adaptive --n_stages_adapt 2 --effect_adaptive 0.4 -y
```

---

## 八、脱落调整

所有类型都支持脱落率调整。计算完成后，手动计算：

```
调整后 N = ceiling(N_calculated / (1 - dropout_rate))
```

**示例：** 计算得 N=100/组，脱落率 10% → 调整后 N = ceiling(100 / 0.9) = 112/组

---

## 快速选择指南

```
你的主要终点是什么？
├── 连续变量 → ttest_ind / ttest_paired / anova / mixed_model
├── 二分类 → proportion_two / non_inferiority / superiority_margin
├── 生存 → survival / survival_exact / ni_survival
├── 诊断 → roc / bland_altman
├── 疫苗 → vaccine_efficacy
├── I期剂量探索 → dose_escalation
├── 复杂设计 → group_sequential / adaptive / mams / conditional_power
├── 多终点 → must_win / multiple_endpoints
├── 生物等效性 → be_tost
└── 其他 → win_ratio / historical_controls / assurance / dunnett / mediation
```

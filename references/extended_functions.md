# Extended Functions Reference / 扩展功能参考

> v4.0 additions: Win-Ratio, Must-Win/Co-Primary, Historical Controls, MAMS, Conditional Power/SSR, NI Survival, Superiority Margin, Assurance, Dunnett, Mediation, Survival Exact

---

## 混合效应模型 (Mixed Model Power) — `simr`

### Clinical Use / 临床场景
- **重复测量**（同一受试者多次随访：基线、3月、6月、12月）
- **多中心试验**（中心作为随机效应）
- **阶梯式设计**（Cluster-level intervention with individual outcomes）
- **纵向数据**（肿瘤大小随时间变化、血糖控制轨迹）

### R 代码
```r
library(simr); library(lme4)
set.seed(42)

# 预试验参数
beta <- c(5.0, -0.8)        # 固定效应:截距=5, 处理效应=-0.8
V1   <- 0.5                 # 随机截距方差
sigma <- 1.0                # 残差标准差

# 数据框架
n_subjects <- 20
n_treatment <- 10
df <- expand.grid(time = c(0, 3, 6, 12), subject = seq_len(n_subjects))
df$treatment <- ifelse(df$subject <= n_treatment, "active", "placebo")

# 构建模型
model <- makeLmer(y ~ treatment * time + (1|subject),
                  fixef = beta, VarCorr = V1, sigma = sigma, data = df)

# 检验效能
result <- powerSim(model, nsim = 1000, test = fcompare(y ~ time + (1|subject)))
print(result)

# 样本量曲线
pc <- powerCurve(model, test = fcompare(y ~ time + (1|subject)),
                 along = "subject", breaks = seq(10, 50, 10))
plot(pc)
```

### CLI
```bash
python scripts/samplesize_power.py --test mixed_model --effect 0.5 --nsim 500
```

---

## ROC 曲线 / ROC Curve — `pROC`

### Clinical Use / 临床场景
- **诊断试验**：新标志物 vs. 金标准（AUC从0.5提升至0.75）
- **预测模型**：构建诊断评分系统
- **生物标志物验证**：确定标志物检测所需样本量

### 公式
基于 Obuchowski 方法（AUC方差的二项分布近似）：

$$n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{4(\arcsin\sqrt{AUC_1} - \arcsin\sqrt{AUC_0})^2}$$

### CLI
```bash
python scripts/samplesize_power.py --test roc --auc0 0.5 --auc1 0.75 --power 0.8
```

---

## Poisson 率比较 / Poisson Rate Comparison

### Clinical Use / 临床场景
- **复发性事件**：癫痫发作次数、哮喘急性加重次数、住院次数
- **罕见事件发生率**：特定不良事件发生率比较
- **率比校正**：随访时间不等长时率比校正

### 方法
Wald 检验 + 正态近似法

### CLI
```bash
python scripts/samplesize_power.py --test poisson --lambda1 0.05 --lambda2 0.03 --t1 2 --t2 2 --power 0.8
```

---

## 类随机设计 / Cluster-Randomized Design

### Clinical Use / 临床场景
- **群组随机**：按中心/诊所/学校随机分组
- **Pragmatic Trial**：全科医生随机到干预组，患者为分析单元
- **阶梯式设计 (Stepped Wedge)**：所有cluster逐步引入干预

### 设计效应公式
$$DEFF = 1 + (m - 1) \times ICC$$

### CLI
```bash
python scripts/samplesize_power.py --test cluster --icc 0.05 --m 30 --n_indiv 64
```

---

## Bland-Altman 方法学比对 / Method Comparison

### Clinical Use / 临床场景
- **器械比对**：新型POCT设备 vs. 中心实验室
- **两次测量一致性**：超声 vs. CT 肿瘤测量
- **诊断方法一致性**：同一标本两种试剂盒

### 公式
基于 Lu et al. (2016) 的 LoA 精度法：

$$n = 2 \times \left(\frac{Z_{1-\alpha/2} \times SD_{diff}}{W}\right)^2$$

其中 W 为 LoA 置信区间允许的半宽度。

### CLI
```bash
python scripts/samplesize_power.py --test bland_altman --sd_diff 5 --w 2.5
```

---

## 生物等效性 / Bioequivalence (TOST) — `PowerTOST`

### Clinical Use / 临床场景
- **仿制药申报**：受试制剂 vs. 参比制剂的AUC/Cmax比
- **不同规格**：剂量比例性研究
- **食物影响**: Fed vs. Fasted BE
- **特殊药品**：窄治疗指数药物（NTID）的高阶BE

### R 代码
```r
library(PowerTOST)
sampleN.TOST(theta0 = 0.95, CV = 0.25, design = "2x2", alpha = 0.05, targetpower = 0.8)
```

### CLI
```bash
python scripts/samplesize_power.py --test be_tost --theta0 0.95 --cv 0.25 --design "2x2"
```

---

## 疫苗效力 / Vaccine Efficacy

### Clinical Use / 临床场景
- **传染病预防**：流感、新冠、肺炎球菌等疫苗试验
- **真实世界效果**：疫苗保护效力研究

### 公式
基于 Halloran et al. 的 Poisson 发病率法：

$$VE = \frac{ARU - ARV}{ARU}$$

$$n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2 \times (1/ARU + 1/ARV)}{(\log(1-VE))^2}$$

### CLI
```bash
python scripts/samplesize_power.py --test vaccine_efficacy --ve_control 0.02 --ve_treatment 0.005 --power 0.8
```

---

## 多终点 / Multiple Endpoints

### Clinical Use / 临床场景
- **复合终点**：心血管试验（MACE: 死亡+MI+卒中）
- **共主要终点**：需要同时有效的多个指标
- **关键次要终点**：确证性试验的层级检验

### 方法
- 共主要终点（相关系数法）：$n_{adj} = n_{single} / (1 - \rho)$
- 复合终点：基于事件计数的 rpact 精确法

### CLI
```bash
python scripts/samplesize_power.py --test multiple_endpoints --effect 0.3 --correlation 0.5
```

---

## 贝叶斯设计 / Bayesian Design — `BayesCTDesign`

### Clinical Use / 临床场景
- **I/II期肿瘤试验**：小样本+历史对照数据借用
- **罕见病试验**：需要整合历史对照
- **适应性设计**：基于后验概率动态调整

### 方法
- `BayesCTDesign::simple_sim()` 蒙特卡洛模拟
- 历史对照权重 a0（0=完全独立，1=完全借用）
- 后验概率 P(效应>margin | data) > 阈值

### CLI
```bash
python scripts/samplesize_power.py --test bayesian --prob_control 0.3 --prob_treatment 0.15 --prior_a0 0.5
```

---

## 剂量递增 / Dose Escalation — `escalation`

### Clinical Use / 临床场景
- **I期肿瘤试验**：首次人体试验剂量探索
- **BOIN/CRM/METHIT** 等现代设计

### 3+3 设计方案
| DLT 数 | 决策 |
|:-------|:-----|
| 0/3    | 升至下一剂量 |
| 1/3    | 再入组3人 |
| 1/6    | 升至下一剂量 |
| ≥2/6   | 前一剂量为 MTD |

### CLI
```bash
python scripts/samplesize_power.py --test dose_escalation --n_doses 5 --target_dlt 0.33
```

---

## Win-Ratio 复合终点 / Win-Ratio Composite Endpoint — `BuyseTest` 模拟

### Clinical Use / 临床场景
- **心血管复合终点**：将全因死亡、心衰住院、疗效恶化按优先级排序
- **肿瘤试验**：PFS + 主观症状改善
- **非参数终点**：不依赖比例风险假设

### 方法
基于 BuyseTest 的优先化 win-ratio 方法：
- 对每个受试者对，按优先级比较直至出现优胜者
- Win-Ratio = 优胜次数 / 落败次数
- 样本量通过 log(WR) 的 SE 近似反推

### 公式（近似）
$$n = \frac{(Z_{1-\alpha/2} + Z_{1-\beta})^2}{(\ln WR)^2 / SE_{approx}^2}$$

### CLI
```bash
python scripts/samplesize_power.py --test win_ratio --win_ratio_theta 1.5 --n_sim 1000
```

---

## Must-Win / 共主要终点 — 相关系数法

### Clinical Use / 临床场景
- **共主要终点**：试验必须同时达到所有主要终点才视为成功
- **联合终点**：安全性+有效性双重指标
- **监管要求**：FDA/EMA 要求多终点确证

### 方法
- 假设 k 个共主要终点，相关系数 ρ
- 每个终点独立所需 n 按效应量计算
- 膨胀因子（inflation）= $1 + (k-1) \times \rho \times 0.5$
- 确保整体检验效能达到目标

### CLI
```bash
python scripts/samplesize_power.py --test must_win --n_endpoints_must 3 --effect_must 0.3 --correlation_must 0.5
```

---

## 历史对照借用 / Historical Controls — `RBesT` MAP先验

### Clinical Use / 临床场景
- **罕见病试验**：历史对照信息减少所需样本量
- **儿科试验**：成人数据外推
- **医疗器械**：已有大量历史数据

### 方法
- **MAP (Maximal A Posteriori) 先验**：将历史数据转化为 Beta 先验分布
- **ESS (Effective Sample Size)**：历史数据相当于的当前样本量
- **样本量缩减**：$N_{borrow} = N_{fixed} \times \frac{1}{1 + ESS_{hist}/N_{fixed}}$

### CLI
```bash
python scripts/samplesize_power.py --test historical_controls --historical_response 15 --historical_n 100 --a0_borrowing 0.5
```

---

## 多臂多阶段设计 / MAMS — `rpact`

### Clinical Use / 临床场景
- **多剂量对比**：同时评估多个剂量 vs. 安慰剂
- **平台试验**：多个治疗臂共享对照组
- **阶段淘汰**：中期分析时淘汰无效臂

### 方法
- 使用 O'Brien-Fleming 类消耗函数
- Bonferroni 法校正多重比较（k 个臂 vs 对照组）
- 每阶段样本量递增，最大样本量 > 固定设计

### CLI
```bash
python scripts/samplesize_power.py --test mams --n_arms_mams 3 --n_stages_mams 2 --delta_effect 0.3
```

---

## 条件效能 / 样本量重估计 / Conditional Power & SSR — `rpact`

### Clinical Use / 临床场景
- **期中分析**：基于已观察数据重新评估试验成功概率
- **样本量重估计 (SSR)**：根据中期效应量调整最终样本量
- **无效性终止**：条件效能过低时提前终止

### 方法
- 条件效能 = 给定中期数据时，最终达到显著性的概率
- 样本量重估计因子：$SSR = (planned\_effect / observed\_effect)^2$
- 逆正态法保持类型 I 错误率控制

### CLI
```bash
python scripts/samplesize_power.py --test conditional_power --timing 0.5 --observed_effect 0.2 --planned_effect 0.3
```

---

## 非劣效生存设计 / Non-Inferiority Survival — `powerSurvEpi`

### Clinical Use / 临床场景
- **肿瘤非劣效**：新疗法不劣于标准治疗（HR < 1.25）
- **器械验证**：新型器械不劣于传统手术
- **仿制药品**：仿制药不劣于原研药

### 方法
- 基于指数分布/比例风险假设
- 使用 `powerSurvEpi::powerAnsi()` 函数
- 考虑招募时间、随访时间、失访率

### CLI
```bash
python scripts/samplesize_power.py --test ni_survival --ni_margin_surv 1.25 --accrual_time 12 --followup_time 12
```

---

## 优效界值设计 / Superiority by a Margin

### Clinical Use / 临床场景
- **临床意义最小差异**：效应不仅统计显著，还需超过临床界值
- **器械/药物审批**：需证明效应 > 预定义界值 $\delta$
- **保守设计**：防止统计显著但临床无意义的结果

### 方法
- 假设检验：$H_0: p_T - p_C \leq \delta$ vs $H_1: p_T - p_C > \delta$
- 样本量计算基于真实效应超过界值的部分：$p_T - p_C - \delta$

### CLI
```bash
python scripts/samplesize_power.py --test superiority_margin --sup_margin 0.05 --p_control_sup 0.3 --delta_sup 0.15
```

---

## 贝叶斯确信度 / Bayesian Assurance — Monte Carlo

### Clinical Use / 临床场景
- **试验前决策**：在试验开始前评估成功概率
- **样本量参考**：找到达到目标确信度（如 80%）的样本量
- **风险沟通**：向申办方直观展示试验成功概率

### 方法
- 从先验分布中抽样"真实"参数值
- 模拟 N 次试验，每次从真实参数生成数据
- 计算显著性检验通过后验概率 > 阈值 的比例
- Assurance = 成功次数 / N

### CLI
```bash
python scripts/samplesize_power.py --test assurance --n_assurance 100 --n_sim_assurance 5000
```

---

## Dunnett 多重比较 / Dunnett Comparisons — `MCPAN`

### Clinical Use / 临床场景
- **多剂量 vs 安慰剂**：多个剂量组同时与对照组比较
- **家族错误率控制**：控制所有比较的整体 I 错误率
- **后期分析**：中期分析后继续进行的多个比较

### 方法
- Dunnett 临界值近似：$d_{crit} \approx Z_{1-\alpha/2} + 0.5 \ln(k)$
- 样本量基于校正后的 Z 值
- Bonferroni 法作为 k > 10 时的备用

### CLI
```bash
python scripts/samplesize_power.py --test dunnett --n_groups_dunnett 3 --n_control_dunnett 50 --effect_dunnett 0.4
```

---

## 中介效应 / Mediation Effects — `powerMediation`

### Clinical Use / 临床场景
- **机制研究**：治疗通过某个中间变量（生物标志物）影响结局
- **中介效应检测**：评估生物标志物的中介作用
- **个性化医疗**：识别受益亚组的机制路径

### 方法
- **乘积系数法 (Sobel)**：效应量 = a × b（a: 治疗→中介, b: 中介→结局）
- **Monte Carlo 模拟**：更精确的样本量估计
- `powerMediation::power.powerMediation.v2()` 提供精确计算

### CLI
```bash
python scripts/samplesize_power.py --test mediation --a_path 0.3 --b_path 0.3
```

---

## 组序贯设计 / Group Sequential Design — `gsDesign`

### Clinical Use / 临床场景
- **期中分析**：在试验完成前多次检查显著性
- **提前终止**：疗效明确或无效时提前停止
- **监管要求**：确证性试验通常需要期中分析

### 方法
- **O'Brien-Fleming (OF)**：早期严格，后期宽松
- **Pocock**：各阶段相同临界值
- **消耗函数 (alpha spending)**：灵活调整期中时机
- 膨胀因子：$N_{gs} = N_{fixed} \times IF$

### CLI
```bash
python scripts/samplesize_power.py --test group_sequential --n_interim 1 --effect_gs 0.4
```

---

## 适应性设计 / Adaptive Design — `rpact`

### Clinical Use / 临床场景
- **样本量重估计 (SSR)**：根据中期数据调整样本量
- **人群富集 (Population Enrichment)**：中期分析后聚焦于有效亚组
- **组合检验法 (Combination Test)**：各阶段 p 值通过逆正态合并

### 方法
- **rpact** 提供完整的适应性设计框架
- **逆正态法**：保持类型 I 错误率
- 需预先指定适应性规则和停止边界

### CLI
```bash
python scripts/samplesize_power.py --test adaptive --n_stages_adapt 2 --effect_adaptive 0.4
```

---

## 精确生存设计 / Survival Exact — `rpact`

### Clinical Use / 临床场景
- **确证性肿瘤试验**：基于事件的精确样本量计算
- **考虑复杂时间线**：招募、随访、失访的完整建模
- **监管申报**：符合 ICH E9 要求的精确计算

### 方法
- 使用 `rpact::getSampleSizeSurvival()` 函数
- 考虑招募时间、随访时间、事件率、失访率
- 基于对数秩检验的精确计算

### CLI
```bash
python scripts/samplesize_power.py --test survival_exact --hr_exact 0.75 --accrual_exact 12 --followup_exact 12
```

---

## Full Command Matrix / 完整命令矩阵

| Test Type | CLI Flag | Required Params |
|:----------|:---------|:----------------|
| Two-sample t-test | `--test ttest_ind` | `--effect` |
| Paired t-test | `--test ttest_paired` | `--effect` |
| ANOVA | `--test anova` | `--effect`, `--k_groups` |
| One proportion | `--test proportion_one` | `--p1` |
| Two proportions | `--test proportion_two` | `--p1`, `--p2` |
| Non-inferiority | `--test non_inferiority` | `--p1`, `--p2`, `--margin` |
| **Mixed Model** | `--test mixed_model` | `--effect` |
| **ROC** | `--test roc` | `--auc1` |
| **Poisson** | `--test poisson` | `--lambda1`, `--lambda2` |
| **Cluster Randomized** | `--test cluster` | `--icc`, `--m`, `--n_indiv` |
| **Bland-Altman** | `--test bland_altman` | `--sd_diff`, `--w` |
| **Bioequivalence** | `--test be_tost` | `--theta0`, `--cv` |
| Equivalence | `--test equivalence` | `--margin` |
| Survival | `--test survival` | `--hazard_ratio` |
| **Survival Exact** | `--test survival_exact` | `--hr_exact` |
| **NI Survival** | `--test ni_survival` | `--ni_margin_surv` |
| **Vaccine Efficacy** | `--test vaccine_efficacy` | `--ve_control`, `--ve_treatment` |
| **Multiple Endpoints** | `--test multiple_endpoints` | `--effect`, `--correlation` |
| **Bayesian** | `--test bayesian` | `--prob_control`, `--prob_treatment` |
| **Dose Escalation** | `--test dose_escalation` | `--n_doses`, `--target_dlt` |
| **Win-Ratio** | `--test win_ratio` | `--win_ratio_theta` |
| **Must-Win** | `--test must_win` | `--n_endpoints_must` |
| **Historical Controls** | `--test historical_controls` | `--historical_response`, `--historical_n` |
| **MAMS** | `--test mams` | `--n_arms_mams` |
| **Conditional Power** | `--test conditional_power` | `--observed_effect` |
| **Superiority Margin** | `--test superiority_margin` | `--sup_margin` |
| **Assurance** | `--test assurance` | `--n_assurance` |
| **Dunnett** | `--test dunnett` | `--n_groups_dunnett` |
| **Mediation** | `--test mediation` | `--a_path`, `--b_path` |
| **Group Sequential** | `--test group_sequential` | `--n_interim` |
| **Adaptive** | `--test adaptive` | `--n_stages_adapt` |

---

## References / 参考文献

- Green P, MacLeod CJ. SIMR: an R package for power analysis of generalized linear mixed models by simulation. Methods in Ecology and Evolution, 2016.
- Obuchowski NA, et al. Sample size requirements for studies of diagnostic tests. Radiology, 1998.
- Lu MJ et al. Sample size for assessing agreement between two instruments. Statistical Methods in Medical Research, 2016.
- Halloran ME, et al. Exposure Efficacy and Change in Rate of Infection with and without a Vaccine. Epidemiology, 1991.
- Labes D, Schütz H, Lang B. PowerTOST: Power and Sample Size for (Bio)Equivalence Studies. CRAN.
- Patterson SD, Jones B. Bioequivalence and Statistics in Clinical Trials. CRC Press.
- Eggleston B et al. BayesCTDesign: Bayesian Clinical Trial Design with Historical Control Data. CRAN.
- Sabanés Bové D et al. crmPack: Model-Based Dose Escalation Designs in R. JSS, 2019.
- Pahl R et al. BuyseTest: A package to compute the Win Ratio. CRAN.
- Wassmer G, Pahlke F. rpact: Confirmatory Adaptive Clinical Trial Design and Analysis. CRAN.
- Wassmer G, Brannath W. Group Sequential and Confirmatory Adaptive Designs in Clinical Trials. Springer.
- Bulus M et al. MCPAN: Multiple Comparisons Using Normal Approximations. CRAN.
- Qiu W et al. powerMediation: Power/Sample Size for Mediation Effects. CRAN.
- Serdar CC et al. RBesT: R Bayesian Evidence Synthesis Tools. CRAN.
- Green SB, et al. Proceedings of the International Society for Clinical Biostatistics. 2023.

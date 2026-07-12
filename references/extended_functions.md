# Extended Functions Reference / 扩展功能参考

> v3.0 additions: Vaccine Efficacy, Bayesian Design (BayesCTDesign), Dose Escalation (escalation), Multiple Endpoints

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
| **Vaccine Efficacy** | `--test vaccine_efficacy` | `--ve_control`, `--ve_treatment` |
| **Multiple Endpoints** | `--test multiple_endpoints` | `--effect`, `--correlation` |
| **Bayesian** | `--test bayesian` | `--prob_control`, `--prob_treatment` |
| **Dose Escalation** | `--test dose_escalation` | `--n_doses`, `--target_dlt` |

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

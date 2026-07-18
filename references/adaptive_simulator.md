# Adaptive-Trial Monte-Carlo Simulator / 自适应试验蒙特卡洛仿真器

Module: `scripts/adaptive_simulator.py` — exposed via the main CLI as
`--test adaptive_simulate`. Ported from the ClawHub skill
`adaptive-trial-simulator` (aipoch-ai) and re-implemented to fit ct-samplesize.
/ 模块 `scripts/adaptive_simulator.py`，经主 CLI `--test adaptive_simulate` 调用。
移植自 ClawHub 技能 `adaptive-trial-simulator`（aipoch-ai）并按本技能规范重写。

## When to use / 何时使用

Use this **simulation** engine when you want to *validate* an adaptive or
group-sequential design by Monte-Carlo (empirical power, empirical type I error,
expected sample size, early-stop probabilities) rather than solve a closed-form
sample size. For **analytic** group-sequential / adaptive sample size (rpact /
gsDesign), use `--test group_sequential` or `--test adaptive` instead — they are
complementary. / 当你想用蒙特卡洛**验证**一个自适应/成组序贯设计（经验功效、
经验 I 类错误、期望样本量、早停概率）时使用本仿真器；若需**解析法**样本量
（rpact/gsDesign），改用 `--test group_sequential` 或 `--test adaptive`。二者互补。

> Pure Python, fully offline: no R, no shell, no `eval`, no code-injection
> surface — runs directly (no `--yes` SAFE-PREVIEW gate). Needs numpy + scipy;
> `--visualize` also needs matplotlib. / 纯 Python、完全离线：无 R/shell/eval、
> 无注入面，直接运行（无需 `--yes` 安全预览）。依赖 numpy+scipy；`--visualize` 需 matplotlib。

## Capabilities / 功能 (6)

| # | Capability / 功能 | How / 实现 |
|---|---|---|
| 1 | Design Simulation / 设计仿真 | Monte-Carlo of the chosen design under H1 & H0 |
| 2 | Sample-Size Re-estimation / 样本量再估计 | promising-zone + Cui-Hung-Wang weighted statistic |
| 3 | Early Stopping / 早停 | efficacy + non-binding futility boundaries |
| 4 | Type I Error Control / I 类错误控制 | alpha-spending calibration, verified under H0 |
| 5 | Multi-Arm / 多臂 | drop-the-loser interim selection (Dunnett/Bonferroni) |
| 6 | Power Optimization / 功效优化 | grid search for min per-arm N reaching target power |

## Designs & spending / 设计与消耗函数

- `--sim_design`: `group_sequential` | `adaptive_reestimate` | `drop_the_loser`
- `--spending_function`: `obrien_fleming` (conservative early) | `pocock`
  (aggressive early) | `power_family` (shape via `--rho`, e.g. 3)

Boundaries are computed by an exact Armitage-McPherson-Rowe recursion on the
Brownian (B-value) scale, reproducing gsDesign-style OBF/Pocock boundaries. /
边界由布朗运动（B-value）尺度上的精确 Armitage-McPherson-Rowe 递推求得。

## Key flags / 关键参数

| Flag | Meaning / 含义 | Default |
|---|---|---|
| `--sim_design` | design type / 设计类型 | group_sequential |
| `--effect_size` | Cohen's d (single-arm designs) | 0.3 |
| `--effect_sizes` | per-arm d list for drop_the_loser, e.g. `0.2,0.35,0.5` | — |
| `--sim_n` | per-arm sample size / 每组样本量 | 100 |
| `--interim_looks` | looks incl. final / 分析次数(含最终) | 2 |
| `--spending_function` | alpha spending / 消耗函数 | obrien_fleming |
| `--rho` | power_family shape / 形状 | 3.0 |
| `--futility` / `--beta` | add non-binding futility / 加 futility | off / 0.2 |
| `--reestimate_method` | SSR method / 再估计法 | promising_zone |
| `--interim_fraction` `--target_cp` `--max_inflation` | SSR controls | 0.5 / 0.9 / 2.0 |
| `--n_arms` `--selection_fraction` `--correction` | multi-arm controls | 3 / 0.5 / dunnett |
| `--optimize` `--n_min` `--n_max` `--power` | power search / 功效搜索 | off / 10 / 1000 / 0.9 |
| `--n_simulations` | MC replications / 重复次数 | 10000 |
| `--alpha` | one-sided alpha (from common flag) | 0.05 |
| `--visualize` `--sim_output` `--sim_seed` | PNG / JSON / seed | off / — / — |

> Note: `--alpha` is the shared common flag (default 0.05). For a one-sided
> 0.025 design pass `--alpha 0.025`. / `--alpha` 为公共参数（默认 0.05）；
> 单侧 0.025 设计请显式加 `--alpha 0.025`。

## Examples / 示例

```bash
# 1) Group-sequential, 3 looks, OBF spending, one-sided 0.025
python samplesize_power.py --test adaptive_simulate --sim_design group_sequential \
  --effect_size 0.3 --sim_n 200 --interim_looks 3 --spending_function obrien_fleming \
  --alpha 0.025 --n_simulations 20000 --sim_seed 42

# 2) With non-binding futility (Pocock spending)
python samplesize_power.py --test adaptive_simulate --sim_design group_sequential \
  --effect_size 0.3 --sim_n 200 --interim_looks 3 --spending_function pocock \
  --futility --beta 0.2 --alpha 0.025

# 3) Sample-size re-estimation (promising zone, CHW statistic)
python samplesize_power.py --test adaptive_simulate --sim_design adaptive_reestimate \
  --effect_size 0.3 --sim_n 200 --interim_fraction 0.5 --target_cp 0.9 \
  --max_inflation 2.0 --alpha 0.025

# 4) Multi-arm drop-the-loser (3 arms) with Dunnett-style adjustment
python samplesize_power.py --test adaptive_simulate --sim_design drop_the_loser \
  --effect_sizes "0.2,0.35,0.5" --sim_n 150 --selection_fraction 0.5 \
  --correction dunnett --alpha 0.025

# 5) Power optimization: min per-arm N reaching 90% power, + PNG
python samplesize_power.py --test adaptive_simulate --optimize \
  --effect_size 0.3 --power 0.9 --interim_looks 2 --alpha 0.025 \
  --n_min 150 --n_max 400 --visualize

# The module can also be run standalone (hyphenated flags):
python adaptive_simulator.py --design group_sequential --effect-size 0.3 \
  --sample-size 200 --interim-looks 3 --spending-function obrien_fleming --alpha 0.025
```

## Output / 输出

A JSON block with (design-dependent): `power`, `type_i_error`,
`expected_sample_size` (total & per-arm), `max_sample_size`,
`early_stop_rate {efficacy, futility}` (GS), `prob_sample_size_increase` (SSR),
`power_correct_selection` / `prob_correct_selection` (multi-arm), and a
`design_config` echoing all inputs plus the computed Z boundaries. / 输出 JSON：
含功效、I 类错误、期望/最大样本量、早停率、（SSR）扩样概率、（多臂）正确选臂概率，
以及回显全部输入与计算所得 Z 边界的 `design_config`。

## Validation / 验证

At α=0.025 the empirical type I error is calibrated to ≈0.025 across all
designs (checked with 20k-40k replications): GS 3-look OBF → power 0.846 / T1E
0.0251; SSR promising-zone → power 0.890 / T1E 0.0251 / 28% inflation prob;
drop-the-loser 3-arm → power_any 0.959 / correct-selection 0.693 / T1E 0.0235. /
α=0.025 下（2万–4万次重复）各设计经验 I 类错误均校准至 ≈0.025。

## Statistical notes / 统计说明

- Effect size is Cohen's d; final non-centrality is `d*sqrt(n/2)` per two-arm Z.
  / 效应量为 Cohen's d，两组 Z 最终非中心参数 `d*sqrt(n/2)`。
- SSR uses the Cui-Hung-Wang (1999) weighted statistic `Zw = w1*Z1 + w2*Z2`
  with pre-planned weights, preserving type I under data-dependent re-estimation.
  / 样本量再估计采用 Cui-Hung-Wang(1999) 加权统计量，权重预先固定以保持 I 类错误。
- Futility is non-binding beta-spending under H1 (efficacy boundaries computed
  independently). / futility 为 H1 下非绑定 beta-spending（efficacy 边界独立计算）。

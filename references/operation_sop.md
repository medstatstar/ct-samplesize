# ct-samplesize Operation SOP

> Agent: `ct-samplesize`
> Version: v3.8.0
> See `SKILL.md` for the canonical definition.

## 1. Purpose

- Covers sample-size & power calculation for clinical-trial practitioners.
- Supports 49+ test types via natural-language prompts; computes power / sample
  size / effect size for t-test, ROC (AUC), Poisson, RCT, SSR, and more.

## 2. Environment

- **R 4.x**: detected by `find_rscript` (which locates `Rscript`). Search order:
  1. `PATH` → `Rscript`
  2. `C:\Tools\R-4.5.1\bin\x64\Rscript.exe`
  3. `C:\Program Files\R\R-4.5.1\bin\x64\Rscript.exe`
  4. `/usr/local/bin/Rscript` and `/usr/bin/Rscript` (macOS / Linux)
  - If none found, emit `error.rscript_not_found`.
- **Python 3.8+**: drives the CLI and the pure-Python fallback.
- **R packages**: `stats`, `pwr`, `rpact`, plus base R.
- Inline R engines: `.R` logic lives in `scripts/r_libs.py` (`I18N_R`,
  `ADAPTIVE_SIM_R`); the CLI writes it to a temp `.R` file and `source()`s it.
- Install helpers: `--install-all-packages`, `--run-install`.

## 3. Agent invocation

### 3.1 Agent entry

The agent reads `SKILL.md` and runs the CLI with `--test`. Default is a
**dry-run**; pass `--yes` to execute.

### 3.2 CLI shape

```bash
python scripts/samplesize_power.py --test <test type> [params] [--dry-run | --yes | --show-code]
```

- `--yes` executes; `--show-code` prints the generated R code; omitting both is a
  dry-run that displays the R code without running it.
- `--show-code` prints the R code (no execution).
- `--yes` / `-y` runs `Rscript` to compute the result.

## 4. Security model

- **dry-run by default**: R code is shown but not executed.
- allowlist: only `_validate_token`, `_safe_r_path_literal`, and `run_r` may
  invoke R — prevents RCE via prompt injection.
- `--yes` runs `subprocess.run([rscript, '--vanilla', tmp])` with no shell.

## 5. Common flags

|Flag|Used for|Default|
|------|------|
|`--test`|`ttest_ind`, `roc`, `poisson`, `cluster`, `adaptive_simulate`, `gsd_*`|—|
|`--alpha`|significance level|0.05|
|`--power`|target power (alternative to `--nobs`)|—|
|`--nobs`|sample size (alternative to `--power`)|—|
|`--effect`|effect size|—|
|`--sd`|standard deviation (t-tests)|—|
|`--side`|`one` or `two`|`two`|
|`--p1` / `--p2`|proportions (two-sample)|—|
|`--sim_design` `--effect_size` `--sim_n` `--interim_looks` `--spending_function` `--n_simulations` `--sim_seed` `--sim_output` `--visualize`|adaptive-simulator controls|—|

## 6. Examples

### 6.1 t-test power → n

```bash
python scripts/samplesize_power.py --test ttest_ind --side one --sd 0.8 --effect 0.5 --power 0.9 --yes
```

Output: `n per group: 45` (Cohen's d = 0.625).

### 6.2 ROC n → power

```bash
python scripts/samplesize_power.py --test roc --auc0 0.6 --auc1 0.8 --nobs 200 --alpha 0.05 --yes
```

Output: `Achieved power: 0.9931`.

### 6.3 Adaptive simulation

```bash
python scripts/samplesize_power.py --test adaptive_simulate \
  --sim_design group_sequential --effect_size 0.3 --sim_n 100 \
  --interim_looks 2 --spending_function obrien_fleming --alpha 0.025 \
  --n_simulations 2000 --sim_seed 42 --yes
```

Reports empirical power, type I error, expected N, efficacy Z bounds, and
early-stop rates. Use `--sim_output results.json` and `--visualize` for artifacts.

## 7. Notes

1. R math uses `._qt(...)` (not `._qt`); fixed in v3.7.1.
2. Under `--yes`, R labels results `label.cohens_d` / `n per group`.
3. `--visualize` / `--plot_effects` / `--n_seq` render PNG charts.
4. `--sim_output` writes a JSON result file.
5. `--show-code` shows the generated R (dry-run) code, which embeds `I18N_R`.

## 8. Troubleshooting

|Symptom|Cause|Fix|
|------|------|------|
|R `unexpected symbol in "_qt"`|old code used `._qt`|use `._qt`; fixed in v3.7.1+|
|ROC `NameError: name 'ss_roc' is not defined`|Python path issue|fixed in v3.7.1+ (R path)|
|`error.rscript_not_found`|Rscript missing|install R or set `RSCRIPT_PATH` / `find_rscript`|
|`pwr` / `rpact` missing|package not installed|run `--install-all-packages`|
|locale shows zh|OS language is zh/CN|expected; output follows OS locale|

## 9. Maintenance

- `.R` logic lives in `r_libs.py`, not standalone `.R` files.
- With `--yes` the code runs (dry-run shows it first); the v3.7.1 fix renamed
  `._qt` to `._qt` consistently.

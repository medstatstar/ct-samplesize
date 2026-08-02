# ct-samplesize — Test Menu (Navigation Aid)

> **What this file is:** the authoritative map of all 49 `--test` types. The agent reads it
> to help a user **pick the right test** when they need to choose. It is a *navigation aid*, not
> a strict taxonomy — the same test may appear under several headings on purpose.
>
> **Triage gate (ct-base §5.2) — read before opening this menu:**
> - **Simple** (the user already named a specific test, e.g. "two-sample t-test") → compute directly, **do not show this menu**.
> - **Vague** (the user is unsure what test to use, e.g. "help me figure out the sample size") → enter **grill-me** branch-by-branch probing; **do not dump this menu**. Clarify the endpoint type, design and goal first, then compute.
> - **Complex** (the user knows the design but hesitates between test types / design families) → use this menu. When they waver on a choice, offer the **③ explain-differences** option (see below) instead of deciding for them.
>
> **③ Can't decide?** → say *"explain the differences between these choices in detail"*, and the agent will clarify the clinical / statistical meaning (e.g. superiority vs non-inferiority, with vs without interim analysis) before you choose. This entry is required on every Complex routing menu (ct-base §4.4).

**Total: 49 test types** — a primary tree of 6 endpoint categories, plus a design-family cross-index.

---

## Part 0 — Find your test by *research question* (start here if unsure)

You do not need to know statistical jargon. Pick the question closest to what you want to find out;
the right `--test` is on the right.

| You want to find out… | Typical design | `--test` |
|---|---|---|
| Does drug A change a **continuous** outcome (BP, HbA1c, score) more than B? | Parallel 2-group | `ttest_ind` |
| Same, but **paired / 2×2 crossover** (each subject their own control)? | Crossover / paired | `ttest_paired` |
| Is a single group's mean different from a known standard? | One-sample | `ttest_one` |
| Do **3+ groups** differ on a continuous outcome? | k-group | `anova` |
| Are two **response rates** (e.g. 20% vs 35%) different? | Parallel 2-group | `proportion_two` |
| Is a single group's rate different from a target? | One-group | `proportion_one` |
| Are two **paired** rates (before/after) different? | Paired | `proportion_paired` |
| How much **more/less likely** is an event with treatment (OR / RR)? | 2-group | `odds_ratio` / `risk_ratio` |
| Is the new treatment **not worse** than control (within a margin)? | Non-inferiority | `non_inferiority` / `ni_survival` |
| Are two treatments **equivalent** (means / HR)? | Equivalence | `equivalence` / `survival_equivalence` |
| Is a generic **bioequivalent** to the reference? | 2×2 crossover BE | `be_tost` |
| Does treatment improve **survival / delay event** (HR)? | Time-to-event | `survival` |
| How well does a **diagnostic test** discriminate (AUC)? | Diagnostic | `roc` |
| Do two measurement methods **agree** (Bland-Altman)? | Method comparison | `bland_altman` |
| How many **events / rate** differ between groups? | Count | `poisson` |
| I want **interim analyses / early stopping** built in. | Group-sequential | `group_sequential` / `gsd_survival` |
| I want the design to **adapt** mid-trial. | Adaptive | `adaptive` |
| I want a **Bayesian** design / assurance. | Bayesian | `bayesian` / `assurance` |
| I'm doing a **Phase I dose-escalation**. | Dose-finding | `dose_escalation` |
| I have **multiple arms / endpoints / clusters**. | Complex design | `mams` / `multiple_endpoints` / `cluster` |

> Any test above is reachable from the full tree in Parts 1–2. If your question isn't listed, jump to the
> endpoint category that matches your outcome type.

---

## Part 1 — Primary Tree by Endpoint Type (authoritative)

### ① Continuous
- `ttest_ind` — Two-means comparison (parallel)
- `ttest_paired` — Paired t / 2×2 crossover
- `ttest_one` — One-sample vs known mean
- `anova` — Multi-group (k groups)
- `equivalence` — Equivalence (means)
- `mixed_model` — Repeated measures / longitudinal

### ② Binary / Proportions
- `proportion_one` — Single-group rate
- `proportion_two` — Two-group rate (chi-square)
- `proportion_paired` — Paired rate (McNemar)
- `odds_ratio` — Odds ratio
- `risk_ratio` — Risk ratio (RR)
- `non_inferiority` — Non-inferiority (rate)
- `superiority_margin` — Superiority by margin
- `be_tost` — Bioequivalence (TOST)
- `vaccine_efficacy` — Vaccine efficacy
- `gsd_proportion` — Group-sequential two proportions

### ③ Count / Rates
- `poisson` — Poisson rate
- `recurrent_events` — Recurrent events (Andersen-Gill)
- `gsd_poisson` — Group-sequential two Poisson rates

### ④ Survival / Time-to-event
- `survival` — Survival (simplified logrank)
- `survival_exact` — Survival (exact)
- `ni_survival` — Non-inferiority survival
- `survival_equivalence` — Survival equivalence (TOST log-HR)
- `survival_superiority` — Survival superiority w/ margin
- `cox_covariate` — Cox regression w/ covariate R²
- `survival_one_sample` — One-sample exponential survival
- `competing_risks` — Competing risks (cum. incidence)
- `survival_historical` — Historical-control logrank
- `gsd_survival` — Group-sequential logrank
- `gsd_hazard` — Group-sequential hazard ratio (HR)
- `gsd_survival_sim` — Group-sequential logrank — Monte-Carlo SIM
- `gsd_hazard_sim` — Group-sequential HR — Monte-Carlo SIM

### ⑤ Diagnostic / Method comparison
- `roc` — ROC curve diagnostic trial
- `bland_altman` — Bland-Altman method comparison

### ⑥ Special / Advanced designs
- `group_sequential` — Group sequential interim (rpact exact two-sample means)
- `adaptive` — Adaptive design
- `adaptive_simulate` — Adaptive design — Monte-Carlo SIM
- `bayesian` — Bayesian design
- `dose_escalation` — Dose escalation (Phase I)
- `mams` — Multi-arm multi-stage (MAMS)
- `dunnett` — Dunnett multiple comparison
- `win_ratio` — Win-Ratio composite endpoint
- `must_win` — Must-Win co-primary endpoints
- `historical_controls` — Historical control borrowing
- `conditional_power` — Conditional power / sample-size re-estimation
- `assurance` — Bayesian assurance
- `multiple_endpoints` — Multiple / compound endpoints
- `mediation` — Mediation effects
- `cluster` — Cluster-randomized

---

## Part 2 — Design-Family Cross-Index

The same tests, regrouped by **study design** — an additional (non-exclusive) entry point for users
who think in design terms rather than endpoint type.

### Group-Sequential / Interim analysis
`group_sequential` · `gsd_proportion` · `gsd_survival` · `gsd_hazard` · `gsd_poisson` · `gsd_survival_sim` · `gsd_hazard_sim`
> Also reachable from ① (means), ② (proportions), ③ (rates), ④ (survival HR).

### Adaptive
`adaptive` · `adaptive_simulate`

### Equivalence / Non-inferiority / Superiority-margin
`equivalence` · `be_tost` · `non_inferiority` · `superiority_margin` · `ni_survival` · `survival_equivalence` · `survival_superiority`

### Bayesian
`bayesian` · `assurance`

### Dose Escalation
`dose_escalation`

### Multi-arm / Multiplicity
`mams` · `dunnett`

### Historical Control
`historical_controls` · `survival_historical`

### Vaccine
`vaccine_efficacy`

### Conditional Power / Sample-size Re-estimation
`conditional_power` · (re-estimation also in `adaptive`)

### Win Statistics
`win_ratio` · `must_win`

### Multiple / Composite Endpoints
`multiple_endpoints`

### Cluster-randomized
`cluster`

### Mediation
`mediation`

### Longitudinal / Mixed-model
`mixed_model`

### Diagnostic / Method comparison
`roc` · `bland_altman`

---

## How the agent should use this menu

1. **Identify the user's endpoint type** → jump to the matching primary-tree category (①–⑥).
2. If the user thinks in **design terms** (e.g. "I want a group-sequential trial"), use the **Design-Family Cross-Index** to locate the test, then confirm the endpoint.
3. The same test may appear in both views — that is intentional (non-exclusive).
4. After picking a test, see [`cli_examples.md`](cli_examples.md) for the exact CLI flags.
5. On any hesitation between choices, offer **③ explain-differences** (ct-base §4.4) before deciding.

# ct-samplesize

[🇨🇳 中文 (Chinese)](./README_ZH.md) | [🇺🇸 English (Current)](#)

> **Clinical Sample Size & Power Calculator** — Auto detect R environment → recommend optimal tools → calculate & explain. Supports Python basic stats and R advanced designs.

## Installation

No extra installation needed. Auto-loads as a WorkBuddy / OpenClaw skill.

## Use Cases

- **Simple**: Two-means comparison, ANOVA, proportions, non-inferiority, survival (simplified)
- **Complex**: Group sequential (interim), adaptive (SSR), MAMS, platform trials, bioequivalence

## Quick Start

```
"Control 20%, treatment 35%, chi-square test, two-sided α=0.05, power=0.8"
"Survival trial with 1 interim analysis, HR=0.75, 1:1 randomization"
"Non-inferiority trial, margin=0.1, control rate=85%, treatment rate=80%"
```

## File Structure

```
ct-samplesize/
├── SKILL.md              ← Skill definition (bilingual, concise)
├── README.md             ← This file (English)
├── README_ZH.md          ← Chinese version
├── AGENTS.md             ← Core execution rules (bilingual)
├── assets/
│   └── icon.svg          ← Skill icon (104×104)
├── scripts/
│   └── samplesize_power.py  ← Python calculator + auto R code gen
└── references/
    ├── r_packages_zh.md     ← R package reference (20+ pkgs)
    ├── formulas_zh.md       ← Formula derivations
    ├── python_usage.md      ← Python quick ref
    ├── r_usage.md           ← R quick ref
    ├── effect_size.md       ← Effect size standards (d/f/h + Z table)
    ├── report_template.md   ← Report template + mandatory R code
    └── examples.md          ← 3 full walkthroughs (proportion/GS/noninferiority)
```

## System Requirements

| Component | Requirement |
|:----------|:------------|
| R | ≥ 3.6.0 (≥ 4.1.0 recommended) + rpact, gsDesign, TrialSize, pwr, PowerTOST |
| Python | ≥ 3.8 + statsmodels ≥ 0.14, numpy ≥ 1.24, scipy ≥ 1.11 |
| OS | Windows / macOS / Linux |

## Core Features

1. **Smart Env Detection**: Auto-detect R installation on every trigger
2. **Dual-path**: Python (simple) + R (exact & complex)
3. **Mandatory R Code**: Regardless of path, always include reproducible R script
4. **Comprehensive**: 20+ R packages, full formula derivations, 3 complete examples

## References

- rpact: https://www.rpact.org/
- gsDesign: https://keaven.github.io/gsDesign/
- TrialSize: https://cran.r-project.org/web/packages/TrialSize/
- PowerTOST: https://cran.r-project.org/web/packages/PowerTOST/
- CRAN ClinicalTrials View: https://cran.r-project.org/web/views/ClinicalTrials.html

## Source Code

https://github.com/medstatstar/ct-samplesize

# ct-samplesize

[🇺🇸 English](./README.md) | [🇨🇳 中文 (Chinese, 当前)](#)

> **临床样本量与检验效能计算专家** — 智能检测 R 环境 → 推荐最优工具 → 完成计算与解释。支持 Python 基础统计和 R 高级设计。
>
> **⚠️ 本地 R 执行：** 本技能通过 subprocess(Rscript) 在本地机器上执行生成的 R 代码。生成的 R 代码按需展示——说 **"带代码"** 查看。执行需要显式确认。

## 安装

无需额外安装，作为 WorkBuddy / OpenClaw 技能自动加载。

## 使用场景

- **简单设计**: 两组均值比较、方差分析、率比较、非劣效、生存分析（简化）
- **复杂设计**: 组序贯（期中分析）、适应性（SSR）、MAMS、多臂平台试验、生物等效性

## 快速开始

```
"对照组有效率20%，试验组35%，做两组率比较的卡方检验，α=0.05双侧，power=0.8"
"设计一个含1次期中分析的生存终点试验，HR=0.75，两组1:1随机"
"非劣效设计，margin=0.1，对照组有效率85%，试验组80%"
```

## 文件结构

```
ct-samplesize/
├── SKILL.md              ← 技能定义（中英双语，精简版）
├── README.md             ← 英文版本
├── README_ZH.md          ← 当前文件（中文版本）
├── AGENTS.md             ← 核心执行规则（中英双语）
├── assets/
│   └── icon.svg          ← 技能图标（104×104）
├── scripts/
│   └── samplesize_power.py  ← Python 计算器 + 自动 R 代码生成
└── references/
    ├── r_packages_zh.md     ← R 包名映射（20+ 包）
    ├── formulas_zh.md       ← 公式推导大全
    ├── python_usage.md      ← Python 快速参考
    ├── r_usage.md           ← R 快速参考
    ├── effect_size.md       ← 效应量标准（d/f/h + Z table）
    ├── report_template.md   ← 报告模板 + 强制 R 代码
    └── examples.md          ← 3 个完整示例（率比较/组序贯/非劣效）
```

## 系统要求

| 组件 | 要求 |
|:-----|:-----|
| R | ≥ 3.6.0（推荐 ≥ 4.1.0）+ rpact, gsDesign, TrialSize, pwr, PowerTOST |
| Python | ≥ 3.8 + statsmodels ≥ 0.14, numpy ≥ 1.24, scipy ≥ 1.11 |
| 操作系统 | Windows / macOS / Linux |

## 核心功能

1. **智能环境检测**: 每次触发时自动检测 R 安装情况
2. **双路径计算**: Python（简单）+ R（精确 & 复杂）
3. **强制 R 代码输出**: 无论走哪条路径，始终包含可复现 R 脚本
4. **全面参考**: 20+ R 包，完整公式推导，3 个完整示例

## 参考文献

- rpact: https://www.rpact.org/
- gsDesign: https://keaven.github.io/gsDesign/
- TrialSize: https://cran.r-project.org/web/packages/TrialSize/
- PowerTOST: https://cran.r-project.org/web/packages/PowerTOST/
- CRAN ClinicalTrials View: https://cran.r-project.org/web/views/ClinicalTrials.html

## 源代码

https://github.com/medstatstar/ct-samplesize

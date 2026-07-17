# Examples / 使用示例

> R code is **hidden by default**. Use `--show-code` to display (execute + show), or `--dry-run` to preview only.

---

## Example 1: Two Proportion Comparison / 两组率比较

**User query:**
> "对照组有效率20%、试验组35%，做两组率比较的卡方检验，α=0.05双侧，power=0.8"

### Step 1 — Preview R Code (dry-run) / 第一步 — 预览 R 代码（不执行）

```bash
python scripts/samplesize_power.py --test proportion_two --p1 0.35 --p2 0.20 --power 0.8
```

Output: R code is displayed (dry-run, NOT executed).

### Step 2 — Execute (after review) / 第二步 — 执行（审查后）

```bash
python scripts/samplesize_power.py --test proportion_two --p1 0.35 --p2 0.20 --power 0.8 -y
```

### Results / 计算结果
- **Per-group N**: 138 → Total 276
- Adjusted for 10% dropout: 154/group → Total 308

---

## Example 2: Group Sequential / 组序贯设计

**User query:**
> "含2次期中分析的生存终点试验，HR=0.7，α=0.025，power=0.9，入组12月，总36月"

### Preview (dry-run) / 预览（不执行）

```bash
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --alpha 0.025 --power 0.9
```

### Execute (after review) / 执行（审查后）

```bash
python scripts/samplesize_power.py --test survival --hazard_ratio 0.7 --alpha 0.025 --power 0.9 -y
```

---

## Example 3: Non-inferiority / 非劣效设计

**User query:**
> "非劣效检验，对照组率70%，试验组预期65%，非劣效界值10%，α=0.025单侧，power=0.8"

### Preview (dry-run) / 预览（不执行）

```bash
python scripts/samplesize_power.py --test non_inferiority --p1 0.65 --p2 0.70 --margin 0.1 --alpha 0.025 --power 0.8
```

### Execute (after review) / 执行（审查后）

```bash
python scripts/samplesize_power.py --test non_inferiority --p1 0.65 --p2 0.70 --margin 0.1 --alpha 0.025 --power 0.8 -y
```

---

## Execution Notes / 执行要点

1. **Default behavior**: R code is executed and results returned; code hidden (add `--show-code` to show, `--dry-run` to preview only)
2. **To show code while executing**: Add `--show-code` (after reviewing a `--dry-run` preview if desired)
3. **All examples**: Follow the same pattern — preview first, then execute with `-y`

> All R code blocks follow `references/report_template.md` standards.

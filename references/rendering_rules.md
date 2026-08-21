# Figure Output & Rendering Rules (ct-base §19)

> Detail companion to `SKILL.md` §Figure Output & Rendering. English-only per ct-base §4.
> (Chinese strings below are **user-facing UI phrases** that agents must quote verbatim to Chinese users — same class as the §6.7.2 conversion notice; they are runtime copy, not documentation prose.)
> Normative source of truth: `ct-base/docs/06-inline-rendering.md` §19 (esp. §19.12).

## Rendering priority — mandatory (user rule 2026-08-20, ct-base §19.12)

1. **Inline first (default):** the agent MUST inline the returned SVG **directly into the conversation stream** via the visualization channel — the figure appears in the chat, not as a file. Files persisted to `CTSS_OUTPUT_DIR` (default `./outputs`, `ctss_<test>_*.svg`) are **backup / editing only** — never present SVG as file-first.
2. **Fallback ladder** (if inline SVG cannot be displayed in the conversation, in order):
   - ① **HTML-wrapped preview** — embed the SVG in an HTML page opened in the preview panel; stays vector (selectable / zoomable / editable).
   - ② **PNG bitmap** — local `cairosvg` conversion.
3. **Natural-language prompts only:** never force the user to touch CLI flags — guide them with a directly-repeatable prompt: 「图形无法预览，请改用 PNG 图片格式重新出图」/「把图转成 PNG 文件」 (EN: "The figure can't be previewed, please re-render it as a PNG image" / "Convert the figure to PNG").

## Power reference line & no hand-redraw rule (user rule 2026-08-20)

- The local fallback generator (`_curve_svg_from_stats`) draws the **power reference line itself** — red dashed line + `power = X` label — whenever (a) the y-axis semantic is Power (reverse solves) and (b) `target_power` is passed (default 0.8 via `--power`, or the auto-curve block's default) and lies in the plotted range. Forward solves (y = sample size) draw none. The reference line uses the **same `sy()` mapping as data points and grid labels** — one coordinate system, no axis misalignment (verified: y-extrapolation round-trips to the target exactly).
- **★ Agent rule — never hand-redraw:** always present the skill-generated SVG as-is (reference line, labels, axes included). If a figure is needed for a case the skill did not plot (e.g. custom BE margins), either extend the skill or reuse the skill's numeric stats with the same axis-mapping conventions — do **not** rebuild the chart with ad-hoc coordinates inside the reply (2026-08-20 incident: an agent-drawn inline widget misaligned its y-axis ticks vs data points/reference line; charting stays under skill control so errors are fixable in code).

## figure_mode (ct-base §19.9)

- `svg_inline` (default) | `png_file` — local `cairosvg` converts each SVG to PNG (`svg_to_png`, strip-clip → bbox → viewBox → rasterize; emits `__FIGURE__ png` markers); use when inline SVG is slow / oversized; gracefully degrades to `svg_inline` if cairosvg missing. Set via `--figure-mode png_file` or `CTSS_FIGURE_MODE=png_file`.

## Render timing & over-threshold hint (ct-base §19.10)

- When `render_elapsed_seconds` > 30s or `render_svg_kb` > 200KB, the skill emits `__RENDER_HINT__` suggesting `png_file`. **★ Agent rule:** surface it in your reply and offer `png_file` — never bury it.

## Symmetry & reference implementation

- The local curve-fallback SVG generator (`_curve_svg_from_stats`) is §19-aligned (700×500, gridlines, multi-series, dynamic axis labels; stdlib only).
- `adapters/rendering.py` is the shared ct-base §19 reference implementation (byte-equivalent to `meta-analysis/adapters/rendering.py`); coze SVGs use fixed `viewBox` with content drawn outside it — the pipeline auto-expands via `content_bbox()` and removes internal `clipPath` so nothing is cropped.
- SVG editing & journal format conversion (EPS/PDF/TIFF 600dpi): `references/svg_editing.md`.

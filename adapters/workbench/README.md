# ct-samplesize 工作台（Workbench）

本地 Web 操作界面：信息输入 → 结果展示 → 图表选项控制 → 追加提问，一站式完成样本量 / 效能计算。

## 启动

> **默认使用正式联网模式**（真实 coze R 引擎），不要默认 MOCK。MOCK 仅用于无网络时的离线演示，返回的是 mock 结果、非真实计算。

```bash
cd ct-samplesize/adapters/workbench
# ✅ 正式计算（默认首选：真实 coze 端点，与 CLI 同套环境变量）
CTSS_COZE_ENDPOINT=https://ct-samplesize.coze.site/run python server.py 8765
# ⚠️ 离线演示（仅无网络时；返回 mock 结果，非真实计算）
CTSS_COZE_MOCK=1 python server.py 8765
```

> **⚠️ 本机系统代理残留（已实测）**：若 Windows 注册表残留 `HTTP(S)_PROXY` 指向空端口（代理软件未运行），urllib 会被拦截导致 coze 连不上。启动正式模式时需剥离代理直连：
> `HTTPS_PROXY= HTTP_PROXY= https_proxy= http_proxy= NO_PROXY=* no_proxy=* CTSS_COZE_ENDPOINT=https://ct-samplesize.coze.site/run python server.py 8765`

## 安全与环境变量（公开部署必读）

| 变量 | 说明 |
|---|---|
| `CTSS_COZE_ENDPOINT` | coze 计算端点（正式）|
| `CTSS_COZE_TOKEN` | coze Bearer token（**推荐**，优先级高于内嵌凭据）|
| `CTSS_COZE_NO_EMBEDDED` | 设为 `1` **强制禁用**内嵌公共凭据，避免密钥随包外泄（**公开部署必须设**）|
| `CTSS_WB_TOKEN` | 工作台 HTTP 鉴权 token；设置后 POST/DELETE 请求必须携带 `Authorization: Bearer <token>` 或 `?token=<token>` |
| `CTSS_COZE_MOCK` | 设为 `1` 启用离线演示模式（不联网，返回 mock 结果）|
| `CTSS_COZE_READ_TIMEOUT` | 读取超时秒（默认 600，冷启动 / 长计算需放宽）|

**公开部署最小配置**：
```bash
CTSS_COZE_NO_EMBEDDED=1 \
CTSS_COZE_ENDPOINT=https://ct-samplesize.coze.site/run \
CTSS_COZE_TOKEN=<your-private-token> \
CTSS_WB_TOKEN=<random-long-secret> \
python server.py 8765 0.0.0.0
```

> ⚠️ 不要在没有反向代理 TLS 的情况下把端口直接暴露到公网。

浏览器打开 <http://127.0.0.1:8765/> 即可。

约束：本后端为 **stdlib-only**（`http.server`），不引入 FastAPI / flask，与技能「零第三方依赖」红线一致。

## 四区功能

1. **信息输入**：检验族（一级）→ 检验方法（二级）两级选择 + 关键词搜索；动态参数表单（必填/通用/曲线/图形，运行时从 argparse 反射，零维护）；求解方向（求 n / 反求 power）；自然语言入口（零 LLM 确定性路由自动选检验+填表）。
2. **结果展示**：当前分析设定块、关键数值卡片、结果说明、内联 SVG 图形、可复现 R 代码、coze 请求信封（预览）。
3. **图表选项控制**：曲线 / 专项图勾选（仅 9 类曲线检验生效）、图形输出格式、分配比图显隐说明（ratio≠1 自动展示）。
4. **追加提问**：会话线程跨轮继承；逐轮 diff（继承 / 覆盖 / 缺失）；快捷修改（仅发变化字段）+ 自然语言追问，均走 `ct-base` 确定性合并（`merge_spec`），不丢参数、不臆造。

## 架构

| 文件 | 职责 |
|---|---|
| `form_schema.py` | 动态表单 schema 反射（49 检验 / 178 参数，源于 argparse + `_contract_index.json`） |
| `session_store.py` | 会话线程 + 确定性合并（复用 `ct-base/scripts/merge_spec.py`，缺则内嵌等价实现） |
| `server.py` | stdlib HTTP 后端（REST + 静态），复用 `CozeBackend` / `samplesize_power.build_parser` |
| `workbench.html` | 单文件前端（零依赖、浅色主题、中英双语），消费上述 REST API |

## REST 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 + 引擎/模式 |
| GET | `/api/schema` | 动态表单目录（49 检验 / 178 参数 / 36 族） |
| GET | `/api/schema/<test>` | 单检验方法表单 |
| POST | `/api/compute` | 计算 `{test, params, options, session_id?}` |
| POST | `/api/preview` | 仅返回 coze 请求信封（dry-run） |
| POST | `/api/nl` | 自然语言 → 选检验 + 抽参数 |
| POST | `/api/export` | 把已算结果固化成单文件 HTML 报告（复用技能 canonical `render_html_report`，与 CLI 报告完全一致） |
| POST/GET/DEL | `/api/session/*` | 会话线程创建 / 列表 / 详情 / 合并 / 重置 / 删除 |

> 注：会话持久化到 `adapters/workbench/sessions.json`，服务重启后可回放历史。

## 导出 HTML 报告

计算完成后，结果展示区顶部出现 **「⬇ 导出 HTML 报告」** 按钮：

- 点击后调用 `POST /api/export`，把当前结果重组成 coze 信封、交给技能既有 `rendering.render_html_report` 生成**单文件 HTML**（内联 SVG 图形 + 可复现 R 代码 + 数值卡片 + 结果说明）。
- 与 CLI 的 `--report` 输出**同源同构**，浏览器直接打开、离线可看、可转发。
- 报告文件名 `ctss_report_<test>.html`，由浏览器下载。
- 未计算 / 结果无内容时按钮禁用。

后端实现要点：`serialize_result` 产出的 `{text, figures, r_code, r_result}` 直接重组成 `render_html_report` 消费的 `{stats, narrative, figures, repro}` 信封，无需重跑计算；临时文件用后清理。

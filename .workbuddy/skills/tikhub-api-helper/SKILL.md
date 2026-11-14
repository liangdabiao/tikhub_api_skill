---
name: tikhub-api-helper
description: 搜索并调用 TikHub API，获取抖音/Douyin、TikTok、小红书、B站、微博、知乎、快手、Instagram、YouTube、Twitter/X、Reddit、Lemon8 等平台的公开数据（用户资料、视频/帖子、评论、搜索、热榜、趋势）。当用户想查社交媒体数据、找某个平台的数据接口、跨平台调研话题或账号、或提到 TikHub / TikHub API / 抖音 API / TikTok API 时使用。支持中英文提问。Use when the user needs to discover or call TikHub social-media data endpoints.
---

# TikHub API Helper

在本地 OpenAPI 规范中检索 TikHub 端点，构造参数并发起调用。

**本目录是独立、可直接发布的 Skill 包**（`.workbuddy/skills/tikhub-api-helper/`）：`SKILL.md`、`api_searcher.py`、`api_client.py`、`openapi.json` 四件套齐全，运行时不依赖目录外任何文件。发布或分享时只打包这一个目录，仓库根的 README、`openapi.md`、探索脚本等一律不带。以下命令默认在本目录下执行。

## 数据源：只用 openapi.json

本 Skill 只把 **`openapi.json`** 当作运行时数据源。`openapi.md` 是同一份规范用 widdershins 渲染出来给人看的副本，**不参与检索、不要整篇读进上下文**。

实测对比（当前 V5.3.1 / 2025-09-21 版本）：

| | `openapi.json` | `openapi.md` |
|---|---|---|
| 性质 | OpenAPI 3.0.1 上游规范 | `generator: @tarslib/widdershins v4.0.30` 派生的展示文档 |
| 体积 | 4.3 MB | 4.0 MB / 108,377 行 / 340 万字符 |
| 结构 | 1067 个端点、51 个标签、2144 个内联参数（784 个 required）、197 个 schema、operationId 100% 唯一且无重复 | 3009 个 H1、9918 个 H3、3501 个代码块、3398 个表格；`# [中文]`、`# [示例/Example]` 等正文标题把层级打乱，无法按标题可靠切分 |
| 可检索性 | `json.load()` 后按 operationId / tag / path 精确取单条，一次只注入约 1 KB 结果 | 只能全文扫描；整篇约百万级 token，且每个端点重复 8 种语言示例和模板化 `ResponseModel`，信噪比低 |
| 参数信息 | 参数名、`in`、`required`、type、default、description 齐全 | 由同一 spec 渲染而来，没有额外信息；示例响应多为 `"string"` 占位 |
| 内容覆盖 | 1067 条路径全部能在 MD 中找到 | 额外 8 个 `/api/v1/...` 字符串是正文举例（如 `/api/v1/tikhub/user/`），不是真端点，容易误导 |

结论：两者同源、端点覆盖一致，但 **JSON 可结构化检索且按需注入，MD 只适合人类查阅**。脚本也只依赖 JSON（`api_searcher.py` 直接 `json.load`）。中文信息没有丢：JSON 的 summary 是「中文 / English」双语，description 含完整中文用途与参数说明。

`openapi.md` 只是开发仓库里的人类阅读副本，不属于本 Skill 包，发布时不带；它也不含 JSON 之外的信息。

## 准备：API Token

脚本源码里**不含任何 token**。调用前需提供（任选其一）：

```bash
export TIKHUB_API_TOKEN=<your token>        # Git Bash / macOS / Linux
# 或在仓库根 .env 写入：TIKHUB_API_TOKEN=<your token>
# 或临时：python api_client.py GET ... --token <your token>
```

未配置时客户端会直接报 `No TikHub API token found` 并退出，不会发出带空 Bearer 的请求（那样只会得到含糊的 403）。公开的免鉴权端点可加 `--no-auth`。

域名：默认 `https://api.tikhub.io`；中国大陆用户加 `--china`（`https://api.tikhub.dev`），或设 `TIKHUB_BASE_URL`。规范文件路径可用 `TIKHUB_OPENAPI_PATH` 覆盖。

## 工作流

1. **理解意图** —— 确认平台和数据类型（用户资料 / 作品详情 / 评论 / 搜索 / 热榜）。
2. **检索端点** —— 用关键词或标签，先看候选的命令与说明。
3. **查详情** —— 用 `detail:` 拿到参数、必填项、返回结构和可直接执行的 `example_call`。
4. **调用** —— 用 `api_client.py`，把详情里的参数填实。
5. **呈现结果** —— 大响应用 `--summary` 看结构或 `--output result.json` 落盘，不要整段灌回对话。

## 命令速查

```bash
# 关键词检索（支持中英文、多个词、自然语言；按相关度排序）
python api_searcher.py "tiktok user profile"
python api_searcher.py "视频评论" --limit 10
python api_searcher.py "douyin hot search" --json      # 机器可读

# 分类浏览
python api_searcher.py tags                            # 51 个标签 + 端点数
python api_searcher.py tag:TikTok-Web-API              # 列全量，不截断
python api_searcher.py popular

# 端点详情：operationId 或路径都行
python api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile
python api_searcher.py detail:fetch_user_profile_api_v1_tiktok_web_fetch_user_profile_get

# 调用
python api_client.py GET /api/v1/health/check --no-auth
python api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"
python api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming" "count=10"
python api_client.py POST /api/v1/tiktok/web/generate_xgnarly --body '{"url":"https://..."}'

# 大响应
python api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}' --summary
python api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}' --output result.json
```

`api_searcher.py` 其他参数：`--spec <path>`、`--limit N`、`--json`、`--full`（详情里附带原始 operation）。
`api_client.py` 其他参数：`--token`、`--base-url`、`--china`、`--no-auth`、`--timeout N`、`--retries N`、`--compact`、`--summary`、`--output <file>`。

## 参数与调用细节

- **先查详情再调用**：`detail:` 会给出每个参数的 `in` / `required` / `type` / `default`。不少端点把所有参数标为可选，却在 description 里要求「至少提供一个」，实际调用仍需填值，否则返回 422。
- **Git Bash / MSYS2**：以 `/api/v1/...` 开头的参数会被改写成形如 `D:/.../PortableGit/api/v1/...` 的盘符路径，客户端会自动还原，无需手动加引号或转义。
- **查询参数**：写成 `k=v` 或 `a=1&b=2`；值里的 `+`、`/`、中文会由客户端正确编码。
- **POST**：`k=v` 进 query，JSON（位置参数或 `--body`）进 body；旧版会把 POST 的 query 参数丢掉，现已修复。
- **重试**：默认 `--retries 0`。TikHub 按次计费，自动重试可能重复扣费；需要时对 429 / 5xx 显式开启。
- **Demo 端点**：`/api/v1/demo/...` 返回固定缓存数据（规范里注明「1 小时缓存」），搜索时已降权；调研真实数据时选非 Demo 端点。

## 常见错误

| 现象 | 处理 |
|---|---|
| `No TikHub API token found` | 配置 `TIKHUB_API_TOKEN` / `.env` / `--token` |
| `401 / 403` | token 无效或无权限；公开端点用 `--no-auth` 对比测试 |
| `422` | 缺参数或参数名不对，用 `detail:` 核对 |
| `429` | 触发限流（规范标注 QPS 10/端点），等待后重试 |
| `Connection error` | 大陆用户加 `--china` |
| `ERROR: openapi.json not found` | 设 `TIKHUB_OPENAPI_PATH` 或 `--spec` |
| 响应过大 | `--summary` / `--output result.json` |

## 参考

- API 文档：https://api.tikhub.io  · Apifox：https://docs.tikhub.io
- 用户后台 / API Keys：https://user.tikhub.io
- 规范版本：`openapi.json` → `info.description` 中的 Release Information

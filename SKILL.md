---
name: tikhub-api-helper
description: 搜索并调用 TikHub API，获取抖音/Douyin、TikTok、小红书、B站、微博、知乎、快手、Instagram、YouTube、Twitter/X、Reddit、Lemon8 等平台的公开数据（用户资料、视频/帖子、评论、搜索、热榜、趋势）。当用户想查社交媒体数据、找某个平台的数据接口、跨平台调研话题或账号、或提到 TikHub / TikHub API / 抖音 API / TikTok API 时使用。支持中英文提问。Use when the user needs to discover or call TikHub social-media data endpoints.
---

# TikHub API Helper

检索本地 OpenAPI 规范中的 TikHub 端点，查清参数后发起调用。覆盖抖音、TikTok、小红书、B 站、微博、知乎、快手、Instagram、YouTube、X/Twitter、Reddit 等平台的公开数据（用户资料、作品、评论、搜索、热榜）。

本仓库根目录就是 Skill 目录：`SKILL.md`、`api_searcher.py`、`api_client.py`、`openapi.json` 同级。以下命令都在该目录执行。

## 数据源

只读同目录的 `openapi.json`（OpenAPI 3.0.1，V5.3.1，1067 端点 / 51 标签）。它是结构化规范，可按路径 / 标签 / operationId 精确取单条端点；不要整篇读进上下文，也不要去找别的文档。需要换规范时用 `TIKHUB_OPENAPI_PATH` 或 `--spec` 指定。

## API Token

源码不含任何 Token。调用前任选其一：

```bash
export TIKHUB_API_TOKEN=<your token>        # Git Bash / macOS / Linux
# 或单次临时传：python api_client.py GET ... --token <your token>
```

未配置时客户端报 `No TikHub API token found` 并退出。公开的免鉴权端点可加 `--no-auth`。域名默认 `https://api.tikhub.io`；大陆用户加 `--china`（`https://api.tikhub.dev`）或设 `TIKHUB_BASE_URL`。

## 工作流

1. 确认平台与数据类型（用户资料 / 作品 / 评论 / 搜索 / 热榜）。
2. 用关键词或标签检索，看候选端点和说明。
3. 用 `detail:` 查参数、必填项、返回结构和可直接执行的 `example_call`。
4. 用 `api_client.py` 填实参数发起调用。
5. 大响应用 `--summary` 看结构或 `--output result.json` 落盘，不要整段灌回对话。

## 命令速查

```bash
# 检索（中英文、多个词、自然语言；按相关度排序）
python api_searcher.py "tiktok user profile"
python api_searcher.py "视频评论" --limit 10
python api_searcher.py "douyin hot search" --json
python api_searcher.py tags
python api_searcher.py tag:TikTok-Web-API
python api_searcher.py popular

# 详情：路径或 operationId 都行
python api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile
python api_searcher.py detail:fetch_user_profile_api_v1_tiktok_web_fetch_user_profile_get

# 调用
python api_client.py GET /api/v1/health/check --no-auth
python api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"
python api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming" "count=10"
python api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}' --summary
python api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}' --output result.json
```

其他参数：搜索器 `--spec <path>` / `--limit N` / `--json` / `--full`；客户端 `--token` / `--base-url` / `--china` / `--no-auth` / `--timeout N` / `--retries N` / `--compact` / `--summary` / `--output <file>`。完整列表见 `--help`。

## 调用细节

- **先查详情再调用**：`detail:` 给出每个参数的 `in` / `required` / `type` / `default`。不少端点参数全标可选，却在 description 里要求「至少提供一个」，不填会返回 422。
- **Git Bash / MSYS2** 会把 `/api/v1/...` 改写成盘符路径，客户端自动还原，不用手动转义。
- **查询参数**写 `k=v` 或 `a=1&b=2`；`+`、`/`、中文会正确编码。POST 时 `k=v` 进 query，JSON（位置参数或 `--body`）进 body。
- **默认不重试**（`--retries 0`）：TikHub 按次计费，自动重试可能重复扣费；需要时对 429 / 5xx 显式开启。
- **别用 Demo 端点**：`/api/v1/demo/...` 返回缓存示例数据，不是真实结果。

## 常见错误

| 现象 | 处理 |
|---|---|
| `No TikHub API token found` | 配置 `TIKHUB_API_TOKEN` 或 `--token` |
| `401 / 403` | Token 无效或无权限；公开端点用 `--no-auth` 对比 |
| `422` | 缺参数或参数名不对，用 `detail:` 核对 |
| `429` | 触发限流，等待后重试 |
| `Connection error` | 大陆用户加 `--china` |
| `openapi.json not found` | 设 `TIKHUB_OPENAPI_PATH` 或 `--spec` |
| 响应过大 | `--summary` / `--output result.json` |

## 参考

- API 文档 https://api.tikhub.io · Apifox https://docs.tikhub.io
- 用户后台 / API Keys https://user.tikhub.io

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
- **ID 参数先用「名称转 ID」端点换**：`detail:` 里的示例 ID（如 `get_channel_info` 的 `UCXuqSBlHAE6Xw-yeJA0Tunw`）只是格式示例，不是目标账号；凭记忆手写 ID 会拿到全 `null` 的 `code 200` 响应（见下节）。YouTube 先用 `GET /api/v1/youtube/web/get_channel_id "channel_name=NBA"` 换出真实 `channel_id`，其它平台用 `detail:` 搜 `username` / `user_id` 找对应的转换端点。
- **Git Bash / MSYS2** 会把 `/api/v1/...` 改写成盘符路径，客户端自动还原，不用手动转义。
- **查询参数**写 `k=v` 或 `a=1&b=2`；`+`、`/`、中文会正确编码。POST 时 `k=v` 进 query，JSON（位置参数或 `--body`）进 body。
- **默认不重试**（`--retries 0`）：TikHub 按次计费，自动重试可能重复扣费；需要时对 429 / 5xx 显式开启。
- **别用 Demo 端点**：`/api/v1/demo/...` 返回缓存示例数据，不是真实结果。
- **判断关键词是否命中不要全文 grep 原始响应**：`params` / `input_keyword` / `request` 等是请求回显（微博综合搜索一次回显 469 次关键词），要按 `data` 里的数据字段路径取值。
- **枚举值以实测为准**：规范没给枚举时先用默认参数试；例如 `/api/v1/bilibili/app/fetch_search_by_type` 传 `search_type=bili_user` 返回 400，传 `video` 正常。
- **单价按端点不同**：`GET /api/v1/tikhub/user/get_endpoint_info "endpoint=/api/v1/..."` 查单价（实测常见 $0.001–0.002/次），账户接口不计费；4xx 请求通常不扣费。

## 跨平台调研取数

各平台响应结构差别很大，批量统计前先按字段路径取值，别全文 grep 也别只看常见字段名：

- **`code 200` 仍可能是空结果**：实测三种空结果都返回 `code 200`、退出码 0，且 `message_zh` 写明「本次请求将被计费」——Threads `fetch_user_info` → `data.user = null`；X `fetch_user_profile` → `data.status = "notfound"`；YouTube `get_channel_info` 传不存在的 `channel_id` → `title` / `subscriber_count` 等全为 `null`。要按业务字段判空，别只按 HTTP 码或退出码算成功，也别把空结果写成「0 粉丝 / 无账号」。
- **TikTok 搜索**：`aweme_list` 常为空，真实结果在 `data.search_item_list[].aweme_info`；单次响应可达 2MB，用 `--output` 落盘再解析。
- **Reddit**：搜索结果在 `data.search.dynamic.components.main.edges[].node.children[]`（`__typename=SearchPost`）；评论在 `postInfoById.commentForest.trees[].node.content.markdown`，默认只返回首屏若干条。
- **Threads**：帖子在 `data.results[].node.thread.thread_items[].post`；评论端点返回的第一条是原帖本身，按 `pk` 过滤再统计。`search_posts` 对长关键词容易超时，短词正常，该端点限流约 3/秒。
- **时间字段不统一**：YouTube 给 `"19 hours ago"` 这类相对字符串，X / TikTok / Threads 给绝对时间或 Unix 秒。做跨平台时间线必须先归一化，否则整批 YouTube 内容会被漏掉。
- 同一条内容经不同数据服务取到的点赞 / 浏览数会有几十到几千的抓取时刻差异，去重时按来源标注，别当成两份独立样本。

## 常见错误

| 现象 | 处理 |
|---|---|
| `No TikHub API token found` | 配置 `TIKHUB_API_TOKEN` 或 `--token` |
| `401 / 403` | Token 无效或无权限；公开端点用 `--no-auth` 对比 |
| `422` | 缺参数或参数名不对，用 `detail:` 核对 |
| `code 200` 但 `user` / `profile` 为 null 或 `status=notfound` | handle 未命中或 ID 无效，按业务字段判空；换正确用户名，或先用名称转 ID 端点 |
| `HTTP 400` | 看 stderr 的 `message_zh` / `router` / `docs`（服务端一般不扣费）；下方清单里的端点属服务端侧不可用，换同平台其它端点 |
| `429` | 触发限流，等待后重试 |
| `Connection error` | 大陆用户加 `--china` |
| `openapi.json not found` | 设 `TIKHUB_OPENAPI_PATH` 或 `--spec` |
| 响应过大 | `--summary` / `--output result.json` |

### V5.3.1 实测稳定报错的端点

换关键词或用最小参数复测仍稳定报 400，不是参数漏填，别在这些端点上反复试：

- `/api/v1/tiktok/web/fetch_search_user`、`/api/v1/tiktok/web/fetch_general_search`
- `/api/v1/instagram/v2/general_search`、`/api/v1/instagram/v3/search_users`、`/api/v1/instagram/v3/general_search`（v1 `fetch_search` 可用，但只返回账号）
- `/api/v1/zhihu/web/fetch_user_search_v3`
- `/api/v1/youtube/web_v2/search_channels`
- `/api/v1/douyin/search/fetch_general_search_v3`、`/api/v1/douyin/douplus/search_user_v2`
- `/api/v1/bilibili/huahuo/upper_by_nickname`（403）

需要用这些平台的数据时，先用 `detail:` 挑同平台其它端点。

## 参考

- API 文档 https://api.tikhub.io · Apifox https://docs.tikhub.io
- 用户后台 / API Keys https://user.tikhub.io

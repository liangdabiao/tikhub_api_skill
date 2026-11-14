# TikHub API Helper

> 源码仓库：https://github.com/liangdabiao/tikhub_api_skill
>
> **这个 GitHub 仓库是源码与文档；真正要安装、发布的 Skill 只有一个目录：`.workbuddy/skills/tikhub-api-helper/`。** 把这一层整个拷走即可运行，仓库根目录的其他文件都是开发期资料，安装 Skill 时一律不需要。

一个 Agent Skill，用于在本地 OpenAPI 规范中检索并调用 TikHub API。TikHub 提供抖音、TikTok、小红书、B 站、微博、知乎、快手、Instagram、YouTube、Twitter/X、Reddit 等多平台公开数据接口。

当前规范：`V5.3.1`（2025-09-21），共 **1067 个端点 / 51 个标签**。标签会随官方更新变化，用 `api_searcher.py tags` 查实时清单，不要在文档里写死数量。

## 本次修复（2026-11-14）

项目此前处于损坏状态，已修复：

| 问题 | 修复 |
|------|------|
| 原先的 `.claude/skills/` 嵌套是错误结构；Skill 文件被平铺到仓库根，且 `openapi.json` 与脚本分离 | 以 `.workbuddy/skills/tikhub-api-helper/` 为**唯一权威、可独立发布**的目录，四件套（`SKILL.md` / 两个脚本 / `openapi.json`）全部内置，删除 `.claude/` 及仓库级遗留文档 |
| 关键词搜索是整串子串匹配，`"tiktok user profile"` 只命中 1 个 Demo 端点 | 改为中英文分词 + 相关度排序，返回真实候选 |
| `tag:` 命令硬编码 `limit=50`，58 个端点的标签被静默截断 | 默认列全量 |
| 文档里的示例 operationId（如 `tiktok_web_fetch_user_profile_get`）在新版规范中全部失效 | 改为分词检索 + 按路径或真实 operationId 查详情 |
| `api_searcher.py` 输出会把整个 operation（含巨型 schema）灌进上下文 | 详情精简为参数 / 响应结构 / 可直接执行的 `example_call`，`--full` 才给原始对象 |
| `api_client.py` 无 token 时静默发送空 `Bearer`，得到含糊的 403 | 多来源读取 token，缺失时明确报错；源码不含任何凭据 |
| Git Bash/MSYS2 把 `/api/v1/...` 改写成 `D:/.../PortableGit/api/v1/...` | 客户端自动还原真实 API 路径 |
| POST 请求丢弃 `k=v` 查询参数 | GET/POST 都支持 query 与 JSON body |
| `explore_openapi.py` 硬编码 `D:/tikhub_api_skill/openapi.json`，直接崩溃 | 复用 `find_spec()` 按仓库结构定位 |
| README / SKILL.md 中多个示例路径与参数名已不存在 | 按 V5.3.1 实测校正 |

## 两份 API 文档用哪个

开发仓库里有两份同版本 API 文档：Skill 包内的 `openapi.json` 和仓库根的 `openapi.md`。**Skill 只带前者，发布时不带 `openapi.md`**，理由：

| | `openapi.json` | `openapi.md` |
|---|---|---|
| 性质 | OpenAPI 3.0.1 上游规范 | widdershins 从同一规范渲染的人类阅读副本 |
| 体积/结构 | 4.3 MB，路径、参数、schema 全部结构化 | 4.0 MB / 10.8 万行，3009 个 H1、9918 个 H3，标题被正文 markdown 打乱 |
| 检索 | `json.load()` 后按路径/标签/operationId 精确取单条，一次只注入约 1 KB | 只能全文扫描，整篇约百万级 token；每端点重复 8 种语言示例 |
| 参数 | 2144 个内联参数（784 个 required），type/default/description 齐全 | 由同一 spec 渲染，无额外信息；示例响应多为 `"string"` 占位 |

两者同源：JSON 的 1067 条路径全部能在 MD 中找到；MD 另多出 8 个 `/api/v1/...` 字符串只是正文举例（如 `/api/v1/tikhub/user/`），并非真实端点。`openapi.md` 只是开发仓库里的人类阅读副本，不属于 Skill 包、发布时不带，也不参与检索。完整实测对比见 `SKILL.md`。

## 项目结构

```
tikhub_api_skill/
├── .workbuddy/skills/tikhub-api-helper/  # ★ 唯一 Skill 包，发布时只取这一层
│   ├── SKILL.md                         # Skill 定义与工作流
│   ├── openapi.json                     # 唯一运行时数据源（4.3 MB）
│   ├── api_searcher.py                  # 检索 / 详情
│   └── api_client.py                    # 调用
│
├── openapi.md                           # 开发资料：人类阅读的派生文档（不打包）
├── openapi说明.md                       # 开发资料：鉴权说明（不打包）
├── explore_openapi.py                   # 开发资料：规范探索脚本（不打包）
├── README.md / README_EN.md             # 仓库文档（不打包）
└── .gitignore
```

**`.workbuddy/skills/tikhub-api-helper/` 是自包含的可发布单元**：把它整个拷到任意目录即可运行，`openapi.json` 与脚本同目录，不依赖上层的 README、`openapi.md` 或任何仓库结构。上面的根目录文件都是开发期资料，打包 Skill 时一律不带。

## 安装与配置

### 1. 取得 Skill

```bash
git clone https://github.com/liangdabiao/tikhub_api_skill.git
cd tikhub_api_skill
```

Skill 本体是 `.workbuddy/skills/tikhub-api-helper/`（四个文件）。二选一：

- **装进 Agent**：把整个目录拷到你的 skills 目录，例如 Claude Code 的 `~/.claude/skills/tikhub-api-helper/`，或 WorkBuddy 项目级 `<项目>/.workbuddy/skills/tikhub-api-helper/`。
- **直接用 CLI**：不拷贝，直接在仓库里按下面的命令调用。

该目录自包含，脱离仓库也能运行；**根目录的 `openapi.md`、`openapi说明.md`、`explore_openapi.py`、`README*` 都是开发资料，安装或发布 Skill 时不要带**。

### 2. 配置 API Token

源码不含任何凭据，调用前必须提供其一：

```bash
export TIKHUB_API_TOKEN="你的 API Token"     # Git Bash / macOS / Linux
set TIKHUB_API_TOKEN=你的 API Token         # Windows CMD
# 或在仓库根创建 .env：TIKHUB_API_TOKEN=你的 API Token（已被 .gitignore 忽略）
# 或临时传 --token <TOKEN>
```

Token 在 [TikHub User](https://user.tikhub.io) 左侧 API Keys 生成。未配置时客户端会直接报错退出；公开的免鉴权端点（如健康检查）可加 `--no-auth`。

**域名**：默认 `https://api.tikhub.io`；中国大陆用户加 `--china`（`https://api.tikhub.dev`）或设 `TIKHUB_BASE_URL`。

## 快速开始

以下命令从仓库根执行；若已在 Skill 目录内，去掉 `$S/` 前缀即可。

```bash
S=.workbuddy/skills/tikhub-api-helper

# 1. 找端点（中英文、多关键词、自然语言）
python $S/api_searcher.py "tiktok user profile"
python $S/api_searcher.py "视频评论" --limit 10
python $S/api_searcher.py tags                       # 51 个标签 + 端点数
python $S/api_searcher.py tag:TikTok-Web-API         # 列全量
python $S/api_searcher.py popular

# 2. 查参数（路径或真实 operationId 均可）
python $S/api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile

# 3. 调用
python $S/api_client.py GET /api/v1/health/check --no-auth
python $S/api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"
python $S/api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming" "count=10"
python $S/api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}' --summary
```

大响应建议 `--summary`（只看结构）或 `--output result.json`（落盘），避免整段塞进对话。更多参数见 `SKILL.md` 或 `--help`。

## API 基础信息

- 鉴权：请求头 `Authorization: Bearer <API Token>`
- 端点格式：`/api/v1/{platform}/{method}/{action}`
- 限流：规范标注 QPS 10 / 端点，超时 30–60 秒
- 重试：客户端默认不重试（TikHub 按次计费，自动重试可能重复扣费），需要时显式 `--retries N`

## 常见用例（已按 V5.3.1 核实）

```bash
# TikTok 用户资料：参数 uniqueId 或 secUid，二者至少填一个
python $S/api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"

# TikTok 作品详情 / 视频搜索
python $S/api_client.py GET /api/v1/tiktok/web/fetch_post_detail "itemId=7xxxx"
python $S/api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming"

# 抖音用户资料 / 综合搜索（POST + JSON body）
python $S/api_client.py GET /api/v1/douyin/web/handler_user_profile "sec_user_id=xxx"
python $S/api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}'

# 小红书笔记搜索 / YouTube 视频搜索
python $S/api_client.py GET /api/v1/xiaohongshu/app_v2/search_notes "keyword=美食"
python $S/api_client.py GET /api/v1/youtube/web/search_video "search_query=music"

# 抖音热榜端点浏览
python $S/api_searcher.py tag:Douyin-Billboard-API
```

> 旧版文档中的 `/api/v1/douyin/web/fetch_user_profile`、`/api/v1/youtube/web/get_trending_videos`、`/api/v1/xiaohongshu/web_v2/fetch_search_notes` 在 V5.3.1 中已不存在。另外 **TikTok** 的用户资料端点用 `uniqueId` / `secUid`，不是 `sec_user_id`；`sec_user_id` 是**抖音** `/api/v1/douyin/web/handler_user_profile` 的必填参数，两者不要混用。调用前一律用 `detail:` 核对。

## 与 OpenClaw X/Twitter 工作流配合

TikHub 适合做多平台公开数据发现，例如跨 TikTok、小红书、YouTube、Twitter/X 和 Reddit 查找趋势、账号、视频或帖子。如果工作流后续需要 OpenClaw 中的账号级 X/Twitter 操作，可以把 TikHub 结果先整理成经过审阅的 source packet，再交给专门的 X/Twitter 插件处理。

- 使用 TikHub 做跨平台发现和公开数据查询。
- 使用 TweetClaw 这类 OpenClaw 插件处理账号级 X/Twitter 搜索、回复发现、用户资料查询、监控、媒体相关流程，或经过明确确认的发帖和回复操作。
- 不要在工具之间复制 API Token、Cookie 或会话材料。只传递已审阅的 URL、帖子 ID、账号、查询词、时间范围和摘要。
- 发帖、回复、关注、私信、资料修改等写操作必须在目标工具中再次获得用户确认。

## 本地验收与发布

发布前跑过的冒烟测试（**全部离线，不消耗任何 API 额度**）：

```bash
S=.workbuddy/skills/tikhub-api-helper
python -m py_compile $S/api_searcher.py $S/api_client.py
python $S/api_searcher.py "tiktok user profile" --limit 3    # 首选结果应为 fetch_user_profile
python $S/api_searcher.py "视频评论" --limit 3                 # 中文检索
python $S/api_searcher.py tags                                 # 51 个标签
python $S/api_searcher.py tag:Douyin-Billboard-API --json      # 31 条，不截断
python $S/api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile
python $S/api_client.py --help
python explore_openapi.py                                      # 1067 端点
```

**自包含检查**：把 `.workbuddy/skills/tikhub-api-helper/` 拷到仓库外的临时目录再运行上面的检索命令，应同样成功（`find_spec()` 会指向同目录的 `openapi.json`）。

- 推送源码仓库：`git add -A && git commit -m "..." && git push origin main`
- 发布 Skill 包：只打包 `.workbuddy/skills/tikhub-api-helper/` 这一个目录，最终应恰好是四个文件（`SKILL.md` / `api_searcher.py` / `api_client.py` / `openapi.json`）。不要带根目录的开发资料，也排除 `__pycache__/`、`.env` 等本地生成物。

> **安全提醒**：旧版本曾在源码里内置默认 API Token，虽已移除，但 **Git 历史中仍可能残留**。请在 [TikHub User](https://user.tikhub.io) 轮换该 Token，且不要把它写进仓库文件。

## 错误处理

| 错误 | 处理 |
|------|------|
| `No TikHub API token found` | 配置 `TIKHUB_API_TOKEN` / `.env` / `--token` |
| `401 / 403` | Token 无效或无权限；用 `--no-auth` 对比测试公开端点 |
| `422` | 参数缺失或名字不对，用 `detail:` 核对 |
| `429` | 限流，等待后重试 |
| `Connection error` | 大陆用户加 `--china` |
| `openapi.json not found` | 设 `TIKHUB_OPENAPI_PATH` 或 `--spec` |

## 相关链接

- 源码仓库：https://github.com/liangdabiao/tikhub_api_skill
- TikHub 官网：https://www.tikhub.io · API 文档：https://api.tikhub.io · Apifox：https://docs.tikhub.io
- 用户后台：https://user.tikhub.io · 监控：https://monitor.tikhub.io · GitHub：https://github.com/TikHub

## 感谢

**linux.do**

## 许可证

本项目仅供学习和参考使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

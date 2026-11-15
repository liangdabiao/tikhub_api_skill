# TikHub API Helper

一个 Agent Skill：用中文或英文搜到需要的 TikHub API 端点，查清参数，然后直接调用。覆盖抖音、TikTok、小红书、B 站、微博、知乎、快手、Instagram、YouTube、X/Twitter、Reddit 等平台的公开数据（用户资料、作品、评论、搜索、热榜、趋势）。

仓库：https://github.com/liangdabiao/tikhub_api_skill
内置规范：V5.3.1，1067 个端点 / 51 个分类。

## 安装

**这个仓库的根目录就是 Skill 目录**，clone 到你的 skills 目录即可，不用再找子目录：

```bash
# Claude Code
git clone https://github.com/liangdabiao/tikhub_api_skill.git ~/.claude/skills/tikhub-api-helper

# WorkBuddy 项目级（在项目根目录执行）
git clone https://github.com/liangdabiao/tikhub_api_skill.git .workbuddy/skills/tikhub-api-helper
```

只想当命令行工具用也行，clone 到任意目录后直接跑下面的命令。

目录里就 5 个文件：`SKILL.md`（Skill 定义）、`api_searcher.py`（搜端点）、`api_client.py`（发请求）、`openapi.json`（API 规范）、`README.md`。**运行时只读同目录的 `openapi.json`**，不联网下载文档，也不依赖目录外的任何文件。

## 配置 Token

源码里不含任何 Token。到 [TikHub User](https://user.tikhub.io) 左侧 API Keys 生成，然后任选一种：

```bash
export TIKHUB_API_TOKEN="你的 Token"     # Git Bash / macOS / Linux
set TIKHUB_API_TOKEN=你的 Token         # Windows CMD
python api_client.py GET ... --token 你的 Token   # 单次临时传
```

没配 Token 时脚本会直接报错退出，不会发出空鉴权请求。公开的免鉴权端点（如健康检查）可以加 `--no-auth`。

> 大陆访问不了默认域名时加 `--china`（走 https://api.tikhub.dev）。

## 三步用法

```bash
# 1. 搜端点：中英文、多个词、自然语言都行，按相关度排序
python api_searcher.py "tiktok user profile"
python api_searcher.py "视频评论" --limit 10
python api_searcher.py tags                     # 列出全部 51 个分类
python api_searcher.py tag:TikTok-Web-API       # 看某个分类下的所有端点

# 2. 查详情：必填项、类型、返回结构，以及一条可直接复制的调用命令
python api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile

# 3. 调用
python api_client.py GET /api/v1/health/check --no-auth
python api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"
python api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}'
```

参数写成 `k=v`；POST 时 `k=v` 进 query、JSON 进 body。大响应用 `--summary`（只看结构）或 `--output result.json`（存文件），别把整段结果灌回对话。完整参数见 `SKILL.md` 或 `--help`。

## 常用例子

| 想做什么 | 命令 |
|---|---|
| TikTok 用户资料 | `python api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"` |
| TikTok 视频搜索 | `python api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming" "count=10"` |
| 抖音综合搜索 | `python api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"乐高"}'` |
| 小红书笔记搜索 | `python api_client.py GET /api/v1/xiaohongshu/app_v2/search_notes "keyword=美食"` |
| YouTube 视频搜索 | `python api_client.py GET /api/v1/youtube/web/search_video "search_query=music"` |

端点路径和参数名会随官方版本变化，**调用前先用 `detail:` 核对**。注意抖音用户资料用 `sec_user_id`，TikTok 用 `uniqueId` / `secUid`，别混用。

## 注意

- TikHub 按次计费，脚本**默认不自动重试**（避免重复扣费）；确实需要时显式加 `--retries N`。
- `/api/v1/demo/...` 返回缓存的示例数据，调研真实数据不要用。
- 不要把 Token 写进仓库文件；本仓库不含 `.gitignore`，用环境变量最安全。
- 限流约 QPS 10/端点：遇到 `429` 稍等再试；`422` 多半是参数名不对，用 `detail:` 查。
- `HTTP 400` 时服务端给的原因和文档链接会打到 stderr；V5.3.1 有少数端点本身不可用，清单见 `SKILL.md`。
- 各端点单价不同，用 `GET /api/v1/tikhub/user/get_endpoint_info "endpoint=/api/v1/..."` 查；账户接口不计费，4xx 通常也不扣费。
- 跨平台批量统计时先确认响应字段路径（TikTok 搜索结果在 `search_item_list`、Reddit 评论在 `commentForest`、YouTube 给的是相对时间），细节见 `SKILL.md`。

## 链接

- 仓库：https://github.com/liangdabiao/tikhub_api_skill
- TikHub 官网 https://www.tikhub.io · API 文档 https://api.tikhub.io · 用户后台 https://user.tikhub.io
- 感谢社区 https://linux.do

仅供学习和参考使用。

# TikHub API Helper

> Source repository: https://github.com/liangdabiao/tikhub_api_skill
>
> **This GitHub repo holds the source and docs; the actual installable/publishable Skill is a single folder: `.workbuddy/skills/tikhub-api-helper/`.** Copy that folder and it runs. Everything else at the repo root is development material and is not needed to install the Skill.

An Agent Skill that searches and calls TikHub APIs from a local OpenAPI spec. TikHub exposes public data endpoints for Douyin, TikTok, Xiaohongshu, Bilibili, Weibo, Zhihu, Kuaishou, Instagram, YouTube, Twitter/X, Reddit and more.

Current spec: **V5.3.1** (2025-09-21), **1067 endpoints / 51 tags**. Tags change with upstream releases, so use `api_searcher.py tags` for a live list instead of hard-coded counts.

## What was broken and is now fixed (2026-11-14)

| Problem | Fix |
|---------|-----|
| The old `.claude/skills/` nesting was the wrong layout; skill files were flattened into the repo root and `openapi.json` was separated from the scripts | Made `.workbuddy/skills/tikhub-api-helper/` the **single authoritative, publishable** folder with all four files self-contained; removed `.claude/` and obsolete repo-level docs |
| Keyword search required the whole query string to match verbatim, so `"tiktok user profile"` returned only one Demo endpoint | Token-based, relevance-ranked Chinese/English search |
| `tag:` was capped at `limit=50`, silently truncating 58-endpoint tags | Lists all endpoints by default |
| Example operationIds in the docs (`tiktok_web_fetch_user_profile_get`, etc.) no longer exist | Search by keyword, then inspect by path or the real operationId |
| Detail output dumped an entire operation including huge schemas into the context | Compact detail (parameters / response shape / ready-to-run `example_call`); `--full` for raw |
| Client silently sent an empty `Bearer` header and returned a confusing 403 | Token loaded from several sources, fails fast with actionable message; no credentials in source |
| Git Bash / MSYS2 rewrote `/api/v1/...` into `D:/.../PortableGit/api/v1/...` | Client normalizes it back automatically |
| POST dropped `k=v` query parameters | Both GET and POST support query params and JSON bodies |
| `explore_openapi.py` hard-coded `D:/tikhub_api_skill/openapi.json` and crashed | Reuses `find_spec()` |
| Several documented paths/params no longer exist | Corrected against V5.3.1 |

## Which API document to use

The dev repo holds two copies of the same spec: `openapi.json` inside the skill folder and `openapi.md` at the repo root. **The skill ships only `openapi.json`; `openapi.md` is excluded from releases**:

| | `openapi.json` | `openapi.md` |
|---|---|---|
| Nature | Upstream OpenAPI 3.0.1 spec | Human-facing widdershins render of the same spec |
| Size / shape | 4.3 MB, fully structured paths, params, schemas | 4.0 MB / 108k lines, 3009 H1 + 9918 H3 headings polluted by markdown inside API descriptions |
| Retrieval | `json.load()` then fetch exactly one operation by path/tag/operationId, injecting ~1 KB | Whole-file scan only; ~1M tokens in full, with 8 language samples repeated per endpoint |
| Parameters | 2144 inline params (784 required) with type/default/description | Rendered from the same spec, nothing extra; response samples are mostly `"string"` placeholders |

They are the same source: all 1067 JSON paths appear in the MD; the 8 extra `/api/v1/...` strings in the MD are prose examples (e.g. `/api/v1/tikhub/user/`), not real endpoints. `openapi.md` is a dev-only human-readable copy, not part of the skill package and not shipped. Full measurements are in `SKILL.md`.

## Project structure

```
tikhub_api_skill/
├── .workbuddy/skills/tikhub-api-helper/  # ★ the only skill package - ship just this folder
│   ├── SKILL.md                         # definition + workflow
│   ├── openapi.json                     # single runtime data source (4.3 MB)
│   ├── api_searcher.py                  # search / detail
│   └── api_client.py                    # calls
│
├── openapi.md                           # dev-only derived doc (not packaged)
├── openapi说明.md                       # dev-only auth notes (not packaged)
├── explore_openapi.py                   # dev-only spec explorer (not packaged)
├── README.md / README_EN.md             # repo docs (not packaged)
└── .gitignore
```

**`.workbuddy/skills/tikhub-api-helper/` is self-contained**: copy that folder anywhere and it runs, because `openapi.json` sits next to the scripts. It does not depend on the README, `openapi.md`, or any repo structure above it. Override the spec path with `TIKHUB_OPENAPI_PATH` / `--spec` if needed.

## Setup

### 1. Get the Skill

```bash
git clone https://github.com/liangdabiao/tikhub_api_skill.git
cd tikhub_api_skill
```

The Skill is `.workbuddy/skills/tikhub-api-helper/` (four files). Pick one:

- **Install into an agent**: copy that whole folder into your skills directory, e.g. Claude Code's `~/.claude/skills/tikhub-api-helper/`, or a WorkBuddy project-level `<project>/.workbuddy/skills/tikhub-api-helper/`.
- **Use the CLI directly**: no copy needed, just run the commands below from the repo.

The folder is self-contained and runs outside the repo. **Do not package `openapi.md`, `openapi说明.md`, `explore_openapi.py`, or the READMEs when installing or shipping the Skill.**

### 2. Configure an API token

No credentials are baked into the source; provide one of these:

```bash
export TIKHUB_API_TOKEN="your token"       # Git Bash / macOS / Linux
set TIKHUB_API_TOKEN=your token            # Windows CMD
# or create .env at the repo root: TIKHUB_API_TOKEN=your token  (gitignored)
# or pass --token <TOKEN> for a single call
```

Generate a token under API Keys in [TikHub User](https://user.tikhub.io). Without one the client exits with a clear error; public endpoints such as health check can use `--no-auth`.

**Domain**: default `https://api.tikhub.io`; users in mainland China can add `--china` (`https://api.tikhub.dev`) or set `TIKHUB_BASE_URL`.

## Quick start

Run from the repo root; drop the `$S/` prefix when already inside the skill directory.

```bash
S=.workbuddy/skills/tikhub-api-helper

# 1. Find endpoints (Chinese/English, multiple words, natural language)
python $S/api_searcher.py "tiktok user profile"
python $S/api_searcher.py "video comments" --limit 10
python $S/api_searcher.py tags                       # 51 tags + counts
python $S/api_searcher.py tag:TikTok-Web-API         # full list
python $S/api_searcher.py popular

# 2. Inspect parameters (path or real operationId)
python $S/api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile

# 3. Call
python $S/api_client.py GET /api/v1/health/check --no-auth
python $S/api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"
python $S/api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming" "count=10"
python $S/api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"lego"}' --summary
```

For large responses use `--summary` (shape only) or `--output result.json`. See `SKILL.md` or `--help` for all flags.

## API basics

- Auth header: `Authorization: Bearer <API Token>`
- Endpoint pattern: `/api/v1/{platform}/{method}/{action}`
- Rate limit noted in the spec: QPS 10 per endpoint; timeout 30–60 s
- Retries default to 0 (TikHub bills per request; auto-retry can double-charge). Opt in with `--retries N`

## Common use cases (verified against V5.3.1)

```bash
# TikTok user profile - provide uniqueId or secUid (at least one)
python $S/api_client.py GET /api/v1/tiktok/web/fetch_user_profile "uniqueId=tiktok"

# TikTok post detail / video search
python $S/api_client.py GET /api/v1/tiktok/web/fetch_post_detail "itemId=7xxxx"
python $S/api_client.py GET /api/v1/tiktok/web/fetch_search_video "keyword=gaming"

# Douyin profile / general search (POST + JSON body)
python $S/api_client.py GET /api/v1/douyin/web/handler_user_profile "sec_user_id=xxx"
python $S/api_client.py POST /api/v1/douyin/search/fetch_general_search_v1 --body '{"keyword":"lego"}'

# Xiaohongshu note search / YouTube video search
python $S/api_client.py GET /api/v1/xiaohongshu/app_v2/search_notes "keyword=food"
python $S/api_client.py GET /api/v1/youtube/web/search_video "search_query=music"

# Browse Douyin billboard endpoints
python $S/api_searcher.py tag:Douyin-Billboard-API
```

> Removed in V5.3.1: `/api/v1/douyin/web/fetch_user_profile`, `/api/v1/youtube/web/get_trending_videos`, `/api/v1/xiaohongshu/web_v2/fetch_search_notes`. Also note **TikTok**'s user profile takes `uniqueId` / `secUid`, not `sec_user_id`; `sec_user_id` is the required parameter of the **Douyin** endpoint `/api/v1/douyin/web/handler_user_profile`. Do not mix them up. Always check with `detail:` before calling.

## Pairing with OpenClaw X/Twitter workflows

TikHub is a good fit for broad public discovery across TikTok, Xiaohongshu, YouTube, Twitter/X, Reddit, and other platforms. If the next step requires account-scoped X/Twitter work inside OpenClaw, first turn the TikHub results into a reviewed source packet, then hand that packet to a dedicated X/Twitter plugin.

- Use TikHub for cross-platform discovery and public data lookups.
- Use an OpenClaw plugin such as TweetClaw for account-backed X/Twitter search, reply discovery, user lookup, monitoring, media-aware workflows, or explicitly approved post and reply actions.
- Do not copy API tokens, cookies, or session material between tools. Pass only reviewed URLs, post IDs, handles, queries, date ranges, and summaries.
- Posting, replying, following, direct messages, profile edits, and other write actions must be confirmed again in the destination tool.

## Local verification and release

Smoke tests run before release (**fully offline, zero API credits used**):

```bash
S=.workbuddy/skills/tikhub-api-helper
python -m py_compile $S/api_searcher.py $S/api_client.py
python $S/api_searcher.py "tiktok user profile" --limit 3    # top hit should be fetch_user_profile
python $S/api_searcher.py tags                                # 51 tags
python $S/api_searcher.py tag:Douyin-Billboard-API --json     # 31 endpoints, not truncated
python $S/api_searcher.py detail:/api/v1/tiktok/web/fetch_user_profile
python $S/api_client.py --help
python explore_openapi.py                                     # 1067 endpoints
```

**Self-contained check**: copy `.workbuddy/skills/tikhub-api-helper/` to a temp folder outside the repo and rerun the search commands above. They must still work, with `find_spec()` pointing at the co-located `openapi.json`.

- Push the source repo: `git add -A && git commit -m "..." && git push origin main`
- Ship the Skill: package only `.workbuddy/skills/tikhub-api-helper/`, which should contain exactly four files (`SKILL.md` / `api_searcher.py` / `api_client.py` / `openapi.json`). Exclude the dev material at the repo root as well as local artifacts such as `__pycache__/` and `.env`.

> **Security note**: an older revision baked a default API token into the source. It has been removed, but **the Git history may still contain it**. Rotate that token in [TikHub User](https://user.tikhub.io) and never commit credentials.

## Error handling

| Error | Action |
|-------|--------|
| `No TikHub API token found` | Set `TIKHUB_API_TOKEN`, `.env`, or `--token` |
| `401 / 403` | Invalid token or missing scope; compare with `--no-auth` on a public endpoint |
| `422` | Missing/wrong parameter name; check `detail:` |
| `429` | Rate limited; wait before retrying |
| `Connection error` | Mainland China users: add `--china` |
| `openapi.json not found` | Set `TIKHUB_OPENAPI_PATH` or `--spec` |

## Links

- Source repo: https://github.com/liangdabiao/tikhub_api_skill
- https://www.tikhub.io · https://api.tikhub.io · https://docs.tikhub.io
- User dashboard: https://user.tikhub.io · Status: https://monitor.tikhub.io · https://github.com/TikHub

## Thanks

**linux.do**

## License

For learning and reference purposes only.

## Contributing

Issues and Pull Requests are welcome!

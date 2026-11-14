
## openapi.json说明：

TikHub.io的大多数API都是RESTFUL的，这意味着你只需要使用基本的HTTP请求即可完成调用。

所有的API都是基于OPenAPI规范进行编写的，这意味着你可以使用我们的openapi.json自动生成任何形式的API文档：

### 鉴权
简介

接口文档中带有🔒图标的端点需要在请求头中携带API Token才可以调用，调用这些接口会使用你账户中的剩余免费额度或账户余额，同时每一个端点还会根据API Token所有者的email地址进行请求速率的限制，每个端点之间都有彼此独立的RPS（Requests per second），在大多数情况下，用户可以每秒请求5次同一个端点。

生成API Token

获取API Token的步骤也很简单，你只需要登录到我们的用户后台 TikHub User，然后点击左侧的API Keys就可以生成你自己的API Token，同时，你可以自定义API Token的权限（Scopes），也可以设置API Token的过期日期（Expire Date），还可以手动暂时关闭API Token（Status）。

在API文档网页上使用

当你完成上面的步骤后，你可以复制你的API Token，然后回到我们的Swagger UI网页，点击页面右侧的绿色Authorize，然后在弹窗底部的Value输入框中粘贴API Token即可完成鉴权。

在HTTP请求中使用

如果你想在HTTP请求中携带API Token，请仔细阅读下方的格式，并且需要在请求头中携带一个叫Authorization的字段，下面我将给出一个JSON作为header的示范：

{

"Authorization":"Bearer Your_API_Token"

}

### 配置 API Token

本项目**不内置任何真实 Token**，源码里也没有默认凭据（历史上曾内置，已移除）。调用前任选一种方式提供：

```bash
export TIKHUB_API_TOKEN="你的 API Token"    # Git Bash / macOS / Linux
set TIKHUB_API_TOKEN=你的 API Token        # Windows CMD
```

也可在 Skill 目录（或仓库根）创建 `.env`，已被 `.gitignore` 忽略：

```
TIKHUB_API_TOKEN=你的 API Token
```

客户端读取顺序：`--token` → `TIKHUB_API_TOKEN` → `TIKHUB_TOKEN` → `.env`。未配置时直接报错退出，不会发出带空 `Bearer` 的请求。Token 在 https://user.tikhub.io 的 API Keys 生成。

> 注：本文件与 `openapi.md` 都是开发期资料，发布 Skill 时不打包。



# ClawDone WeChat Bridge

这个子项目把 `ClawDone` 接到微信上。

它的定位很简单：

- `ClawDone` 继续负责 SSH、tmux、pane、todo 和权限
- `wechat-bridge` 负责扫码登录微信、收微信消息、把消息转成 `ClawDone API` 调用，再把结果发回微信

## 要求

- Node.js `22+`
- 一个已经能正常工作的 `ClawDone` 服务
- `ClawDone` 的 token
  - 权限可以和你网页端一样
  - 最推荐的做法是单独发一个同角色 token 给 bridge，而不是直接复用浏览器里的那个

## 启动

先确保 `ClawDone` 已经在跑：

```bash
python -m clawdone serve \
  --host 0.0.0.0 \
  --port 8787 \
  --rbac-tokens-json '{"web-admin":"admin","wechat-admin":"admin"}'
```

再准备 bridge 配置：

```bash
cd wechat-bridge
cp config.example.json config.json
```

把 `config.json` 里的这些值改掉：

- `clawdoneBaseUrl`
- `clawdoneToken`
- `users`
- 可选的 `defaultProfile` / `defaultTarget`

如果你还不知道自己的微信 sender id，可以先把：

```json
"discoveryMode": true
```

打开。启动后随便给机器人发一条消息，它会把你的 sender id 回给你。填回 `users` 后再把 `discoveryMode` 关掉。

安装依赖并启动：

```bash
npm install
npm start -- --config ./config.json
```

第一次启动会在终端里打印微信二维码。用你的微信扫码并确认后，bridge 就会开始收消息。

## 第一次接入流程

下面这条路径是从零到真正能在微信里发第一个 task 的最短流程。

### 1. 启动 ClawDone 主服务

如果你本机 `python` 命令不可用，直接用 `python3`：

```bash
python3 -m clawdone serve \
  --host 0.0.0.0 \
  --port 8787 \
  --rbac-tokens-json '{"web-admin":"admin","wechat-admin":"admin"}'
```

这里的意思是：

- `web-admin` 给网页端用
- `wechat-admin` 给微信桥用
- 两者都是 `admin`，所以权限和网页一致

### 2. 准备 bridge 配置

```bash
cd /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge
cp config.example.json config.json
```

把 `config.json` 至少改成这样：

```json
{
  "clawdoneBaseUrl": "http://127.0.0.1:8787",
  "clawdoneToken": "wechat-admin",
  "stateFile": "~/.clawdone/wechat-bridge-state.json",
  "discoveryMode": true,
  "users": {}
}
```

这一步先开 `discoveryMode`，因为大多数人一开始并不知道自己的微信 sender id。

### 3. 安装并启动微信桥

```bash
cd /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge
npm install
npm start -- --config ./config.json
```

如果你不想切目录，也可以：

```bash
npm --prefix /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge install
npm --prefix /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge start -- --config /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge/config.json
```

### 4. 扫码登录机器人微信

启动后终端会打印一个二维码。

你需要：

- 用一个微信号去扫它
- 在手机里确认登录

这个二维码的作用是“让 bridge 登录一个微信机器人账号”，不是“给用户做授权绑定”。

### 5. 拿到你自己的 sender id

bridge 登录成功后，用你的微信给这个机器人账号发任意一条消息，例如：

```text
hello
```

因为此时 `discoveryMode` 是开启的，bridge 会回你：

- 你的 sender id
- 提示你把这个 sender id 写进 `config.users`

同时终端日志里也会打印这个 sender id。

### 6. 把自己加入白名单

把 `config.json` 改成类似这样：

```json
{
  "clawdoneBaseUrl": "http://127.0.0.1:8787",
  "clawdoneToken": "wechat-admin",
  "stateFile": "~/.clawdone/wechat-bridge-state.json",
  "discoveryMode": false,
  "users": {
    "wxid_yourself": {
      "name": "me",
      "defaultProfile": "office",
      "defaultTarget": "codex:0.0"
    }
  }
}
```

然后重启 bridge：

```bash
cd /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge
npm start -- --config ./config.json
```

### 7. 在微信里选中你要控制的 agent

建议第一次严格按下面顺序发：

```text
/help
/profiles
/use-profile office
/panes
/use codex:0.0
/where
```

这几步的含义分别是：

- `/profiles`：列出 ClawDone 当前可见的 profile
- `/use-profile office`：选择一个 SSH target / profile
- `/panes`：读取这个 profile 下远程 tmux 的 pane
- `/use codex:0.0`：选择你真正跑着 agent 的 pane
- `/where`：确认当前上下文

### 8. 发第一个 task

上下文选好后，直接发自然语言就行：

```text
请检查 auth 模块的 flaky test，修复后告诉我原因。
```

bridge 会做这些事：

- 调 `ClawDone /api/send`
- 把文字发到当前 pane
- 回你一条“已发送”
- 再自动轮询几次 pane 输出
- 把新增输出回发到微信

### 9. 查看输出 / 中断 / 补操作

最常用的是这几个：

```text
/status
/status 150
/interrupt
/history 10
/todos
```

如果网页端有能力、但 bridge 还没封装成聊天命令，就直接走：

```text
/api GET /api/dashboard
/api GET /api/profiles
/api GET /api/pane?profile=office&target=codex%3A0.0&lines=80
```

## 微信里怎么用

先发：

```text
/help
```

常用命令：

```text
/profiles
/use-profile office
/panes
/use codex:0.0
/where
/status
/interrupt
/history 10
/todos
/todo 修复 flaky test || 看 auth 模块最近失败用例
/confirm <高风险 prompt>
/api GET /api/profiles
```

不带 `/` 的普通文本会直接发到当前 pane，等价于网页里的发送框。

例如：

```text
请检查 auth 模块的 flaky test，修复后总结原因。
```

## 推荐操作顺序

日常使用时，最稳的顺序是：

1. `/where`
2. 如果上下文不对，就 `/use-profile ...` 和 `/use ...`
3. 直接发任务文本
4. 看自动回传结果
5. 需要更多输出时发 `/status`
6. 需要停止时发 `/interrupt`

这样最不容易把任务发错 pane。

## 权限模型

这个 bridge 不是 share-token 只读代理。

它会带着 `Authorization: Bearer <token>` 去调用 `ClawDone`，所以：

- 你的网页端是什么角色
- bridge 用的 token 也是什么角色
- 它看到和能调用的 API 与网页一致

另外，bridge 会自动加：

```text
X-ClawDone-Actor: wechat:<wxid>
```

这样审计里能分清楚操作来自微信，而不是网页。

## 原始 API 代理

如果某个能力 bridge 还没做成友好的聊天命令，可以直接走：

```text
/api GET /api/dashboard
/api GET /api/pane?profile=office&target=codex%3A0.0&lines=80
/api POST /api/todos {"profile":"office","target":"codex:0.0","title":"Check logs","detail":"Look at nginx errors"}
```

这条 `/api` 命令的意义就是保证微信端和网页端能共享同一批后端能力。

## 状态文件

bridge 会把每个微信用户当前选中的：

- `profile`
- `target`

持久化到 `stateFile`。

默认路径是：

```text
~/.clawdone/wechat-bridge-state.json
```

## 已知边界

- 当前只支持文本消息，不处理图片/语音输入
- 自动输出回传是基于轮询 `/api/pane`，不是字级流式
- 微信登录会话由 `wechat-ai` 管理，默认保存在 `~/.wai`

## 常见问题

### 1. 在仓库根目录执行 `npm install` 报错

Node 项目不在仓库根目录，而在 `wechat-bridge`：

```bash
cd /Users/bangshuaipeng/Study/PocketClaw/wechat-bridge
npm install
```

### 2. 微信里发消息提示 `No current profile`

说明你还没选 profile。先发：

```text
/profiles
/use-profile office
```

### 3. 微信里发消息提示 `No current target`

说明你还没选 pane。先发：

```text
/panes
/use codex:0.0
```

### 4. 高风险命令被拦住

如果 `ClawDone` 开了 `risk-policy confirm`，高风险发送会被拦住。这时按提示改用：

```text
/confirm <原始内容>
```

# PocketClaw

PocketClaw 是一个面向手机端的远程控制面板：

- 在手机上配置 SSH 地址、用户名、密码 / key
- 连接到远程 Linux 服务器
- 读取服务器上 `tmux` 里的 session / window / pane
- 把 pane 当成独立的 Codex / vibe agent 线程管理
- 给每个 agent pane 起本地别名
- 用手机浏览器本地语音转文字，把命令发送给对应 agent

这次实现已经从“只控制本机 tmux”升级为“通过 SSH 控制远程 tmux agent”。

## 已实现能力

- 手机端保存多个 SSH Profile
- Profile 字段包含：别名、主机、端口、用户名、密码、SSH key 路径、tmux 路径
- 远程列出 `tmux session / window / pane`
- 把 `pane` 作为 agent 线程目标进行控制
- 给目标 pane 保存本地 alias，例如 `backend-agent`
- 语音转文字在手机浏览器本地完成
- 文本命令通过服务端 SSH 发到目标机器的 tmux pane
- 支持 `Ctrl+C`
- 支持查看目标 pane 最近输出
- 支持访问 token
- 仍保留本地 tmux CLI 子命令，便于调试

## 目录

- `pocketclaw/app.py:1`：Web UI、SSH 配置存储、远程 tmux 控制、CLI
- `pocketclaw/__main__.py:1`：`python -m pocketclaw` 入口
- `tests/test_app.py:1`：tmux、本地配置、远程 snapshot、鉴权测试
- `pyproject.toml:1`：项目依赖与入口

## 安装

建议先安装为可编辑模式：

```bash
python3 -m pip install -e .
```

这会安装 `paramiko`，用于服务端发起 SSH 连接。

## 启动服务

```bash
python3 -m pocketclaw serve --host 0.0.0.0 --port 8787 --token your-secret
```

也可以指定配置文件保存位置：

```bash
python3 -m pocketclaw serve --host 0.0.0.0 --port 8787 \
  --token your-secret \
  --store-path ~/.pocketclaw/profiles.json
```

启动后在手机浏览器打开：

```text
http://<你的服务器IP>:8787
```

## 手机端使用流程

### 1. 新建 SSH Profile

在页面里填写：

- Profile 名称，例如 `office-server`
- SSH Host，例如 `192.168.1.20`
- SSH Port，例如 `22`
- Username，例如 `ubuntu`
- Password，或者填写 SSH key path
- tmux binary，默认 `tmux`

点击 `Save profile` 保存，点击 `Test SSH` 测试是否可连通。

### 2. 选择远程 agent

保存成功后，页面会自动拉取远程：

- `tmux sessions`
- `tmux windows`
- `tmux panes`

页面中：

- `session` 对应 tmux 会话
- `window` 对应 tmux 窗口
- `pane` 对应具体 agent 线程

例如：

- `codex:0.0`
- `codex:1.0`
- `research:2.1`

你可以给选中的 pane 设置 alias，比如：

- `backend-agent`
- `frontend-codex`
- `release-bot`

### 3. 本地语音转文字并发送

- 点击 `Start voice`
- 手机浏览器本地完成语音转文字
- 识别结果写入命令文本框
- 点击 `Send to agent`

PocketClaw 会通过服务端 SSH 执行类似动作：

```bash
tmux send-keys -t codex:0.0 -l 'your command'
tmux send-keys -t codex:0.0 Enter
```

### 4. 中断或查看输出

- `Send Ctrl+C`：向目标 pane 发送中断
- `Refresh output`：查看最近 pane 输出

## 远程服务器准备

在远程服务器上先运行你的 agent，例如：

```bash
tmux new -s codex
codex
```

如果你想在不同窗口 / pane 跑多个 agent，可以继续：

```bash
tmux new-window -t codex -n backend
codex
```

或者在同一个窗口里拆 pane。

## CLI 用法

这些 CLI 子命令仍然针对 PocketClaw 所在机器本地的 tmux，适合调试：

### 列出本地 tmux 会话

```bash
python3 -m pocketclaw list-sessions
```

### 向本地 tmux 会话发命令

```bash
python3 -m pocketclaw send --session codex --command "run tests"
```

### 查看本地 tmux 输出

```bash
python3 -m pocketclaw capture --session codex --lines 80
```

## 配置文件

默认保存到：

```text
~/.pocketclaw/profiles.json
```

其中会包含：

- SSH 主机信息
- 用户名
- 密码（如果你填写了）
- pane alias 映射

## 安全说明

- 当前版本会把 SSH 密码保存在 PocketClaw 服务器本地 JSON 文件中
- 适合内网、自托管、受信机器
- 更推荐用 SSH key，并把 PocketClaw 放在 Tailscale / WireGuard / 局域网 / SSH 隧道后面
- 如果开放到公网，请至少开启 `--token`，并最好再加 HTTPS 反向代理

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 下一步可扩展

- 多服务器分组
- 历史命令模板
- 一键创建 tmux session / window / pane
- WebSocket 实时日志流
- Host key 校验策略
- 使用系统 Keychain / Secret Store 保存 SSH 密码

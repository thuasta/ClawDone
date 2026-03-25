# ClawDone Quick Start

## 1. 主机端（服务端）

```bash
cd /Users/zhangboshi/Downloads/py7cpp/ClawDone

python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

python -m clawdone serve \
  --host 0.0.0.0 \
  --port 8000 \
  --token 1
```

## 2. 客户端（手机/浏览器）

```text
http://<主机IP>:8787
```

1. 在 `Access token` 输入 `your-secret`。
2. 新建 SSH Target（Host/Port/Username/Password 或 SSH key）。
3. 点击 `Save target` -> `Test SSH` -> `Load tmux state`，然后发送命令。

如果手机端打不开或功能不可用，优先检查：

- 服务是否用了 `--host 0.0.0.0`（否则默认只监听本机）
- 手机和服务端是否在同一网络，且 `8787` 端口未被防火墙拦截
- 语音输入是否使用受支持的浏览器；不支持时可直接手动输入命令

## 3. 被控远端机器（首次）

在远端 SSH 里执行：

```bash
tmux new -s codex
codex
```

完成后回到客户端页面，选择 pane 即可使用。

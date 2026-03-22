# Related Works

数据快照时间：`2026-03-19`（GitHub REST API）。

筛选口径：
- 与 ClawDone 相关：`coding-agent`、`terminal/CLI`、`SSH/tmux`、`远程控制`、`Web Terminal`。
- 高星优先：主要选择 `5k+ stars`。
- 近期活跃：优先 `2025-2026` 仍有代码更新的仓库（按 `pushed_at`）。

## 1) Agent / Coding Workflow 方向

| Repo | Stars | 最近 Push (UTC) | 相似点 |
|---|---:|---|---|
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 324,404 | 2026-03-19 | 多平台代理/助手系统，和 ClawDone 同属“远程 AI 助手控制”场景 |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | 69,398 | 2026-03-19 | AI 驱动开发代理，任务执行与状态反馈链路完整 |
| [openinterpreter/open-interpreter](https://github.com/openinterpreter/open-interpreter) | 62,787 | 2026-02-09 | 用自然语言驱动终端/系统操作，和“手机发命令给 agent”思路接近 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 55,877 | 2026-03-18 | 多 agent 编排框架，适合作为任务状态流转/协作模型参考 |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 42,134 | 2026-03-17 | 终端内 AI pair programming，和 ClawDone 的 tmux-agent 控制链路高度相关 |
| [continuedev/continue](https://github.com/continuedev/continue) | 31,943 | 2026-03-18 | 面向代码工作流的 AI 自动化与检查，可参考任务模板/流程管理 |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 18,780 | 2026-03-16 | “Issue -> 修复”代理，适合参考 TODO 状态机与结果证据设计 |

## 2) 远程终端 / SSH / Web Terminal 方向

| Repo | Stars | 最近 Push (UTC) | 相似点 |
|---|---:|---|---|
| [kingToolbox/WindTerm](https://github.com/kingToolbox/WindTerm) | 30,101 | 2025-03-11 | SSH/Shell/tmux 终端能力强，可参考多会话与远程连接体验 |
| [xpipe-io/xpipe](https://github.com/xpipe-io/xpipe) | 13,890 | 2026-03-18 | 统一访问服务器基础设施，和多目标 SSH 管理很接近 |
| [coder/coder](https://github.com/coder/coder) | 12,585 | 2026-03-19 | 面向开发者与 agent 的远程开发环境，适合参考权限与隔离模型 |
| [tsl0922/ttyd](https://github.com/tsl0922/ttyd) | 11,210 | 2026-03-19 | “终端上 Web”的核心模式，与移动端远程控制体验高度相关 |
| [tmate-io/tmate](https://github.com/tmate-io/tmate) | 6,009 | 2026-03-09 | 终端共享/协作模型，可参考远程协作与会话接入方式 |
| [butlerx/wetty](https://github.com/butlerx/wetty) | 5,186 | 2026-02-16 | 浏览器终端方案，适合参考移动端 Web SSH 交互细节 |

## 备注

- 本清单是“相关性 + 高星 + 近期活跃”的工程化筛选，不是严格同类排名。
- Star 与更新时间会实时变化；如需固定版本，建议后续把 commit hash 一并记录。

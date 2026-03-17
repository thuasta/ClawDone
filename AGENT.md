本项目希望通过手机端连接服务器然后可以通过语音的方式向tmux中的codex等vibecoding-agent发送命令，实现下面的功能：


Pocket-Claw is a lightweight tool that allows you to control coding agents running on a remote server directly from your mobile device.

By connecting to a server via SSH, Pocket-Claw enables you to send commands to long-running coding agents (such as Codex or other vibe-coding agents) running inside tmux sessions. This allows developers to start tasks, trigger workflows, and interact with autonomous coding systems from anywhere using only a phone.

The project is designed for developers who frequently run AI coding agents on remote machines and want a simple, mobile-friendly way to control them without opening a full laptop environment.

Typical workflow:
Mobile Phone
      │
      │ SSH
      ▼
Remote Server
      │
      │ tmux send-keys
      ▼
Coding Agent (Codex / Vibe Agent)

Use Cases
1. Trigger an AI coding task remotely

You are away from your computer but want your coding agent to start implementing a feature.

From your phone:

ssh user@server \
"tmux send-keys -t codex 'implement login feature' Enter"

Your Codex agent immediately receives the command.

2. Run a vibe-coding workflow

Trigger an autonomous coding pipeline:

ssh user@server \
"tmux send-keys -t vibecoder 'build project and run tests' Enter"
3. Start long-running coding experiments
ssh user@server \
"tmux send-keys -t agent 'run benchmark suite' Enter"
4. Control multiple agents

If you run multiple agents:

tmux sessions

codex
backend-agent
research-agent

You can send commands independently:

tmux send-keys -t backend-agent "deploy staging" Enter
Example Workflow

Start your coding agent inside tmux:

tmux new -s codex
codex-agent

Detach:

Ctrl+b d

Send commands from your phone:

ssh server "tmux send-keys -t codex 'fix bug in auth module' Enter"
Why This Project

Running coding agents on remote servers is increasingly common, but interacting with them from mobile devices is inconvenient.

Pocket-Claw provides a minimal and powerful interface to:

control remote coding agents

trigger tasks anywhere

keep AI development workflows always accessible


你可以参考的仓库是：
https://github.com/openclaw/openclaw
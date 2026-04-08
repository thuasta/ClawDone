# ClawDone

![ClawDone logo](assets/logo.png)

[简体中文](README.zh-CN.md)

ClawDone is a mobile-friendly control surface for coding agents running on remote Linux servers.

It connects a phone browser to remote `tmux` panes over SSH, so you can inspect sessions, send commands, interrupt running work, review recent output, and track lightweight task state without opening a full laptop environment.

## What It Does

ClawDone is built around this flow:

```text
Mobile Browser
  -> ClawDone Web UI
  -> ClawDone service
  -> SSH
  -> remote tmux pane
  -> coding agent
```

In practice, it is designed for developers who:

- run Codex or other coding agents on remote machines
- keep long-lived agents inside `tmux`
- want to trigger or monitor work from a phone
- need a clearer interface than raw SSH on mobile

## Current Capabilities

### Remote target management

- Save multiple SSH targets
- Organize targets with groups, tags, favorites, and notes
- Store per-target SSH options such as timeouts, retries, and host key policy
- View aggregated dashboard status across targets

### Remote tmux control

- List remote `tmux` sessions, windows, and panes
- Treat a pane as an agent endpoint
- Assign a local alias to a pane such as `backend-agent`
- Send commands to a pane
- Send `Ctrl+C`
- Capture recent pane output

### Mobile-oriented interaction

- Built-in mobile web UI
- Command templates and command history
- Voice-to-text input in the browser
- Faster switching between targets and panes

### Task and delivery primitives

- Create todos for a specific target and pane
- Track todo status such as `todo`, `in_progress`, `blocked`, `done`, and `verified`
- Attach evidence to a task, such as output snippets or summaries
- Clean older completed todos while keeping the latest completed items visible by default
- Record audit logs and task events
- Create workflow triplets for planner / executor / reviewer patterns

### Safety and access control

- Bearer-token protection for the web service
- Optional role mapping for `admin`, `operator`, and `viewer`
- Risk policy for dangerous commands: `allow`, `confirm`, or `deny`
- SSH host key policies: `strict`, `accept-new`, and `insecure`
- Read-only session sharing via scoped share tokens

## Installation

ClawDone requires Python `3.11+`.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

This installs `paramiko` for outbound SSH connections.

## Quick Start

Start the web service:

```bash
python -m clawdone serve \
  --host 0.0.0.0 \
  --port 8787 \
  --token your-secret
```

Then open the service from your phone browser:

```text
http://<server-ip>:8787
```

If port `8787` is blocked or filtered in your LAN environment, switch to another port such as `8000`:

```bash
python -m clawdone serve --host 0.0.0.0 --port 8000 --token your-secret
```

A more explicit production-style example:

```bash
python -m clawdone serve \
  --host 0.0.0.0 \
  --port 8787 \
  --token your-secret \
  --store-path ~/.clawdone/profiles.json \
  --host-key-policy strict \
  --ssh-timeout 10 \
  --ssh-command-timeout 15 \
  --ssh-retries 1 \
  --ssh-retry-backoff-ms 300 \
  --dashboard-workers 8 \
  --risk-policy confirm
```

## WeChat Bridge

ClawDone now includes a repository-local WeChat bridge in [wechat-bridge](wechat-bridge/README.md).

It uses the official iLink-based `wechat-ai` channel to:

- log into WeChat by QR scan
- receive messages from a trusted WeChat user
- call the same ClawDone HTTP APIs that the web UI uses
- send pane output and command results back to WeChat

Quick setup:

```bash
cd wechat-bridge
cp config.example.json config.json
npm install
npm start -- --config ./config.json
```

See [wechat-bridge/README.md](wechat-bridge/README.md) for the full first-run flow, discovery mode, chat commands, and troubleshooting notes.

## Basic Usage

### 1. Add an SSH target

Create a target in the web UI with fields such as:

- name
- host and port
- username
- password or SSH key path
- `tmux` binary path
- group, tags, description, favorite flag
- optional SSH overrides

### 2. Inspect remote tmux state

After saving the target, ClawDone can load:

- sessions
- windows
- panes

Example pane identifiers:

- `codex:0.0`
- `codex:1.0`
- `research:2.1`

### 3. Bind a pane to an agent alias

Examples:

- `backend-agent`
- `frontend-agent`
- `release-bot`

### 4. Send commands or interrupt work

ClawDone sends remote commands with `tmux send-keys`, for example:

```bash
tmux send-keys -t codex:0.0 -l 'run tests and summarize failures'
tmux send-keys -t codex:0.0 Enter
```

It can also send `Ctrl+C` and capture recent pane output.

### 5. Track tasks

You can create a todo for a specific target and pane, update its status, attach evidence, and review the result later from the mobile UI or API.

The TODO view also supports a safer completed-task cleanup flow: by default, `Clear completed` removes only older `done` / `verified` items and keeps the latest `5` completed tasks visible.

## CLI

ClawDone keeps local tmux-oriented commands for debugging and scripting.

List local sessions:

```bash
python -m clawdone list-sessions
```

Send a command to a local tmux session:

```bash
python -m clawdone send --session codex --command "run tests"
```

Interrupt a local tmux session:

```bash
python -m clawdone interrupt --session codex
```

Capture recent output from a local tmux session:

```bash
python -m clawdone capture --session codex --lines 120
```

## Security Notes

- Prefer `--host-key-policy strict` in real deployments.
- Use `--token` or `--rbac-tokens-json` when exposing the service beyond localhost.
- Keep SSH credentials and the profile store in a protected location.
- Use `--risk-policy confirm` or `deny` if agents may receive destructive commands.

## Project Layout

- `clawdone/html.py` — embedded mobile web UI
- `clawdone/web.py` — HTTP routes and request handling
- `clawdone/store.py` — profiles, aliases, templates, todos, audit data
- `clawdone/remote.py` — SSH execution and remote tmux inspection
- `clawdone/local_tmux.py` — local tmux helper client
- `clawdone/cli.py` — CLI entrypoints
- `tests/test_app.py` — tests for storage, web API, and tmux behavior

## Development

Run tests:

```bash
python -m unittest tests.test_app
```

## Project Notes

- `TODO.md` tracks the current roadmap and unfinished work.
- `DONE.md` tracks completed capabilities and recently shipped changes.

## GitHub Pages

This repository now includes a static landing page under `docs/` and an automated deployment workflow at `.github/workflows/deploy-pages.yml`.

Recommended setup for this repo:

1. Commit and push the `docs/` directory to `main` or `master`.
2. Open **Settings → Pages** in the GitHub repository.
3. Set **Source** to **Deploy from a branch**.
4. Select branch `main` and folder `/docs`.
5. Save and wait for GitHub Pages to publish.

Alternative setup:

- Set **Source** to **GitHub Actions** and use `.github/workflows/deploy-pages.yml`.
- Then push to `main` or `master`, or manually run the `deploy-pages` workflow.

For the current repository, the project page is expected at:

```text
https://thuasta.github.io/ClawDone/
```

Note that this is a **project site**, not a user site. Opening `https://thuasta.github.io/` may still show a 404 page, which is expected unless a separate user site exists there.

## Roadmap

See `TODO.md` for the current roadmap and `DONE.md` for completed work.

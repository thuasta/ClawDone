# ClawDone DONE

更新完成时间：`2026-03-23`。

## 已完成能力
- [x] 手机端 Web UI 管理多 SSH target（增删改查、分组、标签、收藏）。
- [x] 远程读取 tmux `session/window/pane`，支持 pane alias。
- [x] 向远程 pane 发送命令、发送 `Ctrl+C`、抓取最近输出。
- [x] Dashboard 展示 target 在线状态、延迟、session/pane 统计。
- [x] 浏览器本地语音转文字、命令模板、最近命令历史。
- [x] Token 鉴权、SSH 超时/重试配置、Host Key Policy。

## 任务闭环
- [x] 任务数据模型与持久化存储。
- [x] TODO API（CRUD / 状态变更 / 证据提交）。
- [x] 移动端“当前 Agent”可视化。
- [x] 任务发布入口（Mobile）。
- [x] agent 回传状态与证据。
- [x] store / web / HTML 相关测试补齐。

## 进度与证据
- [x] Agent 进度卡片。
- [x] 任务时间线。
- [x] 证据查看体验。
- [x] `done -> verified` 双阶段状态。
- [x] 完成证据契约（无证据不能完成）。

## 工作流与治理
- [x] Quick Task 派单流。
- [x] 标准三角色模板：`planner -> executor -> reviewer`。
- [x] handoff packet 标准化。
- [x] WebSocket 入口声明 + SSE 实时 fallback。
- [x] 会话接管与只读分享。
- [x] 危险命令安全闸门。
- [x] RBAC 权限边界。
- [x] 凭据 Vault 化。

## 工程化
- [x] 连接中心 + 批量操作。
- [x] 任务/命令统一事件流与回放。
- [x] 审计日志。
- [x] 任务模板。
- [x] Dashboard 工作流指标与趋势基础能力。
- [x] CI workflow quality gates。
- [x] 可选工作区模板化。

## 本次新增
- [x] TODO 一键清理已完成任务。
- [x] TODO 智能清理：默认保留最近 `5` 条已完成任务，仅清理更旧的完成项。
- [x] 将历史完成项从 `TODO.md` 迁移到 `DONE.md`，只保留当前未完成路线图。

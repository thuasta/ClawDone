# ClawDone TODO

更新完成时间：`2026-03-23`。

## 当前重点
- [ ] TODO 归档而非物理删除
  - 内容：为已完成任务增加 `archived_at / archived_by`，默认列表隐藏归档项，可手动查看。
  - 价值：保留审计和历史，不怕误删。
- [ ] TODO 批量操作
  - 内容：支持批量选择后批量 `assign / verify / archive / delete`。
  - 价值：当一个 agent 产生很多 checklist 时，清理成本更低。
- [ ] TODO 过滤与搜索
  - 内容：按 `status / priority / assignee / target / keyword` 过滤。
  - 价值：任务规模起来后仍可快速定位。

## Agent Runtime
- [ ] 统一 agent runtime 抽象层
  - 内容：抽象 `list_agents / send_task / interrupt / read_output / review_result`。
  - 价值：避免逻辑写死在单一 runtime。
- [ ] Claude Code adapter
  - 内容：在统一 runtime 之上接入 `Claude Code`。
  - 价值：让 ClawDone 不只服务单一 agent。
- [ ] OpenCode adapter（视协议稳定度）
  - 内容：调研 CLI / session / output 协议后再接入。
  - 价值：扩展更多执行后端。

## Control Plane
- [ ] ClawDone MCP server
  - 内容：把后端能力暴露为 MCP tools，而不是暴露前端页面。
  - 范围：`list_targets / list_todos / create_todo / clear_completed / send_command / read_pane_output / review_todo`。
- [ ] Agent 自调用安全边界
  - 内容：加入 target scope、危险操作确认、审计日志、递归调用保护。

## Frontend
- [ ] PWA 打磨
  - 内容：继续优化手机端布局、状态反馈、缓存与断线恢复。
- [ ] 可选桌面壳
  - 内容：优先考虑 `Tauri`，不并行维护多套前端。

## 近期建议顺序
- [ ] 1. TODO 归档 + 批量操作
- [ ] 2. runtime 抽象层
- [ ] 3. Claude Code adapter
- [ ] 4. MCP server

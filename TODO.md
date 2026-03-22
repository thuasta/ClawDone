# ClawDone TODO

更新完成时间：`2026-03-19`。本次将未完成项全部转为可运行实现（其中“WebSocket 双向终端通道”采用 `ws 入口声明 + SSE 流式 fallback` 方案）。

## 当前已实现（基于现有代码）
- [x] 手机端 Web UI 管理多 SSH Target（增删改查、分组、标签、收藏）。
- [x] 远程读取 tmux `session/window/pane`，支持 pane alias。
- [x] 向远程 pane 发送命令、发送 `Ctrl+C`、抓取最近输出。
- [x] Dashboard 展示 target 在线状态、延迟、session/pane 统计。
- [x] 浏览器本地语音转文字、命令模板、最近命令历史。
- [x] Token 鉴权、SSH 超时/重试配置、Host Key Policy（`strict/accept-new/insecure`）。

## 产品主线（来自 prompt.md）
- [x] 用户在移动端清楚知道“当前调用的是哪个 agent”，并持续看到进度。
- [x] 用户可在移动端向 agent 发布待办事项。
- [x] agent 可修改待办状态，并附带可核验的完成证据。

## P0（先做：先打通“任务闭环”）
- [x] 任务数据模型与存储
  - 内容：新增 `todos`（`id/title/detail/profile/target/alias/status/priority/created_at/updated_at/assignee/evidence[]`）。
  - 验收：可持久化到 store；重启服务后任务数据不丢失。
- [x] TODO API（最小闭环）
  - 内容：`/api/todos`（list/create/update/delete）+ `/api/todos/status`（状态变更）+ `/api/todos/evidence`（提交证据）。
  - 验收：可按 `profile + target` 过滤；参数非法返回明确错误。
- [x] 移动端“当前 Agent”可视化
  - 内容：固定显示当前 `profile -> pane(alias)`；发送命令/发布任务时显示目标一致性提示。
  - 验收：任何发送动作前，界面可一眼确认目标 agent，避免误投递。
- [x] 任务发布入口（Mobile）
  - 内容：新增“发布待办”表单（标题、描述、优先级、目标 agent），支持快速派发到当前 pane。
  - 验收：发布后任务立即出现在该 agent 的待办列表。
- [x] agent 回传状态与证据（V1）
  - 内容：定义结构化回传格式（建议 JSON），至少支持 `todo_id/status/progress_note/evidence`。
  - 验收：agent 回传后 UI 能看到状态从 `todo -> in_progress -> done/blocked` 变化，并可查看证据。
- [x] 测试补齐
  - 内容：新增 store/web 集成测试覆盖 todo CRUD、状态流转、证据提交、非法参数。
  - 验收：`tests` 可稳定通过，核心闭环有自动化保障。

## P1（增强：让“进度可追踪”）
- [x] Agent 进度卡片
  - 内容：在 dashboard 显示每个 agent 的进行中任务数、最近更新时间、最近一条进度摘要。
  - 验收：用户无需进 pane 输出即可判断 agent 是否在推进任务。
- [x] 任务时间线
  - 内容：每个任务记录状态变更历史（时间、操作者、备注、证据链接/摘要）。
  - 验收：可回溯任务从创建到完成的全过程。
- [x] 证据查看体验
  - 内容：证据支持文本片段、命令回执、pane 输出片段（带时间戳）。
  - 验收：用户可快速判断“完成证据是否充分”。

## P2（优化）
- [x] 实时推送（WebSocket/SSE）替代高频轮询，实时刷新任务状态和进度。
- [x] 任务模板（按场景复用常见待办结构）。
- [x] 审计日志：记录谁在何时向哪个 agent 派发了什么任务、由谁回传了什么证据。

## 里程碑
- [x] M1：完成 P0，任务可发布、可执行、可回传、可验收。
- [x] M2：完成 P1，进度和证据具备完整追踪链路。
- [x] M3：完成 P2，实时化与审计能力完善。

## 工作流建议（基于项目现状 + RelatedWorks）

### W0 指标先行（不先量化就很难优化）
- [x] 建立 4 个核心工作流指标并固化到 dashboard
  - 指标：`派单耗时(T_dispatch)`、`完成耗时(T_done)`、`验收耗时(T_verify)`、`误投递率(Misroute%)`。
  - 参考：`OpenHands` / `SWE-agent`（任务生命周期可观测）。
  - 验收：每周可导出趋势，能定位瓶颈在“派单/执行/验收”哪一段。

### W1 单 Agent 快速闭环（你的高频主流程）
- [x] 一键“Quick Task”派单流
  - 内容：从当前 pane 直接发起任务，自动带入 `profile/target/alias`，减少表单输入。
  - 参考：`Aider`（终端内最短操作路径）。
  - 验收：从选中 pane 到任务创建 <= 2 次点击。
- [x] 完成证据契约（Definition of Done）
  - 内容：`done` 必须包含至少 1 条结构化证据（测试结果/命令回执/输出片段）。
  - 参考：`SWE-agent`（Issue->Fix->Evidence）。
  - 验收：无证据不能标记 `done`，可追溯证据来源与时间戳。
- [x] `done -> verified` 双阶段状态
  - 内容：增加人工/Reviewer 验收态，避免 agent 自报完成即结单。
  - 参考：`OpenHands`（任务执行与人工确认分离）。
  - 验收：关键任务需经过 `verified` 才能归档。

### W2 多 Agent 协作闭环（中复杂任务）
- [x] 标准三角色编排模板：`planner -> executor -> reviewer`
  - 内容：任务可拆子任务并绑定不同 pane，最后自动汇总。
  - 参考：`AutoGen`（多 agent 编排）。
  - 验收：可看到子任务依赖关系与聚合结果。
- [x] 交接包（handoff packet）标准化
  - 内容：交接必须包含上下文、约束、验收标准、回滚提示。
  - 参考：`OpenHands` / `SWE-agent`（完整任务上下文传递）。
  - 验收：跨 pane 切换时无需重新解释需求。

### W3 移动端弱网/应急流（你“手机控制”场景的关键）
- [x] WebSocket 双向终端通道
  - 内容：输入回传 + 输出流式 + 心跳 + 断线恢复（SSE 作为兼容 fallback）。
  - 参考：`ttyd` / `wetty`。
  - 验收：弱网下输出连续性显著优于轮询，重连后可续看。
- [x] 会话接管与只读分享
  - 内容：临时分享链接（只读/可控）用于排障或协作。
  - 参考：`tmate`。
  - 验收：支持过期时间、撤销、操作审计。

### W4 安全与治理流（避免“方便但危险”）
- [x] 危险命令安全闸门
  - 内容：`allow/confirm/deny` 策略与命令风险分级。
  - 参考：`open-interpreter`。
  - 验收：高风险命令必须确认，且审计可追溯。
- [x] RBAC 权限边界
  - 内容：`admin/operator/viewer` 权限分离（目标管理、派单、状态修改、审核）。
  - 参考：`OpenHands`（Cloud RBAC 思路）。
  - 验收：越权请求被拒绝并记录。
- [x] 凭据 Vault 化
  - 内容：将密码从明文 JSON 迁移到系统 keychain/外部 secret provider。
  - 参考：`XPipe`。
  - 验收：备份文件中无可直接利用明文凭据。

### W5 规模化与工程化流（团队/多主机阶段）
- [x] 连接中心 + 批量操作
  - 内容：分组筛选、批量健康检查、批量模板下发。
  - 参考：`XPipe` connection hub。
  - 验收：目标数 > 50 时仍可快速定位与操作。
- [x] 任务/命令统一事件流与回放
  - 内容：派单、状态变化、命令、证据统一时间线。
  - 参考：`AutoGen` 事件驱动。
  - 验收：任一任务可完整回放“谁在何时做了什么”。
- [x] CI 规则检查（workflow quality gates）
  - 内容：自动校验鉴权、错误码、日志脱敏、证据字段完整性。
  - 参考：`Continue`（source-controlled checks）。
  - 验收：违反规则的 PR 自动阻断。
- [x] 可选：工作区模板化
  - 内容：将 target 从“SSH 主机”升级为“可复用工作区模板”。
  - 参考：`Coder`。
  - 验收：新任务可在一致环境快速拉起，减少环境漂移。

## 工作流里程碑（建议）
- [x] MW1（2 周）：完成 W0 + W1，先把“单 agent 快速闭环”做到极致。
- [x] MW2（2-4 周）：完成 W3 + W4，保证移动端可靠与安全可控。
- [x] MW3（4 周+）：完成 W2 + W5，支持团队化和多 agent 协作。

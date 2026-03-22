# Frontend references for ClawDone

更新时间：2026-03-21

目标：找适合 `ClawDone / PocketClaw` 这类“手机端控制远端 tmux / Codex worker”的高星 GitHub 前端参考，不只是好看，还要能直接借鉴到：

- 移动端聊天体验
- 多会话 / 多 worker 视图
- 状态盘 / 交付页 / TODO 管理
- 认证与设置分屏
- 可持续演进，而不是一次性 demo UI


---

## 结论先说

如果要把现在的前端做漂亮、同时保持开发成本可控，我更推荐：

### 推荐组合 A：最适合我们

- 聊天区交互：借鉴 `open-webui/open-webui`
- 聊天布局细节：借鉴 `mckaywrigley/chatbot-ui`
- 基础组件系统：用 `shadcn-ui/ui`
- 状态盘 / 卡片 / 数据概览：借鉴 `tabler/tabler`
- 表单与设置、后台资源页：参考 `marmelab/react-admin`

这套组合的好处是：

- `Open WebUI` 负责“AI 产品感”
- `Chatbot UI` 负责“对话细节和多模型聊天体验”
- `shadcn/ui` 负责“现代组件质感”
- `Tabler` 负责“状态盘、卡片、后台信息密度”
- `react-admin` 负责“设置、资源管理、CRUD 组织方式”

换句话说，不建议照抄单个项目，而是按页面职责拆着借鉴。

---

## 1) Open WebUI

- GitHub: https://github.com/open-webui/open-webui
- Stars: 约 `123k`
- 技术方向：Svelte + Python，全套 AI 产品 UI
- 适配度：`非常高`

### 适合借鉴什么

- 整体 AI 产品气质
- 移动端友好的聊天布局
- 对话页的层次感、留白、卡片密度
- 语音、多模型、工具调用、侧边能力入口的组织方式
- PWA / mobile-first 思路

### 为什么适合我们

我们的核心不是“传统后台”，而是“远程 AI / worker 控制台”。`Open WebUI` 本质上就是目前最成熟的一类 AI 产品前端范式，尤其适合：

- 对话页作为主入口
- 工具、模型、会话管理并存
- 手机端依然能操作

### 不适合直接照搬的部分

- 它是完整 AI 平台，功能太多
- 信息架构比我们更重
- 如果直接抄，会把我们的“tmux / worker”特色冲淡

### 在我们项目里怎么用

- 对话页视觉气质：直接参考
- 会话列表、顶部工具区、消息气泡：重点参考
- 将“tmux window = 会话”、“pane = worker”映射进去

---

## 2) Chatbot UI

- GitHub: https://github.com/mckaywrigley/chatbot-ui
- Stars: 约 `33.1k`
- 技术方向：Next.js / React，ChatGPT 风格聊天产品
- 适配度：`很高`

### 适合借鉴什么

- 聊天气泡、输入区、消息节奏
- 历史会话列表
- 移动端输入栏和操作按钮布局
- 多模型聊天产品的交互细节

### 为什么适合我们

如果你想让 `ClawDone` 的“对话页”更像微信 / ChatGPT / 自媒体助手，而不是工程后台，`Chatbot UI` 是非常直接的参考。

### 在我们项目里怎么用

- 把“worker chip / worker tab”融合进聊天头部
- 让消息区更像真实 IM，而不是日志窗口
- 保留底部固定输入栏 + 语音按钮 + 发送按钮

### 风险

- 它偏“单聊天产品”，状态盘和交付页参考价值不如 `Tabler`

---

## 3) shadcn/ui

- GitHub: https://github.com/shadcn-ui/ui
- Stars: 约 `104k`
- 技术方向：React + Tailwind 的组件分发体系
- 适配度：`非常高`

### 适合借鉴什么

- 基础视觉体系
- Button / Card / Sheet / Tabs / Dialog / Select / Drawer / Command / Badge
- 现代 SaaS 质感
- 统一组件语言

### 为什么适合我们

我们现在前端最大问题之一不是“没有页面”，而是：

- 组件不统一
- 层级不统一
- 表单、卡片、列表、聊天区像拼出来的

`shadcn/ui` 很适合拿来做下一版的设计底座。

### 在我们项目里怎么用

建议把后续页面抽象成：

- `ConversationList`
- `WorkerChip`
- `StatusCard`
- `TodoBoard`
- `DeliverySummary`
- `SettingsForm`

全部按 shadcn 的组件语言重做。

---

## 4) Tabler

- GitHub: https://github.com/tabler/tabler
- Stars: 约 `40.9k`
- 技术方向：Dashboard UI Kit
- 适配度：`高`

### 适合借鉴什么

- 状态盘
- 数据概览卡片
- 系统监控页
- 交付页 / 审计页 / overview 页
- 图标和后台布局密度

### 为什么适合我们

`ClawDone` 不只是聊天，还需要：

- 目标在线状态
- tmux session / pane 统计
- todo 数量
- audit / delivery / health 信息

这些内容更像“控制台”而不是“聊天产品”，这时候 `Tabler` 比纯聊天项目更合适。

### 在我们项目里怎么用

- `状态盘` 页直接参考 Tabler 卡片布局
- `交付` 页参考 Tabler 的 summary + details 结构
- 全局图标建议直接改用 `tabler-icons`

---

## 5) React Admin

- GitHub: https://github.com/marmelab/react-admin
- Stars: 约 `26.6k`
- 技术方向：React 后台框架
- 适配度：`中高`

### 适合借鉴什么

- 认证与设置页结构
- CRUD 资源页组织方式
- 表单、列表、筛选器的关系
- 后台管理信息架构

### 为什么适合我们

`认证设置`、`target profile`、`session share`、`todo templates` 这些东西，本质上都属于“后台资源管理”。

聊天产品参考项目在这里通常不够强，而 `react-admin` 的信息架构更成熟。

### 在我们项目里怎么用

- 认证设置页布局
- Profile / Target / Share / Template 的资源组织方式
- 列表 + 编辑 + 表单的后台结构

### 不建议直接照搬的部分

- Material Design 的观感偏“后台管理系统”，不够像现代 AI 产品
- 更适合作为结构参考，不适合作为最终视觉风格

---

## 6) Headless UI

- GitHub: https://github.com/tailwindlabs/headlessui
- Stars: 约 `28.3k`
- 技术方向：无样式但可访问的 UI primitives
- 适配度：`中高`

### 适合借鉴什么

- Tabs / Listbox / Dialog / Menu / Combobox 等交互原语
- 可访问性和键盘操作
- 移动端 drawer / popover 类交互

### 为什么适合我们

如果下一版你准备从“内嵌字符串 HTML”迁到 React / Vue / Svelte，这个库很适合作为交互底层，不会把视觉强绑定死。

---

## 不建议作为主参考的项目

### vue-element-admin

- GitHub: https://github.com/PanJiaChen/vue-element-admin
- 历史地位很高，但视觉年代感较强
- 更像传统企业后台，不像现代 AI / mobile-first 产品
- 可以参考信息架构，不建议作为视觉主方向

---

## 对我们最有价值的页面映射

### 1. 状态盘

优先参考：

- `tabler/tabler`
- `react-admin`

我们可以借鉴：

- 统计卡片
- 在线状态
- 目标列表
- 审计与交付概览

### 2. 认证设置

优先参考：

- `react-admin`
- `shadcn-ui/ui`

我们可以借鉴：

- 分组表单
- 资源页组织
- 安全设置和 token 管理

### 3. 对话

优先参考：

- `open-webui/open-webui`
- `mckaywrigley/chatbot-ui`

我们可以借鉴：

- 微信 / ChatGPT 风格消息区
- 会话列表
- 底部输入栏
- 手机端操作按钮

### 4. TODO

优先参考：

- `react-admin`
- `tabler/tabler`

我们可以借鉴：

- 任务状态列表
- 标签、优先级、时间线
- 证据与备注的 inspector 视图

### 5. 交付

优先参考：

- `tabler/tabler`
- `open-webui/open-webui`

我们可以借鉴：

- Summary + evidence + timeline + pane snapshot 的组合页

---

## 最推荐的重做路线

### 路线 1：最低风险

保留 Python 服务端，只重做前端 HTML/CSS/JS，视觉上参考：

- `Open WebUI` 的聊天页
- `Tabler` 的状态盘

优点：

- 改动最小
- 后端接口不用大改

缺点：

- 内嵌 HTML 继续变大
- 组件化能力有限

### 路线 2：最推荐

把前端独立成 React / Next.js 小前端，技术底座参考：

- `shadcn-ui/ui`
- `headlessui`
- `tabler-icons`

页面设计参考：

- `Open WebUI`
- `Chatbot UI`
- `Tabler`

优点：

- 后面更好迭代
- 更容易把聊天、状态盘、TODO、交付做漂亮
- 组件和状态管理会清晰很多

缺点：

- 首次迁移成本更高

---

## 我给你的实际建议

如果你要我继续做，我建议下一步直接定成：

- 视觉风格：`Open WebUI + Chatbot UI`
- 组件体系：`shadcn/ui`
- 状态盘与交付：`Tabler`
- 表单 / 资源页结构：`react-admin`

也就是：

- 聊天页像 AI 产品
- 状态页像控制台
- 设置页像现代后台
- TODO/交付页像任务运营面板

这比只抄一个项目会更适合我们这个产品。

---

## Sources

- Open WebUI: https://github.com/open-webui/open-webui
- Chatbot UI: https://github.com/mckaywrigley/chatbot-ui
- shadcn/ui: https://github.com/shadcn-ui/ui
- Tabler: https://github.com/tabler/tabler
- React Admin: https://github.com/marmelab/react-admin
- Headless UI: https://github.com/tailwindlabs/headlessui
- vue-element-admin: https://github.com/PanJiaChen/vue-element-admin

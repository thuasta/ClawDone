# AGENTSMEMORY

## 2026-03-24 Code Simplification Notes

### Scope
- Simplified repeated Todo action logic in `clawdone/html.py` without changing API contracts.

### What Was Simplified
- Added `requireSelectedTodo(action)`:
  - Centralized “must select a todo first” validation and status message.
- Added `runTodoAction(action, options)`:
  - Centralized try/catch flow, missing-todo recovery, and optional post-action refresh (`loadTodos` + `loadDashboard`).
- Refactored these functions to use shared helpers:
  - `updateTodoStatus`
  - `addTodoEvidence`
  - `reportTodo`
  - `supervisorDispatchTodo`
  - `supervisorReviewTodo`
  - `supervisorAcceptTodo`
  - `applyTodoToCommand`

### Result
- Removed duplicated error handling/refresh boilerplate across multiple functions.
- Kept behavior consistent while making the code easier to read and maintain.

### Verification
- Ran:
  - `PYTHONPATH=. pytest -q tests/test_app.py::HtmlTests tests/test_app.py::RenderIndexHtmlTests::test_render_index_html_marks_requested_view_on_buttons`
- Result: `9 passed`.

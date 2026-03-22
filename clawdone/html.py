"""Embedded mobile web UI."""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>ClawDone</title>
  <style>
    :root {
      color-scheme: dark;
      --background: #020817;
      --foreground: #e2e8f0;
      --card: #0f172a;
      --card-foreground: #e2e8f0;
      --muted: #94a3b8;
      --muted-foreground: #94a3b8;
      --popover: #0b1222;
      --border: #1e293b;
      --input: #0b1222;
      --ring: #3b82f6;
      --primary: #e2e8f0;
      --primary-foreground: #020617;
      --secondary: #1e293b;
      --secondary-foreground: #f8fafc;
      --destructive: #ef4444;
      --destructive-foreground: #fef2f2;
      --success: #22c55e;
      --warning: #f59e0b;
      --radius: 0.75rem;
      --shadow: 0 1px 3px rgba(15, 23, 42, 0.5), 0 12px 28px rgba(2, 6, 23, 0.35);
    }
    * { box-sizing: border-box; }
    html, body { min-height: 100%; }
    body {
      margin: 0;
      font-family: "Inter", "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(1100px 320px at 50% -140px, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0) 62%),
        linear-gradient(180deg, #020617 0%, #020817 100%);
      color: var(--foreground);
      line-height: 1.45;
    }
    .wrap {
      width: min(1160px, 100%);
      margin: 0 auto;
      padding: 24px 16px 68px;
    }
    h1, h2, h3, p { margin: 0; }
    .hero {
      margin-bottom: 16px;
      display: grid;
      gap: 10px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .brand-logo {
      width: 56px;
      height: 56px;
      object-fit: contain;
      border-radius: 16px;
      border: 1px solid rgba(59, 130, 246, 0.28);
      background: rgba(15, 23, 42, 0.92);
      box-shadow: var(--shadow);
      padding: 6px;
      flex: 0 0 auto;
    }
    .brand-copy {
      display: grid;
      gap: 6px;
    }
    .hero h1 {
      font-size: clamp(1.45rem, 2.1vw, 1.95rem);
      line-height: 1.2;
      letter-spacing: -0.02em;
    }
    .sub {
      color: var(--muted-foreground);
      max-width: 90ch;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      padding: 6px 12px;
      border-radius: 999px;
      border: 1px solid rgba(59, 130, 246, 0.38);
      background: rgba(30, 58, 138, 0.2);
      color: #bfdbfe;
      font-size: 0.82rem;
      font-weight: 500;
    }
    .card {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border);
      border-radius: calc(var(--radius) + 3px);
      box-shadow: var(--shadow);
      padding: 16px;
      margin-bottom: 14px;
    }
    .grid { display: grid; gap: 12px; }
    .grid-2 { display: grid; gap: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .grid-3 { display: grid; gap: 10px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .grid-4 { display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .main-grid { display: grid; gap: 14px; grid-template-columns: 1.15fr 1fr; }
    label {
      display: block;
      margin-bottom: 7px;
      color: var(--muted-foreground);
      font-size: 0.85rem;
      font-weight: 500;
    }
    input, select, textarea {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 9px 12px;
      background: var(--input);
      color: var(--foreground);
      font: inherit;
      transition: border-color 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
    }
    input::placeholder, textarea::placeholder {
      color: #64748b;
    }
    input:focus, select:focus, textarea:focus, button:focus-visible {
      outline: none;
      border-color: var(--ring);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.22);
    }
    textarea {
      min-height: 124px;
      resize: vertical;
      padding: 11px 12px;
    }
    button {
      width: 100%;
      min-height: 40px;
      border: 1px solid transparent;
      border-radius: var(--radius);
      padding: 9px 12px;
      background: var(--secondary);
      color: var(--secondary-foreground);
      font: inherit;
      font-weight: 600;
      cursor: pointer;
      transition: transform 120ms ease, background-color 120ms ease, border-color 120ms ease, opacity 120ms ease;
    }
    button:hover { transform: translateY(-1px); }
    button:active { transform: translateY(0); }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
    .primary {
      background: var(--primary);
      color: var(--primary-foreground);
    }
    .secondary {
      background: var(--secondary);
      border-color: var(--border);
      color: var(--secondary-foreground);
    }
    .danger {
      background: var(--destructive);
      color: var(--destructive-foreground);
    }
    .ghost {
      background: transparent;
      border-color: var(--border);
      color: var(--foreground);
    }
    .muted { color: var(--muted-foreground); }
    .status {
      min-height: 38px;
      border-radius: var(--radius);
      border: 1px dashed var(--border);
      background: rgba(15, 23, 42, 0.45);
      color: #86efac;
      font-size: 0.95rem;
      padding: 8px 10px;
      margin-top: 2px;
    }
    .status.error {
      color: #fecaca;
      border-color: rgba(239, 68, 68, 0.5);
      background: rgba(127, 29, 29, 0.34);
    }
    .status.warn {
      color: #fde68a;
      border-color: rgba(245, 158, 11, 0.45);
      background: rgba(120, 53, 15, 0.26);
    }
    .hint {
      color: var(--muted-foreground);
      font-size: 0.82rem;
      line-height: 1.45;
    }
    .kpi {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: rgba(15, 23, 42, 0.65);
    }
    .kpi strong {
      display: block;
      font-size: 1.18rem;
      margin-bottom: 4px;
      letter-spacing: -0.01em;
    }
    .list {
      display: grid;
      gap: 8px;
      max-height: 320px;
      overflow: auto;
      padding-right: 2px;
    }
    .target-card {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px 13px;
      background: rgba(15, 23, 42, 0.62);
      color: var(--foreground);
      text-align: left;
      transition: border-color 120ms ease, background-color 120ms ease, transform 120ms ease;
    }
    .target-card-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .target-card-name {
      display: grid;
      gap: 4px;
      min-width: 0;
    }
    .target-card-name strong {
      font-size: 0.95rem;
      line-height: 1.2;
    }
    .target-card-host {
      color: var(--muted-foreground);
      font-size: 0.8rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .target-card-foot {
      margin-top: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted-foreground);
      font-size: 0.78rem;
    }
    .target-card:hover {
      border-color: #475569;
      background: rgba(30, 41, 59, 0.64);
      transform: translateY(-1px);
    }
    .target-card.active {
      border-color: var(--ring);
      background: rgba(30, 58, 138, 0.24);
    }
    .badge-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid #334155;
      color: #cbd5e1;
      font-size: 0.78rem;
    }
    .badge.ok {
      color: #bbf7d0;
      border-color: rgba(34, 197, 94, 0.5);
      background: rgba(20, 83, 45, 0.4);
    }
    .badge.bad {
      color: #fecdd3;
      border-color: rgba(239, 68, 68, 0.5);
      background: rgba(127, 29, 29, 0.4);
    }
    .section-title { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .section-title h2 {
      font-size: 1.02rem;
      letter-spacing: -0.01em;
    }
    .row-inline { display: flex; gap: 8px; align-items: center; }
    .row-inline > button { flex: 1; }
    .checkbox {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 12px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--input);
    }
    .checkbox input {
      width: 16px;
      height: 16px;
      margin: 0;
      accent-color: #3b82f6;
    }
    pre {
      margin: 0;
      padding: 12px;
      background: rgba(2, 6, 23, 0.92);
      border-radius: var(--radius);
      border: 1px solid var(--border);
      color: #dbeafe;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 240px;
      font-size: 0.86rem;
      line-height: 1.5;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    details.fold {
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      background: rgba(11, 18, 34, 0.5);
      padding: 10px 12px;
    }
    details.fold.fold-panel {
      border-style: solid;
      background: rgba(9, 14, 27, 0.42);
      padding: 12px 14px;
    }
    details.fold > summary {
      cursor: pointer;
      font-weight: 600;
      color: var(--foreground);
      list-style: none;
      user-select: none;
    }
    details.fold > summary::-webkit-details-marker {
      display: none;
    }
    details.fold > summary::after {
      content: "Show";
      float: right;
      color: var(--muted-foreground);
      font-size: 0.78rem;
      font-weight: 500;
    }
    details.fold[open] > summary::after {
      content: "Hide";
    }
    .fold-body {
      margin-top: 10px;
      display: grid;
      gap: 10px;
    }
    .fold-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-right: 20px;
    }
    .fold-head strong {
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: -0.01em;
    }
    .fold-head span {
      color: var(--muted-foreground);
      font-size: 0.8rem;
    }
    .settings-grid {
      display: grid;
      gap: 12px;
    }
    .settings-card {
      display: grid;
      gap: 10px;
      padding: 4px 0;
    }
    .pagination {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-wrap: wrap;
      gap: 6px;
    }
    .pagination button {
      width: auto;
      min-width: 36px;
      min-height: 34px;
      padding: 6px 10px;
      font-size: 0.85rem;
    }
    .pagination .page-current {
      background: rgba(59, 130, 246, 0.22);
      border-color: var(--ring);
      color: #dbeafe;
    }
    .pagination .page-ellipsis {
      color: var(--muted-foreground);
      padding: 0 2px;
      font-size: 0.85rem;
    }
    .stack-list {
      display: grid;
      gap: 8px;
    }
    .list-item {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 12px;
      background: rgba(11, 18, 34, 0.72);
      color: var(--foreground);
      text-align: left;
    }
    .list-item.active {
      border-color: var(--ring);
      background: rgba(30, 58, 138, 0.22);
    }
    .list-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 0.92rem;
    }
    .list-item .hint {
      display: block;
      margin-top: 4px;
    }
    .todo-board {
      display: grid;
      gap: 12px;
    }
    .todo-lane {
      display: grid;
      gap: 10px;
      border: 1px solid rgba(51, 65, 85, 0.65);
      border-radius: 16px;
      padding: 12px;
      background: rgba(11, 18, 34, 0.34);
    }
    .todo-lane-head {
      display: grid;
      grid-template-columns: 40px minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
    }
    .todo-lane-copy {
      min-width: 0;
      display: grid;
      gap: 2px;
    }
    .todo-lane-title {
      font-weight: 700;
      font-size: 0.94rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .todo-lane-meta {
      color: var(--muted-foreground);
      font-size: 0.78rem;
    }
    .todo-count {
      font-size: 0.78rem;
      color: var(--muted-foreground);
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid rgba(51, 65, 85, 0.7);
      background: rgba(15, 23, 42, 0.55);
    }
    .todo-lane-body {
      display: grid;
      gap: 8px;
    }
    .todo-bar {
      display: grid;
      gap: 8px;
      border: 1px solid rgba(51, 65, 85, 0.7);
      border-radius: 14px;
      padding: 10px;
      background: rgba(15, 23, 42, 0.55);
      transition: border-color 120ms ease, background-color 120ms ease;
    }
    .todo-bar.active {
      border-color: rgba(96, 165, 250, 0.7);
      background: rgba(30, 64, 175, 0.18);
    }
    .todo-bar-head {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 10px;
      align-items: start;
    }
    .todo-check {
      width: 28px;
      min-height: 28px;
      height: 28px;
      padding: 0;
      border-radius: 999px;
      border: 1px solid rgba(96, 165, 250, 0.52);
      background: rgba(30, 41, 59, 0.62);
      color: #dbeafe;
      font-size: 0.82rem;
      font-weight: 700;
    }
    .todo-check.status-in_progress {
      background: rgba(59, 130, 246, 0.18);
    }
    .todo-check.status-done,
    .todo-check.status-verified {
      background: rgba(34, 197, 94, 0.2);
      border-color: rgba(34, 197, 94, 0.55);
    }
    .todo-check.status-blocked {
      background: rgba(239, 68, 68, 0.18);
      border-color: rgba(239, 68, 68, 0.45);
    }
    .todo-bar-copy {
      min-width: 0;
      display: grid;
      gap: 4px;
      cursor: pointer;
    }
    .todo-bar-title {
      font-weight: 650;
      line-height: 1.35;
    }
    .todo-bar-detail {
      color: var(--muted-foreground);
      font-size: 0.82rem;
      line-height: 1.45;
    }
    .todo-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      justify-content: flex-end;
    }
    .todo-badge {
      font-size: 0.73rem;
      line-height: 1;
      padding: 5px 7px;
      border-radius: 999px;
      border: 1px solid rgba(51, 65, 85, 0.75);
      color: var(--muted-foreground);
      background: rgba(15, 23, 42, 0.6);
      text-transform: lowercase;
    }
    .todo-badge.status-in_progress { color: #93c5fd; }
    .todo-badge.status-done { color: #86efac; }
    .todo-badge.status-verified { color: #bbf7d0; }
    .todo-badge.status-blocked { color: #fca5a5; }
    .todo-bar-progress {
      height: 5px;
      width: 100%;
      border-radius: 999px;
      background: rgba(30, 41, 59, 0.9);
      overflow: hidden;
    }
    .todo-bar-progress > span {
      display: block;
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(59, 130, 246, 0.9) 0%, rgba(34, 197, 94, 0.92) 100%);
    }
    .todo-bar-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .todo-mini {
      width: auto;
      min-height: 30px;
      padding: 5px 10px;
      font-size: 0.78rem;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.56);
      border: 1px solid rgba(51, 65, 85, 0.65);
      color: var(--muted-foreground);
    }
    .empty-state {
      padding: 14px;
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      color: var(--muted-foreground);
      text-align: center;
      background: rgba(11, 18, 34, 0.36);
    }
    .hidden-select {
      position: absolute;
      opacity: 0;
      pointer-events: none;
      width: 1px;
      height: 1px;
      overflow: hidden;
    }
    .chatbot-layout {
      display: grid;
      grid-template-columns: minmax(280px, 320px) minmax(0, 1fr);
      gap: 14px;
      align-items: start;
    }
    .chat-sidebar,
    .chat-main {
      border: 1px solid var(--border);
      border-radius: 20px;
      background: rgba(15, 23, 42, 0.9);
      box-shadow: 0 10px 24px rgba(2, 6, 23, 0.22);
    }
    .chat-sidebar {
      display: grid;
      gap: 4px;
      padding: 14px 14px 10px;
      position: sticky;
      top: 12px;
    }
    .chatbot-sidebar-header {
      display: grid;
      gap: 4px;
    }
    .chatbot-sidebar-header h2,
    .chat-main-header h2 {
      font-size: 1.08rem;
      letter-spacing: -0.02em;
    }
    .chatbot-overline {
      display: none;
    }
    .chatbot-agent-card,
    .chatbot-sidebar-panel {
      display: grid;
      gap: 8px;
      padding: 10px 2px 12px;
      border: 0;
      border-bottom: 1px solid rgba(51, 65, 85, 0.55);
      border-radius: 0;
      background: transparent;
    }
    .chatbot-agent-card strong {
      font-size: 0.98rem;
      font-weight: 650;
    }
    .chatbot-agent-card span,
    .chatbot-sidebar-panel .hint {
      color: var(--muted-foreground);
      font-size: 0.84rem;
      line-height: 1.5;
    }
    .chatbot-sidebar-title {
      font-size: 0.75rem;
      color: var(--muted-foreground);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }
    .chat-main {
      display: grid;
      grid-template-rows: auto minmax(420px, 1fr) auto;
      min-height: 760px;
      overflow: hidden;
    }
    .chat-main-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      padding: 16px 18px 14px;
      border-bottom: 1px solid rgba(51, 65, 85, 0.65);
      background: rgba(15, 23, 42, 0.96);
    }
    .chat-main-header .hint {
      margin-top: 6px;
      display: block;
    }
    .chat-main-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }
    .chat-main-actions button {
      width: auto;
      min-width: 112px;
    }
    .chat-feed {
      display: grid;
      align-content: start;
      gap: 14px;
      overflow: auto;
      padding: 18px 18px 20px;
      background:
        radial-gradient(620px 240px at 50% 0, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0) 70%),
        linear-gradient(180deg, rgba(2, 6, 23, 0.12) 0%, rgba(2, 6, 23, 0.28) 100%);
    }
    .message {
      display: grid;
      gap: 8px;
      width: 100%;
    }
    .message.user {
      justify-items: end;
    }
    .message.agent {
      justify-items: start;
    }
    .message-meta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted-foreground);
      font-size: 0.76rem;
      padding: 0 6px;
      letter-spacing: 0.01em;
    }
    .message-body {
      max-width: min(100%, 760px);
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid rgba(51, 65, 85, 0.8);
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.58;
      box-shadow: 0 10px 24px rgba(2, 6, 23, 0.12);
    }
    .message.user .message-body {
      background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%);
      border-color: rgba(96, 165, 250, 0.62);
      color: #eff6ff;
      border-bottom-right-radius: 8px;
      max-width: min(88%, 640px);
    }
    .message.agent .message-body {
      background: rgba(17, 24, 39, 0.95);
      color: #dbeafe;
      border-bottom-left-radius: 8px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      font-size: 0.84rem;
      max-width: min(92%, 760px);
    }
    .composer {
      display: grid;
      gap: 12px;
      padding: 16px 18px 18px;
      border-top: 1px solid rgba(51, 65, 85, 0.65);
      background: rgba(15, 23, 42, 0.98);
    }
    .composer-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .composer-head label {
      margin: 0;
      color: var(--foreground);
      font-size: 0.92rem;
    }
    .chat-input {
      min-height: 116px;
      border-radius: 18px;
      border-color: rgba(51, 65, 85, 0.95);
      background: rgba(2, 6, 23, 0.85);
      padding: 14px 16px;
      line-height: 1.6;
    }
    .composer-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: space-between;
    }
    .composer-actions .row-inline {
      flex-wrap: wrap;
      width: 100%;
      justify-content: space-between;
    }
    .composer-actions button {
      flex: 1 1 140px;
    }
    .thread-list {
      display: grid;
      gap: 4px;
      max-height: 360px;
      overflow: auto;
    }
    .thread-card {
      width: 100%;
      border: 1px solid transparent;
      border-radius: 14px;
      padding: 11px 12px;
      background: rgba(11, 18, 34, 0.24);
      color: var(--foreground);
      text-align: left;
      transition: background-color 120ms ease, color 120ms ease, border-color 120ms ease;
      box-shadow: none;
    }
    .thread-card:hover {
      background: rgba(30, 41, 59, 0.42);
      border-color: rgba(71, 85, 105, 0.7);
    }
    .thread-card.active {
      background: rgba(37, 99, 235, 0.16);
      border-color: rgba(96, 165, 250, 0.5);
      color: #e5eefc;
    }
    .thread-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
      font-weight: 700;
    }
    .worker-strip {
      display: grid;
      gap: 6px;
    }
    .worker-chip {
      width: 100%;
      display: grid;
      grid-template-columns: 40px minmax(0, 1fr);
      align-items: center;
      gap: 10px;
      min-height: 58px;
      padding: 9px 10px;
      border: 1px solid transparent;
      border-radius: 14px;
      background: rgba(11, 18, 34, 0.2);
      color: var(--foreground);
      text-align: left;
      box-shadow: none;
    }
    .worker-chip:hover {
      background: rgba(30, 41, 59, 0.42);
      border-color: rgba(71, 85, 105, 0.65);
    }
    .worker-chip.active {
      background: rgba(37, 99, 235, 0.16);
      border-color: rgba(96, 165, 250, 0.5);
      color: #e5eefc;
    }
    .worker-avatar {
      position: relative;
      width: 40px;
      height: 40px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      background: linear-gradient(180deg, rgba(59, 130, 246, 0.9) 0%, rgba(29, 78, 216, 0.92) 100%);
      color: #eff6ff;
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .worker-chip.active .worker-avatar {
      box-shadow: 0 0 0 2px rgba(147, 197, 253, 0.45);
    }
    .worker-dot {
      position: absolute;
      right: 1px;
      bottom: 1px;
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: #475569;
      border: 2px solid rgba(15, 23, 42, 0.9);
    }
    .worker-dot.live {
      background: #22c55e;
    }
    .worker-copy {
      min-width: 0;
      display: grid;
      gap: 3px;
    }
    .worker-name {
      font-size: 0.9rem;
      font-weight: 650;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .worker-meta {
      color: var(--muted-foreground);
      font-size: 0.76rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .page-view {
      display: none;
      gap: 14px;
    }
    .page-view.active {
      display: grid;
    }
    .tabbar {
      position: fixed;
      left: 50%;
      bottom: max(12px, env(safe-area-inset-bottom));
      transform: translateX(-50%);
      width: min(760px, calc(100% - 24px));
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
      padding: 8px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(2, 6, 23, 0.92);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      z-index: 20;
    }
    .tab-button {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      border-radius: 14px;
      background: transparent;
      border-color: transparent;
      color: var(--muted-foreground);
      font-weight: 700;
      text-decoration: none;
    }
    .tab-button.active {
      background: rgba(59, 130, 246, 0.18);
      border-color: rgba(59, 130, 246, 0.38);
      color: #dbeafe;
    }
    body {
      background:
        radial-gradient(900px 280px at 50% -180px, rgba(59, 130, 246, 0.14), rgba(59, 130, 246, 0) 62%),
        linear-gradient(180deg, #030712 0%, #0a1120 100%);
    }
    .wrap {
      width: min(1080px, 100%);
      padding: 20px 16px 72px;
    }
    .hero {
      margin-bottom: 10px;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: start;
    }
    .hero-meta {
      display: grid;
      gap: 8px;
      align-content: start;
      min-width: min(260px, 100%);
    }
    .hero-note {
      padding: 10px 12px;
      border: 1px solid rgba(51, 65, 85, 0.7);
      border-radius: 14px;
      background: rgba(11, 18, 34, 0.5);
      color: var(--muted-foreground);
      font-size: 0.82rem;
      line-height: 1.5;
    }
    .action-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .action-strip > button {
      width: auto;
      flex: 1 1 160px;
    }
    .stats-grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .stats-grid.compact .kpi {
      background: rgba(11, 18, 34, 0.48);
    }
    .workspace-grid {
      display: grid;
      gap: 14px;
      grid-template-columns: minmax(0, 1.05fr) minmax(300px, 0.95fr);
      align-items: start;
    }
    .panel-stack,
    .settings-shell,
    .todo-shell,
    .delivery-shell,
    .inspector-stack,
    .support-list {
      display: grid;
      gap: 14px;
    }
    .settings-shell {
      grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
      align-items: start;
    }
    .todo-shell,
    .delivery-shell {
      grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
      align-items: start;
    }
    .support-card {
      gap: 10px;
    }
    .support-item {
      padding: 12px 14px;
      border: 1px solid rgba(51, 65, 85, 0.65);
      border-radius: 14px;
      background: rgba(11, 18, 34, 0.4);
    }
    .support-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 0.9rem;
    }
    .card,
    .chat-sidebar,
    .chat-main {
      background: rgba(9, 14, 27, 0.82);
      border-color: rgba(51, 65, 85, 0.7);
      border-radius: 18px;
      box-shadow: 0 8px 22px rgba(2, 6, 23, 0.2);
    }
    .kpi {
      background: rgba(11, 18, 34, 0.54);
      padding: 14px;
    }
    .target-card,
    .list-item,
    .todo-lane,
    .todo-bar {
      background: rgba(11, 18, 34, 0.52);
      box-shadow: none;
    }
    details.fold {
      background: rgba(11, 18, 34, 0.42);
      border-color: rgba(51, 65, 85, 0.7);
    }
    details.fold.fold-panel {
      background: rgba(9, 14, 27, 0.36);
    }
    .chatbot-layout {
      grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
      gap: 12px;
    }
    .chat-sidebar {
      gap: 8px;
      padding: 14px 14px 12px;
    }
    .chat-main {
      min-height: 680px;
    }
    .chat-main-header,
    .composer {
      padding-left: 16px;
      padding-right: 16px;
    }
    .chat-feed {
      padding: 16px;
    }
    .tabbar {
      width: min(680px, calc(100% - 24px));
      background: rgba(6, 11, 23, 0.92);
      box-shadow: 0 10px 24px rgba(2, 6, 23, 0.26);
    }
    @media (max-width: 900px) {
      .main-grid, .grid-2, .grid-3, .grid-4, .chatbot-layout, .workspace-grid, .settings-shell, .todo-shell, .delivery-shell, .stats-grid, .hero { grid-template-columns: 1fr; }
      .row-inline {
        flex-direction: column;
        align-items: stretch;
      }
      .chat-sidebar {
        position: static;
      }
      .chat-main {
        min-height: 680px;
      }
      .chat-main-header,
      .composer-actions .row-inline {
        flex-direction: column;
        align-items: stretch;
      }
      .chat-main-actions {
        width: 100%;
        justify-content: stretch;
      }
      .chat-main-actions button {
        width: 100%;
      }
      .wrap { padding-bottom: 110px; }
    }
    @media (max-width: 520px) {
      .wrap { padding: 18px 12px 100px; }
      .card { padding: 13px; }
      button, input, select, textarea { font-size: 16px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="page-view active" id="view-dashboard">
    <section class="hero">
      <div class="brand">
        <img class="brand-logo" src="/assets/logo.png" alt="ClawDone logo">
        <div class="brand-copy">
          <h1>ClawDone</h1>
          <p class="sub">A mobile control surface for remote tmux panes, coding agents, lightweight task routing, and delivery review.</p>
        </div>
      </div>
      <div class="hero-meta">
        <div class="pill">Remote agent console</div>
        <div class="hero-note">Start with a target, bind to a pane, then move into work, tasks, or delivery without leaving your phone.</div>
      </div>
    </section>

    <section class="card grid">
      <div class="section-title"><h2>Overview</h2><span class="hint">Current fleet status and routing metrics</span></div>
      <div class="action-strip">
        <button class="secondary" id="refreshDashboard">Refresh dashboard</button>
        <button class="ghost" id="refreshState">Refresh selected target</button>
      </div>
      <div class="stats-grid">
        <div class="kpi"><strong id="profileCount">0</strong><span>Targets</span></div>
        <div class="kpi"><strong id="onlineCount">0</strong><span>Online</span></div>
        <div class="kpi"><strong id="sessionCount">0</strong><span>Sessions</span></div>
        <div class="kpi"><strong id="paneCount">0</strong><span>Agent panes</span></div>
      </div>
      <div class="stats-grid compact">
        <div class="kpi"><strong id="dispatchMetric">-</strong><span>T_dispatch (sec)</span></div>
        <div class="kpi"><strong id="doneMetric">-</strong><span>T_done (sec)</span></div>
        <div class="kpi"><strong id="verifyMetric">-</strong><span>T_verify (sec)</span></div>
        <div class="kpi"><strong id="misrouteMetric">0%</strong><span>Misroute</span></div>
      </div>
      <div id="status" class="status"></div>
    </section>

    <section class="workspace-grid">
      <details class="card grid fold fold-panel" data-fold-key="dashboard-targets" open>
        <summary><div class="fold-head"><strong>Targets</strong><span>Choose a machine first</span></div></summary>
        <div class="fold-body">
          <div>
            <label for="profileSelect">Saved target</label>
            <select id="profileSelect"></select>
          </div>
          <div id="targetList" class="list"></div>
          <div class="pagination" id="targetPagination"></div>
        </div>
      </details>

      <div class="panel-stack">
        <details class="card grid fold fold-panel" data-fold-key="dashboard-pane" open>
          <summary><div class="fold-head"><strong>Pane</strong><span>Lock onto the agent you want to drive</span></div></summary>
          <div class="fold-body">
            <div class="grid-3">
              <div>
                <label for="session">tmux session</label>
                <select id="session"></select>
              </div>
              <div>
                <label for="window">tmux window</label>
                <select id="window"></select>
              </div>
              <div>
                <label for="pane">Agent pane</label>
                <select id="pane"></select>
              </div>
            </div>
            <div class="grid-2">
              <div>
                <label for="agentAlias">Pane alias</label>
                <input id="agentAlias" placeholder="backend-agent">
              </div>
              <div class="action-strip">
                <button class="secondary" id="saveAlias">Save alias</button>
                <button class="ghost" id="refreshPane">Refresh output</button>
              </div>
            </div>
          </div>
        </details>

        <section class="card support-card">
          <div class="section-title"><h2>Flow</h2><span class="hint">Suggested operating sequence</span></div>
          <div class="support-list">
            <div class="support-item"><strong>1. Select target</strong><span class="hint">Choose the machine that hosts the agent session you need.</span></div>
            <div class="support-item"><strong>2. Select pane</strong><span class="hint">Bind the current session, window, and pane before issuing commands.</span></div>
            <div class="support-item"><strong>3. Switch tabs</strong><span class="hint">Use Work for commands, Tasks for todo tracking, and Delivery for review.</span></div>
          </div>
        </section>
      </div>
    </section>
    </div>

    <div class="page-view" id="view-auth">
    <section class="card grid">
      <div class="section-title"><h2>Settings</h2><span class="hint">Access token, UI preferences, and SSH target settings</span></div>
      <div class="settings-shell">
        <details class="fold fold-panel" data-fold-key="settings-access" open>
          <summary><div class="fold-head"><strong>Access & View</strong><span>Browser-only preferences</span></div></summary>
          <div class="fold-body settings-card">
          <div class="grid-2">
            <div>
              <label for="token">Access token</label>
              <input id="token" type="password" placeholder="Only needed if ClawDone was started with --token">
            </div>
            <div>
              <label for="paneLines">Pane lines per refresh</label>
              <input id="paneLines" type="number" min="40" max="400" value="120">
            </div>
          </div>
          <div class="grid-3">
            <div>
              <label for="targetPageSize">Targets per page</label>
              <input id="targetPageSize" type="number" min="1" max="24" value="6">
            </div>
            <div>
              <label for="historyPageSize">Messages per page</label>
              <input id="historyPageSize" type="number" min="1" max="30" value="8">
            </div>
            <div>
              <label for="todoPageSize">Todos per page</label>
              <input id="todoPageSize" type="number" min="1" max="20" value="6">
            </div>
          </div>
          <div class="grid-2">
            <button class="primary" id="saveUiSettings">Save settings</button>
            <button class="ghost" id="resetUiSettings" type="button">Reset view settings</button>
          </div>
          </div>
        </details>

        <details class="fold fold-panel" data-fold-key="settings-profile" open>
          <summary><div class="fold-head"><strong>Target Profile</strong><span>Host, auth, and SSH options</span></div></summary>
          <div class="fold-body settings-card">
          <div class="grid-3">
            <div>
              <label for="profileName">Name</label>
              <input id="profileName" placeholder="gpu-box">
            </div>
            <div>
              <label for="host">SSH host / IP</label>
              <input id="host" placeholder="192.168.1.20">
            </div>
            <div>
              <label for="username">SSH username</label>
              <input id="username" placeholder="ubuntu">
            </div>
          </div>
          <div class="grid-2">
            <div>
              <label for="password">SSH password (optional)</label>
              <input id="password" type="password" placeholder="Leave blank to keep existing password">
            </div>
            <div>
              <label for="keyFilename">SSH key path (optional)</label>
              <input id="keyFilename" placeholder="~/.ssh/id_ed25519">
            </div>
          </div>
          <div class="grid-4">
            <button class="primary" id="saveProfile">Save target</button>
            <button class="secondary" id="testProfile">Test SSH</button>
            <button class="secondary" id="loadProfileState">Load tmux state</button>
            <button class="danger" id="deleteProfile">Delete target</button>
          </div>
          <details class="fold">
            <summary>Advanced target options</summary>
            <div class="fold-body">
              <div class="grid-3">
                <div>
                  <label for="port">SSH port</label>
                  <input id="port" type="number" value="22">
                </div>
                <div>
                  <label for="profileGroup">Group</label>
                  <input id="profileGroup" placeholder="work">
                </div>
                <div>
                  <label for="profileTags">Tags</label>
                  <input id="profileTags" placeholder="gpu, research">
                </div>
              </div>
              <div class="grid-2">
                <div>
                  <label for="passwordRef">Password ref (vault)</label>
                  <input id="passwordRef" placeholder="env:CLAWDONE_OFFICE_PWD or file:~/.secrets/office.pwd">
                </div>
                <div>
                  <label for="tmuxBin">tmux binary</label>
                  <input id="tmuxBin" value="tmux">
                </div>
              </div>
              <div>
                <label for="profileDescription">Description</label>
                <input id="profileDescription" placeholder="Research box with multiple Codex agents">
              </div>
              <div class="grid-3">
                <div>
                  <label for="hostKeyPolicy">Host key policy</label>
                  <select id="hostKeyPolicy">
                    <option value="">Inherit server default</option>
                    <option value="strict">strict (verify known_hosts)</option>
                    <option value="accept-new">accept-new (trust first use)</option>
                    <option value="insecure">insecure (skip verification)</option>
                  </select>
                </div>
                <div>
                  <label for="sshTimeout">SSH connect timeout (sec)</label>
                  <input id="sshTimeout" type="number" min="0" placeholder="0 = inherit">
                </div>
                <div>
                  <label for="sshCommandTimeout">SSH command timeout (sec)</label>
                  <input id="sshCommandTimeout" type="number" min="0" placeholder="0 = inherit">
                </div>
              </div>
              <div class="grid-2">
                <div>
                  <label for="sshRetries">SSH retries</label>
                  <input id="sshRetries" type="number" min="0" placeholder="0 = no retry">
                </div>
                <div>
                  <label for="sshRetryBackoffMs">Retry backoff (ms)</label>
                  <input id="sshRetryBackoffMs" type="number" min="0" placeholder="250">
                </div>
              </div>
              <div class="checkbox">
                <input id="profileFavorite" type="checkbox">
                <label for="profileFavorite" style="margin:0">Favorite target</label>
              </div>
            </div>
          </details>
          </div>
        </details>
      </div>
    </section>
    </div>

    <div hidden>
      <select id="templateSelect"></select>
      <input id="templateName">
      <select id="templateScope"><option value=""></option><option value="current">current</option></select>
      <button id="applyTemplate" type="button"></button>
      <button id="saveTemplate" type="button"></button>
      <button id="deleteTemplate" type="button"></button>
      <select id="historySelect"></select>
      <div id="historyList"></div>
      <div id="historyPagination"></div>
      <button id="applyHistory" type="button"></button>
      <button id="clearHistory" type="button"></button>
    </div>

    <div class="page-view" id="view-chat">
    <section class="chatbot-layout">
      <aside class="chat-sidebar">
        <div class="chatbot-sidebar-header">
          <h2>Work</h2>
          <div class="hint">A lighter command view for the currently selected agent.</div>
        </div>
        <div class="chatbot-agent-card">
          <div class="chatbot-sidebar-title">Active agent</div>
          <strong id="currentAgentLabel">No pane selected</strong>
          <span id="currentAgentHint">Select a pane.</span>
        </div>
        <div class="chatbot-sidebar-panel">
          <div class="chatbot-sidebar-title">Agents</div>
          <div id="workerList" class="worker-strip"></div>
        </div>
        <div class="chatbot-sidebar-panel">
          <label for="chatSessionSelect">Session</label>
          <select id="chatSessionSelect"></select>
          <div class="hint" id="chatConversationHint">Choose a thread to focus the feed.</div>
        </div>
        <div class="chatbot-sidebar-panel">
          <div class="chatbot-sidebar-title">Threads</div>
          <div id="conversationList" class="thread-list"></div>
        </div>
      </aside>

      <section class="chat-main">
        <div class="chat-main-header">
          <div>
            <h2>Command stream</h2>
            <span class="hint" id="selectedPaneLabel">No pane selected</span>
          </div>
          <div class="chat-main-actions">
            <button class="ghost" id="copyTargetLabel">Copy</button>
            <button class="secondary" id="refreshChatPane">Refresh</button>
            <button class="danger" id="interrupt">Interrupt</button>
          </div>
        </div>
        <div id="chatFeed" class="chat-feed"></div>
        <pre id="paneOutput" style="display:none">Choose a target first.</pre>
        <div class="composer">
          <div class="composer-head">
            <label for="command">Message</label>
          </div>
          <textarea id="command" class="chat-input" placeholder="Describe the next step for the selected agent. Example: analyze the bug, patch it, run tests, then summarize the changes."></textarea>
          <div class="composer-actions">
            <div class="row-inline">
              <button class="primary" id="sendCommand">Send</button>
              <button class="ghost" id="appendNewline">New line</button>
              <button class="primary" id="startVoice">Start voice</button>
              <button class="secondary" id="stopVoice">Stop voice</button>
            </div>
          </div>
        </div>
      </section>
    </section>
    </div>

    <div class="page-view" id="view-todo">
    <section class="todo-shell">
      <section class="card todo-compose">
        <div class="section-title"><h2>Tasks</h2><span class="hint">Create work items for the current agent.</span></div>
        <div>
          <label for="todoDetail">Task brief</label>
          <textarea id="todoDetail" placeholder="Describe the task, constraints, and acceptance criteria for the current agent."></textarea>
        </div>
        <div class="grid-2">
          <button class="primary" id="createTodo">Create task for current agent</button>
          <button class="secondary" id="refreshTodos">Refresh task list</button>
        </div>
        <details class="fold fold-panel" data-fold-key="todo-list" open>
          <summary><div class="fold-head"><strong>Task board</strong><span>Active work grouped by agent thread</span></div></summary>
          <div class="fold-body">
            <div id="todoBoard" class="todo-board"></div>
            <div class="pagination" id="todoPagination" style="display:none"></div>
          </div>
        </details>
      </section>

      <section class="card inspector-stack">
        <div class="section-title"><h2>Inspector</h2><span class="hint">Selected task details, evidence, and reusable actions</span></div>
        <select id="todoSelect" class="hidden-select"></select>
        <div class="hint" id="todoMeta">No tasks yet.</div>
        <details class="fold fold-panel" data-fold-key="todo-advanced" open>
          <summary><div class="fold-head"><strong>Task details</strong><span>Status, evidence, and templates</span></div></summary>
          <div class="fold-body">
            <div class="grid-3">
              <div>
                <label for="todoTitle">Title</label>
                <input id="todoTitle" placeholder="Override the title if needed">
              </div>
              <div>
                <label for="todoPriority">Priority</label>
                <select id="todoPriority">
                  <option value="low">low</option>
                  <option value="medium" selected>medium</option>
                  <option value="high">high</option>
                  <option value="urgent">urgent</option>
                </select>
              </div>
              <div>
                <label for="todoAssignee">Assignee</label>
                <input id="todoAssignee" placeholder="backend-agent">
              </div>
            </div>
            <div class="grid-2">
              <div>
                <label for="todoStatus">Status</label>
                <select id="todoStatus">
                  <option value="todo">todo</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                  <option value="verified">verified</option>
                  <option value="blocked">blocked</option>
                </select>
              </div>
              <div>
                <label for="todoProgressNote">Progress note</label>
                <input id="todoProgressNote" placeholder="What changed in this step?">
              </div>
            </div>
            <div class="action-strip">
              <button class="secondary" id="quickTodo">Quick task</button>
              <button class="secondary" id="createTriplet">Triplet workflow</button>
              <button class="secondary" id="applyTodoToCommand">Use in command</button>
              <button class="secondary" id="updateTodoStatus">Update status</button>
            </div>
            <div>
              <label for="todoEvidence">Evidence (text or JSON)</label>
              <textarea id="todoEvidence" placeholder='Text note, or JSON like {"type":"pane_output","content":"tests passed"}'></textarea>
            </div>
            <div class="action-strip">
              <button class="secondary" id="addTodoEvidence">Add evidence</button>
              <button class="ghost" id="reportTodo">Agent report</button>
              <button class="secondary" id="applyTodoTemplate">Apply template</button>
              <button class="secondary" id="saveTodoTemplate">Save template</button>
            </div>
            <div class="grid-3">
              <div>
                <label for="todoTemplateSelect">Template</label>
                <select id="todoTemplateSelect"></select>
              </div>
              <div>
                <label for="todoTemplateName">Template name</label>
                <input id="todoTemplateName" placeholder="Bugfix task template">
              </div>
              <div class="action-strip">
                <button class="danger" id="deleteTodoTemplate">Delete template</button>
              </div>
            </div>
            <div class="grid-2">
              <div>
                <label for="todoTimeline">Timeline</label>
                <pre id="todoTimeline">No todo selected.</pre>
              </div>
              <div>
                <label for="todoEvidenceList">Evidence</label>
                <pre id="todoEvidenceList">No evidence yet.</pre>
              </div>
            </div>
            <div>
              <label for="auditSelect">Recent audit events (current agent)</label>
              <select id="auditSelect"></select>
            </div>
          </div>
        </details>
      </section>
    </section>
    </div>

    <div class="page-view" id="view-delivery">
    <section class="delivery-shell">
      <section class="card grid">
        <div class="section-title"><h2>Delivery</h2><span class="hint">Review the selected agent, task status, timeline, and evidence.</span></div>
        <div class="kpi">
          <strong id="deliveryAgentLabel">No pane selected</strong>
          <span id="deliveryAgentHint"></span>
        </div>
        <div class="hint" id="deliveryTodoMeta">No todo selected.</div>
        <details class="fold fold-panel" data-fold-key="delivery-summary" open>
          <summary><div class="fold-head"><strong>Summary</strong><span>Timeline and evidence</span></div></summary>
          <div class="fold-body grid-2">
            <div>
              <label for="deliveryTimeline">Timeline</label>
              <pre id="deliveryTimeline">No todo selected.</pre>
            </div>
            <div>
              <label for="deliveryEvidence">Evidence</label>
              <pre id="deliveryEvidence">No evidence yet.</pre>
            </div>
          </div>
        </details>
      </section>
      <section class="card grid">
        <div class="section-title"><h2>Snapshot</h2><span class="hint">Recent audit activity and pane output</span></div>
        <details class="fold fold-panel" data-fold-key="delivery-output" open>
          <summary><div class="fold-head"><strong>Output</strong><span>Audit and pane snapshot</span></div></summary>
          <div class="fold-body">
            <div>
              <label for="deliveryAudit">Recent audit events</label>
              <pre id="deliveryAudit">No audit events.</pre>
            </div>
            <div>
              <label for="deliveryPaneOutput">Current delivery snapshot</label>
              <pre id="deliveryPaneOutput">Choose a target first.</pre>
            </div>
          </div>
        </details>
      </section>
    </section>
    </div>

    <nav class="tabbar" aria-label="Primary">
      <button class="tab-button" type="button" data-view-button="chat">Work</button>
      <button class="tab-button" type="button" data-view-button="todo">Tasks</button>
      <button class="tab-button" type="button" data-view-button="delivery">Delivery</button>
      <button class="tab-button active" type="button" data-view-button="dashboard">Home</button>
      <button class="tab-button" type="button" data-view-button="auth">Settings</button>
    </nav>

  </div>

  <script>
    const tokenInput = document.getElementById('token');
    const statusEl = document.getElementById('status');
    const profileSelect = document.getElementById('profileSelect');
    const targetListEl = document.getElementById('targetList');
    const profileNameInput = document.getElementById('profileName');
    const profileGroupInput = document.getElementById('profileGroup');
    const profileTagsInput = document.getElementById('profileTags');
    const hostInput = document.getElementById('host');
    const portInput = document.getElementById('port');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const passwordRefInput = document.getElementById('passwordRef');
    const keyFilenameInput = document.getElementById('keyFilename');
    const tmuxBinInput = document.getElementById('tmuxBin');
    const profileDescriptionInput = document.getElementById('profileDescription');
    const hostKeyPolicySelect = document.getElementById('hostKeyPolicy');
    const sshTimeoutInput = document.getElementById('sshTimeout');
    const sshCommandTimeoutInput = document.getElementById('sshCommandTimeout');
    const sshRetriesInput = document.getElementById('sshRetries');
    const sshRetryBackoffMsInput = document.getElementById('sshRetryBackoffMs');
    const profileFavoriteInput = document.getElementById('profileFavorite');
    const sessionSelect = document.getElementById('session');
    const windowSelect = document.getElementById('window');
    const paneSelect = document.getElementById('pane');
    const aliasInput = document.getElementById('agentAlias');
    const templateSelect = document.getElementById('templateSelect');
    const templateNameInput = document.getElementById('templateName');
    const templateScopeSelect = document.getElementById('templateScope');
    const paneLinesInput = document.getElementById('paneLines');
    const targetPageSizeInput = document.getElementById('targetPageSize');
    const historyPageSizeInput = document.getElementById('historyPageSize');
    const todoPageSizeInput = document.getElementById('todoPageSize');
    const historyListEl = document.getElementById('historyList');
    const todoBoardEl = document.getElementById('todoBoard');
    const chatFeedEl = document.getElementById('chatFeed');
    const chatSessionSelect = document.getElementById('chatSessionSelect');
    const chatConversationHintEl = document.getElementById('chatConversationHint');
    const conversationListEl = document.getElementById('conversationList');
    const workerListEl = document.getElementById('workerList');
    const targetPaginationEl = document.getElementById('targetPagination');
    const historyPaginationEl = document.getElementById('historyPagination');
    const todoPaginationEl = document.getElementById('todoPagination');
    const viewButtons = Array.from(document.querySelectorAll('[data-view-button]'));
    const dashboardViewEl = document.getElementById('view-dashboard');
    const authViewEl = document.getElementById('view-auth');
    const chatViewEl = document.getElementById('view-chat');
    const todoViewEl = document.getElementById('view-todo');
    const deliveryViewEl = document.getElementById('view-delivery');
    const historySelect = document.getElementById('historySelect');
    const commandInput = document.getElementById('command');
    const paneOutputEl = document.getElementById('paneOutput');
    const selectedPaneLabel = document.getElementById('selectedPaneLabel');
    const currentAgentLabelEl = document.getElementById('currentAgentLabel');
    const currentAgentHintEl = document.getElementById('currentAgentHint');
    const deliveryAgentLabelEl = document.getElementById('deliveryAgentLabel');
    const deliveryAgentHintEl = document.getElementById('deliveryAgentHint');
    const deliveryTodoMetaEl = document.getElementById('deliveryTodoMeta');
    const deliveryTimelineEl = document.getElementById('deliveryTimeline');
    const deliveryEvidenceEl = document.getElementById('deliveryEvidence');
    const deliveryAuditEl = document.getElementById('deliveryAudit');
    const deliveryPaneOutputEl = document.getElementById('deliveryPaneOutput');
    const todoTitleInput = document.getElementById('todoTitle');
    const todoDetailInput = document.getElementById('todoDetail');
    const todoPrioritySelect = document.getElementById('todoPriority');
    const todoAssigneeInput = document.getElementById('todoAssignee');
    const todoSelect = document.getElementById('todoSelect');
    const todoStatusSelect = document.getElementById('todoStatus');
    const todoProgressNoteInput = document.getElementById('todoProgressNote');
    const todoEvidenceInput = document.getElementById('todoEvidence');
    const todoTemplateSelect = document.getElementById('todoTemplateSelect');
    const todoTemplateNameInput = document.getElementById('todoTemplateName');
    const todoTimelineEl = document.getElementById('todoTimeline');
    const todoEvidenceListEl = document.getElementById('todoEvidenceList');
    const auditSelect = document.getElementById('auditSelect');
    const todoMetaEl = document.getElementById('todoMeta');
    const profileCountEl = document.getElementById('profileCount');
    const onlineCountEl = document.getElementById('onlineCount');
    const sessionCountEl = document.getElementById('sessionCount');
    const paneCountEl = document.getElementById('paneCount');
    const dispatchMetricEl = document.getElementById('dispatchMetric');
    const doneMetricEl = document.getElementById('doneMetric');
    const verifyMetricEl = document.getElementById('verifyMetric');
    const misrouteMetricEl = document.getElementById('misrouteMetric');

    const storedToken = localStorage.getItem('clawdone-token') || '';
    tokenInput.value = storedToken;

    const DEFAULT_UI_SETTINGS = {
      paneLines: 120,
      targetPageSize: 6,
      historyPageSize: 8,
      todoPageSize: 6,
    };

    function loadUiSettings() {
      try {
        return { ...DEFAULT_UI_SETTINGS, ...(JSON.parse(localStorage.getItem('clawdone-ui-settings') || '{}') || {}) };
      } catch (_) {
        return { ...DEFAULT_UI_SETTINGS };
      }
    }


    function initializeFoldPanels() {
      foldPanels.forEach((panel) => {
        const key = panel.dataset.foldKey;
        if (!key) return;
        const stored = localStorage.getItem(`clawdone-fold-${key}`);
        if (stored === 'open') panel.open = true;
        if (stored === 'closed') panel.open = false;
        panel.addEventListener('toggle', () => {
          localStorage.setItem(`clawdone-fold-${key}`, panel.open ? 'open' : 'closed');
        });
      });
    }

    let profilesCache = [];
    let dashboardCache = { targets: [] };
    let stateCache = { sessions: [] };
    let templatesCache = [];
    let historyCache = [];
    let todosCache = [];
    let todoTemplatesCache = [];
    let auditLogsCache = [];
    let todoStream = null;
    let latestPaneOutput = 'Choose a target first.';
    let uiSettings = loadUiSettings();
    let uiState = { targetPage: 1, historyPage: 1, todoPage: 1, currentView: localStorage.getItem('clawdone-view') || 'dashboard' };
    const foldPanels = Array.from(document.querySelectorAll('details[data-fold-key]'));
    let paneLoadVersion = 0;
    let todoLoadVersion = 0;
    let remoteStateLoadVersion = 0;

    function headers() {
      const token = tokenInput.value.trim();
      if (token) {
        localStorage.setItem('clawdone-token', token);
      } else {
        localStorage.removeItem('clawdone-token');
      }
      const result = { 'Content-Type': 'application/json' };
      if (token) {
        result['Authorization'] = `Bearer ${token}`;
      }
      return result;
    }

    function setStatus(message, type = 'info') {
      statusEl.textContent = message;
      statusEl.classList.remove('error', 'warn');
      if (type === 'error') statusEl.classList.add('error');
      if (type === 'warn') statusEl.classList.add('warn');
    }

    function optionalIntOrZero(value) {
      const parsed = Number.parseInt(String(value || '').trim(), 10);
      if (!Number.isFinite(parsed)) return 0;
      return Math.max(0, parsed);
    }

    function positiveInt(value, fallback, max = 500) {
      const parsed = Number.parseInt(String(value || '').trim(), 10);
      if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
      return Math.min(parsed, max);
    }

    function syncUiSettingsInputs() {
      paneLinesInput.value = String(uiSettings.paneLines);
      targetPageSizeInput.value = String(uiSettings.targetPageSize);
      historyPageSizeInput.value = String(uiSettings.historyPageSize);
      todoPageSizeInput.value = String(uiSettings.todoPageSize);
    }

    function currentUiSettings() {
      return {
        paneLines: positiveInt(paneLinesInput.value, DEFAULT_UI_SETTINGS.paneLines, 400),
        targetPageSize: positiveInt(targetPageSizeInput.value, DEFAULT_UI_SETTINGS.targetPageSize, 24),
        historyPageSize: positiveInt(historyPageSizeInput.value, DEFAULT_UI_SETTINGS.historyPageSize, 30),
        todoPageSize: positiveInt(todoPageSizeInput.value, DEFAULT_UI_SETTINGS.todoPageSize, 20),
      };
    }

    function saveUiSettings() {
      uiSettings = currentUiSettings();
      uiState = { targetPage: 1, historyPage: 1, todoPage: 1 };
      localStorage.setItem('clawdone-ui-settings', JSON.stringify(uiSettings));
      syncUiSettingsInputs();
      renderTargetCards();
      renderHistory();
      renderTodos();
      renderChatFeed();
      loadPane().catch(() => {});
      setStatus('Settings saved. Front-end pagination and chat view updated.');
    }

    function resetUiSettings() {
      uiSettings = { ...DEFAULT_UI_SETTINGS };
      uiState = { targetPage: 1, historyPage: 1, todoPage: 1 };
      localStorage.removeItem('clawdone-ui-settings');
      syncUiSettingsInputs();
      renderTargetCards();
      renderHistory();
      renderTodos();
      renderChatFeed();
      loadPane().catch(() => {});
      setStatus('View settings reset to defaults.');
    }

    function clampPage(page, totalPages) {
      return Math.min(Math.max(1, page), Math.max(1, totalPages));
    }

    function paginate(items, page, pageSize) {
      const totalPages = Math.max(1, Math.ceil(items.length / Math.max(1, pageSize)));
      const safePage = clampPage(page, totalPages);
      const start = (safePage - 1) * pageSize;
      return {
        items: items.slice(start, start + pageSize),
        page: safePage,
        totalPages,
        totalItems: items.length,
      };
    }

    function buildPageTokens(page, totalPages) {
      if (totalPages <= 5) {
        return Array.from({ length: totalPages }, (_, index) => index + 1);
      }
      const tokens = [1];
      const start = Math.max(2, page - 1);
      const end = Math.min(totalPages - 1, page + 1);
      if (start > 2) tokens.push('…');
      for (let current = start; current <= end; current += 1) {
        tokens.push(current);
      }
      if (end < totalPages - 1) tokens.push('…');
      tokens.push(totalPages);
      return tokens;
    }

    function renderPager(container, page, totalPages, onSelect) {
      container.innerHTML = '';
      if (totalPages <= 1) return;

      const prevButton = document.createElement('button');
      prevButton.type = 'button';
      prevButton.className = 'ghost';
      prevButton.textContent = '‹';
      prevButton.disabled = page <= 1;
      prevButton.addEventListener('click', () => onSelect(page - 1));
      container.appendChild(prevButton);

      buildPageTokens(page, totalPages).forEach((token) => {
        if (token === '…') {
          const ellipsis = document.createElement('span');
          ellipsis.className = 'page-ellipsis';
          ellipsis.textContent = '…';
          container.appendChild(ellipsis);
          return;
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = token === page ? 'ghost page-current' : 'ghost';
        button.textContent = String(token);
        button.disabled = token === page;
        button.addEventListener('click', () => onSelect(token));
        container.appendChild(button);
      });

      const nextButton = document.createElement('button');
      nextButton.type = 'button';
      nextButton.className = 'ghost';
      nextButton.textContent = '›';
      nextButton.disabled = page >= totalPages;
      nextButton.addEventListener('click', () => onSelect(page + 1));
      container.appendChild(nextButton);
    }

    function escapeHtml(text) {
      return String(text || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        ...options,
        headers: { ...headers(), ...(options.headers || {}) },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `Request failed (${response.status})`);
      }
      return payload;
    }

    function currentProfileName() {
      return profileSelect.value.trim();
    }

    function currentProfile() {
      return profilesCache.find((profile) => profile.name === currentProfileName()) || null;
    }

    function currentWindowLabel(window) {
      if (!window) return 'No window selected';
      return `${window.index}: ${window.name || 'unnamed window'}`;
    }

    function setActiveView(view) {
      const safeView = ['dashboard', 'auth', 'chat', 'todo', 'delivery'].includes(view) ? view : 'dashboard';
      uiState.currentView = safeView;
      localStorage.setItem('clawdone-view', safeView);
      dashboardViewEl.classList.toggle('active', safeView === 'dashboard');
      authViewEl.classList.toggle('active', safeView === 'auth');
      chatViewEl.classList.toggle('active', safeView === 'chat');
      todoViewEl.classList.toggle('active', safeView === 'todo');
      deliveryViewEl.classList.toggle('active', safeView === 'delivery');
      viewButtons.forEach((button) => button.classList.toggle('active', button.dataset.viewButton === safeView));
      if (typeof window.scrollTo === 'function') {
        window.scrollTo(0, 0);
      }
    }

    function currentDashboardTarget() {
      return (dashboardCache.targets || []).find((target) => target.name === currentProfileName()) || null;
    }

    function profileLabel(profile) {
      const favorite = profile.favorite ? '★ ' : '';
      const group = profile.group ? ` · ${profile.group}` : '';
      return `${favorite}${profile.name}${group}`;
    }

    function targetStatusLabel(target) {
      const status = target.online ? 'online' : 'offline';
      return `${target.name} · ${status} · ${target.session_count} sessions · ${target.pane_count} panes`;
    }

    function fillProfileForm(profile) {
      if (!profile) {
        profileNameInput.value = '';
        profileGroupInput.value = 'General';
        profileTagsInput.value = '';
        hostInput.value = '';
        portInput.value = '22';
        usernameInput.value = '';
        passwordInput.value = '';
        passwordRefInput.value = '';
        passwordInput.placeholder = 'Leave blank to keep existing password';
        keyFilenameInput.value = '';
        tmuxBinInput.value = 'tmux';
        profileDescriptionInput.value = '';
        hostKeyPolicySelect.value = '';
        sshTimeoutInput.value = '';
        sshCommandTimeoutInput.value = '';
        sshRetriesInput.value = '';
        sshRetryBackoffMsInput.value = '';
        profileFavoriteInput.checked = false;
        return;
      }
      profileNameInput.value = profile.name || '';
      profileGroupInput.value = profile.group || 'General';
      profileTagsInput.value = (profile.tags || []).join(', ');
      hostInput.value = profile.host || '';
      portInput.value = String(profile.port || 22);
      usernameInput.value = profile.username || '';
      passwordInput.value = '';
      passwordRefInput.value = profile.password_ref || '';
      passwordInput.placeholder = profile.has_password ? 'Stored password is kept unless you enter a new one' : 'Optional password';
      keyFilenameInput.value = profile.key_filename || '';
      tmuxBinInput.value = profile.tmux_bin || 'tmux';
      profileDescriptionInput.value = profile.description || '';
      hostKeyPolicySelect.value = profile.host_key_policy || '';
      sshTimeoutInput.value = profile.ssh_timeout ? String(profile.ssh_timeout) : '';
      sshCommandTimeoutInput.value = profile.ssh_command_timeout ? String(profile.ssh_command_timeout) : '';
      sshRetriesInput.value = profile.ssh_retries ? String(profile.ssh_retries) : '';
      sshRetryBackoffMsInput.value = profile.ssh_retry_backoff_ms ? String(profile.ssh_retry_backoff_ms) : '';
      profileFavoriteInput.checked = Boolean(profile.favorite);
    }

    function readProfileForm() {
      return {
        name: profileNameInput.value.trim(),
        group: profileGroupInput.value.trim() || 'General',
        tags: profileTagsInput.value.trim(),
        host: hostInput.value.trim(),
        port: Number(portInput.value || '22'),
        username: usernameInput.value.trim(),
        password: passwordInput.value,
        password_ref: passwordRefInput.value.trim(),
        key_filename: keyFilenameInput.value.trim(),
        tmux_bin: tmuxBinInput.value.trim() || 'tmux',
        description: profileDescriptionInput.value.trim(),
        host_key_policy: hostKeyPolicySelect.value.trim(),
        ssh_timeout: optionalIntOrZero(sshTimeoutInput.value),
        ssh_command_timeout: optionalIntOrZero(sshCommandTimeoutInput.value),
        ssh_retries: optionalIntOrZero(sshRetriesInput.value),
        ssh_retry_backoff_ms: optionalIntOrZero(sshRetryBackoffMsInput.value),
        favorite: profileFavoriteInput.checked,
      };
    }

    function updateKpis() {
      profileCountEl.textContent = String(dashboardCache.profile_count || profilesCache.length || 0);
      onlineCountEl.textContent = String(dashboardCache.online_count || 0);
      const sessions = stateCache.sessions || [];
      const windows = sessions.flatMap((session) => session.windows || []);
      const panes = windows.flatMap((window) => window.panes || []);
      sessionCountEl.textContent = String(sessions.length);
      paneCountEl.textContent = String(panes.length);
      const metrics = dashboardCache.workflow_metrics || {};
      const dispatch = Number(metrics.t_dispatch_avg_sec);
      const done = Number(metrics.t_done_avg_sec);
      const verify = Number(metrics.t_verify_avg_sec);
      const misroute = Number(metrics.misroute_pct);
      dispatchMetricEl.textContent = Number.isFinite(dispatch) ? String(Math.round(dispatch)) : '-';
      doneMetricEl.textContent = Number.isFinite(done) ? String(Math.round(done)) : '-';
      verifyMetricEl.textContent = Number.isFinite(verify) ? String(Math.round(verify)) : '-';
      misrouteMetricEl.textContent = Number.isFinite(misroute) ? `${misroute.toFixed(2)}%` : '0%';
    }

    function option(label, value) {
      const element = document.createElement('option');
      element.value = value;
      element.textContent = label;
      return element;
    }

    function selectedSessionData() {
      return (stateCache.sessions || []).find((session) => session.name === sessionSelect.value) || null;
    }

    function selectedWindowData() {
      const session = selectedSessionData();
      return session ? (session.windows || []).find((window) => String(window.index) === windowSelect.value) || null : null;
    }

    function selectedPaneData() {
      const window = selectedWindowData();
      return window ? (window.panes || []).find((pane) => pane.target === paneSelect.value) || null : null;
    }

    function currentTargetLabel() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      if (!profile || !target) return 'No pane selected';
      const pane = selectedPaneData();
      const alias = pane && pane.alias ? ` (${pane.alias})` : '';
      return `${profile} → ${target}${alias}`;
    }

    function renderChatFeed() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      chatFeedEl.innerHTML = '';
      if (!profile || !target) {
        chatFeedEl.innerHTML = '<div class="empty-state">Select a pane to start.</div>';
        return;
      }
      const relatedHistory = historyCache.filter((entry) => entry.profile === profile && entry.target === target);
      const historyPage = paginate(relatedHistory, uiState.historyPage, uiSettings.historyPageSize);
      uiState.historyPage = historyPage.page;

      if (!historyPage.items.length && !latestPaneOutput.trim()) {
        chatFeedEl.innerHTML = '<div class="empty-state">No messages yet.</div>';
        return;
      }

      [...historyPage.items].reverse().forEach((entry) => {
        const node = document.createElement('div');
        node.className = 'message user';
        const alias = entry.alias || entry.target;
        node.innerHTML = `
          <div class="message-meta">You · ${escapeHtml(entry.created_at || '-')} · ${escapeHtml(alias)}</div>
          <div class="message-body">${escapeHtml(entry.command || '')}</div>
        `;
        chatFeedEl.appendChild(node);
      });

      const pane = selectedPaneData();
      const alias = (pane && pane.alias) || target;
      const agentNode = document.createElement('div');
      agentNode.className = 'message agent';
      agentNode.innerHTML = `
        <div class="message-meta">Codex · live pane snapshot · ${escapeHtml(alias)}</div>
        <div class="message-body">${escapeHtml(latestPaneOutput || '[empty pane]')}</div>
      `;
      chatFeedEl.appendChild(agentNode);
      chatFeedEl.scrollTop = chatFeedEl.scrollHeight;
    }

    function renderChatSessionSelect() {
      const previous = chatSessionSelect.value;
      chatSessionSelect.innerHTML = '';
      const sessions = stateCache.sessions || [];
      if (!sessions.length) {
        chatSessionSelect.appendChild(option('No tmux sessions', ''));
        return;
      }
      sessions.forEach((session) => {
        chatSessionSelect.appendChild(option(`${session.name} (${(session.windows || []).length} windows)`, session.name));
      });
      chatSessionSelect.value = sessions.some((session) => session.name === previous) ? previous : sessionSelect.value;
    }

    function renderConversationList() {
      conversationListEl.innerHTML = '';
      const session = selectedSessionData();
      if (!session || !(session.windows || []).length) {
        conversationListEl.innerHTML = '<div class="empty-state">No threads.</div>';
        chatConversationHintEl.textContent = 'No threads yet.';
        return;
      }
      const currentWindow = selectedWindowData();
      chatConversationHintEl.textContent = `${session.name} · ${session.windows.length} conversation(s)`;
      session.windows.forEach((window) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `thread-card ${currentWindow && String(currentWindow.index) === String(window.index) ? 'active' : ''}`;
        const workerNames = (window.panes || []).map((pane) => pane.alias || pane.target).slice(0, 4).join(' · ');
        button.innerHTML = `
          <div class="thread-title"><span>${escapeHtml(currentWindowLabel(window))}</span><span class="muted">${(window.panes || []).length} workers</span></div>
          <div class="hint">${escapeHtml(workerNames || 'No workers yet')}</div>
        `;
        button.addEventListener('click', () => {
          windowSelect.value = String(window.index);
          uiState.historyPage = 1;
          uiState.todoPage = 1;
          renderPanes();
          renderConversationList();
          loadPane();
          loadTodos();
        });
        conversationListEl.appendChild(button);
      });
    }

    function workerDisplayName(pane) {
      if (!pane) return 'Agent';
      return String(pane.alias || pane.target || 'Agent').trim() || 'Agent';
    }

    function workerInitials(pane) {
      const label = workerDisplayName(pane)
        .replace(/[_:.]+/g, ' ')
        .trim();
      const parts = label.split(/\\s+/).filter(Boolean);
      if (!parts.length) return 'AG';
      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
      }
      return `${parts[0][0] || ''}${parts[1][0] || ''}`.toUpperCase();
    }

    function renderWorkerList() {
      workerListEl.innerHTML = '';
      const window = selectedWindowData();
      if (!window || !(window.panes || []).length) {
        workerListEl.innerHTML = '<div class="empty-state">No agents.</div>';
        return;
      }
      window.panes.forEach((pane) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `worker-chip ${pane.target === paneSelect.value ? 'active' : ''}`;
        const label = workerDisplayName(pane);
        const command = pane.current_command || 'shell';
        const initials = workerInitials(pane);
        const liveClass = pane.active ? 'live' : '';
        button.title = `${pane.target} · ${command}`;
        button.innerHTML = `
          <div class="worker-avatar">${escapeHtml(initials)}<span class="worker-dot ${liveClass}"></span></div>
          <div class="worker-copy">
            <div class="worker-name">${escapeHtml(label)}</div>
            <div class="worker-meta">${escapeHtml(command)} · ${escapeHtml(pane.target || '')}</div>
          </div>
        `;
        button.addEventListener('click', () => {
          paneSelect.value = pane.target;
          uiState.historyPage = 1;
          uiState.todoPage = 1;
          syncAliasInput();
          renderWorkerList();
          loadPane();
          loadTodos();
        });
        workerListEl.appendChild(button);
      });
    }

    function syncDeliveryView() {
      deliveryAgentLabelEl.textContent = currentTargetLabel();
      deliveryAgentHintEl.textContent = currentAgentHintEl.textContent;
      deliveryPaneOutputEl.textContent = latestPaneOutput || '[empty pane]';

      const todo = selectedTodo();
      if (!todo) {
        deliveryTodoMetaEl.textContent = 'No todo selected.';
        deliveryTimelineEl.textContent = 'No todo selected.';
        deliveryEvidenceEl.textContent = 'No evidence yet.';
      } else {
        deliveryTodoMetaEl.textContent = todoMetaEl.textContent;
        deliveryTimelineEl.textContent = todoTimelineEl.textContent;
        deliveryEvidenceEl.textContent = todoEvidenceListEl.textContent;
      }

      if (!auditLogsCache.length) {
        deliveryAuditEl.textContent = 'No audit events.';
        return;
      }
      deliveryAuditEl.textContent = auditLogsCache
        .slice(0, 12)
        .map((entry) => `${entry.created_at || '-'} · ${entry.action || '-'} · ${entry.actor || 'unknown'} · ${entry.note || entry.status || '-'}`)
        .join('\\n');
    }

    function updateCurrentAgentCard() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      currentAgentLabelEl.textContent = currentTargetLabel();
      if (!profile || !target) {
        currentAgentHintEl.textContent = 'Select a pane.';
        syncDeliveryView();
        return;
      }
      const pane = selectedPaneData();
      const window = selectedWindowData();
      const session = selectedSessionData();
      const alias = pane && pane.alias ? pane.alias : '(no alias)';
      const cmd = pane && pane.current_command ? pane.current_command : 'shell';
      const conversation = window ? currentWindowLabel(window) : 'no window';
      currentAgentHintEl.textContent = `${profile} · ${session ? session.name : '-'} · ${conversation} · ${alias} · ${cmd}`;
      syncDeliveryView();
    }

    function requireCurrentAgent(action, silent = false) {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      if (!profile || !target) {
        if (!silent) setStatus(`Choose a target and pane before ${action}.`, 'error');
        return null;
      }
      return { profile, target };
    }

    function selectedTodo() {
      return todosCache.find((todo) => todo.id === todoSelect.value) || null;
    }

    function parseEvidenceInput(raw) {
      const text = String(raw || '').trim();
      if (!text) return null;
      if ((text.startsWith('{') && text.endsWith('}')) || (text.startsWith('[') && text.endsWith(']'))) {
        try {
          return JSON.parse(text);
        } catch (_) {
          return text;
        }
      }
      return text;
    }

    function closeTodoStream() {
      if (todoStream) {
        todoStream.close();
        todoStream = null;
      }
    }

    function openTodoStream() {
      closeTodoStream();
      const selected = requireCurrentAgent('starting live updates', true);
      if (!selected || !window.EventSource) return;
      const token = tokenInput.value.trim();
      const query = new URLSearchParams({
        profile: selected.profile,
        target: selected.target,
        interval: '3',
      });
      if (token) query.set('token', token);
      const streamUrl = `/api/todos/stream?${query.toString()}`;
      todoStream = new EventSource(streamUrl);
      todoStream.onmessage = (event) => {
        try {
          JSON.parse(event.data || '{}');
          loadTodos().catch(() => {});
          loadDashboard().catch(() => {});
        } catch (_) {
          // ignore malformed chunks
        }
      };
      todoStream.onerror = () => {
        // Connection may be rotated by server; fallback polling remains active.
      };
    }

    function renderProfileSelect() {
      const previous = currentProfileName();
      profileSelect.innerHTML = '';
      if (!profilesCache.length) {
        profileSelect.appendChild(option('No saved targets', ''));
        fillProfileForm(null);
        return;
      }
      profilesCache.forEach((profile) => profileSelect.appendChild(option(profileLabel(profile), profile.name)));
      profileSelect.value = profilesCache.some((profile) => profile.name === previous) ? previous : profilesCache[0].name;
      fillProfileForm(currentProfile());
    }

    function renderTargetCards() {
      targetListEl.innerHTML = '';
      const targets = dashboardCache.targets || [];
      if (!targets.length) {
        targetListEl.innerHTML = '<div class="muted">No targets yet. Save one to get started.</div>';
        targetPaginationEl.innerHTML = '';
        return;
      }
      const page = paginate(targets, uiState.targetPage, uiSettings.targetPageSize);
      uiState.targetPage = page.page;
      renderPager(targetPaginationEl, page.page, page.totalPages, (nextPage) => {
        uiState.targetPage = nextPage;
        renderTargetCards();
      });
      page.items.forEach((target) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = `target-card ${target.name === currentProfileName() ? 'active' : ''}`;
        const todoSummary = target.todo_summary || {};
        const inProgress = Number(todoSummary.in_progress_count || 0);
        const lastNote = String(todoSummary.last_note || '').trim();
        card.innerHTML = `
          <div class="target-card-head">
            <div class="target-card-name">
              <strong>${target.favorite ? '★ ' : ''}${escapeHtml(target.name)}</strong>
              <span class="target-card-host">${escapeHtml(target.host || 'No host')}</span>
            </div>
            <span class="badge ${target.online ? 'ok' : 'bad'}">${target.online ? 'Online' : 'Offline'}</span>
          </div>
          <div class="badge-row">
            <span class="badge">${escapeHtml(target.group || 'General')}</span>
            <span class="badge">${target.session_count} sessions</span>
            <span class="badge">${target.pane_count} panes</span>
            <span class="badge">${inProgress} active tasks</span>
          </div>
          <div class="hint">${escapeHtml(target.error ? target.error : (lastNote || target.description || target.tags.join(', ') || 'Ready'))}</div>
          <div class="target-card-foot"><span>${escapeHtml((target.tags || []).slice(0, 3).join(' · ') || 'No tags')}</span><span>${target.online ? 'Available' : 'Needs attention'}</span></div>
        `;
        card.addEventListener('click', async () => {
          profileSelect.value = target.name;
          fillProfileForm(currentProfile());
          await loadSelectedProfile();
        });
        targetListEl.appendChild(card);
      });
    }

    function renderSessions() {
      const previousSession = sessionSelect.value;
      sessionSelect.innerHTML = '';
      const sessions = stateCache.sessions || [];
      if (!sessions.length) {
        sessionSelect.appendChild(option('No tmux sessions', ''));
        chatSessionSelect.innerHTML = '';
        chatSessionSelect.appendChild(option('No tmux sessions', ''));
        windowSelect.innerHTML = '';
        paneSelect.innerHTML = '';
        aliasInput.value = '';
        selectedPaneLabel.textContent = currentTargetLabel();
        renderConversationList();
        renderWorkerList();
        updateKpis();
        return;
      }
      sessions.forEach((session) => {
        sessionSelect.appendChild(option(`${session.name} (${(session.windows || []).length} windows)`, session.name));
      });
      sessionSelect.value = sessions.some((session) => session.name === previousSession) ? previousSession : sessions[0].name;
      renderChatSessionSelect();
      renderWindows();
      updateKpis();
    }

    function renderWindows() {
      const previousWindow = windowSelect.value;
      const session = selectedSessionData();
      windowSelect.innerHTML = '';
      if (!session || !(session.windows || []).length) {
        windowSelect.appendChild(option('No windows', ''));
        paneSelect.innerHTML = '';
        aliasInput.value = '';
        selectedPaneLabel.textContent = currentTargetLabel();
        renderConversationList();
        renderWorkerList();
        return;
      }
      session.windows.forEach((window) => {
        windowSelect.appendChild(option(`${window.index}: ${window.name}${window.active ? ' · active' : ''}`, String(window.index)));
      });
      const fallback = session.windows.find((window) => window.active) || session.windows[0];
      windowSelect.value = session.windows.some((window) => String(window.index) === previousWindow) ? previousWindow : String(fallback.index);
      renderPanes();
      renderConversationList();
    }

    function renderPanes() {
      const previousPane = paneSelect.value;
      const window = selectedWindowData();
      paneSelect.innerHTML = '';
      if (!window || !(window.panes || []).length) {
        paneSelect.appendChild(option('No panes', ''));
        aliasInput.value = '';
        selectedPaneLabel.textContent = currentTargetLabel();
        renderWorkerList();
        return;
      }
      window.panes.forEach((pane) => {
        const aliasPrefix = pane.alias ? `${pane.alias} · ` : '';
        const cmd = pane.current_command || 'shell';
        paneSelect.appendChild(option(`${aliasPrefix}${pane.target} · ${cmd}${pane.active ? ' · active' : ''}`, pane.target));
      });
      const fallback = window.panes.find((pane) => pane.active) || window.panes[0];
      paneSelect.value = window.panes.some((pane) => pane.target === previousPane) ? previousPane : fallback.target;
      syncAliasInput();
      renderWorkerList();
    }

    function syncAliasInput() {
      const pane = selectedPaneData();
      aliasInput.value = pane ? (pane.alias || '') : '';
      selectedPaneLabel.textContent = currentTargetLabel();
      renderConversationList();
      renderWorkerList();
      updateCurrentAgentCard();
    }

    function renderTemplates() {
      templateSelect.innerHTML = '';
      if (!templatesCache.length) {
        templateSelect.appendChild(option('No templates yet', ''));
        return;
      }
      templatesCache.forEach((template) => {
        const scope = template.profile ? ` · ${template.profile}` : ' · global';
        templateSelect.appendChild(option(`${template.name}${scope}`, template.id));
      });
    }

    function renderHistory() {
      historySelect.innerHTML = '';
      historyListEl.innerHTML = '';
      if (!historyCache.length) {
        historySelect.appendChild(option('No recent commands', ''));
        historyListEl.innerHTML = '<div class="empty-state">No recent commands for this target yet.</div>';
        historyPaginationEl.innerHTML = '';
        renderChatFeed();
        return;
      }
      historyCache.forEach((entry) => {
        const label = `${entry.profile} · ${entry.alias || entry.target} · ${entry.command.slice(0, 40)}`;
        historySelect.appendChild(option(label, entry.id));
      });
      const page = paginate(historyCache, uiState.historyPage, uiSettings.historyPageSize);
      uiState.historyPage = page.page;
      renderPager(historyPaginationEl, page.page, page.totalPages, async (nextPage) => {
        uiState.historyPage = nextPage;
        await loadHistory();
      });
      page.items.forEach((entry, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'list-item';
        button.innerHTML = `
          <strong>${escapeHtml(entry.alias || entry.target || 'agent')}</strong>
          <span class="hint">${escapeHtml(entry.created_at || '-')}</span>
          <span class="hint">${escapeHtml((entry.command || '').slice(0, 160))}</span>
        `;
        button.addEventListener('click', () => {
          historySelect.value = entry.id;
          applyHistory();
          renderHistory();
        });
        if (historySelect.value === entry.id || (!historySelect.value && index === 0)) {
          historySelect.value = entry.id;
          button.classList.add('active');
        }
        historyListEl.appendChild(button);
      });
      renderChatFeed();
    }

    function renderTodoTemplates() {
      const previous = todoTemplateSelect.value;
      todoTemplateSelect.innerHTML = '';
      if (!todoTemplatesCache.length) {
        todoTemplateSelect.appendChild(option('No todo templates', ''));
        todoTemplateNameInput.value = '';
        return;
      }
      todoTemplatesCache.forEach((template) => {
        const scope = template.target ? ` · ${template.target}` : (template.profile ? ` · ${template.profile}` : ' · global');
        todoTemplateSelect.appendChild(option(`${template.name}${scope}`, template.id));
      });
      todoTemplateSelect.value = todoTemplatesCache.some((item) => item.id === previous) ? previous : todoTemplatesCache[0].id;
      const selected = todoTemplatesCache.find((item) => item.id === todoTemplateSelect.value);
      todoTemplateNameInput.value = selected ? selected.name : '';
    }

    function renderAuditLogs() {
      auditSelect.innerHTML = '';
      if (!auditLogsCache.length) {
        auditSelect.appendChild(option('No audit events', ''));
        syncDeliveryView();
        return;
      }
      auditLogsCache.forEach((entry) => {
        const actor = entry.actor || 'unknown';
        const label = `${entry.created_at} · ${entry.action} · ${actor} · ${entry.note || entry.status || '-'}`;
        auditSelect.appendChild(option(label.slice(0, 140), entry.id));
      });
      syncDeliveryView();
    }

    function todoStatusClass(status) {
      const value = String(status || 'todo').trim().toLowerCase() || 'todo';
      return `status-${value}`;
    }

    function todoProgressPercent(status) {
      const value = String(status || 'todo').trim().toLowerCase();
      if (value === 'verified') return 100;
      if (value === 'done') return 80;
      if (value === 'in_progress') return 45;
      if (value === 'blocked') return 100;
      return 12;
    }

    function nextTodoStatus(status) {
      const value = String(status || 'todo').trim().toLowerCase() || 'todo';
      if (value === 'todo') return 'in_progress';
      if (value === 'in_progress') return 'done';
      if (value === 'done') return 'verified';
      if (value === 'blocked') return 'in_progress';
      return value;
    }

    function todoCheckLabel(status) {
      const value = String(status || 'todo').trim().toLowerCase() || 'todo';
      if (value === 'verified') return '✓';
      if (value === 'done') return '✓';
      if (value === 'in_progress') return '…';
      if (value === 'blocked') return '!';
      return '○';
    }

    function currentTodoTargets() {
      const window = selectedWindowData();
      if (window && (window.panes || []).length) {
        return (window.panes || []).map((pane) => ({
          target: pane.target,
          alias: pane.alias || '',
          command: pane.current_command || 'shell',
          pane,
        }));
      }
      const targets = [];
      const seen = new Set();
      todosCache.forEach((todo) => {
        const target = String(todo.target || '').trim();
        if (!target || seen.has(target)) return;
        seen.add(target);
        targets.push({ target, alias: todo.alias || '', command: '', pane: null });
      });
      return targets;
    }

    function selectTodo(todoId, options = {}) {
      const nextId = String(todoId || '').trim();
      if (!nextId) return;
      todoSelect.value = nextId;
      if (options.openAdvanced) {
        const advanced = document.querySelector('[data-fold-key="todo-advanced"]');
        if (advanced) advanced.open = true;
      }
      renderTodos();
      syncTodoInspector();
    }

    async function quickTodoStatus(todoId) {
      const todo = todosCache.find((item) => item.id === todoId);
      if (!todo) return;
      const nextStatus = nextTodoStatus(todo.status);
      if (nextStatus === todo.status) {
        selectTodo(todo.id, { openAdvanced: true });
        return;
      }
      const needsEvidence = ['done', 'verified'].includes(nextStatus) && !((todo.evidence || []).length);
      const note = (window.prompt(`Update ${todo.title} → ${nextStatus}. Optional note:`, todo.progress_note || '') || '').trim();
      let evidence = null;
      if (needsEvidence) {
        const raw = window.prompt(`Add evidence to move ${todo.title} to ${nextStatus}:`, 'tests passed / pane output / summary') || '';
        evidence = raw.trim();
        if (!evidence) {
          setStatus(`Evidence is required before marking as ${nextStatus}.`, 'warn');
          return;
        }
      }
      try {
        if (needsEvidence || note) {
          await api('/api/todos/report', {
            method: 'POST',
            body: JSON.stringify({
              todo_id: todo.id,
              status: nextStatus,
              progress_note: note,
              evidence: evidence || undefined,
              actor: 'mobile-user',
            }),
          });
        } else {
          await api('/api/todos/status', {
            method: 'POST',
            body: JSON.stringify({
              todo_id: todo.id,
              status: nextStatus,
              progress_note: '',
              actor: 'mobile-user',
            }),
          });
        }
        await loadTodos();
        await loadDashboard();
        selectTodo(todo.id, { openAdvanced: nextStatus === 'blocked' });
        setStatus(`Updated ${todo.title} → ${nextStatus}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function quickTodoNote(todoId) {
      const todo = todosCache.find((item) => item.id === todoId);
      if (!todo) return;
      const note = (window.prompt(`Add a note for ${todo.title}:`, todo.progress_note || '') || '').trim();
      if (!note) return;
      try {
        await api('/api/todos/report', {
          method: 'POST',
          body: JSON.stringify({
            todo_id: todo.id,
            status: todo.status,
            progress_note: note,
            actor: 'mobile-user',
          }),
        });
        await loadTodos();
        await loadDashboard();
        selectTodo(todo.id, { openAdvanced: true });
        setStatus('Task note saved.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function quickTodoUse(todoId) {
      const todo = todosCache.find((item) => item.id === todoId);
      if (!todo) return;
      selectTodo(todo.id, { openAdvanced: true });
      applyTodoToCommand();
      setActiveView('chat');
    }

    function renderTodos() {
      const previous = todoSelect.value;
      todoSelect.innerHTML = '';
      todoBoardEl.innerHTML = '';
      todoPaginationEl.innerHTML = '';

      todosCache.forEach((todo) => {
        const shortTitle = todo.title.length > 42 ? `${todo.title.slice(0, 42)}...` : todo.title;
        const label = `[${todo.status}] [${todo.priority}] ${shortTitle}`;
        todoSelect.appendChild(option(label, todo.id));
      });

      const targets = currentTodoTargets();
      const preferredTarget = paneSelect.value.trim();
      const preferredTodo = todosCache.find((todo) => todo.target === preferredTarget) || todosCache[0] || null;
      todoSelect.value = todosCache.some((todo) => todo.id === previous) ? previous : (preferredTodo ? preferredTodo.id : '');

      if (!targets.length) {
        todoSelect.innerHTML = '';
        todoSelect.appendChild(option('No tasks', ''));
        todoStatusSelect.value = 'todo';
        todoProgressNoteInput.value = '';
        todoMetaEl.textContent = 'No tasks yet.';
        todoBoardEl.innerHTML = '<div class="empty-state">Select a conversation with agents to see task bars.</div>';
        return;
      }

      const grouped = new Map();
      targets.forEach((item) => grouped.set(item.target, []));
      todosCache.forEach((todo) => {
        if (!grouped.has(todo.target)) return;
        grouped.get(todo.target).push(todo);
      });

      targets.forEach((item) => {
        const lane = document.createElement('section');
        lane.className = 'todo-lane';
        const laneTodos = (grouped.get(item.target) || []).slice().sort((left, right) => String(right.updated_at || '').localeCompare(String(left.updated_at || '')));
        lane.innerHTML = `
          <div class="todo-lane-head">
            <div class="worker-avatar">${escapeHtml(workerInitials(item.pane || { alias: item.alias, target: item.target }))}<span class="worker-dot ${item.pane && item.pane.active ? 'live' : ''}"></span></div>
            <div class="todo-lane-copy">
              <div class="todo-lane-title">${escapeHtml(workerDisplayName(item.pane || { alias: item.alias, target: item.target }))}</div>
              <div class="todo-lane-meta">${escapeHtml(item.command || item.target)}</div>
            </div>
            <div class="todo-count">${laneTodos.length} task${laneTodos.length === 1 ? '' : 's'}</div>
          </div>
          <div class="todo-lane-body"></div>
        `;
        const body = lane.querySelector('.todo-lane-body');
        if (!laneTodos.length) {
          body.innerHTML = '<div class="empty-state">No tasks for this agent.</div>';
        } else {
          laneTodos.forEach((todo) => {
            const card = document.createElement('article');
            card.className = `todo-bar ${todo.id === todoSelect.value ? 'active' : ''}`;
            const detail = String(todo.detail || '').trim();
            const trimmedDetail = detail.length > 120 ? `${detail.slice(0, 120)}...` : detail;
            const progress = todoProgressPercent(todo.status);
            card.innerHTML = `
              <div class="todo-bar-head">
                <button type="button" class="todo-check ${todoStatusClass(todo.status)}" title="Advance status">${todoCheckLabel(todo.status)}</button>
                <div class="todo-bar-copy">
                  <div class="todo-bar-title">${escapeHtml(todo.title || '')}</div>
                  <div class="todo-bar-detail">${escapeHtml(trimmedDetail || 'No detail')}</div>
                </div>
                <div class="todo-badges">
                  <span class="todo-badge ${todoStatusClass(todo.status)}">${escapeHtml(todo.status || 'todo')}</span>
                  <span class="todo-badge">${escapeHtml(todo.priority || 'medium')}</span>
                </div>
              </div>
              <div class="todo-bar-progress"><span style="width:${progress}%"></span></div>
              <div class="todo-bar-actions">
                <button type="button" class="todo-mini todo-note">Note</button>
                <button type="button" class="todo-mini todo-use">Use</button>
              </div>
            `;
            card.querySelector('.todo-bar-copy').addEventListener('click', () => selectTodo(todo.id, { openAdvanced: true }));
            card.querySelector('.todo-check').addEventListener('click', (event) => {
              event.stopPropagation();
              quickTodoStatus(todo.id);
            });
            card.querySelector('.todo-note').addEventListener('click', (event) => {
              event.stopPropagation();
              quickTodoNote(todo.id);
            });
            card.querySelector('.todo-use').addEventListener('click', (event) => {
              event.stopPropagation();
              quickTodoUse(todo.id);
            });
            body.appendChild(card);
          });
        }
        todoBoardEl.appendChild(lane);
      });

      const totalCount = todosCache.length;
      const selectedLabel = selectedTodo() ? `Selected: ${selectedTodo().title}` : 'Select a task to inspect details.';
      todoMetaEl.textContent = `${totalCount} task${totalCount === 1 ? '' : 's'} in this profile. ${selectedLabel}`;
      syncTodoInspector();
    }

    function syncTodoInspector() {
      const todo = selectedTodo();
      if (!todo) {
        todoStatusSelect.value = 'todo';
        todoProgressNoteInput.value = '';
        todoMetaEl.textContent = todosCache.length ? 'Select a task to inspect details.' : 'No tasks yet.';
        todoTimelineEl.textContent = 'No todo selected.';
        todoEvidenceListEl.textContent = 'No evidence yet.';
        syncDeliveryView();
        return;
      }
      todoStatusSelect.value = todo.status || 'todo';
      todoProgressNoteInput.value = todo.progress_note || '';
      const evidenceCount = (todo.evidence || []).length;
      const alias = todo.alias || '(no alias)';
      todoMetaEl.textContent = `${todo.profile} -> ${todo.target} (${alias}) · ${todo.status} · evidence ${evidenceCount} · updated ${todo.updated_at || '-'}`;
      const timelineLines = (todo.events || []).map((event) => {
        const ts = event.created_at || '-';
        const actor = event.actor || 'unknown';
        const status = event.status ? ` [${event.status}]` : '';
        const note = event.note || '';
        return `${ts} · ${actor}${status} · ${note}`;
      });
      todoTimelineEl.textContent = timelineLines.length ? timelineLines.join('\\n') : 'No timeline events.';
      const evidenceLines = (todo.evidence || []).map((entry) => {
        const ts = entry.created_at || '-';
        const source = entry.source ? ` · ${entry.source}` : '';
        return `${ts} · ${entry.type}${source}\n${entry.content}`;
      });
      todoEvidenceListEl.textContent = evidenceLines.length ? evidenceLines.join('\\n\\n') : 'No evidence yet.';
      syncDeliveryView();
    }

    async function loadProfiles() {
      const data = await api('/api/profiles');
      profilesCache = data.profiles || [];
      renderProfileSelect();
    }

    async function loadDashboard() {
      const data = await api('/api/dashboard');
      dashboardCache = data;
      renderTargetCards();
      updateKpis();
    }

    async function loadTemplates() {
      const profile = currentProfileName();
      const data = await api(`/api/templates?profile=${encodeURIComponent(profile)}`);
      templatesCache = data.templates || [];
      renderTemplates();
    }

    async function loadHistory() {
      const profile = currentProfileName();
      const limit = Math.max(uiSettings.historyPageSize * Math.max(uiState.historyPage, 1), uiSettings.historyPageSize);
      const data = await api(`/api/history?profile=${encodeURIComponent(profile)}&limit=${limit}`);
      historyCache = data.history || [];
      renderHistory();
    }

    async function loadTodoTemplates() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      const data = await api(`/api/todo-templates?profile=${encodeURIComponent(profile)}&target=${encodeURIComponent(target)}`);
      todoTemplatesCache = data.templates || [];
      renderTodoTemplates();
    }

    async function loadAuditLogs() {
      const selected = requireCurrentAgent('loading audit logs', true);
      if (!selected) {
        auditLogsCache = [];
        renderAuditLogs();
        return;
      }
      const data = await api(`/api/audit?profile=${encodeURIComponent(selected.profile)}&target=${encodeURIComponent(selected.target)}&limit=25`);
      auditLogsCache = data.logs || [];
      renderAuditLogs();
    }

    async function loadTodos() {
      const requestVersion = ++todoLoadVersion;
      const profile = currentProfileName();
      const selectedTarget = paneSelect.value.trim();
      if (!profile) {
        if (requestVersion !== todoLoadVersion) return;
        todosCache = [];
        renderTodos();
        await loadAuditLogs();
        updateCurrentAgentCard();
        closeTodoStream();
        return;
      }
      const data = await api(`/api/todos?profile=${encodeURIComponent(profile)}`);
      if (requestVersion !== todoLoadVersion || currentProfileName() !== profile) {
        return;
      }
      todosCache = data.todos || [];
      renderTodos();
      await Promise.all([loadTodoTemplates(), loadAuditLogs()]);
      if (requestVersion !== todoLoadVersion || currentProfileName() !== profile) {
        return;
      }
      if (selectedTarget) {
        openTodoStream();
      } else {
        closeTodoStream();
      }
      updateCurrentAgentCard();
    }

    async function loadRemoteState() {
      const requestVersion = ++remoteStateLoadVersion;
      const profile = currentProfileName();
      if (!profile) {
        if (requestVersion !== remoteStateLoadVersion) return;
        stateCache = { sessions: [] };
        renderSessions();
        latestPaneOutput = 'Choose a target first.';
        paneOutputEl.textContent = latestPaneOutput;
        todosCache = [];
        renderTodos();
        updateCurrentAgentCard();
        renderChatFeed();
        return;
      }
      const currentSession = sessionSelect.value;
      const currentWindow = windowSelect.value;
      const currentPane = paneSelect.value;
      const data = await api(`/api/remote/state?profile=${encodeURIComponent(profile)}`);
      if (requestVersion !== remoteStateLoadVersion || currentProfileName() !== profile) {
        return;
      }
      stateCache = data;
      renderSessions();
      if (currentSession) {
        const session = (stateCache.sessions || []).find((item) => item.name === currentSession);
        if (session) {
          sessionSelect.value = currentSession;
          renderWindows();
        }
      }
      if (currentWindow) {
        const window = selectedSessionData() ? (selectedSessionData().windows || []).find((item) => String(item.index) === currentWindow) : null;
        if (window) {
          windowSelect.value = currentWindow;
          renderPanes();
        }
      }
      if (currentPane) {
        const pane = selectedWindowData() ? (selectedWindowData().panes || []).find((item) => item.target === currentPane) : null;
        if (pane) {
          paneSelect.value = currentPane;
          syncAliasInput();
        }
      }
      await loadPane();
      await loadTodos();
      if (requestVersion !== remoteStateLoadVersion || currentProfileName() !== profile) {
        return;
      }
      updateCurrentAgentCard();
    }

    async function loadPane() {
      const requestVersion = ++paneLoadVersion;
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      selectedPaneLabel.textContent = currentTargetLabel();
      if (!profile || !target) {
        if (requestVersion !== paneLoadVersion) return;
        latestPaneOutput = 'Choose a target and pane first.';
        paneOutputEl.textContent = latestPaneOutput;
        renderChatFeed();
        syncDeliveryView();
        return;
      }
      const data = await api(`/api/pane?profile=${encodeURIComponent(profile)}&target=${encodeURIComponent(target)}&lines=${uiSettings.paneLines}`);
      if (requestVersion !== paneLoadVersion || currentProfileName() !== profile || paneSelect.value.trim() !== target) {
        return;
      }
      latestPaneOutput = data.output || '[empty pane]';
      paneOutputEl.textContent = latestPaneOutput;
      renderChatFeed();
      syncDeliveryView();
    }

    async function loadSelectedProfile() {
      uiState.historyPage = 1;
      uiState.todoPage = 1;
      fillProfileForm(currentProfile());
      await Promise.all([loadTemplates(), loadHistory()]);
      try {
        await loadRemoteState();
      } catch (error) {
        stateCache = { sessions: [] };
        renderSessions();
        latestPaneOutput = error.message;
        paneOutputEl.textContent = latestPaneOutput;
        todosCache = [];
        renderTodos();
        closeTodoStream();
        updateCurrentAgentCard();
        renderChatFeed();
        setStatus(error.message, 'error');
      }
      renderTargetCards();
    }

    async function refreshAll() {
      try {
        await Promise.all([loadProfiles(), loadDashboard()]);
        await loadSelectedProfile();
        setStatus('Dashboard refreshed.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveProfile() {
      const profile = readProfileForm();
      if (!profile.name || !profile.host || !profile.username) {
        setStatus('Name, host and username are required.', 'error');
        return;
      }
      try {
        await api('/api/profiles/save', { method: 'POST', body: JSON.stringify(profile) });
        await Promise.all([loadProfiles(), loadDashboard()]);
        profileSelect.value = profile.name;
        await loadSelectedProfile();
        setStatus(`Saved target ${profile.name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function testProfile() {
      const profile = readProfileForm();
      if (!profile.name || !profile.host || !profile.username) {
        setStatus('Fill name, host and username first.', 'error');
        return;
      }
      try {
        const data = await api('/api/profiles/test', { method: 'POST', body: JSON.stringify(profile) });
        if (data.ok) {
          setStatus(`SSH ok · ${data.session_count} session(s), ${data.pane_count} pane(s).`);
        } else {
          setStatus(data.error || 'SSH test failed.', 'error');
        }
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteProfile() {
      const name = currentProfileName() || profileNameInput.value.trim();
      if (!name) {
        setStatus('Choose a target to delete.', 'error');
        return;
      }
      try {
        await api('/api/profiles/delete', { method: 'POST', body: JSON.stringify({ name }) });
        await Promise.all([loadProfiles(), loadDashboard()]);
        await loadSelectedProfile();
        setStatus(`Deleted target ${name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveAlias() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      if (!profile || !target) {
        setStatus('Choose a pane first.', 'error');
        return;
      }
      try {
        await api('/api/alias/save', { method: 'POST', body: JSON.stringify({ profile, target, alias: aliasInput.value.trim() }) });
        await Promise.all([loadDashboard(), loadRemoteState()]);
        setStatus(`Saved alias for ${target}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function saveTemplate() {
      const name = templateNameInput.value.trim();
      const command = commandInput.value.trim();
      if (!name || !command) {
        setStatus('Template name and command are required.', 'error');
        return;
      }
      const profile = templateScopeSelect.value === 'current' ? currentProfileName() : '';
      try {
        await api('/api/templates/save', { method: 'POST', body: JSON.stringify({ id: templateSelect.value, name, command, profile, target: paneSelect.value.trim() }) });
        await loadTemplates();
        setStatus(`Saved template ${name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteTemplate() {
      const id = templateSelect.value.trim();
      if (!id) {
        setStatus('Choose a template first.', 'error');
        return;
      }
      try {
        await api('/api/templates/delete', { method: 'POST', body: JSON.stringify({ id }) });
        templateNameInput.value = '';
        await loadTemplates();
        setStatus('Template deleted.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function applyTemplate() {
      const template = templatesCache.find((item) => item.id === templateSelect.value);
      if (!template) {
        setStatus('Choose a template first.', 'error');
        return;
      }
      templateNameInput.value = template.name || '';
      commandInput.value = template.command || '';
      templateScopeSelect.value = template.profile ? 'current' : '';
      setStatus(`Applied template ${template.name}.`);
    }

    function applyHistory() {
      const entry = historyCache.find((item) => item.id === historySelect.value);
      if (!entry) {
        setStatus('Choose a history item first.', 'error');
        return;
      }
      commandInput.value = entry.command || '';
      setStatus('Applied recent command.');
    }

    async function clearHistory() {
      try {
        await api('/api/history/clear', { method: 'POST', body: JSON.stringify({ profile: currentProfileName() }) });
        await loadHistory();
        setStatus('History cleared for current target.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function createTodo() {
      const selected = requireCurrentAgent('sending a requirement');
      if (!selected) return;
      const detail = todoDetailInput.value.trim();
      if (!detail) {
        setStatus('Please describe the requirement first.', 'error');
        return;
      }
      const title = todoTitleInput.value.trim() || detail.split(/\\n+/)[0].trim().slice(0, 140) || 'New requirement';
      const pane = selectedPaneData();
      try {
        const response = await api('/api/todos', {
          method: 'POST',
          body: JSON.stringify({
            title,
            detail,
            profile: selected.profile,
            target: selected.target,
            alias: (pane && pane.alias) || '',
            status: 'todo',
            priority: todoPrioritySelect.value,
            assignee: todoAssigneeInput.value.trim(),
          }),
        });
        todoTitleInput.value = title;
        todoDetailInput.value = '';
        await loadTodos();
        todoSelect.value = response.todo.id;
        syncTodoInspector();
        await loadDashboard();
        setStatus(`Requirement sent to ${selected.target}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function quickTodo() {
      const selected = requireCurrentAgent('creating quick task');
      if (!selected) return;
      const pane = selectedPaneData();
      const fallbackTitle = commandInput.value.trim().split('\\n')[0] || `Quick task for ${selected.target}`;
      const title = (todoTitleInput.value.trim() || fallbackTitle).slice(0, 140);
      try {
        await api('/api/todos/quick', {
          method: 'POST',
          body: JSON.stringify({
            title,
            detail: todoDetailInput.value.trim(),
            profile: selected.profile,
            target: selected.target,
            alias: (pane && pane.alias) || '',
            priority: todoPrioritySelect.value,
            assignee: todoAssigneeInput.value.trim(),
          }),
        });
        await loadTodos();
        await loadDashboard();
        setStatus(`Quick task created for ${selected.target}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function createTripletWorkflow() {
      const selected = requireCurrentAgent('creating triplet workflow');
      if (!selected) return;
      const title = todoTitleInput.value.trim();
      if (!title) {
        setStatus('Todo title is required for triplet workflow.', 'error');
        return;
      }
      const detail = todoDetailInput.value.trim();
      const handoffPacket = {
        context: detail || title,
        constraints: 'Keep changes minimal, do not break existing behavior.',
        acceptance: 'All relevant tests pass and summary is provided.',
        rollback: 'If blocked, stop and provide rollback-safe patch plan.',
      };
      try {
        const response = await api('/api/workflows/triplet', {
          method: 'POST',
          body: JSON.stringify({
            title,
            detail,
            profile: selected.profile,
            target: selected.target,
            planner_target: selected.target,
            executor_target: selected.target,
            reviewer_target: selected.target,
            priority: todoPrioritySelect.value,
            handoff_packet: handoffPacket,
          }),
        });
        await loadTodos();
        await loadDashboard();
        setStatus(`Triplet workflow created: ${response.workflow_id}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function updateTodoStatus() {
      const todo = selectedTodo();
      if (!todo) {
        setStatus('Choose a todo first.', 'error');
        return;
      }
      try {
        await api('/api/todos/status', {
          method: 'POST',
          body: JSON.stringify({
            todo_id: todo.id,
            status: todoStatusSelect.value,
            progress_note: todoProgressNoteInput.value.trim(),
            actor: 'mobile-user',
          }),
        });
        await loadTodos();
        await loadDashboard();
        setStatus(`Updated todo status to ${todoStatusSelect.value}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function addTodoEvidence() {
      const todo = selectedTodo();
      if (!todo) {
        setStatus('Choose a todo first.', 'error');
        return;
      }
      const evidence = parseEvidenceInput(todoEvidenceInput.value);
      if (!evidence) {
        setStatus('Evidence text or JSON is required.', 'error');
        return;
      }
      try {
        await api('/api/todos/evidence', {
          method: 'POST',
          body: JSON.stringify({
            todo_id: todo.id,
            evidence,
            actor: 'mobile-user',
          }),
        });
        todoEvidenceInput.value = '';
        await loadTodos();
        await loadDashboard();
        setStatus('Todo evidence added.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function reportTodo() {
      const todo = selectedTodo();
      if (!todo) {
        setStatus('Choose a todo first.', 'error');
        return;
      }
      const evidence = parseEvidenceInput(todoEvidenceInput.value);
      try {
        await api('/api/todos/report', {
          method: 'POST',
          body: JSON.stringify({
            todo_id: todo.id,
            status: todoStatusSelect.value,
            progress_note: todoProgressNoteInput.value.trim(),
            evidence: evidence || undefined,
            actor: 'agent',
          }),
        });
        todoEvidenceInput.value = '';
        await loadTodos();
        await loadDashboard();
        setStatus('Agent report applied to todo.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function applyTodoTemplate() {
      const template = todoTemplatesCache.find((item) => item.id === todoTemplateSelect.value);
      if (!template) {
        setStatus('Choose a todo template first.', 'error');
        return;
      }
      todoTemplateNameInput.value = template.name || '';
      todoTitleInput.value = template.title || '';
      todoDetailInput.value = template.detail || '';
      todoPrioritySelect.value = template.priority || 'medium';
      todoAssigneeInput.value = template.assignee || '';
      setStatus(`Applied todo template ${template.name}.`);
    }

    async function saveTodoTemplate() {
      const selected = requireCurrentAgent('saving todo template');
      if (!selected) return;
      const name = todoTemplateNameInput.value.trim();
      const title = todoTitleInput.value.trim();
      if (!name || !title) {
        setStatus('Template name and todo title are required.', 'error');
        return;
      }
      try {
        await api('/api/todo-templates/save', {
          method: 'POST',
          body: JSON.stringify({
            id: todoTemplateSelect.value,
            name,
            title,
            detail: todoDetailInput.value.trim(),
            priority: todoPrioritySelect.value,
            assignee: todoAssigneeInput.value.trim(),
            profile: selected.profile,
            target: selected.target,
          }),
        });
        await loadTodoTemplates();
        await loadAuditLogs();
        setStatus(`Saved todo template ${name}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    async function deleteTodoTemplate() {
      const id = todoTemplateSelect.value.trim();
      if (!id) {
        setStatus('Choose a todo template first.', 'error');
        return;
      }
      try {
        await api('/api/todo-templates/delete', { method: 'POST', body: JSON.stringify({ id }) });
        await loadTodoTemplates();
        await loadAuditLogs();
        setStatus('Todo template deleted.');
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function applyTodoToCommand() {
      const todo = selectedTodo();
      if (!todo) {
        setStatus('Choose a todo first.', 'error');
        return;
      }
      const detail = todo.detail ? `\\n\\nDetails:\\n${todo.detail}` : '';
      commandInput.value = `TODO ${todo.id}: ${todo.title}${detail}`;
      setStatus('Todo content copied into command box.');
    }

    async function sendCommand() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      const command = commandInput.value.trim();
      if (!profile || !target) {
        setStatus('Choose a target and pane first.', 'error');
        return;
      }
      if (!command) {
        setStatus('Enter a command first.', 'error');
        return;
      }
      try {
        await api('/api/send', {
          method: 'POST',
          body: JSON.stringify({ profile, target, command, press_enter: true, expected_target: target }),
        });
        commandInput.value = '';
        await Promise.all([loadHistory(), loadPane()]);
        setStatus(`Sent command to ${target}.`);
      } catch (error) {
        if (String(error.message || '').includes('confirm_risk=true')) {
          const ok = window.confirm('This command looks dangerous. Send anyway?');
          if (ok) {
            try {
              await api('/api/send', {
                method: 'POST',
                body: JSON.stringify({ profile, target, command, press_enter: true, expected_target: target, confirm_risk: true }),
              });
              commandInput.value = '';
              await Promise.all([loadHistory(), loadPane()]);
              setStatus(`Sent command to ${target} with risk confirmation.`, 'warn');
              return;
            } catch (retryError) {
              setStatus(retryError.message, 'error');
              return;
            }
          }
          setStatus('Cancelled risky command.', 'warn');
          return;
        }
        setStatus(error.message, 'error');
      }
    }

    async function interrupt() {
      const profile = currentProfileName();
      const target = paneSelect.value.trim();
      if (!profile || !target) {
        setStatus('Choose a target and pane first.', 'error');
        return;
      }
      try {
        await api('/api/interrupt', { method: 'POST', body: JSON.stringify({ profile, target }) });
        await loadPane();
        setStatus(`Sent Ctrl+C to ${target}.`);
      } catch (error) {
        setStatus(error.message, 'error');
      }
    }

    function appendNewline() {
      const value = commandInput.value;
      commandInput.value = value.endsWith('\\n') ? value : `${value}\\n`;
      commandInput.focus();
    }

    async function copyTargetLabel() {
      try {
        await navigator.clipboard.writeText(currentTargetLabel());
        setStatus('Copied selected target label.');
      } catch (error) {
        setStatus('Clipboard is unavailable in this browser.', 'warn');
      }
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = navigator.language || 'en-US';
      recognition.onresult = (event) => {
        let transcript = '';
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          transcript += event.results[index][0].transcript;
        }
        commandInput.value = transcript.trim();
        setStatus('Listening… local speech-to-text is updating the command box.');
      };
      recognition.onerror = (event) => {
        setStatus(`Voice input error: ${event.error}`, 'error');
      };
    } else {
      setStatus('Voice input is unavailable in this browser. Use Chrome-based browsers or type commands manually.', 'warn');
    }

    document.getElementById('refreshDashboard').addEventListener('click', refreshAll);
    document.getElementById('refreshState').addEventListener('click', loadSelectedProfile);
    document.getElementById('saveUiSettings').addEventListener('click', saveUiSettings);
    document.getElementById('resetUiSettings').addEventListener('click', resetUiSettings);
    document.getElementById('saveProfile').addEventListener('click', saveProfile);
    document.getElementById('testProfile').addEventListener('click', testProfile);
    document.getElementById('loadProfileState').addEventListener('click', loadSelectedProfile);
    document.getElementById('deleteProfile').addEventListener('click', deleteProfile);
    document.getElementById('saveAlias').addEventListener('click', saveAlias);
    document.getElementById('saveTemplate').addEventListener('click', saveTemplate);
    document.getElementById('deleteTemplate').addEventListener('click', deleteTemplate);
    document.getElementById('applyTemplate').addEventListener('click', applyTemplate);
    document.getElementById('applyHistory').addEventListener('click', applyHistory);
    document.getElementById('clearHistory').addEventListener('click', clearHistory);
    document.getElementById('createTodo').addEventListener('click', createTodo);
    document.getElementById('quickTodo').addEventListener('click', quickTodo);
    document.getElementById('createTriplet').addEventListener('click', createTripletWorkflow);
    document.getElementById('refreshTodos').addEventListener('click', loadTodos);
    document.getElementById('applyTodoToCommand').addEventListener('click', applyTodoToCommand);
    document.getElementById('updateTodoStatus').addEventListener('click', updateTodoStatus);
    document.getElementById('addTodoEvidence').addEventListener('click', addTodoEvidence);
    document.getElementById('reportTodo').addEventListener('click', reportTodo);
    document.getElementById('applyTodoTemplate').addEventListener('click', applyTodoTemplate);
    document.getElementById('saveTodoTemplate').addEventListener('click', saveTodoTemplate);
    document.getElementById('deleteTodoTemplate').addEventListener('click', deleteTodoTemplate);
    document.getElementById('sendCommand').addEventListener('click', sendCommand);
    document.getElementById('interrupt').addEventListener('click', interrupt);
    document.getElementById('appendNewline').addEventListener('click', appendNewline);
    document.getElementById('copyTargetLabel').addEventListener('click', copyTargetLabel);
    document.getElementById('refreshPane').addEventListener('click', loadPane);
    document.getElementById('refreshChatPane').addEventListener('click', loadPane);
    document.getElementById('startVoice').addEventListener('click', () => {
      if (!recognition) {
        setStatus('Voice input is unavailable in this browser.', 'error');
        return;
      }
      recognition.start();
      setStatus('Voice capture started.');
    });
    document.getElementById('stopVoice').addEventListener('click', () => {
      if (!recognition) return;
      recognition.stop();
      setStatus('Voice capture stopped.');
    });

    tokenInput.addEventListener('change', refreshAll);
    profileSelect.addEventListener('change', loadSelectedProfile);
    viewButtons.forEach((button) => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        setActiveView(button.dataset.viewButton || 'chat');
      });
    });
    chatSessionSelect.addEventListener('change', () => {
      sessionSelect.value = chatSessionSelect.value;
      uiState.historyPage = 1;
      uiState.todoPage = 1;
      renderWindows();
      loadPane();
      loadTodos();
    });
    sessionSelect.addEventListener('change', () => { uiState.historyPage = 1; uiState.todoPage = 1; renderWindows(); loadPane(); loadTodos(); });
    windowSelect.addEventListener('change', () => { uiState.historyPage = 1; uiState.todoPage = 1; renderPanes(); loadPane(); loadTodos(); });
    paneSelect.addEventListener('change', () => { uiState.historyPage = 1; uiState.todoPage = 1; syncAliasInput(); loadPane(); loadTodos(); });
    templateSelect.addEventListener('change', () => {
      const template = templatesCache.find((item) => item.id === templateSelect.value);
      templateNameInput.value = template ? template.name : '';
      templateScopeSelect.value = template && template.profile ? 'current' : '';
    });
    todoSelect.addEventListener('change', syncTodoInspector);
    todoTemplateSelect.addEventListener('change', () => {
      const template = todoTemplatesCache.find((item) => item.id === todoTemplateSelect.value);
      todoTemplateNameInput.value = template ? template.name : '';
    });

    initializeFoldPanels();
    syncUiSettingsInputs();
    setActiveView(uiState.currentView);
    refreshAll();
    setInterval(() => {
      if (currentProfileName()) {
        loadPane().catch(() => {});
      }
    }, 5000);
    setInterval(() => {
      // SSE handles near-real-time todo updates; this is a fallback refresh.
      if (currentProfileName() && paneSelect.value.trim()) {
        loadTodos().catch(() => {});
      }
    }, 45000);
    setInterval(() => {
      loadDashboard().catch(() => {});
    }, 20000);
  </script>
</body>
</html>
"""

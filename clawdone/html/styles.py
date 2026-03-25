"""Embedded CSS for the mobile UI."""

INDEX_CSS = """
    :root {
      color-scheme: dark;
      --background: #09090b;
      --foreground: #fafafa;
      --card: #18181b;
      --card-foreground: #fafafa;
      --muted: #27272a;
      --muted-foreground: #a1a1aa;
      --popover: #18181b;
      --border: #3f3f46;
      --input: #27272a;
      --ring: #3b82f6;
      --primary: #3b82f6;
      --primary-foreground: #eff6ff;
      --secondary: #27272a;
      --secondary-foreground: #fafafa;
      --destructive: #ef4444;
      --destructive-foreground: #fef2f2;
      --success: #22c55e;
      --warning: #f59e0b;
      --radius: 0.5rem;
      --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.3);
    }
    * { box-sizing: border-box; }
    html, body { min-height: 100%; }
    body {
      margin: 0;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--background);
      color: var(--foreground);
      line-height: 1.5;
      font-size: 14px;
    }
    .wrap {
      width: min(1120px, 100%);
      margin: 0 auto;
      padding: 20px 16px 80px;
    }
    .view-switcher {
      position: sticky;
      top: 10px;
      z-index: 20;
      margin: 0 0 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 6px;
      border: 1px solid rgba(63,63,70,0.9);
      border-radius: 999px;
      background: rgba(9,9,11,0.86);
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 28px rgba(0,0,0,0.22);
    }
    .view-chip {
      width: auto;
      min-height: 32px;
      padding: 6px 12px;
      border: 1px solid transparent;
      border-radius: 999px;
      background: transparent;
      color: var(--muted-foreground);
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.01em;
    }
    .view-chip:hover {
      opacity: 1;
      background: rgba(255,255,255,0.04);
      color: var(--foreground);
    }
    .view-chip.active {
      background: linear-gradient(135deg, rgba(59,130,246,0.26), rgba(29,78,216,0.42));
      border-color: rgba(96,165,250,0.5);
      color: #eff6ff;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
    }
    h1, h2, h3, p { margin: 0; }
    .hero {
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .brand-mark {
      width: 36px;
      height: 36px;
      display: grid;
      place-items: center;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--card);
      flex: 0 0 auto;
    }
    .brand-logo {
      width: 22px;
      height: 22px;
      object-fit: contain;
    }
    .brand-copy { display: grid; gap: 1px; }
    .brand-kicker {
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--primary);
      font-weight: 600;
    }
    .hero h1 {
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-subline { display: none; }
    .sub {
      color: var(--muted-foreground);
      max-width: 90ch;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--muted);
      color: var(--muted-foreground);
      font-size: 0.78rem;
      font-weight: 500;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: calc(var(--radius) + 2px);
      padding: 16px;
      margin-bottom: 12px;
    }
    .grid { display: grid; gap: 12px; }
    .grid-2 { display: grid; gap: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .grid-3 { display: grid; gap: 10px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .grid-4 { display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .main-grid { display: grid; gap: 12px; grid-template-columns: 1.15fr 1fr; }
    label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted-foreground);
      font-size: 0.8rem;
      font-weight: 500;
    }
    input, select, textarea {
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 7px 10px;
      background: var(--input);
      color: var(--foreground);
      font: inherit;
      font-size: 0.875rem;
      transition: border-color 100ms, box-shadow 100ms;
    }
    input::placeholder, textarea::placeholder { color: #52525b; }
    input:focus, select:focus, textarea:focus, button:focus-visible {
      outline: none;
      border-color: var(--ring);
      box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
    }
    textarea {
      min-height: 100px;
      resize: vertical;
    }
    button {
      width: 100%;
      min-height: 36px;
      border: 1px solid transparent;
      border-radius: var(--radius);
      padding: 7px 12px;
      background: var(--secondary);
      color: var(--secondary-foreground);
      font: inherit;
      font-size: 0.875rem;
      font-weight: 500;
      cursor: pointer;
      transition: opacity 100ms, background-color 100ms;
    }
    button:hover { opacity: 0.85; }
    button:active { opacity: 0.7; }
    button:disabled { opacity: 0.4; cursor: not-allowed; }
    .primary { background: var(--primary); color: var(--primary-foreground); }
    .secondary { background: var(--secondary); border-color: var(--border); color: var(--secondary-foreground); }
    .danger { background: var(--destructive); color: var(--destructive-foreground); }
    .ghost { background: transparent; border-color: var(--border); color: var(--foreground); }
    .muted { color: var(--muted-foreground); }
    .status {
      min-height: 34px;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      background: var(--muted);
      color: #86efac;
      font-size: 0.85rem;
      padding: 7px 10px;
      margin-top: 2px;
    }
    .status.error { color: #fca5a5; border-color: rgba(239,68,68,0.4); background: rgba(127,29,29,0.3); }
    .status.warn { color: #fde68a; border-color: rgba(245,158,11,0.4); background: rgba(120,53,15,0.25); }
    .hint { color: var(--muted-foreground); font-size: 0.8rem; line-height: 1.5; }
    .kpi {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: var(--muted);
    }
    .kpi strong { display: block; font-size: 1.25rem; margin-bottom: 2px; font-weight: 700; }
    .kpi span { font-size: 0.75rem; color: var(--muted-foreground); text-transform: uppercase; letter-spacing: 0.05em; }
    .list { display: grid; gap: 6px; max-height: 320px; overflow: auto; }
    .target-card {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: var(--card);
      color: var(--foreground);
      text-align: left;
      transition: border-color 100ms, background-color 100ms;
    }
    .target-card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
    .target-card-name { display: grid; gap: 2px; min-width: 0; }
    .target-card-name strong { font-size: 0.9rem; }
    .target-card-host { color: var(--muted-foreground); font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .target-card-foot { margin-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; color: var(--muted-foreground); font-size: 0.75rem; }
    .target-card:hover { border-color: #52525b; background: #1c1c1f; }
    .target-card.active { border-color: var(--ring); background: rgba(59,130,246,0.08); }
    .badge-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 7px;
      border-radius: 999px;
      background: var(--muted);
      border: 1px solid var(--border);
      color: var(--muted-foreground);
      font-size: 0.72rem;
    }
    .badge.ok { color: #bbf7d0; border-color: rgba(34,197,94,0.4); background: rgba(20,83,45,0.35); }
    .badge.bad { color: #fecdd3; border-color: rgba(239,68,68,0.4); background: rgba(127,29,29,0.35); }
    .section-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; }
    .section-title h2 { font-size: 0.95rem; font-weight: 600; letter-spacing: -0.01em; }
    .row-inline { display: flex; gap: 6px; align-items: center; }
    .row-inline > button { flex: 1; }
    .checkbox {
      display: flex; align-items: center; gap: 8px;
      padding: 7px 10px; border: 1px solid var(--border);
      border-radius: var(--radius); background: var(--input);
    }
    .checkbox input { width: 14px; height: 14px; margin: 0; accent-color: var(--primary); }
    pre {
      margin: 0; padding: 12px;
      background: #000;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      color: #d4d4d8;
      overflow: auto; white-space: pre-wrap; word-break: break-word;
      min-height: 200px; font-size: 0.8rem; line-height: 1.6;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
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
      background: var(--muted);
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
      background: rgba(9,9,11,0.92);
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
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--card);
      padding: 10px 12px;
    }
    details.fold.fold-panel {
      border-style: solid;
      background: var(--card);
      padding: 12px 14px;
    }
    details.fold > summary {
      cursor: pointer; font-weight: 600; color: var(--foreground);
      list-style: none; user-select: none; font-size: 0.875rem;
    }
    details.fold > summary::-webkit-details-marker { display: none; }
    details.fold > summary::after {
      content: "Show"; float: right; color: var(--muted-foreground);
      font-size: 0.75rem; font-weight: 500;
    }
    details.fold[open] > summary::after { content: "Hide"; }
    .fold-body { margin-top: 10px; display: grid; gap: 10px; }
    .fold-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-right: 20px; }
    .fold-head strong { font-size: 0.9rem; font-weight: 600; }
    .fold-head span { color: var(--muted-foreground); font-size: 0.75rem; }
    .settings-grid { display: grid; gap: 12px; }
    .settings-card { display: grid; gap: 12px; padding: 2px 0 0; }
    .settings-page { gap: 12px; }
    .settings-page > .section-title { margin-bottom: 2px; }
    .settings-shell { gap: 10px; }
    .settings-shell .fold-panel { border-radius: var(--radius); padding: 10px 12px; }
    .settings-shell .fold-body { margin-top: 12px; gap: 12px; }
    .settings-shell .fold-head { margin-right: 18px; }
    .settings-shell .fold-head strong { font-size: 0.9rem; }
    .settings-shell .fold-head span { font-size: 0.72rem; }
    .settings-card .grid-2, .settings-card .grid-3, .settings-card .grid-4 { gap: 10px; }
    .settings-inputs { display: grid; gap: 10px; }
    .settings-actions { display: flex; flex-wrap: wrap; gap: 6px; }
    .settings-actions > button { width: auto; flex: 1 1 120px; }
    .settings-options { display: grid; gap: 6px; grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .settings-shell label { font-size: 0.75rem; color: var(--muted-foreground); margin-bottom: 4px; }
    .settings-shell textarea { min-height: 80px; }
    .settings-note { font-size: 0.72rem; color: var(--muted-foreground); }
    .checkbox-row {
      display: inline-flex; gap: 6px; align-items: center;
      min-height: 36px; color: var(--muted-foreground);
      padding: 7px 10px; border: 1px solid var(--border);
      border-radius: var(--radius); background: var(--input); font-size: 0.8rem;
    }
    .checkbox-row input { width: auto; margin: 0; }
    .pagination { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 4px; }
    .pagination button { width: auto; min-width: 32px; min-height: 30px; padding: 4px 8px; font-size: 0.8rem; }
    .pagination .page-current { background: rgba(59,130,246,0.2); border-color: var(--ring); color: #dbeafe; }
    .pagination .page-ellipsis { color: var(--muted-foreground); padding: 0 2px; font-size: 0.8rem; }
    .stack-list { display: grid; gap: 6px; }
    .list-item {
      width: 100%; border: 1px solid var(--border); border-radius: var(--radius);
      padding: 9px 11px; background: var(--card); color: var(--foreground); text-align: left;
    }
    .list-item.active { border-color: var(--ring); background: rgba(59,130,246,0.08); }
    .list-item strong { display: block; margin-bottom: 2px; font-size: 0.875rem; }
    .list-item .hint { display: block; margin-top: 2px; }
    .todo-board { display: grid; gap: 14px; }
    .todo-lane { display: grid; gap: 6px; border: 0; padding: 0; background: transparent; }
    .todo-lane-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 0 2px; }
    .todo-lane-copy { min-width: 0; display: flex; align-items: center; gap: 6px; }
    .todo-lane-title { font-weight: 600; font-size: 0.875rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .todo-lane-meta { display: none; }
    .todo-count { font-size: 0.72rem; color: var(--muted-foreground); }
    .todo-lane-body { display: grid; gap: 2px; }
    .todo-bar { display: grid; gap: 0; border: 0; border-radius: var(--radius); padding: 2px 0; background: transparent; }
    .todo-bar.active { background: rgba(255,255,255,0.03); }
    .todo-bar-head { display: grid; grid-template-columns: 30px minmax(0,1fr); gap: 8px; align-items: center; padding: 4px 2px; }
    .todo-check {
      width: 26px; min-height: 26px; height: 26px; padding: 0;
      border-radius: 7px; border: 1.5px solid rgba(113,113,122,0.6);
      background: transparent; color: var(--primary); font-size: 0.85rem; font-weight: 700; box-shadow: none;
    }
    .todo-check.status-in_progress, .todo-check.status-done, .todo-check.status-verified { border-color: rgba(113,113,122,0.7); color: var(--primary); }
    .todo-check.status-blocked { color: #f87171; border-color: rgba(248,113,113,0.45); }
    .todo-bar-copy { min-width: 0; display: grid; gap: 2px; cursor: pointer; }
    .todo-bar-title { font-size: 0.9rem; font-weight: 500; line-height: 1.35; color: var(--foreground); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .todo-bar.is-complete .todo-bar-title { color: var(--muted-foreground); text-decoration: line-through; text-decoration-thickness: 1px; }
    .todo-bar-detail { display: none; color: var(--muted-foreground); font-size: 0.75rem; line-height: 1.45; }
    .todo-bar.active .todo-bar-detail { display: block; }
    .todo-badges, .todo-bar-progress, .todo-bar-actions { display: none; }
    .checklist-compose { display: grid; gap: 12px; }
    .checklist-toolbar { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; justify-content: flex-end; }
    .checklist-toolbar .hint { display: none; }
    .checklist-actions { display: flex; flex-wrap: wrap; gap: 6px; width: 100%; }
    .checklist-actions > button { flex: 1 1 140px; width: auto; }
    .checklist-stage { display: grid; gap: 4px; padding: 0; border: 0; border-radius: 0; background: transparent; }
    .checklist-stage strong { font-size: 0.9rem; line-height: 1.25; }
    .checklist-stage .hint { font-size: 0.78rem; }
    .checklist-group { display: grid; gap: 0; padding: 0; border: 0; border-radius: 0; background: transparent; }
    .checklist-group-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 0 2px 8px; }
    .checklist-group-copy { display: grid; gap: 2px; min-width: 0; }
    .checklist-group-copy strong { font-size: 0.9rem; line-height: 1.2; }
    .checklist-counter { font-size: 0.78rem; color: var(--muted-foreground); padding: 0; border: 0; border-radius: 0; background: transparent; }
    .checklist-items { display: grid; gap: 0; border-top: 1px solid var(--border); }
    .checklist-row {
      display: grid; grid-template-columns: 32px minmax(0,1fr); gap: 10px;
      align-items: start; padding: 10px 4px; border: 0;
      border-bottom: 1px solid var(--border); border-radius: 0;
      background: transparent; transition: background-color 100ms; cursor: pointer;
    }
    .checklist-row:hover { background: rgba(255,255,255,0.03); }
    .checklist-row.active { background: rgba(59,130,246,0.08); }
    .checklist-row.is-complete { opacity: 0.65; }
    .checklist-row.is-complete .checklist-text { text-decoration: line-through; color: var(--muted-foreground); }
    .checklist-toggle {
      width: 24px; min-height: 24px; height: 24px; padding: 0;
      border-radius: 7px; border: 1px solid rgba(82,82,91,0.9);
      background: transparent; color: transparent; box-shadow: none;
    }
    .checklist-toggle.is-complete { background: rgba(59,130,246,0.15); border-color: rgba(96,165,250,0.7); color: #93c5fd; }
    .checklist-copy { display: grid; gap: 2px; min-width: 0; }
    .checklist-text { font-size: 0.9rem; line-height: 1.45; color: var(--foreground); word-break: break-word; }
    .checklist-sub { color: var(--muted-foreground); font-size: 0.72rem; line-height: 1.35; display: none; }
    .checklist-row.active .checklist-sub, .checklist-row.has-detail .checklist-sub { display: block; }
    .empty-state {
      padding: 14px; border: 1px dashed var(--border); border-radius: var(--radius);
      color: var(--muted-foreground); text-align: center; background: transparent; font-size: 0.85rem;
    }
    .gantt-container { width: 100%; overflow-x: auto; min-height: 48px; }
    .gantt-container svg { display: block; width: 100%; overflow: visible; font-family: inherit; }
    .gantt-container .gantt-empty { padding: 14px; color: var(--muted-foreground); font-size: 0.85rem; text-align: center; }
    .hidden-select { position: absolute; opacity: 0; pointer-events: none; width: 1px; height: 1px; overflow: hidden; }
    .todo-bar {
      display: grid;
      gap: 0;
      border: 0;
      border-radius: 12px;
      padding: 2px 0;
      background: transparent;
    }
    .todo-bar.active {
      background: rgba(255, 255, 255, 0.03);
    }
    .todo-bar-head {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 10px;
      align-items: center;
      padding: 4px 2px;
    }
    .todo-check {
      width: 30px;
      min-height: 30px;
      height: 30px;
      padding: 0;
      border-radius: 9px;
      border: 2px solid rgba(148, 163, 184, 0.55);
      background: transparent;
      color: #60a5fa;
      font-size: 0.95rem;
      font-weight: 700;
      box-shadow: none;
    }
    .todo-check.status-in_progress,
    .todo-check.status-done,
    .todo-check.status-verified {
      border-color: rgba(148, 163, 184, 0.62);
      color: #60a5fa;
    }
    .todo-check.status-blocked {
      color: #f87171;
      border-color: rgba(248, 113, 113, 0.45);
    }
    .todo-bar-copy {
      min-width: 0;
      display: grid;
      gap: 2px;
      cursor: pointer;
    }
    .todo-bar-title {
      font-size: 0.98rem;
      font-weight: 500;
      line-height: 1.35;
      color: rgba(226, 232, 240, 0.92);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .todo-bar.is-complete .todo-bar-title {
      color: rgba(148, 163, 184, 0.72);
      text-decoration: line-through;
      text-decoration-thickness: 2px;
    }
    .todo-bar-detail {
      display: none;
      color: var(--muted-foreground);
      font-size: 0.78rem;
      line-height: 1.45;
    }
    .todo-bar.active .todo-bar-detail {
      display: block;
    }
    .todo-badges,
    .todo-bar-progress,
    .todo-bar-actions {
      display: none;
    }
    .checklist-compose {
      display: grid;
      gap: 12px;
    }
    .checklist-toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      justify-content: flex-end;
    }
    .checklist-toolbar .hint {
      display: none;
    }
    .checklist-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      width: 100%;
    }
    .checklist-actions > button {
      flex: 1 1 160px;
      width: auto;
    }
    .chatbot-layout {
      display: grid;
      grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
      gap: 12px;
      align-items: start;
    }
    .chat-sidebar, .chat-main {
      border: 1px solid var(--border);
      border-radius: calc(var(--radius) + 2px);
      background: var(--card);
    }
    .chat-sidebar {
      display: grid;
      gap: 0;
      padding: 14px 12px 10px;
      position: sticky;
      top: 12px;
    }
    .chatbot-sidebar-header { display: grid; gap: 4px; padding-bottom: 10px; border-bottom: 1px solid var(--border); margin-bottom: 4px; }
    .chatbot-sidebar-header h2, .chat-main-header h2 { font-size: 0.95rem; font-weight: 600; }
    .chatbot-overline { display: none; }
    .chatbot-agent-card, .chatbot-sidebar-panel {
      display: grid; gap: 6px; padding: 10px 0;
      border: 0; border-bottom: 1px solid var(--border); border-radius: 0; background: transparent;
    }
    .chatbot-agent-card strong { font-size: 0.875rem; font-weight: 600; }
    .chatbot-agent-card span, .chatbot-sidebar-panel .hint { color: var(--muted-foreground); font-size: 0.78rem; line-height: 1.5; }
    .chatbot-sidebar-title { font-size: 0.68rem; color: var(--muted-foreground); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
    .chat-main {
      display: grid;
      grid-template-rows: auto minmax(380px, 1fr) auto;
      min-height: 680px;
      overflow: hidden;
    }
    .chat-main-header {
      display: flex; align-items: flex-start; justify-content: space-between;
      gap: 10px; padding: 14px 16px 12px;
      border-bottom: 1px solid var(--border);
    }
    .chat-main-header .hint { margin-top: 4px; display: block; }
    .chat-main-actions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }
    .chat-main-actions button { width: auto; min-width: 90px; }
    .chat-feed {
      display: grid; align-content: start; gap: 12px;
      overflow: auto; padding: 16px;
      background: var(--background);
    }
    .message { display: grid; gap: 6px; width: 100%; }
    .message.user { justify-items: end; }
    .message.agent { justify-items: start; }
    .message-meta { display: inline-flex; align-items: center; gap: 6px; color: var(--muted-foreground); font-size: 0.72rem; padding: 0 4px; }
    .message-body {
      max-width: min(100%, 720px); padding: 10px 14px;
      border-radius: 12px; border: 1px solid var(--border);
      white-space: pre-wrap; word-break: break-word; line-height: 1.6;
    }
    .message.user .message-body {
      background: var(--primary); border-color: rgba(96,165,250,0.5);
      color: var(--primary-foreground); border-bottom-right-radius: 4px;
      max-width: min(85%, 600px);
    }
    .message.agent .message-body {
      background: #000; color: #d4d4d8; border-bottom-left-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.8rem; max-width: min(92%, 720px);
    }
    .composer {
      display: grid; gap: 10px; padding: 14px 16px 16px;
      border-top: 1px solid var(--border);
    }
    .composer-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .composer-head label { margin: 0; color: var(--foreground); font-size: 0.875rem; font-weight: 500; }
    .chat-input {
      min-height: 96px; border-radius: var(--radius);
      border-color: var(--border); background: var(--input);
      padding: 10px 12px; line-height: 1.6;
    }
    .composer-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; }
    .composer-actions .row-inline { flex-wrap: wrap; width: 100%; justify-content: space-between; }
    .composer-actions button { flex: 1 1 120px; }
    .thread-list { display: grid; gap: 3px; max-height: 300px; overflow: auto; }
    .thread-card {
      width: 100%; border: 1px solid transparent; border-radius: var(--radius);
      padding: 8px 10px; background: transparent; color: var(--foreground);
      text-align: left; transition: background-color 100ms, border-color 100ms; box-shadow: none;
    }
    .thread-card:hover { background: var(--muted); border-color: var(--border); }
    .thread-card.active { background: rgba(59,130,246,0.12); border-color: rgba(96,165,250,0.4); }
    .thread-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px; font-weight: 600; font-size: 0.85rem; }
    .worker-strip { display: grid; gap: 4px; }
    .worker-chip {
      width: 100%; display: grid; grid-template-columns: 38px minmax(0,1fr);
      align-items: center; gap: 10px; min-height: 52px; padding: 8px 10px;
      border: 1px solid var(--border); border-radius: var(--radius);
      background: var(--card); color: var(--foreground); text-align: left;
    }
    .worker-chip:hover { background: var(--muted); }
    .worker-chip.active { background: rgba(59,130,246,0.1); border-color: rgba(96,165,250,0.45); }
    .worker-avatar {
      position: relative; width: 38px; height: 38px; border-radius: var(--radius);
      display: grid; place-items: center; color: #eff6ff; overflow: hidden;
      isolation: isolate; border: 1px solid rgba(255,255,255,0.08);
    }
    .worker-avatar::before {
      content: ""; position: absolute; inset: 0;
      background: radial-gradient(circle at 28% 24%, rgba(255,255,255,0.2), transparent 38%); z-index: -1;
    }
    .worker-avatar[data-tone="tone-0"] { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); }
    .worker-avatar[data-tone="tone-1"] { background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%); }
    .worker-avatar[data-tone="tone-2"] { background: linear-gradient(135deg, #0891b2 0%, #0f766e 100%); }
    .worker-avatar[data-tone="tone-3"] { background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); }
    .worker-avatar[data-tone="tone-4"] { background: linear-gradient(135deg, #65a30d 0%, #15803d 100%); }
    .worker-avatar[data-tone="tone-5"] { background: linear-gradient(135deg, #db2777 0%, #9333ea 100%); }
    .worker-initials { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.02em; }
    .worker-glyph { position: absolute; top: 4px; left: 5px; font-size: 0.58rem; line-height: 1; color: rgba(255,255,255,0.7); }
    .worker-chip.active .worker-avatar { box-shadow: 0 0 0 2px rgba(147,197,253,0.4); }
    .worker-dot { position: absolute; right: 1px; bottom: 1px; width: 8px; height: 8px; border-radius: 999px; background: #52525b; border: 1.5px solid var(--card); }
    .worker-dot.live { background: var(--success); }
    .worker-copy { min-width: 0; display: grid; gap: 2px; }
    .worker-name { font-size: 0.85rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .worker-meta { color: var(--muted-foreground); font-size: 0.72rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .page-view { display: none; gap: 12px; }
    .page-view.active { display: grid; }
    .page-view.view-entering { animation: page-view-enter 160ms ease-out; }
    @keyframes page-view-enter {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .action-strip { display: flex; flex-wrap: wrap; gap: 6px; }
    .action-strip > button { width: auto; flex: 1 1 140px; }
    .stats-grid { display: grid; gap: 8px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .workspace-grid { display: grid; gap: 12px; grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.95fr); align-items: start; }
    .panel-stack, .settings-shell, .todo-shell, .delivery-shell, .inspector-stack, .support-list { display: grid; gap: 12px; }
    .settings-shell { grid-template-columns: minmax(0, 1fr); align-items: start; }
    .todo-shell { grid-template-columns: minmax(0, 1.08fr) minmax(300px, 0.92fr); align-items: start; }
    .delivery-shell { grid-template-columns: minmax(0, 1fr); align-items: start; }
    .delivery-page { gap: 12px; }
    .delivery-head { display: grid; gap: 4px; padding: 2px 0; }
    .delivery-head strong { font-size: 0.95rem; line-height: 1.3; }
    .delivery-head .hint { font-size: 0.78rem; }
    .support-card { gap: 8px; }
    .support-item { padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--muted); }
    .support-item strong { display: block; margin-bottom: 2px; font-size: 0.85rem; }
    .hero-meta { display: none; }
    .hero-note { display: none; }
    @media (max-width: 900px) {
      .main-grid, .grid-2, .grid-3, .grid-4, .chatbot-layout, .workspace-grid, .settings-shell, .todo-shell, .delivery-shell, .stats-grid, .settings-options { grid-template-columns: 1fr; }
      .row-inline { flex-direction: column; align-items: stretch; }
      .chat-sidebar { position: static; }
      .chat-main-header, .composer-actions .row-inline { flex-direction: column; align-items: stretch; }
      .chat-main-actions { width: 100%; justify-content: stretch; }
      .chat-main-actions button { width: 100%; }
      .view-chip { flex: 1 1 calc(50% - 6px); text-align: center; }
      .wrap { padding-bottom: 100px; }
    }
    @media (max-width: 520px) {
      .wrap { padding: 16px 12px 90px; }
      .card { padding: 12px; }
      .view-switcher { top: 8px; gap: 5px; padding: 5px; }
      button, input, select, textarea { font-size: 16px; }
    }
  """

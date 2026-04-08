export function normalizeCommandText(text) {
  const value = String(text ?? "").trim();
  if (!value) {
    return "";
  }
  if (value.startsWith("／")) {
    return `/${value.slice(1)}`;
  }
  return value;
}

export function truncateText(text, maxChars) {
  const value = String(text ?? "").trim();
  if (!value) {
    return "";
  }
  if (value.length <= maxChars) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxChars - 16)).trimEnd()}\n\n[truncated]`;
}

function overlapLineCount(previousLines, nextLines) {
  const max = Math.min(previousLines.length, nextLines.length);
  for (let size = max; size > 0; size -= 1) {
    const prevSlice = previousLines.slice(previousLines.length - size).join("\n");
    const nextSlice = nextLines.slice(0, size).join("\n");
    if (prevSlice === nextSlice) {
      return size;
    }
  }
  return 0;
}

export function computeOutputDelta(previousOutput, nextOutput) {
  const previous = String(previousOutput ?? "");
  const next = String(nextOutput ?? "");
  if (!next || next === previous) {
    return "";
  }
  if (!previous) {
    return next.trim();
  }
  if (next.startsWith(previous)) {
    return next.slice(previous.length).trim();
  }

  const previousLines = previous.split("\n");
  const nextLines = next.split("\n");
  const overlap = overlapLineCount(previousLines, nextLines);
  if (overlap > 0) {
    return nextLines.slice(overlap).join("\n").trim();
  }
  return next.trim();
}

export function flattenPanes(snapshot) {
  const panes = [];
  for (const session of snapshot.sessions || []) {
    for (const window of session.windows || []) {
      for (const pane of window.panes || []) {
        panes.push(pane);
      }
    }
  }
  return panes;
}

export function formatDashboard(dashboard) {
  const targets = Array.isArray(dashboard.targets) ? dashboard.targets : [];
  if (targets.length === 0) {
    return "No saved profiles.";
  }
  return targets
    .map((target) => {
      const status = target.online ? "online" : "offline";
      const panes = Number(target.pane_count || 0);
      const sessions = Number(target.session_count || 0);
      return `${target.name} · ${status} · ${sessions} session(s) · ${panes} pane(s)`;
    })
    .join("\n");
}

export function formatPanes(snapshot, currentTarget = "") {
  const panes = flattenPanes(snapshot);
  if (panes.length === 0) {
    return "No tmux panes found for this profile.";
  }
  return panes
    .map((pane) => {
      const marker = pane.target === currentTarget ? "* " : "- ";
      const alias = pane.alias ? ` · alias=${pane.alias}` : "";
      const title = pane.title ? ` · title=${pane.title}` : "";
      const cmd = pane.current_command ? ` · cmd=${pane.current_command}` : "";
      return `${marker}${pane.target}${alias}${title}${cmd}`;
    })
    .join("\n");
}

export function formatHistory(historyPayload) {
  const entries = Array.isArray(historyPayload.history) ? historyPayload.history : [];
  if (entries.length === 0) {
    return "No command history yet.";
  }
  return entries
    .map((entry) => `- ${entry.created_at || "-"} · ${entry.target} · ${entry.command}`)
    .join("\n");
}

export function formatTodos(todosPayload) {
  const todos = Array.isArray(todosPayload.todos) ? todosPayload.todos : [];
  if (todos.length === 0) {
    return "No todos in the current scope.";
  }
  return todos
    .map((todo) => `- [${todo.status}] ${todo.id.slice(0, 8)} · ${todo.title}`)
    .join("\n");
}

export function formatPaneOutput(output, maxChars) {
  const trimmed = truncateText(output, maxChars);
  if (!trimmed) {
    return "Pane output is empty.";
  }
  return `Recent pane output:\n${trimmed}`;
}

export function formatApiResult(payload, maxChars) {
  const rendered =
    typeof payload === "string"
      ? payload
      : JSON.stringify(payload, null, 2);
  return truncateText(rendered, maxChars);
}

export function parseApiCommand(text) {
  const trimmed = String(text ?? "").trim();
  const match = trimmed.match(/^\/api\s+([A-Za-z]+)\s+(\S+)(?:\s+([\s\S]+))?$/);
  if (!match) {
    return null;
  }
  const method = match[1].toUpperCase();
  const path = match[2];
  const rawBody = String(match[3] || "").trim();
  let body;
  if (rawBody) {
    body = JSON.parse(rawBody);
  }
  return { method, path, body };
}

export const HELP_TEXT = [
  "ClawDone WeChat bridge",
  "",
  "/profiles",
  "/use-profile <name>",
  "/panes",
  "/use <session:window.pane>",
  "/where",
  "/status [lines]",
  "/interrupt",
  "/history [limit]",
  "/todos [status]",
  "/todo <title> || <detail>",
  "/confirm <prompt>",
  "/api <METHOD> <path> [json]",
  "",
  "Plain text without / will be sent to the current pane as a task prompt.",
].join("\n");

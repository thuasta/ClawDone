export class ClawDoneClient {
  constructor(baseUrl, token) {
    this.baseUrl = String(baseUrl).replace(/\/+$/, "");
    this.token = token;
  }

  async requestJson(method, path, { actor = "", body = undefined } = {}) {
    const url = new URL(path, `${this.baseUrl}/`);
    const headers = {
      Authorization: `Bearer ${this.token}`,
    };
    if (actor) {
      headers["X-ClawDone-Actor"] = actor;
    }
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    const text = await response.text();
    const contentType = response.headers.get("content-type") || "";
    let payload = text;
    if (contentType.includes("application/json")) {
      try {
        payload = JSON.parse(text || "{}");
      } catch {
        payload = { error: text };
      }
    }

    if (!response.ok) {
      const message =
        payload && typeof payload === "object" && !Array.isArray(payload) && payload.error
          ? String(payload.error)
          : `HTTP ${response.status}`;
      const error = new Error(message);
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  getDashboard(actor) {
    return this.requestJson("GET", "/api/dashboard", { actor });
  }

  getProfiles(actor) {
    return this.requestJson("GET", "/api/profiles", { actor });
  }

  getRemoteState(profile, actor) {
    return this.requestJson("GET", `/api/remote/state?profile=${encodeURIComponent(profile)}`, { actor });
  }

  getPane(profile, target, lines, actor) {
    return this.requestJson(
      "GET",
      `/api/pane?profile=${encodeURIComponent(profile)}&target=${encodeURIComponent(target)}&lines=${encodeURIComponent(String(lines))}`,
      { actor },
    );
  }

  getHistory(profile, limit, actor) {
    return this.requestJson(
      "GET",
      `/api/history?profile=${encodeURIComponent(profile)}&limit=${encodeURIComponent(String(limit))}`,
      { actor },
    );
  }

  getTodos(profile, target, status, actor) {
    const params = new URLSearchParams();
    if (profile) params.set("profile", profile);
    if (target) params.set("target", target);
    if (status) params.set("status", status);
    return this.requestJson("GET", `/api/todos?${params.toString()}`, { actor });
  }

  sendCommand(profile, target, command, actor, confirmRisk = false) {
    return this.requestJson("POST", "/api/send", {
      actor,
      body: {
        profile,
        target,
        command,
        confirm_risk: confirmRisk,
        press_enter: true,
      },
    });
  }

  interrupt(profile, target, actor) {
    return this.requestJson("POST", "/api/interrupt", {
      actor,
      body: {
        profile,
        target,
      },
    });
  }

  createTodo(profile, target, title, detail, actor) {
    return this.requestJson("POST", "/api/todos", {
      actor,
      body: {
        profile,
        target,
        title,
        detail,
      },
    });
  }

  rawApi(method, path, actor, body) {
    return this.requestJson(method, path, { actor, body });
  }
}

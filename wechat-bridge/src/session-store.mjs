import { readFile, writeFile } from "node:fs/promises";

import { ensureParentDir } from "./config.mjs";

export class SessionStore {
  constructor(stateFile, users) {
    this.stateFile = stateFile;
    this.users = users;
    this.state = { users: {} };
  }

  async load() {
    try {
      const raw = await readFile(this.stateFile, "utf-8");
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object" && parsed.users && typeof parsed.users === "object") {
        this.state = parsed;
      }
    } catch (error) {
      if (error && error.code !== "ENOENT") {
        throw error;
      }
      this.state = { users: {} };
    }

    for (const [senderId, defaults] of Object.entries(this.users)) {
      const current = this.state.users[senderId] || {};
      this.state.users[senderId] = {
        currentProfile: String(current.currentProfile || defaults.defaultProfile || "").trim(),
        currentTarget: String(current.currentTarget || defaults.defaultTarget || "").trim(),
        updatedAt: String(current.updatedAt || ""),
      };
    }
  }

  async save() {
    await ensureParentDir(this.stateFile);
    await writeFile(this.stateFile, JSON.stringify(this.state, null, 2));
  }

  get(senderId) {
    return this.state.users[senderId] || {
      currentProfile: String(this.users[senderId]?.defaultProfile || ""),
      currentTarget: String(this.users[senderId]?.defaultTarget || ""),
      updatedAt: "",
    };
  }

  async update(senderId, patch) {
    const current = this.get(senderId);
    this.state.users[senderId] = {
      ...current,
      ...patch,
      updatedAt: new Date().toISOString(),
    };
    await this.save();
    return this.state.users[senderId];
  }
}

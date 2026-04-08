import { WeixinChannel } from "wechat-ai";
import { pathToFileURL } from "node:url";

import { ClawDoneClient } from "./clawdone-client.mjs";
import { loadBridgeConfig } from "./config.mjs";
import {
  HELP_TEXT,
  computeOutputDelta,
  formatApiResult,
  formatDashboard,
  formatHistory,
  formatPaneOutput,
  formatPanes,
  formatTodos,
  normalizeCommandText,
  parseApiCommand,
  truncateText,
} from "./formatting.mjs";
import { SessionStore } from "./session-store.mjs";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parsePositiveInt(value, fallback) {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }
  const parsed = Number.parseInt(String(value), 10);
  if (Number.isNaN(parsed) || parsed <= 0) {
    throw new Error("Expected a positive integer.");
  }
  return parsed;
}

export class WeChatClawDoneBridge {
  constructor(config) {
    this.config = config;
    this.client = new ClawDoneClient(config.clawdoneBaseUrl, config.clawdoneToken);
    this.channel = new WeixinChannel({
      type: "weixin",
      enabled: true,
      ...(config.weixin.baseUrl ? { baseUrl: config.weixin.baseUrl } : {}),
    });
    this.sessions = new SessionStore(config.stateFile, config.users);
    this.watchers = new Map();
    this.unknownUsersWarned = new Set();
    this.stopping = false;
  }

  actorFor(senderId) {
    return `wechat:${senderId}`;
  }

  async start() {
    await this.sessions.load();
    this.installSignalHandlers();
    console.log(`ClawDone WeChat bridge starting`);
    console.log(`ClawDone API: ${this.config.clawdoneBaseUrl}`);
    console.log(`State file: ${this.config.stateFile}`);
    await this.channel.start((message) => {
      void this.handleInboundMessage(message).catch((error) => {
        console.error(`handleInboundMessage failed: ${error instanceof Error ? error.stack || error.message : String(error)}`);
      });
    });
  }

  installSignalHandlers() {
    const stop = async () => {
      await this.stop();
      process.exit(0);
    };
    process.once("SIGINT", () => void stop());
    process.once("SIGTERM", () => void stop());
  }

  async stop() {
    if (this.stopping) {
      return;
    }
    this.stopping = true;
    for (const watcher of this.watchers.values()) {
      watcher.cancelled = true;
    }
    this.watchers.clear();
    try {
      await this.channel.stop();
    } catch (error) {
      console.error(`channel.stop failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  isAllowed(senderId) {
    return Boolean(this.config.users[senderId]);
  }

  async maybeSendTyping(message) {
    if (typeof this.channel.sendTyping !== "function") {
      return;
    }
    try {
      await this.channel.sendTyping(message.senderId, message.replyToken);
    } catch {
      return;
    }
  }

  async reply(message, text) {
    const payload = truncateText(text, this.config.reply.maxMessageChars);
    if (!payload) {
      return;
    }
    try {
      await this.channel.send({
        targetId: message.senderId,
        text: payload,
        replyToken: message.replyToken,
      });
    } catch (error) {
      if (!message.replyToken) {
        throw error;
      }
      await this.channel.send({
        targetId: message.senderId,
        text: payload,
      });
    }
  }

  async rejectUnknownUser(message) {
    if (this.unknownUsersWarned.has(message.senderId)) {
      return;
    }
    this.unknownUsersWarned.add(message.senderId);
    console.log(`Unknown WeChat sender: ${message.senderId}`);
    if (this.config.discoveryMode) {
      await this.reply(
        message,
        [
          "Discovery mode is enabled.",
          `Your sender id is: ${message.senderId}`,
          "Add it to config.users, then restart the bridge.",
        ].join("\n"),
      );
      return;
    }
    await this.reply(message, "This WeChat user is not allowed to use this ClawDone bridge.");
  }

  currentSession(senderId) {
    return this.sessions.get(senderId);
  }

  requireProfile(senderId) {
    const session = this.currentSession(senderId);
    if (!session.currentProfile) {
      throw new Error("No current profile. Use /profiles and /use-profile <name> first.");
    }
    return session;
  }

  requireTarget(senderId) {
    const session = this.requireProfile(senderId);
    if (!session.currentTarget) {
      throw new Error("No current target. Use /panes and /use <session:window.pane> first.");
    }
    return session;
  }

  cancelWatcher(senderId) {
    const watcher = this.watchers.get(senderId);
    if (!watcher) {
      return;
    }
    watcher.cancelled = true;
    this.watchers.delete(senderId);
  }

  async handleInboundMessage(message) {
    if (!this.isAllowed(message.senderId)) {
      await this.rejectUnknownUser(message);
      return;
    }

    if (Array.isArray(message.media) && message.media.length > 0) {
      await this.reply(message, "Media input is not supported yet. Send text commands or plain task prompts.");
      return;
    }

    const text = normalizeCommandText(message.text);
    if (!text) {
      await this.reply(message, HELP_TEXT);
      return;
    }

    if (text.startsWith("/")) {
      await this.handleSlashCommand(message, text);
      return;
    }
    try {
      await this.handlePrompt(message, text, false);
    } catch (error) {
      await this.reply(message, this.formatError(error, text));
    }
  }

  async handleSlashCommand(message, text) {
    const [commandToken, ...restParts] = text.split(/\s+/);
    const command = commandToken.toLowerCase();
    const rest = restParts.join(" ").trim();
    const actor = this.actorFor(message.senderId);

    try {
      switch (command) {
        case "/help":
          await this.reply(message, HELP_TEXT);
          return;

        case "/profiles": {
          await this.maybeSendTyping(message);
          const dashboard = await this.client.getDashboard(actor);
          await this.reply(message, formatDashboard(dashboard));
          return;
        }

        case "/use-profile": {
          if (!rest) {
            throw new Error("Usage: /use-profile <name>");
          }
          const profiles = await this.client.getProfiles(actor);
          const names = new Set((profiles.profiles || []).map((profile) => profile.name));
          if (!names.has(rest)) {
            throw new Error(`Unknown profile: ${rest}`);
          }
          this.cancelWatcher(message.senderId);
          await this.sessions.update(message.senderId, {
            currentProfile: rest,
            currentTarget: "",
          });
          await this.reply(message, `Current profile set to ${rest}. Use /panes to pick a target.`);
          return;
        }

        case "/panes": {
          const session = this.requireProfile(message.senderId);
          await this.maybeSendTyping(message);
          const snapshot = await this.client.getRemoteState(session.currentProfile, actor);
          await this.reply(message, formatPanes(snapshot, session.currentTarget));
          return;
        }

        case "/use": {
          if (!rest) {
            throw new Error("Usage: /use <session:window.pane>");
          }
          const session = this.requireProfile(message.senderId);
          const snapshot = await this.client.getRemoteState(session.currentProfile, actor);
          const panes = new Set((snapshot.sessions || []).flatMap((item) => (item.windows || []).flatMap((window) => (window.panes || []).map((pane) => pane.target))));
          if (!panes.has(rest)) {
            throw new Error(`Unknown target for ${session.currentProfile}: ${rest}`);
          }
          this.cancelWatcher(message.senderId);
          await this.sessions.update(message.senderId, { currentTarget: rest });
          await this.reply(message, `Current target set to ${session.currentProfile} · ${rest}`);
          return;
        }

        case "/where": {
          const session = this.currentSession(message.senderId);
          await this.reply(
            message,
            [
              `profile: ${session.currentProfile || "-"}`,
              `target: ${session.currentTarget || "-"}`,
              `actor: ${actor}`,
            ].join("\n"),
          );
          return;
        }

        case "/status": {
          const session = this.requireTarget(message.senderId);
          const lines = parsePositiveInt(rest || this.config.reply.statusLines, this.config.reply.statusLines);
          await this.maybeSendTyping(message);
          const pane = await this.client.getPane(session.currentProfile, session.currentTarget, lines, actor);
          await this.reply(message, formatPaneOutput(pane.output, this.config.reply.maxMessageChars));
          return;
        }

        case "/interrupt": {
          const session = this.requireTarget(message.senderId);
          this.cancelWatcher(message.senderId);
          await this.client.interrupt(session.currentProfile, session.currentTarget, actor);
          await this.reply(message, `Sent Ctrl+C to ${session.currentProfile} · ${session.currentTarget}`);
          return;
        }

        case "/history": {
          const session = this.requireProfile(message.senderId);
          const limit = parsePositiveInt(rest || 10, 10);
          await this.maybeSendTyping(message);
          const history = await this.client.getHistory(session.currentProfile, limit, actor);
          await this.reply(message, formatHistory(history));
          return;
        }

        case "/todos": {
          const session = this.requireProfile(message.senderId);
          await this.maybeSendTyping(message);
          const todos = await this.client.getTodos(session.currentProfile, session.currentTarget, rest, actor);
          await this.reply(message, formatTodos(todos));
          return;
        }

        case "/todo": {
          const session = this.requireTarget(message.senderId);
          if (!rest) {
            throw new Error("Usage: /todo <title> || <detail>");
          }
          const [titlePart, detailPart = ""] = rest.split("||");
          const title = String(titlePart || "").trim();
          const detail = String(detailPart || "").trim();
          if (!title) {
            throw new Error("Todo title is required.");
          }
          const result = await this.client.createTodo(session.currentProfile, session.currentTarget, title, detail, actor);
          await this.reply(message, `Todo created: ${result.todo.id.slice(0, 8)} · ${result.todo.title}`);
          return;
        }

        case "/confirm": {
          if (!rest) {
            throw new Error("Usage: /confirm <prompt>");
          }
          await this.handlePrompt(message, rest, true);
          return;
        }

        case "/api": {
          await this.maybeSendTyping(message);
          const parsed = parseApiCommand(text);
          if (!parsed) {
            throw new Error("Usage: /api <METHOD> <path> [json]");
          }
          const payload = await this.client.rawApi(parsed.method, parsed.path, actor, parsed.body);
          await this.reply(message, formatApiResult(payload, this.config.reply.maxMessageChars));
          return;
        }

        default:
          await this.reply(message, HELP_TEXT);
      }
    } catch (error) {
      await this.reply(message, this.formatError(error, text));
    }
  }

  formatError(error, originalText = "") {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes("dangerous command requires confirm_risk=true")) {
      return `ClawDone marked this as high-risk. Re-send with:\n/confirm ${originalText.replace(/^\/confirm\s+/, "").trim()}`;
    }
    return `Error: ${message}`;
  }

  async handlePrompt(message, prompt, confirmRisk) {
    const session = this.requireTarget(message.senderId);
    const actor = this.actorFor(message.senderId);
    const cleaned = String(prompt || "").trim();
    if (!cleaned) {
      throw new Error("Prompt is empty.");
    }

    this.cancelWatcher(message.senderId);
    await this.maybeSendTyping(message);

    let baselineOutput = "";
    try {
      const pane = await this.client.getPane(
        session.currentProfile,
        session.currentTarget,
        this.config.reply.statusLines,
        actor,
      );
      baselineOutput = String(pane.output || "");
    } catch {
      baselineOutput = "";
    }

    try {
      await this.client.sendCommand(session.currentProfile, session.currentTarget, cleaned, actor, confirmRisk);
    } catch (error) {
      await this.reply(message, this.formatError(error, cleaned));
      return;
    }

    await this.reply(message, `Sent to ${session.currentProfile} · ${session.currentTarget}`);
    await this.startAutoPoll(message, session.currentProfile, session.currentTarget, actor, baselineOutput);
  }

  async startAutoPoll(message, profile, target, actor, baselineOutput) {
    if (!this.config.reply.autoPollEnabled) {
      return;
    }

    const watcher = { cancelled: false };
    this.watchers.set(message.senderId, watcher);

    void (async () => {
      let lastOutput = String(baselineOutput || "");
      let idleRounds = 0;
      const maxIdleRounds = 2;

      for (let round = 0; round < this.config.reply.autoPollMaxRounds; round += 1) {
        await sleep(this.config.reply.autoPollIntervalMs);
        if (watcher.cancelled) {
          break;
        }
        const pane = await this.client.getPane(profile, target, this.config.reply.statusLines, actor);
        const nextOutput = String(pane.output || "");
        const delta = computeOutputDelta(lastOutput, nextOutput);
        if (delta) {
          idleRounds = 0;
          lastOutput = nextOutput;
          await this.reply(message, `Pane update:\n${truncateText(delta, this.config.reply.maxMessageChars)}`);
          continue;
        }

        lastOutput = nextOutput;
        idleRounds += 1;
        if (idleRounds >= maxIdleRounds) {
          break;
        }
      }
    })()
      .catch(async (error) => {
        console.error(`auto-poll failed: ${error instanceof Error ? error.stack || error.message : String(error)}`);
        try {
          await this.reply(message, `Auto-follow failed: ${error instanceof Error ? error.message : String(error)}`);
        } catch {
          return;
        }
      })
      .finally(() => {
        if (this.watchers.get(message.senderId) === watcher) {
          this.watchers.delete(message.senderId);
        }
      });
  }
}

export async function main() {
  const argv = process.argv.slice(2);
  const configFlagIndex = argv.findIndex((value) => value === "--config");
  const configPath =
    configFlagIndex >= 0 && argv[configFlagIndex + 1]
      ? argv[configFlagIndex + 1]
      : undefined;

  const config = await loadBridgeConfig(configPath);
  const bridge = new WeChatClawDoneBridge(config);
  await bridge.start();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack || error.message : String(error));
    process.exit(1);
  });
}

import { mkdir, readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";

const DEFAULT_REPLY = {
  autoPollEnabled: true,
  autoPollIntervalMs: 4000,
  autoPollMaxRounds: 5,
  maxMessageChars: 1600,
  statusLines: 100,
};

export function expandHome(value) {
  const text = String(value ?? "").trim();
  if (!text) {
    return "";
  }
  if (text === "~") {
    return homedir();
  }
  if (text.startsWith("~/")) {
    return resolve(homedir(), text.slice(2));
  }
  return resolve(text);
}

export async function ensureParentDir(filePath) {
  const parent = dirname(filePath);
  await mkdir(parent, { recursive: true });
}

function normalizeUsers(rawUsers) {
  if (rawUsers === undefined) {
    return {};
  }
  if (!rawUsers || typeof rawUsers !== "object" || Array.isArray(rawUsers)) {
    throw new Error("config.users must be an object keyed by WeChat sender id");
  }

  const users = {};
  for (const [senderId, rawValue] of Object.entries(rawUsers)) {
    const cleanedSenderId = String(senderId).trim();
    if (!cleanedSenderId) {
      continue;
    }
    const value = rawValue && typeof rawValue === "object" && !Array.isArray(rawValue) ? rawValue : {};
    users[cleanedSenderId] = {
      name: String(value.name ?? "").trim(),
      defaultProfile: String(value.defaultProfile ?? "").trim(),
      defaultTarget: String(value.defaultTarget ?? "").trim(),
    };
  }

  return users;
}

export async function loadBridgeConfig(configPathArg) {
  const resolvedConfigPath = expandHome(configPathArg || process.env.CLAWDONE_WECHAT_CONFIG || "./config.json");
  const raw = await readFile(resolvedConfigPath, "utf-8");
  const parsed = JSON.parse(raw);

  const clawdoneBaseUrl = String(parsed.clawdoneBaseUrl ?? "").trim().replace(/\/+$/, "");
  const clawdoneToken = String(parsed.clawdoneToken ?? process.env.CLAWDONE_WECHAT_TOKEN ?? "").trim();
  if (!clawdoneBaseUrl) {
    throw new Error("config.clawdoneBaseUrl is required");
  }
  if (!clawdoneToken) {
    throw new Error("config.clawdoneToken is required (or set CLAWDONE_WECHAT_TOKEN)");
  }

  const stateFile = expandHome(parsed.stateFile || "~/.clawdone/wechat-bridge-state.json");
  const weixinBaseUrl = String(parsed.weixin?.baseUrl ?? "").trim();
  const reply = {
    ...DEFAULT_REPLY,
    ...(parsed.reply && typeof parsed.reply === "object" ? parsed.reply : {}),
  };
  const discoveryMode = Boolean(parsed.discoveryMode);
  const users = normalizeUsers(parsed.users);
  if (!discoveryMode && Object.keys(users).length === 0) {
    throw new Error("config.users must declare at least one allowed WeChat sender id unless discoveryMode is true");
  }

  return {
    configPath: resolvedConfigPath,
    clawdoneBaseUrl,
    clawdoneToken,
    stateFile,
    discoveryMode,
    users,
    weixin: {
      baseUrl: weixinBaseUrl,
    },
    reply: {
      autoPollEnabled: Boolean(reply.autoPollEnabled),
      autoPollIntervalMs: Math.max(1000, Number(reply.autoPollIntervalMs) || DEFAULT_REPLY.autoPollIntervalMs),
      autoPollMaxRounds: Math.max(1, Number(reply.autoPollMaxRounds) || DEFAULT_REPLY.autoPollMaxRounds),
      maxMessageChars: Math.max(400, Number(reply.maxMessageChars) || DEFAULT_REPLY.maxMessageChars),
      statusLines: Math.max(20, Number(reply.statusLines) || DEFAULT_REPLY.statusLines),
    },
  };
}

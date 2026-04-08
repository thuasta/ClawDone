import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SessionStore } from "../src/session-store.mjs";

test("SessionStore seeds defaults and persists updates", async () => {
  const dir = await mkdtemp(join(tmpdir(), "clawdone-wechat-"));
  const stateFile = join(dir, "state.json");
  const store = new SessionStore(stateFile, {
    wxid_me: {
      defaultProfile: "office",
      defaultTarget: "codex:0.0",
    },
  });

  await store.load();
  assert.deepEqual(store.get("wxid_me"), {
    currentProfile: "office",
    currentTarget: "codex:0.0",
    updatedAt: "",
  });

  await store.update("wxid_me", {
    currentTarget: "codex:1.0",
  });

  const reloaded = new SessionStore(stateFile, {
    wxid_me: {
      defaultProfile: "office",
      defaultTarget: "codex:0.0",
    },
  });
  await reloaded.load();
  assert.equal(reloaded.get("wxid_me").currentProfile, "office");
  assert.equal(reloaded.get("wxid_me").currentTarget, "codex:1.0");
  assert.ok(reloaded.get("wxid_me").updatedAt);
});

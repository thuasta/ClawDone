import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { loadBridgeConfig } from "../src/config.mjs";

test("loadBridgeConfig allows empty users only in discovery mode", async () => {
  const dir = await mkdtemp(join(tmpdir(), "clawdone-wechat-config-"));

  const blockedPath = join(dir, "blocked.json");
  await writeFile(
    blockedPath,
    JSON.stringify({
      clawdoneBaseUrl: "http://127.0.0.1:8787",
      clawdoneToken: "token",
      users: {},
    }),
  );
  await assert.rejects(() => loadBridgeConfig(blockedPath), /discoveryMode is true/);

  const allowedPath = join(dir, "allowed.json");
  await writeFile(
    allowedPath,
    JSON.stringify({
      clawdoneBaseUrl: "http://127.0.0.1:8787",
      clawdoneToken: "token",
      discoveryMode: true,
      users: {},
    }),
  );
  const config = await loadBridgeConfig(allowedPath);
  assert.equal(config.discoveryMode, true);
  assert.deepEqual(config.users, {});
});

import test from "node:test";
import assert from "node:assert/strict";

import { WeChatClawDoneBridge, main } from "../src/bridge.mjs";

test("bridge module exports the runnable entrypoints", () => {
  assert.equal(typeof WeChatClawDoneBridge, "function");
  assert.equal(typeof main, "function");
});

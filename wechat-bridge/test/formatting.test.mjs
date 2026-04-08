import test from "node:test";
import assert from "node:assert/strict";

import { computeOutputDelta, parseApiCommand, truncateText } from "../src/formatting.mjs";

test("computeOutputDelta returns appended content", () => {
  const previous = "line 1\nline 2";
  const next = "line 1\nline 2\nline 3";
  assert.equal(computeOutputDelta(previous, next), "line 3");
});

test("computeOutputDelta handles sliding pane windows", () => {
  const previous = "line 1\nline 2\nline 3";
  const next = "line 2\nline 3\nline 4";
  assert.equal(computeOutputDelta(previous, next), "line 4");
});

test("parseApiCommand parses method path and json body", () => {
  assert.deepEqual(
    parseApiCommand('/api POST /api/todos {"title":"Fix","profile":"office"}'),
    {
      method: "POST",
      path: "/api/todos",
      body: {
        title: "Fix",
        profile: "office",
      },
    },
  );
});

test("truncateText preserves shorter text and truncates long text", () => {
  assert.equal(truncateText("short", 20), "short");
  assert.match(truncateText("abcdefghijklmnopqrstuvwxyz", 16), /\[truncated\]$/);
});

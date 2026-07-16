// Domain tests for src/domain/integrity.js (Stage 2, FR-6 fail-closed judgement).
// Chain (hard fail) / count (hard fail) / empty-content (warning) / freshness (info).
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const structuredCloneFn = globalThis.structuredClone || ((v) => JSON.parse(JSON.stringify(v)));

const { buildMessageTree } = require("../src/domain/message_tree.js");
const { verifyIntegrity } = require("../src/domain/integrity.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

test("verifyIntegrity passes cleanly on a healthy fixture: ok, counts, freshness, no warnings", () => {
  const data = loadFixture("conversation_tree.json");
  const tree = buildMessageTree(data.chat_messages);
  const result = verifyIntegrity(tree, data.current_leaf_message_uuid);

  assert.equal(result.ok, true);
  assert.deepEqual(result.failures, []);
  assert.deepEqual(result.warnings, []);
  assert.deepEqual(result.counts, { human: 3, assistant: 3 });
  assert.equal(result.freshness, "2026-01-15T09:05:09.000Z"); // msg 0008's created_at
});

test("verifyIntegrity fails closed on a pruned/dangling fixture (AC-3 core)", () => {
  const data = loadFixture("conversation_pruned.json");
  const tree = buildMessageTree(data.chat_messages);
  const result = verifyIntegrity(tree, data.current_leaf_message_uuid);

  assert.equal(result.ok, false);
  assert.ok(result.failures.length > 0);
  assert.ok(result.failures.some((f) => /chain verification failed/i.test(f)));
  assert.ok(result.failures.some((f) => /dangling/i.test(f)));
});

test("verifyIntegrity warns (not fails) on an empty-content message that is on the leaf path", () => {
  const data = loadFixture("conversation_tree.json");
  const cloned = structuredCloneFn(data);
  const msg0003 = cloned.chat_messages.find((m) => m.uuid === "bbbbbbbb-0000-4000-8000-000000000003");
  msg0003.content = [];

  const tree = buildMessageTree(cloned.chat_messages);
  const result = verifyIntegrity(tree, cloned.current_leaf_message_uuid);

  assert.equal(result.ok, true, "empty content is a warning, not a hard failure");
  assert.ok(result.warnings.some((w) => w.includes(msg0003.uuid) && /empty content/i.test(w)));
});

test("verifyIntegrity warns on an assistant message with no text block, still on the leaf path", () => {
  const data = loadFixture("conversation_tree.json");
  const cloned = structuredCloneFn(data);
  const msg0004 = cloned.chat_messages.find((m) => m.uuid === "bbbbbbbb-0000-4000-8000-000000000004");
  msg0004.content = msg0004.content.filter((b) => b.type !== "text"); // drop the trailing text block

  const tree = buildMessageTree(cloned.chat_messages);
  const result = verifyIntegrity(tree, cloned.current_leaf_message_uuid);

  assert.equal(result.ok, true);
  assert.ok(result.warnings.some((w) => w.includes(msg0004.uuid) && /no text block/i.test(w)));
});

test("verifyIntegrity does not warn about the dead branch's empty-content message (not on leaf path)", () => {
  const data = loadFixture("conversation_tree.json");
  const tree = buildMessageTree(data.chat_messages);
  const result = verifyIntegrity(tree, data.current_leaf_message_uuid);

  // msg 0006 (dead branch, user_canceled, empty content) must not surface a warning
  // because it never gets serialized.
  assert.ok(!result.warnings.some((w) => w.includes("bbbbbbbb-0000-4000-8000-000000000006")));
});

test("verifyIntegrity hard-fails when a leaf-path message has an unrecognized sender value", () => {
  const data = loadFixture("conversation_tree.json");
  const cloned = structuredCloneFn(data);
  const msg0007 = cloned.chat_messages.find((m) => m.uuid === "bbbbbbbb-0000-4000-8000-000000000007");
  msg0007.sender = "system"; // neither human nor assistant

  const tree = buildMessageTree(cloned.chat_messages);
  const result = verifyIntegrity(tree, cloned.current_leaf_message_uuid);

  assert.equal(result.ok, false);
  assert.ok(result.failures.some((f) => /count mismatch/i.test(f)));
});

test("verifyIntegrity handles the degenerate single root-only message case", () => {
  const onlyMessage = {
    uuid: "eeeeeeee-0000-4000-8000-000000000001",
    sender: "human",
    content: [{ type: "text", text: "Only message.", citations: [] }],
    files: [],
    created_at: "2026-02-01T00:00:00.000Z",
    parent_message_uuid: "00000000-0000-4000-8000-000000000000",
  };
  const tree = buildMessageTree([onlyMessage]);
  const result = verifyIntegrity(tree, onlyMessage.uuid);

  assert.equal(result.ok, true);
  assert.deepEqual(result.counts, { human: 1, assistant: 0 });
  assert.equal(result.freshness, "2026-02-01T00:00:00.000Z");
});

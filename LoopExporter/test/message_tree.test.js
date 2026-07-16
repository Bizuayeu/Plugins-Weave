// Domain tests for src/domain/message_tree.js (Stage 2, FR-3).
// Verifies: uuid->message indexing, and that resolveLeafPath returns ONLY the
// current leaf's ancestry (root -> leaf, chronological order) -- dead branches
// from edits/regenerations must never be included (FR-3 default).
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { buildMessageTree, resolveLeafPath, ROOT_SENTINEL } = require("../src/domain/message_tree.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

test("buildMessageTree indexes every message by uuid", () => {
  const data = loadFixture("conversation_tree.json");
  const tree = buildMessageTree(data.chat_messages);
  assert.equal(tree.byUuid.size, data.chat_messages.length);
  for (const msg of data.chat_messages) {
    assert.equal(tree.byUuid.get(msg.uuid), msg);
  }
});

test("resolveLeafPath returns only the current leaf path in root -> leaf order, excluding dead branches", () => {
  const data = loadFixture("conversation_tree.json");
  const tree = buildMessageTree(data.chat_messages);
  const result = resolveLeafPath(tree, data.current_leaf_message_uuid);

  const resultUuids = result.map((m) => m.uuid);
  assert.deepEqual(resultUuids, [
    "bbbbbbbb-0000-4000-8000-000000000001",
    "bbbbbbbb-0000-4000-8000-000000000002",
    "bbbbbbbb-0000-4000-8000-000000000003",
    "bbbbbbbb-0000-4000-8000-000000000004",
    "bbbbbbbb-0000-4000-8000-000000000007",
    "bbbbbbbb-0000-4000-8000-000000000008",
  ]);

  const humanCount = result.filter((m) => m.sender === "human").length;
  const assistantCount = result.filter((m) => m.sender === "assistant").length;
  assert.equal(humanCount, 3);
  assert.equal(assistantCount, 3);

  // The dead branch (0005 -> 0006, the user_canceled empty-content leaf) must not appear.
  assert.ok(!resultUuids.includes("bbbbbbbb-0000-4000-8000-000000000005"));
  assert.ok(!resultUuids.includes("bbbbbbbb-0000-4000-8000-000000000006"));
});

test("resolveLeafPath throws when a parent reference is dangling before reaching the root sentinel", () => {
  const data = loadFixture("conversation_pruned.json");
  const tree = buildMessageTree(data.chat_messages);
  assert.throws(
    () => resolveLeafPath(tree, data.current_leaf_message_uuid),
    /dangling parent reference/i
  );
});

test("resolveLeafPath throws on a cycle instead of looping forever", () => {
  const cycleA = { uuid: "cycle-a", parent_message_uuid: "cycle-b", sender: "human", content: [] };
  const cycleB = { uuid: "cycle-b", parent_message_uuid: "cycle-a", sender: "assistant", content: [] };
  const tree = buildMessageTree([cycleA, cycleB]);
  assert.throws(() => resolveLeafPath(tree, "cycle-a"), /cycle detected/i);
});

test("resolveLeafPath handles the degenerate case of a single root-only message", () => {
  const onlyMessage = {
    uuid: "eeeeeeee-0000-4000-8000-000000000001",
    sender: "human",
    content: [{ type: "text", text: "Only message.", citations: [] }],
    files: [],
    created_at: "2026-02-01T00:00:00.000Z",
    parent_message_uuid: ROOT_SENTINEL,
  };
  const tree = buildMessageTree([onlyMessage]);
  const result = resolveLeafPath(tree, onlyMessage.uuid);
  assert.deepEqual(result, [onlyMessage]);
});

test("resolveLeafPath throws when the leaf uuid itself does not exist in the tree", () => {
  const data = loadFixture("conversation_tree.json");
  const tree = buildMessageTree(data.chat_messages);
  assert.throws(() => resolveLeafPath(tree, "nonexistent-uuid"), /no message found/i);
});

// Smoke test for Stage 1 (Phase 0): confirms the synthetic fixtures are valid JSON
// with the shapes Stage 2's domain tests will rely on, and doubles as the
// node:test execution-basis smoke check for this package.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

test("conversation_tree.json parses as JSON and has the expected top-level shape", () => {
  const data = loadFixture("conversation_tree.json");
  assert.ok(Array.isArray(data.chat_messages), "chat_messages must be an array");
  assert.ok(data.chat_messages.length > 0, "chat_messages must not be empty");
  assert.equal(typeof data.current_leaf_message_uuid, "string");
  for (const msg of data.chat_messages) {
    assert.equal(typeof msg.parent_message_uuid, "string", `message ${msg.uuid} must have parent_message_uuid`);
  }
});

test("conversation_tree.json root message uses the documented root constant", () => {
  const data = loadFixture("conversation_tree.json");
  const ROOT_CONST = "00000000-0000-4000-8000-000000000000";
  const roots = data.chat_messages.filter((m) => m.parent_message_uuid === ROOT_CONST);
  assert.equal(roots.length, 1, "exactly one message should be the root");
});

test("conversation_tree.json contains a branch point (one parent with two children)", () => {
  const data = loadFixture("conversation_tree.json");
  const byParent = {};
  for (const m of data.chat_messages) {
    byParent[m.parent_message_uuid] = (byParent[m.parent_message_uuid] || 0) + 1;
  }
  const branchCounts = Object.values(byParent).filter((c) => c > 1);
  assert.equal(branchCounts.length, 1, "exactly one branch point expected");
});

test("conversation_tree.json contains a dead branch with empty content (user_canceled)", () => {
  const data = loadFixture("conversation_tree.json");
  const deadLeaves = data.chat_messages.filter(
    (m) => Array.isArray(m.content) && m.content.length === 0 && m.stop_reason === "user_canceled"
  );
  assert.equal(deadLeaves.length, 1, "exactly one empty-content user_canceled message expected");
});

test("conversation_tree.json content blocks cover all 4 known types", () => {
  const data = loadFixture("conversation_tree.json");
  const types = new Set();
  for (const m of data.chat_messages) {
    for (const block of m.content || []) {
      types.add(block.type);
    }
  }
  for (const expected of ["text", "thinking", "tool_use", "tool_result"]) {
    assert.ok(types.has(expected), `expected block type "${expected}" to be present`);
  }
});

test("conversation_pruned.json parses as JSON", () => {
  const data = loadFixture("conversation_pruned.json");
  assert.ok(Array.isArray(data.chat_messages));
});

test("conversation_pruned.json has a broken chain (a parent_message_uuid with no matching message)", () => {
  const data = loadFixture("conversation_pruned.json");
  const ROOT_CONST = "00000000-0000-4000-8000-000000000000";
  const existingUuids = new Set(data.chat_messages.map((m) => m.uuid));
  const dangling = data.chat_messages.filter(
    (m) => m.parent_message_uuid !== ROOT_CONST && !existingUuids.has(m.parent_message_uuid)
  );
  assert.ok(dangling.length > 0, "expected at least one message with a dangling parent_message_uuid");
});

test("organizations.json parses as JSON and matches the [{ uuid, ... }] hypothesis shape", () => {
  const data = loadFixture("organizations.json");
  assert.ok(Array.isArray(data), "organizations.json root must be an array");
  assert.ok(data.length > 0, "organizations.json must not be empty");
  for (const org of data) {
    assert.equal(typeof org.uuid, "string");
  }
});

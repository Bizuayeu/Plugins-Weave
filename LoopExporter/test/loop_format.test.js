// Domain tests for src/domain/loop_format.js (Stage 2, FR-4 / FR-7).
// Golden test wires message_tree.js + blocks.js + loop_format.js together over
// conversation_tree.json and compares the full rendered document byte-for-byte
// against test/fixtures/expected_loop.txt (synthetic content only -- no real
// Loop transcription; skeleton was confirmed by Read-only reference against
// L00551, see the task report).
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { buildMessageTree, resolveLeafPath } = require("../src/domain/message_tree.js");
const { convertMessage } = require("../src/domain/blocks.js");
const { renderLoopDocument, sanitizeFilename } = require("../src/domain/loop_format.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

test("renderLoopDocument matches the FR-4 skeleton exactly (golden test against expected_loop.txt)", () => {
  const data = loadFixture("conversation_tree.json");
  const tree = buildMessageTree(data.chat_messages);
  const leafPath = resolveLeafPath(tree, data.current_leaf_message_uuid);
  const convertedMessages = leafPath.map((msg) => convertMessage(msg).text);
  const counts = {
    human: leafPath.filter((m) => m.sender === "human").length,
    assistant: leafPath.filter((m) => m.sender === "assistant").length,
  };

  const output = renderLoopDocument({
    conversation: data,
    path: leafPath,
    convertedMessages,
    counts,
    meta: { extractedAt: "2026-07-16T12:00:00.000Z", exporterVersion: "0.1.0" },
  });

  const expected = fs.readFileSync(path.join(FIXTURES_DIR, "expected_loop.txt"), "utf8");
  assert.equal(output, expected);
});

test("renderLoopDocument uses /chat/{uuid} as Source, never /share/", () => {
  const conversation = { uuid: "cccccccc-0000-4000-8000-000000000099" };
  const humanMsg = { sender: "human" };
  const output = renderLoopDocument({
    conversation,
    path: [humanMsg],
    convertedMessages: ["hello"],
    counts: { human: 1, assistant: 0 },
    meta: { extractedAt: "2026-01-01T00:00:00.000Z", exporterVersion: "0.1.0" },
  });
  assert.match(output, /Source: \[Claude Chat\]\(https:\/\/claude\.ai\/chat\/cccccccc-0000-4000-8000-000000000099\)/);
  assert.ok(!output.includes("/share/"));
});

test("renderLoopDocument maps human -> ## User and assistant -> ## Claude in isolation", () => {
  const output = renderLoopDocument({
    conversation: { uuid: "u" },
    path: [{ sender: "human" }, { sender: "assistant" }],
    convertedMessages: ["hi", "hello back"],
    counts: { human: 1, assistant: 1 },
    meta: { extractedAt: "2026-01-01T00:00:00.000Z", exporterVersion: "0.1.0" },
  });
  const userIdx = output.indexOf("## User");
  const claudeIdx = output.indexOf("## Claude");
  assert.ok(userIdx !== -1 && claudeIdx !== -1);
  assert.ok(userIdx < claudeIdx);
});

test("renderLoopDocument throws if path and convertedMessages lengths disagree", () => {
  assert.throws(() => {
    renderLoopDocument({
      conversation: { uuid: "u" },
      path: [{ sender: "human" }, { sender: "assistant" }],
      convertedMessages: ["only one"],
      counts: { human: 1, assistant: 1 },
      meta: { extractedAt: "2026-01-01T00:00:00.000Z", exporterVersion: "0.1.0" },
    });
  }, /same length/i);
});

test("sanitizeFilename builds L{number}_{title}.txt and strips illegal filesystem characters", () => {
  assert.equal(sanitizeFilename("00554", 'A/B\\C<D>E:F"G|H?I*J'), "L00554_ABCDEFGHIJ.txt");
});

test("sanitizeFilename collapses and trims whitespace to underscores", () => {
  assert.equal(sanitizeFilename("00002", "  multiple   spaces  "), "L00002_multiple_spaces.txt");
});

test("sanitizeFilename passes through a synthetic Japanese title unchanged", () => {
  assert.equal(sanitizeFilename("00099", "テスト用タイトル例"), "L00099_テスト用タイトル例.txt");
});

test("sanitizeFilename does not crash when the title is entirely illegal characters", () => {
  assert.equal(sanitizeFilename("00100", "???"), "L00100_.txt");
});

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
const { renderLoopDocument, sanitizeFilename, parseLoopNumberInput } = require("../src/domain/loop_format.js");

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

test("sanitizeFilename normalizes a leading L/l on the loop number instead of doubling it (LL00551 bug)", () => {
  assert.equal(sanitizeFilename("L00551", "タイトル"), "L00551_タイトル.txt");
  assert.equal(sanitizeFilename("l00551", "タイトル"), "L00551_タイトル.txt");
  assert.equal(sanitizeFilename(" L00551 ", "タイトル"), "L00551_タイトル.txt");
});

test("parseLoopNumberInput: a bare number (with or without leading L) carries no title override", () => {
  assert.deepEqual(parseLoopNumberInput("L00556"), { loopNumber: "L00556", titleOverride: null });
  assert.deepEqual(parseLoopNumberInput("00556"), { loopNumber: "00556", titleOverride: null });
});

test("parseLoopNumberInput: L{number}_{title} splits at the first underscore into number and title override", () => {
  assert.deepEqual(parseLoopNumberInput("L00556_自作タイトル"), {
    loopNumber: "L00556",
    titleOverride: "自作タイトル",
  });
  assert.deepEqual(parseLoopNumberInput("00556_タイトル"), {
    loopNumber: "00556",
    titleOverride: "タイトル",
  });
});

test("parseLoopNumberInput: underscores inside the title are preserved (split at the FIRST underscore only)", () => {
  assert.deepEqual(parseLoopNumberInput("L00556_A_B"), { loopNumber: "L00556", titleOverride: "A_B" });
});

test("parseLoopNumberInput: a trailing underscore with no title is NOT an override (typo-safe: falls back to the session name)", () => {
  assert.deepEqual(parseLoopNumberInput("L00556_"), { loopNumber: "L00556", titleOverride: null });
  assert.deepEqual(parseLoopNumberInput("L00556_   "), { loopNumber: "L00556", titleOverride: null });
});

test("parseLoopNumberInput: blank / null input yields a blank loop number (caller treats it as cancel)", () => {
  assert.deepEqual(parseLoopNumberInput(null), { loopNumber: "", titleOverride: null });
  assert.deepEqual(parseLoopNumberInput(""), { loopNumber: "", titleOverride: null });
  assert.deepEqual(parseLoopNumberInput("   "), { loopNumber: "", titleOverride: null });
});

test("parseLoopNumberInput: a title with no number yields a blank loop number (caller treats it as cancel -- numbering stays human)", () => {
  assert.deepEqual(parseLoopNumberInput("_タイトルのみ"), { loopNumber: "", titleOverride: "タイトルのみ" });
});

test("parseLoopNumberInput: surrounding whitespace is trimmed from both parts", () => {
  assert.deepEqual(parseLoopNumberInput("  L00556_題名  "), { loopNumber: "L00556", titleOverride: "題名" });
});

test("parseLoopNumberInput composes with sanitizeFilename: the override becomes the filename title verbatim-sanitized", () => {
  const parsed = parseLoopNumberInput("L00556_自作の題名");
  assert.equal(sanitizeFilename(parsed.loopNumber, parsed.titleOverride), "L00556_自作の題名.txt");
});

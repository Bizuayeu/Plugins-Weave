// Adapter tests for src/adapter/loop_file_presenter.js (Stage 3).
// presentLoopFile is a thin bundle of Domain's renderLoopDocument +
// sanitizeFilename; these tests confirm the bundle produces byte-identical output
// to calling the two Domain functions directly, and that conversation.name feeds
// the filename title (FR-7 prefill) while loopNumber passes through verbatim
// (never inferred).
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { buildMessageTree, resolveLeafPath } = require("../src/domain/message_tree.js");
const { convertMessage } = require("../src/domain/blocks.js");
const { renderLoopDocument, sanitizeFilename } = require("../src/domain/loop_format.js");
const { presentLoopFile } = require("../src/adapter/loop_file_presenter.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

function buildLeafPathArgs(data) {
  const tree = buildMessageTree(data.chat_messages);
  const leafPath = resolveLeafPath(tree, data.current_leaf_message_uuid);
  const convertedMessages = leafPath.map((msg) => convertMessage(msg).text);
  const counts = {
    human: leafPath.filter((m) => m.sender === "human").length,
    assistant: leafPath.filter((m) => m.sender === "assistant").length,
  };
  return { path: leafPath, convertedMessages, counts };
}

test("presentLoopFile produces text byte-identical to calling renderLoopDocument directly", () => {
  const data = loadFixture("conversation_tree.json");
  const { path: leafPath, convertedMessages, counts } = buildLeafPathArgs(data);
  const meta = { extractedAt: "2026-07-16T12:00:00.000Z", exporterVersion: "0.1.0" };

  const direct = renderLoopDocument({ conversation: data, path: leafPath, convertedMessages, counts, meta });
  const { text } = presentLoopFile({
    conversation: data,
    path: leafPath,
    convertedMessages,
    counts,
    meta,
    loopNumber: "00553",
  });

  assert.equal(text, direct);

  const expected = fs.readFileSync(path.join(FIXTURES_DIR, "expected_loop.txt"), "utf8");
  assert.equal(text, expected);
});

test("presentLoopFile derives the filename from conversation.name via sanitizeFilename, verbatim loopNumber", () => {
  const data = loadFixture("conversation_tree.json");
  const { path: leafPath, convertedMessages, counts } = buildLeafPathArgs(data);
  const meta = { extractedAt: "2026-07-16T12:00:00.000Z", exporterVersion: "0.1.0" };

  const { filename } = presentLoopFile({
    conversation: data,
    path: leafPath,
    convertedMessages,
    counts,
    meta,
    loopNumber: "00553",
  });

  assert.equal(filename, sanitizeFilename("00553", data.name));
  assert.equal(filename, "L00553_Example_placeholder_conversation.txt");
});

test("presentLoopFile: an explicit titleOverride replaces conversation.name in the filename (text untouched)", () => {
  const data = loadFixture("conversation_tree.json");
  const { path: leafPath, convertedMessages, counts } = buildLeafPathArgs(data);
  const meta = { extractedAt: "2026-07-16T12:00:00.000Z", exporterVersion: "0.1.0" };

  const { filename, text } = presentLoopFile({
    conversation: data,
    path: leafPath,
    convertedMessages,
    counts,
    meta,
    loopNumber: "00553",
    titleOverride: "上書き題名",
  });

  assert.equal(filename, "L00553_上書き題名.txt");
  assert.equal(text, renderLoopDocument({ conversation: data, path: leafPath, convertedMessages, counts, meta }));
});

test("presentLoopFile never invents a loop number -- an unusual verbatim value passes straight through", () => {
  const data = loadFixture("conversation_tree.json");
  const { path: leafPath, convertedMessages, counts } = buildLeafPathArgs(data);
  const meta = { extractedAt: "2026-01-01T00:00:00.000Z", exporterVersion: "0.1.0" };

  const { filename } = presentLoopFile({
    conversation: data,
    path: leafPath,
    convertedMessages,
    counts,
    meta,
    loopNumber: "not-a-real-number-42",
  });

  assert.ok(filename.startsWith("Lnot-a-real-number-42_"));
});

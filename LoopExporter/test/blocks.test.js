// Domain tests for src/domain/blocks.js (Stage 2, FR-5 default-column rules).
// text passthrough (citations dropped) / tool_use+tool_result dedup / thinking
// excluded / unknown type preserved with a warning / files[] annotated.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { convertBlocks, formatFileAnnotations, convertMessage } = require("../src/domain/blocks.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

function findMessage(data, uuid) {
  const msg = data.chat_messages.find((m) => m.uuid === uuid);
  assert.ok(msg, `fixture message ${uuid} must exist`);
  return msg;
}

test("convertBlocks keeps text blocks as-is and drops citations (body only)", () => {
  const data = loadFixture("conversation_tree.json");
  const msg = findMessage(data, "bbbbbbbb-0000-4000-8000-000000000001");
  const result = convertBlocks(msg.content);
  assert.equal(result.text, "Please summarize the attached status report and list open action items.");
  assert.deepEqual(result.warnings, []);
});

test("convertBlocks excludes thinking blocks entirely", () => {
  const data = loadFixture("conversation_tree.json");
  const msg = findMessage(data, "bbbbbbbb-0000-4000-8000-000000000002");
  const result = convertBlocks(msg.content);
  assert.ok(!result.text.includes("Considering how to best structure"));
  assert.equal(result.text, "Sure -- here is a structured summary of the three sections in the report.");
});

test("convertBlocks summarizes a tool_use/tool_result pair as a single non-duplicated line", () => {
  const data = loadFixture("conversation_tree.json");
  const msg = findMessage(data, "bbbbbbbb-0000-4000-8000-000000000004");
  const result = convertBlocks(msg.content);

  const toolLineMatches = result.text.match(/\[tool: web_search\]/g) || [];
  assert.equal(toolLineMatches.length, 1, "the web_search tool line must appear exactly once");
  assert.ok(result.text.includes("I searched for related background material"));
});

test("convertBlocks preserves an unknown block type as raw JSON and records a warning", () => {
  const fabricated = [
    { type: "text", text: "Before the unknown block.", citations: [] },
    { type: "mystery_block", foo: "bar", nested: { baz: 1 } },
  ];
  const result = convertBlocks(fabricated);
  assert.match(result.text, /"type":"mystery_block"/);
  assert.match(result.text, /"foo":"bar"/);
  assert.equal(result.warnings.length, 1);
  assert.match(result.warnings[0], /unknown/i);
  assert.match(result.warnings[0], /mystery_block/);
});

test("convertBlocks handles an orphan tool_use (no matching tool_result) without crashing", () => {
  const fabricated = [
    {
      type: "tool_use",
      id: "toolu_orphan",
      name: "bash_tool",
      input: {},
    },
  ];
  const result = convertBlocks(fabricated);
  assert.equal(result.text, "[tool: bash_tool]");
});

test("convertBlocks handles an orphan tool_result (no matching tool_use) as its own line", () => {
  const fabricated = [
    {
      type: "tool_result",
      tool_use_id: "toolu_never_seen",
      name: "web_fetch",
      content: [],
    },
  ];
  const result = convertBlocks(fabricated);
  assert.equal(result.text, "[tool: web_fetch]");
});

test("convertBlocks returns empty text and no warnings for an empty content array", () => {
  const result = convertBlocks([]);
  assert.equal(result.text, "");
  assert.deepEqual(result.warnings, []);
});

test("formatFileAnnotations returns one [file: name] line per file, empty array when none", () => {
  const data = loadFixture("conversation_tree.json");
  const msg = findMessage(data, "bbbbbbbb-0000-4000-8000-000000000001");
  assert.deepEqual(formatFileAnnotations(msg.files), ["[file: example-status-report.docx]"]);
  assert.deepEqual(formatFileAnnotations([]), []);
  assert.deepEqual(formatFileAnnotations(undefined), []);
});

test("convertMessage composes block conversion and file annotations for a full message", () => {
  const data = loadFixture("conversation_tree.json");
  const msg = findMessage(data, "bbbbbbbb-0000-4000-8000-000000000001");
  const result = convertMessage(msg);
  assert.equal(
    result.text,
    "Please summarize the attached status report and list open action items.\n\n[file: example-status-report.docx]"
  );
  assert.deepEqual(result.warnings, []);
});

test("convertMessage with no files omits the file annotation entirely", () => {
  const data = loadFixture("conversation_tree.json");
  const msg = findMessage(data, "bbbbbbbb-0000-4000-8000-000000000003");
  const result = convertMessage(msg);
  assert.equal(result.text, "Also check reference-file-01 and search for related background material.");
});

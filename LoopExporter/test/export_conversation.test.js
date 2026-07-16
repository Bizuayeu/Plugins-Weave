// UseCase tests for src/usecase/export_conversation.js (Stage 3).
// Wires the REAL claude_api_gateway.js (Adapter) with a mock fetch to exercise a
// true end-to-end cycle -- fetch -> gateway mapping -> tree -> verify -> convert
// -> render -> save -- matching "一巡ゴールデン" from IMPLEMENTATION_PLAN Stage 3.
// No real network access anywhere in this file (絶対規約 #2).
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { exportConversation, IntegrityError } = require("../src/usecase/export_conversation.js");
const { createClaudeApiGateway, SessionExpiredError } = require("../src/adapter/claude_api_gateway.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");
const FIXED_CLOCK = () => "2026-07-16T12:00:00.000Z";
const EXPORTER_VERSION = "0.1.0";

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

/** Dispatches by URL substring, same convention as claude_api_gateway.test.js. */
function createDispatchFetch({ orgBody, orgStatus = 200, conversationBody, conversationStatus = 200 }) {
  return async (url) => {
    if (url.includes("chat_conversations")) {
      return jsonResponse(conversationStatus, conversationBody);
    }
    return jsonResponse(orgStatus, orgBody);
  };
}

function createSaverSpy() {
  const calls = [];
  const saver = async (args) => {
    calls.push(args);
  };
  saver.calls = calls;
  return saver;
}

test("exportConversation: golden one-cycle -- fetch -> convert -> save, text matches expected_loop.txt exactly", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn, baseUrl: "https://claude.ai" });
  const saver = createSaverSpy();

  const result = await exportConversation({
    gateway,
    saver,
    promptLoopNumber: () => "00553",
    clock: FIXED_CLOCK,
    exporterVersion: EXPORTER_VERSION,
    chatId: conv.uuid,
  });

  const expectedText = fs.readFileSync(path.join(FIXTURES_DIR, "expected_loop.txt"), "utf8");

  assert.equal(saver.calls.length, 1, "saver must be called exactly once on the happy path");
  assert.equal(saver.calls[0].text, expectedText);
  assert.equal(saver.calls[0].filename, "L00553_Example_placeholder_conversation.txt");

  assert.equal(result.cancelled, false);
  assert.equal(result.filename, "L00553_Example_placeholder_conversation.txt");
  assert.deepEqual(result.warnings, []);
  assert.deepEqual(result.counts, { human: 3, assistant: 3 });
  assert.equal(result.freshness, "2026-01-15T09:05:09.000Z");
});

test("exportConversation: fail-closed -- IntegrityError is thrown and saver is never called (AC-3 core, UseCase layer)", async () => {
  const org = loadFixture("organizations.json");
  const pruned = loadFixture("conversation_pruned.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: pruned });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  await assert.rejects(
    () =>
      exportConversation({
        gateway,
        saver,
        promptLoopNumber: () => "00554",
        clock: FIXED_CLOCK,
        exporterVersion: EXPORTER_VERSION,
        chatId: pruned.uuid,
      }),
    IntegrityError
  );

  assert.equal(saver.calls.length, 0, "saver must never be called when integrity verification fails");
});

test("exportConversation: IntegrityError carries the failures[] from verifyIntegrity for the UI to display", async () => {
  const org = loadFixture("organizations.json");
  const pruned = loadFixture("conversation_pruned.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: pruned });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  await assert.rejects(
    () =>
      exportConversation({
        gateway,
        saver,
        promptLoopNumber: () => "00554",
        clock: FIXED_CLOCK,
        exporterVersion: EXPORTER_VERSION,
        chatId: pruned.uuid,
      }),
    (err) => {
      assert.ok(err instanceof IntegrityError);
      assert.ok(err.failures.length > 0);
      assert.ok(err.failures.some((f) => /dangling/i.test(f)));
      return true;
    }
  );
});

test("exportConversation: an HTTP error from the gateway (e.g. session expiry) propagates and saver is never called", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv, conversationStatus: 401 });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  await assert.rejects(
    () =>
      exportConversation({
        gateway,
        saver,
        promptLoopNumber: () => "00555",
        clock: FIXED_CLOCK,
        exporterVersion: EXPORTER_VERSION,
        chatId: conv.uuid,
      }),
    SessionExpiredError
  );

  assert.equal(saver.calls.length, 0);
});

test("exportConversation: cancels cleanly (no saver call) when promptLoopNumber resolves to null", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  const result = await exportConversation({
    gateway,
    saver,
    promptLoopNumber: () => null,
    clock: FIXED_CLOCK,
    exporterVersion: EXPORTER_VERSION,
    chatId: conv.uuid,
  });

  assert.deepEqual(result, { cancelled: true });
  assert.equal(saver.calls.length, 0);
});

test("exportConversation: cancels cleanly (no saver call) when promptLoopNumber resolves to a blank string", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  const result = await exportConversation({
    gateway,
    saver,
    promptLoopNumber: () => "   ",
    clock: FIXED_CLOCK,
    exporterVersion: EXPORTER_VERSION,
    chatId: conv.uuid,
  });

  assert.deepEqual(result, { cancelled: true });
  assert.equal(saver.calls.length, 0);
});

test("exportConversation: merges the gateway's unknown-field warnings into its own returned warnings", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  conv.mystery_top_level_field = "surprise";
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  const result = await exportConversation({
    gateway,
    saver,
    promptLoopNumber: () => "00556",
    clock: FIXED_CLOCK,
    exporterVersion: EXPORTER_VERSION,
    chatId: conv.uuid,
  });

  assert.ok(result.warnings.some((w) => /mystery_top_level_field/.test(w)));
});

test("exportConversation: merges convertMessage's block-level warnings (unknown content type) into its own returned warnings", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const msg0004 = conv.chat_messages.find((m) => m.uuid === "bbbbbbbb-0000-4000-8000-000000000004");
  msg0004.content.push({ type: "mystery_widget", foo: "bar" });
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });
  const saver = createSaverSpy();

  const result = await exportConversation({
    gateway,
    saver,
    promptLoopNumber: () => "00557",
    clock: FIXED_CLOCK,
    exporterVersion: EXPORTER_VERSION,
    chatId: conv.uuid,
  });

  assert.ok(result.warnings.some((w) => /mystery_widget/.test(w)));
  assert.equal(saver.calls.length, 1, "a block-level warning must not block the save (warning, not failure)");
});

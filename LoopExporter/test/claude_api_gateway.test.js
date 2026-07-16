// Adapter tests for src/adapter/claude_api_gateway.js (Stage 3, FR-2 / NFR-2 /
// NFR-3 / §9.4). All fetch calls are mocked in-process -- no real network access
// (絶対規約 #2).
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { createClaudeApiGateway, SessionExpiredError, ApiDriftError } = require("../src/adapter/claude_api_gateway.js");

const FIXTURES_DIR = path.join(__dirname, "fixtures");

function loadFixture(name) {
  const raw = fs.readFileSync(path.join(FIXTURES_DIR, name), "utf8");
  return JSON.parse(raw);
}

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

function brokenJsonResponse(status) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => {
      throw new SyntaxError("Unexpected token in JSON");
    },
  };
}

/**
 * Dispatches by URL substring: requests containing "chat_conversations" hit the
 * conversation endpoint double; everything else (GET /api/organizations) hits the
 * org endpoint double. Records every call for URL/opts assertions.
 */
function createDispatchFetch({
  orgBody,
  orgStatus = 200,
  brokenOrgJson = false,
  conversationBody,
  conversationStatus = 200,
  brokenConversationJson = false,
}) {
  const calls = [];
  const fetchFn = async (url, opts) => {
    calls.push({ url, opts });
    if (url.includes("chat_conversations")) {
      return brokenConversationJson ? brokenJsonResponse(conversationStatus) : jsonResponse(conversationStatus, conversationBody);
    }
    return brokenOrgJson ? brokenJsonResponse(orgStatus) : jsonResponse(orgStatus, orgBody);
  };
  fetchFn.calls = calls;
  return fetchFn;
}

test("fetchConversation calls the real observed URL shape and passes credentials: include", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn, baseUrl: "https://claude.ai" });

  await gateway.fetchConversation("some-chat-id");

  const orgCall = fetchFn.calls.find((c) => !c.url.includes("chat_conversations"));
  const convCall = fetchFn.calls.find((c) => c.url.includes("chat_conversations"));

  assert.equal(orgCall.url, "https://claude.ai/api/organizations");
  assert.deepEqual(orgCall.opts, { credentials: "include" });

  assert.equal(
    convCall.url,
    `https://claude.ai/api/organizations/${org[0].uuid}/chat_conversations/some-chat-id` +
      "?tree=True&rendering_mode=messages&render_all_tools=true&consistency=strong"
  );
  assert.deepEqual(convCall.opts, { credentials: "include" });
});

test("fetchConversation returns a clean mapped conversation with zero warnings for a fully-known fixture", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });

  const { conversation, warnings } = await gateway.fetchConversation(conv.uuid);

  assert.deepEqual(warnings, []);
  assert.equal(conversation.uuid, conv.uuid);
  assert.equal(conversation.name, conv.name);
  assert.equal(conversation.current_leaf_message_uuid, conv.current_leaf_message_uuid);
  assert.equal(conversation.chat_messages.length, conv.chat_messages.length);
});

test("getOrganizationId is fetched once and cached across repeated fetchConversation calls", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });

  await gateway.fetchConversation("chat-1");
  await gateway.fetchConversation("chat-2");

  const orgCalls = fetchFn.calls.filter((c) => !c.url.includes("chat_conversations"));
  assert.equal(orgCalls.length, 1, "GET /api/organizations must be called exactly once, not once per fetchConversation");
});

test("getOrganizationId resolves the first organization's uuid", async () => {
  const org = loadFixture("organizations.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: {} });
  const gateway = createClaudeApiGateway({ fetchFn });

  const orgId = await gateway.getOrganizationId();
  assert.equal(orgId, org[0].uuid);
});

test("fetchConversation warns (not fails) on an unknown top-level field, and still returns the conversation", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  conv.mystery_top_level_field = "surprise";
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });

  const { conversation, warnings } = await gateway.fetchConversation(conv.uuid);

  assert.ok(warnings.some((w) => /mystery_top_level_field/.test(w)));
  assert.equal(conversation.uuid, conv.uuid, "a warning must not block the mapped conversation from being returned");
});

test("fetchConversation warns on an unknown field inside a chat_messages[] element", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  conv.chat_messages[0].mystery_msg_field = 42;
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });

  const { warnings } = await gateway.fetchConversation(conv.uuid);

  assert.ok(warnings.some((w) => /mystery_msg_field/.test(w) && w.includes(conv.chat_messages[0].uuid)));
});

test("fetchConversation does not re-check content[] block types (blocks.js already owns that per NFR-3)", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  conv.chat_messages[0].content.push({ type: "mystery_block", foo: "bar" });
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });

  const { warnings } = await gateway.fetchConversation(conv.uuid);

  assert.ok(
    !warnings.some((w) => /mystery_block/.test(w)),
    "content[]-level unknown types must not be double-checked by the gateway"
  );
});

test("fetchConversation throws ApiDriftError when a required field is missing (chat_messages)", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  delete conv.chat_messages;
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv });
  const gateway = createClaudeApiGateway({ fetchFn });

  await assert.rejects(() => gateway.fetchConversation(conv.uuid), ApiDriftError);
});

test("fetchConversation throws ApiDriftError when the response body is not valid JSON", async () => {
  const org = loadFixture("organizations.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: null, brokenConversationJson: true });
  const gateway = createClaudeApiGateway({ fetchFn });

  await assert.rejects(() => gateway.fetchConversation("chat-x"), ApiDriftError);
});

test("fetchConversation classifies HTTP 401 and 403 as SessionExpiredError (session-expiry family, §9.4)", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");

  for (const status of [401, 403]) {
    const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv, conversationStatus: status });
    const gateway = createClaudeApiGateway({ fetchFn });
    await assert.rejects(
      () => gateway.fetchConversation(conv.uuid),
      SessionExpiredError,
      `status ${status} must classify as SessionExpiredError`
    );
  }
});

test("fetchConversation classifies HTTP 404 and 500 as ApiDriftError (API-change family, §9.4)", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");

  for (const status of [404, 500]) {
    const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv, conversationStatus: status });
    const gateway = createClaudeApiGateway({ fetchFn });
    await assert.rejects(
      () => gateway.fetchConversation(conv.uuid),
      ApiDriftError,
      `status ${status} must classify as ApiDriftError`
    );
  }
});

test("getOrganizationId classifies HTTP 401 as SessionExpiredError too (shared classification helper)", async () => {
  const fetchFn = createDispatchFetch({ orgBody: {}, orgStatus: 401, conversationBody: {} });
  const gateway = createClaudeApiGateway({ fetchFn });

  await assert.rejects(() => gateway.getOrganizationId(), SessionExpiredError);
});

test("getOrganizationId throws ApiDriftError when the response does not match the [{uuid,...}] shape", async () => {
  const fetchFn = createDispatchFetch({ orgBody: [], conversationBody: {} }); // empty array
  const gateway = createClaudeApiGateway({ fetchFn });

  await assert.rejects(() => gateway.getOrganizationId(), ApiDriftError);
});

test("errors carry a .status and .code for UI branching", async () => {
  const org = loadFixture("organizations.json");
  const conv = loadFixture("conversation_tree.json");
  const fetchFn = createDispatchFetch({ orgBody: org, conversationBody: conv, conversationStatus: 403 });
  const gateway = createClaudeApiGateway({ fetchFn });

  await assert.rejects(
    () => gateway.fetchConversation(conv.uuid),
    (err) => {
      assert.equal(err.code, "SESSION_EXPIRED");
      assert.equal(err.status, 403);
      return true;
    }
  );
});

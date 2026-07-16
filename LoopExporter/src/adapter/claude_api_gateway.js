// Adapter: claude.ai internal JSON API gateway (FR-2, NFR-2, NFR-3, §9.4).
// Owns the ONLY mapping from the real API response shape to the Domain-facing
// intermediate representation (NFR-2 "変換を単一モジュールに隔離" -- when the API
// drifts, this is the one file to repair). fetch is injected (fetchFn) so this
// module never references a global fetch and stays fixture-testable from node:test;
// it does not import chrome.* or touch the DOM.
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

// docs/SCHEMA_NOTES.md §3.1 / §3.2 -- the field sets actually observed on the real
// endpoint. Anything outside these sets is reported as a warning, never silently
// dropped (NFR-3). content[]-level unknown block types are already handled by
// src/domain/blocks.js (which preserves+warns), so they are intentionally NOT
// re-checked here -- checking them twice would just double the warning noise.
const KNOWN_TOP_LEVEL_FIELDS = new Set([
  "uuid",
  "name",
  "summary",
  "model",
  "created_at",
  "updated_at",
  "settings",
  "is_starred",
  "is_temporary",
  "project_uuid",
  "platform",
  "is_wiggle_enabled",
  "effective_thinking_mode",
  "current_leaf_message_uuid",
  "chat_messages",
]);

const KNOWN_MESSAGE_FIELDS = new Set([
  "uuid",
  "text",
  "content",
  "sender",
  "index",
  "created_at",
  "updated_at",
  "truncated",
  "attachments",
  "files",
  "sync_sources",
  "parent_message_uuid",
  "stop_reason", // assistant-only, per SCHEMA_NOTES §3.2, but still a known field
]);

/**
 * §9.4 first-triage bucket 1: HTTP 401/403. The UI should suggest re-login to
 * claude.ai and retry.
 */
class SessionExpiredError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "SessionExpiredError";
    this.code = "SESSION_EXPIRED";
    this.status = status;
  }
}

/**
 * §9.4 first-triage bucket 2: HTTP 404/5xx, a malformed JSON body, or a missing
 * required field. The UI should suggest the fixture-diff repair path (re-capture
 * via docs/SCHEMA_NOTES.md §1 and diff).
 */
class ApiDriftError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiDriftError";
    this.code = "API_DRIFT";
    this.status = status;
  }
}

function errorClassForStatus(status) {
  return status === 401 || status === 403 ? SessionExpiredError : ApiDriftError;
}

async function parseJsonOrThrow(response, url) {
  try {
    return await response.json();
  } catch (err) {
    throw new ApiDriftError(`GET ${url}: response body is not valid JSON (${err.message}).`, response.status);
  }
}

/**
 * @param {Object} obj
 * @param {Set<string>} knownFields
 * @param {string} label - human-readable description of obj, used in the warning text
 * @returns {string[]}
 */
function collectUnknownFieldWarnings(obj, knownFields, label) {
  const warnings = [];
  for (const key of Object.keys(obj || {})) {
    if (!knownFields.has(key)) {
      warnings.push(`Unknown field "${key}" on ${label} -- kept out of the mapped conversation, not silently dropped.`);
    }
  }
  return warnings;
}

/**
 * @typedef {Object} MappedConversation
 * @property {string} uuid
 * @property {string} [name]
 * @property {string} current_leaf_message_uuid
 * @property {Array<Object>} chat_messages
 */

/**
 * @typedef {Object} FetchConversationResult
 * @property {MappedConversation} conversation
 * @property {string[]} warnings
 */

/**
 * @param {Object} params
 * @param {function(string, Object): Promise<{ok: boolean, status: number, json: function(): Promise<*>}>} params.fetchFn
 *   Injected, browser-fetch-shaped function. Real caller (content.js) passes the
 *   real `fetch`; tests pass a mock that never leaves the process (絶対規約 #2).
 * @param {string} [params.baseUrl] - defaults to "https://claude.ai"
 */
function createClaudeApiGateway(params) {
  const { fetchFn, baseUrl } = params;
  const base = baseUrl || "https://claude.ai";
  let cachedOrgId = null;

  /**
   * FR-2: resolves the org id via `GET /api/organizations`, caching it in an
   * instance-local variable after the first successful call (chrome.storage is
   * deliberately not used -- see IMPLEMENTATION_PLAN.md Stage 3 notes: minimal
   * solution, no Adapter-layer chrome.* dependency).
   * @returns {Promise<string>}
   */
  async function getOrganizationId() {
    if (cachedOrgId) return cachedOrgId;

    const url = `${base}/api/organizations`;
    const response = await fetchFn(url, { credentials: "include" });
    if (!response.ok) {
      const ErrorClass = errorClassForStatus(response.status);
      throw new ErrorClass(`GET ${url} failed with HTTP ${response.status}.`, response.status);
    }
    const data = await parseJsonOrThrow(response, url);
    if (!Array.isArray(data) || data.length === 0 || !data[0] || typeof data[0].uuid !== "string") {
      throw new ApiDriftError(`GET ${url}: response did not match the expected [{uuid, ...}] shape.`, response.status);
    }

    cachedOrgId = data[0].uuid;
    return cachedOrgId;
  }

  /**
   * Fetches one conversation tree (real URL confirmed in docs/SCHEMA_NOTES.md §2:
   * tree=True&rendering_mode=messages&render_all_tools=true&consistency=strong)
   * and maps it to the Domain-facing intermediate representation. This function is
   * the single place that knows the real response shape (NFR-2).
   * @param {string} chatId - from the `/chat/{uuid}` URL path (FR-1)
   * @returns {Promise<FetchConversationResult>}
   */
  async function fetchConversation(chatId) {
    const orgId = await getOrganizationId();
    const url =
      `${base}/api/organizations/${orgId}/chat_conversations/${chatId}` +
      "?tree=True&rendering_mode=messages&render_all_tools=true&consistency=strong";

    const response = await fetchFn(url, { credentials: "include" });
    if (!response.ok) {
      const ErrorClass = errorClassForStatus(response.status);
      throw new ErrorClass(`GET ${url} failed with HTTP ${response.status}.`, response.status);
    }
    const raw = await parseJsonOrThrow(response, url);

    if (
      !raw ||
      typeof raw.uuid !== "string" ||
      typeof raw.current_leaf_message_uuid !== "string" ||
      !Array.isArray(raw.chat_messages)
    ) {
      throw new ApiDriftError(
        `GET ${url}: response is missing a required field (uuid / current_leaf_message_uuid / chat_messages).`,
        response.status
      );
    }

    const warnings = collectUnknownFieldWarnings(raw, KNOWN_TOP_LEVEL_FIELDS, "the conversation (top-level)");
    raw.chat_messages.forEach((msg, i) => {
      warnings.push(
        ...collectUnknownFieldWarnings(msg, KNOWN_MESSAGE_FIELDS, `chat_messages[${i}] (uuid: ${msg && msg.uuid})`)
      );
    });

    const conversation = {
      uuid: raw.uuid,
      name: raw.name,
      current_leaf_message_uuid: raw.current_leaf_message_uuid,
      chat_messages: raw.chat_messages,
    };

    return { conversation, warnings };
  }

  return { getOrganizationId, fetchConversation };
}

Fuhito.claudeApiGateway = { createClaudeApiGateway, SessionExpiredError, ApiDriftError };

if (typeof module !== "undefined") {
  module.exports = Fuhito.claudeApiGateway;
}
})();

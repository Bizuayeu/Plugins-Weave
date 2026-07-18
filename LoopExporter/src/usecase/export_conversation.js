// UseCase: fail-closed orchestration of one export cycle (FR-2/FR-3/FR-5/FR-6/FR-7).
// Depends on Domain only -- no fetch / chrome.* / DOM. gateway, saver,
// promptLoopNumber and clock are all injected by the caller (content.js in Stage
// 4), which is what keeps this module fixture-testable and free of any concrete
// Adapter/Infrastructure import (Testability first, per dev-rules Decision
// Priority). In particular this module never calls Date.now() itself -- the
// caller injects `clock`, which is what makes the golden-output test
// deterministic.
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

const messageTreeModule =
  typeof module !== "undefined" ? require("../domain/message_tree.js") : Fuhito.messageTree;
const blocksModule = typeof module !== "undefined" ? require("../domain/blocks.js") : Fuhito.blocks;
const integrityModule =
  typeof module !== "undefined" ? require("../domain/integrity.js") : Fuhito.integrity;
const loopFormatModule =
  typeof module !== "undefined" ? require("../domain/loop_format.js") : Fuhito.loopFormat;

/**
 * Thrown when FR-6's verifyIntegrity reports ok:false. Carries the structured
 * failure/warning/count/freshness data so the UI (Stage 4) can render diagnostics
 * without re-deriving them. Export always stops here -- saver is never invoked
 * once this is thrown (this is the UseCase-layer half of FR-6's "ファイルを出力
 * せずエラー表示で停止"; src/domain/integrity.js itself never throws).
 */
class IntegrityError extends Error {
  constructor(integrityResult) {
    const failures = integrityResult.failures;
    super(`Fuhito: integrity verification failed -- ${failures.join(" / ")}`);
    this.name = "IntegrityError";
    this.failures = failures;
    this.warnings = integrityResult.warnings;
    this.counts = integrityResult.counts;
    this.freshness = integrityResult.freshness;
  }
}

/**
 * FR-7: a cancelled loop-number prompt (null, undefined, or blank/whitespace-only
 * string -- e.g. the user dismissed a `window.prompt()`-style dialog) must abort
 * the export without ever calling saver, exactly like a verification failure does.
 * @param {*} value
 * @returns {boolean}
 */
function isBlankLoopNumber(value) {
  return value === null || value === undefined || String(value).trim() === "";
}

/**
 * Orchestrates one export cycle end to end:
 * gateway.fetchConversation -> buildMessageTree -> verifyIntegrity (fail-closed:
 * throws IntegrityError and never calls saver when ok===false) -> resolveLeafPath
 * -> convertMessage per message -> promptLoopNumber -> parseLoopNumberInput
 * (cancel-safe: returns without calling saver when the number part is blank;
 * a "L{番号}_{タイトル}" input's title overrides conversation.name, FR-7)
 * -> renderLoopDocument + sanitizeFilename -> saver.
 *
 * @param {Object} params
 * @param {{fetchConversation: function(string): Promise<{conversation: Object, warnings: string[]}>}} params.gateway
 *   Duck-typed Adapter interface (see src/adapter/claude_api_gateway.js for the
 *   real implementation) -- injected so this module has zero static Adapter import.
 * @param {function({filename: string, text: string}): (void|Promise<void>)} params.saver
 * @param {function(): (string|null|undefined|Promise<string|null|undefined>)} params.promptLoopNumber
 * @param {function(): string} params.clock - returns an ISO8601 "Extracted" timestamp
 * @param {string} params.exporterVersion - e.g. "0.1.0"
 * @param {string} params.chatId - conversation id extracted from the `/chat/{uuid}` URL (FR-1)
 * @returns {Promise<
 *   {cancelled: true} |
 *   {cancelled: false, filename: string, warnings: string[], counts: {human: number, assistant: number}, freshness: string|null}
 * >}
 * @throws {IntegrityError} when FR-6 verification fails
 */
async function exportConversation(params) {
  const { gateway, saver, promptLoopNumber, clock, exporterVersion, chatId } = params;

  const { conversation, warnings: gatewayWarnings } = await gateway.fetchConversation(chatId);

  const tree = messageTreeModule.buildMessageTree(conversation.chat_messages);
  const integrityResult = integrityModule.verifyIntegrity(tree, conversation.current_leaf_message_uuid);

  if (!integrityResult.ok) {
    throw new IntegrityError(integrityResult);
  }

  const leafPath = messageTreeModule.resolveLeafPath(tree, conversation.current_leaf_message_uuid);
  const converted = leafPath.map((msg) => blocksModule.convertMessage(msg));
  const convertedMessages = converted.map((c) => c.text);
  const blockWarnings = converted.reduce((acc, c) => acc.concat(c.warnings), []);

  const rawLoopInput = await promptLoopNumber();
  const { loopNumber, titleOverride } = loopFormatModule.parseLoopNumberInput(rawLoopInput);
  if (isBlankLoopNumber(loopNumber)) {
    return { cancelled: true };
  }

  const text = loopFormatModule.renderLoopDocument({
    conversation,
    path: leafPath,
    convertedMessages,
    counts: integrityResult.counts,
    meta: { extractedAt: clock(), exporterVersion },
  });
  const filename = loopFormatModule.sanitizeFilename(
    loopNumber,
    titleOverride !== null ? titleOverride : conversation.name
  );

  await saver({ filename, text });

  return {
    cancelled: false,
    filename,
    warnings: [...gatewayWarnings, ...blockWarnings, ...integrityResult.warnings],
    counts: integrityResult.counts,
    freshness: integrityResult.freshness,
  };
}

Fuhito.exportConversation = { exportConversation, IntegrityError };

if (typeof module !== "undefined") {
  module.exports = Fuhito.exportConversation;
}
})();

// Domain: FR-6 completeness verification -- the reason this tool exists.
// Pure judgement function: never throws IntegrityError itself (that is Stage 3's
// UseCase layer's job); it returns a structured result the caller inspects.
// Pure functions only -- no fetch / chrome.* / DOM access.
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

const messageTreeModule =
  typeof module !== "undefined" ? require("./message_tree.js") : Fuhito.messageTree;

const ROOT_SENTINEL = messageTreeModule.ROOT_SENTINEL;

/**
 * @typedef {Object} IntegrityResult
 * @property {boolean} ok
 * @property {string[]} failures - hard-fail reasons (empty when ok === true)
 * @property {string[]} warnings - soft findings that do not block export
 * @property {{human: number, assistant: number}} counts
 * @property {string|null} freshness - created_at of the leaf path's last message
 */

/**
 * FR-6 fail-closed integrity verification, performed in four parts:
 *  1. Chain verification (hard fail) -- leaf -> root parent_message_uuid walk
 *     must terminate at the root sentinel without a dangling reference or cycle.
 *  2. Count verification (hard fail):
 *     (a) every message in the tree resolves within the parent/child graph
 *         (no dangling parent_message_uuid references anywhere, not just on
 *         the leaf path);
 *     (b) every leaf-path message classifies as human or assistant, so the
 *         header count baked into the Loop document is never a silent undercount.
 *  3. Empty-content verification (warning) -- leaf-path messages with empty
 *     content[], or assistant messages with content but no text block. Dead
 *     branches are excluded by construction (they are never on the leaf path
 *     and never get serialized).
 *  4. Freshness (info) -- the leaf path's last message's created_at, so the UI
 *     can show "captured up to when".
 *
 * @param {import("./message_tree.js").MessageTree} tree
 * @param {string} currentLeafUuid
 * @returns {IntegrityResult}
 */
function verifyIntegrity(tree, currentLeafUuid) {
  const failures = [];
  const warnings = [];
  let counts = { human: 0, assistant: 0 };
  let freshness = null;

  // 2(a): dangling parent_message_uuid references across the FULL message set.
  const allMessages = Array.from(tree.byUuid.values());
  const dangling = allMessages
    .filter((m) => m.parent_message_uuid !== ROOT_SENTINEL && !tree.byUuid.has(m.parent_message_uuid))
    .map((m) => m.uuid);
  if (dangling.length > 0) {
    failures.push(`Dangling parent_message_uuid reference(s) found for message(s): ${dangling.join(", ")}.`);
  }

  // 1: chain verification (leaf -> root).
  let leafPath = null;
  try {
    leafPath = messageTreeModule.resolveLeafPath(tree, currentLeafUuid);
  } catch (err) {
    failures.push(`Chain verification failed: ${err.message}`);
  }

  if (leafPath) {
    for (const msg of leafPath) {
      if (msg.sender === "human") counts.human++;
      else if (msg.sender === "assistant") counts.assistant++;
    }

    // 2(b): every leaf-path message must be classified human or assistant.
    if (counts.human + counts.assistant !== leafPath.length) {
      failures.push(
        `Message count mismatch: ${leafPath.length} message(s) on the leaf path but only ` +
          `${counts.human + counts.assistant} classified as human/assistant ` +
          "(an unrecognized sender value would be silently dropped from the header count)."
      );
    }

    // 3: empty-content warnings.
    for (const msg of leafPath) {
      const hasContent = Array.isArray(msg.content) && msg.content.length > 0;
      if (!hasContent) {
        warnings.push(`Message ${msg.uuid} (${msg.sender}) on the leaf path has empty content.`);
      } else if (msg.sender === "assistant") {
        const hasText = msg.content.some((b) => b && b.type === "text");
        if (!hasText) {
          warnings.push(`Assistant message ${msg.uuid} on the leaf path has no text block.`);
        }
      }
    }

    // 4: freshness.
    freshness = leafPath[leafPath.length - 1].created_at;
  }

  return { ok: failures.length === 0, failures, warnings, counts, freshness };
}

Fuhito.integrity = { verifyIntegrity };

if (typeof module !== "undefined") {
  module.exports = Fuhito.integrity;
}
})();

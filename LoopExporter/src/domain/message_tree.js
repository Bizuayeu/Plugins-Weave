// Domain: conversation tree indexing and current-leaf-path resolution (FR-3).
// Pure functions only -- no fetch / chrome.* / DOM access, per Stage 2 Success Criteria.
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

// Root sentinel per docs/SCHEMA_NOTES.md §3.2: the root message's own
// parent_message_uuid is always this constant (confirmed against the real sample,
// exactly one message matches it).
const ROOT_SENTINEL = "00000000-0000-4000-8000-000000000000";

/**
 * @typedef {Object} MessageTree
 * @property {Map<string, Object>} byUuid - uuid -> chat_messages[] element
 */

/**
 * Builds a uuid -> message index from the flat chat_messages[] array.
 * @param {Array<Object>} chatMessages
 * @returns {MessageTree}
 */
function buildMessageTree(chatMessages) {
  const byUuid = new Map();
  for (const msg of chatMessages || []) {
    byUuid.set(msg.uuid, msg);
  }
  return { byUuid };
}

/**
 * Resolves the current leaf path (root -> leaf, chronological order) by walking
 * parent_message_uuid pointers backward from currentLeafUuid to rootSentinel.
 *
 * This intentionally returns ONLY the current leaf's ancestry. Dead branches left
 * behind by edits/regenerations are never included -- full-tree export (branch
 * archaeology) is explicit Phase-2 scope and out of bounds for this function
 * (要件定義書 FR-3 オプション行 / IMPLEMENTATION_PLAN Stage 2).
 *
 * @param {MessageTree} tree
 * @param {string} currentLeafUuid
 * @param {string} [rootSentinel] - defaults to ROOT_SENTINEL
 * @returns {Array<Object>} messages in root -> leaf order
 * @throws {Error} if a parent reference cannot be resolved before reaching
 *   rootSentinel (dangling reference), or if a cycle is detected
 */
function resolveLeafPath(tree, currentLeafUuid, rootSentinel) {
  const root = rootSentinel || ROOT_SENTINEL;
  const reversed = [];
  const visited = new Set();
  let cursor = currentLeafUuid;

  while (cursor !== root) {
    if (visited.has(cursor)) {
      throw new Error(`resolveLeafPath: cycle detected at message ${cursor}.`);
    }
    const message = tree.byUuid.get(cursor);
    if (!message) {
      throw new Error(
        `resolveLeafPath: no message found for uuid ${cursor} (dangling parent reference).`
      );
    }
    visited.add(cursor);
    reversed.push(message);
    cursor = message.parent_message_uuid;
  }

  reversed.reverse();
  return reversed;
}

Fuhito.messageTree = { ROOT_SENTINEL, buildMessageTree, resolveLeafPath };

if (typeof module !== "undefined") {
  module.exports = Fuhito.messageTree;
}
})();

// Domain: Loop-compatible document rendering (FR-4) and filename sanitization (FR-7).
// Pure functions only -- no fetch / chrome.* / DOM access. In particular, the
// Extracted timestamp and Exporter version are received as arguments (meta) --
// this module never calls Date.now() itself, for purity and testability.
//
// FR-4 skeleton is a compatibility contract with the existing 550+-file Loop
// corpus: "# Claude" title, a metadata block (Source/Extracted/Exporter/Messages,
// no blank lines between them), a "---" divider, then "## User" / "## Claude"
// headings alternating per message, each heading followed by a blank line and
// the message body. Every section (title / metadata block / divider / each
// heading+body) is separated from its neighbor by exactly one blank line --
// confirmed by Read-only structural comparison against
// Homunculus-Weave-Private/EpisodicRAG/Loops/L00551_*.txt (see task report for
// the confirmed facts; no content from that file is reproduced here).
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

const ILLEGAL_FILENAME_CHARS = /[\/\\<>:"|?*]/g;

/**
 * @typedef {Object} LoopMeta
 * @property {string} extractedAt - ISO8601 timestamp, injected by the caller
 * @property {string} exporterVersion - e.g. "0.1.0"
 */

/**
 * Renders a Loop-compatible document for the given (already leaf-path-resolved,
 * already FR-5-converted) conversation.
 *
 * @param {Object} params
 * @param {{uuid: string}} params.conversation
 * @param {Array<{sender: string}>} params.path - root -> leaf messages (for the
 *   human/assistant heading mapping only; body text comes from convertedMessages)
 * @param {string[]} params.convertedMessages - same length/order as path
 * @param {{human: number, assistant: number}} params.counts
 * @param {LoopMeta} params.meta
 * @returns {string}
 */
function renderLoopDocument(params) {
  const { conversation, path, convertedMessages, counts, meta } = params;

  if (path.length !== convertedMessages.length) {
    throw new Error("renderLoopDocument: path and convertedMessages must be the same length.");
  }

  const headerBlock = [
    `Source: [Claude Chat](https://claude.ai/chat/${conversation.uuid})`,
    `Extracted: ${meta.extractedAt}`,
    `Exporter: Fuhito v${meta.exporterVersion}`,
    `Messages: human ${counts.human} / assistant ${counts.assistant}`,
  ].join("\n");

  const messageSections = path.map((msg, i) => {
    const heading = msg.sender === "human" ? "## User" : "## Claude";
    return `${heading}\n\n${convertedMessages[i]}`;
  });

  const sections = ["# Claude", headerBlock, "---", ...messageSections];
  return sections.join("\n\n") + "\n";
}

/**
 * FR-7: `L{番号}_{タイトル}.txt`. loopNumber is used verbatim (never inferred or
 * padded here -- numbering authority stays on the human side, per the L00551
 * renumbering-correction lesson cited in the requirements doc).
 * @param {string|number} loopNumber
 * @param {string} title
 * @returns {string}
 */
function sanitizeFilename(loopNumber, title) {
  const safeTitle = String(title == null ? "" : title)
    .replace(ILLEGAL_FILENAME_CHARS, "")
    .trim()
    .replace(/\s+/g, "_");
  return `L${loopNumber}_${safeTitle}.txt`;
}

Fuhito.loopFormat = { renderLoopDocument, sanitizeFilename };

if (typeof module !== "undefined") {
  module.exports = Fuhito.loopFormat;
}
})();

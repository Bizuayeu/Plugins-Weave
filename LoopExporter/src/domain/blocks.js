// Domain: content-block conversion rules (FR-5, default column only -- the
// "オプション" column in the requirements table is explicit Phase-2 scope / YAGNI).
// Pure functions only -- no fetch / chrome.* / DOM access.
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

/**
 * @typedef {Object} ConvertBlocksResult
 * @property {string} text
 * @property {string[]} warnings
 */

/**
 * Converts one message's content[] blocks into Loop-compatible body text.
 *
 * Rules (FR-5 defaults):
 *  - text          -> kept as-is (citations[] dropped; body text only)
 *  - tool_use / tool_result -> one line "[tool: {name}]"; a tool_use/tool_result
 *    pair sharing the same id/tool_use_id collapses to a single line (no doubling)
 *  - thinking      -> excluded (not part of the existing Loop corpus)
 *  - unknown type  -> the raw block is preserved (JSON.stringify) in the output
 *    AND recorded as a warning -- never silently dropped (NFR-3)
 *
 * @param {Array<Object>} content
 * @returns {ConvertBlocksResult}
 */
function convertBlocks(content) {
  const parts = [];
  const warnings = [];
  const summarizedToolIds = new Set();

  for (const block of content || []) {
    const type = block && block.type;

    if (type === "text") {
      if (block.text) parts.push(block.text);
    } else if (type === "thinking") {
      // FR-5 default: excluded entirely.
    } else if (type === "tool_use") {
      parts.push(`[tool: ${block.name}]`);
      if (block.id) summarizedToolIds.add(block.id);
    } else if (type === "tool_result") {
      if (block.tool_use_id && summarizedToolIds.has(block.tool_use_id)) {
        // The paired tool_use already emitted the summary line; skip to avoid doubling.
      } else {
        parts.push(`[tool: ${block.name}]`);
        if (block.tool_use_id) summarizedToolIds.add(block.tool_use_id);
      }
    } else {
      warnings.push(`Unknown content block type "${type}" preserved as raw JSON.`);
      parts.push(JSON.stringify(block));
    }
  }

  return { text: parts.join("\n\n"), warnings };
}

/**
 * Formats FR-5 file annotations for a message's files[] array (the real-world
 * carrier of attachment data -- docs/SCHEMA_NOTES.md §3.2 confirms attachments[]
 * was observed always-empty; files[] carries the actual uploaded documents).
 * @param {Array<Object>} files
 * @returns {string[]} one "[file: {name}]" line per file
 */
function formatFileAnnotations(files) {
  const lines = [];
  for (const file of files || []) {
    if (file && file.file_name) {
      lines.push(`[file: ${file.file_name}]`);
    }
  }
  return lines;
}

/**
 * Converts a full chat message (content[] + files[]) into the Loop body text for
 * that message. Thin composition of convertBlocks + formatFileAnnotations so
 * callers (tests, and Stage 3's UseCase) do not have to duplicate the merge order.
 * @param {Object} message - a chat_messages[] element (needs .content, .files)
 * @returns {ConvertBlocksResult}
 */
function convertMessage(message) {
  const blockResult = convertBlocks(message.content);
  const fileLines = formatFileAnnotations(message.files);

  const parts = [];
  if (blockResult.text) parts.push(blockResult.text);
  for (const line of fileLines) parts.push(line);

  return { text: parts.join("\n\n"), warnings: blockResult.warnings };
}

Fuhito.blocks = { convertBlocks, formatFileAnnotations, convertMessage };

if (typeof module !== "undefined") {
  module.exports = Fuhito.blocks;
}
})();

// Adapter: bundles Domain's renderLoopDocument + sanitizeFilename (src/domain/
// loop_format.js) into the single {filename, text} shape a saver ultimately writes
// to disk. Depends on Domain only -- no fetch / chrome.* / DOM.
"use strict";

var Fuhito = globalThis.Fuhito || (globalThis.Fuhito = {});

// IIFE: classic scripts share one global lexical scope -- keep every top-level
// const/class file-local so files cannot collide (see test/classic_script_load.test.js).
(function () {

const loopFormatModule =
  typeof module !== "undefined" ? require("../domain/loop_format.js") : Fuhito.loopFormat;

/**
 * @param {Object} params
 * @param {{uuid: string, name?: string}} params.conversation
 * @param {Array<{sender: string}>} params.path - root -> leaf messages
 * @param {string[]} params.convertedMessages - same length/order as path
 * @param {{human: number, assistant: number}} params.counts
 * @param {{extractedAt: string, exporterVersion: string}} params.meta
 * @param {string|number} params.loopNumber - never inferred; passed through
 *   verbatim to sanitizeFilename (FR-7 -- numbering authority stays on the human
 *   side, per the L00551 renumbering-correction lesson).
 * @param {string|null} [params.titleOverride] - human-typed filename title from
 *   the "L{番号}_{タイトル}" prompt form (see loop_format.parseLoopNumberInput);
 *   when present it outranks conversation.name.
 * @returns {{filename: string, text: string}}
 */
function presentLoopFile(params) {
  const { conversation, path, convertedMessages, counts, meta, loopNumber, titleOverride } = params;

  const text = loopFormatModule.renderLoopDocument({ conversation, path, convertedMessages, counts, meta });
  // FR-7: the filename title comes from the human's explicit override when one
  // was typed, else from the conversation's own name -- this tool never invents
  // a title any more than it invents a loop number.
  const filename = loopFormatModule.sanitizeFilename(
    loopNumber,
    titleOverride != null ? titleOverride : conversation.name
  );

  return { filename, text };
}

Fuhito.loopFilePresenter = { presentLoopFile };

if (typeof module !== "undefined") {
  module.exports = Fuhito.loopFilePresenter;
}
})();

// Browser-path regression test for the MV3 classic-script pipeline.
//
// manifest.json's content_scripts load every src file as a classic script, and
// classic scripts all share ONE global lexical scope -- a top-level
// const/class collision between any two files is a SyntaxError that silently
// kills the later file (its Fuhito.* assignment never runs). node:test's
// require() path gives each file its own module scope, so the other 64 tests
// can stay green while the browser build is broken. This test is the only
// place that reproduces the browser condition: no module, no require, one
// shared scope, manifest load order.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ROOT = path.join(__dirname, "..");

test("classic-script load: manifest js files evaluate in one shared scope and publish the full Fuhito namespace", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "manifest.json"), "utf8"));
  const files = manifest.content_scripts[0].js;
  assert.ok(files.length > 0, "manifest content_scripts[0].js is empty");

  // The browser condition: no module, no require. `var Fuhito` and any leaked
  // top-level const/class land on this single shared context.
  const context = vm.createContext({});

  for (const rel of files) {
    // content.js needs a DOM (document/window); its syntax is covered by
    // `node --check` and it publishes nothing on the namespace, so the
    // library pipeline (everything before it) is what this test exercises.
    if (rel === "src/content.js") continue;
    const code = fs.readFileSync(path.join(ROOT, rel), "utf8");
    // filename makes a collision SyntaxError name the offending file.
    vm.runInContext(code, context, { filename: rel });
  }

  const Fuhito = context.Fuhito;
  assert.ok(Fuhito, "Fuhito namespace was never created");
  // Exactly the public API content.js consumes, plus every intermediate the
  // later files resolve from the namespace when `module` is undefined.
  assert.equal(typeof Fuhito.messageTree.buildMessageTree, "function");
  assert.equal(typeof Fuhito.messageTree.resolveLeafPath, "function");
  assert.equal(typeof Fuhito.blocks.convertMessage, "function");
  assert.equal(typeof Fuhito.integrity.verifyIntegrity, "function");
  assert.equal(typeof Fuhito.loopFormat.renderLoopDocument, "function");
  assert.equal(typeof Fuhito.loopFormat.sanitizeFilename, "function");
  assert.equal(typeof Fuhito.claudeApiGateway.createClaudeApiGateway, "function");
  assert.equal(typeof Fuhito.loopFilePresenter.presentLoopFile, "function");
  assert.equal(typeof Fuhito.exportConversation.exportConversation, "function");
  assert.equal(typeof Fuhito.exportConversation.IntegrityError, "function");
});

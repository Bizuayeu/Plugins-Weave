// Infrastructure: MV3 content script (FR-1 chatId extraction, FR-7 loop-number
// prompt, Blob download, error/toast display). This is the ONLY file permitted
// to touch document / window / chrome.* -- it drives Fuhito purely through the
// public API published on the shared `Fuhito` namespace (Fuhito.claudeApiGateway,
// Fuhito.exportConversation), the same object src/domain/*.js, src/adapter/*.js
// and src/usecase/*.js attach to when manifest.json loads them (classic script,
// array order, no bundler -- see IMPLEMENTATION_PLAN.md Stage 4 / NFR-5). It
// never calls into src/domain/*.js directly.
"use strict";

(function () {
  // Defensive guard against double-injection (e.g. dev-mode extension reload
  // re-running content_scripts on an already-loaded tab).
  if (window.__fuhitoContentLoaded) return;
  window.__fuhitoContentLoaded = true;

  // Keep in sync with manifest.json "version".
  const EXPORTER_VERSION = "0.2.0";

  const CHAT_PATH_RE = /^\/chat\/([0-9a-fA-F-]+)/;

  const BUTTON_ID = "fuhito-export-button";
  const TOAST_ID = "fuhito-export-toast";
  const TOAST_DURATION_MS = 12000;
  const REINJECT_INTERVAL_MS = 3000;

  // credentials: "include" is already set inside claude_api_gateway.js -- not
  // repeated here.
  const gateway = Fuhito.claudeApiGateway.createClaudeApiGateway({
    fetchFn: (...args) => fetch(...args),
  });

  /**
   * FR-1: chatId comes only from the `/chat/{uuid}` URL path, re-read at click
   * time (no persistent URL-change observer -- SPA route changes are cheap to
   * re-check on demand instead of watched for).
   * @returns {string|null}
   */
  function extractChatId() {
    const match = CHAT_PATH_RE.exec(location.pathname);
    return match ? match[1] : null;
  }

  /**
   * FR-7: manual Loop-number entry, default blank, never inferred. Returning
   * null (dialog dismissed) or "" (blank submit) both mean "cancel" --
   * export_conversation.js already treats both as cancelled. A full
   * "L00553_タイトル" input overrides the session-name title (parsing lives in
   * domain/loop_format.js parseLoopNumberInput, not here).
   * @returns {string|null}
   */
  function promptLoopNumber() {
    return window.prompt(
      "フヒト: Loop番号を入力してください（例: L00553）。L00553_タイトル 形式ならタイトルも上書き（省略時はセッション名）。空欄でキャンセル。",
      ""
    );
  }

  /**
   * @param {{filename: string, text: string}} params
   */
  function saveTextFile({ filename, text }) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  // --- minimal UI: one fixed button + a toast, no dependency on claude.ai's
  // own DOM structure --------------------------------------------------------

  function ensureButton() {
    let button = document.getElementById(BUTTON_ID);
    if (button && document.body && document.body.contains(button)) return button;

    button = document.createElement("button");
    button.id = BUTTON_ID;
    button.type = "button";
    button.textContent = "フヒト: Loop保存";
    Object.assign(button.style, {
      position: "fixed",
      right: "16px",
      bottom: "16px",
      zIndex: "2147483647",
      padding: "8px 14px",
      borderRadius: "8px",
      border: "1px solid #6b6b6b",
      background: "#2d2d2d",
      color: "#f5f5f5",
      fontSize: "13px",
      fontFamily: "system-ui, sans-serif",
      cursor: "pointer",
      boxShadow: "0 2px 8px rgba(0,0,0,0.35)",
    });
    button.addEventListener("click", onExportClick);
    document.body.appendChild(button);
    return button;
  }

  /**
   * @param {string} message
   * @param {"success"|"error"} tone
   */
  function showToast(message, tone) {
    const existing = document.getElementById(TOAST_ID);
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = TOAST_ID;
    toast.textContent = message;
    Object.assign(toast.style, {
      position: "fixed",
      right: "16px",
      bottom: "56px",
      zIndex: "2147483647",
      maxWidth: "360px",
      padding: "10px 14px",
      borderRadius: "8px",
      background: tone === "error" ? "#5c1a1a" : "#1a3d1a",
      color: "#f5f5f5",
      fontSize: "12px",
      lineHeight: "1.5",
      fontFamily: "system-ui, sans-serif",
      whiteSpace: "pre-wrap",
      boxShadow: "0 2px 8px rgba(0,0,0,0.35)",
    });
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), TOAST_DURATION_MS);
  }

  /**
   * @param {string[]} warnings
   * @returns {string}
   */
  function formatWarnings(warnings) {
    if (!warnings || warnings.length === 0) return "";
    const shown = warnings.slice(0, 3);
    const rest = warnings.length - shown.length;
    const lines = shown.map((w) => `- ${w}`);
    if (rest > 0) lines.push(`...ほか${rest}件`);
    return `\n警告 (${warnings.length}件):\n${lines.join("\n")}`;
  }

  async function onExportClick() {
    const button = ensureButton();
    if (button.disabled) return; // 運用規律: 1クリック1GET

    const chatId = extractChatId();
    if (!chatId) {
      showToast("会話ページ（claude.ai/chat/{id}）で実行してください。", "error");
      return;
    }

    button.disabled = true;
    button.style.opacity = "0.6";
    button.style.cursor = "wait";

    try {
      const result = await Fuhito.exportConversation.exportConversation({
        gateway,
        saver: saveTextFile,
        promptLoopNumber,
        clock: () => new Date().toISOString(),
        exporterVersion: EXPORTER_VERSION,
        chatId,
      });

      if (result.cancelled) {
        // FR-7: dismissed/blank prompt aborts quietly, same as a verification
        // failure aborts loudly -- no file was written either way.
        return;
      }

      const freshnessLine = result.freshness ? `鮮度: ${result.freshness}` : "鮮度: 不明";
      const countsLine = `human ${result.counts.human} / assistant ${result.counts.assistant}`;
      showToast(
        `保存しました: ${result.filename}\n${countsLine}\n${freshnessLine}${formatWarnings(result.warnings)}`,
        "success"
      );
    } catch (err) {
      // Discriminate by .name / .code, not instanceof (robust to the classic
      // script load order rather than relying on identity across the shared
      // Fuhito namespace).
      if (err && err.name === "IntegrityError") {
        showToast(
          `完全性検証に失敗したため、ファイルは出力していません。\n${err.failures.join("\n")}`,
          "error"
        );
      } else if (err && err.code === "SESSION_EXPIRED") {
        showToast(
          "セッション切れの可能性があります。claude.ai に再ログインしてから再試行してください。",
          "error"
        );
      } else if (err && err.code === "API_DRIFT") {
        showToast(
          "claude.ai の API 変更の疑いがあります。docs/SCHEMA_NOTES.md の手順で再採取・修理してください。",
          "error"
        );
      } else {
        showToast(`予期しないエラー: ${err && err.message ? err.message : String(err)}`, "error");
      }
    } finally {
      button.disabled = false;
      button.style.opacity = "1";
      button.style.cursor = "pointer";
    }
  }

  // --- SPA safety net: cheap periodic re-injection check, not a DOM/URL
  // observer (YAGNI -- see IMPLEMENTATION_PLAN.md Stage 4 notes) -------------
  ensureButton();
  setInterval(ensureButton, REINJECT_INTERVAL_MS);
})();

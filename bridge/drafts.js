/* Frugal Flock — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/frugal-flock
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";
  const panel = document.getElementById("manual-drafts");
  const notice = document.querySelector(".notice");
  const readOnlyNotice = notice.textContent.trim();
  const request = document.getElementById("draft-request");
  const identity = document.getElementById("draft-id");
  const status = document.getElementById("draft-status");
  const result = document.getElementById("draft-result");
  const buttons = ["save-draft", "reopen-draft"].map((id) =>
    document.getElementById(id),
  );
  let token = null,
    busy = false;
  function controls() {
    for (const button of buttons) button.disabled = busy || !token;
  }
  function message(value, error = false) {
    status.textContent = value;
    status.className = error ? "error" : "";
  }
  async function session() {
    token = null;
    controls();
    const response = await fetch("/api/session", { cache: "no-store" });
    if (!response.ok) throw new Error("session unavailable");
    const data = await response.json();
    if (data.schema_version !== 1 || typeof data.manual_drafts !== "boolean")
      throw new Error("invalid capability");
    panel.hidden = !data.manual_drafts;
    if (!data.manual_drafts) notice.textContent = readOnlyNotice;
    if (data.manual_drafts) {
      if (typeof data.token !== "string" || !data.token)
        throw new Error("missing session");
      token = data.token;
      document.querySelector(".notice").textContent =
        "Manual draft preview. Saving stores your text locally; no AI or worker starts. Recorded task decisions remain separate from readiness and acceptance.";
    }
    controls();
    return data.manual_drafts;
  }
  function show(data) {
    if (
      data.schema_version !== 1 ||
      data.state !== "draft" ||
      !/^[0-9a-f]{32}$/.test(data.id) ||
      typeof data.request !== "string" ||
      !/^[0-9a-f]{64}$/.test(data.content_sha256)
    )
      throw new Error("invalid draft");
    document.getElementById("draft-text").textContent = data.request;
    document.getElementById("draft-reference").textContent =
      "ID: " + data.id + " · SHA-256: " + data.content_sha256;
    identity.value = data.id;
    location.hash = "draft=" + data.id;
    result.hidden = false;
  }
  async function operation(save) {
    if (busy || !token) return;
    if (save && !request.value.trim()) {
      message("Enter a request before saving.", true);
      return;
    }
    if (!save && !/^[0-9a-f]{32}$/.test(identity.value)) {
      message("Enter the 32-character draft ID.", true);
      return;
    }
    busy = true;
    controls();
    result.hidden = true;
    message(save ? "Saving your manual draft…" : "Opening your manual draft…");
    try {
      const response = await fetch(
        save ? "/api/plans" : "/api/plans/" + identity.value,
        {
          method: save ? "POST" : "GET",
          cache: "no-store",
          headers: {
            "X-Frugal-Flock-Session": token,
            ...(save ? { "Content-Type": "application/json" } : {}),
          },
          ...(save ? { body: JSON.stringify({ request: request.value }) } : {}),
        },
      );
      if (response.status === 403) {
        await session();
        message(
          "Session refreshed. Review your text and choose " +
            (save ? "Save draft" : "Reopen draft") +
            " again. No retry was sent.",
          true,
        );
      } else if (!save && response.status === 404) {
        message("Draft not found in this project.", true);
      } else {
        if (!response.ok) throw new Error("operation unavailable");
        show(await response.json());
        message(
          save
            ? "Manual draft saved. No AI or worker started."
            : "Manual draft reopened. No AI or worker started.",
        );
      }
    } catch (_) {
      message(
        save
          ? "Save outcome not confirmed. Your text is kept. No retry was sent."
          : "Draft could not be opened. No current draft is claimed.",
        true,
      );
    } finally {
      busy = false;
      controls();
    }
  }
  document.getElementById("draft-form").addEventListener("submit", (event) => {
    event.preventDefault();
    operation(true);
  });
  document.getElementById("reopen-form").addEventListener("submit", (event) => {
    event.preventDefault();
    operation(false);
  });
  session()
    .then((enabled) => {
      const saved = location.hash.match(/^#draft=([0-9a-f]{32})$/);
      if (enabled && saved) {
        identity.value = saved[1];
        operation(false);
      }
    })
    .catch(() => {
      token = null;
      controls();
      message("Draft session unavailable. Reload to reconnect.", true);
    });
})();

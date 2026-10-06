/* Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/unio
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";
  const panel = document.getElementById("manual-drafts");
  const notice = document.querySelector(".notice");
  const readOnlyNotice = notice.textContent.trim();
  const selected = document.getElementById("selected-work");
  const empty = document.getElementById("workspace-empty");
  const request = document.getElementById("draft-request");
  const identity = document.getElementById("draft-id");
  const status = document.getElementById("draft-status");
  const result = document.getElementById("draft-result");
  const buttons = ["save-draft", "reopen-draft"].map((id) =>
    document.getElementById(id),
  );
  let token = null,
    busy = false,
    executionBusy = false;
  function controls() {
    for (const button of buttons) button.disabled = busy || executionBusy || !token;
    document.getElementById("draft-form").setAttribute("aria-busy", String(busy));
    document.getElementById("reopen-form").setAttribute("aria-busy", String(busy));
  }
  function mode(data) {
    const live = data.execution === true;
    panel.hidden = !data.manual_drafts;
    selected.hidden = !data.manual_drafts;
    document.getElementById("mode-label").textContent = live
      ? "Live execution" : data.manual_drafts ? "Manual drafts" : "Read-only";
    notice.textContent = live
      ? "Live execution is enabled. Saving and preparing do not call providers. Approve run permits spending; Start once and Request review are separate explicit actions."
      : data.manual_drafts
        ? "Manual draft preview. Saving stores your text locally; no AI or worker starts. Recorded task decisions remain separate from readiness and acceptance."
        : readOnlyNotice;
    document.getElementById("draft-help").textContent = live
      ? "Save your exact request, then prepare the configured scope, checks and lab preview. Saving does not start a worker."
      : "Save your request locally. Saving stores text only; no AI or worker starts.";
    document.getElementById("workspace-empty-help").textContent = live
      ? "Save a request or reopen a job. Inspect its exact preview before approving spending and starting once."
      : "Write your task in the composer, or reopen a saved draft. Your exact text will appear here.";
    document.getElementById("mode-footer").textContent = live
      ? "Execution mode can spend provider allowance through explicit Start once and Request review actions. Acceptance applies only to the current verified and reviewed revision; it does not merge, install or publish. Authentication and provider capacity are unknown."
      : data.manual_drafts
        ? "Manual mode saves and reopens literal drafts only. Authentication and provider capacity are unknown. Use CLI result to recheck current source readiness."
        : "Default mode observes local activity only. Authentication and provider capacity are unknown. Use CLI result to recheck current readiness.";
  }
  function message(value, error = false) {
    status.textContent = value;
    status.className = error ? "error" : "";
  }
  function disconnected() {
    token = null;
    controls();
    document.getElementById("mode-label").textContent = "Mode unavailable";
    notice.textContent = "Session unavailable. No execution capability is confirmed. Reload to reconnect.";
    document.dispatchEvent(new CustomEvent("unio-session", {
      detail: { manual_drafts: false, execution: false, token: null },
    }));
    message("Draft session unavailable. Reload to reconnect.", true);
  }
  async function session() {
    token = null;
    controls();
    const response = await fetch("/api/session", { cache: "no-store" });
    if (!response.ok) throw new Error("session unavailable");
    const data = await response.json();
    if (data.schema_version !== 1 || typeof data.manual_drafts !== "boolean")
      throw new Error("invalid capability");
    mode(data);
    if (data.manual_drafts) {
      if (typeof data.token !== "string" || !data.token)
        throw new Error("missing session");
      token = data.token;
    }
    controls();
    document.dispatchEvent(new CustomEvent("unio-session", { detail: data }));
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
    empty.hidden = true;
    document.dispatchEvent(new CustomEvent("saved-draft", { detail: data }));
  }
  async function operation(save) {
    if (busy || executionBusy || !token) return;
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
    document.dispatchEvent(new Event("draft-opening"));
    message(save ? "Saving your manual draft…" : "Opening your manual draft…");
    try {
      const response = await fetch(
        save ? "/api/plans" : "/api/plans/" + identity.value,
        {
          method: save ? "POST" : "GET",
          cache: "no-store",
          headers: {
            "X-Unio-Session": token,
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
      document.dispatchEvent(new Event("draft-idle"));
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
  document.addEventListener("refresh-session", (event) => {
    session().then(event.detail.resolve).catch((error) => {
      disconnected();
      event.detail.reject(error);
    });
  });
  document.addEventListener("execution-busy", (event) => {
    executionBusy = event.detail;
    controls();
  });
  session()
    .then((enabled) => {
      const saved = location.hash.match(/^#draft=([0-9a-f]{32})$/);
      if (enabled && saved) {
        identity.value = saved[1];
        operation(false);
      }
    })
    .catch(disconnected);
})();

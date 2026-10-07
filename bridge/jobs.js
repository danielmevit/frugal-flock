/* Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/unio
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";
  const panel = document.getElementById("execution-panel");
  const status = document.getElementById("job-status");
  const stageTitle = document.getElementById("stage-title");
  const stageHelp = document.getElementById("stage-help");
  const reopen = document.getElementById("reopen-job-form");
  const buttons = Object.fromEntries(
    ["prepare", "approve", "start", "verify", "review", "accept", "stop", "cancel", "refresh"]
      .map((action) => [action, document.getElementById("job-" + action)]),
  );
  const contextKey = "unio_execution_context";
  const pendingKey = "unio_pending_operation";
  let token = null, enabled = false, busy = false, draftBusy = false;
  let currentDraft = null, currentJob = null, initialized = false;
  let needsRead = false;
  let available = new Set();

  function stored(key) {
    const raw = sessionStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  }
  function remember(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value));
  }
  function opaqueKey(storageKey, known = null) {
    let key = sessionStorage.getItem(storageKey);
    if (key && !/^[0-9a-f]{32}$/.test(key)) throw new Error("Saved action context is invalid. No action was sent.");
    if (known && key && key !== known) throw new Error("Saved action key conflicts with this job. No action was sent.");
    if (!key) {
      key = known || Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map((byte) => byte.toString(16).padStart(2, "0")).join("");
      sessionStorage.setItem(storageKey, key);
    }
    return key;
  }
  function jobKey(kind, known = null) {
    return opaqueKey(`unio_job_${currentJob.job.id}_${kind}`, known);
  }
  function draftKey() {
    return opaqueKey(`unio_draft_${currentDraft.id}_request`);
  }
  function message(value, error = false) {
    status.textContent = value;
    status.className = error ? "error" : "";
  }
  function controls() {
    for (const [action, button] of Object.entries(buttons))
      button.disabled = busy || draftBusy || !token || !available.has(action) ||
        (needsRead && !["refresh", "stop"].includes(action));
    document.getElementById("reopen-job").disabled = busy || draftBusy || !token;
    panel.setAttribute("aria-busy", String(busy));
    reopen.setAttribute("aria-busy", String(busy));
  }
  function setBusy(value, text, error = false) {
    busy = value;
    controls();
    document.dispatchEvent(new CustomEvent("execution-busy", { detail: value }));
    if (text) message(text, error);
  }
  function sameRevision(a, b) {
    return !!a && !!b && ["base_commit", "candidate_commit", "task_sha256", "worktree_sha256"]
      .every((key) => typeof a[key] === "string" && a[key] === b[key]);
  }
  function element(tag, value, className = "") {
    const node = document.createElement(tag);
    node.textContent = value;
    node.className = className;
    return node;
  }
  function stage(name, title, help) {
    stageTitle.textContent = title;
    stageHelp.textContent = help;
    for (const item of document.querySelectorAll("#job-stages li")) {
      item.removeAttribute("aria-current");
      if (item.dataset.stage === name) item.setAttribute("aria-current", "step");
    }
  }
  function offer(action, permitted = true) {
    buttons[action].hidden = false;
    if (permitted) available.add(action);
  }
  function preview(job) {
    const p = job.preview;
    const content = document.getElementById("job-preview-text");
    content.replaceChildren();
    if (!p) return;
    content.append(element("h4", "Request"));
    const request = element("pre", p.request);
    request.id = "job-request-text";
    content.append(request);
    const grid = element("div", "", "preview-grid");
    for (const [label, lines] of [["Allowed scope", p.scope], ["Validate checks", p.validate]]) {
      const section = element("div", "");
      section.append(element("h4", label), element("pre", lines.join("\n")));
      grid.append(section);
    }
    content.append(grid);
    const providers = element("div", "", "provider-labels");
    for (const [label, worker, company] of [["Source worker", p.worker, p.worker_company], ["Independent reviewer", p.reviewer, p.reviewer_company]]) {
      const group = element("div", "");
      group.append(element("h4", label), element("strong", company), element("p", worker));
      providers.append(group);
    }
    content.append(providers);
    document.getElementById("job-reference-text").textContent =
      `Job ID: ${job.job.id}\nDraft ID: ${job.job.draft_id}\nDraft SHA-256: ${job.job.draft_sha256}\nTask ID: ${p.task_id}\nTask SHA-256: ${p.task_sha256}\nPreview SHA-256: ${p.preview_hash}`;
  }
  function evidence(job) {
    const grid = document.getElementById("job-evidence");
    grid.replaceChildren();
    const n = job.native_result;
    const values = [
      ["Launch receipt", job.execution.state.replaceAll("_", " ") + " · exit " + (job.execution.launcher_exit ?? "unknown")],
      ["Native process", n ? n.process.state.replaceAll("_", " ") + " · exit " + (n.process.exit_code ?? "unknown") : "Unavailable; no completion claimed"],
      ["Validation", n ? `${n.validation.state.replaceAll("_", " ")} · ${n.validation.checks_run} checks / ${n.validation.checks_failed} failed · scope ${n.validation.scope}` : "No current checks available"],
      ["Independent review", n ? n.review.state.replaceAll("_", " ") + " · " + (n.review.reviewer || "no reviewer recorded") : "No current review available"],
      ["Source readiness", n ? n.stale ? "Stale evidence" : n.ready_for_human_review ? "Current verified and reviewed revision" : "Not ready for acceptance" : "Unknown"],
      ["Acceptance", job.acceptance.state === "accepted" ? "Current revision accepted" : job.acceptance.state === "stale" ? "Stale; earlier acceptance does not apply" : "Pending; run approval is separate"],
    ];
    for (const [label, value] of values) {
      const row = element("div", "");
      row.append(element("dt", label), element("dd", value));
      grid.append(row);
    }
    document.getElementById("job-result-text").textContent = JSON.stringify({
      execution: job.execution, native_result: n, acceptance: job.acceptance, warnings: job.warnings,
    }, null, 2);
  }
  const warningHelp = {
    binding_stale: "The fixed execution binding changed.",
    draft_stale: "The saved request no longer matches its recorded hash.",
    ownership_unknown: "Worker ownership is uncertain; another start is not permitted.",
    outcome_unknown: "An action outcome is unknown; reads cannot authorize another attempt.",
    stopped: "Project STOP is active.",
    native_result_unavailable: "Current native evidence is unavailable.",
    native_result_invalid: "The native result could not be validated; no readiness is claimed.",
  };
  function renderJob(job) {
    currentJob = job;
    panel.hidden = !enabled;
    document.getElementById("workspace-empty").hidden = !!(currentDraft || job);
    // The job preview contains the exact request; avoid displaying it twice.
    document.getElementById("draft-result").hidden = !!job || !currentDraft;
    available = new Set();
    for (const button of Object.values(buttons)) button.hidden = true;
    document.getElementById("job-preview").hidden = !job;
    document.getElementById("job-result").hidden = !job;
    const warnings = document.getElementById("job-warnings");
    warnings.replaceChildren();
    warnings.hidden = !job || !job.warnings.length;
    document.getElementById("job-state").textContent = job ? job.job.state.replaceAll("_", " ") : "Saved draft";
    if (!job) {
      stage("preview", "Prepare a preview", "Next: prepare the saved request with the fixed scope, checks and configured labs. Preparation makes no provider call and grants no spending approval.");
      offer("prepare", !!currentDraft);
      offer("refresh", !!currentDraft);
      controls();
      return;
    }
    preview(job);
    evidence(job);
    for (const warning of job.warnings)
      warnings.append(element("li", (warningHelp[warning] || "Recorded warning.") + " (" + warning + ")"));
    offer("refresh");
    const state = job.job.state;
    const n = job.native_result;
    const blocked = job.warnings.some((warning) => ["binding_stale", "draft_stale", "ownership_unknown", "outcome_unknown", "stopped"].includes(warning));
    const uncertain = state === "completion_unknown" || job.execution.state === "completion_unknown";
    const currentProcess = n && !n.stale && n.process.state === "succeeded" && n.process.exit_code === 0 && sameRevision(n.process.revision, n.current_revision);
    const checked = currentProcess && n.validation.state === "passed" && n.validation.scope === "OK" && n.validation.checks_run > 0 && n.validation.checks_failed === 0 && !n.validation.reasons.length && sameRevision(n.validation.revision, n.current_revision);
    const reviewed = checked && n.review.state === "approved" && n.review.process_exit_code === 0 && n.review.material_complete && !n.review.reasons.length && n.review.reviewer === job.preview.reviewer && sameRevision(n.review.revision, n.current_revision);
    if (state === "cancelled") {
      stage("preview", "Job cancelled", "This waiting job was cancelled before reservation. Cancellation does not terminate a live worker. You can save a new request explicitly.");
    } else if (uncertain) {
      stage("run", "Completion is unknown", "Next: refresh recorded state or explicitly stop this task. A lost response is not permission to start or spend again; no automatic retry is sent.");
      offer("stop");
    } else if (blocked || (n && n.stale) || job.acceptance.state === "stale") {
      stage("verify", "Current evidence needs attention", "Next: refresh and inspect warnings and exact revision details. Stale evidence or a changed binding cannot authorize a run, review or current acceptance.");
      if (state === "reserved" && (!n || n.process.state === "running")) offer("stop");
      if (["awaiting_owner_approval", "approved"].includes(state)) offer("cancel");
    } else if (state === "awaiting_owner_approval") {
      stage("approve", "Inspect before approving", "Next: inspect the exact preview below. Approve run permits the configured worker and reviewer spending, but starts neither. Acceptance of verified and reviewed source comes later.");
      offer("approve"); offer("cancel");
    } else if (state === "approved") {
      stage("run", "Approved; ready to start once", "Next: Start once launches the configured worker and can spend provider allowance. Approval alone has not started it. Cancel job is available before reservation.");
      offer("start"); offer("cancel");
    } else if (state === "reserved") {
      if (job.acceptance.state === "accepted") {
        stage("accept", "Current revision accepted", "Acceptance records this exact verified and reviewed revision. It does not merge, install or publish. Refresh to check whether the evidence remains current.");
      } else if (!n || ["not_run", "running"].includes(n.process.state)) {
        stage("run", n ? "Worker evidence: " + n.process.state.replaceAll("_", " ") : "Waiting for native evidence", "Next: refresh to observe the native process. A launch receipt does not establish worker success. Stop task targets only this job; cancellation is no longer available.");
        offer("stop");
      } else if (!currentProcess) {
        stage("run", "Worker did not succeed", "Inspect the native exit and revision details. No automatic retry or provider switch is available. Any correction requires another explicitly scoped task.");
      } else if (!checked) {
        stage("verify", "Check the source changes", n.validation.state === "not_run"
          ? "Next: Verify changes runs the fixed Validate commands against the current successful native revision. Worker success alone does not make the source ready."
          : "Checks did not pass. Inspect the scope, failed checks and exact native reasons below. No successful verification or acceptance is claimed.");
        offer("verify", n.validation.state === "not_run");
      } else if (!reviewed) {
        stage("review", "Independent review", n.review.state === "not_run"
          ? "Next: Request review spends allowance for one configured independent reviewer call. Current passed checks are required. A failed or unknown review is not retried automatically."
          : "The recorded review is not an approval of this current revision. Inspect its exact state and reasons. Another paid review is not offered for this job.");
        offer("review", n.review.state === "not_run");
      } else {
        stage("accept", "Decide on the current revision", "Next: accept only the exact current verified and reviewed revision shown in details. This source decision is separate from spending approval and does not merge, install or publish.");
        offer("accept", n.ready_for_human_review === true);
      }
    } else {
      stage("run", "Job state unavailable", "Refresh this job to read current state. No execution readiness is claimed.");
    }
    controls();
  }

  async function checkSession() {
    return new Promise((resolve, reject) => document.dispatchEvent(new CustomEvent("refresh-session", { detail: { resolve, reject } })));
  }
  const errorHelp = {
    outcome_unknown: "Outcome is unknown. Refresh job to read evidence before any further action.",
    not_ready: "Current native evidence does not permit this action. Refresh job and inspect details.",
    binding_stale: "The execution binding changed. Refresh job and inspect warnings.",
    draft_stale: "The saved draft no longer matches this job. Your text and context are kept.",
    worker_unavailable: "The configured worker is unavailable. No provider switch was made.",
    stopped: "Project STOP is active. No start is permitted.",
    conflict: "This action conflicts with recorded job context. Refresh job; no new intent was created.",
    job_not_found: "Job not found in this project's execution records.",
    storage_unavailable: "Job storage is unavailable. Your text and context are kept.",
    native_unavailable: "Native evidence is unavailable. No completion is claimed.",
  };
  async function apiCall(method, path, body) {
    if (!token) throw new Error("Execution session unavailable. No action was sent.");
    const response = await fetch(path, {
      method, cache: "no-store",
      headers: { "X-Unio-Session": token, ...(body ? { "Content-Type": "application/json" } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    if (response.status === 403) {
      await checkSession();
      throw new Error("Session refreshed. Refresh job to read current state. No retry was sent.");
    }
    if (!response.ok) {
      const data = await response.json();
      throw new Error((errorHelp[data.error] || "Operation unavailable. Your request and context are kept.") + " (" + data.error + ") No retry was sent.");
    }
    return response.json();
  }
  function recordJob(data) {
    if (data.schema_version !== 1 || !data.job || !/^[0-9a-f]{32}$/.test(data.job.id) || !data.preview || !data.execution || !data.acceptance || !Array.isArray(data.warnings))
      throw new Error("Job response unavailable. No readiness is claimed.");
    remember(contextKey, { jobId: data.job.id, draftId: data.job.draft_id });
    document.getElementById("job-id").value = data.job.id;
    location.hash = "job=" + data.job.id;
    needsRead = false;
    document.getElementById("result-title").textContent = "Current evidence";
    renderJob(data);
  }
  async function openJob(id, restoring = false) {
    if (busy || !enabled) return;
    document.getElementById("job-id").value = id;
    if (!currentJob && !currentDraft) {
      panel.hidden = false;
      document.getElementById("workspace-empty").hidden = true;
      document.getElementById("job-state").textContent = "Reading saved work";
      stage("preview", "Open a saved job", "Reopening reads recorded state only. If the ID cannot be opened, keep the ID and check it in Reopen saved work. No worker or review starts.");
    }
    setBusy(true, restoring ? "Restoring job context; reading state only…" : "Reopening job…");
    try {
      recordJob(await apiCall("GET", "/api/jobs/" + id));
      message(restoring ? "Job context restored. No POST was sent. Inspect current evidence." : "Job reopened. Inspect current evidence.");
    } catch (error) {
      needsRead = true;
      document.getElementById("reopen-details").open = true;
      document.getElementById("result-title").textContent = "Last observed evidence; reopen unavailable";
      message(error.message, true);
    }
    finally { setBusy(false); }
  }
  async function refresh() {
    if (busy || !enabled) return;
    setBusy(true, "Refreshing job evidence…");
    try {
      if (currentJob) recordJob(await apiCall("GET", "/api/jobs/" + currentJob.job.id));
      else if (currentDraft) {
        const key = sessionStorage.getItem(`unio_draft_${currentDraft.id}_request`);
        const data = await apiCall("GET", "/api/jobs");
        const job = data.jobs.find((view) => view.job.request_key === key && view.job.draft_id === currentDraft.id);
        if (job) recordJob(job);
        else {
          renderJob(null);
          if (needsRead) stage("preview", "Preparation outcome not confirmed", "Next: refresh the saved intent. No matching job is currently recorded; an unconfirmed preparation is not repeated automatically or replaced with a new key.");
        }
      }
      message("Job refreshed. Reads do not retry actions.");
    } catch (error) {
      needsRead = true;
      document.getElementById("result-title").textContent = "Last observed evidence; refresh unavailable";
      message(error.message, true);
    }
    finally { setBusy(false); }
  }
  function actionBody(action) {
    if (action === "prepare") return { draft_id: currentDraft.id, expected_hash: currentDraft.content_sha256, request_key: draftKey() };
    if (action === "approve") return { expected_hash: currentJob.job.draft_sha256, approval_key: jobKey("approval_key", currentJob.job.approval_key), preview_hash: currentJob.preview.preview_hash };
    if (action === "start") return { approval_key: jobKey("approval_key", currentJob.job.approval_key), reservation_key: jobKey("reservation_key", currentJob.job.reservation_key) };
    if (action === "cancel") return {};
    if (action === "accept") return { revision_hash: currentJob.native_result.current_revision.candidate_commit, action_key: jobKey("action_key_accept") };
    return { action_key: jobKey("action_key_" + action) };
  }
  const sending = {
    prepare: "Preparing the exact preview…", approve: "Recording run approval…", start: "Sending start-once intent…",
    verify: "Running the fixed checks…", review: "Requesting the configured review once…", accept: "Recording current source acceptance…",
    stop: "Requesting stop for this task…", cancel: "Cancelling the waiting job…",
  };
  const completed = {
    prepare: "Job prepared. Inspect the exact preview before approving.", approve: "Run approved. No worker started.",
    start: "Launch response recorded. Inspect native evidence; launch acceptance is not worker success.",
    verify: "Verification response recorded. Inspect the actual checks and reasons below.",
    review: "Review response recorded. Inspect the actual decision and reasons below.",
    accept: "Current revision accepted. No merge, installation or publication occurred.",
    stop: "Stop response recorded. Inspect native evidence; termination is not assumed.", cancel: "Job cancelled before reservation.",
  };
  async function act(action) {
    if (busy || draftBusy || !enabled || !available.has(action) ||
        (needsRead && action !== "stop")) return;
    const hadFocus = document.activeElement === buttons[action];
    let completedResponse = false;
    setBusy(true, sending[action]);
    try {
      const body = actionBody(action);
      const id = action === "prepare" ? currentDraft.id : currentJob.job.id;
      const path = action === "prepare" ? "/api/jobs" : `/api/jobs/${id}/${action}`;
      const key = `unio_action_${id}_${action}`;
      const revision = ["verify", "review", "accept"].includes(action) ? currentJob.native_result.current_revision : null;
      const intent = { path, body, revision };
      const old = stored(key);
      if (old && JSON.stringify(old) !== JSON.stringify(intent)) throw new Error("Saved action belongs to different inputs or revision. No new intent or action key was created.");
      remember(key, intent);
      remember(contextKey, { jobId: currentJob ? currentJob.job.id : null, draftId: currentDraft ? currentDraft.id : currentJob.job.draft_id });
      remember(pendingKey, intent);
      // The complete opaque intent is saved before this single POST. Recovery only reads.
      const data = await apiCall("POST", path, body);
      recordJob(data);
      sessionStorage.removeItem(pendingKey);
      message(completed[action]);
      completedResponse = true;
    } catch (error) {
      needsRead = true;
      document.getElementById("result-title").textContent = "Last observed evidence; action response unconfirmed";
      if (currentJob) document.getElementById("job-state").textContent = "Last observed: " + currentJob.job.state.replaceAll("_", " ");
      const known = error instanceof TypeError ? "Response not confirmed. Your request and action context are kept. Refresh job to read state. No retry was sent." : error.message;
      message(known, true);
    } finally {
      setBusy(false);
      if (completedResponse && hadFocus && buttons[action].hidden) {
        const next = Object.entries(buttons).find(([name, button]) => available.has(name) && !button.hidden && !button.disabled);
        if (next) next[1].focus();
      }
    }
  }
  for (const action of Object.keys(sending)) buttons[action].addEventListener("click", () => act(action));
  buttons.refresh.addEventListener("click", refresh);
  reopen.addEventListener("submit", (event) => {
    event.preventDefault();
    const id = document.getElementById("job-id").value;
    if (/^[0-9a-f]{32}$/.test(id)) openJob(id);
  });
  document.addEventListener("draft-opening", () => { draftBusy = true; controls(); });
  document.addEventListener("draft-idle", () => {
    draftBusy = false;
    if (!currentJob && document.getElementById("draft-result").hidden) available.delete("prepare");
    controls();
  });
  document.addEventListener("saved-draft", async (event) => {
    currentDraft = event.detail;
    if (!enabled || busy) return;
    if (currentJob && currentJob.job.draft_id === currentDraft.id) { renderJob(currentJob); return; }
    try {
      remember(contextKey, { draftId: currentDraft.id, jobId: null });
      renderJob(null);
      needsRead = false;
      message("Draft loaded. Prepare a preview; no worker has started.");
      if (sessionStorage.getItem(`unio_draft_${currentDraft.id}_request`)) await refresh();
    } catch (_) { message("Action storage unavailable. Execution actions require saved opaque context.", true); available.clear(); controls(); }
  });
  document.addEventListener("unio-session", async (event) => {
    const data = event.detail;
    enabled = data.execution === true && typeof data.token === "string" && !!data.token;
    token = enabled ? data.token : null;
    reopen.hidden = !enabled;
    panel.hidden = !enabled || !(currentDraft || currentJob);
    controls();
    if (!enabled || initialized) return;
    initialized = true;
    try {
      const hash = location.hash.match(/^#job=([0-9a-f]{32})$/);
      const context = stored(contextKey);
      if (hash || (!location.hash && context && context.jobId)) {
        const id = hash ? hash[1] : context.jobId;
        if (/^[0-9a-f]{32}$/.test(id)) await openJob(id, true);
      } else if (!location.hash && context && /^[0-9a-f]{32}$/.test(context.draftId)) {
        document.getElementById("draft-id").value = context.draftId;
        document.getElementById("reopen-form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      }
      if (stored(pendingKey)) message("An earlier action response was not confirmed. Context is kept; recovery reads state only. No POST was retried.", true);
    } catch (_) {
      message("Saved execution context unavailable. Reopen the job by ID; no action was retried.", true);
    }
  });
})();

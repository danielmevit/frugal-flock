/* Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/unio
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";
  const executionPanel = document.getElementById("execution-panel");
  const jobStatus = document.getElementById("job-status");
  const jobPreviewText = document.getElementById("job-preview-text");
  const jobResultText = document.getElementById("job-result-text");
  
  const buttons = {
    prepare: document.getElementById("job-prepare"),
    approve: document.getElementById("job-approve"),
    start: document.getElementById("job-start"),
    verify: document.getElementById("job-verify"),
    review: document.getElementById("job-review"),
    accept: document.getElementById("job-accept"),
    stop: document.getElementById("job-stop"),
    cancel: document.getElementById("job-cancel"),
    refresh: document.getElementById("job-refresh"),
  };

  let token = null;
  let isExecutionEnabled = false;
  let currentDraft = null;
  let currentJob = null;
  let busy = false;

  function getJobKey(jobId, kind) {
    const storageKey = `unio_job_${jobId}_${kind}`;
    let val = sessionStorage.getItem(storageKey);
    if (!val) {
      val = Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map(b => b.toString(16).padStart(2, "0")).join("");
      sessionStorage.setItem(storageKey, val);
    }
    return val;
  }

  function getDraftKey(draftId) {
    const storageKey = `unio_draft_${draftId}_request`;
    let val = sessionStorage.getItem(storageKey);
    if (!val) {
      val = Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map(b => b.toString(16).padStart(2, "0")).join("");
      sessionStorage.setItem(storageKey, val);
    }
    return val;
  }

  async function checkSession() {
    try {
      const response = await fetch("/api/session", { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      if (data.schema_version === 1 && data.execution) {
        isExecutionEnabled = true;
        token = data.token;
        document.querySelector(".notice").textContent = "Execution mode active. Actual provider API calls will run.";
        document.getElementById("draft-help").textContent = "Save your request to create a draft. You can then prepare it as an execution job.";
      }
    } catch (_) {}
  }

  function setBusy(state, msg, error = false) {
    busy = state;
    for (const key in buttons) {
      buttons[key].disabled = state;
    }
    if (msg) {
      jobStatus.textContent = msg;
      jobStatus.className = error ? "error" : "";
    }
  }

  function renderJob(job) {
    currentJob = job;
    executionPanel.hidden = false;
    
    for (const key in buttons) {
      buttons[key].hidden = true;
    }
    buttons.refresh.hidden = false;
    document.getElementById("job-preview").hidden = true;
    document.getElementById("job-result").hidden = true;

    if (!job) {
      buttons.prepare.hidden = false;
      return;
    }

    if (job.preview) {
      document.getElementById("job-preview").hidden = false;
      const req = job.preview.request;
      const scope = job.preview.scope ? job.preview.scope.join("\n") : "";
      const validate = job.preview.validate ? job.preview.validate.join("\n") : "";
      const workers = `Worker: ${job.preview.worker} (${job.preview.worker_company})\nReviewer: ${job.preview.reviewer} (${job.preview.reviewer_company})`;
      jobPreviewText.textContent = `Request:\n${req}\n\nScope:\n${scope}\n\nValidate:\n${validate}\n\nProviders:\n${workers}`;
    }

    if (job.execution) {
      document.getElementById("job-result").hidden = false;
      let resText = `State: ${job.execution.state}\nLauncher Exit: ${job.execution.launcher_exit !== null ? job.execution.launcher_exit : "null"}\n`;
      if (job.native_result) {
        resText += `\nNative Result:\n`;
        resText += `Stale: ${job.native_result.stale}\nReady: ${job.native_result.ready_for_human_review}\n`;
        if (job.native_result.process) resText += `Process: ${job.native_result.process.state} (Exit: ${job.native_result.process.exit_code})\n`;
        if (job.native_result.validation) {
          resText += `Validation: ${job.native_result.validation.state}\n`;
          if (job.native_result.validation.reasons && job.native_result.validation.reasons.length > 0) {
            resText += `Reasons: ${job.native_result.validation.reasons.join(", ")}\n`;
          }
        }
        if (job.native_result.review) {
          resText += `Review: ${job.native_result.review.state}\n`;
          if (job.native_result.review.reasons && job.native_result.review.reasons.length > 0) {
            resText += `Reasons: ${job.native_result.review.reasons.join(", ")}\n`;
          }
        }
      }
      if (job.acceptance) {
        resText += `\nAcceptance State: ${job.acceptance.state}`;
      }
      jobResultText.textContent = resText;
    }

    const jobState = job.job.state;
    console.log("job state: " + jobState);
    if (jobState === "awaiting_owner_approval") {
      buttons.approve.hidden = false;
      buttons.cancel.hidden = false;
    } else if (jobState === "approved") {
      buttons.start.hidden = false;
      buttons.cancel.hidden = false;
    } else if (jobState === "reserved" || jobState === "completion_unknown") {
      buttons.stop.hidden = false;
      if (jobState === "reserved" && job.execution.state !== "completion_unknown") {
        buttons.verify.hidden = false;
        buttons.review.hidden = false;
        buttons.accept.hidden = false;
      }
      
      const res = job.native_result;
      if (res) {
        if (res.process && res.process.state !== "succeeded") {
           buttons.verify.disabled = true;
           buttons.review.disabled = true;
           buttons.accept.disabled = true;
        }
        if (res.validation && res.validation.state !== "passed") {
           buttons.review.disabled = true;
           buttons.accept.disabled = true;
        }
        if (res.review && res.review.state !== "approved" && res.review.state !== "not_run") {
           buttons.accept.disabled = true;
        }
        if (res.stale) {
           buttons.accept.disabled = true;
        }
      } else {
        buttons.review.disabled = true;
        buttons.accept.disabled = true;
      }
    } else if (jobState === "cancelled") {
      // no actions
    }
  }

  async function apiCall(method, path, body) {
    if (!token) throw new Error("session unavailable");
    const headers = { "X-Unio-Session": token };
    if (body) {
      headers["Content-Type"] = "application/json";
    }
    const response = await fetch(path, {
      method: method,
      cache: "no-store",
      headers: headers,
      ...(body ? { body: JSON.stringify(body) } : {})
    });
    if (response.status === 403) {
      await checkSession();
      throw new Error("Session refreshed. Please try again. No retry was sent.");
    }
    if (!response.ok) {
      let errText = "operation unavailable";
      try {
        const data = await response.json();
        if (data.error) errText = data.error;
      } catch (e) {}
      throw new Error(errText);
    }
    return response.json();
  }

  document.addEventListener("saved-draft", async (e) => {
    currentDraft = e.detail;
    if (!isExecutionEnabled) return;
    
    currentJob = null;
    executionPanel.hidden = false;
    setBusy(false, "Draft loaded. Ready to prepare execution.");
    renderJob(null);
  });

  buttons.prepare.addEventListener("click", async () => {
    if (!currentDraft || busy) return;
    setBusy(true, "Preparing job...");
    try {
      const data = await apiCall("POST", "/api/jobs", {
        draft_id: currentDraft.id,
        expected_hash: currentDraft.content_sha256,
        request_key: getDraftKey(currentDraft.id)
      });
      renderJob(data);
      setBusy(false, "Job prepared.");
    } catch (e) {
      setBusy(false, e.message, true);
    }
  });

  buttons.approve.addEventListener("click", async () => {
    if (!currentJob || busy) return;
    setBusy(true, "Approving job...");
    try {
      const data = await apiCall("POST", `/api/jobs/${currentJob.job.id}/approve`, {
        expected_hash: currentJob.job.draft_sha256,
        approval_key: getJobKey(currentJob.job.id, "approval_key"),
        preview_hash: currentJob.preview.preview_hash
      });
      renderJob(data);
      setBusy(false, "Job approved.");
    } catch (e) {
      setBusy(false, e.message, true);
    }
  });

  buttons.start.addEventListener("click", async () => {
    if (!currentJob || busy) return;
    setBusy(true, "Starting job...");
    try {
      const data = await apiCall("POST", `/api/jobs/${currentJob.job.id}/start`, {
        approval_key: getJobKey(currentJob.job.id, "approval_key"),
        reservation_key: getJobKey(currentJob.job.id, "reservation_key")
      });
      renderJob(data);
      setBusy(false, "Job started.");
    } catch (e) {
      setBusy(false, e.message, true);
    }
  });

  ['verify', 'review', 'stop'].forEach(action => {
    buttons[action].addEventListener("click", async () => {
      if (!currentJob || busy) return;
      setBusy(true, `${action}ing job...`);
      try {
        const data = await apiCall("POST", `/api/jobs/${currentJob.job.id}/${action}`, {
          action_key: getJobKey(currentJob.job.id, `action_key_${action}`)
        });
        renderJob(data);
        setBusy(false, `Job ${action} done.`);
      } catch (e) {
        setBusy(false, e.message, true);
      }
    });
  });

  buttons.cancel.addEventListener("click", async () => {
    if (!currentJob || busy) return;
    setBusy(true, "Cancelling job...");
    try {
      const data = await apiCall("POST", `/api/jobs/${currentJob.job.id}/cancel`, {});
      renderJob(data);
      setBusy(false, "Job cancelled.");
    } catch (e) {
      setBusy(false, e.message, true);
    }
  });

  buttons.accept.addEventListener("click", async () => {
    if (!currentJob || busy) return;
    setBusy(true, "Accepting job...");
    try {
      const data = await apiCall("POST", `/api/jobs/${currentJob.job.id}/accept`, {
        revision_hash: currentJob.native_result ? currentJob.native_result.current_revision.candidate_commit : "",
        action_key: getJobKey(currentJob.job.id, "action_key_accept")
      });
      renderJob(data);
      setBusy(false, "Job accepted.");
    } catch (e) {
      setBusy(false, e.message, true);
    }
  });

  buttons.refresh.addEventListener("click", async () => {
    if (!currentJob || busy) return;
    setBusy(true, "Refreshing job...");
    try {
      const data = await apiCall("GET", `/api/jobs/${currentJob.job.id}`);
      renderJob(data);
      setBusy(false, "Job refreshed.");
    } catch (e) {
      setBusy(false, e.message, true);
    }
  });

  const reopenJobForm = document.getElementById("reopen-job-form");
  if (reopenJobForm) {
    reopenJobForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (busy) return;
      const id = document.getElementById("job-id").value;
      if (!/^[0-9a-f]{32}$/.test(id)) return;
      setBusy(true, "Reopening job...");
      try {
        const data = await apiCall("GET", `/api/jobs/${id}`);
        renderJob(data);
        setBusy(false, "Job reopened.");
      } catch (err) {
        setBusy(false, err.message, true);
      }
    });
  }

  checkSession().then(() => {
    if (isExecutionEnabled && reopenJobForm) {
      reopenJobForm.hidden = false;
    }
  });
})();

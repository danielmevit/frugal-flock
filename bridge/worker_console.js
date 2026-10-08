/* Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/unio
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";
  const section = document.getElementById("worker-console");
  const status = document.getElementById("console-status");
  const workers = document.getElementById("console-workers");
  const panel = document.getElementById("console-panel");
  const outputPanel = document.getElementById("console-output");
  const filesPanel = document.getElementById("console-files");
  const meta = document.getElementById("console-meta");
  const outputText = document.getElementById("console-text");
  const fileMeta = document.getElementById("console-file-meta");
  const fileList = document.getElementById("console-file-list");
  const fileText = document.getElementById("console-file-text");
  const older = document.getElementById("console-older");
  const newer = document.getElementById("console-newer");
  const outputTab = document.getElementById("console-tab-output");
  const filesTab = document.getElementById("console-tab-files");
  const TEXT_LIMIT = 16384;
  const PAGE_LIMIT = 8;
  let token = null;
  let outputOn = false;
  let filesOn = false;
  let timer = 0;
  let running = false;
  let epoch = 0;
  let wantSoon = false;
  let failed = false;
  let backoff = 2000;
  let selectedName = null;
  let selectedProgressId = null;
  let selectedFilesId = null;
  let runId = null;
  let generation = null;
  let tab = "output";
  let fileId = null;
  let pages = [];
  let pageIndex = 0;
  let note = "";

  function text(tag, value, className) {
    const element = document.createElement(tag);
    element.textContent = value;
    if (className) element.className = className;
    return element;
  }
  function say(value) {
    if (status.textContent !== value) status.textContent = value;
  }
  function plan(ms) {
    clearTimeout(timer);
    timer = 0;
    if ((!outputOn && !filesOn) || document.hidden) return;
    timer = setTimeout(run, ms);
  }
  function resetPages() {
    pages = [];
    pageIndex = 0;
    runId = null;
    generation = null;
    outputText.textContent = "";
  }
  function clearObservation() {
    workers.replaceChildren();
    resetPages();
    fileId = null;
    fileList.replaceChildren();
    fileText.textContent = "";
    fileMeta.textContent = "";
    meta.textContent = "";
    panel.hidden = true;
  }
  function shutdown(message) {
    epoch += 1;
    outputOn = false;
    filesOn = false;
    token = null;
    clearTimeout(timer);
    clearObservation();
    section.hidden = true;
    say(message);
  }
  function ageOf(iso) {
    const then = Date.parse(iso);
    if (!Number.isFinite(then)) return "Observed " + iso;
    const seconds = Math.max(0, Math.round((Date.now() - then) / 1000));
    return "Observed " + iso + " · age " + seconds + "s";
  }
  function recorded(view) {
    if (view.state === "unavailable" || !view.output) return "Unavailable. No owned Source run is claimed.";
    const source = view.source || {};
    const verification = view.verification || {};
    const review = view.review || {};
    const acceptance = view.acceptance || {};
    const output = view.output;
    const exitCode = source.exit_code === null || source.exit_code === undefined ? "none" : String(source.exit_code);
    let line = "Recorded source " + (source.state || "unavailable")
      + " · exit " + exitCode
      + " · verification " + (verification.state || "unavailable")
      + " · review " + (review.state || "unavailable")
      + " · acceptance " + (acceptance.state || "unavailable")
      + " · liveness " + (view.observed_liveness || "unknown")
      + " · phase " + (view.observed_phase || "unknown")
      + " · output " + (output.state || "unavailable");
    if (view.observation_stale === true) line += " · observation stale";
    if (view.recorded_evidence_stale === true) line += " · recorded evidence stale";
    if (output.state === "quiet") line += " · quiet does not prove completion or failure";
    if (output.state === "first_output_wait") line += " · no Source record yet";
    if (output.state === "missing") line += " · Source log is missing";
    return line;
  }
  function chooseTab(next) {
    tab = next;
    const output = next === "output";
    outputTab.setAttribute("aria-selected", output ? "true" : "false");
    filesTab.setAttribute("aria-selected", output ? "false" : "true");
    outputPanel.hidden = !output;
    filesPanel.hidden = output;
  }
  function showOutputPage() {
    const page = pages[pageIndex];
    older.disabled = pageIndex <= 0;
    newer.disabled = !page || page.atEnd !== false || !page.next;
    if (!page) {
      outputText.textContent = "";
      return;
    }
    outputText.textContent = page.text;
    const bits = [recorded(page.view)];
    if (page.view.observed_at) bits.unshift(ageOf(page.view.observed_at));
    if (page.view.output.modified_at) bits.push("Log modified " + page.view.output.modified_at);
    if (page.atEnd === true) bits.push("This page reached the current end of the observed log. That is not execution completion.");
    if (page.partial === true) bits.push("A partial record is held until the next newline.");
    if (page.discarded) bits.push("Earlier displayed pages were discarded to bound this panel.");
    if (note) bits.push(note);
    meta.textContent = bits.join(" ");
  }
  function remember(view, requestedCursor) {
    const output = view.output;
    if (!output || typeof output.text !== "string") throw Object.assign(new Error("http"), { status: 503 });
    if (runId && view.run_id !== runId) {
      note = "The latest run changed. Previous pages were reset.";
      pages = [];
      pageIndex = 0;
    }
    if (generation && output.generation && output.generation !== generation) {
      note = "The Source generation changed. Showing a new observation from the start.";
      if (requestedCursor) {
        pages = [];
        pageIndex = 0;
        runId = view.run_id;
        generation = output.generation;
        return false;
      }
    }
    runId = view.run_id;
    generation = output.generation;
    let shown = output.text;
    if (shown.length > TEXT_LIMIT) shown = shown.slice(0, TEXT_LIMIT);
    const entry = {
      cursor: requestedCursor,
      next: typeof output.next_cursor === "string" ? output.next_cursor : null,
      text: shown,
      atEnd: output.at_end === true,
      partial: output.partial_record === true,
      view: view,
      discarded: false,
    };
    if (!requestedCursor) {
      pages = [entry];
      pageIndex = 0;
    } else if (pages[pageIndex] && pages[pageIndex].cursor === requestedCursor) {
      pages[pageIndex] = entry;
    } else {
      pages = pages.slice(0, pageIndex + 1);
      pages.push(entry);
      pageIndex = pages.length - 1;
      if (pages.length > PAGE_LIMIT) {
        pages = pages.slice(pages.length - PAGE_LIMIT);
        pages[0].discarded = true;
        pageIndex = pages.length - 1;
      }
    }
    showOutputPage();
    return true;
  }
  async function getJSON(path) {
    if (!token) throw Object.assign(new Error("session"), { session: true });
    let response;
    try {
      response = await fetch(path, { cache: "no-store", headers: { "X-Unio-Session": token } });
    } catch (_) {
      throw Object.assign(new Error("network"), { network: true });
    }
    if (response.status === 403) {
      await new Promise((resolve, reject) => {
        document.dispatchEvent(new CustomEvent("refresh-session", { detail: { resolve, reject } }));
      });
      throw Object.assign(new Error("session"), { session: true });
    }
    if (!response.ok) {
      let body = null;
      try { body = await response.json(); } catch (_) { body = null; }
      throw Object.assign(new Error("http"), { status: response.status, body: body });
    }
    return response.json();
  }
  function outputPath() {
    return "/api/progress/workers/" + selectedProgressId + "/runs/" + runId + "/output";
  }
  async function loadOutput(ticket) {
    if (!selectedProgressId) return;
    if (!runId) {
      const listed = await getJSON("/api/progress/workers/" + selectedProgressId);
      if (ticket !== epoch) return;
      if (!listed.run_id) {
        meta.textContent = recorded(listed);
        outputText.textContent = "";
        older.disabled = true;
        newer.disabled = true;
        return;
      }
      runId = listed.run_id;
    }
    const current = pages[pageIndex];
    const cursor = current ? current.cursor : null;
    const path = outputPath() + (cursor ? "?cursor=" + encodeURIComponent(cursor) : "");
    try {
      const view = await getJSON(path);
      if (ticket !== epoch) return;
      if (remember(view, cursor) === false) {
        note = "The Source generation changed. Showing a new observation from the start.";
        say(note);
        const fresh = await getJSON("/api/progress/workers/" + selectedProgressId + "/runs/" + view.run_id + "/output");
        if (ticket !== epoch) return;
        remember(fresh, null);
      }
    } catch (error) {
      if (error.status === 503 || (error.status === 404 && !cursor)) {
        outputText.textContent = "";
        meta.textContent = "Source output is unavailable. No current page is claimed.";
        older.disabled = true;
        newer.disabled = true;
        return;
      }
      if (error.status === 409 && cursor) {
        note = "The Source generation or run changed. Showing a new observation from the start.";
        say(note);
        resetPages();
        const listed = await getJSON("/api/progress/workers/" + selectedProgressId);
        if (ticket !== epoch || !listed.run_id) return;
        runId = listed.run_id;
        const fresh = await getJSON(outputPath());
        if (ticket !== epoch) return;
        remember(fresh, null);
        return;
      }
      throw error;
    }
  }
  async function loadFiles(ticket) {
    if (!selectedFilesId) {
      fileMeta.textContent = "No file grant for this worker. Worktree files stay unavailable.";
      fileList.replaceChildren();
      fileText.textContent = "";
      return;
    }
    const listing = await getJSON("/api/worker-files/workers/" + selectedFilesId + "/files");
    if (ticket !== epoch || listing.schema_version !== 1 || !Array.isArray(listing.files)) {
      throw Object.assign(new Error("http"), { status: 503 });
    }
    fileList.replaceChildren();
    const seen = new Set();
    for (const file of listing.files) {
      if (!file || typeof file.file_id !== "string" || typeof file.relative_path !== "string") continue;
      seen.add(file.file_id);
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = file.relative_path;
      button.setAttribute("aria-pressed", file.file_id === fileId ? "true" : "false");
      button.addEventListener("click", () => {
        fileId = file.file_id;
        fileText.textContent = "";
        wantSoon = true;
        if (!running) plan(200);
      });
      item.append(button);
      fileList.append(item);
    }
    const suffix = listing.truncated === true ? " Tracked file list truncated at 256 paths." : "";
    fileMeta.textContent = "Tracked source text only." + suffix + " Filename exclusions do not prove the remaining text is secret-free.";
    if (fileId && !seen.has(fileId)) {
      fileId = null;
      fileText.textContent = "";
      fileMeta.textContent += " The previously selected file is not in this list.";
    }
    if (!fileId) return;
    let preview;
    try {
      preview = await getJSON("/api/worker-files/workers/" + selectedFilesId + "/files/" + fileId);
    } catch (error) {
      if (error.status === 503 || error.status === 404) {
        fileText.textContent = "";
        fileMeta.textContent += " File content is unavailable.";
        return;
      }
      throw error;
    }
    if (ticket !== epoch || typeof preview.text !== "string") return;
    fileText.textContent = preview.text;
    fileMeta.textContent += preview.truncated === true ? " Preview truncated at 64 KiB." : " Full observed text is shown.";
    if (preview.observed_at) fileMeta.textContent += " " + ageOf(preview.observed_at);
  }
  function render(progress, fileWorkers) {
    const byName = new Map();
    if (progress && Array.isArray(progress.workers)) {
      for (const view of progress.workers) {
        if (view && typeof view.worker === "string") byName.set(view.worker, { progress: view });
      }
    }
    if (Array.isArray(fileWorkers)) {
      for (const row of fileWorkers) {
        if (!row || typeof row.worker !== "string") continue;
        const slot = byName.get(row.worker) || {};
        slot.files = row;
        byName.set(row.worker, slot);
      }
    }
    if (selectedName && !byName.has(selectedName)) {
      selectedName = null;
      selectedProgressId = null;
      selectedFilesId = null;
      panel.hidden = true;
      resetPages();
    }
    workers.replaceChildren();
    if (!byName.size) {
      workers.append(text("p", "No granted worker is currently listed.", "small"));
    }
    for (const [name, slot] of byName) {
      const view = slot.progress;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "console-worker";
      button.setAttribute("aria-controls", "console-panel");
      button.setAttribute("aria-expanded", selectedName === name && !panel.hidden ? "true" : "false");
      button.dataset.worker = name;
      button.dataset.task = view && typeof view.task === "string" ? view.task : "";
      button.dataset.output = outputOn && view ? "true" : "false";
      button.dataset.files = filesOn && slot.files ? "true" : "false";
      const title = view && view.task ? name + " / " + view.task : name;
      const excerpt = view && view.output && typeof view.output.excerpt === "string" && view.output.excerpt
        ? view.output.excerpt : (view ? "No filtered excerpt in this observation." : "Source output is not enabled. No Source excerpt is claimed.");
      button.append(
        text("strong", title),
        text("span", view && view.observed_at ? ageOf(view.observed_at) : "Observation age unavailable", "small"),
        text("span", view ? recorded(view) : "Files grant only. No Source state is claimed.", "small"),
        text("span", excerpt, "console-excerpt"),
      );
      button.addEventListener("click", () => {
        if (selectedName === name && !panel.hidden) {
          chooseTab(outputOn ? "output" : "files");
          return;
        }
        selectedName = name;
        panel.hidden = false;
        note = "";
        resetPages();
        fileId = null;
        fileText.textContent = "";
        epoch += 1;
        chooseTab(outputOn ? "output" : "files");
        wantSoon = true;
        if (!running) plan(200);
      });
      workers.append(button);
      if (selectedName === name) {
        const nextProgress = view && typeof view.worker_id === "string" ? view.worker_id : null;
        const nextFiles = slot.files && typeof slot.files.worker_id === "string" ? slot.files.worker_id : null;
        if (selectedProgressId && nextProgress && selectedProgressId !== nextProgress) {
          note = "The latest task changed. Previous output pages were reset.";
          resetPages();
        }
        selectedProgressId = nextProgress;
        selectedFilesId = nextFiles;
      }
    }
    say(note || (outputOn ? "Source observation is reading granted workers." : "Worktree file observation is reading granted workers."));
  }
  function failure(error) {
    clearObservation();
    selectedName = null;
    if (error && error.session) {
      backoff = 2000;
      say("Session refreshed. No action was replayed. No current output is claimed until the next read.");
      return;
    }
    backoff = 5000;
    const code = error && error.body && error.body.error;
    if (code === "progress_unavailable" || error && error.status === 503 && outputOn) {
      say("Source observation is unavailable. No current output is claimed.");
      return;
    }
    if (code === "files_unavailable") {
      say("File observation is unavailable. No current file text is claimed.");
      return;
    }
    say("Connection unavailable. No current output or files are claimed.");
  }
  async function once(ticket) {
    let progress = null;
    let fileWorkers = null;
    if (outputOn) {
      progress = await getJSON("/api/progress/workers");
      if (ticket !== epoch) return;
      if (!progress || progress.schema_version !== 1 || !Array.isArray(progress.workers)) {
        throw Object.assign(new Error("http"), { status: 503 });
      }
    }
    if (filesOn) {
      const body = await getJSON("/api/worker-files/workers");
      if (ticket !== epoch) return;
      if (!body || body.schema_version !== 1 || !Array.isArray(body.workers)) {
        throw Object.assign(new Error("http"), { status: 503 });
      }
      fileWorkers = body.workers;
    }
    if (ticket !== epoch) return;
    render(progress, fileWorkers);
    if (panel.hidden) return;
    if (tab === "output" && outputOn) await loadOutput(ticket);
    if (tab === "files") {
      if (!filesOn) {
        fileList.replaceChildren();
        fileText.textContent = "";
        fileMeta.textContent = "Worktree files are not enabled for this preview.";
      } else await loadFiles(ticket);
    }
    note = "";
  }
  async function run() {
    if (running || (!outputOn && !filesOn)) return;
    running = true;
    const ticket = epoch;
    failed = false;
    try {
      await once(ticket);
    } catch (error) {
      if (ticket === epoch) {
        failed = true;
        failure(error);
      }
    } finally {
      running = false;
      if (outputOn || filesOn) {
        const wait = wantSoon ? 200 : (failed ? backoff : 2000);
        wantSoon = false;
        plan(wait);
      }
    }
  }
  outputTab.addEventListener("click", () => {
    chooseTab("output");
    wantSoon = true;
    if (!running) plan(200);
  });
  filesTab.addEventListener("click", () => {
    chooseTab("files");
    wantSoon = true;
    if (!running) plan(200);
  });
  older.addEventListener("click", () => {
    if (pageIndex <= 0) return;
    pageIndex -= 1;
    showOutputPage();
  });
  newer.addEventListener("click", () => {
    const page = pages[pageIndex];
    if (!page || page.atEnd !== false || !page.next) return;
    if (pages[pageIndex + 1]) {
      pageIndex += 1;
      showOutputPage();
      return;
    }
    pages = pages.slice(0, pageIndex + 1);
    pages.push({ cursor: page.next, text: "", atEnd: null, partial: false, view: page.view, next: null, discarded: false });
    pageIndex += 1;
    wantSoon = true;
    if (!running) plan(200);
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && (outputOn || filesOn) && !running) plan(200);
  });
  document.addEventListener("unio-session", (event) => {
    const data = event.detail || {};
    const next = typeof data.token === "string" ? data.token : null;
    const output = data.progress_output === true && !!next;
    const files = data.worker_files === true && !!next;
    const changed = next !== token || output !== outputOn || files !== filesOn;
    token = next;
    outputOn = output;
    filesOn = files;
    if (!outputOn && !filesOn) {
      shutdown("Worker output and files are off. No Source excerpt or worktree text is claimed.");
      return;
    }
    section.hidden = false;
    if (changed) {
      epoch += 1;
      clearObservation();
      selectedName = null;
      note = "Session updated. Reading the current observation. No action was replayed.";
      say(note);
      wantSoon = true;
      if (!running) plan(200);
    } else if (!running && !timer) {
      plan(200);
    }
  });

  // Local map requests carry only an exact worker and task identity. Anything
  // else is ignored; no request opens a worker the console has not listed.
  document.addEventListener("unio-open-console", (event) => {
    const detail = event.detail;
    if (!detail || typeof detail !== "object" || Array.isArray(detail)) return;
    const proto = Object.getPrototypeOf(detail);
    if (proto !== Object.prototype && proto !== null) return;
    const worker = detail.worker;
    const task = detail.task;
    if (typeof worker !== "string" || !worker || typeof task !== "string") return;
    const match = Array.from(workers.querySelectorAll("button.console-worker"))
      .find((b) => b.dataset.worker === worker && b.dataset.task === task);
    if (!match) return;
    match.click();
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    section.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "start" });
  });
})();

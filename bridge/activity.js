/* Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/unio
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const themeSelector = document.getElementById("theme-selector");
  const STORAGE_KEY = "unio-theme-preference";
  const mql = window.matchMedia("(prefers-color-scheme: dark)");

  // The live selected preference is the authority. Storage only seeds it on
  // load, so a denied or failing store never overrides an explicit choice.
  function normalTheme(value) {
    return value === "light" || value === "dark" ? value : "system";
  }
  function storedTheme() {
    try {
      return normalTheme(localStorage.getItem(STORAGE_KEY));
    } catch (_) {
      return "system";
    }
  }
  let themePreference = storedTheme();

  function applyTheme() {
    const actual = themePreference === "system" ? (mql.matches ? "dark" : "light") : themePreference;
    document.documentElement.dataset.theme = actual;
    document.documentElement.dataset.themePreference = themePreference;
  }

  if (themeSelector) {
    themeSelector.value = themePreference;
    themeSelector.addEventListener("change", () => {
      themePreference = normalTheme(themeSelector.value);
      themeSelector.value = themePreference;
      try {
        localStorage.setItem(STORAGE_KEY, themePreference);
      } catch (_) {}
      applyTheme();
    });
  }
  mql.addEventListener("change", applyTheme);
  applyTheme();

  const status = document.getElementById("status");
  let busy = false;

  let currentView = window.innerWidth >= 1000 ? "map" : "list";
  let mapHistoryVisible = false;
  let mapSearchQuery = "";
  let mapWorkerFilter = "";
  let mapStateFilter = "";
  let mapCurrentPage = 0;
  let mapFitView = false;
  const MAP_PAGE_SIZE = 24;
  let lastData = null;
  // Selection is an exact node key plus its tuple; never a display label.
  let selected = null;

  function updateViewSwitch() {
    const mapBtn = document.getElementById("view-map");
    const listBtn = document.getElementById("view-list");
    if (mapBtn && listBtn) {
      mapBtn.setAttribute("aria-pressed", currentView === "map" ? "true" : "false");
      listBtn.setAttribute("aria-pressed", currentView === "list" ? "true" : "false");
      document.getElementById("tasks-map-container").hidden = currentView !== "map";
      document.getElementById("tasks").hidden = currentView !== "list";
    }
  }

  const mapBtn = document.getElementById("view-map");
  if (mapBtn) {
    mapBtn.addEventListener("click", () => { currentView = "map"; updateViewSwitch(); if (lastData) render(lastData); });
    document.getElementById("view-list").addEventListener("click", () => { currentView = "list"; updateViewSwitch(); if (lastData) render(lastData); });
    document.getElementById("map-history-toggle").addEventListener("change", (e) => { mapHistoryVisible = e.target.checked; mapCurrentPage = 0; if (lastData) render(lastData); });
    document.getElementById("map-search").addEventListener("input", (e) => { mapSearchQuery = e.target.value.toLowerCase(); mapCurrentPage = 0; if (lastData) render(lastData); });
    document.getElementById("map-worker-filter").addEventListener("change", (e) => { mapWorkerFilter = e.target.value; mapCurrentPage = 0; if (lastData) render(lastData); });
    document.getElementById("map-state-filter").addEventListener("change", (e) => { mapStateFilter = e.target.value; mapCurrentPage = 0; if (lastData) render(lastData); });
    document.getElementById("map-prev-page").addEventListener("click", () => { mapCurrentPage = Math.max(0, mapCurrentPage - 1); if (lastData) render(lastData); });
    document.getElementById("map-next-page").addEventListener("click", () => { mapCurrentPage++; if (lastData) render(lastData); });
    document.getElementById("map-fit").addEventListener("click", () => { mapFitView = true; applyMapPresentation(); });
    document.getElementById("map-reset").addEventListener("click", () => { mapFitView = false; applyMapPresentation(); });
    updateViewSwitch();
    applyMapPresentation();
  }

  function text(tag, value, className = "") {
    const element = document.createElement(tag);
    element.textContent = value;
    element.className = className;
    return element;
  }
  function setText(element, value) {
    if (element.textContent !== value) element.textContent = value;
  }
  function label(value) {
    return String(value).replaceAll("_", " ");
  }

  function render(data) {
    lastData = data;
    if (currentView === "map") { renderMap(data); }

    const tasks = document.getElementById("tasks");
    tasks.replaceChildren();
    for (const result of data.results) {
      const row = text("div", "", "row");
      const identity = text("div", "");
      identity.append(text("strong", result.worker + " / " + result.task));
      identity.append(
        text("p", "Recorded at " + (result.recorded_at || "unknown")),
      );
      const state = text("div", "", "data");
      state.append(
        text(
          "span",
          result.activity.replaceAll("_", " "),
          "chip" +
            (result.activity === "completion_unknown" ||
            result.process.state === "failed"
              ? " warn"
              : ""),
        ),
      );
      state.append(
        text(
          "p",
          "Process " +
            result.process.state.replaceAll("_", " ") +
            " · exit " +
            (result.process.exit_code ?? "unknown") +
            " · worker lock " +
            result.worker_lock,
        ),
      );
      state.append(
        text(
          "p",
          "Validation " +
            result.validation.state.replaceAll("_", " ") +
            " · " +
            result.validation.checks_run +
            " checks / " +
            result.validation.checks_failed +
            " failed",
        ),
      );
      state.append(
        text(
          "p",
          "Review " +
            result.review.state.replaceAll("_", " ") +
            " · reviewer " +
            (result.review.reviewer || "not recorded"),
        ),
      );
      if (result.activity === "completion_unknown")
        state.append(
          text(
            "p",
            "No completion recorded; interruption possible. Detached processes are not ruled out.",
          ),
        );
      row.append(identity, state);
      tasks.append(row);
    }
    if (!data.results.length)
      tasks.append(text("p", "No structured task evidence yet.", "small"));
    const limits = document.getElementById("limits");
    limits.replaceChildren();
    for (const agent of data.agents) {
      const row = text("div", "", "row");
      row.append(text("strong", agent.name));
      const info = text("div", "", "data");
      info.append(
        text(
          "span",
          agent.bench.off ? "OFF" : "on",
          "chip" + (agent.bench.off ? " warn" : ""),
        ),
      );
      info.append(
        text(
          "p",
          "Binary " +
            (agent.binary.present === null
              ? "unknown"
              : agent.binary.present
                ? "installed"
                : "missing") +
            " · authentication unknown · capacity unknown",
        ),
      );
      if (agent.bench.operator_retry_at !== null)
        info.append(
          text(
            "p",
            "Operator retry epoch " +
              agent.bench.operator_retry_at +
              "; not a provider reset.",
          ),
        );
      row.append(info);
      limits.append(row);
    }
    if (!data.agents.length)
      limits.append(text("p", "No tool observations recorded. Authentication and capacity remain unknown.", "small"));
    for (const retry of data.retries)
      limits.append(
        text(
          "p",
          retry.task +
            ": " +
            retry.failed_attempts +
            " failed attempts · " +
            (retry.blocked
              ? "BLOCKED"
              : retry.retry_granted
                ? "one retry granted"
                : "brake clear"),
          "small",
        ),
      );
    document.getElementById("events").textContent = JSON.stringify(
      { recent_events: data.recent_events, warnings: data.warnings },
      null,
      2,
    );
    status.className = "";
    status.textContent =
      "Observed " +
      data.observed_at +
      " · STOP " +
      (data.stopped ? "active" : "clear");
  }

  // JSON arrays cannot collide for different tuples, whatever the names hold.
  function taskKey(worker, task) { return JSON.stringify(["task", worker, task]); }
  function workerKey(worker) { return JSON.stringify(["worker", worker]); }
  const HUB_KEY = JSON.stringify(["hub"]);

  function sectionState(r, name) {
    const section = r && r[name];
    return section && typeof section.state === "string" ? section.state : "unavailable";
  }

  // Process success is not acceptance. Only fully passed and approved records
  // collapse into history; every failed, unknown, incomplete, stale or
  // unreviewed record stays visible as needing attention.
  function classify(r) {
    const process = sectionState(r, "process");
    const validation = sectionState(r, "validation");
    const review = sectionState(r, "review");
    const reasons = [];
    if (process === "running") {
      if (r.activity === "running_recorded") return { category: "active", reasons: ["process running"] };
      reasons.push("process running without a held worker lock; completion unknown");
    } else if (process !== "succeeded") {
      reasons.push("process " + label(process));
    }
    if (r.activity === "completion_unknown" && process !== "running") reasons.push("completion unknown");
    if (validation !== "passed") reasons.push("validation " + label(validation));
    if (review !== "approved") reasons.push("review " + label(review));
    if (r.stale === true) reasons.push("recorded evidence stale");
    return reasons.length ? { category: "attention", reasons } : { category: "finished", reasons: [] };
  }
  const CATEGORY_TEXT = {
    active: "Active",
    attention: "Needs attention",
    finished: "Finished (checks passed and review approved; not your acceptance)",
  };

  function mapLayer(svg, name) {
    let layer = svg.querySelector(':scope > g[data-layer="' + name + '"]');
    if (!layer) {
      layer = document.createElementNS(SVG_NS, "g");
      layer.dataset.layer = name;
      if (name === "links") svg.insertBefore(layer, svg.firstChild);
      else svg.appendChild(layer);
    }
    return layer;
  }

  function applyMapPresentation() {
    const svg = document.getElementById("work-map");
    const fit = document.getElementById("map-fit");
    if (!svg) return;
    const height = Number(svg.dataset.contentHeight) || 200;
    svg.setAttribute("viewBox", "0 0 800 " + height);
    if (mapFitView) {
      const available = (svg.parentElement && svg.parentElement.clientWidth) || 800;
      svg.style.width = "100%";
      svg.style.height = Math.max(120, Math.min(480, Math.ceil(height * available / 800))) + "px";
    } else {
      svg.style.width = "800px";
      svg.style.height = height + "px";
    }
    svg.dataset.view = mapFitView ? "fit" : "actual";
    if (fit) fit.setAttribute("aria-pressed", mapFitView ? "true" : "false");
  }

  function syncWorkerOptions(names) {
    const select = document.getElementById("map-worker-filter");
    const wanted = Array.from(new Set(names)).sort();
    const desired = [{ value: "", text: "All Workers" }].concat(wanted.map((w) => ({ value: w, text: w })));
    if (mapWorkerFilter && !wanted.includes(mapWorkerFilter))
      desired.push({ value: mapWorkerFilter, text: mapWorkerFilter + " (not in current observation)" });
    const existing = new Map(Array.from(select.options).map((option) => [option.value, option]));
    desired.forEach((want, index) => {
      let option = existing.get(want.value);
      existing.delete(want.value);
      if (!option) {
        option = document.createElement("option");
        option.value = want.value;
      }
      setText(option, want.text);
      if (select.options[index] !== option) select.insertBefore(option, select.options[index] || null);
    });
    for (const option of existing.values()) option.remove();
    if (select.value !== mapWorkerFilter) select.value = mapWorkerFilter;
  }

  function createNodeGroup() {
    const g = document.createElementNS(SVG_NS, "g");
    const rect = document.createElementNS(SVG_NS, "rect");
    const title = document.createElementNS(SVG_NS, "title");
    const textLabel = document.createElementNS(SVG_NS, "text");
    const textState = document.createElementNS(SVG_NS, "text");
    textLabel.setAttribute("class", "node-label");
    textState.setAttribute("class", "node-state");
    rect.setAttribute("x", -60);
    rect.setAttribute("y", -18);
    rect.setAttribute("width", 120);
    rect.setAttribute("height", 36);
    rect.setAttribute("rx", 5);
    rect.setAttribute("fill", "var(--paper)");
    for (const node of [textLabel, textState]) {
      node.setAttribute("text-anchor", "middle");
      node.style.pointerEvents = "none";
    }
    textLabel.setAttribute("y", "-2");
    textLabel.setAttribute("fill", "var(--text-main)");
    textLabel.setAttribute("font-size", "12px");
    textState.setAttribute("y", "10");
    textState.setAttribute("fill", "var(--muted)");
    textState.setAttribute("font-size", "10px");
    g.append(rect, title, textLabel, textState);
    g.setAttribute("role", "button");
    g.setAttribute("tabindex", "0");
    g.style.cursor = "pointer";
    // Handlers read the group's current dataset, never a captured record.
    g.addEventListener("click", () => selectNode(g));
    g.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectNode(g);
      }
    });
    return g;
  }

  function selectNode(g) {
    if (!lastData || !g.isConnected) return;
    selected = {
      key: g.dataset.nodeKey,
      kind: g.dataset.kind,
      worker: g.dataset.worker,
      task: g.dataset.task,
    };
    renderMap(lastData);
  }

  function clearSelection() {
    selected = null;
    clearDetails();
    const svg = document.getElementById("work-map");
    if (svg) svg.focus({ preventScroll: true });
    if (lastData) renderMap(lastData);
  }

  // Order children without moving the focused group, so focus survives.
  function orderGroups(layer, ordered) {
    const current = Array.from(layer.children);
    if (current.length === ordered.length && current.every((g, i) => g === ordered[i])) return;
    const active = document.activeElement;
    const anchorIndex = ordered.indexOf(active);
    if (anchorIndex < 0) {
      for (const g of ordered) layer.appendChild(g);
      return;
    }
    const anchor = ordered[anchorIndex];
    for (let i = 0; i < anchorIndex; i++) layer.insertBefore(ordered[i], anchor);
    let previous = anchor;
    for (let i = anchorIndex + 1; i < ordered.length; i++) {
      layer.insertBefore(ordered[i], previous.nextSibling);
      previous = ordered[i];
    }
  }

  function renderMap(data) {
    const svg = document.getElementById("work-map");
    const countsSpan = document.getElementById("map-counts");
    const pagination = document.getElementById("map-pagination");
    const prevBtn = document.getElementById("map-prev-page");
    const nextBtn = document.getElementById("map-next-page");
    const pageInfo = document.getElementById("map-page-info");

    syncWorkerOptions(data.results.map((r) => r.worker));

    const filtered = [];
    const categories = new Map();
    const tally = { active: 0, attention: 0, finished: 0 };

    for (const r of data.results) {
      const verdict = classify(r);
      categories.set(r, verdict);
      tally[verdict.category]++;
      const isFinished = verdict.category === "finished";
      // The Finished filter exposes history without the separate toggle.
      if (isFinished && !mapHistoryVisible && mapStateFilter !== "finished") continue;
      if (mapWorkerFilter && r.worker !== mapWorkerFilter) continue;
      if (mapStateFilter && verdict.category !== mapStateFilter) continue;
      const stateStr = (sectionState(r, "process") + " " + r.activity + " " + sectionState(r, "validation") + " " + sectionState(r, "review") + " " + verdict.category).toLowerCase();
      const searchMatch = !mapSearchQuery ||
          r.worker.toLowerCase().includes(mapSearchQuery) ||
          r.task.toLowerCase().includes(mapSearchQuery) ||
          stateStr.includes(mapSearchQuery);
      if (searchMatch) filtered.push(r);
    }

    let counts = data.results.length + " total tasks (" + tally.attention + " need attention, " + tally.active + " active, " + tally.finished + " finished) · " + filtered.length + " shown";
    if (mapWorkerFilter && !data.results.some((r) => r.worker === mapWorkerFilter))
      counts += " · worker " + mapWorkerFilter + " is not in the current observation";
    setText(countsSpan, counts);

    filtered.sort((a, b) => {
      if (a.worker !== b.worker) return a.worker < b.worker ? -1 : 1;
      return a.task < b.task ? -1 : a.task > b.task ? 1 : 0;
    });

    const totalPages = Math.ceil(filtered.length / MAP_PAGE_SIZE);
    if (mapCurrentPage >= totalPages) mapCurrentPage = Math.max(0, totalPages - 1);
    const pageTasks = filtered.slice(mapCurrentPage * MAP_PAGE_SIZE, (mapCurrentPage + 1) * MAP_PAGE_SIZE);

    if (filtered.length > MAP_PAGE_SIZE) {
      pagination.hidden = false;
      setText(pageInfo, "Page " + (mapCurrentPage + 1) + " of " + (totalPages || 1));
      prevBtn.disabled = mapCurrentPage === 0;
      nextBtn.disabled = mapCurrentPage >= totalPages - 1;
    } else {
      pagination.hidden = true;
      setText(pageInfo, "");
    }

    const workers = Array.from(new Set(pageTasks.map((r) => r.worker))).sort();
    const workerX = 250, taskX = 550;
    let currentY = 50;
    let wY = 50;
    const nodes = [];
    const links = [];
    const hub = { key: HUB_KEY, kind: "hub", label: "Project Hub", x: 50, y: 50 };
    nodes.push(hub);
    for (const w of workers) {
      const y = Math.max(wY, currentY);
      const own = pageTasks.filter((r) => r.worker === w);
      const workerNode = { key: workerKey(w), kind: "worker", label: w, worker: w, x: workerX, y: y, count: own.length };
      nodes.push(workerNode);
      links.push([hub, workerNode]);
      own.forEach((r, index) => {
        const taskNode = { key: taskKey(r.worker, r.task), kind: "task", label: r.task, worker: r.worker, task: r.task, x: taskX, y: y + index * 40, data: r, verdict: categories.get(r) };
        nodes.push(taskNode);
        links.push([workerNode, taskNode]);
      });
      currentY = y + own.length * 40 + 20;
      wY += 60;
    }

    svg.dataset.contentHeight = String(Math.max(200, currentY));
    applyMapPresentation();

    const linkLayer = mapLayer(svg, "links");
    const nodeLayer = mapLayer(svg, "nodes");
    linkLayer.replaceChildren(...links.map(([src, tgt]) => {
      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("x1", src.x + 60);
      line.setAttribute("y1", src.y);
      line.setAttribute("x2", tgt.x - 60);
      line.setAttribute("y2", tgt.y);
      line.setAttribute("stroke", "var(--line)");
      line.setAttribute("stroke-width", "2");
      return line;
    }));

    // Reuse the same group for the same exact key; remove only obsolete ones.
    const existing = new Map();
    for (const g of Array.from(nodeLayer.children)) {
      if (g.dataset.nodeKey && !existing.has(g.dataset.nodeKey)) existing.set(g.dataset.nodeKey, g);
      else g.remove();
    }
    const ordered = [];
    for (const n of nodes) {
      let g = existing.get(n.key);
      existing.delete(n.key);
      if (!g) g = createNodeGroup();
      g.dataset.nodeKey = n.key;
      g.dataset.kind = n.kind;
      if (n.worker !== undefined) g.dataset.worker = n.worker; else delete g.dataset.worker;
      if (n.task !== undefined) g.dataset.task = n.task; else delete g.dataset.task;
      const isSelected = !!selected && selected.key === n.key;
      g.setAttribute("transform", "translate(" + n.x + ", " + n.y + ")");
      g.setAttribute("aria-pressed", isSelected ? "true" : "false");
      let description = n.label;
      let stateText = "";
      let aria = "Project hub";
      if (n.kind === "worker") {
        aria = "Worker " + n.worker + ", " + n.count + (n.count === 1 ? " task" : " tasks") + " shown";
      } else if (n.kind === "task") {
        const r = n.data;
        const facts = "process " + label(sectionState(r, "process")) + ", validation " + label(sectionState(r, "validation")) + ", review " + label(sectionState(r, "review"));
        aria = "Task " + r.task + " on worker " + r.worker + ". " + (n.verdict.category === "finished" ? "Finished" : CATEGORY_TEXT[n.verdict.category]) + ": " + facts + ".";
        description = r.worker + " / " + r.task + "\nProcess: " + sectionState(r, "process") + "\nValidation: " + sectionState(r, "validation") + "\nReview: " + sectionState(r, "review");
        stateText = sectionState(r, "process") !== "succeeded" ? sectionState(r, "process") : (sectionState(r, "validation") !== "passed" ? sectionState(r, "validation") : sectionState(r, "review"));
        g.dataset.category = n.verdict.category;
      }
      if (n.kind !== "task") delete g.dataset.category;
      if (g.getAttribute("aria-label") !== aria) g.setAttribute("aria-label", aria);
      const rect = g.querySelector("rect");
      rect.setAttribute("stroke", isSelected ? "var(--focus-ring)" : "var(--btn-border)");
      rect.setAttribute("stroke-width", isSelected ? "3" : "1");
      setText(g.querySelector("title"), description);
      setText(g.querySelector(".node-label"), n.label.length > 15 ? n.label.substring(0, 13) + "..." : n.label);
      setText(g.querySelector(".node-state"), stateText.length > 15 ? stateText.substring(0, 13) + "..." : stateText);
      ordered.push(g);
    }
    let lostFocus = false;
    for (const g of existing.values()) {
      if (g === document.activeElement) lostFocus = true;
      g.remove();
    }
    if (lostFocus) svg.focus({ preventScroll: true });
    orderGroups(nodeLayer, ordered);

    renderDetails(data, pageTasks, categories);
  }

  function clearDetails() {
    const details = document.getElementById("map-details");
    details.replaceChildren();
    details.hidden = true;
    delete details.dataset.key;
    delete details.dataset.mode;
  }

  function renderDetails(data, pageTasks, categories) {
    if (!selected || selected.kind !== "task") {
      clearDetails();
      return;
    }
    const r = data.results.find((t) => t.worker === selected.worker && t.task === selected.task);
    if (r && pageTasks.includes(r)) showDetails(r, data, categories.get(r));
    else showMissing(r ? "filtered" : "absent");
  }

  // Build the detail skeleton once per exact selection and mode; later polls
  // only update text, so focused controls are never replaced.
  function detailsFor(mode, build) {
    const details = document.getElementById("map-details");
    details.hidden = false;
    if (details.dataset.key !== selected.key || details.dataset.mode !== mode) {
      details.replaceChildren();
      details.dataset.key = selected.key;
      details.dataset.mode = mode;
      build(details);
    }
    return details;
  }
  function clearButton() {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.id = "map-clear-sel";
    btn.textContent = "Clear selection";
    btn.addEventListener("click", clearSelection);
    return btn;
  }

  function showMissing(reason) {
    const details = detailsFor("missing", (root) => {
      const p = document.createElement("p");
      p.className = "warnings";
      const message = document.createElement("span");
      message.dataset.field = "missing";
      p.append(message, " ", clearButton());
      root.appendChild(p);
    });
    const name = selected.worker + " / " + selected.task;
    setText(details.querySelector('[data-field="missing"]'), reason === "filtered"
      ? "Selected task " + name + " is off-page or filtered out."
      : "Selected task " + name + " is not in the current observation.");
  }

  function consoleRoute(r) {
    const button = Array.from(document.querySelectorAll("#console-workers button.console-worker"))
      .find((b) => b.dataset.worker === r.worker);
    if (!button) return { text: "Protected output and worktree files are unavailable for this worker in the current session.", action: null };
    const output = button.dataset.output === "true";
    const files = button.dataset.files === "true";
    const latest = button.dataset.task || "";
    const event = { worker: r.worker, task: latest };
    if (output && latest === r.task) {
      return {
        text: files ? "Source output and tracked worktree files are available for this task."
          : "Source output is available for this task. Worktree files are not enabled.",
        action: { label: "Open Source console for " + r.worker + " / " + r.task, event },
      };
    }
    if (output && latest) {
      return {
        text: "Protected output is currently showing a different/latest task (" + latest + "), not this historical record."
          + (files ? " Tracked worktree files show the worker's current worktree, not this record." : " Worktree files are not enabled."),
        action: { label: "Open console for different/latest task " + latest, event },
      };
    }
    if (files) {
      return {
        text: (output ? "Source output has no recorded task for this worker. " : "Source output is not enabled. ")
          + "Only tracked worktree files are available; they show the worker's current worktree, not this record.",
        action: { label: "Open worktree files for " + r.worker, event },
      };
    }
    return { text: "Source output has no recorded task for this worker, and worktree files are not enabled.", action: null };
  }

  function showDetails(r, data, verdict) {
    const details = detailsFor("task", (root) => {
      const header = document.createElement("div");
      header.className = "map-details-header";
      const h3 = document.createElement("h3");
      h3.dataset.field = "title";
      header.append(h3, clearButton());
      root.appendChild(header);
      const grid = document.createElement("dl");
      grid.className = "evidence-grid";
      grid.style.margin = "16px 0";
      for (const [name, title] of [["observed", "Observed"], ["recorded", "Recorded"], ["status", "Status"], ["activity", "Activity"], ["process", "Process"], ["validation", "Validation"], ["review", "Review"]]) {
        const row = document.createElement("div");
        const dt = document.createElement("dt");
        dt.textContent = title;
        const dd = document.createElement("dd");
        dd.dataset.field = name;
        row.append(dt, dd);
        grid.appendChild(row);
      }
      root.appendChild(grid);
      const consoleDiv = document.createElement("div");
      consoleDiv.className = "map-details-console";
      const p = document.createElement("p");
      p.className = "small";
      p.dataset.field = "console";
      consoleDiv.appendChild(p);
      root.appendChild(consoleDiv);
    });
    const field = (name) => details.querySelector('[data-field="' + name + '"]');
    setText(field("title"), r.worker + " / " + r.task);
    setText(field("observed"), "Current observation " + (data.observed_at || "unknown"));
    setText(field("recorded"), "Task evidence recorded " + (r.recorded_at || "unknown"));
    setText(field("status"), CATEGORY_TEXT[verdict.category] + (verdict.reasons.length ? " · " + verdict.reasons.join("; ") : ""));
    setText(field("activity"), label(r.activity));
    setText(field("process"), label(sectionState(r, "process")) + " · exit " + (r.process && r.process.exit_code !== null && r.process.exit_code !== undefined ? r.process.exit_code : "unknown"));
    setText(field("validation"), label(sectionState(r, "validation")) + " · " + (r.validation ? r.validation.checks_run : "unknown") + " checks / " + (r.validation ? r.validation.checks_failed : "unknown") + " failed");
    setText(field("review"), label(sectionState(r, "review")) + " · reviewer " + ((r.review && r.review.reviewer) || "not recorded"));

    const route = consoleRoute(r);
    const consoleText = field("console");
    setText(consoleText, route.text);
    let open = details.querySelector('[data-field="console-open"]');
    if (!route.action) {
      if (open) open.remove();
      return;
    }
    if (!open) {
      open = document.createElement("button");
      open.type = "button";
      open.className = "primary";
      open.dataset.field = "console-open";
      open.addEventListener("click", () => {
        if (!lastData || open.dataset.worker === undefined) return;
        document.dispatchEvent(new CustomEvent("unio-open-console", {
          detail: { worker: open.dataset.worker, task: open.dataset.task },
        }));
      });
      consoleText.parentElement.appendChild(open);
    }
    open.dataset.worker = route.action.event.worker;
    open.dataset.task = route.action.event.task;
    setText(open, route.action.label);
  }

  function clearMapAfterFailure() {
    const svg = document.getElementById("work-map");
    svg.replaceChildren();
    svg.dataset.contentHeight = "200";
    applyMapPresentation();
    clearDetails();
    setText(document.getElementById("map-counts"), "");
    document.getElementById("map-pagination").hidden = true;
    setText(document.getElementById("map-page-info"), "");
    document.getElementById("map-prev-page").disabled = true;
    document.getElementById("map-next-page").disabled = true;
    syncWorkerOptions([]);
  }

  async function refresh() {
    if (busy) return;
    busy = true;
    document.getElementById("tasks").setAttribute("aria-busy", "true");
    try {
      const response = await fetch("/api/activity", { cache: "no-store" });
      if (!response.ok) throw new Error("observer unavailable");
      render(await response.json());
    } catch (_) {
      lastData = null;
      // Remove old states so a failed observation cannot look current.
      clearMapAfterFailure();
      document.getElementById("tasks").replaceChildren();
      document.getElementById("limits").replaceChildren();
      document.getElementById("events").textContent = "";
      status.className = "error";
      status.textContent =
        "Local activity is unavailable. No current state is claimed.";
    } finally {
      busy = false;
      document.getElementById("tasks").setAttribute("aria-busy", "false");
    }
  }
  document.getElementById("refresh").addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 2000);
})();

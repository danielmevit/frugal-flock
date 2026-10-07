/* Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/unio
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";

  const themeSelector = document.getElementById("theme-selector");
  const STORAGE_KEY = "unio-theme-preference";

  function applyTheme(theme) {
    if (theme === "system") {
      delete document.documentElement.dataset.theme;
      return;
    }
    document.documentElement.dataset.theme = theme;
  }

  function loadTheme() {
    let saved = "system";
    try {
      saved = localStorage.getItem(STORAGE_KEY) || "system";
    } catch (e) {}
    if (saved !== "light" && saved !== "dark") saved = "system";
    if (themeSelector) themeSelector.value = saved;
    applyTheme(saved);
  }

  if (themeSelector) {
    themeSelector.addEventListener("change", () => {
      const value = themeSelector.value;
      try {
        localStorage.setItem(STORAGE_KEY, value);
      } catch (e) {}
      applyTheme(value);
    });
  }
  loadTheme();

  const status = document.getElementById("status");
  let busy = false;

  let currentView = window.innerWidth >= 1000 ? "map" : "list";
  let mapHistoryVisible = false;
  let mapSearchQuery = "";
  let mapCurrentPage = 0;
  const MAP_PAGE_SIZE = 24;
  let lastData = null;

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
    mapBtn.addEventListener("click", () => { currentView = "map"; updateViewSwitch(); if(lastData) render(lastData); });
    document.getElementById("view-list").addEventListener("click", () => { currentView = "list"; updateViewSwitch(); if(lastData) render(lastData); });
    document.getElementById("map-history-toggle").addEventListener("change", (e) => { mapHistoryVisible = e.target.checked; mapCurrentPage = 0; if(lastData) render(lastData); });
    document.getElementById("map-search").addEventListener("input", (e) => { mapSearchQuery = e.target.value.toLowerCase(); mapCurrentPage = 0; if(lastData) render(lastData); });
    document.getElementById("map-prev-page").addEventListener("click", () => { mapCurrentPage = Math.max(0, mapCurrentPage - 1); if(lastData) render(lastData); });
    document.getElementById("map-next-page").addEventListener("click", () => { mapCurrentPage++; if(lastData) render(lastData); });
    updateViewSwitch();
  }

    document.getElementById("map-fit").addEventListener("click", () => {
       const svg = document.getElementById("work-map");
       svg.style.width = "100%";
       svg.style.height = "100%";
       // simple fit to width
    });
    document.getElementById("map-reset").addEventListener("click", () => {
       const svg = document.getElementById("work-map");
       svg.style.width = "800px";
       // height is set during render based on items
       if (lastData) renderMap(lastData);
    });

  function text(tag, value, className = "") {
    const element = document.createElement(tag);
    element.textContent = value;
    element.className = className;
    return element;
  }
    let selectedNodeId = null;
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


  function renderMap(data) {
    const svg = document.getElementById("work-map");
    const details = document.getElementById("map-details");
    const countsSpan = document.getElementById("map-counts");
    const pagination = document.getElementById("map-pagination");
    const prevBtn = document.getElementById("map-prev-page");
    const nextBtn = document.getElementById("map-next-page");
    const pageInfo = document.getElementById("map-page-info");

    let filtered = [];
    let finishedCount = 0;

    for (let r of data.results) {
      const stateStr = (r.process.state + " " + r.activity + " " + r.validation.state + " " + r.review.state).toLowerCase();

      let isFinished = r.process.state !== "running" && r.process.state !== "starting" && r.process.state !== "unknown";
      if (r.activity === "completion_unknown") isFinished = false;

      if (isFinished) finishedCount++;
      if (!mapHistoryVisible && isFinished) continue;

      const searchMatch = !mapSearchQuery ||
          r.worker.toLowerCase().includes(mapSearchQuery) ||
          r.task.toLowerCase().includes(mapSearchQuery) ||
          stateStr.includes(mapSearchQuery);

      if (searchMatch) filtered.push(r);
    }

    countsSpan.textContent = `${data.results.length} total tasks (${finishedCount} finished)`;

    filtered.sort((a, b) => {
      if (a.worker !== b.worker) return a.worker.localeCompare(b.worker);
      return a.task.localeCompare(b.task);
    });

    const totalPages = Math.ceil(filtered.length / MAP_PAGE_SIZE);
    if (mapCurrentPage >= totalPages) mapCurrentPage = Math.max(0, totalPages - 1);

    const pageTasks = filtered.slice(mapCurrentPage * MAP_PAGE_SIZE, (mapCurrentPage + 1) * MAP_PAGE_SIZE);

    if (filtered.length > MAP_PAGE_SIZE) {
      pagination.hidden = false;
      pageInfo.textContent = `Page ${mapCurrentPage + 1} of ${totalPages || 1}`;
      prevBtn.disabled = mapCurrentPage === 0;
      nextBtn.disabled = mapCurrentPage >= totalPages - 1;
    } else {
      pagination.hidden = true;
    }

    const workersMap = new Map();
    for (let r of pageTasks) {
      workersMap.set(r.worker, true);
    }
    const workers = Array.from(workersMap.keys()).sort();

    const projectX = 50, projectY = 50;
    const workerX = 250, taskX = 550;
    let currentY = 50;

    const nodes = [];
    const links = [];
    nodes.push({ id: "project-hub", label: "Project Hub", x: projectX, y: projectY, type: "hub" });

    let workerYs = {};
    let wY = 50;

    for (let w of workers) {
      workerYs[w] = Math.max(wY, currentY);
      nodes.push({ id: `worker-${w}`, label: w, x: workerX, y: workerYs[w], type: "worker", worker: w });
      links.push({ source: "project-hub", target: `worker-${w}` });

      let tCount = 0;
      for (let r of pageTasks) {
        if (r.worker === w) {
          const ty = workerYs[w] + tCount * 40;
          const taskId = `${r.worker}:::${r.task}`;
          nodes.push({ id: taskId, label: r.task, x: taskX, y: ty, type: "task", data: r });
          links.push({ source: `worker-${w}`, target: taskId });
          tCount++;
        }
      }
      currentY = workerYs[w] + tCount * 40 + 20;
      wY += 60;
    }

    const totalHeight = Math.max(200, currentY);
    svg.setAttribute("viewBox", `0 0 800 ${totalHeight}`);
    svg.style.height = `${totalHeight}px`;
    if (!svg.style.width) svg.style.width = "800px";

    // Reuse existing DOM elements to preserve focus
    const oldLines = Array.from(svg.querySelectorAll("line"));
    const oldGroups = Array.from(svg.querySelectorAll("g"));

    // Links
    for (let i = 0; i < links.length; i++) {
      const l = links[i];
      const src = nodes.find(n => n.id === l.source);
      const tgt = nodes.find(n => n.id === l.target);
      let line = oldLines[i];
      if (!line) {
        line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        svg.insertBefore(line, svg.firstChild);
      }
      line.setAttribute("x1", src.x + 60);
      line.setAttribute("y1", src.y);
      line.setAttribute("x2", tgt.x - 60);
      line.setAttribute("y2", tgt.y);
      line.setAttribute("stroke", "var(--line)");
      line.setAttribute("stroke-width", "2");
    }
    for (let i = links.length; i < oldLines.length; i++) {
      oldLines[i].remove();
    }

    // Nodes
    let selectedNodeExists = false;
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      let g = oldGroups[i];
      if (!g) {
        g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        g.appendChild(rect);
        g.appendChild(text);
        svg.appendChild(g);
      }
      g.setAttribute("transform", `translate(${n.x}, ${n.y})`);
      g.style.cursor = "pointer";
      g.setAttribute("tabindex", "0");
      g.id = "map-node-" + n.id;

      // We must clear old event listeners.
      // The easiest way without removing DOM is to just set an onclick attribute.
      // But we can't capture `n.data` easily. We can attach it to the element.
      g._nodeData = n;
      g.onclick = function() {
         selectedNodeId = this._nodeData.id;
         if (this._nodeData.type === "task") {
            showDetails(this._nodeData.data);
         } else {
            details.hidden = true;
         }
         if (lastData) renderMap(lastData);
      };
      g.onkeydown = function(e) {
         if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            this.onclick();
         }
      };

      const rect = g.querySelector("rect");
      rect.setAttribute("x", -60);
      rect.setAttribute("y", -15);
      rect.setAttribute("width", 120);
      rect.setAttribute("height", 30);
      rect.setAttribute("rx", 5);
      rect.setAttribute("fill", "var(--paper)");
      rect.setAttribute("stroke", n.id === selectedNodeId ? "var(--focus-ring)" : "var(--btn-border)");
      rect.setAttribute("stroke-width", n.id === selectedNodeId ? "3" : "1");
      if (n.id === selectedNodeId) selectedNodeExists = true;

      const text = g.querySelector("text");
      text.textContent = n.label.length > 15 ? n.label.substring(0, 13) + "..." : n.label;
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("alignment-baseline", "middle");
      text.setAttribute("fill", "var(--text-main)");
      text.setAttribute("font-size", "12px");
      text.style.pointerEvents = "none";
    }
    for (let i = nodes.length; i < oldGroups.length; i++) {
      oldGroups[i].remove();
    }

    if (!selectedNodeExists) {
       details.hidden = true;
    } else if (selectedNodeId && selectedNodeId.includes(":::")) {
       const r = pageTasks.find(t => `${t.worker}:::${t.task}` === selectedNodeId);
       if (r) {
          showDetails(r);
       } else {
          details.hidden = false;
          details.innerHTML = `<p class="warnings">Selected task is off-page or filtered out. <button type="button" id="map-clear-sel">Clear selection</button></p>`;
          document.getElementById("map-clear-sel").addEventListener("click", () => {
             selectedNodeId = null;
             details.hidden = true;
             if (lastData) renderMap(lastData);
          });
       }
    }
  }

  function showDetails(r) {
    const details = document.getElementById("map-details");
    details.hidden = false;

    // Check if worker console has this worker
    const buttons = Array.from(document.querySelectorAll("#console-workers button.console-worker"));
    const workerBtn = buttons.find(b => b.querySelector('strong') && b.querySelector('strong').textContent.startsWith(r.worker));

    let consoleText = "Protected output unavailable.";
    let hasConsole = false;
    if (workerBtn) {
       const title = workerBtn.querySelector('strong').textContent;
       if (title.includes(r.task)) {
          consoleText = "Source output and tracked files are available for this task.";
          hasConsole = true;
       } else {
          const latestTask = title.split(" / ")[1] || "unknown task";
          consoleText = `Protected output is currently showing a different/latest task (${latestTask}), not this historical record.`;
          hasConsole = true;
       }
    }

    const consoleBtn = hasConsole ? `<button type="button" class="primary" onclick="document.dispatchEvent(new CustomEvent('unio-open-console', { detail: { worker: '${r.worker}', task: '${r.task}' } }))">Open Source Console</button>` : '';

    details.innerHTML = `
      <div class="map-details-header">
         <h3>${r.worker} / ${r.task}</h3>
      </div>
      <div class="evidence-grid" style="margin: 16px 0;">
         <div>
           <dt>Recorded</dt>
           <dd>${r.recorded_at || "unknown"}</dd>
         </div>
         <div>
           <dt>Activity</dt>
           <dd><span class="chip">${r.activity.replaceAll("_", " ")}</span></dd>
         </div>
         <div>
           <dt>Process</dt>
           <dd>${r.process.state.replaceAll("_", " ")} · exit ${r.process.exit_code ?? "unknown"}</dd>
         </div>
         <div>
           <dt>Validation</dt>
           <dd>${r.validation.state.replaceAll("_", " ")}</dd>
         </div>
      </div>
      <div class="map-details-console">
         <p class="small">${consoleText}</p>
         ${consoleBtn}
      </div>
    `;
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
      // Remove old states so a failed observation cannot look current.
      document.getElementById("work-map").replaceChildren();
document.getElementById("map-details").replaceChildren();
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

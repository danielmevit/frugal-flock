/* Frugal Flock — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
 * https://github.com/danielmevit/frugal-flock
 * SPDX-License-Identifier: AGPL-3.0-only; see LICENSE and NOTICE. No warranty. */
(function () {
  "use strict";
  const status = document.getElementById("status");
  let busy = false;
  function text(tag, value, className = "") {
    const element = document.createElement(tag);
    element.textContent = value;
    element.className = className;
    return element;
  }
  function render(data) {
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
  async function refresh() {
    if (busy) return;
    busy = true;
    try {
      const response = await fetch("/api/activity", { cache: "no-store" });
      if (!response.ok) throw new Error("observer unavailable");
      render(await response.json());
    } catch (_) {
      // Remove old states so a failed observation cannot look current.
      document.getElementById("tasks").replaceChildren();
      document.getElementById("limits").replaceChildren();
      document.getElementById("events").textContent = "";
      status.className = "error";
      status.textContent =
        "Local activity is unavailable. No current state is claimed.";
    } finally {
      busy = false;
    }
  }
  document.getElementById("refresh").addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 2000);
})();

/* Frugal Flock — Copyright (C) 2026 Daniel Mitev
 * Daniel Mevit (@danielmevit), https://github.com/danielmevit/frugal-flock
 * SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
 * See LICENSE and NOTICE; distributed without warranty.
 */
(function () {
  "use strict";
  const { createSession, transition } = globalThis.FrugalFlockDemo;
  let state = createSession();
  const narrow = matchMedia("(max-width:720px)");
  const disclosure = document.querySelector(".inspector-disclosure");
  const resizeInspector = () => {
    disclosure.open = !narrow.matches;
  };
  narrow.addEventListener("change", resizeInspector);
  resizeInspector();
  const body = document.getElementById("conversation-body");
  const inspector = document.getElementById("inspector-body");
  const announcement = document.getElementById("announcement");
  const error = document.getElementById("error");
  const escape = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const button = (action, label, primary = false, value = "") =>
    `<button type="button" class="${primary ? "primary" : ""}" data-action="${action}" data-value="${escape(value)}">${label}</button>`;
  const lead = (text) =>
    `<div class="lead-message"><span class="avatar" aria-hidden="true">C</span><div><p class="message-header"><strong>Codex</strong> · sample lead</p><p class="message-text">${text}</p></div></div>`;
  const form = (action, id, label, initial, submit) =>
    `<form data-submit="${action}"><label for="${id}">${label}</label><textarea id="${id}" name="response" required maxlength="2000">${escape(initial)}</textarea><p class="field-hint">This demo uses a fixed search scenario. Your response stays in this page. Ctrl/Command+Enter submits; Enter adds a new line.</p><div class="actions"><button type="submit" class="primary">${submit}</button></div></form>`;
  const checks = () =>
    `<ul class="checks-list">${["Search finds matching entries", "Keyboard reaches results", "Empty queries are handled"].map((name) => `<li><span>${name}</span><span class="chip ${state.validation === "passed" ? "" : "neutral"}">${state.validation === "passed" ? "Passed" : "Pending"}</span></li>`).join("")}</ul>`;
  const evidence = () =>
    `<dl class="status-grid">${[
      ["Worker process", state.process],
      ["Validation", state.validation],
      ["Reviewer decision", state.review],
      ["Your acceptance", state.human],
      ["Project integration", state.integration],
    ]
      .map(
        ([label, value]) =>
          `<div><dt>${label}</dt><dd>${escape(value.replaceAll("_", " "))}</dd></div>`,
      )
      .join("")}</dl>`;
  const sampleDetails =
    () => `<details><summary>Sample changes and evidence</summary><p class="small">Example files and decisions only. No real repository is connected.</p><pre>src/search.js        + search matching
src/search.test.js   + keyboard and empty query checks

Sample candidate: revision ${state.revision}
Provider exit and real capacity: not observed</pre>${evidence()}</details>`;
  function render(moveFocus = false) {
    const names = {
      welcome: "One conversation. A small next step.",
      connect: "Choose your first tool.",
      describe: "What would you like to build?",
      plan: "A plan you can review.",
      running: "Your flock is working.",
      question: "One choice before we continue.",
      limited: "Keep the work. Choose what follows.",
      checking: "The work finished. Checks come next.",
      reviewing: "A second look at the result.",
      review: "Ready for your review.",
      applied: "A small change, reviewed and applied.",
      stopped: "Work stopped. Context stays here.",
    };
    document.getElementById("conversation-title").textContent =
      names[state.phase];
    document.getElementById("project-state").textContent =
      state.phase === "welcome"
        ? "Not opened"
        : state.phase === "applied"
          ? "Demo result applied"
          : "Sample workspace";
    let content = "";
    if (state.phase === "welcome")
      content =
        lead(
          "Bring your idea and the coding tools you already use. We’ll make a small plan, check the work, and leave the decision with you.",
        ) +
        `<div class="task-card"><h2>Try a garden journal</h2><p>Follow a search feature from first idea through a question, a provider limit, and your final review.</p><div class="actions">${button("open", "Open sample project", true)}</div></div>`;
    if (state.phase === "connect")
      content =
        lead(
          "Start with one worker. I’ll help with the plan and review the result. These connections are sample data.",
        ) +
        `<div class="task-card"><h2>Your sample flock</h2><div class="tool-choice"><div><strong>OpenCode Go</strong><span>GLM 5.3 · worker · sample connection</span></div><span class="chip neutral">Not connected</span></div><div class="tool-choice"><div><strong>Codex</strong><span>Lead and reviewer · sample connection</span></div><span class="chip">Selected</span></div><p class="field-hint">No sign-in occurs. Real authentication and remaining quota are unknown.</p><div class="actions">${button("connect", "Connect sample tool", true)}</div></div>`;
    if (state.phase === "describe" || state.phase === "stopped")
      content =
        lead(
          state.phase === "stopped"
            ? "The sample workflow is stopped. Earlier events remain below. Review a new plan before restarting."
            : "Tell me one thing you want to change. I’ll show you the proposed work before anyone starts.",
        ) +
        `<div class="task-card">${form("plan", "request", "Describe a change", state.request || "Add search so I can find past journal entries by title or text.", "Create plan")}</div>`;
    if (state.phase === "plan")
      content =
        lead(
          "Here’s the sample plan. One worker will build it, I’ll review it, and you’ll decide whether to apply the result.",
        ) +
        `<div class="task-card"><h2>Find past journal entries</h2><p>${escape(state.request)}</p>${state.feedback ? `<p><strong>Your requested change:</strong> ${escape(state.feedback)}</p>` : ""}<ul class="scope-list"><li>1. Add a search input to the journal.</li><li>2. Show matching entries and a useful empty state.</li><li>3. Check keyboard access and review the complete change.</li></ul><p class="field-hint">OpenCode Go · GLM 5.3 builds. Codex reviews. Everything here is simulated.</p><div class="actions">${button("start", "Approve and start", true)}</div></div>`;
    if (state.phase === "running")
      content =
        lead(
          state.step === 2
            ? "You selected Grok. It will continue the sample search change and run the unfinished checks."
            : "OpenCode Go is building the sample search feature. We’ll check the result before asking you to accept it.",
        ) +
        `<div class="task-card"><h2>${state.step === 2 ? "Continuing from the sample checkpoint" : "Building search"}</h2><p>${state.step === 1 ? "Your search choice is recorded. The next event demonstrates a provider limit." : "No progress percentage or remaining quota is inferred."}</p><div class="actions">${button("advance", "Show next sample event", true)}${button("stop", "Stop")}</div></div>`;
    if (state.phase === "question")
      content =
        lead(
          "Should search match only entry titles, or include the entry text too?",
        ) +
        `<div class="task-card">${form("answer", "answer", "Your answer", "Match titles and entry text.", "Send answer")}<div class="actions">${button("stop", "Stop")}</div></div>`;
    if (state.phase === "limited")
      content =
        lead(
          "This is a simulated provider limit. We’ll keep the sample work visible and ask you before changing workers.",
        ) +
        `<div class="limit-card"><h2>OpenCode Go reached a simulated limit</h2><p>Sample checkpoint: search input committed. Keyboard checks and review unfinished.</p><p>Reset time: not reported. Remaining quota: unknown.</p><p><strong>Grok</strong> is the named replacement in this scenario. Its connection is sample data.</p><div class="actions">${button("continue", "Continue with Grok", true, "Grok")}${button("stop", "Stop")}</div></div>${sampleDetails()}`;
    if (state.phase === "checking")
      content =
        lead(
          "Grok finished the sample change. That process completion is separate from validation and review.",
        ) +
        `<div class="task-card"><h2>Checking the result</h2>${checks()}<div class="actions">${button("advance", "Show check results", true)}${button("stop", "Stop")}</div></div>`;
    if (state.phase === "reviewing")
      content =
        lead(
          "The three sample checks passed. Codex is reviewing the whole change before it reaches your acceptance decision.",
        ) +
        `<div class="task-card"><h2>Review in progress</h2>${checks()}<div class="actions">${button("advance", "Show reviewer decision", true)}${button("stop", "Stop")}</div></div>`;
    if (state.phase === "review")
      content =
        lead(
          "The sample validation passed and Codex approved the change. Your acceptance and integration are still pending.",
        ) +
        `<div class="task-card"><h2>Search is ready for your decision</h2><p>Find journal entries by title or text, with keyboard access and an empty state.</p>${checks()}<p class="small">Applying changes affects this demo only. Your real files will not change.</p><div class="actions">${button("apply", "Apply changes", true)}</div>${sampleDetails()}</div><div class="task-card">${form("changes", "feedback", "What should change?", "", "Request changes")}</div>`;
    if (state.phase === "applied")
      content =
        lead(
          "You accepted and applied the sample result inside the demo. Your real project has not changed.",
        ) +
        `<div class="task-card"><h2>Applied in this demo only</h2><p>You stayed in control through the plan, the interruption, the review and the final decision.</p>${evidence()}<div class="actions">${button("reset", "Try the demo again", true)}</div></div>`;
    if (state.events.length && state.phase !== "welcome")
      content += `<details class="activity-history"><summary>Sample activity · ${state.events.length} events</summary><ol class="event-list">${state.events.map((event, i) => `<li><span class="number">Event ${i + 1}</span>${escape(event)}</li>`).join("")}</ol></details>`;
    body.innerHTML = content;
    inspector.innerHTML = `<section><h2>My flock · sample</h2><div class="tool"><span class="avatar" aria-hidden="true">C</span><div><strong>Codex</strong><p>Lead &amp; reviewer · sample</p><p>Capacity unknown</p></div></div><div class="tool"><span class="avatar" aria-hidden="true">${state.worker === "Grok" ? "G" : "O"}</span><div><strong>${escape(state.worker)}</strong><p>${escape(state.model)} · worker · sample</p><p>Capacity unknown</p></div></div></section><section><h2>Current task</h2><h3>Search journal entries</h3><p class="small">One small change. One worker. A separate review before your decision.</p><ul class="scope-list"><li>Search input</li><li>Matching entries</li><li>Keyboard and empty states</li></ul></section><section><h2>Sample checks</h2>${checks()}</section><section><h2>Your control</h2><p class="small">Approve the plan, choose any replacement, and decide whether to apply changes.</p><details><summary>Demo boundaries</summary><p class="small">No provider calls, sign-in, filesystem access, project writes, real checkpoints, or merges occur. Activity advances only when you choose the next sample event.</p></details></section>`;
    error.hidden = true;
    announcement.textContent = names[state.phase] + " Sample data only.";
    if (moveFocus) document.getElementById("conversation-title").focus();
  }
  function act(action, value = "") {
    try {
      state = transition(state, action, value);
      render(true);
    } catch (exception) {
      error.textContent = exception.message;
      error.hidden = false;
      error.focus();
    }
  }
  document.addEventListener("click", (event) => {
    const target = event.target.closest("button[data-action]");
    if (target) act(target.dataset.action, target.dataset.value || "");
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.defaultPrevented ||
      event.repeat ||
      event.isComposing ||
      event.key !== "Enter" ||
      !(event.ctrlKey || event.metaKey) ||
      event.altKey ||
      event.shiftKey ||
      !(event.target instanceof HTMLTextAreaElement)
    )
      return;
    const form = event.target.closest("form[data-submit]");
    if (!form) return;
    event.preventDefault();
    form.requestSubmit();
  });
  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form[data-submit]");
    if (!form) return;
    event.preventDefault();
    act(form.dataset.submit, new FormData(form).get("response"));
  });
  render();
})();

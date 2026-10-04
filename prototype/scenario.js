/* Frugal Flock — Copyright (C) 2026 Daniel Mitev
 * Daniel Mevit (@danielmevit), https://github.com/danielmevit/frugal-flock
 * SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
 * See LICENSE and NOTICE; distributed without warranty.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.FrugalFlockDemo = api;
})(globalThis, function () {
  "use strict";
  function createSession() {
    return {
      phase: "welcome",
      request: "",
      feedback: "",
      answer: "",
      worker: "OpenCode Go",
      model: "GLM 5.3",
      reviewer: "Codex",
      revision: 1,
      step: 0,
      events: [],
      process: "not_run",
      validation: "not_run",
      review: "not_run",
      human: "pending",
      integration: "not_attempted",
    };
  }
  function transition(previous, action, value = "") {
    const s = { ...previous, events: [...previous.events] };
    const event = (text) => s.events.push(text);
    const requirePhase = (...phases) => {
      if (!phases.includes(s.phase))
        throw new Error("That action is unavailable at this step.");
    };
    const text = () => {
      if (typeof value !== "string" || !value.trim())
        throw new Error("Please enter a response first.");
      return value.trim().slice(0, 2000);
    };
    if (action === "reset") return createSession();
    if (action === "open") {
      requirePhase("welcome");
      s.phase = "connect";
    } else if (action === "connect") {
      requirePhase("connect");
      s.phase = "describe";
      event("Sample OpenCode Go connection selected.");
    } else if (action === "plan") {
      requirePhase("describe", "stopped");
      s.request = text();
      s.phase = "plan";
      s.process = s.validation = s.review = "not_run";
      s.human = "pending";
      s.integration = "not_attempted";
      s.worker = "OpenCode Go";
      s.model = "GLM 5.3";
      s.step = 0;
      event("A sample search plan is ready for your approval.");
    } else if (action === "start") {
      requirePhase("plan");
      s.phase = "running";
      s.process = "running";
      s.step = 0;
      event(s.worker + " started the sample search task.");
    } else if (action === "advance") {
      requirePhase("running", "checking", "reviewing");
      if (s.phase === "running" && s.step === 0) {
        s.phase = "question";
        event("The worker needs your choice about search behavior.");
      } else if (s.phase === "running" && s.step === 1) {
        s.phase = "limited";
        s.process = "completion_unknown";
        event(
          "Simulated OpenCode Go limit. Sample committed work is listed in the checkpoint.",
        );
      } else if (s.phase === "running" && s.step === 2) {
        s.phase = "checking";
        s.process = "succeeded";
        event("Grok finished the sample task. Validation has not finished.");
      } else if (s.phase === "checking") {
        s.phase = "reviewing";
        s.validation = "passed";
        event("All three sample checks passed. Codex is reviewing the result.");
      } else if (s.phase === "reviewing") {
        s.phase = "review";
        s.review = "approved";
        event(
          "Codex approved the sample result. Your acceptance is still pending.",
        );
      } else throw new Error("No next sample event is available.");
    } else if (action === "answer") {
      requirePhase("question");
      s.answer = text();
      s.phase = "running";
      s.step = 1;
      event("Your answer: " + s.answer);
    } else if (action === "continue") {
      requirePhase("limited");
      if (value !== "Grok")
        throw new Error("Select the named sample replacement: Grok.");
      s.worker = "Grok";
      s.model = "Sample model";
      s.phase = "running";
      s.process = "running";
      s.step = 2;
      s.validation = s.review = "not_run";
      event("You chose Grok to continue from the sample checkpoint.");
    } else if (action === "changes") {
      requirePhase("review");
      s.feedback = text();
      s.phase = "plan";
      s.revision += 1;
      s.worker = "OpenCode Go";
      s.model = "GLM 5.3";
      s.process = s.validation = s.review = "not_run";
      s.human = "pending";
      s.integration = "not_attempted";
      event(
        "Changes requested: " +
          s.feedback +
          ". Previous approval is invalidated.",
      );
    } else if (action === "apply") {
      requirePhase("review");
      if (
        s.process !== "succeeded" ||
        s.validation !== "passed" ||
        s.review !== "approved"
      )
        throw new Error("All result checks and review must pass first.");
      s.human = "accepted";
      s.integration = "simulated_applied";
      s.phase = "applied";
      event(
        "You applied the sample result inside this demo. No real project changed.",
      );
    } else if (action === "stop") {
      requirePhase("running", "question", "limited", "checking", "reviewing");
      s.phase = "stopped";
      if (s.process !== "succeeded") s.process = "completion_unknown";
      s.review = "not_run";
      event("Sample workflow stopped. Earlier sample events remain available.");
    } else throw new Error("Unknown demo action.");
    return s;
  }
  return { createSession, transition };
});

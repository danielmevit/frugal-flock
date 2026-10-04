// Frugal Flock — Copyright (C) 2026 Daniel Mitev
// Public attribution: Daniel Mevit (@danielmevit)
// Original project: https://github.com/danielmevit/frugal-flock
// SPDX-License-Identifier: AGPL-3.0-only
// Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
// See LICENSE and NOTICE; distributed without warranty.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { createSession, transition: next } = require("../scenario.js");
function review() {
  let state = createSession();
  for (const [action, value] of [
    ["open"],
    ["connect"],
    ["plan", "Find entries"],
    ["start"],
    ["advance"],
    ["answer", "Title and text"],
    ["advance"],
    ["continue", "Grok"],
    ["advance"],
    ["advance"],
    ["advance"],
  ])
    state = next(state, action, value);
  return state;
}
test("full journey keeps provider recovery and human integration explicit", () => {
  let state = createSession();
  assert.throws(() => next(state, "apply"));
  for (const action of ["open", "connect"]) state = next(state, action);
  assert.throws(() => next(state, "plan", "  "));
  state = next(state, "plan", "Search");
  assert.equal(state.process, "not_run");
  state = next(state, "start");
  state = next(state, "advance");
  assert.equal(state.phase, "question");
  assert.throws(() => next(state, "answer", ""));
  state = next(state, "answer", "Titles");
  state = next(state, "advance");
  assert.equal(state.phase, "limited");
  assert.equal(state.process, "completion_unknown");
  assert.throws(() => next(state, "continue", "Claude"));
  state = next(state, "continue", "Grok");
  assert.equal(state.worker, "Grok");
  state = next(state, "advance");
  assert.equal(state.process, "succeeded");
  assert.equal(state.validation, "not_run");
  state = next(state, "advance");
  assert.equal(state.validation, "passed");
  assert.equal(state.review, "not_run");
  state = next(state, "advance");
  assert.equal(state.review, "approved");
  assert.equal(state.human, "pending");
  assert.equal(state.integration, "not_attempted");
  state = next(state, "apply");
  assert.equal(state.human, "accepted");
  assert.equal(state.integration, "simulated_applied");
});
test("request changes invalidates approval and requires a fresh approved plan", () => {
  const ready = review();
  assert.throws(() => next(ready, "changes", ""));
  const changed = next(ready, "changes", "Make empty-state text clearer");
  assert.equal(changed.phase, "plan");
  assert.equal(changed.review, "not_run");
  assert.equal(changed.revision, ready.revision + 1);
  assert.equal(changed.human, "pending");
  assert.throws(() => next(changed, "apply"));
  assert.equal(ready.review, "approved");
});
test("Stop preserves history without inventing an exit or silently restarting", () => {
  let state = next(
    next(next(next(createSession(), "open"), "connect"), "plan", "Search"),
    "start",
  );
  const stopped = next(state, "stop");
  assert.equal(stopped.phase, "stopped");
  assert.equal(stopped.process, "completion_unknown");
  assert.ok(stopped.events.length > state.events.length);
  assert.throws(() => next(stopped, "advance"));
  const plan = next(
    { ...stopped, worker: "Grok", model: "Sample model" },
    "plan",
    stopped.request,
  );
  assert.equal(plan.worker, "OpenCode Go");
  assert.equal(plan.phase, "plan");
  assert.equal(plan.process, "not_run");
});
test("apply is refused if any evidence dimension is not passed", () => {
  for (const field of ["process", "validation", "review"])
    assert.throws(() => next({ ...review(), [field]: "not_run" }, "apply"));
});

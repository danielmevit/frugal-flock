# M2 first installed-release dogfood task

The original prototype is published as `5d40d68`. One small enhancement
will exercise the existing installed v0.4.0 worker/verify/review/result cycle
while the next version stays in source. No global reinstall or release.

Task: Ctrl+Enter or Command+Enter submits the currently focused demo form
once through its existing validation/submit path. Plain Enter remains a
newline. Empty/whitespace inputs, repeated keydown, unrelated keys or focus
outside a form must not advance the scenario. Add a visible shortcut hint
and browser checks without changing the sample state API or adding dependencies.

The new `wt/opencode-m2` on `agent/opencode-m2` preserves every earlier
worker branch. Allowed edits: prototype/app.js, prototype/tests/browser.cjs,
continuation prompt and one task changelog. Shared prototype interfaces are
frozen in the published source. Native Validate commands check JS syntax,
state guards, the browser journey and whitespace. Local test tools are
provided from workspace tmp; no dependency installation in the worker.

Launch requires fresh owner quota approval: one OpenCode Go GLM 5.3 CLI
worker invocation, 180 seconds, no invocation retries. Root Codex reviews
all task/diff material here, with no paid provider reviewer. Any native
review transport must be explicitly described as a local material-bound
transport of that real decision, never a second provider review. Human
acceptance/integration remain separate. Preserve interrupted partial work;
root may finish it here without another worker call.

A temporary local config pins opencode-go/glm-5.3/max using --auto; global
profiles/auth remain unchanged. Binary present is only local diagnostics;
authentication and remaining capacity are unknown. The local task, manifest
and receipts stay under coord/ and tmp/m2-keyboard-20261004/, not in Git.
M2 acceptance still needs two new-user feedback sessions before live UI
execution. This native CLI task does not connect the sample UI to providers.

## First keyboard attempt: preserved failure

The owner approved one GLM 5.3/max worker on 2026-10-04. Installed v0.4.0
returned exit 124 at 180 seconds, with no edits or commits. Tooling discovery
consumed the window, including a broad browser search. Native verification
ran all five baseline checks successfully but failed overall with empty_work.
Readiness was false. No invocation retry or additional reviewer call occurred.
The prepared tools were already available; future orders should give their
exact paths inline and prohibit broad searches instead of relying on inherited
environment discovery. These native logs/results stay local and unchanged.

Root Codex (`gpt-6.1-sol`, xhigh) finished the keyboard enhancement here.
Both shortcuts, required/trimmed validation, ignored keys and the full browser
journey passed, as did all four state tests and JS syntax. That local finish
is a source change; the failed native worker remains a failed dogfood attempt.

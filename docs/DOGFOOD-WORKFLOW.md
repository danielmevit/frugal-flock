# Build Unio with Unio

The owner's main objective is to implement the next milestones through the
flock while testing it in real use. Canary success alone is not completion
of this objective. On 2026-10-05 the owner explicitly reiterated that goal.
Root's direct prototype/bridge/storage/API/form work remains useful source,
but is identified as direct Codex implementation, not native worker success.
The GLM keyboard timeout stays failed; the Claude guide cycle stays successful.

For each next implementation slice:

1. The lead freezes one tiny task/interface and prepares a clean worker worktree
   under wt/ from current main. Put exact local test/tool paths in the task;
   prohibit dependency discovery/broad filesystem searches. Native auth and
   provider capacity stay unknown until a real approved invocation.
2. Ask the owner before spending provider quota, stating model/effort,
   invocation count, timeout and no-retry bound. No reply means no approval.
   (Existing explicit invocation authorization is honored without asking again.)
3. Use the installed release's run command, with only temporary local model
   config. Do not reinstall while it builds the next source version.
4. Preserve real worker logs/exits/partial changes. A failed or interrupted
   run is not a successful dogfood cycle; no automatic invocation retry.
   Diagnose, preserve and propose one bounded finishing task through the flock.
5. Run native verify against the frozen task/current candidate. If it fails,
   keep the failure and fix via the same controlled task/review process.
6. The current lead reads the full task and diff and reviews in-session.
   There is no extra paid reviewer. Bind any local decision transport to the
   exact material hash and actual reviewer/model; never call it a provider
   review. Preserve the native different-agent gate: when Claude is lead,
   choose a different-provider implementation worker for this arrangement.
   Same-provider review must not claim independent different-provider approval.
7. Recheck native result and retain a pre-integration receipt. Distinguish
   process, validation, review, human acceptance and integration. Source main
   changes can make the old native result stale; do not assume readiness persists.
8. Integrate each finished slice as its own no-ff main merge and push, using
   the owner's standing authorization. Include current main first; preserve
   old worker branches, append dated exact-model log entries and update handoff.

The lead focuses on task design, review, testing, diagnosis and integration.
Direct source fixes must be identified explicitly and bounded, and must not
silently replace this implementation cadence. The owner's waiver of two
user-feedback sessions removes that prerequisite only; quota approval and
truthful native evidence remain required. No real user sessions are claimed.

First native slice done: [durable waiting-job records](JOB-QUEUE-STORE.md)
were built by an OpenCode Go GLM 5.3/max worker in two owner-approved runs
of 600 seconds (the first timed out after committing and drew a
changes-requested lead review; the finishing run passed in 306 seconds),
reviewed in-session by the Claude lead and merged as 2539c64. Next
concrete task: explicit owner approval plus reservation/recovery records,
still with no executor, through the same cadence. Put a commit-by time in
each task so the worker's log entry fits.

Owner direction, 2026-10-05: use every available AI for flock work: Codex
(Sol 6.1, xhigh), OpenCode Go (GLM 5.3, high), the Grok CLI (high) and
Antigravity (Gemini 3.1 Pro, high). A different vendor may perform the
native review, in addition to the lead's full review; the owner can act as
the human reviewer. Each task or review is one invocation with a stated
timeout and no automatic retry, and every spend is logged.

# Frugal Flock — continue with another AI

This handoff is portable: it requires the public repository, not the
previous conversation, one particular model, or private coordination logs.
If the next AI cannot access GitHub, attach this file and the documents
listed in its reading order.

## Current baseline

- Public repository: https://github.com/danielmevit/frugal-flock
- Published implementation/README baseline: `f962b6a`. Read the latest main
  for this handoff and the research documents added afterward.
- Product: Frugal Flock. Tagline: Small plans. Big ideas.
- Commands: `frugal-flock`, `frgl-flc`, and compatibility `agentteam`.
- The runtime is embedded in `agentteam-install.sh`; the canonical
  `frugal-flock-install.sh` is a wrapper, not a second implementation.
- The UI and recovery flow are proposals. No frontend framework has been
  selected, and no working graphical app should be assumed to exist.
- Existing baseline checks passed: 40 selftests, 14 adversarial probes,
  branding smoke, ShellCheck, and documentation lint. Re-run appropriate
  checks for new changes; do not reuse those results as proof of new work.

## Next milestone and boundaries

Build a clickable, locally runnable prototype with clearly labeled sample
data. Validate comprehension before wiring up providers or an execution
service. Do not expand this into a whole desktop product in one session.

Five connected flows must work:

1. Choose a sample project and see sample tool-connection states.
2. Describe a change and review its proposed sample plan.
3. Approve the plan, follow sample progress, and answer a sample question.
4. Simulate a limit, inspect a saved-work summary, and choose a named
   replacement provider, wait/retry, or save for later.
5. Review a sample diff and checks, then request changes or simulate Apply.

One project workspace should contain the conversation and relevant plan,
activity, and review cards. Keep the actual provider names visible; do not
turn the main interface into a wall of terminals or quota charts.

## Acceptance criteria

- The complete journey is clickable and repeatable, with a reset-to-demo
  action and no dead-end primary buttons.
- Every simulated plan, connection, quota limit, checkpoint, and result is
  visibly sample data. No live provider calls or real filesystem/Git actions.
- Unknown capacity remains Unknown; do not invent provider percentages or
  assume another provider inherits conversation memory.
- Pause new work and Stop this run are explained as different actions.
- Failed, missing, or unknown checks cannot enable the successful Apply
  state. Reviewer completion and reviewer approval remain separate.
- Request changes is as discoverable as accepting a result.
- Keyboard navigation, visible focus, text status labels, readable type,
  and narrow-screen behavior are checked. Respect reduced-motion settings.
- Provide exact install/start/build/test commands. Run what the environment
  supports; list anything not run and why. Include tests for state transitions.
- Leave the existing CLI behavior, aliases, and configuration untouched.

## Copy-paste prompt

```text
Continue Frugal Flock from https://github.com/danielmevit/frugal-flock.
Use the latest main; do not restart the rename or assume prior chat memory.

The idea: different AI coding agents from different companies work as a
human-supervised team on one project. The audience includes learners,
makers, designers, solo developers, and small teams using modest AI plans.
Name: Frugal Flock. Tagline: Small plans. Big ideas.

First inspect the checkout and applicable AGENTS.md/MASTER.md/WORKER.md
instructions. Preserve existing changes. Use CodeGraph only if this repo
already has a .codegraph directory; do not create an index unasked.
Read README.md, docs/RESEARCH-FINDINGS.md, research/COMPETITIVE-REVIEW.md,
docs/ENGINE-FINDINGS.md, docs/BRAND.md, docs/UX-DIRECTION.md, TODO.md,
and this docs/AI-HANDOFF.md. Do not assume the historical Claude research
contains current provider pricing, permissions, or product facts.

My next requested milestone is the clickable mock-data UX prototype from
AI-HANDOFF.md, not the full backend. Present a short implementation plan
and an appropriate lightweight stack. Follow any applicable approval and
delegation rules before coding; then complete and verify that milestone.
Use a dedicated branch/worktree where required. Do not merge or push
without my approval; the previous publication approval was not permanent.

Build one calm project workspace with a persistent conversation plus plan,
activity, and review cards. Cover sample project/tool setup, describing a
task, plan approval, progress/questions, a provider-limit interruption with
saved-work summary and replacement choice, and review/request-changes/apply.
Use off-white, charcoal, restrained status accents, clear system typography,
keyboard access, visible focus, and words as well as colors for status.
Actual provider names must stay visible. No need for generated artwork.

Label all sample data and simulated actions. Do not invoke real agents,
collect credentials, execute shell text from the UI, touch real projects,
or make real commits/merges through the prototype. No invented quota bars,
silent paid fallbacks, automatic shared memory, or claims that recovery
already works. Keep process, validation, reviewer, human, and integration
states distinct. An unchecked or failed result cannot look ready to apply.

Preserve frugal-flock, frgl-flc, legacy agentteam, AGENTTEAM_* variables,
~/.config/agentteam, and the Linux flock utility. Do not rewrite the Bash
engine or fix all engine findings inside this UI-only milestone. The
engine, local bridge, durable jobs, and real provider recovery are later.

Meet the acceptance criteria in AI-HANDOFF.md. Test the interactive paths,
including limits, unknown capacity, failed/missing checks, and revisions.
Run the relevant existing regression checks without spending provider
quota. Report actual commands/results, preview instructions, changed files,
and unresolved limitations. Update TODO.md and leave a concise handoff so
another AI can continue. Stop at the verified prototype milestone.
```

## Later milestones, not included in the prompt above

1. Design and test structured result states for engine findings E1–E3.
2. Build a protected, localhost-only, read-only adapter before live controls.
3. Add bounded operations, durable jobs, and reconnectable progress.
4. Implement checkpointed provider continuation, with revalidation.
5. Add explicit human-approved integration tied to exact revisions.
6. Test with two newcomers and compare human effort against the old CLI.

Follow [TODO.md](../TODO.md) for priorities. Public visibility is not a
license decision; the owner still needs to choose a license before calling
the project open source.

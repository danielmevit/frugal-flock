# Frugal Flock — continuation report, 2026-10-04

## Exact stopping point

Repository: https://github.com/danielmevit/frugal-flock (public).
Brand: Frugal Flock — Small plans. Big ideas.

Start future sessions with [the continuation prompt](development/continue-with-ai-prompt.md).
The owner requested smaller checkpoints and an updated living prompt at
each one. The latest request is project-state cleanup and handoff only.
No implementation or new worker dispatch is authorized by this document.
Once the owner asks to resume, the next implementation checkpoint is ONLY
the hidden-index-flag fix and tests.

**M1 is not complete or merged.** All implementation work is preserved
on `agent/codex`, final implementation checkpoint
`80feafb15049411238b864cace7077af3f43376b`. Main retains the stable 0.3.1
runtime plus the latest docs, research, plan, and this handoff. The worker
runtime prints 0.4.0, but no release tag or completed-release claim exists.
Do not install the candidate globally or mistake main for the candidate.

The implementation checkout is clean and no worker remains active. The
last worker hit its provider usage limit after committing its progress.
No user credentials/configuration were changed and no live provider calls
were made by tests. Nothing was merged into main. All previous history is
retained. The saved quality commits were fast-forwarded intact into the
Codex checkout; the former `agent/kimi` branch is historical, not active.

## What is saved

| Commit / location | Work |
|---|---|
| `e230ad4`, main ancestor | Frozen M1 quality contract. |
| `e3bf9a1`, main ancestor | Quality-first plan, plain-language keywords/workflows, competitor feature decisions, Toolcraft reference, portable AI handoff. |
| `9f296da`, agent/codex | Strict missing-scope/check handling; auto-verify exit propagation; isolated check runner; updated initial operational docs/Word guide. |
| `4b8296c`, agent/codex | Embedded Python-stdlib revision snapshots/results, separate outcomes, gated review, availability JSON, host-access warnings, local context handoff. |
| `ef44611`, agent/codex | Expanded mock acceptance cases and small review-prompt/dispatch corrections. |
| `80feafb`, agent/codex | Regression for attempted public verify lock bypass. |
| Latest main docs | This report, updated M1 status/prompt, and the capacity-aware continuation proposal. |

## Documentation-only cleanup verification

- All 27 root/docs Markdown files passed `bash tools/check-docs.sh`.
- The changelog fragment and four local workspace/coordination Markdown
  files also passed the checker. All 74 relative links in the eight current
  handoff/navigation documents resolved; no obsolete prompt-name references
  remained in those documents. `git diff --check` passed.
- `git worktree list --porcelain` confirmed every registered checkout is
  inside the enclosing Frugal Flock folder. `agentteam status` recognized
  the moved layout, found all worker checkouts clean and reported no running jobs.
- No runtime source changes, new task dispatches, runtime test runs, provider
  calls, global installs, or main-branch implementation integration occurred.

## Earlier implementation verification

These results belong to the saved implementation before the workspace
relocation. This documentation-only checkpoint does not rerun or extend
the runtime test evidence and does not close any remaining M1 finding.

The lead independently ran the first increment's focused tests and full
isolated runner: 40 selftests, 16 focused regressions, 14 adversarial
probes, branding/aliases/Linux-flock checks, exact protocol identity,
installer syntax, installed-runtime ShellCheck, docs lint, and whitespace
checks passed. The Guidebook Word file was regenerated.

The frozen task gate also passed on `9f296da` and `4b8296c`: allowed scope
OK and 5/5 Validate commands passing. Final-checkpoint verification is
recorded below before publication. Passing tests do not close the known
correctness gaps or prove full contract coverage.

Final independent verification on `80feafb`: native frozen task gate
PASS, scope OK, **5/5 Validate commands** passed. A separate focused run
passed **16 basic plus 64 additional contract checks**. The gate's full
runner also reran the 40 selftests, 14 adversarial probes, installed-runtime
ShellCheck, syntax, branding/aliases/protocol identity and docs lint.
Known correctness findings below remain open despite these passing tests.

## Next work, in priority order

1. **Close the hidden-index-flag gap.** Snapshots hash real tracked content,
   including assume-unchanged files, but `changed()` and review material
   use Git diff/status paths that can omit those edits. Prevent passing
   scope/full-review claims over omitted work. Conservative refusal of
   assume-unchanged/skip-worktree flags is acceptable if documented; test it.
2. **Handle post-run snapshot failure truthfully.** `cmd_run` currently
   returns early if the post-run snapshot fails, before persisting the
   worker's actual exit/final report. Test a worker that exits nonzero after
   introducing an unsupported file type; preserve its actual exit and
   an explicit failed/unknown evidence state without asserting readiness.
   This is a source-review finding, not yet a dedicated reproduced test.
3. Finish missing acceptance cases, especially binary/oversized/partial
   review material, interrupted/atomic handoff publication, and a systematic
   audit against every frozen contract clause.
4. Finish help and completion for `result`, `handoff`, and `agents --json`;
   document the Python dependency, JSON schema, changed review exits,
   clean-committed/text-only review restrictions, and supported/unsupported
   snapshot cases. `docs/QUALITY-USAGE.md` and the changelog currently
   describe only the first increment and are stale relative to the candidate.
5. Update affected setup/operational/protocol documents and regenerate
   affected Word manuals. Preserve embedded/source PROTOCOL byte identity.
6. Re-run all gates, inspect the exact diff, record evidence, and obtain
   owner integration. Only then mark M1 accepted and move to UI work.

The known lock-bypass route through `verify WORKER TASK locked` was closed
by the dispatcher change; `80feafb` adds a held-lock regression. Do not
confuse that addressed issue with the two unresolved findings above.

## Continuing locally or from a fresh clone

Local workspace: `D:\Vibe Coding\_vm\frugal-flock`, or
`/mnt/d/Vibe Coding/_vm/frugal-flock` in WSL. Its main checkout is `repo/`,
Codex's implementation checkout is `wt/codex/`, and coordination is `coord/`.
Private references/prototypes are in `artifacts/`; disposable project
checks belong in `tmp/`. Read [WORKSPACE-RULES.md](development/WORKSPACE-RULES.md).

Native task `FF-QUALITY-kimi` and its append-only reports retain their
historical names and frozen scope/Validate commands. The native attempt
timed out; later built-in workers produced the saved implementation. No
new Codex task has been dispatched. When implementation is requested,
prepare a bounded Codex continuation without rewriting that history.

For a fresh clone, read this report from main, fetch the remote branches,
and work from `origin/agent/codex` using the repository's worker workflow.
Do not reset an existing dirty checkout. Main-only docs can be read with
`git show origin/main:docs/M1-STATUS.md` and equivalent paths after fetching.
No private logs or scratch files are required to resume.

The owner requested the local app-folder rename. The former
`agentteam-docs` folder was moved to `frugal-flock`, and `git worktree repair`
repaired all five linked worker references. No files were deleted and the
quality worktree remained clean. Subsequently, the Git checkout was placed
inside `frugal-flock/repo` and all worktrees and coordination moved under
the same enclosing workspace. All linked Git paths were repaired again.
Legacy command/config names are retained. Local `coord/`, `artifacts/`,
and `tmp/` are not part of the public repository; the portable handoff must
not depend on them, and private raw logs must not be published as backup.

Candidate checks for the next authorized implementation session, from
`wt/codex` (these are instructions, not results from this docs checkpoint):

```bash
export TMPDIR="/mnt/d/Vibe Coding/_vm/frugal-flock/tmp"
bash -n agentteam-install.sh
bash -n frugal-flock-install.sh
bash tests/frugal-flock-quality.sh
bash tools/quality-check.sh
bash tools/check-docs.sh
git diff --check
```

On another machine, set TMPDIR to its own workspace's existing `tmp/`
folder. If the native setup exists, also run the frozen validation gate
for the newly prepared Codex task and inspect its appended report and real
diff. Do not weaken the frozen scope or checks. The installed 0.3.1 tool
has a known missing-report issue on a first verify; use a project-local
temporary candidate install if needed, never silently replace the global
installation. Passing scripted checks is not full milestone acceptance.

## Product direction preserved

- Quality before UX; no graphical interface has been built.
- One place to coordinate separate coding agents/providers, not merged
  model weights, pooled subscriptions, or automatically shared memory.
- Adopt useful competitor ideas: explicit lifecycle states, evidence
  packages, optional independent review, separate workspaces, approachable
  team overview, and safe continuation. See FEATURE-DECISIONS.md.
- The owner especially values capacity-aware continuation: give a 30%-left
  agent a finishable task and reserve room for tests/checkpointing. See
  CAPACITY-AWARE-CONTINUATION.md. Telemetry/manual input/dry-run scheduling
  and real checkpoint/restore are future work, not features shipped by M1.
- M1's `handoff` is a local same-checkout CONTEXT packet, not a backup of
  dirty files, automatic provider migration, or an OS sandbox.
- Future UI may borrow Toolcraft's working-area/compact-inspector feel.
  Do not run its scaffolder or copy its code, templates, runtime, or assets.
- Preserve `frugal-flock`, `frgl-flc`, compatibility `agentteam`, existing
  `AGENTTEAM_*` variables/config paths, and the Linux `flock` utility.
- Public visibility is confirmed separately from licensing; a project
  license still needs the owner's decision.

## Copy-paste prompt

Open [continue-with-ai-prompt.md](development/continue-with-ai-prompt.md), copy the
text under **Prompt to paste**, and paste it into the next AI chat. This is
the single current prompt; this report supplies its supporting evidence.

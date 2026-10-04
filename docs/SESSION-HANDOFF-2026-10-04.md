# Frugal Flock — continuation report, 2026-10-04

## Exact stopping point

Repository: https://github.com/danielmevit/frugal-flock (public).
Brand: Frugal Flock — Small plans. Big ideas.

Start future sessions with [FRUGAL-FLOCK-NEXT-AI.md](../FRUGAL-FLOCK-NEXT-AI.md).
The owner requested smaller checkpoints and an updated living prompt at
each one. The next checkpoint is ONLY the hidden-index-flag fix and tests.

**M1 is not complete or merged.** All implementation work is preserved
on `agent/kimi`, final checkpoint
`80feafb15049411238b864cace7077af3f43376b`. Main retains the stable 0.3.1
runtime plus the latest docs, research, plan, and this handoff. The worker
runtime prints 0.4.0, but no release tag or completed-release claim exists.
Do not install the candidate globally or mistake main for the candidate.

The implementation checkout is clean and no worker remains active. The
last worker hit its provider usage limit after committing its progress.
No user credentials/configuration were changed and no live provider calls
were made by tests. Nothing was merged. All previous history is retained.

## What is saved

| Commit / location | Work |
|---|---|
| `e230ad4`, main ancestor | Frozen M1 quality contract. |
| `e3bf9a1`, main ancestor | Quality-first plan, plain-language keywords/workflows, competitor feature decisions, Toolcraft reference, portable AI handoff. |
| `9f296da`, agent/kimi | Strict missing-scope/check handling; auto-verify exit propagation; isolated check runner; updated initial operational docs/Word guide. |
| `4b8296c`, agent/kimi | Embedded Python-stdlib revision snapshots/results, separate outcomes, gated review, availability JSON, host-access warnings, local context handoff. |
| `ef44611`, agent/kimi | Expanded mock acceptance cases and small review-prompt/dispatch corrections. |
| `80feafb`, agent/kimi | Regression for attempted public verify lock bypass. |
| Latest main docs | This report, updated M1 status/prompt, and the capacity-aware continuation proposal. |

## Verification

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

Local layout: main checkout `/mnt/d/Vibe Coding/_vm/frugal-flock`, worker
checkout `/mnt/d/Vibe Coding/_vm/wt/kimi`, coordination in `../coord`.
Native task `FF-QUALITY-kimi` retains its frozen scope/Validate commands.
The old native Kimi log records a timeout, not the later built-in workers'
final result. Use commits, this report, and fresh tests as authority.

For a fresh clone, read this report from main, fetch the remote branches,
and work from `origin/agent/kimi` using the repository's worker workflow.
Do not reset an existing dirty checkout. Main-only docs can be read with
`git show origin/main:docs/M1-STATUS.md` and equivalent paths after fetching.
No private logs or scratch files are required to resume.

The owner requested the local app-folder rename. The former
`agentteam-docs` folder was moved to `frugal-flock`, and `git worktree repair`
repaired all five linked worker references. No files were deleted and the
quality worktree remained clean. Legacy command/config names are retained.

Candidate checks, from its checkout:

```bash
bash -n agentteam-install.sh
bash -n frugal-flock-install.sh
bash tests/frugal-flock-quality.sh
bash tools/quality-check.sh
bash tools/check-docs.sh
git diff --check
```

If the local native setup exists, additionally run
`agentteam verify kimi FF-QUALITY-kimi` from the main checkout, then read
the real diff and appended report. Do not change the frozen task to weaken
the gate. Passing scripted checks is not full milestone acceptance.

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

```text
Continue Frugal Flock at https://github.com/danielmevit/frugal-flock.
First read FRUGAL-FLOCK-NEXT-AI.md, the continuation report and M1-STATUS from
latest main. The implementation is NOT on main: it is on agent/kimi at
80feafb15049411238b864cace7077af3f43376b. Fetch and inspect actual branch
state; preserve existing changes and follow AGENTS/MASTER/WORKER rules.
Do not restart the rename, research, or already implemented quality work.

Finish M1 QUALITY before UX, following docs/QUALITY-M1-CONTRACT.md frozen
at e230ad4. Start with the report's hidden-index-flag scope/review gap and
post-run snapshot failure/exit preservation. Add regression tests, finish
missing contract coverage, help/completion, schema/dependency/command docs,
matching embedded/source protocol, changelog and affected Word manuals.
Run the exact isolated checks listed in the report and inspect the real
diff. Tests must use mocks, not live providers. Never claim M1 complete
merely because existing tests pass. Record actual SHA/results and leftovers.

Preserve aliases/config paths and Linux flock. No global install, credential
changes, paid fallback, merge or release without owner authorization.
The previous push approval applies to the completed handoff publication,
not a standing authorization for future external changes.

The owner endorsed capacity-aware task sizing and clean continuation after
limits. Read docs/CAPACITY-AWARE-CONTINUATION.md from main; it remains a
later milestone. M1 handoff is context for the same checkout, not a backup
or automatic migration. Future UI follows docs/UX-DIRECTION.md and
docs/TOOLCRAFT-REFERENCE.md: original components, no copied Toolcraft code.
Leave a tested, committed checkpoint and an updated next-AI handoff.
Use small single-issue checkpoints. Update FRUGAL-FLOCK-NEXT-AI.md after
each checkpoint with its exact SHA, tests, workers, gaps and next task.
```

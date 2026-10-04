# Milestone 1 — quality checkpoint

## Status

In progress, **not accepted or merged**. The public shipped CLI baseline
is 0.3.1. Do not advertise the planned 0.4.0 changes as shipped until the
implementation is independently verified and integrated by the owner.

Frozen requirements: [QUALITY-M1-CONTRACT.md](QUALITY-M1-CONTRACT.md)
at `e230ad4`. The current implementation target is `agent/codex` in
`../wt/codex`, relative to the main `repo/` checkout. Its four saved quality
commits end at **`80feafb15049411238b864cace7077af3f43376b`**.
These existing commits were fast-forwarded into Codex's checkout without
changing the implementation or merging it into main. The former branch
and `FF-QUALITY-kimi` task/reports are historical records, not the current
worker assignment.

The checkout is clean and no implementation worker is active. The owner
has limited the current work to project-state cleanup and handoff docs.
Do not dispatch or resume implementation until explicitly requested.
This is **work in progress, not an accepted 0.4.0 release**. See the
[final continuation report](SESSION-HANDOFF-2026-10-04.md) for the exact
code/document branches, known blockers, and next actions.

## Resume locally

```bash
agentteam status
git -C ../wt/codex status --short --branch
git -C ../wt/codex log -4 --oneline
```

Inspect the saved candidate without changing either checkout:

```bash
git diff main...agent/codex --stat
git diff main...agent/codex -- agentteam-install.sh tests/ tools/quality-check.sh
```

When implementation is authorized again, the lead should prepare a bounded
Codex task preserving the frozen scope and validation requirements. Do not
rewrite the historical task or dispatch a worker just to complete this handoff.
Use the candidate checks in the [continuation report](SESSION-HANDOFF-2026-10-04.md).

Review the real diff, not just the report. A failure needs a bounded repair
task; preserve the original contract and all partial work. Never reset a
dirty worktree or restart an interrupted implementation from scratch.

## First increment — independently checked

Candidate `9f296da` adds strict missing-scope/check handling (INCOMPLETE,
exit 2), preserves real-failure precedence, and propagates automatic
verification failures while keeping the worker's own failure exit.
Reasons remain in terminal output and append-only reports.

Independent checks on 2026-10-04:

- `bash tests/frugal-flock-quality.sh`: 16 focused regressions passed.
- `bash tools/quality-check.sh`: passed, including 40 selftests, those
  16 focused regressions, 14 adversarial probes, installer syntax,
  installed-runtime ShellCheck, branding/aliases/protocol identity, and
  documentation lint. Repeated successfully after the manual corrections.
- `git diff --check`: clean. `docs/GUIDEBOOK.docx` regenerated.
- Source inspection confirms the bounded E1/exit-propagation changes;
  the full milestone contract is not yet implemented.

The frozen gate passed on `9f296da` and `4b8296c`: scope OK and all five
Validate commands passed. Final-checkpoint results are recorded in the
continuation report. A passing gate does not prove that every contract
edge is covered. No owner integration has occurred.

Final candidate `80feafb` also passed the native frozen gate (scope OK,
5/5 commands). Independent focused results: 16 basic + 64 contract checks.
The exact next small task and checkpoint-maintenance rule are in the root
[continuation prompt](../continue-with-ai-prompt.md).

## Later implementation checkpoints

- `4b8296c`: embedded Python-stdlib snapshots, atomic result storage,
  separate outcomes, conservative reviewer parsing/gating, availability
  JSON, trusted-host warnings, and manual handoff packets.
- `ef44611`: broader mock acceptance cases plus prompt/dispatch fixes.
- `80feafb`: regression proving an extra public verify argument cannot
  bypass a held worker lock.

These are implemented candidates, not claims of complete reliability.
The initial `docs/QUALITY-USAGE.md` on the worker branch still describes
only the first increment and needs updating for the newer commands.

## Remaining before M1 can be accepted

1. Fix the hidden-index-flag gap: snapshots hash actual tracked contents,
   but Git's diff/status-derived scope and review material can omit edits
   under assume-unchanged/skip-worktree flags. Reject unsupported flags
   conservatively or prove complete material/scope; add regressions.
2. Repair/audit run finalization when the post-run snapshot fails: the
   current early return can lose the actual worker exit and leave persisted
   process state running. Preserve truthful failed-process evidence without
   manufacturing a fresh revision; add a nonzero-worker/snapshot-failure test.
3. Expand missing acceptance coverage, especially binary/oversized review
   material, interrupted packet publication, and full contract edge cases.
4. Update help/completion, Python dependency/setup instructions, result
   schema and command docs, changed review exits/constraints, operational
   protocol copies, and affected Word manuals. Changelog also needs the
   later increment description.
5. Run all gates again, inspect the exact final diff, and obtain owner
   acceptance/integration before claiming M1 complete or starting live UX.

Do not repeat the completed rename, research, or first increment. Continue
from this saved branch and preserve its changes. The runtime now embeds its
own helper; the older scratch prototype is now kept locally in
`artifacts/legacy-prototypes/agentteam-quality.py` under the enclosing
workspace. It is obsolete and must not replace the embedded helper.
A fresh clone needs no private logs,
temporary helper, or original conversation.

## Boundaries

M1 adds dependable CLI evidence and a manual context packet. It does not
add a GUI, automatic provider migration, full dirty-file backup, an OS
sandbox, or automatic merging. No global installation is part of this task.
Use [the continuation prompt](../continue-with-ai-prompt.md) to start the
next AI session; [AI-HANDOFF.md](AI-HANDOFF.md) is supporting product context.

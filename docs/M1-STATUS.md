# Milestone 1 — quality checkpoint

## Status

In progress, **not accepted or merged**. The public shipped CLI baseline
is 0.3.1. Do not advertise the planned 0.4.0 changes as shipped until the
implementation is independently verified and integrated by the owner.

Frozen requirements: [QUALITY-M1-CONTRACT.md](QUALITY-M1-CONTRACT.md)
at `e230ad4`. Local implementation: task `FF-QUALITY-kimi`, branch
`agent/kimi`, worktree `../wt/kimi`. The native Kimi attempt hit its
30-minute timeout (exit 124) without repository edits or commits. Its
scratch helper was not validated and is not a shipped feature.

A single built-in implementation worker is continuing the same frozen
scope in that worktree, with tested incremental commits requested. The
native runner's status will not show this built-in worker: consult the
active session before starting another writer. Do not reset or sync its
checkout during implementation.

## Resume locally

```bash
agentteam status
git -C ../wt/kimi status --short --branch
git -C ../wt/kimi log -3 --oneline
tail -n 25 ../coord/reports/FF-QUALITY-kimi.log
```

After the worker stops, inspect its report and run the frozen task gate:

```bash
agentteam verify kimi FF-QUALITY-kimi
git diff main...agent/kimi --stat
git diff main...agent/kimi -- agentteam-install.sh tests/ tools/quality-check.sh
```

Review the real diff, not just the report. A failure needs a bounded repair
task; preserve the original contract and all partial work. Never reset a
dirty worktree or restart an interrupted implementation from scratch.

## Acceptance record

Pending: candidate commit, exact independent test counts/results, source
review, any remaining contract failures, and owner integration decision.
The next reviewer must replace this pending record with actual evidence.
Old branding tests are baseline evidence only.

## Boundaries

M1 adds dependable CLI evidence and a manual context packet. It does not
add a GUI, automatic provider migration, full dirty-file backup, an OS
sandbox, or automatic merging. No global installation is part of this task.
Use [AI-HANDOFF.md](AI-HANDOFF.md) as the next-AI prompt.

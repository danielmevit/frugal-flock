# Frugal Flock — engine findings and acceptance criteria

Reviewed 2026-10-03 against published baseline `f962b6a`. This is a
source-backed follow-up list, not a claim that these issues were fixed.
The rename and documentation work did not change these semantics.

The owner subsequently requested **quality before UX**. The bounded
[M1 contract](QUALITY-M1-CONTRACT.md) targets E1–E3, honest E5 diagnostics,
E4 warnings, and a manual E6 context packet. Track implementation evidence
in [M1 status](M1-STATUS.md); assignment alone does not close a finding.

2026-10-04 checkpoint: worker branch `agent/codex` at `80feafb` contains
strict verification, exit propagation, structured evidence, review parsing,
honest availability, and manual context packets. It is not merged into
main or accepted as complete. Hidden-index-flag handling, post-run snapshot
failure finalization, coverage, and documentation need follow-up; see
[the continuation report](SESSION-HANDOFF-2026-10-04.md). E4 OS isolation
and full E6 automatic checkpointed migration remain future work.

## E1. Missing evidence can still receive PASS

Status: open; must be resolved before a UI treats verification as permission
to apply changes.

In `cmd_verify`, no scope patterns produce `UNCHECKED`. No validation
commands leave both counters at zero. Neither condition alone changes
the final verdict from PASS. A nonempty candidate can therefore pass
without either class of evidence. The self-test even includes the current
permissive no-Validate behavior; passing it does not resolve this finding.
See [verification logic at the reviewed revision](https://github.com/danielmevit/frugal-flock/blob/f962b6a/agentteam-install.sh#L571-L639).

Required outcome: distinguish complete verification, failed verification,
and missing evidence. M1 deliberately provides no waiver bypass. Missing evidence
must not silently enable Apply. Define compatibility before changing CLI
exit codes or the task schema.

Regression cases: missing scope; missing checks; both missing; all checks
present and passing; failed check. Update the old permissive self-test
intentionally, not accidentally. Any future waiver needs a separate contract.

## E2. Worker exit and verification outcome are different

Status: open.

With automatic verification enabled, `cmd_run` invokes `cmd_verify` with
`|| true`, then returns the worker process's original exit code. A worker
exit of zero can coexist with failed validation in the report.
See [automatic verification](https://github.com/danielmevit/frugal-flock/blob/f962b6a/agentteam-install.sh#L518-L525).

Required outcome: preserve both process status and validation status in a
structured result. A client must never turn process exit zero alone into
Ready to apply. Whether to change the public CLI exit code is a deliberate
compatibility decision, not a frontend assumption.

Regression cases: worker succeeds/checks fail; worker fails/checks pass;
checks not run; all checks pass. Verify each state survives persistence
and a client refresh.

## E3. A reviewer finishing does not mean approval

Status: open.

`cmd_review` asks for an APPROVE or REQUEST-CHANGES line, but records and
returns the review process's exit code without parsing that decision.
See [review implementation](https://github.com/danielmevit/frugal-flock/blob/f962b6a/agentteam-install.sh#L787-L842).

Required outcome: separate process result from approved, changes requested,
and unknown reviewer decisions. Missing, contradictory, or malformed
verdicts are not approvals. Bind a usable decision to the reviewed revision.

Regression cases: exit zero with REQUEST-CHANGES; missing verdict; multiple
conflicting verdicts; valid approval; review timeout; candidate changed
after the review. No case should silently become accepted by a human.

## E4. Worktrees are not security isolation

Status: current limitation; document now, decide stronger isolation before
supporting less-trusted workloads or exposing an execution service.

Several shipped invocation templates enable broad permissions. Separate
Git worktrees and branch/scope checks help coordinate edits but do not
prevent operating-system access outside the worker folder. A reviewer
launched in a temporary directory is not thereby sandboxed either.
See [invocation templates](https://github.com/danielmevit/frugal-flock/blob/f962b6a/agentteam-install.sh#L1605-L1635)
and [review launch](https://github.com/danielmevit/frugal-flock/blob/f962b6a/agentteam-install.sh#L826-L829).

Current guidance: use a disposable environment without production secrets;
WSL by itself is not a host-file isolation boundary. Task scope checks
are not a claim of prevention before execution.

Acceptance criteria for any later sandbox claim: an explicit threat model,
OS-enforced filesystem/process/network limits, and negative tests proving
the worker cannot access protected resources. A frontend must not expose
an arbitrary shell endpoint or copy provider tokens into browser storage.

## E5. Availability is not a universal quota reading

Status: current limitation; model honestly in the UI.

The engine provides binary detection, manual/timed benching, and optional
failed-run limit-message detection. These are not proof of a valid login
or a provider's remaining allowance. An operator-selected retry interval
is not a confirmed provider reset time. See `cmd_agents`, `cmd_off`, and
the `LIMIT_RE`/`AGENTTEAM_AUTO_OFF` handling in
[the engine](../agentteam-install.sh).

Required states: installed, sign-in needed, available, limited, unavailable,
or unknown, with evidence and timestamps when available. Show no invented
percentages. Authentication checks and live smoke calls must be distinguished
from free local diagnostics.

## E6. Reliable cross-provider continuation is still product work

Status: planned, not implemented as an automatic flow.

Task files, worktrees, reports, and availability controls are useful
ingredients. They do not by themselves implement a durable checkpoint,
safe provider replacement, preserved conversation context, and resumed
validation. During the rename, a human-supervised replacement preserved
partial edits after a limit; that is an operational example, not proof of
an automatic recovery feature.

Acceptance criteria: settle or stop the old run; capture committed and
uncommitted work, exact revisions, task instructions, completed checks,
and unfinished work; select a named available replacement; preserve the
checkpoint; revalidate and seek human acceptance. Test interruption during
editing, validation, and handoff. Prevent two agents writing the same
workspace while continuation is being prepared.

## What is already working

The reviewed baseline includes three compatible command names, worktrees,
task scope checks, validation execution, reports, ledger events, manual
availability controls, and human-controlled integration. Published checks
passed: 40 selftests, 14 adversarial probes, branding smoke, documentation
lint, and ShellCheck. The main publication turn reran those checks.

Existing regression coverage includes path traversal, task tampering,
rename-source scope checking, validation stdin isolation, and run/verify
locking. These checks establish their tested behavior, not resolution of
E1–E6 or production-grade security.

## Order of work

Complete and verify M1 before starting the mock-data UX prototype. Its
frozen contract covers exact candidate/base revisions, task text, and
dirty/untracked worktree contents. Full E4 OS isolation and full E6 automatic
checkpointed migration remain separate work. A manual same-checkout context
packet is not a backup of uncommitted files. After M1 acceptance and the
prototype, begin the local adapter read-only with explicit safety boundaries.

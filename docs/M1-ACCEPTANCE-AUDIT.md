# Milestone 1 — acceptance audit

Audit of the frozen [QUALITY-M1-CONTRACT.md](QUALITY-M1-CONTRACT.md)
(`e230ad4`) against the regressions that prove each requirement. Written
2026-10-04 by Claude Code subagent `claude-tests` (Claude Opus 5.5) on
branch `agent/claude-tests`, based on main `fade423`. This audit is
evidence for M1 item 3. It is not an acceptance claim: only the owner
accepts M1.

## Where the evidence lives

- **quality**: labels from `tests/frugal-flock-quality.sh` (16 basic checks).
- **contract**: `quality:` labels from `tests/frugal-flock-quality-cases.py`.
- **coverage**: `coverage:` labels from `tests/frugal-flock-quality-coverage.py`,
  added by this audit to close the gaps it found.
- **selftest**: `frugal-flock selftest` check names.
- **probe**: `tests/agentteam-probes.sh` probe names.
- **branding**: `tests/frugal-flock-branding.sh`.

All of these run from `bash tools/quality-check.sh` with mock providers
only. Status values: covered, partial, gap, or not mock-testable.

## Scope and limits

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| Limits | Public command and config names stay compatible | branding: shared entrypoints, completion, reinstall | covered |
| Limits | Old reports and ledger history are preserved | coverage: `reports and ledger are append-only` | covered |
| Limits | Python 3 standard library only, no downloaded dependency | Helper imports are stdlib (code inspection); `tools/quality-check.sh` checks local `python3` | covered by inspection |
| Limits | New dependency is preflighted before a provider starts | coverage: `missing Python 3 stops run before any provider starts` | covered |
| Limits | Installer stays self-contained; aliases share one runtime | branding: three shared entrypoints, protocol identity | covered |

## 1. Fail closed on absent verification evidence

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| 1 | PASS and exit 0 only with scope, at least one check, all checks passing | quality: `complete validation`, `ordinary worker` | covered |
| 1 | Missing scope gives INCOMPLETE, exit 2 | quality: `missing-scope incomplete` | covered |
| 1 | Missing checks give INCOMPLETE, exit 2 | quality: `missing-checks incomplete`, `missing-both incomplete`; selftest: `verify is INCOMPLETE on a no-Validate task` | covered |
| 1 | Check failure fails, normally exit 1 | quality: `real check failure`; coverage: `failed check persisted with counts` | covered |
| 1 | Scope violation fails | quality: `real scope violation` | covered |
| 1 | Tampered task file fails | probe: `verify-launders-worker-scope-rewrite` (asserts not PASS, nonzero) | covered |
| 1 | Empty work fails | quality: `empty candidate failure`; selftest: `verify FAILs an empty run` | covered |
| 1 | Unavailable base fails | probe: `verify-passes-on-vanished-base` | covered, exit 2 (see finding F1) |
| 1 | Failure takes precedence over incomplete evidence | coverage: `real failure outranks missing checks` | covered |
| 1 | Failure reasons are preserved individually | coverage: `missing scope and checks keep both reasons`, `real failure outranks missing checks` | covered |
| 1 | No waiver mechanism | No waiver command or flag exists (code inspection) | not mock-testable: absence of a feature |
| 1 | Old no-Validate selftest expects incomplete | selftest: `verify is INCOMPLETE on a no-Validate task` | covered |

## 2. Separate outcomes and bind evidence to work

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| 2 | Schema-versioned JSON persisted under `coord/results/WORKER/TASK.json` | contract: `current success persists and reloads` | covered |
| 2 | Atomic replacement while holding the worker lock | contract: run/review/verify `refuses worker lock`; coverage: `no temporary result files left behind` | partial: a kill during the result write is not simulated |
| 2 | Append-only reports and ledger retained | coverage: `reports and ledger are append-only`; selftest: `run event in ledger.jsonl` | covered |
| 2 | Every minimum field present, including reviewer ID | coverage: `result carries every contract field` | covered |
| 2 | Worktree hash covers index, tracked and untracked content, not just names | contract: `tracked content stale`, `index stale`, `untracked content changes hash`, `assume-unchanged content is hashed` | covered |
| 2 | Ignored files excluded; file type and mode included | coverage: `ignored files stay out of the hash; mode changes are in it`; contract: `symlink target hashed without dereference` | covered |
| 2 | Spaces, Unicode, symlinks and JSON escaping handled | contract: `JSON-special untracked filename`, `symlink target hashed without dereference` | covered |
| 2 | Process states, exit null while unknown | coverage: `process is running with an unknown exit, then succeeded`; contract: `snapshot failure keeps worker exit 7` | covered |
| 2 | Validation states with scope, counts, reasons and revision | contract: `candidate changes during validation`; coverage: `failed check persisted with counts` | covered |
| 2 | Review states, reviewer, process exit and revision | contract: review table, `timeout process exit preserved` | covered |
| 2 | Human pending and integration not attempted, never forged | contract: `separate human and integration states`, `malformed state rejects human forged` | covered |
| 2 | `result` prints JSON only and calls no provider | contract: every `result` read parses stdout as JSON; coverage: `result and handoff never invoke a provider` | covered |
| 2 | Changed commit, base, task, index or content makes evidence stale | contract: `task hash stale`, `tracked content stale`, `index stale`, `candidate commit stale`, `base commit stale`, `JSON-special untracked filename` | covered |
| 2 | Missing or malformed result fails closed | contract: `missing result fails closed`, `malformed JSON fails closed for result and handoff`, `malformed state rejects` cases | covered |
| 2 | Old PASS report text is never backfilled | coverage: `old PASS report text is not trusted as structured evidence` | covered |
| 2 | Changes during checks or review cannot receive fresh evidence | contract: `candidate changes during validation`, `candidate changes during review` | covered |
| 2 | Readiness needs succeeded, passed, approved, current, not stale | contract: `current success persists and reloads`; coverage: `auto-verify keeps worker exit and validation; a failed worker is never ready` | covered |
| 2 | Unknown and not-run states stay visible | contract: `handoff without result has explicit unknown states` | covered |
| 2 | A new run resets old readiness | contract: `new run clears old validation/review` | covered |
| 2 | Auto-verify keeps both worker exit and verification outcome | quality: `auto-verify failure propagates`, `auto-verify incomplete propagates`, `worker failure preserved`; coverage: `auto-verify keeps worker exit and validation` | covered |
| 2 | Auto-verify off: exit 0, validation not run, not ready | quality: `ordinary worker`; contract: `new run clears old validation/review` | covered |
| 2 | Post-run snapshot failure keeps the real exit (M1 item 2) | contract: `snapshot failure keeps worker exit 7`, `snapshot failure still writes report and ledger`, `unbound process evidence stays stale after cleanup` | covered |

## 3. Parse independent review conservatively

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| 3 | Exactly one standalone verdict line; otherwise unknown | contract: `review no verdict`, `review malformed verdict`, `review indented verdict`, `review duplicate verdict`, `review contradictory verdict` | covered |
| 3 | Reviewer process failure is failed regardless of text | contract: `review process failed with approval` | covered |
| 3 | Raw output kept locally, never run as shell | coverage: `raw reviewer output kept locally and never executed` | covered |
| 3 | Stderr cannot manufacture approval | contract: `review stderr approval` | covered |
| 3 | Exits 0 approve, 1 changes or failure, 2 unknown or stale | contract: review table codes, `task hash stale` | covered |
| 3 | Actual reviewer process exit persisted separately | contract: `timeout process exit preserved`, review table | covered |
| 3 | Current passed validation required before any reviewer runs | contract: `review requires structured validation`; coverage: `no reviewer runs without current passed validation` | covered |
| 3 | Worker lock held; before and after revisions compared | contract: `review holds worker lock`, `candidate changes during review` | covered |
| 3 | Human acceptance stays pending | contract: `separate human and integration states` | covered |
| 3 | Incomplete material reported, never approved | contract: `dirty review refused without invocation`, `flagged index refuses review material`; coverage: binary, oversized and non-UTF-8 material refused before any reviewer runs | covered |

## 4. Honest availability and execution boundary

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| 4 | `agents --json` fields: binary, bench, retry, unknown auth and capacity, trusted host | contract: `availability authentication/capacity unknown`, `operator retry recorded honestly` | covered |
| 4 | No sign-in or quota probe; configured commands never executed | contract: `no availability command executed` | covered |
| 4 | Leading assignments and `env` resolved; ambiguous wrappers unknown | contract: `assignments/env and quoted executable resolve`, `missing and ambiguous binaries truthful` | covered |
| 4 | Human output separates installed from usable; bench is not a provider reset | coverage: `human availability separates installed from usable`; contract: `operator retry recorded honestly` | covered |
| 4 | Live run, review and smoke announce host-level access, no sandbox claim | coverage: `run, review and smoke state the trusted-host boundary` | covered |
| 4 | User's authenticated CLIs and global config untouched | Suites use isolated config directories by design | not mock-testable: real accounts are out of reach |
| 4 | Full OS isolation | Out of scope by contract | not applicable |

## 5. A next-AI packet, not an automatic restore

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| 5 | Refuse a locked or running worker | contract: `handoff refuses worker lock`, `review holds worker lock` | covered |
| 5 | New unique packet under `coord/handoffs/WORKER/TASK/` | contract: `unique atomic handoff`; coverage: `next handoff after an interruption is complete and unique` | covered |
| 5 | Task text, current result, revision, changed files and `HANDOFF.md` sections | contract: `handoff contains only context`; coverage: `handoff packet carries task, revision, checks, issues and next steps` | covered |
| 5 | Uncommitted and untracked work stated as left in the source checkout | contract: `handoff states source-only untracked work` | covered |
| 5 | No credentials, config, ignored files, raw logs or home folders copied | contract: `handoff contains only context` (exact file set) | covered |
| 5 | Warn to review task text before sharing | coverage: `handoff packet carries task, revision, checks, issues and next steps` | covered |
| 5 | No upload, no replacement provider invoked | coverage: `result and handoff never invoke a provider` | covered |
| 5 | Atomic output; before and after revisions compared | coverage: `candidate change during handoff publishes no packet`, `handoff killed mid-publication publishes no partial packet` | covered (see finding F2) |
| 5 | Paths stay under the coordination root; symlink escape refused | contract: `handoff symlink escape refused`, `result symlink refused` | covered |
| 5 | Prior packets stay intact | coverage: both atomic-publication checks compare earlier packets byte for byte | covered |
| 5 | Invalid worker or task IDs fail | contract: `result invalid IDs refused`, `handoff invalid IDs refused`; probe: `control-id-escape` | covered |
| 5 | Packet says old evidence needs rechecking after edits or a move | coverage: `handoff packet carries task, revision, checks, issues and next steps` | covered |

## Acceptance gate

| Clause | Requirement | Evidence | Status |
|---|---|---|---|
| Gate | Focused mock-only regression script and repeatable isolated runner | `tests/frugal-flock-quality.sh`, `tools/quality-check.sh` | covered |
| Gate | Every listed case: scope, failures, auto-verify, review decisions, stale states, filenames, reload, locking, atomic packets, availability | Sections 1 to 5 above | covered |
| Gate | Selftest, probes, branding, ShellCheck, syntax and docs lint all run | `tools/quality-check.sh` | covered |
| Gate | Embedded and source PROTOCOL identity preserved | branding: protocol identity | covered |
| Gate | Docs, examples and manuals updated for changed behavior | M1 item 4 (subagents `claude-help` and `claude-docs`) | outside this audit |
| Gate | No completion claim with failing checks or unimplemented clauses | Owner acceptance in M1 item 5 | outside this audit |

## Findings

- **F1, minor, open:** `verify` with an unavailable base exits 2, because the
  revision snapshot fails before the base check that would exit 1. It never
  reports PASS and records nothing, so it fails closed. The contract says
  "normally 1". Left unchanged: making it 1 means reordering `cmd_verify`,
  a bash command outside this audit's scope.
- **F2, observation:** a handoff killed mid-publication leaves a
  `.pending-*` scratch folder in `coord/handoffs/WORKER/TASK/`. No partial
  packet is ever published under a final name, and earlier packets are
  untouched, so the atomicity requirement holds. The folder can be deleted.
- No new defect: all 23 coverage checks passed on the first run of the
  unchanged engine.

## Still open

- A kill during the result-file write is not simulated (atomic rename by
  code inspection only).
- Global configuration and real-account behavior cannot be tested with mocks.

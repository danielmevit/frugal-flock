# Recovery validation — 2026-10-08

The v0.5.4 recovery features are implemented in source. Published and installed
v0.5.3 remains unchanged. Source integration is not release acceptance.

## Results so far

The first combined source gate stopped on an outdated completion expectation:
the runtime exposes four save commands, while that assertion required three.
The corrected full manual-saving suite passed 186 checks. A later standalone
packaging comparison exposed an outdated embedded model-scoreboard guide;
the guide was synchronized with its canonical repository copy without weakening
the comparison. Its six focused native checks passed.

The original failing runs remain evidence. This is component coverage gathered
across those runs and bounded corrections, not a claim that the original full
gate passed. Unchanged earlier results are reused under the current YOLO policy.

| Area | Observed result |
| --- | --- |
| Native runner and evidence contracts | Selftest 40, shell regressions 16, contract regressions 80, coverage regressions 26: passed |
| Loop protection, limit handling and observation | 22, 9 and 26 checks respectively: passed |
| Provider prompt transport | 73 checks plus isolated dispatch/reinstall fixtures: passed; no real AI calls |
| Browser progress, API, files and server | 20, 12, 16 and 17 tests respectively: passed |
| Work modes and account admission | 57 policy and 32 guard checks: passed |
| Manual and automatic saving | 186 and 61 checks respectively: passed |
| Authorized continuation | Original 90-second case deadline and later 30-minute overall check timed out; completed prefix retained, remaining phase passed 31 assertions; default full-sequence release gate pending |
| Lead cooldown | 106 offline assertions passed; real metadata-only quota/configuration checks passed; genuine limit-to-restart cycle not_run |
| Queue and browser execution | 34 queue, 60 execution-service and 22 execution-API tests passed; plan storage/API and process cleanup passed |
| Adversarial probes | All 14 held; zero broken probes |
| Standalone guide parity | Six focused native checks passed after synchronizing the embedded guide |

All new corrections were performed by the existing lead, with personal review.
No additional implementation/reviewer AI sessions were started for these checks;
no fresh independent AI-lab approval is claimed. Worker failures and prior
independent reviews retain their original attribution.

The first versioned v0.5.4 candidate gate completed in 1,922.265 seconds and
failed in the interruption fixture: it allowed only eight seconds for mock
startup, while native baseline recovery capture runs before provider launch
and has its own 30-second budget. The bounded test-only correction keeps all
22 loop-brake assertions and allows 60 seconds to observe startup. Only its
holding mock receives a longer provider timeout; ordinary runs and production
runtime limits are unchanged. All 22 checks and both native validation checks
passed. Five measured startups took 9.766–13.182 seconds, beyond the old limit.
The original gate remains failed; its guarded packaging job correctly stopped
without generating artifacts. The corrected candidate still needs its complete
release gate and genuine cooldown acceptance.

The continuation harness now allows its outer call to outlive the native
provider deadline and preserves timeout output. The longer run progressed
through durable Unknown, shared-account refusal and changed-task rejection
before its overall deadline. Its revision binding also became stale when the
lead moved main during validation. That failure is retained. The focused remaining-phase check kept main frozen and passed 31 assertions,
including interruption cleanup, successful continuation, prompt integrity, clean
recovery and final source/result preservation. Its output explicitly says partial.
Every original assertion remains in the default release invocation.

## Remaining release work

The version/changelog are prepared on the unpublished release branch. Run the
required full gate on the corrected exact v0.5.4 candidate, including default
full continuation. Exercise a genuine
supported subscription limit and restart before publication. Check artifacts and upgrade
preservation before publication and verified installation. Offline clocks and
a successful ordinary launch do not establish genuine quota recovery.

The genuine cycle requires the current Codex workflow to exit before an owner
enables the supervisor. The first supported adapter is Codex CLI 0.161.0 on
Linux/Python 3.11+ with an individual first-party ChatGPT subscription. Do not
manufacture a limit, bypass account admission or infer a worker reset from the
lead's allowance. See [lead cooldown recovery](../LEAD-COOLDOWN.md).

## Performance finding

On this mounted workspace, the continuation fixture recorded legitimate calls
of 92.676 and 167.882 seconds, beyond the old outer 90-second test deadline.
An observed helper was waiting in filesystem RPC. These are local measurements,
not model benchmarks or proof of the complete latency cause. Profile repeated
filesystem/Git reads in the later performance milestone; retain recovery
integrity checks and real provider timeout limits while doing so.

## Agent credit

Commit author identity remains the human contributor. Some historical Claude
commits include Co-authored-by trailers; recent Codex lead commits lacked an
agent-credit trailer. This metadata difference does not describe the amount of
work done. Record actual AI assistance consistently in new commit messages and
receipts, while preserving published history and attribution to other workers.
GitHub links contributor credit through account-associated commit email; do not
invent an agent email or promise that a text credit creates a sidebar entry.
See [GitHub’s coauthor guidance](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors).

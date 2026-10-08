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
| Authorized continuation | Original 90-second case deadline and later 30-minute overall check timed out; completed assertions passed, remaining lifecycle checks in progress; full-sequence acceptance pending |
| Lead cooldown | 106 offline assertions passed; real metadata-only quota/configuration checks passed; genuine limit-to-restart cycle not_run |
| Queue and browser execution | 34 queue, 60 execution-service and 22 execution-API tests passed; plan storage/API and process cleanup passed |
| Adversarial probes | All 14 held; zero broken probes |
| Standalone guide parity | Six focused native checks passed after synchronizing the embedded guide |

All new corrections were performed by the existing lead, with personal review.
No additional implementation/reviewer AI sessions were started for these checks;
no fresh independent AI-lab approval is claimed. Worker failures and prior
independent reviews retain their original attribution.

The continuation harness now allows its outer call to outlive the native
provider deadline and preserves timeout output. The longer run progressed
through durable Unknown, shared-account refusal and changed-task rejection
before its overall deadline. Its revision binding also became stale when the
lead moved main during validation. That failure is retained. The next focused
check keeps main frozen and runs only the remaining cases; its output explicitly
says partial. Every original assertion remains in the default release invocation.

## Remaining release work

Finish the continuation sequence, exercise a genuine supported subscription
limit and restart, then finalize the version/changelog and run the required
full gate on the exact v0.5.4 release candidate. Check artifacts and upgrade
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

# Recovery validation — 2026-10-08

The v0.5.4 recovery release passed its complete automated quality gate and
installer upgrade/restore checks. Its optional lead cooldown supervisor is
experimental: the genuine subscription-limit-to-restart cycle remains unverified.

## Complete candidate verification — 2026-10-09

The tested [v0.5.4 candidate at `5a839fc`](https://github.com/danielmevit/unio/commit/5a839fc69e942c694b12c926f3eecb076dff2ade)
passed the complete `bash tools/quality-check.sh` against frozen base
`3a56c444c6fe591f3dda1b84e92be0816baedb7b`. Native verification passed all
three checks and its nine-path scope in 1,408.12 seconds. This includes the
default full continuation sequence: all 65 assertions passed. Manual saving
passed 186 checks, automatic saving 61, cooldown 106 offline assertions and
all 14 adversarial probes held. Existing-lead personal review approved the
exact candidate; no new independent AI-lab review or model call is claimed.

The full gate used an unprivileged private user/mount namespace and a temporary
RAM filesystem inside the workspace for test fixtures. Source, configuration
and receipts stayed on the normal workspace filesystem. Commands, assertions
and required runtime deadlines were unchanged. This is supported-filesystem
acceptance, not a claim that Windows-mounted Git operations became faster.

Exact installer, source archive, legal files and checksums are prepared privately.
Isolated upgrades from the published legacy 0.4.0 and Unio 0.5.3 preserved
operator configuration; explicit backup restoration passed. Foreign commands
and aliases survived. Installed helper and model guidance matched canonical
source. A separate real Windows-mounted native worker at the exact candidate
saved 236 paths and five commits in 20.131 seconds; inspection confirmed a
complete usable snapshot. An earlier attempt on a packaging branch correctly
refused its unsupported worker identity and remains recorded as a refusal.
The real smoke does not establish timing for every tree or automatic save.

Genuine subscription-limit-to-restart acceptance remains **not run**. Neither
the offline cooldown checks nor the earlier real metadata probe proves that
cycle. On 2026-10-09 the owner explicitly approved publication and installation
without waiting for a genuine limit. The release discloses that limitation;
lead cooldown remains disabled until explicitly enabled. The original failed gates and private
diagnostic outcomes retain their actual results.

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
| Authorized continuation | Earlier case/overall timeout failures retained; focused remaining phase passed 31 assertions; corrected exact candidate's default full sequence passed all 65 assertions |
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
lead moved main during validation. That failure is retained. The focused remaining-phase check kept main frozen and passed 31 assertions,
including interruption cleanup, successful continuation, prompt integrity, clean
recovery and final source/result preservation. Its output explicitly says partial.
Every original assertion remains in the default release invocation.

## Release decision and remaining live validation

The owner chose YOLO delivery on 2026-10-09: ship the tested pre-user release,
disclose unverified behavior and fix demonstrated bugs without waiting hours
for a naturally occurring quota event. This supersedes the earlier local
requirement to observe a genuine limit before publication. It concerns the
lead CLI only; existing worker limit handling stays unchanged.

Final release documentation is the only change after the passed candidate.
An exact Git path/blob/mode comparison verifies that every non-Markdown file,
including installer, runtime helpers, browser assets and all tests, matches the
complete-gate candidate. Final documentation and artifact checks bind that
unchanged runtime evidence to the release. Original failed runs remain failures.

The genuine cycle stays not_run until it actually happens. At a future natural
limit, use an owner terminal after existing Codex workflows exit, preserve real
wait/reset/restarted-exit evidence and follow the [cooldown guide](../LEAD-COOLDOWN.md).
Do not burn allowance, bypass admission or present an offline clock as a real reset.
This follow-up no longer blocks publication or installation.

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

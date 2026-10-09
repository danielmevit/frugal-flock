# Continue Unio

Read the local project's newest coordination log and actual receipts before
starting work. They take precedence over dated examples in the repository.
Check the owner's latest instructions, `unio version`, and `unio policy`;
do not infer current availability from an earlier successful worker run.

## Current public checkpoint — 2026-10-09

[Unio v0.5.6](https://github.com/danielmevit/unio/releases/tag/v0.5.6)
adds installed manual allowance tracking. Its exact release source is
`98036e10c9d664179877a08b62933036fb0142ee`. The complete quality gate
passed in 734.105 seconds; isolated installer and upgrade/backup-restore
checks passed. Release assets bind the exact source with checksums and
provenance. Later documentation-only commits do not rewrite that release.

- v0.5.3: a real browser-to-worker workflow, output/files, work modes and
  native shared-budget workflow admission.
- v0.5.4: manual and automatic recovery saves, separately authorized saved-work
  continuation and experimental, opt-in lead cooldown restart.
- v0.5.5: installed `unio browser`, left-to-right active-first work map,
  task-first cards with local AI identity and muted outcome strips.
- v0.5.6: `unio capacity record`/`show`, shared-budget groups and multiple
  windows, observation age, optional reset time and JSON output.

Capacity readings are manual. Missing, invalid, stale or expired data supplies
no usable allowance; a passed reset does not prove refill. No automatic
provider reading, browser meter or dispatch integration is installed. See
[capacity usage](CAPACITY-READINGS.md) and [quota monitoring](../PROVIDER-QUOTA-MONITORING.md).

Genuine lead subscription-limit-to-restart acceptance remains unobserved.
The owner approved publication with cooldown experimental and explicitly
enabled, without waiting hours to manufacture a usage-limit event. Preserve
that limitation; do not introduce the removed publication hold again.
See [cooldown usage](../LEAD-COOLDOWN.md).

## Next functional work

Read the [roadmap](ROADMAP.md), [consolidated backlog](IMPROVEMENT-BACKLOG.md)
and [version plan](../VERSION-PLAN.md). Finish one bounded feature at a time.

1. Add supported, read-only allowance and readiness adapters with truthful
   Unknown, observation age and reset handling. Auth status and allowance
   are separate: the [help-only inventory](AUTH-READINESS-INVENTORY.md)
   recommends Claude's documented JSON auth command as the smallest auth
   adapter; it has not established safe output fields or exit semantics.
2. Connect checked capacity/readiness evidence to scheduling and explain
   why a worker is idle or a task waits. Existing per-budget admission stays
   authoritative; a manual reading grants no launch or retry permission.
3. Measure mounted-filesystem saving and observation overhead before
   optimizing it. A killed or unstable save helper is not proof of lost
   committed work or of an existing last-good save; inspect actual evidence.

Phone/session pairing, live lead messaging and further UI polish remain
planned. The browser launcher is local by default; it does not provide a
paired remote session. See [mobile session companion](MOBILE-SESSION-COMPANION.md).

## Delegation and delivery

Read [lead routing](LEAD-ROUTING.md), [model effort](MODEL-EFFORT.md),
[task-fit evidence](MODEL-SCOREBOARD.md), [worker escalation](../ai/LEAD-ESCALATION.md)
and [work modes](../WORK-MODES.md).

- The current owner-selected cadence is YOLO/low: focused checks per coherent
  feature, personal lead assessment and the complete gate at release. Reuse
  unchanged passing evidence. Future owners can select another review policy.
- Low tier allows one independent workflow per shared budget, including the
  lead. Do not start an extra Codex worker beside a Codex lead. Independent
  budgets may advance disjoint ready tasks concurrently.
- Available Codex, Claude, Grok and Gemini are main implementation options.
  Choose by checked task fit and current owner availability. The latest batch
  used Opus for implementation, Gemini for a bounded CLI-help inventory and
  verified-free LongCat for a predefined local link audit. Original failures
  and lead corrections are recorded in the scoreboard; no model ranking or
  independent security acceptance follows from these small samples.
- Free OpenCode models remain routine supporting workers. Check current zero
  pricing and pin primary/helper routes before each assignment. No paid-token
  fallback, account creation, billing change or promotion to lead is allowed.
- Start at high or the supported middle; GLM stays high. Escalate supported
  effort only for a concrete difficulty, with max reserved for occasional
  narrow work. A requested level does not prove the effective level.
- Use one Source invocation per task unless the owner explicitly authorizes
  another. Preserve a struggling worker, try one suitable replacement, then
  let the existing lead finish the remaining correction. Do not cycle through
  more sessions on the lead's limited budget.
- Substantial tasks normally get 90 minutes, or up to two hours for heavier
  work. Commit an early coherent checkpoint, preserve reports and inspect
  automatic saves. A snapshot is not a commit or an off-device backup.
- Resume Unio before Source/review and stop it afterward. Keep paths quoted,
  take log timestamps from `date`, and avoid self-matching process patterns.

Publish only completed, meaningfully tested versions under current owner
authorization. Keep published tags and assets immutable, install and exercise
the exact verified artifact, preserve operator configuration and retain a
rollback backup. Never merge or push a designated private lead branch.

Older dated findings and release notes are historical evidence. Start with
this checkpoint, the current backlog and local receipts rather than reviving
their completed work or superseded provider holds.

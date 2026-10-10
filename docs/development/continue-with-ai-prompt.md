# Continue Unio

Read the local project's newest coordination log and actual receipts before
starting work. They take precedence over dated examples in the repository.
Check the owner's latest instructions, `unio version`, and `unio policy`;
do not infer current availability from an earlier successful worker run.

## Current public checkpoint — 2026-10-09

[Unio v0.5.7](https://github.com/danielmevit/unio/releases/tag/v0.5.7)
is published and installed. Exact release source:
`30842abea68c8789bfb86b86460e7b13fe51b026`. The complete unchanged quality
gate passed in 1376.59 seconds; five isolated artifact checks (including
40/40 selftest), upgrade/backup restore and official download checks passed.
The installed engine, capacity runtime, dashboard and browser files match
that release, with operator settings and custom lead templates preserved.
Later commits do not rewrite published tags or assets.

- v0.5.3: browser-to-worker workflow, output/files, work modes and native
  shared-budget workflow admission.
- v0.5.4: manual/automatic saves, separately authorized continuation and
  experimental owner-enabled lead cooldown restart.
- v0.5.5: installed browser launcher and interactive, task-first work map.
- v0.5.6: installed manual capacity readings, age/reset and Unknown handling.
- v0.5.7: managed background dashboard, shared task filters, visible AI agents
  and limits, plus explicit Codex metadata refresh with cached observations.

The browser reads local observations; it never queries a provider. Explicit
`unio capacity refresh codex --group codex` updates the supported Codex reading.
Other account readiness, fleet refresh and dispatch integration remain planned.
Missing, stale or expired readings stay Unknown; a passed reset is not proof
of refill. See [capacity usage](CAPACITY-READINGS.md).

Main also contains optional source-tree [subscription adapters](../integrations/README.md),
not packaged in the v0.5.7 installer. Awaiting a future release, the installer
on main now copies both exact adapter files to `~/.config/unio/lib/adapters`
and adds read-only `unio integrations [--json]` (file metadata only; JSON via
isolated stdlib Python). Its offline test and generator check are wired into
the quality gate, which has not yet been run in full for this addition. Vibe 2.26.1 supports explicitly pinned
GLM 5.3 and Mistral Medium 3.5/high, with 2M/$5 default and 4M/$10 substantial
cumulative task bounds. Both pins were checked against the actual installed
CLI schema offline; nine functional tests passed. A real corrected-wrapper GLM
run saved an early packaging commit, then ended with a connection failure at
1,791,060 cumulative tokens/estimated $2.571018, below its local bounds.
Opus completed the saved implementation, passed four native checks and received
personal lead approval. Packaging is merged alongside the owner's website.
Effective model/effort and remaining monthly allowance stay Unknown.

Perplexity supports one research answer or a selected-file code-proposal packet,
then a separate capable implementation agent reviews, applies and validates.
GLM 5.3, Kimi K3 and the connector's GPT-6 Sol Thinking identifier are pinned;
GPT-6.1 Sol is not exposed in that pin and is not silently aliased. Eleven
offline tests passed. The owner completed manual setup; one account-backed GLM
Thinking trial succeeded in 121 seconds. It returned a plan referencing missing
attachments, so its proposed implementation and claimed tests remain unverified.
The prompt now requests code/tests inline; no attachment is downloaded. This is
one account observation, not proof of another account's access or effective identity.
Use the [manual setup and native proposal workflow](../integrations/PERPLEXITY-WEB.md).
The disabled upstream text tool parser is not enabled as a command executor.

Genuine lead subscription-limit-to-restart acceptance remains unobserved.
The owner approved experimental opt-in publication without waiting hours to
manufacture that event. Do not revive that removed release hold.
See [cooldown usage](../LEAD-COOLDOWN.md).

Local workspace relocation completed 2026-10-09: use
`/mnt/d/Vibe Coding/_vm/unio` (`D:\Vibe Coding\_vm\unio`). All 149 Git
worktrees and refs were preserved and repaired. Historical evidence keeps its
old paths; resolve them through local `coord/WORKSPACE-PATHS.json`. See the
[completed relocation record](WORKSPACE-RENAME.md).

## Project website — 2026-10-10

A one-page Astro site lives in `site/` and publishes to
<https://danielmevit.github.io/unio/> through `.github/workflows/deploy.yml`
on every push to `main` that touches `site/`, the workflow or `CHANGELOG.md`.
The workflow pins its actions to commit SHAs, and only the deploy job may
write to Pages. The page reads its version from the newest `CHANGELOG.md`
heading. Colors are the dashboard's dark theme in `bridge/activity.css`; the
layout follows the owner's game-UI reference (HUD bars, readouts, inverted
selections, bracketed panels) without its accent colors. Fonts are
self-hosted through Fontsource. Lab logos in `site/src/marks.ts` are copied
from the dashboard's MIT-licensed Lobe Icons paths. The hero screenshot shows
stand-in agents named after real tools, so the dashboard draws their logos;
no provider is called. The capture script is local at
`tmp/site-demo/showcase2.sh`. Preview with
`cd site && npm install && npx astro build && npx astro preview`.

## Next functional work

Read the [roadmap](ROADMAP.md), [consolidated backlog](IMPROVEMENT-BACKLOG.md)
and [version plan](../VERSION-PLAN.md). Finish one bounded feature at a time.

1. Finish adapter packaging release checks and one bounded inline-code proposal
   trial on the owner-selected GLM/Kimi routes. Assign actual readiness
   implementation separately; preserve the first incomplete GLM proposal and
   all real failures without a blind retry or separately billed fallback.
2. Add supported, read-only allowance and readiness adapters with truthful
   Unknown, observation age and reset handling. Auth status and allowance
   are separate: the [help-only inventory](AUTH-READINESS-INVENTORY.md)
   recommends Claude's documented JSON auth command as the smallest auth
   adapter; it has not established safe output fields or exit semantics.
3. Connect checked capacity/readiness evidence to scheduling and explain
   why a worker is idle or a task waits. Existing per-budget admission stays
   authoritative; a manual reading grants no launch or retry permission.
4. Measure mounted-filesystem saving and observation overhead before
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
- Available Codex, Claude, Grok, Gemini and explicitly pinned Vibe workers
  are main implementation options.
  Choose by checked task fit and current owner availability. The latest batch
  used Opus for the Perplexity adapter and existing-lead concrete corrections
  after incomplete or invalid worker attempts. Original failures
  and lead corrections are recorded in the scoreboard; no model ranking or
  independent security acceptance follows from these small samples.
- Free OpenCode models remain routine supporting workers. Check current zero
  pricing and pin primary/helper routes before each assignment. No paid-token
  fallback, account creation, billing change or promotion to lead is allowed.
- Start at high or the supported middle; GLM stays high. Escalate supported
  effort only for a concrete difficulty, up to supported xhigh. Never request
  max or ultra; a high-only route stays high. A requested level does not
  prove the effective level.
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

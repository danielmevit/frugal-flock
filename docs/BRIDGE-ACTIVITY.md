# First local bridge slice: read-only Activity

This implements only the first read-only Activity view in [TODO](../TODO.md)
section 4. It uses the existing [watch schema](WATCH-USAGE.md), with original
HTML/CSS/JS and a Python standard-library server. It is a source preview,
not a release, a command-free launcher or a live execution UI.

The owner supplies an enclosing workspace (repo/, coord/, wt/) and an explicit
trusted CLI executable. There is one fixed observation command:
`ENGINE watch --once --json`, with cwd set to the selected workspace's repo/,
stdin closed, a 10-second timeout and no shell. The service serializes
observations and caches each result or failure for one second. It accepts
schema 1 with the expected top-level collection types, omits unexpected
top-level data, and never relays raw stdout/stderr errors. Invalid/nonzero/
timed-out observations return 503 without stale data. The browser polls at
two seconds; failure clears old task/tool/event displays.

Default mode allows only GET of the root, two assets, /api/activity and
the /api/session capability document. The server
binds loopback 127.0.0.1, chooses an unused port by default, checks Host and
any Origin header against its actual origin, supplies no CORS permission,
and sends no-store, nosniff and a same-origin content policy. No route can
select another project, engine, path, command or provider. Non-GET methods
are refused by default. An explicit --enable-plan-drafts option now adds
only protected manual create/read under the [draft contract](PLAN-DRAFTS.md).
There are no dispatch, approval, retry or merge actions.
The fixed engine is trusted local code, not an isolated command sandbox.

## Disposable source build

Installed v0.4.0 continues dogfooding and is not replaced. It cannot observe
with watch. Build a preview CLI under the enclosing workspace's tmp/:

```bash
AGENTTEAM_BIN_DIR=/path/to/frugal-flock/tmp/activity-build/bin \
AGENTTEAM_CONF_DIR=/path/to/frugal-flock/tmp/activity-build/conf \
AGENTTEAM_COMPLETION_DIR=/path/to/frugal-flock/tmp/activity-build/completion \
  bash frugal-flock-install.sh
```

Do not set the temporary install's config override when starting the preview
unless you intentionally want to observe those temporary profiles. The CLI
normally reads the selected project's local profiles first, then existing
native configuration. This local diagnostic reads command strings to check
binary presence; it does not invoke providers or read authentication stores.
See [server usage and checks](../bridge/README.md).

## Evidence and limits

Show recorded process exit, validation and reviewer verdict independently.
Human acceptance/integration and current revision readiness are not inferred.
Free worker locks with recorded running state show completion unknown, with
null exits preserved and detached processes not ruled out. Authentication,
remaining quota and reset time stay unknown. An operator retry epoch is an
operator reminder. A runner limit pattern is an observation, not a confirmed
provider quota report. Old ledger entries need no fabricated start/decision
fields. The preview displays recent events in a disclosure as text.

The server is an observation process, not an atomic transaction across all
coordination files. Production packaging, folder selection, sign-in/setup,
a durable queue and execution operations remain separate tasks. The manual
draft create/read API is an explicit opt-in, with no provider dispatch. The owner
waived the two-person feedback prerequisite on 2026-10-04; no sessions exist.
The next slices use judgment/automated checks while retaining run/quota
approval and truthful evidence. Choose one bounded next task.

## Source checkpoint verification (2026-10-04)

Seven Python stdlib HTTP/observer tests passed: fixed argv/cache, failure
cache clearing, invalid output/timeout, assets/loopback, method/Host/Origin/
path refusal before observation and nonleaking unavailable responses.
The Chromium browser checks passed recorded failure, unknown completion,
escaped task text, refresh without fixture writes, unavailable/recovery,
narrow layout and only same-origin GET requests. JS syntax passed and
screenshots were inspected. Optional browser tooling is kept in workspace
scratch, not a runtime dependency.

A loopback HTTP request using the disposable current-source watch executable
against the real project returned 200. It showed GLM process failed/124 and
validation failed, and Claude process succeeded/0, validation passed and
review approved. All 36 observed coordination-file hashes were unchanged.
The installed v0.4.0 executable and global profile hashes also remained
unchanged. No provider invocation occurred during bridge checks. Receipts
and screenshots stay local under workspace tmp/m2-bridge-20261004/.

## Optional browser opening

The source server accepts --open-browser to request the default browser for
its already-bound loopback origin. It remains off by default. Failed or
missing browser configuration leaves the printed URL available and the
read-only service running; desktop opening happens on a daemon thread so a
slow opener does not delay the service. No real desktop browser is launched
by the automated tests. This convenience does not provide folder selection,
engine/provider installation or sign-in, a packaged launcher, or durable jobs.

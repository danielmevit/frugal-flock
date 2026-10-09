# Unio 0.5.7 — dashboard and AI allowance overview

Start or reuse your local dashboard:

```bash
unio dashboard ensure --open-browser
unio dashboard status
```

Unio prints the actual loopback browser link. The managed dashboard stays
running after the launching terminal exits; `unio dashboard stop` stops that
dashboard. Lead startup instructions request the browser link. An arbitrary
existing lead CLI conversation is not automatically attached or captured.

The visible **AI agents & limits** section shows configured routes, shared
budget groups, registered lead, work mode/tier and native workflow counts.
Allowance windows include remaining percentages, reset estimates, observation
age and source. Missing, invalid, stale and expired values stay Unknown.
A reset time passing does not establish restored allowance or permission to run.

Refresh supported Codex subscription metadata explicitly:

```bash
unio capacity refresh codex --group codex
unio capacity show --provider codex --json
```

Refresh reads account/rate-limit metadata without starting a model turn or
logging in. The browser reads cached local state and never triggers a refresh.
Other routes use manual readings or remain Unknown; authentication and current
readiness are distinct. Existing worker admission, bench and retry rules apply.

Map and list share search, worker, lifecycle and category filters and pagination.
Current work excludes finished history; All states and Finished expose it.
The node detail pane again occupies its own desktop column and stacks on narrow
screens. Categories use whole task tokens rather than incidental substrings.

The [lead handover guide](development/LEAD-CAPACITY-HANDOVER.md) documents conserving
lead allowance and a future temporary acting lead. Automatic role switching is
planned; this release does not implement it.

Validation covers cached provider input bounds, installed payload identity,
managed dashboard lifecycle, read-only limits API and real browser interaction.
The release process runs the complete offline quality gate and isolated artifact
installation/upgrade checks. Exact-source checksums accompany the assets.

[Release and downloads](https://github.com/danielmevit/unio/releases/tag/v0.5.7).

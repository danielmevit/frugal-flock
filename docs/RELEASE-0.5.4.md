# Draft: Unio 0.5.4 — keep your work moving

This is an unpublished release candidate. The official installed release is
still v0.5.3. Do not treat this draft, a branch or offline checks as a published
release or a demonstrated subscription reset.

Unio adds recovery saves around native worker runs, preserves unfinished work
through interruption, and lets a separately authorized task continue from an
explicitly restored checkpoint. Durable claims keep uncertain or completed
launches from silently running again.

An owner-enabled supervisor can wait outside the lead CLI and start it again
after a confirmed allowance cooldown. The first supported adapter is Codex CLI
0.161.0 on Linux/Python 3.11+ with an individual first-party ChatGPT subscription.
The known five-hour fallback is five hours and one minute. Each launch requires
fresh ordinary-usage permission; other CLI versions/routes need verified
adapters. Genuine limit-to-restart acceptance remains required before release.

The local browser adds Light/Dark themes, a responsive radial work map, zoom
and pan, details for every node and small status indicators. Observation has a
bounded configurable deadline; increasing that deadline is not a speed claim.
The browser remains in the source archive, with explicit local startup grants
for execution, output and files. The installer installs the CLI and its helper.

See [work saving](WORK-SAVING.md), [lead cooldown recovery](LEAD-COOLDOWN.md),
[browser startup](../bridge/README.md) and the
[validation findings](development/RECOVERY-ACCEPTANCE-2026-10-08.md).

Publish only the exact versioned source that passes the complete quality gate,
supported genuine cooldown acceptance and artifact/upgrade checks. Preserve
all original failed runs. No new paid-token route, worker retry or release
permission follows from restarting the lead.

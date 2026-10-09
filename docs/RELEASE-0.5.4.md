# Unio 0.5.4 — keep your work moving

[Download Unio 0.5.4](https://github.com/danielmevit/unio/releases/tag/v0.5.4).
This release delivers recovery saves, authorized continuation and the live
work map. Its complete automated quality gate and installer upgrade/restore
checks passed. Lead cooldown restart is experimental; a genuine subscription
limit followed by an automatic restart has not yet been verified.

Unio adds recovery saves around native worker runs, preserves unfinished work
through interruption, and lets a separately authorized task continue from an
explicitly restored checkpoint. Durable claims keep uncertain or completed
launches from silently running again.

An experimental, owner-enabled supervisor can wait outside the lead CLI and start it again
after a confirmed allowance cooldown. The first supported adapter is Codex CLI
0.161.0 on Linux/Python 3.11+ with an individual first-party ChatGPT subscription.
The known five-hour fallback is five hours and one minute. Each launch requires
fresh ordinary-usage permission; other CLI versions/routes need verified
adapters. It is disabled until explicitly enabled. The 106 offline cooldown
assertions and a real metadata-only probe passed; neither proves a genuine
limit-to-restart cycle. The owner approved release with this limitation disclosed.

The local browser adds Light/Dark themes, a responsive radial work map, zoom
and pan, details for every node and small status indicators. Observation has a
bounded configurable deadline; increasing that deadline is not a speed claim.
The browser remains in the source archive, with explicit local startup grants
for execution, output and files. The installer installs the CLI and its helper.

See [work saving](WORK-SAVING.md), [lead cooldown recovery](LEAD-COOLDOWN.md),
[browser startup](../bridge/README.md) and the
[validation findings](development/RECOVERY-ACCEPTANCE-2026-10-08.md).

The release runtime and tests are byte-identical to the candidate that passed
the complete gate; final changes are documentation only. Final source identity,
documentation and asset checks bind that evidence to this release. Earlier
failed runs remain preserved. No new paid-token route or worker retry permission
follows from restarting the lead. The packaged `unio browser` launcher is a
separate later feature and is not included here.

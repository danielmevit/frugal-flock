# Unio 0.5.9 — clearer dashboard and agent fleet

Open the dashboard for your current project:

```bash
unio dashboard ensure --open-browser
```

Use the URL printed by the command. It serves your local project observations;
a separate design preview can show demo data. The managed dashboard runs in the
background until you stop it with `unio dashboard stop`.

The dashboard now starts with a readable task list. Each task shows its agent,
Run/Checks/Review evidence, recorded time and a suggested next step. Copying a
command does not execute it. Work map remains available, and your chosen view
is remembered. The map keeps its zoom, pan, filters and task detail panel.
Agent cards bring tool status, workflow occupancy and allowance readings
together; aliases that genuinely share a budget have a shared allowance card.
A readable activity timeline keeps raw evidence available in a folded section.

These views describe recorded evidence. A successful run does not prove its
checks passed, approval does not prove a merge, and an unknown or stale allowance
does not become usable quota when its reset time passes. Further map grouping
is separate follow-up work.

The optional [Copilot Auto Balance adapter](integrations/GITHUB-COPILOT.md) is
included in `unio integrations`. It uses the native GitHub CLI for bounded text
proposals with local/BYOK models excluded. Balance is automatic routing, not a
fixed model or effort level. Native usage does not establish remaining account
allowance. Setup and authentication remain explicit and manual.

The packaged [agent fleet guide](development/AGENT-FLEET.md), routing and effort
instructions explain how to
assign capable implementation workers, research/proposal routes and routine
helpers while respecting shared subscriptions. Existing operator configuration
is preserved on upgrade. An AI response is still a proposal until inspected and
validated under your chosen work policy.

The owner-built [website](https://danielmevit.github.io/unio/) is preserved.
This release does not add phone pairing or automatic acting-lead handover.
Save-retention reliability and supported worker readiness are the next functional
milestones. Existing experimental lead cooldown behavior is unchanged.

[Release and downloads](https://github.com/danielmevit/unio/releases/tag/v0.5.9).

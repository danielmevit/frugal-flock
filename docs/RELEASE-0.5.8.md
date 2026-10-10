# Unio 0.5.8 — optional subscription adapters

Find the packaged adapters and their setup guides:

```bash
unio integrations
unio integrations --json
```

The standalone installer now includes the exact Vibe and Perplexity adapter
scripts. Discovery reads only local file metadata; it does not load an adapter,
read credentials, log in, contact an AI service or start a model. File presence
does not establish authentication or remaining allowance.

[Mistral Vibe](integrations/MISTRAL-VIBE.md) runs implementation tasks through
Vibe 2.26.1 with explicit GLM 5.3 or Mistral Medium 3.5 pins and high effort.
Task bounds default to 2 million cumulative tokens, $5 estimated and 90 minutes;
larger authorized tasks can select the documented bounds. Estimates do not
measure remaining subscription allowance or authorize overage.

[Perplexity Pro](integrations/PERPLEXITY-WEB.md) supplies one research answer or
a code proposal using selected context. A separate implementation agent checks
the proposal, applies suitable changes and runs the assigned validation.
Prompts request code and tests inline; generated attachments are not downloaded,
and a proposal's claimed test results are not treated as verified.

External tools and sign-in require explicit manual setup. The Perplexity
connector is unofficial and stores a reusable local account credential; read
the setup guide's security section before choosing it. Unio neither installs
that dependency nor copies its token into a project. Both adapters use explicit
aliases and ordinary native workflow admission, including shared-budget slots.
No automatic model fallback is added. Effective server-side identity and
unobserved allowance remain Unknown.

The first genuine GLM Perplexity trial returned useful planning text but referred
to missing code attachments. A Vibe GLM run saved an early packaging commit,
then ended with a connection failure below its local task bounds. Opus completed
that saved implementation. These are individual task observations, not a model
ranking. A separate Kimi proposal delivered both files inline, but its local
fake tests exposed one incorrect fixture; that parser is not included here.
See the [task-fit guide](development/MODEL-SCOREBOARD.md).

The owner-built [project website](https://danielmevit.github.io/unio/) is
preserved. This release adds no remote pairing or automatic lead handover.
The experimental lead cooldown feature retains its existing limitations.

Release preparation includes the complete offline quality gate, copied-installer
checks, isolated installation and upgrade checks, and exact-source asset hashes.
Automatic saves on this development workspace encountered the existing project
retention cap; save retention and mounted-filesystem overhead remain separate
follow-up work. Commit important work early and inspect actual save outcomes.

[Release and downloads](https://github.com/danielmevit/unio/releases/tag/v0.5.8).

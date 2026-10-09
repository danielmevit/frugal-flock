# Use Mistral Vibe as an optional Unio worker

This source-tree adapter runs the owner's installed Vibe 2.26.1 CLI. It supports
GLM 5.3 (`zai-glm-5-3`, AI lab Z.ai) and Mistral Medium 3.5
(`mistral-medium-3-5`, AI lab Mistral). Both use the Mistral transport and share
one subscription budget.

## Where the adapter lives

- Source checkout: `tools/vibe-worker.py`.
- Installed copy: `~/.config/unio/lib/adapters/vibe-worker.py` (or under
  `$UNIO_CONF_DIR`). **Development addition awaiting a future release:** the
  installer on `main` places the exact reviewed bytes there, but the released
  v0.5.7 installer does not. Use the source-checkout path with v0.5.7.

`unio integrations` (or `--json`) shows the installed path and whether the file
is present. It reads only file metadata: it never runs Vibe or the adapter, so
`installed: true` says nothing about sign-in or remaining allowance.

## Configure an explicit worker

Sign in manually through the native Vibe CLI using the intended subscription.
The adapter does not install Vibe, log in, copy credentials, change billing or
select another provider as fallback. It preserves the native HOME/VIBE_HOME
location; process-local model overrides do not change the owner's config files.
The owner remains responsible for selecting a funded native account.

Create an existing private receipts directory, then add shell command lines to
an explicit Unio `agents.conf`. Replace the example paths with your own quoted
absolute paths. TASKFILE supplies the prompt without putting its contents in argv.

```text
vibeglm=python3 '/path/to/repo/tools/vibe-worker.py' --model glm-5-3 --receipt-dir '/path/to/private receipts'
vibe35=python3 '/path/to/repo/tools/vibe-worker.py' --model mistral-medium-3-5 --receipt-dir '/path/to/private receipts'
```

With an installer that packages the adapter, point the same lines at the
installed copy instead, for example
`python3 '/home/you/.config/unio/lib/adapters/vibe-worker.py' --model glm-5-3 ...`.
Both copies are byte-identical; pins, effort and bounds do not change.

The file uses `alias=command`, not TOML worker sections. Make the directory
owner-only (for example `mkdir -m 700 '/path/to/private receipts'`). Map both aliases
to the same shared budget before running them:

```bash
unio account vibeglm mistral
unio account vibe35 mistral
unio resume
UNIO_TIMEOUT=5460 unio run vibeglm-feature TASK-ID
unio stop
unio verify vibeglm-feature TASK-ID
```

Low tier permits one independent workflow in that Mistral group. Different
Mistral, OpenCode and Perplexity accounts remain separate even if they offer the
same GLM model. Follow the current project's invocation, review and acceptance
rules; an adapter's exit zero alone does not establish acceptable code.

## Model pins, effort and task bounds

The exact wire model, full definition, positive prices, one-model wire-name
allowlist, compaction model and utility selections are explicit. Title generation,
experiments, updates, connectors, MCP and subagent calls are disabled. The built-in
auto-approve agent receives only bash/read_file/write_file/edit/grep tools. Worktrees
and these flags provide trusted-host execution, not an operating-system sandbox.

High is explicitly configured. The installed Vibe backend maps medium/high/max
to wire high; this adapter accepts no effort override and never requests max.
Do not promise xhigh or server-proven effective effort on this route. The standing
[effort policy](../development/MODEL-EFFORT.md) permits at most supported xhigh on
other routes. Configuration/export metadata is not server identity evidence.

Ordinary implementation defaults are 2,000,000 cumulative tokens, $5 estimated
price, 120 turns and 90 minutes. Substantial work can explicitly select 4,000,000,
$10, up to 180 turns and 120 minutes. Values must be finite and positive within
those supported bounds. The owner-selected task scope and funded subscription
remain the spending authority; these defaults do not authorize additional charges.

Keep the native Unio deadline above the CLI allowance plus shutdown margin:
5460 seconds for the default, or 7260 for a 7200-second CLI task. An earlier
outer timeout still wins; increasing only --max-tokens cannot extend it.

Token totals include context sent again across steps; they are different from a
model's context window or per-response output budget. A final call can overshoot
Vibe's token/estimated-price threshold. Explicit model prices make its estimate
meaningful, but do not measure remaining included monthly allowance or prevent
subscription overage by themselves. A local token/time/price stop is not provider
exhaustion, and never changes Unio's bench, policy or authentication state.
See [task budgets](../development/TASK-TIME-BUDGETS.md) for planning guidance.

## Receipts and actual outcomes

Each invocation creates a new private run directory beneath the explicit existing
parent. It contains a bounded frozen UTF-8 task copy, native stdout and native export/
journal. Those files can contain task text and session data: keep them private.
The adapter stdout and `receipt.json` contain only allowlisted operational metadata,
never the raw prompt, answer, config, exception or authentication material.

The receipt reports requested/configured model and high effort, actual process
exit, time, task hash and selected bounds. Effective model/effort and remaining
subscription allowance remain Unknown. Native schema-1 usage uses input_tokens,
output_tokens, cached_input_tokens and total_tokens; cost_usd is an estimate.
Missing usage/cost remain null rather than invented zero. Malformed, duplicate or
nonfinite export data cannot establish success. A nonzero native result is preserved;
a missing/invalid export after exit zero makes the adapter fail with exit 2.

Vibe exits 0 when finished, 1 on usage/configuration errors, 2 for infrastructure
failure, and 3 for limits/refusal. Its socket-only exit 4 is preserved if encountered,
though this adapter does not select a socket. Adapter deadline exit is 124; graceful
interruption is 130. The adapter starts one CLI invocation with no replay and sets
Vibe's retry elapsed budget to zero; this does not prove every SDK internal retry
is disabled. Owned process groups are cleaned up on deadline/output overflow.

The initial GLM trial stopped at a local 200k cumulative cap; Medium 3.5 stopped at
600k after producing partial code. These are not subscription-limit observations or
a fair reasoning comparison. Preserve them, use larger task-sized bounds for new
authorized work, and judge models by accepted real task outcomes. A catalog entry
for a newer Mistral model does not establish this account's access or its quality.

## References

- [Mistral subscription billing and usage](https://docs.mistral.ai/admin/billing-usage/subscriptions).
- [Mistral model pricing](https://docs.mistral.ai/inference/pricing).
- [Mistral reasoning controls](https://docs.mistral.ai/studio/conversations/reasoning).
- [Official Vibe source](https://github.com/mistralai/mistral-vibe), matched to installed 2.26.1.

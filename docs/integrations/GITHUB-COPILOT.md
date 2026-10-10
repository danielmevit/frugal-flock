# GitHub Copilot Free / Balanced

The source checkout adds `tools/copilot-worker.py` as a bounded routine
proposal worker. This is unreleased development work; the published 0.5.8
installer includes Vibe and Perplexity, not Copilot. The next installer
packages this helper alongside them without installing or authenticating
any external tool. Follow [the fleet guide](../development/AGENT-FLEET.md)
for assignments and shared budget groups.

## What Balanced selects

On the inspected Copilot CLI 1.0.95, Balanced maps to `--model auto
--auto-tier balance`. It is an automatic routing profile, not a fixed model,
AI lab or reasoning-effort level. GitHub selects eligible models under the
account's plan and policies. The adapter requests medium reasoning for its
routine tasks; acceptance of that setting does not prove effective depth.
No max/ultra request is made. An unsupported version or setting fails rather
than silently changing routes.

The owner reports Copilot Free. Its included allowance is the only authorized
funding; no purchase, upgrade, billing change, paid API or local fallback is
permitted. Remaining allowance stays Unknown until a supported account
reading supplies it. The adapter does not establish the account's plan or
turn a paid account into a Free one.

## Manual setup

Install the official [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli)
if needed. This adapter supports the inspected 1.0.95 executable and opts out
of automatic updates for each call. Sign in directly in your terminal if
needed; do not paste tokens or login output into tasks, chat or Git:

```bash
copilot login
```

Existing native authentication stays in Copilot's own store. Unio does not
copy or print it. A CLI installation or successful login is not evidence of
remaining Free allowance.

From an initialized Unio project, create a private receipt parent and add
an alias to your existing `agents.conf` without replacing its other entries.
For current 0.5.8, point the alias to the reviewed source-checkout helper:

```text
copilot=python3 '/absolute/path/to/unio/tools/copilot-worker.py' --receipt-dir '/absolute/private/copilot-proposals'
```

Once a published release packages Copilot, the helper path can be
`~/.config/unio/lib/adapters/copilot-worker.py` (or under `UNIO_CONF_DIR`).
Keep the receipt parent outside the Git checkout, owned by you and mode0700.
The adapter requires it to exist; it never creates an account or dependency.
Then assign a concrete task using an explicitly prepared worker worktree:

```bash
unio account copilot copilot
unio resume
UNIO_TIMEOUT=960 unio run copilot-docs TASK-ID
unio stop
```

The worker name's prefix selects the `copilot` alias. Its task must contain
the public context needed for the proposal. Prepare the registered worktree
using normal Unio project setup first. All aliases on this GitHub account
share one budget; low tier permits one independent workflow in that group.
Known unmanaged owner sessions also consume allowance even though native
slot counts cannot see them.

## Proposal boundaries

Use Copilot for small documentation drafts, inventories and mechanical
patch proposals initially. A capable implementation agent or the existing
lead checks and applies suitable output in its own worktree, then runs the
assigned checks. Delivery is not acceptance, and generated tests are not
independent proof. This adapter does not execute suggested commands or
apply patches. It cannot establish cross-lab review independence because
Auto does not pin the underlying AI lab.

The wrapper feeds task text through stdin, avoiding large argument limits.
It selects GitHub Auto Balance explicitly, clears inherited local/BYOK route
overrides and supplies an empty provider registry for this invocation.
Native credentials remain in place; local model definitions are not edited.
There is no local model, paid API, alternate account, fleet or automatic
continuation fallback.

Each call uses a new neutral private directory, explicit tool restrictions,
disabled hooks and MCP servers, no remote export/control, custom instructions,
BASH_ENV or experimental mode. Configured plugins or extensions that the
wrapper cannot safely exclude cause refusal. These are execution controls
on a trusted host, not an operating-system sandbox or a guarantee about
upstream GitHub behavior. Review any update before widening compatibility.

## Limits and receipts

Default task deadline is15minutes; up to2hours can be selected for a justified
task. Keep the outer Unio deadline above the adapter's deadline plus shutdown
margin. `--max-ai-credits` defaults to30, the native minimum. This is a soft
session limit, observed after a model response and capable of overshoot;
it neither measures remaining account allowance nor enforces a billing cap.
It does not authorize extra charges. A failed run never starts another route.

Each invocation writes a new private receipt, frozen task and native proposal/
usage output. Preserve the actual exit, configured route, task hash and elapsed
time. Effective model, AI lab, effort and remaining allowance stay Unknown
unless separately supported evidence establishes them. Raw answers, usage and
diagnostics may contain task/session data: keep them private. A native usage
file measures that session's consumption, not the account's remaining quota.
The adapter's stdout contains operational metadata, not raw account settings.

## Trial status

The adapter's focused offline checks and first real bounded routine task are
pending. No Copilot completion, code-quality score or account allowance has
yet been established. Update this section from the original receipt after
the task ends; preserve operational failures without calling them model
quality results.

## References checked 2026-10-10

- [GitHub Auto selection and Balance profile](https://docs.github.com/en/copilot/concepts/models/auto-model-selection).
- [Official plans and CLI programmatic availability](https://github.com/features/copilot/plans).
- [Native CLI command reference and tool controls](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).
- [Provider registry and settings precedence](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference).
- Installed `copilot --help`, `copilot help config`, `copilot help providers`,
  `copilot help billing` and `copilot help limits` for1.0.95. Native help says
  the minimum credit limit is30 and session-wide, with possible overshoot;
  online reference wording differs, so keep the supported version explicit.

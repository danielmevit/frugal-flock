# AI Provider Auth Readiness Inventory

This inventory documents the capabilities of installed AI assistants to verify non-generating authentication status. The goal is to support future readiness adapters without running inference or spending tokens.

> **Data Collection Evidence**: CLI bounded introspection (`--version` and `--help` for auth/status commands) ran on 2026-10-09, local UTC+02:00. No network probes, token reads, or generating commands were executed by this inventory.

## Tool Inventory

### Claude (Claude Code)
- **Version**: `2.1.295 (Claude Code)`
- **Command**: `claude auth status`
- **Output Format**: Documented support for `--json` (default) or `--text`.
- **Exit Semantics**: Unknown/unverified from help text.
- **Safe Fields**: Unknown/unverified (needs inspection of output structure).
- **Limitations**: Sign-in metadata does not prove the next request will authenticate successfully or that quota remains. This project's earlier refresh conflict occurred despite healthy sign-in metadata.

### Codex (codex-cli)
- **Version**: `0.161.0`
- **Command**: `codex login status`
- **Output Format**: Unknown/unverified (no `--json` flag documented for this subcommand).
- **Exit Semantics**: Unknown/unverified.
- **Safe Fields**: Unknown/unverified.
- **Limitations**: `codex doctor` supports `--json` and diagnoses "local Codex installation, config, auth, and runtime", which might be an alternative.

### Antigravity (agy)
- **Version**: `1.3.2`
- **Command**: `Unknown/unverified`
- **Output Format**: Unknown/unverified.
- **Exit Semantics**: Unknown/unverified.
- **Safe Fields**: Unknown/unverified.
- **Limitations**: No top-level `auth`, `login`, or `status` subcommands documented in `agy --help`.

### Grok
- **Version**: `1.0.46 (2765805b9442) [stable]`
- **Command**: `Unknown/unverified`
- **Output Format**: Unknown/unverified.
- **Exit Semantics**: Unknown/unverified.
- **Safe Fields**: Unknown/unverified.
- **Limitations**: Provides `grok login` and `grok logout`, but no dedicated auth status command. `grok doctor` checks terminal/input but doesn't mention auth in its help description.

### OpenCode
- **Version**: `1.18.35`
- **Command**: `opencode auth list` (or `opencode auth ls`)
- **Output Format**: Human-readable output. No documented JSON option.
- **Exit Semantics**: Unknown/unverified.
- **Safe Fields**: Unknown/unverified.
- **Limitations**: Help describes listing providers and credentials. Actual output was not inspected here; do not retain raw output or treat listed credentials as verified provider readiness.

## Adapter Recommendation
**Claude** (`claude auth status --json`) is the recommended smallest supported first adapter. It provides a dedicated status command and explicitly documents `--json` output support natively. This avoids regex parsing of human-readable text output which is brittle.

### Distinctions
When implementing the adapter, keep the following orthogonal states distinct:
- **Binary Presence**: Tool is installed and runnable.
- **Login**: Token/credential is present locally.
- **Readiness**: Whether the intended workflow can run under current permissions, authentication and capacity. Status-command behavior must be verified individually; local sign-in metadata alone does not establish this.
- **Quota / Spend Permission / Reset**: Having valid auth does not guarantee capacity or quota is available for generation. A healthy authstatus is not remaining allowance or restored capacity.

## Commands Executed
- `claude --version`, `claude auth --help`, `claude auth status --help`
- `codex --version`, `codex --help`, `codex doctor --help`, `codex login --help`, `codex login status --help`
- `agy --version`, `agy --help`
- `grok --version`, `grok --help`, `grok login --help`, `grok doctor --help`
- `opencode --version`, `opencode auth --help`, `opencode auth list --help`

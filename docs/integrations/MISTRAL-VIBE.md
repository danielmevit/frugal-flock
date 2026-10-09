# Mistral Vibe Integration

This document describes the optional Mistral Vibe worker adapter for Unio.

## Account & Budget
- **Budget Group**: `antigravity` (for this worker execution).
- **Mistral Allowances**: One Mistral budget in low tier. Distinct from OpenCode/Perplexity GLM budgets.
- **Monthly Allowance**: The user reported allowance is not a live capacity reading. No paygo changes are made. Do not guess 5h/reset limits.
- **Workflow**: One workflow lowtier.
- **Login**: Manual login via native Vibe owner is required.

## Config
Copyable quoted `agents.conf` setup:
```
[worker.vibeglm]
command = "python3 tools/vibe-worker.py --model glm-5-3 --receipt-dir tmp/vibe-receipt"
group = "mistral"

[worker.vibe35]
command = "python3 tools/vibe-worker.py --model mistral-medium-3-5 --receipt-dir tmp/vibe-receipt"
group = "mistral"
```

## Lifecycle
- **Resume/Run/Stop**: Managed through standard `agents.conf` lifecycle.
- **API Levels**: CLI 2.26.1 maps medium/high/max to high, and low to none. Do not promise API max is selectable. High is the default and only guaranteed effective effort.

## Evaluation
- Source/report result vs acceptance: Verify outcomes via the safe receipt in the receipt directory, which excludes credentials/raw responses.

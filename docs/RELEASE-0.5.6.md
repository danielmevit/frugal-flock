# Unio 0.5.6 — manual allowance tracking

Record the remaining allowance you saw, then see how old that reading is:

```bash
unio capacity record --group codex --window five-hour --window-minutes 300 \
    --remaining-percent 42 --observed-at "$(date -Is)"
unio capacity show --group codex
```

Inside an initialized workspace, Unio selects that workspace. Elsewhere,
put `--project PATH` before `record` or `show`. Add `--json` to `show` for a
normalized machine-readable view. Read the [capacity guide](development/CAPACITY-READINGS.md)
for optional reset times, all arguments and storage details.

This is manual tracking. Each shared budget can hold several limit windows.
Missing, invalid, stale or expired readings never supply usable allowance;
a passed reset does not imply refill. Other clients can spend the same budget.
These commands make no provider call and do not change dispatch, retries or
agent availability. Automatic provider readings and browser meters remain planned.

The standalone installer packages the store and CLI independently of the
browser. Copied-installer checks cover project paths with spaces, exact
payload bytes, isolated imports, input refusals and reinstall preservation.
The original 13 browser files are unchanged. Release validation also runs
the complete offline quality gate, isolated installation and upgrade checks;
exact source and checksum evidence accompany the release assets.

Supporting documentation includes a [help-only auth inventory](development/AUTH-READINESS-INVENTORY.md)
and a [local link audit](development/LINK-AUDIT-2026-10-09.md). Neither proves
live provider readiness or validates external web links. Personal lead review
corrected the workers' factual and extreme-input findings before publication.

[Official release and downloads](https://github.com/danielmevit/unio/releases/tag/v0.5.6).

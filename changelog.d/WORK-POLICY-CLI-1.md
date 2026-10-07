# WORK-POLICY-CLI-1 — work-policy command/state slice

Unio 0.5.3 (development source): the visible command/state half of work
modes and subscription tiers. New commands `unio mode [yolo|medium|safe]`,
`unio tier [low|medium|high]`, `unio lead [agent|none]`,
`unio account [agent group]` and `unio policy [--json]` persist exact
typed state in `coord/work-policy.json` (schema 1, missing file means
defaults `medium`/`low`), reject duplicate/unknown keys, unknown schema,
wrong types, invalid enums/labels and symlink/nonregular/hardlinked or
oversized state without resetting it, and write atomically serialized by
`coord/.locks/work-policy.lock`. Invalid or surplus arguments fail before
any write or dispatch. `unio policy --json` reports the state, the
per-group workflow limit (low 1, medium 2, high 4), `capacity` unknown
and `workflow_enforcement` advisory; human output, `unio init`,
`unio status`, help and shell completion expose the same. Fresh lead
templates read `unio policy` before planning, existing custom MASTER.md
files keep their content with one idempotent reference, and `unio init`
installs `coord/docs/WORK-MODES.md`. Released 0.5.2 lacks these switches;
native enforced slots are the next slice. New focused mock suite
`tests/unio-work-policy.py` covers defaults, every enum switch,
persistence, lead/account grouping, invalid arguments and
malformed/unsafe/oversized state in a path with spaces, with no provider
calls.

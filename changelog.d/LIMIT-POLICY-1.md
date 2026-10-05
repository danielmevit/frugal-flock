# LIMIT-POLICY-1 — truthful limit observations without text-driven benching

Unio 0.5.1 (unreleased): a run now counts as failed for the limit helper
only on a nonzero actual exit or the empty-work rule (zero commits against
the base and zero uncommitted files), preserving the real exit in every
receipt, and one normalized final 60-line window (ANSI/control escapes and
carriage returns stripped, never executing log text) drives both the
report display and matching while the raw log is kept. The warning and
ledger wall=1 mean suspected limit language, never a confirmed quota, and
a successful run with work stays wall=0. Worker text never benches an
agent or writes availability/configuration state: UNIO_AUTO_OFF is
accepted for compatibility and has no effect, while explicit unio off/on
remains the operator's control. Help, docs/PROTOCOL.md with its embedded
copy and docs/QUALITY-USAGE.md are updated, and tests/unio-limit-wall.py
replaces the automatic-bench expectations with regressions for genuine
phrases, printed repository text, exit-zero empty work, successful and
failed committed work, ANSI/carriage returns, a phrase 50 lines from the
end, and AUTO_OFF=1 with unchanged availability/config files.

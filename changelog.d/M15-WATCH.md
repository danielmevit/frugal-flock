## M1.5 read-only activity monitor

Add `watch` with human and newline-delimited JSON snapshots, once or on
changes: local runs, recorded verdicts, failures, retry brakes, STOP and
operator limits. Preserve unknown completion for unheld running evidence;
never infer an exit or fresh readiness. No provider/auth/quota probe, raw
log/task content read or coordination mutation. Record run starts and
review decisions in the local ledger. Add focused offline regressions.

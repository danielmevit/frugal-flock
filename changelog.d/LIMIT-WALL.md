## LIMIT-WALL — stop false usage-limit walls on ordinary worker output

Narrow the limit-wall matcher to provider limit phrases (rate limit /
rate-limited, usage limit, limit reached/exceeded, quota
exceeded/exhausted/exceeded your quota, too many requests, resets at/in);
the bare word `quota` no longer matches, so worker prose like "the
preceding quota question is superseded" cannot wall a run. A run that
exits 0 never records wall=1, never warns and is never benched whatever
its output says, so the task-text exemption is removed. Only a failed
run whose log tail matches the narrowed phrases records wall=1, warns,
and with AGENTTEAM_AUTO_OFF=1 benches the agent for 5h. Add
tests/frugal-flock-limit-wall.py to the quality checks alongside the
loop brake and bridge job store tests.

## M1.5 task loop brake

After two unsuccessful tracked attempts on a task ID, refuse another worker
invocation before calling the configured provider, across workers. Count
nonzero exits, failed/incomplete validation and interrupted starts once per
attempt. The owner can grant one more invocation with `allow-retry TASK`;
grants do not accumulate or erase history. Malformed/symlink state fails
closed. Tracking starts with this source version; installed releases and
historical reports are unchanged. Add mock refusal and concurrency checks.

# Continue one authorized task from restored work

- Add `unio save continue SAVE_ID DESTINATION NEW_TASK` for a separately
  authorized task whose destination already exactly matches its saved state.
- Bind one durable claim to the save, worker, full new-task hash and fingerprint;
  block replay after completion, refusal, interruption or uncertain launch.
- Preserve native STOP, account/tier admission, retry limits, actual exits,
  automatic saves and optional fresh verification with one worker lock. Skip
  auto-sync only for continuation to keep recovered commits and edits intact.
- Add offline lifecycle and authority checks. Recovery remains unverified and
  grants no inherited review, acceptance or extra invocation.

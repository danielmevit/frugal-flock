# Finish the local workspace rename

Owner request recorded 2026-10-09T22:05:58+02:00: after the current release and integration batch
is finished, rename the enclosing legacy workspace from `frugal-flock` to `unio`.
The intended local destination is `D:\Vibe Coding\_vm\unio` on Windows,
or `/mnt/d/Vibe Coding/_vm/unio` in WSL. Keep `repo/`, `wt/`, `coord/`, `tmp/`
and `artifacts/` together. The public project is already named Unio.

This is scheduled work, not a claim that the directory has moved. Complete the
current release gate, artifact/install checks and active worker/controller jobs
first. Do not move a live process's checkout or mutate frozen run paths.

The lead will inventory active dashboard/supervisor processes and worktrees,
retain rollback information, refuse an occupied destination, and move the entire
workspace together. Stop only its identified managed dashboard before the move;
preserve unrelated AI CLI sessions and processes. Reopen from the new location,
run Git worktree repair and check every registered worktree and branch. Update
current configuration, entry instructions and future wrapper paths. Keep historical
receipts and logs truthful rather than rewriting their original paths. Old frozen
wrappers are historical evidence; create new configurations for future tasks.

Verify `unio doctor`, policy/status and read-only dashboard startup from the new
project path. Confirm all files, branches, saved work and custom operator settings
are preserved, then report the actual new folder and browser URL. Installed CLIs
and native credential stores remain in their supported system locations.

Current release and adapter state belongs in the newest continuation document
and workspace coordination log; this relocation must not delay a finished release.

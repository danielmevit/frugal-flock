# Local workspace rename — completed

Completed 2026-10-09T23:09:23+02:00: the workspace now lives at
`D:\Vibe Coding\_vm\unio`, or `/mnt/d/Vibe Coding/_vm/unio` in WSL.
All 149 registered Git worktrees were repaired and checked against their exact
previous HEADs and common Git directory; all branch and tag refs were preserved.
The same directory was renamed, with no copying or removal of saved work.
Current entry instructions and the lead checkpoint helper use the new path.

The initial Linux/DrvFS rename was refused with permission error 13. Its receipt
is preserved. A bounded Windows-native rename succeeded after native workflows
were idle, STOP was set and idle coordination handles were closed. Only the
identified legacy preview was stopped; unrelated AI CLI sessions were preserved.

Historical logs, receipts and frozen run configurations retain their original
paths. The local `coord/WORKSPACE-PATHS.json` maps the old prefix to the new one
when locating evidence. Create fresh per-run configurations for new tasks;
do not rerun an old wrapper by changing its historical receipt. Native installed
CLIs and credential stores remain in their supported system locations.

## Original request and relocation procedure

Owner request recorded 2026-10-09T22:05:58+02:00: after the current release and integration batch
is finished, rename the enclosing legacy workspace from `frugal-flock` to `unio`.
The intended local destination is `D:\Vibe Coding\_vm\unio` on Windows,
or `/mnt/d/Vibe Coding/_vm/unio` in WSL. Keep `repo/`, `wt/`, `coord/`, `tmp/`
and `artifacts/` together. The public project is already named Unio.

The relocation is complete as recorded above. The procedure followed was to complete the
current release gate, artifact/install checks and active worker/controller jobs
first. Do not move a live process's checkout or mutate frozen run paths.

Before any future relocation, inventory active dashboard/supervisor processes and worktrees,
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

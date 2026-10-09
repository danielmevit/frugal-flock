# Standalone browser launcher

Frozen 2026-10-09 for `BROWSER-LAUNCHER-1`, the first everyday-launch slice.
This is separate development after the frozen v0.5.4 recovery candidate.
No later version is assigned or published by this contract.

`unio browser` starts the existing local dashboard using packaged files,
without a source checkout or a manually assembled Python command. Infer the
enclosing workspace from its repo, worker or subdirectory, or accept an
explicit `--project` from outside. Print the selected project, CLI version,
engine and configuration plus the actual loopback URL.

The invoked CLI's resolved executable is fixed for observation and execution;
the installed launcher does not expose `--engine`. Resolve its configuration
before the observer changes directories. Keep the source server's explicit
engine option for developers. Use one shared server parser/validation path;
packaging does not relax grants or duplicate execution policy.

Default launch is read-only, makes no model calls, writes no project state
and never changes STOP or lead/account policy. Browser opening is opt-in.
Preserve all existing explicit draft/execution/output/files flags and required
startup inputs. Existing loopback, Host, Origin and token checks remain.
No UI redesign, cache optimization, background service or automatic startup.

The standalone installer carries exactly the canonical thirteen browser
modules/assets. A deterministic embed tool and full-gate parity check prevent
source/install drift. No download or extra dependency; Python 3.9+ is required
to launch. Check generated destination types before replacement; refuse
symlinked directories/files and hardlinked payload files. Preserve owner
configuration, bench state, playbooks and unrelated files on reinstall.

Verify installed standalone bytes, actual loopback HTTP/assets/activity,
inferred/explicit project paths containing spaces, explicit manual drafts,
fixed engine/config despite a PATH decoy, startup refusal and preservation.
Reuse existing server checks, personal review and focused native validation
under YOLO. Keep the earlier recovery candidate/assets/evidence frozen; this
feature branch waits for that release boundary before main integration.

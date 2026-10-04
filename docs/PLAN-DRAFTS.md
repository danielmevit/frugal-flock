# Manual plan drafts: first control foundation

The owner waived the two-person feedback prerequisite on 2026-10-04;
proceed with judgment/automated checks. This small slice implements only
storage for a manually entered draft, before the protected HTTP/UI step.
The current Activity service remains read-only. No provider quota is used.

PlanStore in bridge/plan_store.py takes one real enclosing workspace and
creates coord/ui-plans/. It creates and reads immutable schema-1 records:
opaque random ID, UTC creation time, state draft and literal request text
(1 through 4000 characters, not entirely whitespace). The caller receives
a SHA-256 of the saved bytes; this identifies content and is not approval.
Requests may contain newlines or shell-looking text; they are stored as
JSON data only. This slice cannot compile native task orders, execute checks,
generate a plan with an AI, approve work, start jobs or call providers.

Creation writes a private temporary file, flushes/fsyncs it, publishes via
an exclusive hard link, removes the temporary name and fsyncs the directory.
Existing records cannot be overwritten. If the process stops before publication,
an unfinished temporary file is not a plan and is left for a future explicit
cleanup step. Store reopening preserves records and hashes; it does not resume
any work. Atomic publication and fsync require a supported local filesystem.
A failed operation must not be reported as a saved draft.

Directory-relative file descriptors and no-follow flags prevent selecting
another path through the record ID or symlinked coord/storage/record paths.
Reads are bounded at 64 KiB and refuse nonregular files (including FIFOs),
malformed JSON, unknown schemas/fields, mismatched IDs or forged approved
state. Requested directory/file modes are 0700/0600; actual native filesystem
permissions still govern local account access. The trusted-host boundary
remains; worktrees and storage directories are not an OS sandbox.

Eight workspace-local checks passed on 2026-10-05: restart and literal
Unicode/request preservation, invalid inputs/IDs, collision no-overwrite,
corrupt/forged records, symlink/FIFO refusal, symlink directory refusal and
20 concurrent unique complete creations. No real-project draft was created;
checks wrote only disposable workspace tmp fixtures. Receipts stay local
under tmp/bridge-plan-drafts/receipts/. The routine quality gate includes
the stdlib store suite, with no new runtime dependency or global install.

## One next task: protected create/read API

Add only explicit opt-in manual-draft mode to the existing loopback preview.
Default mode stays read-only. A same-origin session token and exact Origin/
Host checks must protect create; reject wrong methods/types, oversized body,
unknown fields and caller-selected filesystem paths. The configured project
is fixed by startup. GET of a validated opaque ID returns that draft/hash.
The UI must call it a manual draft, state where it is saved, and make clear
that saving does not start an AI or consume provider quota.

No approve/start/retry/merge endpoint belongs in that task. Native task
compilation must later prevent user text from becoming Allowed scope or
Validate lines. Durable job execution must separately freeze task/revision,
require explicit provider approval, preserve native exit/result dimensions,
and recover unknown completion without automatic duplicate dispatch.

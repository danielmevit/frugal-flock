# Manual plan drafts: first control foundation

The owner waived the two-person feedback prerequisite on 2026-10-04;
proceed with judgment/automated checks. This small slice implements only
storage for a manually entered draft, now with a protected opt-in HTTP API.
Default Activity mode remains read-only; opt-in mode now has a manual
browser form.
No provider quota is used.

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

## Protected opt-in create/read API (2026-10-05)

The procedure below describes current Unio source and its `X-Unio-Session`
header, renamed consistently in slice D across the server, browser client
and API tests. The historical and rename-verification results have separate
subsections after the current procedure.

Start the server with --enable-plan-drafts to enable only manual-draft
storage in the fixed startup project. Default startup neither constructs
PlanStore nor creates its directory. GET /api/session returns schema 1,
manual_drafts true/false and a random token only in enabled mode. Host must
match the bound address; any Origin must match. No CORS permission is given.

POST /api/plans requires an exact same-origin Origin and one matching
X-Unio-Session header. It accepts only application/json with one
request field, explicit nonambiguous Content-Length at most 32 KiB, no
Transfer-Encoding, valid UTF-8/JSON and no duplicate JSON fields. Body reads
have a five-second deadline. A complete valid save returns 201 and the
immutable draft/hash. Unknown keys, invalid types, whitespace/overlong
requests, path selectors or partial bodies fail without saving a record.

GET /api/plans/ID requires the token and a validated opaque ID. Missing
records return 404; corrupted/unavailable storage returns 503 with no raw
paths, request contents or forged approvals. Restart rotates session tokens;
saved drafts remain readable using the new token. HTTP responses are no-store.
There is no automatic request retry, AI generation, approval, job, native task
publication, provider dispatch or merge endpoint. Saving is not quota approval.

### Historical API verification before the Unio rename

The following earlier 2026-10-05 measurements used the legacy
`X-Frugal-Flock-Session` header. They describe the original API build, not
the current procedure printed above.

Eight HTTP API checks passed: save/read/reopen as literal data, default
read-only, Origin/Host/session refusal, JSON/type/size/duplicate-field rejection,
body framing/missing length/premature EOF, method/path/ID refusal, nonleaking
storage failures/corruption and old token refusal. Eleven existing HTTP/
observer/browser-opening cases passed. The default Chromium journey passed
and confirmed no draft directory creation. An actual opt-in CLI restart
saved one draft, reopened identical content/hash and refused the previous
token. All API test writes were workspace-local fixtures; no real-project
plan or provider call. Receipts: workspace tmp/bridge-plan-api/receipts/.

### Unio rename verification (2026-10-05)

The later slice D candidate bf2ffb1 uses `X-Unio-Session`. Its four stdlib
bridge suites passed (15 server, 8 plan-store, 8 API and 15 job-store tests),
as did the Node scenario suite and all three existing Chromium journeys:
prototype, read-only Activity and manual drafts. These are the rename
checks; no new production plan, provider call or earlier CLI-restart claim
is inferred. Receipts: workspace tmp/rename-unio/receipts/.

## Manual browser form (2026-10-05)

The form appears only when /api/session says manual drafts are enabled.
Saving displays literal text and a disclosed ID/hash, with explicit wording
that no AI planning, worker start or quota approval occurs. Reopen reads by
validated ID. The URL fragment holds only the last saved/read opaque ID;
a page reload fetches a new in-memory session token and safely reads that
record. No token or request text is put in the URL or browser local storage.

Empty/whitespace input is rejected. A shared busy guard stops duplicate
submission. Session refusal refreshes the capability/token and asks the user
to explicitly try again; a disabled capability hides the form and restores
the read-only notice. Failed/unknown saves preserve typed text in the page
and never automatically repeat POST. That text is not a durable backup:
refreshing before a confirmed save may lose it. Missing/unavailable reads
hide the old result instead of claiming a current draft.

Both Chromium journeys passed: default read-only/no draft directory and
opt-in create/reopen/reload, duplicate submission, escaped literal text,
missing ID, stale session, unknown save with no retry, explicit resave,
mode disable, mobile layout and no external requests/page errors. Eleven
HTTP/asset/observer/opening cases passed, plus JS/Python syntax and docs
checks. Screenshots were inspected; fixtures and receipts remain local
under workspace tmp/bridge-plan-ui/. No provider call or actual-project draft
was created. Native runtime and global profile hashes remained unchanged.

## One next task

Prepare one tiny installed-release dogfood code enhancement with exact
workspace-local tool paths and a narrow file scope. Ask fresh provider quota
before any native worker launch; the previous approved worker calls are used.
Root reviews here with no paid reviewer and preserves native failure evidence.

Native task compilation must later prevent user text from becoming Allowed
scope or Validate lines. Durable job execution must separately freeze task/
revision, require explicit provider approval, preserve native exit/result
states and recover unknown completion without automatic duplicate dispatch.
The current UI has no plan generation, approve/start/retry/merge operation.

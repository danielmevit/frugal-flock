# Work-saving implementation contract

Planned for v0.5.4. No runtime or release is delivered by this document.
Root's contract amendment follows review of the preserved Grok b2d1cd5 draft
and Gemini562de04 concise draft. Both original outcomes remain unchanged.

Unio saves actual unfinished files without asking an AI to write a final
answer. A later recovery restores those bytes into a separate idle worker.
A save is private, local and unverified; it grants no acceptance or retry.
The source worker, its failed result and its existing branch remain intact.

## Delivery boundaries

1. Capture/inspect/restore: one Python standard-library helper embedded in
   the installer, commands/help/completion, focused offline acceptance checks.
2. Native baseline/periodic/final saving and one authorized continuation,
   dependent on this format. Existing worker limit/bench/retry behavior stays.
3. Lead cooldown supervisor after saving works; its separate contract controls
   restart evidence and waiting. No quota adapter or rerouting in slices1–2.

Use current installed controls and owner-selected work/review policy. No new
package, API call, automatic merge, billing change or stronger permissions.
The version moves to0.5.4 only for the completed combined release.

## Commands and authority

| Command | Result |
| --- | --- |
| `unio save create WORKER TASK` | Publish a complete manual save or refuse |
| `unio save inspect SAVE_ID [--json]` | Validate and describe a save without mutation |
| `unio save inspect --worker WORKER [--json]` | Last good save and separate latest attempt |
| `unio save restore SAVE_ID DESTINATION` | Restore into another clean idle owned worker |
| `unio save continue SAVE_ID DESTINATION NEW_TASK` | Slice2: one explicitly authorized new run |

Create/inspect/restore make zero provider calls and work while STOP is set.
Continue respects STOP, native budget admission, existing retry/limit policy
and the frozen new task. Unknown outcomes never authorize another call.
Arguments use native worker/task ID validation; save/claim IDs are generated
32-character lowercase hexadecimal. No caller-supplied filesystem path.
Success exits0; known failure/refusal1; bad arguments, busy locks or unknown
partial mutation2. Human output is short; JSON stdout is one bounded object.
The provider's actual exit remains the continuation command's exit.

## Stored state and format

Private root: `coord/saves/`0700, owned by the current user. Each published
save is `SAVE_ID/manifest.json`, `context/task.md`, `pool/SHA256` and optional
`bundle`. Files0600; directories0700. No symlinks/hardlinks/extra files.
Use UTF-8 JSON, reject duplicate/unknown keys and wrong types. Schema1 is
strict; unsupported versions refuse. Content hashes are SHA256, not Git OIDs.
Git OIDs match the recorded sha1/sha256 object format and full lowercase length.

Manifest keys (all required; null permitted only where stated):

| Key | Exact meaning |
| --- | --- |
| `schema_version` | Integer1 |
| `status`, `content_complete` | Literal `complete`, boolean true |
| `save_id`, `worker`, `task` | Bound native identities |
| `run_id` | Real native attempt identity or null; never invented |
| `reason` | `manual`, `baseline`, `periodic`, `final`, `final-failure` |
| `provider_exit` | Null for manual/baseline/periodic;0 for final; nonzero for final-failure |
| `observed_at`, `published_at` | Tool-generated timezone-qualified timestamps |
| `fingerprint` | SHA256 of canonical state described below |
| `git` | Exact Git object described below |
| `entries` | Sorted complete supported path inventory described below |
| `context` | Exactly task SHA256, byte count and `literal:true` |

Git object keys: `object_format`, `base_commit`, `head_commit`, `head_tree`,
`commit_ids`, `bundle_sha256`, `bundle_bytes`. Base is the actual frozen task
base when available, otherwise the observed native coord/base commit, with
that choice recorded in the attempt evidence. Base must be ancestor of HEAD.
Commit IDs are the complete topological BASE..HEAD range, including merges.
HEAD==base means empty commits, null bundle hash and0bytes; otherwise bundle
has exactly HEAD and that base prerequisite, verified before publication.
Scan every carried commit tree, including a secret file later deleted.
Do not copy raw Git internals or unrelated history. Restore requires that base
already exists; do not fetch it from the network or invent another base.

Each entry has exactly `path`, `index`, `worktree`:

- Path is relative UTF-8, unique and sorted; no absolute/dot/dotdot/.git
  components, controls, backslashes or leading-hyphen components. Max1024bytes
  per path/255per component; reject ASCII-case collisions for portability.
- Index is null (absent) or exactly `{mode,oid,sha256,bytes}`. Modes100644 or
  100755, stage0 only. Store exact index blob bytes in pool, including empty.
- Worktree is null (absent) or exactly `{mode,sha256,bytes}`. Mode is actual
  ordinary POSIX permission bits, without setuid/setgid/sticky; pool has exact
  file bytes. Git index modes and disk permissions are preserved separately.

Inventory covers union of HEAD paths, every index path and every supported
nonignored worktree file. Absence explicitly represents staged/unstaged deletes;
index/worktree separation preserves different staged and unstaged bytes. Nonignored
untracked files have null index. Renames need no special encoding. Every referenced
pool file exists and matches hash/length; every pool file is referenced. Empty
bytes remain an actual blob, not absent. Fingerprint is SHA256 of canonical
JSON of git state excluding bundle hash/length, entries and context. It excludes
save ID/timestamps/reason/exit/run ID so unchanged state can be detected.

Refuse unmerged, sparse, assume-unchanged, skip-worktree and intent-to-add indexes;
missing blobs, nested repos/gitlinks, symlinks, hardlinks and other nonregular
required files. Explicitly report unsupported state rather than silently omit it.
Ignored untracked caches and native ignored role cards are omitted; tracked files
remain required even if ignored. Apply exclusions before reading ignored bodies.
Secret-name refusal includes ignored `.env` paths, id_rsa/id_ed25519/id_ecdsa,
private-key pem/p12/pfx files and credentials/secrets json/yaml/yml/toml/txt names,
using the native init pattern case-insensitively. Scan HEAD/index/current files
and all bundled history. `UNIO_ALLOW_SECRETS` never relaxes save rules. Filename
checks cannot prove ordinary source/task text contains no secret.

Bounds:4000entries,100commits,4MiB per body,32MiB total unique pool+bundle,
1MiB task context,1MiB manifest,64MiB total observation reads. Enforce numeric
bounds while streaming, not after unbounded buffering. Git subprocesses use
bounded output/deadlines and exact owned-process cleanup. A capture has a30s
maximum; exceeding it refuses and never extends an AI provider deadline.

## Capture, publication and retention

Use sanitized argv-only Git calls with no credential/network fallback. Clear
caller GIT_DIR/WORK_TREE/INDEX_FILE/OBJECT_DIRECTORY/ALTERNATE_OBJECT_DIRECTORIES/
COMMON_DIR/NAMESPACE overrides, disable prompts and hooks for helper invocations;
do not write those settings into repository config. Confirm owned worker root,
branch and common repository; no-follow regular-file reads throughout.

Make two full bounded observations: paths, index/flags, HEAD/base, task bytes,
file bytes/modes and content hashes. Any detected change refuses `unstable`.
This checks repeated observations; it is not an atomic filesystem snapshot.
Stage under `.staging-SAVE_ID/`, write content then manifest, fsync files and
directories, verify content, then atomic rename and fsync parent. Only a valid
fully published directory counts as a save. Failed or interrupted publication
leaves the prior good save. A post-rename crash is discoverable without a second
pointer. Clean only tool-owned abandoned staging under the saves lock.

Keep latest5 unreferenced saves per worker; claims pin their saves. Hard caps8
per worker and32per project include corrupt evidence; refuse when pinning/corrupt
evidence prevents retention. Evict only older validated unreferenced saves after
new publication is durable. Store a separate latest attempt per worker atomically,
with actual time/reason/outcome and last-good ID; it contains no file bodies.
Inspect clearly distinguishes last good save from a newer failed/unstable attempt.
Missing live freshness is Unknown, not current or saved. Inspect is read-only.

## Locks, restore and failure evidence

Shell holds the native worker lock once: source for manual create, destination
for restore/continue. In-run captures inherit existing ownership without
reflocking. The Python helper alone takes `coord/.locks/saves.lock` for bounded
publication/retention/claim updates; never nest that lock or hold it during AI.
Inspect by ID needs no worker lock. Live inspection while busy reports Unknown.
Validate lock/store ownership, file type and private modes; do not repair unsafe
paths by chmod. Source is never opened for writing by restore.

Destination must be a different existing owned Unio worker, idle, clean and on
its own agent/DESTINATION branch at exact base, with the same common repository.
Preflight complete manifest/pool/context/bundle, limits/permissions/paths/index
and ignored-file collisions before any destination mutation. Verify carried
history in private quarantine with trusted existing base objects. No arbitrary
bundle refs/hooks/network. Invalid input leaves destination objects/refs/files
unchanged. Preserve destination native ignored markers/role cards and caches.

Durably reserve a claim binding save, destination, complete preimage and intent.
Mark `mutating` before mutation. Materialize committed HEAD by a verified
fast-forward of only destination branch, rebuild exact full index from stored
blobs, then recreate supported working files/modes and remove required tracked
deletions. Never auto-commit, reset source, clean ignored files or move another
branch. Compare final HEAD/index/bytes/modes to saved fingerprint before success.
A failure either restores the exact destination preimage and records `failed`,
or leaves truthful `unknown` evidence. Crash during mutation stays unknown until
explicit reconciliation proves saved state or preimage. Never automatically retry
restore into an unresolved destination. Extra Git objects after a proven rollback
are unreferenced; report them honestly. Source HEAD/index/files remain unchanged.

Claims are strict schema1 JSON with exact claim/save/worker/task IDs, source
fingerprint, preimage fingerprint, timestamps, state and outcome; no arbitrary
paths or shell. States reserved/mutating/restored/failed/unknown/calling/called.
Create/restore failures do not rewrite Source exit/verification/review/readiness.

## Native supervision and continuation

Slice2 saves baseline before provider spawn, periodic at most once per60s while
state changes, and final after reaping success/failure/timeout/interruption.
No AI answer is required. Save errors leave prior good evidence and actual
provider exit intact; do not kill or bench a worker merely because capture fails.
Timers/helper children close inherited control/worker descriptors and are stopped
and reaped on exit. Save failure is separate from native quality-snapshot failure.

Continue requires an existing separately frozen NEW_TASK, different from the
saved task, with actual scope/checks and current authorization. Saved task bytes
are literal context; never generate new authority from saved Validate text.
Destination must already match the saved fingerprint. Record one durable claim
per save before dispatch, bind NEW_TASK SHA and destination. Claim replay makes
zero calls; calling/unknown never permits another task/destination to replay it.
Enter the native run body with destination lock already held, without nested
public run/verify. Skip autosync only for this continuation so restored edits
survive; ordinary runs retain their behavior. Admission still uses current tiers.
Record calling before the one provider start; after any uncertain launch retain
unknown. Never inherit old checks/acceptance or grant extra retries. Fresh native
checks and the owner's selected review policy govern the continued candidate.

## Focused acceptance

Compare actual committed/staged/unstaged/untracked/deleted/binary/empty/executable
bytes, full index modes and HEAD after restore, including divergent staged versus
working bytes. Prove source immutability and0calls for create/inspect/restore.
Test equal-base/no-bundle; carried secret then deleted; corruption and unsupported
states before destination mutation; concurrent edits; interrupted publication;
last-good retention/pinning; refused/partial restore and exact rollback/Unknown.
Use offline workers for periodic and quota/timeout/signal failures, preserving
actual exits and final saves without final AI text. Continue tests prove explicit
new task/check authority, one call, replay/unknown refusal, STOP/current budget
admission, no autosync loss and no inherited readiness. Full gate at release;
no duplicated broad suites within each Source. Lead restart is a later slice.

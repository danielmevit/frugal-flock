# Unio — Handoff

How to take over **Unio** and keep improving it without re-deriving anything.
Written after the v0.3.x hardening rounds (`D:\Vibe Coding\_vm\unio-docs` — the
orchestration tool that ran the `repos` build with five AI vendors in parallel); point
any model at this file and say: *"You're taking over Unio — read
`docs/HANDOFF.md` and continue."*

---

## 1. What the thing is

Unio turns several AI coding subscriptions (Claude, Codex, Grok, OpenCode/Kimi,
Antigravity) into one coordinated team on a single Ubuntu/WSL machine. One AI is the
**foreman** (plans, writes work orders, verifies); the others are **workers**, each
building in its own git worktree; the **human owner** is the only one who merges.

It is not an AI and contains none. It calls the vendors' official CLIs under their
**subscription logins** — no API keys anywhere, ever. Anything that looks like an
"API" in the docs means the `unio` subcommand surface, nothing more.

Three load-bearing ideas, in the order they matter:

- **Isolation** — one worktree + one `agent/<w>` branch per worker; they physically
  cannot overwrite each other.
- **Receipts over reports** — every run yields the agent's claim *and* the diff.
  `unio verify` is the machine floor of that evidence. Reports lie; a real vendor
  once reported "all tests passed / NEEDS-REVIEW: None" having committed nothing at all.
- **One human gate** — nothing enters the base branch without a human merge.

## 2. Repository layout — what to edit

> **The product is one file.** `unio-install.sh` *embeds* the entire `unio`
> tool (installed to `~/.local/bin/unio`), every template (MASTER/WORKER/TASK/
> SABOTEUR/PROTOCOL), the agents.conf defaults, and bash completion. Editing the
> installed copy at `~/.local/bin/unio` is always wrong — it is overwritten on the
> next install. Edit the installer, re-run it, re-test.

| Path | What it is |
|---|---|
| `unio-install.sh` | **The product.** ~1900 lines: the tool + templates + completion. |
| `docs/PROTOCOL.md` | Normative spec for the AIs. **Duplicated inside the installer** as the template shipped into every project — the two must stay byte-identical. |
| `docs/GUIDEBOOK.md` | The complete manual (also built to `.docx`). `docs/HANDBOOK.md` is its terse twin. |
| `docs/TESTPLAN.md`, `examples/` | The break-it campaign and replayable demos. |
| `tests/unio-probes.sh` | **Adversarial probe suite** — 14 probes, 3 controls. Free to run. |
| `tools/check-docs.sh`, `tools/make-docx.sh` | Doc lint (Word-safe Markdown) and the `.docx` build. |

After any `PROTOCOL.md` edit:

```bash
bash unio-install.sh                                   # rewrite templates
cp ~/.config/unio/templates/PROTOCOL.md docs/PROTOCOL.md
diff ~/.config/unio/templates/PROTOCOL.md docs/PROTOCOL.md   # must be empty
```

## 3. The change loop for Unio itself

Every change to the installer goes through the same four gates. None is optional; each
has caught a real regression.

```bash
bash -n unio-install.sh          # 1. syntax
bash unio-install.sh             # 2. install (never touches your agents.conf)
unio selftest                    # 3. 40 checks, mock agents, ZERO quota
bash tests/unio-probes.sh        # 4. 14 adversarial probes, ZERO quota
./tools/check-docs.sh                 # 5. docs lint (+ --selftest for the linter)
shellcheck -S warning <extracted bin> # 6. keep it at 0 warnings
```

Extract the embedded tool for shellcheck with:

```bash
sed -n '/^cat > "$BIN_DIR\/unio" <<.UNIO_BIN_EOF.$/,/^UNIO_BIN_EOF$/p' \
  unio-install.sh | sed '1d;$d' > /tmp/ab.sh
```

Version lives in `UNIO_VERSION` near the top of the embedded script; the scheme is
`0.x.y`, matching the other projects here.

## 4. Testing philosophy — mock agents, then adversaries

- **`selftest`** rehearses the entire loop (init → run → verify → bench → lock →
  background + kill → sync → review → score) in a throwaway sandbox using *mock agents*:
  `agents.conf` lines that are plain shell scripts. Zero quota, ~15 seconds. Add a check
  here for every bug you fix.
- **`tests/unio-probes.sh`** attacks the machinery: state corruption, concurrency,
  input validation, and above all **whether a worker can cheat the gate**. Keep its three
  *controls* (basic loop, worker lock, id escape) passing — a suite where everything is
  BROKEN is a broken suite, and the controls are what prove otherwise.
- The mock-agent trick is the single most valuable technique in this repo: you can
  simulate a rogue, a liar, a quota wall, or a hung vendor without spending a token.

> Rule learned the hard way: a fix is not done until a probe or selftest check pins it.
> The tamper-detection fix below was itself wrong on the first attempt, and only the
> probe suite caught it.

## 5. What the adversarial rounds actually found

Real defects, listed because the *classes* recur — pattern-match on these when reviewing
new code:

- **Inherited stdin.** A loop reading a file on stdin lets the command it invokes eat the
  remaining lines. It bit `smoke`, then `run`, then `verify` — the same bug three times.
  Every agent/Validate invocation now carries `</dev/null`.
- **Guessing identity from paths.** Hooks detected "is this a worker?" by looking for
  `/worktrees/` in the git dir, which misfired when `repo/` was itself a linked worktree
  and blocked the *owner's* commits. Now each worker worktree carries an
  `.unio-worker` marker and the hooks read that.
- **Enforcement with a hole in it.** `pre-commit`/`pre-push` cannot see `git update-ref`,
  so a worker could move the base branch invisibly. A `reference-transaction` hook closes
  every ref path.
- **The gate's yardstick was writable by the gated party.** A worker could append to its
  own task file and be judged against the widened scope. The task file is now
  fingerprinted **before dispatch**; a mismatch at verify time is a TAMPERED failure.
- **Errors swallowed = false confidence.** `2>/dev/null || true` around the diff meant a
  dangling `coord/base` produced PASS with no evidence. Fail closed.
- **Names that address files must be validated.** `check_id` guards worker and task ids —
  it was missing on agent names, making `unio on ../../x` a file-delete primitive.
  It also now rejects whitespace/control characters, which had allowed forged ledger rows.
- **Wall-clock is not elapsed work.** Durations measured with `date` counted a Windows
  sleep: a ten-minute run logged 38995s and poisoned the scorecard. Timings use a
  monotonic clock; `wall_s` and `suspended` are recorded, and `score` excludes slept-through
  runs.
- **An optional accelerator on the critical path is an outage.** `init` built a CodeGraph
  index inline in each new worktree with its output on `/dev/null`, so six workers meant
  minutes of apparent hang, a stray indexer daemon each, and one dispatch that silently
  never fired. Work that only makes things *faster* must be detached, time-boxed, and
  skipped when the owner never asked for it — a repo with no `.codegraph/` is a decision,
  not an omission.

## 6. The vendor fleet, accounts and quota

`~/.config/unio/agents.conf` is the lego file — one line per agent, each a shell
command invoking that vendor's CLI headless. Re-running the installer never overwrites it.

| Agent | Subscription | Notes |
|---|---|---|
| `claude` | Anthropic (`CLAUDE_CONFIG_DIR="$HOME/.claude"`) | The only one costing Claude quota. |
| `codex` | ChatGPT | Needs `--skip-git-repo-check`; reads stdin, hence the `</dev/null` guard. |
| `grok` | xAI | Fastest of the fleet. |
| `opencode` / `kimi` | OpenCode | `kimi` pins `opencode-go/kimi-k3`; produced the most rigorous saboteur report so far. |
| `antigravity` | Google | **Benched.** Two consecutive failures: a 10.8h hang and a 55m timeout with no output. |

> **Never point `claude` at `~/.claude4`.** That config dir is the human's own
> diagnostics session; using it for worker runs burns the quota they need to supervise
> with. Prefer the non-Claude vendors whenever Claude quota is tight — a saboteur or fix
> task on Codex or Kimi costs nothing from the Anthropic pool.

Vendor outages are routine, not exceptional: a 503 killed a saboteur mid-run. Bench the
agent (`unio off <a> 30m`), reroute the seat, carry on.

## 7. Working conventions that keep the machinery honest

- **Freeze the contract, commit it, `sync`, *then* dispatch.** Workers branched before a
  contract commit build against stale code and fail on missing files. `run` now warns when
  a worker is behind base; `UNIO_AUTO_SYNC=1` fixes it automatically.
- **Task files are machine-enforced in two places**: every `- path` line under
  `## Allowed scope`, and every `$ command` line under `## Validate`. Write them precisely
  or the gate cannot help you.
- **Never leave background runs open overnight** — a sleeping host suspends them.
- **Merge a task before stacking a follow-up on the same worker.** `verify` scope-checks
  the worker's whole branch against base, because that whole diff is what a merge will
  land. So a second task dispatched to a worker whose first task is still unmerged is
  judged against the *union* of both scopes and reports VIOLATION for files the follow-up
  never touched. Either merge first, or write the follow-up's `## Allowed scope` as the
  union. The verdict is not wrong, but it reads as the worker's fault when it is the
  dispatcher's.
- **Saboteur rotation is the quality loop.** `unio sabotage` (no worker) rotates the
  seat; `sabotage --all` runs every vendor for a finished feature. Saboteurs *can* run in
  parallel safely (isolated worktrees) — `--all` is sequential only to protect quota. A
  finding two vendors reach independently is almost certainly real; one they disagree
  about needs adjudication, not a fix.
- **Docs must survive Word conversion** — see `docs/DOC-CONVENTIONS.md`. The rule that
  bites: never leave a bare `<placeholder>` outside backticks; converters delete it
  silently.

## 8. Current state and open threads

- v0.3.x installed; **selftest 40 green, probes 14/14 held, shellcheck 0, docs lint clean.**
- `repos` (`D:\Vibe Coding\_vm\projects`) is the reference project built with it — see its
  own `HANDOFF.md`.
- `myapp` (the scorecard, separate repo) still parses `reports/*.md`; migrating it to read
  `ledger.jsonl` is the natural next real task.

## 9. Handoff prompt (fill in)

> You're taking over **Unio** at `/mnt/d/Vibe Coding/_vm/frugal-flock-docs`. Read
> `docs/HANDOFF.md`, then `docs/PROTOCOL.md` (normative) and `docs/GUIDEBOOK.md` (the
> manual). The product is `unio-install.sh` — never edit the installed copy. Every
> change: `bash -n` → install → `unio selftest` → `bash tests/unio-probes.sh` →
> `./tools/check-docs.sh` → shellcheck at 0 warnings, and pin each fix with a new check.
> Work on `main`; commit with a message that explains the *class* of bug, not just the
> line. Prefer non-Claude vendors for any dispatched work, and never point the `claude`
> agent at `~/.claude4`.

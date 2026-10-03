# Multi-Agent Claude Coding Setup — Review and Build Plan

> Historical research, retained for context. This is not the current product
> plan or a reliable source of current provider pricing, access, or policy.
> In particular, Git worktrees are not a filesystem security sandbox.
> Start with the [current findings index](../docs/RESEARCH-FINDINGS.md),
> [competitor comparison](COMPETITIVE-REVIEW.md), and
> [engine findings](../docs/ENGINE-FINDINGS.md). Reverify time-sensitive
> provider claims against official sources before relying on them.

Reviewed 2026-07-10. Claims verified against current docs and reporting; sources at the bottom. Anything I could not verify is marked.

---

## 1. Verdict

The architecture is sound. The premise is broken.

Everything downstream of "multiple Claude Pro accounts" — worktrees, file-based coordination, master/worker split, Markdown board — is legitimate and close to what Anthropic itself now ships. But the account strategy at the center of your plan is the one part that is (a) the actual ToS risk, (b) economically pointless, and (c) unnecessary, because parallelism in Claude Code is per-session, not per-account.

You aimed your ToS caution at browser automation. Wrong target. The enforcement Anthropic actually runs today is against exactly two things you're planning around:

1. **Multiple consumer accounts operated by one person to multiply usage.** The Usage Policy prohibits creating or managing multiple accounts to evade detection or circumvent platform safeguards, and rotating accounts to dodge limits is a documented ban reason. N Pro accounts logged into Claude Code on one machine, one IP, one payment identity, hammering code in parallel all day is the textbook limit-evasion signature. Manual login through the official binary does not launder this — the accounts, payments, IPs, and usage pattern are the signal, not the client.
2. **Claude subscription auth in third-party tools.** Your "Worker OpenCode (Claude sub)" is dead on arrival. Anthropic deployed server-side client checks on 2026-01-09 ("This credential is only authorized for use with Claude Code") and fully enforced on 2026-04-04. OpenCode removed Claude Pro/Max OAuth from its codebase in March 2026 after Anthropic legal requests. This also covers Cline, RooCode, and even subscription OAuth inside Anthropic's own Agent SDK.

Meanwhile browser automation — the thing you spent a constraint section on — you were never going to do anyway.

### The economics kill it even without the ToS

Anthropic prices Max as a multiple of Pro on purpose: 5 × Pro ($100) = Max 5x ($100), 10 × Pro ($200) = Max 20x ($200). Multi-accounting buys you approximately zero extra usage per dollar and costs you N logins, N emails, N payment methods, and ban exposure. Worse: Pro's Claude Code access is **Sonnet-only — no Opus**. Your design puts the "Lead Engineer" — the one role that most needs the strongest model for planning and review — on the weakest tier. Max gets Opus.

### The capability you want already exists officially

- **Parallelism is per-account, not per-session.** Anthropic's own docs have a page telling you to run parallel Claude Code sessions in git worktrees. One subscription, N simultaneous sessions, shared quota pool.
- **Agent teams** (experimental, in Claude Code now): a lead session spawns teammates — each a *separate full Claude Code instance with its own context window* — coordinated through a shared task list with dependency tracking, rendered in-process or as tmux split panes. This is your Master/Worker-Bee design, built by Anthropic, on one account. Your requirement said "not internal subagents" — agent teams are not subagents; they are peer Claude Code processes, which is what you were trying to fake with separate accounts.
- **Claude Code on the web / `--cloud`**: fire off N parallel tasks that each run on an isolated Anthropic-managed VM against your GitHub repo, on subscription, no extra compute charge.
- **GitHub Actions on subscription**: `claude setup-token` generates an OAuth token (valid ~1 year) that the official `anthropics/claude-code-action` accepts — sanctioned headless automation for Pro/Max, no API key.

So: keep your architecture, delete the multi-account layer, and spend the same money on one Max plan plus (if you want genuinely independent second opinions) one subscription per *other vendor* — that's the legitimate version of "multiple real accounts."

---

## 2. Answers to your 15 questions

1. **Technically feasible with multiple Pro accounts?** Yes, mechanically — separate credential stores per session (e.g. `CLAUDE_CONFIG_DIR`, or separate WSL users) make it work. Feasible ≠ permitted ≠ sensible. See verdict.
2. **Official way to link multiple Claude accounts into one master/worker system?** No account-linking exists for consumer plans. The official multi-agent surfaces are: agent teams, parallel worktree sessions, Claude Code on the web, and Team/Enterprise seats (which are per-person — buying 5 seats for yourself recreates the same evasion problem at a higher price).
3. **ToS/account risk if each account is manually logged in via Claude Code?** Yes. The risk is the multi-account usage pattern itself, not the login method. Bans for limit evasion, account sharing/reselling, and third-party OAuth use are documented and enforcement tightened hard in Jan–Apr 2026. Read the Usage Policy yourself before spending money: https://www.anthropic.com/legal/aup
4. **Fragile parts?** (a) Coordination files living on git branches — updates are invisible across branches until merge, and the board becomes a permanent merge conflict; (b) prompt-level file boundaries — they evaporate under context compaction; (c) role-based worker split (backend/frontend/tests/review) — it's a dependency chain pretending to be parallel work; (d) trusting worker self-reports about tests; (e) LLM-performed merges.
5. **Preventing workers from overwriting each other?** Three hard layers, zero trust in prompts: worktree isolation (can't touch files outside their checkout), a `PreToolUse` hook that mechanically blocks Edit/Write outside the assigned scope, and a CI scope check that fails any PR touching files outside the branch's manifest. Plus single-writer coordination files.
6. **Worktree/branch structure?** Below, §5.
7. **Best file-communication model?** Your model, with two fixes: coordination directory lives *outside the repo* (shared filesystem, all sessions see it live, no git lag, no conflicts), and every file has exactly one writer. With agent teams, the built-in shared task list replaces most of the board.
8. **Should master merge?** No. Master reviews diffs, orders the merge sequence, prepares rebases, writes the integration plan. A human clicks merge, gated by CI. Enforce with branch protection even solo. LLM merge conflict resolution produces silent semantic breakage — the worst failure class there is.
9. **More automation without API keys/browser automation?** Sanctioned paths, in order: agent teams (self-coordinating task list); headless `claude -p "..."` — the official binary on subscription auth, fully scriptable from bash/tmux; hooks (auto-update reports on Stop); `claude setup-token` + `claude-code-action` so @claude on GitHub issues/PRs spawns workers in CI; Claude Code on the web for parallel cloud sessions. Scripting your own local CLI is local tooling, not browser automation — it's fine.
10. **Existing tools?** Yes, this is a crowded space now: **agent teams** (official), **Pane** (runpane.com — open-source desktop agent manager, explicitly built for Windows/WSL, worktree-per-session, agent-agnostic — your mention checks out and it's a strong fit), **claude-squad** (terminal, tmux+worktrees), **Conductor** (Mac only — irrelevant for you), **Crystal** (deprecated Feb 2026 → Nimbalyst), **cmux**. You do not need to build anything.
11. **Safest MVP?** §4, Tier 1.
12. **Best advanced setup?** §4, Tiers 2–3.
13. **Failure cases?** §8.
14. **Guardrails?** §7.
15. **Which tools?** Claude Code + WSL2 + tmux (or Pane) + GitHub + GitHub Actions. Cursor is a single-agent editor — wrong shape. Warp orchestrates via its own bundled credits — excluded by your own constraint. Codex CLI yes, as a second-vendor worker (included in ChatGPT Plus since Feb 2026). Gemini CLI: free individual access **ended 2026-06-18**; it now needs Google AI Pro/Ultra or a Code Assist license (successor: Antigravity CLI) — only add it if you already pay Google.

---

## 3. The honest capacity math

Limits are shared across Claude Code, claude.ai chat, and Cowork, per account:

| Plan | $/mo | Claude Code models | Rough weekly ceiling* |
|---|---|---|---|
| Pro | $20 | Sonnet only | ~40–80 Sonnet hrs |
| Max 5x | $100 | Sonnet + Opus | ~5× Pro |
| Max 20x | $200 | Sonnet + Opus | up to ~480 Sonnet hrs or ~40 Opus hrs |

*Community-measured ranges as of mid-2026; a temporary +50% weekly-limit promotion runs through ~2026-07-13, so current numbers are inflated. Verify on your own usage page.

Three parallel workers burn roughly 3× wall-clock hours; agent teams burn tokens faster than solo sessions by design. A Pro account running a 3-agent team dies in roughly a day or two of real use. **Max 5x is the realistic floor for this workflow; 20x if it's your daily driver.** One quota pool is also *simpler*: no per-account window desync where worker 3 stalls at 80% task completion because its personal 5-hour window reset at a different time.

---

## 4. Recommended architecture, three tiers

### Tier 1 — Safest MVP (start here, this week)

One Max 5x account. Try **agent teams first** — it may make the rest of this document unnecessary:

```bash
# in WSL, in your repo
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude
# then: "Create an agent team: one teammate on the backend task, one on the
#        frontend task. Split panes." (split panes requires tmux)
```

Lead = your master. Teammates = separate Claude Code instances, own contexts, shared task list with dependency tracking (blocked tasks auto-unblock). Known rough edges (it's experimental): in-process teammates don't survive `/resume`, and task status occasionally lags — nudge the lead when a done task looks stuck.

If agent teams feel too raw, fall back to the manual version: **master session + 2 worker sessions** (not 4 — see §6) in worktrees, coordination directory, hooks, CI, you merge. Full setup in §5.

### Tier 2 — Advanced local: independent vendors, not duplicate accounts

If what you actually want from "multiple real accounts" is *independent paid agents that can disagree with each other*, buy across vendors — one subscription each, every login official:

- **Claude Code** (Max) — master + N Claude workers/teammates
- **Codex CLI** (ChatGPT Plus, $20) — worker; included in paid ChatGPT plans since Feb 2026, signs in with ChatGPT account
- **Gemini CLI** — only if you already pay for Google AI Pro/Ultra (free tier ended 2026-06-18)
- **OpenCode — drop it.** No compliant strong backend under your constraints: Claude sub auth is blocked, its native models are per-token.

Orchestrate the panes with **tmux** or **Pane** (agent-agnostic, Windows/WSL-native, worktree-per-session with diff review — closest ready-made match to your spec). Cross-vendor also hedges you against any single vendor's limit window or outage, and a Codex worker reviewing Claude's code catches different bugs than Claude reviewing itself.

### Tier 3 — Most automated (no API keys, no browser automation)

GitHub becomes the task board and the workers become event-driven:

1. `claude setup-token` → store as `CLAUDE_CODE_OAUTH_TOKEN` repo secret (Pro/Max supported, official action).
2. Master session (local, Opus) plans and files one GitHub issue per work package, labeled and scoped.
3. `anthropics/claude-code-action` workflow: @claude mention on an issue → worker runs in CI, opens a PR. Issues = your AGENT_BOARD, PRs = reports, CI = test truth.
4. For long tasks, `claude --cloud` / Claude Code on the web runs parallel sessions on Anthropic-managed VMs against the repo — subscription-covered, no compute charge.
5. You review and merge. Branch protection + required checks enforce it.

Caveat: Actions runtime draws from the same subscription pool, and heavy unattended automation is exactly where you should re-read current limits — capacity policy has changed three times in twelve months (weekly limits Aug 2025, budget doubling May 2026, promo lift July 2026).

---

## 5. Step-by-step setup — Windows + WSL

```bash
# 0. Prereqs (once)
wsl --install -d Ubuntu                     # PowerShell, then reboot into Ubuntu
sudo apt update && sudo apt install -y git tmux jq gh
# install node LTS (nvm recommended), then:
npm install -g @anthropic-ai/claude-code
claude          # log in once with your (one) Max account
gh auth login

# 1. Layout — worktrees as siblings, coordination OUTSIDE git
mkdir -p ~/code/myproj && cd ~/code/myproj
git clone git@github.com:you/myproj.git main
mkdir -p wt coord/reports
cd main
git worktree add ../wt/backend  -b agent/backend
git worktree add ../wt/frontend -b agent/frontend
```

```text
~/code/myproj/
├── main/            # master session; main branch; read-mostly
├── wt/
│   ├── backend/     # worker A; branch agent/backend
│   └── frontend/    # worker B; branch agent/frontend
└── coord/           # NOT in git — live shared memory
    ├── board.md     # written ONLY by master
    ├── decisions.md # written ONLY by master
    ├── blockers.md  # append-only, anyone
    └── reports/
        ├── backend.md   # written ONLY by worker A
        └── frontend.md  # written ONLY by worker B
```

Why coordination lives outside the repo: on branches, each worker sees a *stale snapshot* of the board and their updates are invisible to everyone until merge — then all board files conflict. On the shared filesystem every session reads live state. Git carries code; the filesystem carries chatter. (Worktrees also share one `.git`, so per-worktree git hooks are unreliable — another reason enforcement lives in Claude hooks + CI, not git hooks.)

```bash
# 2. Per-worktree scope enforcement
mkdir -p ~/code/myproj/wt/backend/.claude/hooks
```

`wt/backend/.claude/allowed-paths.txt`:

```text
src/server/**
tests/server/**
coord-link/reports/backend.md
```

`wt/backend/.claude/hooks/scope-guard.sh` (same script every worktree; `chmod +x`):

```bash
#!/usr/bin/env bash
# Blocks Edit/Write outside this worker's assigned scope. PreToolUse hook.
input=$(cat)
path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$path" ] && exit 0
rel=$(realpath -m --relative-to="$CLAUDE_PROJECT_DIR" "$path")
case "$rel" in ../*)
  echo "BLOCKED: $path is outside your worktree." >&2; exit 2;;
esac
while IFS= read -r glob; do
  [ -z "$glob" ] && continue
  case "$rel" in $glob) exit 0;; esac
done < "$CLAUDE_PROJECT_DIR/.claude/allowed-paths.txt"
echo "BLOCKED: $rel is not in your scope (.claude/allowed-paths.txt). If you need it, append a request to blockers.md and stop." >&2
exit 2
```

`wt/backend/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          { "type": "command",
            "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/scope-guard.sh" }
        ]
      }
    ]
  }
}
```

(Enable shell globstar semantics if you want `**` to match nested dirs strictly; the simple `case` match above treats `src/server/**` loosely, which is fine in practice. Check hook JSON fields against current docs — code.claude.com/docs/en/hooks — the schema has evolved.)

```bash
# 3. Symlink coord into each worktree so the agent can reach it,
#    and gitignore the link
ln -s ~/code/myproj/coord ~/code/myproj/wt/backend/coord-link
echo "coord-link" >> ~/code/myproj/wt/backend/.gitignore   # or global gitignore

# 4. CI scope check + branch protection
```

`.github/workflows/scope.yml` (in the repo):

```yaml
name: scope-check
on: pull_request
jobs:
  scope:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: changed files must match branch scope
        run: |
          prefix="${GITHUB_HEAD_REF#agent/}"
          manifest="scopes/${prefix}.txt"
          [ -f "$manifest" ] || { echo "no manifest for $prefix"; exit 1; }
          git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD" | \
          python3 -c '
          import sys, fnmatch
          globs=[l.strip() for l in open(sys.argv[1]) if l.strip()]
          bad=[f for f in sys.stdin.read().split()
               if not any(fnmatch.fnmatch(f,g) for g in globs)]
          if bad: print("OUT OF SCOPE:", *bad, sep="\n  "); sys.exit(1)
          ' "$manifest"
```

Commit `scopes/backend.txt`, `scopes/frontend.txt` mirroring the allowed-paths files. Then on GitHub: protect `main` — require PR, require `scope-check` + tests green. Now a worker *cannot* land an out-of-scope change even if it talks itself past the local hook with `bash sed`.

```bash
# 5. Launch (manual-worktree variant)
tmux new-session -d -s agents -c ~/code/myproj/main -n master 'claude'
tmux new-window  -t agents -n backend  -c ~/code/myproj/wt/backend  'claude'
tmux new-window  -t agents -n frontend -c ~/code/myproj/wt/frontend 'claude'
tmux attach -t agents
```

Or skip tmux and use **Pane** (runpane.com) — it manages exactly this: named sessions, worktree isolation, per-pane branch/port/status, diff review. Or the agent-teams route from §4 Tier 1, which replaces the window juggling entirely.

---

## 6. Fixing your worker split (this matters more than the tooling)

Your split — Backend / Frontend / Tests / Review — is role-based. Roles are a *pipeline*: frontend consumes the backend's API, tests consume both, review consumes everything. Run them in parallel and the frontend worker invents the API shape, the test worker tests code that doesn't exist, and the review worker reviews stale diffs. You'll spend the integration phase reconciling three guesses.

Do this instead:

1. **Contract-first, then fan out.** Master's first job each cycle: freeze the interfaces the tasks share — API schema/types/fixtures — commit them to `main` *before* assigning. Workers build against frozen contracts.
2. **Split by feature, not by layer**, whenever possible. Two workers on two independent features (each owning its slice of backend+frontend+tests) beats four workers on coupled layers.
3. **Tests ship with the feature.** Each worker writes tests for its own task; the task isn't done until its CI is green. A standing "tests worker" only makes sense for dedicated hardening passes (coverage gaps, regression suites) — as an occasional task, not a permanent seat.
4. **Review is a phase, not a worker.** The master (on Opus) reviews PR diffs after work exists. A parallel "review account" idles, then reviews stale code. If you want independent review, that's the Codex-as-second-vendor slot.
5. **Start with 2 workers.** Your real bottleneck is not generation, it's *your* review bandwidth. Four workers producing PRs faster than you can read them is a queue, not a speedup. Scale to 3–4 only after 2 feels limiting.

---

## 7. Guardrails

Durable rules live in each worktree's `CLAUDE.md` — kickoff prompts get compacted away mid-session; `CLAUDE.md` gets reloaded.

Hard (mechanical) guardrails:

- Worktree isolation + scope-guard hook + CI scope check (§5) — three layers, no trust in prompts.
- Single-writer coordination files; `blockers.md` append-only.
- Branch protection on `main`: PR required, CI required, you merge.
- **Dependency ownership**: `package.json`/lockfiles/migrations belong to exactly one designated worker per cycle. Lockfiles are the #1 cross-worker conflict magnet.
- **Port assignments** per worktree (backend dev server 3001, frontend 3002, ...) written into the board — parallel dev servers otherwise fight over ports and agents "fix" it by editing config.
- **Kill switch**: workers must halt when `coord/STOP` exists. `touch coord/STOP` ends a runaway cycle.
- CI is the only accepted test evidence: reports must cite commit SHA + CI run URL, not "tests passed."

Board schema (master-written, one block per task):

```markdown
## T3 · backend · Implement /auth endpoints
state: doing            # todo | doing | blocked | review | done
owner: backend
branch: agent/backend
scope: src/server/auth/**, tests/server/auth/**
contract: openapi.yaml @ a1b2c3d
depends: —
done-when: PR open, CI green, report filed
```

---

## 8. Failure cases to expect

| Failure | Mitigation |
|---|---|
| Account ban / lockout (multi-account evasion pattern) | Don't multi-account Anthropic. One Max + cross-vendor. |
| Worker edits out of scope via shell tricks (`sed`, `mv`) | CI scope check catches what the hook misses; branch protection blocks the merge. |
| Semantic conflicts that merge cleanly (two "compatible" PRs break each other) | Contract-first; merge in dependency order; full CI on `main` after each merge, fix-forward before next merge. |
| Worker claims tests pass; they don't | CI-or-it-didn't-happen. |
| Duplicate helpers (two workers each invent `formatDate`) | Shared `utils/` owned by one worker; master de-dupes in review phase. |
| Context compaction erases the rules | Rules in `CLAUDE.md`, not prompts. |
| Blocker ping-pong deadlock (A waits on B waits on A) | Master heartbeat: check `blockers.md` every cycle; workers stop after writing a blocker instead of improvising. |
| Quota exhaustion mid-sprint | One pooled Max quota (predictable) > N desynced Pro windows; schedule heavy fan-out early in the weekly window; watch the promo expiry ~Jul 13. |
| Agent-teams rough edges (lost teammates on resume, stale task status) | Treat as experimental; keep the manual-worktree fallback; nudge the lead on stuck tasks. |
| Master "helpfully" writes code or merges | Master `CLAUDE.md` forbids source edits; no push rights to `main`; human merges. |

---

## 9. Prompts (revised)

Why yours needed surgery: rules were in the kickoff prompt (compaction deletes them), no contract-freeze step, no stop conditions, "run the relevant tests" is unfalsifiable, and reports lacked commit SHA/CI evidence. Durable rules below go in `CLAUDE.md`; kickoff prompts stay short.

**Worker `CLAUDE.md`** (e.g. `wt/backend/CLAUDE.md`):

```markdown
# Role: Worker "backend"
- Branch agent/backend in this worktree only. Never touch main.
- Scope: only paths in .claude/allowed-paths.txt. Blocked edit? Append the
  need to coord-link/blockers.md and stop that thread of work.
- Coordination: read coord-link/board.md before starting and after each task.
  You write ONLY coord-link/reports/backend.md. blockers.md is append-only.
- Contracts in board tasks are frozen. Never change an interface; blocker it.
- Dependencies: do not edit package.json/lockfiles unless the task grants it.
- Dev server port: 3001.
- Done = task test command green locally, committed, branch pushed, PR opened
  (gh pr create), report filed with: summary, files, commit SHA, CI run URL,
  assumptions, risks, what to review carefully. Then set task state: review.
- Stop conditions: same obstacle twice → blocker + stop. Architecture change
  needed → blocker + stop. coord-link/STOP exists → stop immediately.
```

**Worker kickoff prompt:**

```text
Read CLAUDE.md, then coord-link/board.md. Claim the task owned by "backend"
(set state: doing). Execute it within scope. Follow the done/stop rules.
```

**Master `CLAUDE.md`** (`main/CLAUDE.md`):

```markdown
# Role: Lead engineer (planning, review, integration — NOT implementation)
- You never edit source files. You never merge. Daniel merges.
- You write coord/board.md and coord/decisions.md; you read everything.
- Before assigning dependent tasks: freeze contracts (schemas, types,
  fixtures), commit them to main, reference the SHA in each task.
- Tasks must have disjoint scope globs. Dependency edits (package.json,
  lockfiles, migrations): at most one task per cycle may touch them.
- Board schema: state/owner/branch/scope/contract/depends/done-when.
```

**Master planning kickoff:**

```text
Inspect the repo and coord/board.md. Plan the next cycle for 2 workers
(backend, frontend): freeze any shared contracts first, then write
independent, disjoint-scope tasks to the board per the schema. Flag anything
that cannot be parallelized and propose the sequence instead. Do not
implement anything.
```

**Master integration kickoff:**

```text
Read coord/board.md, coord/reports/*, coord/blockers.md, each open PR diff
and its CI status. Produce coord/integration-plan.md: verify each worker
stayed in scope and CI is green; list conflicts, semantic risks between
branches, duplicated logic, missing tests, unresolved blockers; give a merge
order with rebase steps. Leave concrete review comments per PR. Do not merge.
```

---

## 10. Cross-vendor orchestration: one Claude master driving Gemini, Grok, OpenCode

(Added after Daniel scratched the multi-Claude-account idea in favor of: Claude as the single master, with his existing Gemini, Grok, and OpenCode subscriptions as workers.)

**Verdict: yes, this works, and it's the fully sanctioned version.** The mechanism is simple: every one of these CLIs now ships an official headless mode and authenticates with its own subscription login. To the master Claude session, a worker is just a shell command it runs through its Bash tool — no API keys, no browser automation, no cross-vendor OAuth smuggling.

### Worker status (verified 2026-07-10)

| Worker | Headless invocation | Auth | Notes |
|---|---|---|---|
| Claude Code (master) | interactive session (+ `claude -p` for its own spawns) | your existing sub | Master stays interactive; Opus if Max |
| Gemini CLI | `gemini -p "..."` (add `--yolo` for unattended writes) | cached Google account login, incl. Google AI Pro/Ultra | Official headless docs; JSON output mode |
| Grok Build (xAI) | headless mode supported — check `grok --help` for current flag | browser sign-in with SuperGrok / X Premium+ | Launched 2026-05-25, **early beta** — expect syntax churn, review its output hard |
| OpenCode | `opencode run "..."` | needs a provider: **GitHub Copilot sub** (officially supported by GitHub since 2026-01-16, device-code login) or **OpenCode Go** ($10/mo flat) | Go = 13 open-weight models (Chinese labs, US/EU hosting), $12/5h · $30/wk usage caps. Flat-rate, so it passes your no-per-token rule — but it *is* the "third-party bundled models" thing you excluded in round one, and it's the weakest model tier in this fleet. Your call. Claude sub inside OpenCode remains banned. |

### Wiring

The §5 skeleton carries over unchanged — worktree per worker, coord dir, scope CI. Only the worker processes change. A delegation from the master session looks like:

```bash
# Master Claude runs this via its Bash tool (long runs: background + poll)
cd ~/code/myproj/wt/frontend && \
  gemini --yolo -p "$(cat ../../coord/tasks/T4-frontend.md)" \
  > ../../coord/reports/T4-frontend.out 2>&1
git -C ~/code/myproj/wt/frontend diff --stat   # then review the actual diff
```

Loop: master writes a *self-contained* task spec to `coord/tasks/<id>.md` → runs the worker CLI headless inside that worker's worktree → reads the diff and output → accepts (worker branch → PR) or re-briefs with a sharper spec. Wrap each worker call in a slash command or skill once the pattern stabilizes; MCP wrappers for gemini/codex exist, but raw bash is the lowest-code path you asked for.

Add a delegation policy to the master `CLAUDE.md`:

```markdown
# Delegation policy
- gemini: repo-wide analysis, large-context reads, summarizing unfamiliar
  code, mechanical bulk edits
- grok (Grok Build, beta): isolated features/tests in its own worktree;
  review every diff closely
- opencode (Go models): cheap chores only — lint fixes, doc updates, test
  boilerplate. Never architecture.
- you (Claude): contracts, architecture, hard bugs, all review, integration
- Every delegation: self-contained spec in coord/tasks/<id>.md, worker runs
  headless in its own worktree, you review the diff before anything merges.
```

Ready-made versions of this exact pattern, if you want zero glue code: **Sage** (pure-bash orchestrator, runtime-agnostic across Claude Code/Codex/Gemini/Cline, worktree isolation, headless CI mode) and **the-perfect-orchestrator** (one lead Claude Code session commanding N workers in tmux panes, coordination via plain files). Directory of the whole ecosystem: bradAGI/awesome-cli-coding-agents.

### The honest caveats

**This is fire-and-forget delegation, not puppeteering.** Headless calls are one-shot: the worker gets your spec, does the task, returns text, and forgets everything. There is no standing worker session the master converses with. Tight back-and-forth means re-sending context every call — so task specs must be self-contained work packages (the §7 board schema is exactly that). If a task needs ten rounds of dialogue, it was a Claude task.

**The weakest worker sets your review bill.** Every worker-hour of output costs master-Claude (and you) review time. Gemini on multi-file edits and OpenCode Go's open-weight models produce more rework than Claude; Grok Build is a two-month-old beta. If a worker's acceptance rate is low, delegation is negative-sum — you burn Claude quota reviewing slop instead of writing code. That's why the delegation policy above assigns by strength, not by availability.

**Start with two, measure, then grow.** Claude master + Gemini worker first (it's the most proven pair — Gemini's context window genuinely complements Claude). Add Grok Build once you've seen its diff quality on your codebase. Add OpenCode Go only if chore volume justifies $10/mo. Orchestration overhead is real; more agents ≠ more shipped code.

---

## 11. What I'd do in your position

Today: enable agent teams on your existing account, run one real feature with a lead + 2 teammates in tmux split panes, and see how far the built-in task list gets you. This week: if you outgrow it or want durable process, add the §5 skeleton (worktrees, coord dir, scope guard, CI check) — it composes with agent teams and with manual sessions. When you actually hit quota walls: upgrade to Max 20x before you even think about a second Anthropic account. If you want a genuinely independent second brain: ChatGPT Plus + Codex CLI in one more pane, reviewing Claude's PRs. Total spend $120–220/mo, every login official, nothing to hide.

---

## Sources

Official docs:
- Agent teams: https://code.claude.com/docs/en/agent-teams
- Parallel sessions with worktrees: https://code.claude.com/docs/en/worktrees
- Claude Code on the web: https://code.claude.com/docs/en/claude-code-on-the-web
- GitHub Actions integration: https://code.claude.com/docs/en/github-actions
- claude-code-action setup (OAuth token for Pro/Max): https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md
- Hooks reference (verify schema): https://code.claude.com/docs/en/hooks
- Anthropic Usage Policy (read the multi-account clause yourself): https://www.anthropic.com/legal/aup
- Max plan: https://support.claude.com/en/articles/11049741-what-is-the-max-plan
- Claude Code with Pro/Max: https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan

Third-party OAuth crackdown (Jan–Apr 2026):
- Hacker News: https://news.ycombinator.com/item?id=46549823
- OpenCode removal of Claude auth: https://ridakaddir.com/blog/post/did-anthropic-kill-opencode-claude-subscription-ban
- Enforcement analysis: https://paddo.dev/blog/anthropic-walled-garden-crackdown/

Multi-account risk reporting (secondary — verify against the Usage Policy above):
- https://dev.to/vainamoinen/two-multi-account-claude-code-architectures-one-anthropic-accepts-one-they-ban-2om7
- https://metricnexus.ai/blog/anthropic-banning-multiple-claude-accounts

Limits and pricing (2026 state):
- https://ccforeveryone.com/guides/claude-code-limits-and-pricing
- https://www.truefoundry.com/blog/claude-code-limits-explained
- https://www.explainx.ai/blog/claude-usage-limits-2026-timeline-explained

Tools and vendors:
- Pane (Windows/WSL agent manager): https://runpane.com/claude-code
- claude-squad: https://dev.to/stevengonsalvez/claude-squad-run-multiple-ai-agents-in-parallel-without-the-mess-1hfl
- Crystal → Nimbalyst: https://github.com/stravu/crystal
- Codex CLI (ChatGPT plan sign-in): https://developers.openai.com/codex/cli
- CLI comparison (incl. Gemini free-tier status): https://www.deployhq.com/blog/comparing-claude-code-openai-codex-and-google-gemini-cli-which-ai-coding-assistant-is-right-for-your-deployment-workflow

Cross-vendor orchestration (§10):
- Gemini CLI headless mode: https://google-gemini.github.io/gemini-cli/docs/cli/headless.html
- Gemini CLI auth (Google AI Pro/Ultra login): https://google-gemini.github.io/gemini-cli/docs/get-started/authentication.html
- Grok Build announcement (xAI): https://x.ai/news/grok-build-cli
- Grok Build overview: https://medium.com/@candemir13/grok-build-what-xai-actually-shipped-and-whats-overstated-f98961b0d301
- GitHub Copilot officially supports OpenCode: https://github.blog/changelog/2026-01-16-github-copilot-now-supports-opencode/
- OpenCode Go plan: https://opencode.ai/go
- OpenCode Go review (caps, models): https://www.bitdoze.com/opencode-go-plan/
- Orchestrating CLI agents with Claude Code: https://www.365iwebdesign.co.uk/news/2026/01/29/orchestrate-ai-agents-claude-code/
- Agent swarm guide (Claude+Codex+Gemini): https://www.codeagentswarm.com/en/guides/ai-cli-agent-swarm
- Ecosystem directory (Sage, the-perfect-orchestrator, parallel runners): https://github.com/bradAGI/awesome-cli-coding-agents

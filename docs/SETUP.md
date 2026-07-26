# agentteam — your 5-CLI team on one Ubuntu VM

One master CLI session (default: Claude Code) delegates coding tasks to
worker CLI agents (Codex, Antigravity, OpenCode, Grok Build), each
running headless in its own git worktree under its own subscription login.
No API keys, no browser automation.

Built around Daniel's operating standard (`ai-project-setup-playbook.md` +
`ai-full-build-recipe.md`): dev/main branch model, AGENTS.md router +
docs/ai/, CodeGraph for structure, verified milestones, strict commit
hygiene. v2 tested end-to-end 2026-07-10 (init on a dev-branch repo →
delegate → run → report → diff → off/on quota switch → limit auto-detect →
stop/resume). Headless syntax per CLI verified against official docs the
same day — sources at the bottom.

## Lego principles

- **One agent = one line** in `agents.conf`. Add, remove, or re-tune agents
  without touching anything else.
- **One switch per agent**: `agentteam off codex 5h` when it burns its
  5-hour window, `off codex 7d` for a weekly cap, `on codex` to re-enable.
  Expiries clear themselves; the master reroutes around OFF agents.
- **Master is whoever you launch** in the repo dir — the role card is
  symlinked as CLAUDE.md, AGENTS.md, and GEMINI.md, so any CLI picks it up.
- **Per-project overrides**: `coord/agents.conf` beats the global config;
  `coord/base` sets the integration branch.

## 1. Install (once, on the VM)

```bash
bash agentteam-install.sh
# ~/.local/bin must be on PATH (Ubuntu default; otherwise:)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
agentteam selftest       # rehearse the whole loop with mock agents — no quota
agentteam version        # confirm what's installed
```

Tab-completion (commands, workers, tasks, agents) installs automatically;
open a new shell to pick it up.

## 2. Log in each CLI once (interactive, one time)

Headless runs reuse cached credentials. On a GUI-less VM most logins print
a URL + code you open in the browser on your Windows host.

| Agent | Install | Login | Verify |
|---|---|---|---|
| Claude Code | `npm i -g @anthropic-ai/claude-code` | `claude` | `claude -p "say ok"` |
| Codex | `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` | `codex` → ChatGPT account | `codex exec "say ok"` |
| Antigravity | install per antigravity.google (`agy` binary) | `agy` → Google account (prints URL + code over SSH) | `agy -p "say ok"` |
| OpenCode | `curl -fsSL https://opencode.ai/install \| bash` | `opencode auth login` (Go) or `/connect` (Copilot) | `opencode run "say ok"` |
| Grok Build | `curl -fsSL https://x.ai/cli/install.sh \| bash` | `grok` → xAI/X sign-in | `grok -p "say ok"` |

Antigravity note: Google shut down Gemini CLI on 2026-06-18; Antigravity CLI
(`agy`) is its replacement and fills the Google seat. Unattended syntax,
verified on a live install 2026-07-17:
`agy -p "..." --dangerously-skip-permissions --print-timeout 55m` — the
print-mode timeout defaults to just 5 minutes, hence the override. The tool
is young; recheck `agy --help` after updates. If background runs act odd,
read the task .log first.

CodeGraph (your standard): wire agents once per the playbook —
`codegraph install -t claude,codex,opencode,antigravity`. Grok has no
CodeGraph target; it uses shell `codegraph explore "..."` (the worker card
says so). `agentteam init` indexes a new worktree only when your clone is
itself indexed (there is a `.codegraph/` in `repo/`), and it does that in the
background, time-boxed by `AGENTTEAM_CG_INDEX_TIMEOUT` (default 600s). An
unindexed repo stays unindexed — that is your call, not the tool's.

## 3. Set up a project

One command does the whole recipe below (clone → dev → init → playbooks
from `~/.config/agentteam/playbooks/`):

```bash
cd ~/code && agentteam new <repo-url> myproj
```

Or step by step:

```bash
cd ~/code && mkdir myproj && cd myproj
git clone <your-repo-url> repo && cd repo
git checkout dev                       # your model: dev = work, main = releases
agentteam init codex antigravity opencode grok
agentteam agents                       # every row: OK + on
cp ~/path/to/ai-*.md ../coord/docs/    # your playbooks -> master's reading ritual
```

Layout created next to the clone:

```text
myproj/
├── repo/          # your clone on dev — master session runs HERE
│   └── MASTER.md  #   symlinked as CLAUDE.md / AGENTS.md / GEMINI.md
├── wt/
│   ├── codex/     # worktree, branch agent/codex (forked from dev), WORKER.md
│   ├── antigravity/ # ... same per worker; bg-indexed if repo/ is indexed
│   ├── opencode/
│   └── grok/
└── coord/
    ├── base       # integration branch (auto-detected: dev)
    ├── docs/      # YOUR playbooks — master reads these first
    ├── board.md   # master-owned task board
    ├── tasks/     # task specs (TEMPLATE.md included)
    ├── reports/   # auto-generated run reports + full logs
    └── blockers.md
```

Role cards and `.codegraph/` are excluded via `.git/info/exclude` — the repo
stays clean. If the repo already has its own AGENTS.md router (your standard
setup), init does NOT overwrite it; it tells you to add one line: "Also read
and follow MASTER.md." Workers are likewise told to follow the repo's
AGENTS.md reading ritual, with agentteam boundaries taking precedence.

## 4. Run a cycle

```bash
cd ~/code/myproj/repo
claude        # or codex / agy / grok — whatever opens here IS the master
```

First prompt to the master:

```text
Read MASTER.md and the playbooks in ../coord/docs/. I want: <feature/fix>.
Check agentteam agents, propose a task breakdown, and wait for my "go"
before delegating. Then run the cycle and end with a merge recommendation.
```

The master (or you, in a second terminal) drives everything with:

```bash
agentteam run codex T1-codex        # run a task (foreground)
agentteam run -b grok T2-grok       # long task in background
agentteam tail T2-grok              # watch a background run live
agentteam kill T2-grok              # stop a background run
agentteam status                    # off-agents, tasks, review queue, jobs
agentteam verify codex T1-codex     # machine gate: scope + Validate + commits
agentteam diff codex                # the REAL diff vs dev — reports can lie
agentteam review codex T1-codex     # a rival vendor reviews the diff
agentteam sync                      # after merges: refresh all workshops
agentteam race T5 codex grok        # bake-off: two vendors, one task, one winner
agentteam sabotage opencode         # saboteur seat: failing tests vs fresh merges
agentteam off antigravity 5h        # it hit its window -> bench it
agentteam stop                      # kill switch for the whole project
```

You merge, nobody else — into dev, per your model:

```bash
cd ~/code/myproj/repo
git merge --no-ff agent/codex       # after the milestone gate passes
```

Acceptance gate (from your recipe, enforced by MASTER.md): `agentteam
verify` PASS + clean build (0 warnings where the repo enforces it) +
tests green + smoke run + changelog fragment (`changelog.d/<ID>.md` —
workers never edit CHANGELOG.md itself) — only then is a branch
merge-ready. main is touched only on an explicit release.

If Claude Code asks approval for every agentteam call, allow once in
`repo/.claude/settings.json`:

```json
{ "permissions": { "allow": ["Bash(agentteam *)"] } }
```

## 5. The quota switch (5-hour and weekly limits)

When an agent exhausts its plan window, bench it — everything else keeps
running:

```bash
agentteam off codex 5h    # 5-hour window burned; auto-ON when it resets
agentteam off grok 7d     # weekly cap burned
agentteam off opencode    # off until you say otherwise
agentteam on codex        # manual re-enable anytime
agentteam agents          # shows on/OFF + auto-on countdown per agent
```

Mechanics: `run` refuses OFF agents with a clear message, expired timers
clear themselves, `status` lists benched agents first. After every run the
log is scanned for limit language ("rate limit", "usage limit", "quota",
"resets at"...) and prints the exact `off` command to use; set
`AGENTTEAM_AUTO_OFF=1` to auto-bench an agent for 5h when that fires.
MASTER.md tells the master to check availability before delegating and
reroute by the fallback policy (codex→claude/grok, antigravity→codex,
grok→codex, opencode→any idle) — work never queues on a dead agent.

## 6. Tuning agents

`~/.config/agentteam/agents.conf` (or per-project `coord/agents.conf`):
one line per agent, `$TASKFILE` holds the task path, command runs inside
the worker's worktree.

```text
opencode=opencode run --dangerously-skip-permissions -m opencode/<model> "$(cat "$TASKFILE")"
```

Two workers on one engine: `agentteam init codex-2` (prefix before the dash
picks the agent). Timeout: `AGENTTEAM_TIMEOUT=7200 agentteam run ...`.

## 7. Read this before you scale up

- **Workers run with auto-approve flags** (`--dangerously-skip-permissions`,
  `--yolo`, `--always-approve`, `workspace-write`). Acceptable *because*
  this is an isolated VM — keep it that way: push branches to the remote
  often, snapshot the VM, no production credentials on it.
- **Basic plans are small.** Every delegation burns that vendor's quota and
  the master burns Claude quota planning and reviewing. Start with master +
  codex, count accepted diffs, then add agents. A worker whose diffs keep
  getting rejected costs more than it produces — bench it permanently.
- **Task files are the whole interface.** Workers have no memory of the
  master's chat. Vague task file = garbage diff. TEMPLATE.md's sections are
  the minimum, not bureaucracy.
- **Commit hygiene is enforced by prompt, verified by you**: workers are
  told to stage only their own files (no blind `git add -A`) and to add a
  CHANGELOG entry. The diff shows whether they obeyed.
- **Grok Build is a beta** (2026-05-25). If a run fails instantly, check
  `grok --help` and fix the conf line.
- **Always read the diff.** The report's output tail is the agent's claim;
  `agentteam diff <worker>` is the truth.

## 8. Troubleshooting

- `not inside an agentteam project` — run from the clone or any project
  subdir (it searches upward for `coord/` + `wt/`).
- Worker hangs → an approval prompt its auto-approve flag didn't cover, or
  expired login. Check `coord/reports/<task>.log`, re-login that CLI, verify
  with the §2 one-liner.
- Nonzero exit + near-empty log → not logged in or wrong flag;
  `agentteam agents` + §2 verify commands isolate it fast.
- Codex edits files but can't commit ("index.lock" / .git not writable) →
  its workspace-write sandbox keeps .git read-only, and a worktree's git
  metadata lives in the main repo's .git/worktrees/. The conf uses
  `--sandbox danger-full-access` for exactly this reason — don't "harden"
  it back to workspace-write, it breaks worktree commits.
- Wrong integration branch → edit `coord/base`.
- WSL `/mnt` quirks from your GOTCHAS don't apply on the native-ext4 VM;
  if you ever move this workflow to WSL-on-Windows-drive, re-add
  `codegraph sync` after edits and `git config core.filemode false`.

## Sources (verified 2026-07-10)

- Claude Code CLI: https://code.claude.com/docs/en/cli-reference
- Codex non-interactive (`codex exec`, `--sandbox workspace-write`): https://developers.openai.com/codex/noninteractive
- Codex CLI + plans: https://developers.openai.com/codex/cli
- Gemini CLI shutdown / Antigravity transition: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- Antigravity CLI hands-on (`agy -p`, headless): https://dev.to/arindam_1729/antigravity-cli-a-hands-on-guide-to-googles-terminal-coding-agent-5bc7
- agy headless/CI quirks: https://antigravitylab.net/en/articles/integrations/antigravity-cli-headless-non-interactive-ci-design
- OpenCode CLI (`run`, `--auto`, `-m`): https://opencode.ai/docs/cli/
- OpenCode Go plan: https://opencode.ai/go
- Grok Build (`grok -p`, `--always-approve`): https://x.ai/news/grok-build-cli and https://mer.vin/2026/05/grok-build-cli-xai-terminal-coding-agent-with-plan-mode-subagents-and-headless-ci/
- Antigravity official docs: https://antigravity.google/docs/cli-using

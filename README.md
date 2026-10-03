# Frugal Flock

Small plans. Big ideas.

Coordinate the AI coding tools you already use: review a plan, delegate work
to Claude, Codex, Antigravity, Grok or OpenCode, and check the results before
you merge. Runs through their CLIs on an Ubuntu VM or WSL using subscription
logins.

## Bootstrap a new machine
    bash frugal-flock-install.sh          # then log in each CLI once (docs/SETUP.md §2)
    frugal-flock selftest                 # mock agents, zero quota
    frgl-flc help                         # optional short command

`frugal-flock` is the canonical command; `frgl-flc` and legacy `agentteam`
point to the same implementation. Completion is installed for all three names.
The canonical installer is a thin wrapper around `agentteam-install.sh`;
keep both files together. Old installation automation continues to work.

Compatibility names stay in place: all `AGENTTEAM_*` environment overrides,
`~/.config/agentteam/` (including `agents.conf`, templates, playbooks and quota
state), and project state such as `.agentteam-worker`. Reinstalling preserves
your existing `agents.conf`; no user data is migrated or deleted. The implementation
remains at `~/.local/bin/agentteam`, with links for the two new names. We never
install a command called `flock`: Linux `flock` remains the locking utility.

Identity and product direction: [Brand](docs/BRAND.md) ·
[UX direction](docs/UX-DIRECTION.md) · [Next steps](TODO.md).

## Documents
| File | For | What |
|---|---|---|
| docs/HANDOFF.md | me + AIs | **Taking over the project** — what to edit, the change loop, the bug classes found, accounts/quota, handoff prompt |
| docs/GUIDEBOOK.md | me (+ beginners) | **The complete manual** — every feature, step-by-step usage, full troubleshooting, glossary. Word copy: `docs/GUIDEBOOK.docx`, regenerate with `./tools/make-docx.sh` |
| docs/HANDBOOK.md | me | Daily operations, all commands, real worked example |
| docs/EXAMPLE.md | me | Replayable tour of every feature (`bash examples/demo.sh /tmp/agentteam-demo`) |
| docs/TESTPLAN.md | me | Break-it campaign then a real build: `bash examples/breakit.sh`, real-fleet checks, first project |
| docs/SETUP.md | me | Compact install + setup reference |
| docs/MASTER-PLAN.md | me | Beginner deep-dive + phased roadmap + dictionary |
| docs/PROTOCOL.md | the AIs | Normative system spec (auto-installed into every project's coord/docs/) |
| docs/ai-project-setup-playbook.md | me + AIs | My project structure standard |
| docs/ai-full-build-recipe.md | me + AIs | My build process standard |
| research/multi-agent-claude-review.md | reference | Original architecture research, ToS analysis, sources |
| docs/DOC-CONVENTIONS.md | me + AIs | **Read before writing or editing any doc here** — Word/PDF-safe Markdown rules; enforced by `./tools/check-docs.sh` |

## Tools
    ./tools/check-docs.sh      # lint every doc for conversion-breaking Markdown
    ./tools/make-docx.sh       # docs/GUIDEBOOK.md -> docs/GUIDEBOOK.docx (pandoc)
    bash examples/demo.sh DIR  # replay every feature (stand-in fleet, zero quota)
    bash examples/breakit.sh   # adversarial campaign: attack every guarantee
    bash examples/stamp-build.sh  # build a real tool through the full loop (TESTPLAN Part C)

Built product: github.com/danielmevit/myapp (the agent scorecard).

# agentteam — private ops repo

One master AI session delegating to worker AI CLIs (Claude, Codex,
Antigravity, Grok, OpenCode) on an Ubuntu VM. Subscription logins only.

## Bootstrap a new machine
    bash agentteam-install.sh          # then log in each CLI once (docs/SETUP.md §2)

## Documents
| File | For | What |
|---|---|---|
| docs/HANDBOOK.md | me | Daily operations, all commands, real worked example |
| docs/EXAMPLE.md | me | Replayable tour of every feature (`bash examples/demo.sh /tmp/agentteam-demo`) |
| docs/SETUP.md | me | Compact install + setup reference |
| docs/MASTER-PLAN.md | me | Beginner deep-dive + phased roadmap + dictionary |
| docs/PROTOCOL.md | the AIs | Normative system spec (auto-installed into every project's coord/docs/) |
| docs/ai-project-setup-playbook.md | me + AIs | My project structure standard |
| docs/ai-full-build-recipe.md | me + AIs | My build process standard |
| research/multi-agent-claude-review.md | reference | Original architecture research, ToS analysis, sources |

Built product: github.com/danielmevit/myapp (the agent scorecard).

## README FAQ and lead AI permissions

Add a collapsible FAQ to the README: cost, how it differs from calling AI
tools directly, which tools are needed, Windows and Mac, how the AIs
coordinate, safety, how work is checked, usage limits, and refused runs or
permission prompts. SETUP gains section 9, "Lead AI permissions": what each
lead mode does, a Claude Code allowlist for the `frugal-flock` commands and
the `coord/` folder kept out of Git through `.git/info/exclude`, what that
allowlist does not allow, and why skipping permissions belongs only on a
disposable VM. The docs checker allows exactly `<details>` and `<summary>`,
only in files named README.md, with self-test probes for the allowed
dropdown, a placeholder inside one, and dropdowns in other files. Reviewed
by Grok, Codex, Gemini and GLM before the lead's final review. The
README's "Coming from agentteam?" section is removed at the owner's request;
the legacy command, installer and paths keep working.

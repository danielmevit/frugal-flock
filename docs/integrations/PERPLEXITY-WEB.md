# Perplexity Pro research and code proposals

*Prepared 2026-10-09. Optional, owner-installed research and proposal workflow.*

`tools/perplexity-worker.py` sends one bounded question to Perplexity
through your existing Perplexity Pro web subscription and prints the
answer. It can also include selected source files and save a code proposal for
another agent to review and implement through Unio. It does not edit project
files, run proposed commands, commit, or give an accepted final review.

The adapter passed offline fake fixtures (`tests/unio-perplexity.py`). A first
genuine GLM 5.3 Thinking request through one owner's Pro account also succeeded
on 2026-10-09 in about 121 seconds. It returned a readiness plan but referred to
code attachments the text-only adapter did not receive. That proposal is incomplete;
its claimed test results were not verified. Proposal prompts now ask for code and
tests inline. This trial does not establish another account's access, remaining
allowance or the effective server-side model identity.

A separate Kimi K3 Thinking trial on 2026-10-10 completed in about 300 seconds
with both requested code files inline. After personal inspection, a local run
of its six proposed test methods exposed one incorrect array fixture. The
draft remains unmerged; the inline workflow works, but proposals still require
implementation review and actual checks.

## Where the adapter lives

- Source checkout: `tools/perplexity-worker.py`.
- Installed copy: `~/.config/unio/lib/adapters/perplexity-worker.py` (or under
  `$UNIO_CONF_DIR`). Unio 0.5.8 and later package the exact reviewed script.
  Use the source-checkout path with 0.5.7 or earlier.

Installing Unio does not install the connector, sign in or contact Perplexity.
`unio integrations` (or `--json`) shows the installed path and whether the file
is present. It reads only file metadata: it never imports the connector, reads
the token or runs the adapter. `installed: true` is not readiness; sign-in,
entitlement and allowance stay unknown. Manual installation and login remain
owner steps. The single account-specific trial above is separate from installation
or file presence.

## What it uses

The adapter relies on the community library
[jacob-bd/perplexity-web-mcp](https://github.com/jacob-bd/perplexity-web-mcp),
distribution `perplexity-web-mcp-cli` 0.16.1 at commit
`e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d`, import name
`perplexity_web_mcp`, MIT licensed. It is an optional external
dependency: you install it yourself, and Unio copies none of its code.
Its licence stays with that package.

All links below are permalinks to that exact commit.

| Fact the adapter depends on | Source |
|---|---|
| `Perplexity(session_token, config)` passes `ClientConfig.max_retries` to its HTTP client | [`core.py#L176-L197`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/core.py#L176-L197) |
| `create_conversation(ConversationConfig)` returns a `Conversation` | [`core.py#L199-L202`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/core.py#L199-L202) |
| `Conversation.ask(query)` returns the conversation; read `.answer` and `.search_results` | [`core.py#L385-L400`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/core.py#L385-L400), [`#L429-L455`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/core.py#L429-L455) |
| One ask is several HTTP requests: an init-search GET, the answer POST, then a thread GET for sources and possibly report downloads | [`core.py#L457-L497`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/core.py#L457-L497), [`#L976-L989`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/core.py#L976-L989) |
| `ClientConfig.max_retries` defaults to 3; the retry stop is `max_retries + 1` attempts, so 0 means one attempt | [`config.py#L37-L51`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/config.py#L37-L51), [`resilience.py#L83-L99`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/resilience.py#L83-L99) |
| `Models.GLM_5_3` is `glm_5_3_thinking`, `Models.KIMI_K3` is `kimik3thinking`, both thinking-only | [`models.py#L97`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/models.py#L97), [`#L106`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/models.py#L106) |
| `token_store.load_token()` reads `~/.config/perplexity-web-mcp/token`, then `PERPLEXITY_SESSION_TOKEN` | [`token_store.py#L76-L99`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/token_store.py#L76-L99) |

### Why the adapter calls the library directly

Plain `pwm ask` is not bounded enough:

- With an explicit model it calls `shared.ask`
  ([`cli/main.py#L221`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/cli/main.py#L221)).
  Its shared client config does not set `max_retries`, so the default of
  3 applies
  ([`shared.py#L410-L429`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/shared.py#L410-L429)).
  On an authentication failure it reloads the token and asks again
  ([`shared.py#L628-L652`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/shared.py#L628-L652)).
- Without an explicit model it calls `smart_ask`
  ([`cli/main.py#L246`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/cli/main.py#L246)).
  `SmartRouter` then picks the model from quota and moves to `pplx_pro`
  ("Best") or Sonar when quota is critical or used up
  ([`router.py#L248-L278`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/router.py#L248-L278)).

The adapter avoids `shared`, `SmartRouter`, council, deep research and
auth refresh. Its child process makes exactly these calls:

1. `token_store.load_token()` once.
2. `Perplexity(token, ClientConfig(max_retries=0, logging_level=LogLevel.DISABLED, rotate_fingerprint=False, timeout=...))`.
3. `create_conversation(ConversationConfig(model=..., source_focus=..., save_to_library=False))`.
4. One `conversation.ask(prompt)`.

`source_focus` is `[SourceFocus.WEB]` for `--source web` (the default)
or `[]` for `--source none`.

### Corrections to the earlier Gemini contract

The earlier contract draft (branch `antigravity-perplexity-contract`) got
these points wrong:

- The package is `perplexity-web-mcp-cli`, not `perplexity-web-mcp`.
- The loopback API proxy cannot currently let Claude Code or Unio edit,
  run or commit through Perplexity. Tool calling is commented out
  ([`api/server.py#L53-L54`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/api/server.py#L53-L54)).
  A full coding-harness path stays future work.
- GLM 5.3 and Kimi K3 have no thinking toggle. Each exists only as a
  thinking identifier. The effective reasoning depth is not exposed, so
  there is no high or xhigh setting.
- `pwm ask` does not "fail closed" on auth. It rereads the token and
  retries once, and its HTTP layer retries up to three times (see above).
- Still accurate: `pwm api` binds `127.0.0.1` by default and refuses
  non-loopback hosts without an API key
  ([`api/server.py#L94-L108`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/api/server.py#L94-L108)).

### Can Perplexity write code?

The models can suggest code, explain a failure and propose a patch from context
supplied in a question. This adapter returns that text for the lead to assess.
It does not give the model local file or command access.

The community connector author disabled its tool-calling integration because
models did not reliably follow the requested format. Its unused
[`tool_calling.py`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/api/tool_calling.py)
tries to turn text such as `Action:` into tool requests. Uncommenting an import
does not connect that parser to the request/response handlers or provide a
reliable coding workflow.

Unio supports a proposal handoff with `--context-file` and `--proposal-dir`:
the lead supplies selected project files; Perplexity proposes code; a separate
implementation agent reviews the suggestion, applies suitable changes within
its task's allowed paths and runs the checks. The packet is a draft, not an
automatically applied or validated patch. A later interactive worker
would also need a bounded loop for file reads, edits and explicitly authorized
commands. That interactive loop is not implemented here. Both workflows retain
one workflow per Perplexity account, no automatic model fallback and no execution
of arbitrary instructions from an answer. Upstream's disabled parser is not an Unio setting
the owner needs to enable.

### The alternative that was not chosen

`perplexity-subscription-mcp` 0.1.2
([balakumardev/perplexity-web-wrapper](https://github.com/balakumardev/perplexity-web-wrapper)
at `87aa8b0a2ab81d83d218dcb04a48e2e7a306cf3c`) was not chosen, for three
reasons:

- It authenticates with browser cookies that you export by hand.
- Its hard-coded model mapping is obsolete (`r1`, `o3-mini`, Claude 3.7),
  with no GLM 5.3 or Kimi K3
  ([`client.py#L107-L122`](https://github.com/balakumardev/perplexity-web-wrapper/blob/87aa8b0a2ab81d83d218dcb04a48e2e7a306cf3c/perplexity_subscription_mcp/client.py#L107-L122)).
- Its development REST server allows any origin with credentials
  ([`api/main.py#L27-L33`](https://github.com/balakumardev/perplexity-web-wrapper/blob/87aa8b0a2ab81d83d218dcb04a48e2e7a306cf3c/api/main.py#L27-L33)),
  and its README starts it on `0.0.0.0`. Do not use that pattern.

## Models, labs and budgets

| `--model` | Configured identifier | Model lab | Transport and budget |
|---|---|---|---|
| `glm53` | `glm_5_3_thinking` | Z.ai | Perplexity Pro web, group `perplexity` |
| `kimi_k3` | `kimik3thinking` | Moonshot AI | Perplexity Pro web, group `perplexity` |
| `gpt6_sol` | `gpt6_sol_thinking` | OpenAI | Perplexity Pro web, group `perplexity` |

These models come from different AI labs, but all run through one Perplexity Pro
web allowance. That allowance is separate from Z.ai, Moonshot or OpenCode
accounts. It is also separate from the Perplexity API (Sonar, credits),
which is billed separately. The adapter never falls back to the API, to
another model or to another mode. If a model is missing from the installed
library, or Perplexity refuses it, the run fails without a retry.

The identifier is what the adapter asks for. It does not prove which model
Perplexity actually used. Every receipt therefore records
`effective_model: unknown` and `effective_lab: unknown`. An answer from
this adapter can't count as cross-lab review evidence, and it is never an
accepted final review.

Perplexity's help centre lists which advanced models each plan includes:
[models in your subscription](https://www.perplexity.ai/help-center/en/articles/10354919-what-advanced-ai-models-are-included-in-my-subscription)
and
[choosing a plan](https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you).
A static catalogue does not prove that your account has access.

The pinned connector exposes GPT-6 Sol Thinking through
[`Models.GPT_6_SOL_THINKING`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/models.py#L55-L59).
It does not define GPT-6.1 Sol. `gpt6_sol` is not presented as a 6.1 alias;
GPT-6.1 availability and its exact identifier need account-specific evidence
before adding that route. All three supported routes request Thinking; its
effective depth is unknown and there is no high/xhigh/max effort flag here.

## Owner setup (manual, once)

> **Read this before running any setup command.**
>
> - **Unofficial and unsupported.** The connector is not affiliated with or
>   supported by Perplexity. Its author labels it a learning project for
>   research and education and warns that consequences for your account,
>   including rate limiting, suspension or termination, are possible
>   ([README](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/README.md#L46-L49)). This repeats upstream's warning; Unio
>   has not observed any account restriction.
> - **Plaintext token.** The pinned code stores your session token as plain
>   text in `~/.config/perplexity-web-mcp/token`, created with mode `0600` in a
>   directory created with mode `0700`, not in an operating-system keyring
>   ([`token_store.py#L19-L73`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/token_store.py#L19-L73)).
>   Any software running as your user, including this package's dependencies,
>   can read it. A virtual environment separates packages; it is not a sandbox.
> - **Pins are partial.** The commit pin fixes the connector's own code. Its
>   dependencies are version ranges that pip resolves at install time
>   ([`pyproject.toml#L25-L39`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/pyproject.toml#L25-L39)), so transitive
>   packages are not pinned. No pin proves that code is safe.
> - **Login output is secret.** `pwm login` may print part of the session token
>   ([`cli/auth.py#L226-L232`](https://github.com/jacob-bd/perplexity-web-mcp/blob/e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d/src/perplexity_web_mcp/cli/auth.py#L226-L232)).
>   Keep the email code, the token and all login output in your terminal. Never
>   put them in a chat, task file, receipt or Git.
> - **Credentials stay native.** The token remains in the connector's own config
>   outside any repository; Unio never copies it. Unio's bounded proposal
>   workflow and offline adapter tests are not a security audit of the upstream
>   connector or its dependencies.
> - **Alternative without login.** You can research manually in the Perplexity
>   web app and transfer a proposal yourself into a task for an implementation
>   agent. That needs no connector installation or login.

Run these steps yourself in a terminal, not through an AI agent. Upstream
supports Python 3.10 to 3.13.

```bash
python3 -m venv "$HOME/.local/share/unio-perplexity"
"$HOME/.local/share/unio-perplexity/bin/python" -m pip install \
  "perplexity-web-mcp-cli @ git+https://github.com/jacob-bd/perplexity-web-mcp.git@e34b5082d6c16283358d8a1e3cbd7fa61c35fc0d"
"$HOME/.local/share/unio-perplexity/bin/pwm" login
```

`pwm login` asks for your email, then for the 6-digit code that Perplexity
emails you. It stores the session token in
`~/.config/perplexity-web-mcp/token`. Never paste that token or the code
into a chat or a task file. The commit pin fixes the library itself.
Its own dependencies are resolved by pip at install time.

Do not run `pwm hack`, browser-cookie exports, `pwm api` or any
global configuration change for this adapter.

## Use

The adapter must run with the same interpreter that has the library
installed. First, a read-only check:

```bash
PPLX_PY="$HOME/.local/share/unio-perplexity/bin/python"
"$PPLX_PY" tools/perplexity-worker.py --check
```

`--check` inspects only the installed package metadata, version and
module files. It does not import the package, read the token or use the
network. It reports auth, effective model and remaining capacity as
unknown.

Then make one bounded, genuine question:

```bash
mkdir -p "$HOME/.local/state/unio-perplexity-receipts"
chmod 700 "$HOME/.local/state/unio-perplexity-receipts"
"$PPLX_PY" tools/perplexity-worker.py --model glm53 --source web \
  --prompt-file "my question.md" --timeout 600 --receipt-dir "$HOME/.local/state/unio-perplexity-receipts"
```

### Research, propose, review, implement

Choose a real task and only the source files it needs. Run from the checkout:

```bash
mkdir -p "$HOME/.local/state/unio-perplexity-proposals"
chmod 700 "$HOME/.local/state/unio-perplexity-proposals"
"$PPLX_PY" tools/perplexity-worker.py --model glm53 --source web \
  --prompt-file "coordination task.md" \
  --context-file "tools/example.py" --context-file "tests/example.py" \
  --proposal-dir "$HOME/.local/state/unio-perplexity-proposals" --timeout 600
```

Replace the example file names with actual selected files. No directory scan or
automatic context upload occurs. Up to 20 explicit regular UTF-8 files are
accepted; the task, instructions and context together must fit 512 KiB.
Secret-looking filenames such as `.env`, private keys and `token` are refused.
Select appropriate source content yourself; filename checks cannot detect every
secret. Context is transmitted to your Perplexity web account with the question.

Each successful proposal creates a fresh private folder containing `task.md`,
`proposal.md`, `handoff.md` and `receipt.json`. The proposal contains the answer,
code suggestions and citations. The receipt records selected-file hashes and
the complete question hash. Files are mode `0600`, the folder mode `0700`.
No project source is changed. A failed or interrupted query creates no usable
proposal; a receipt without a proposal records that failure.

The lead creates the next bounded Unio task for an available main implementation
agent and cites the packet's path. That agent reads the original task and draft,
checks current source, rejects unsuitable suggestions, makes appropriate edits
in its own worktree and runs the defined validation. The lead inspects the diff
and results before integration. Perplexity's answer alone never accepts work.
The implementation assignment is a separate authorized task, not an automatic
second provider call hidden inside this adapter.

With `--proposal-dir --json`, stdout is packet metadata and
`status: draft_requires_review`; the answer stays in `proposal.md`.
`--proposal-dir` and `--receipt-dir` are mutually exclusive: proposals already
contain their own receipt. Without proposal mode, normal answer output remains.

How each option behaves:

- **Task.** The question comes from `--prompt-file` or `$TASKFILE`,
  never from argv. It must be a regular UTF-8 file of at most 512 KiB.
  Symlinks and FIFOs are refused.
- **`--context-file`.** Repeat to attach selected reference files to the question;
  no model-specified file reads or traversal are performed.
- **`--proposal-dir`.** Save a private draft packet for implementation review.
- **Validation first.** Flags, the task file and the bounds are all
  validated before anything is imported or authenticated.
- **`--timeout`.** The whole-run deadline in seconds, 2 to 3600.
  Default 600.
- **`--max-output`.** The answer size limit in bytes, 4 KiB to 16 MiB.
  Default 1 MiB.
- **`--json`.** Prints only the cleaned answer, the deduplicated
  `http(s)` citations and honest metadata.
- **`--receipt-dir`.** Must be an existing directory owned by you with
  mode `0700`. Each run creates its own new `0700` subdirectory holding
  `receipt.json` (mode `0600`). Receipts are never overwritten.

The parent process runs one child with the same interpreter (`-I`), in a
private temporary working directory. The parent handles the rest:

- It reads and discards the child's stderr.
- It caps the child's stdout.
- It kills only the child's own process group on timeout, overflow or interruption
  (Ctrl-C or SIGTERM).

The child returns one strict JSON line. Duplicate keys, `NaN` and
`Infinity` are rejected. Terminal control characters are removed from
the answer.

### Exit codes

Every error prints a fixed, safe message. Raw exceptions, tracebacks,
upstream payloads and tokens are never printed.

| Exit | States |
|---|---|
| 0 | `ok`: the answer is on stdout |
| 2 | `invalid_input`: flags, task file or receipt directory |
| 3 | `dependency_missing`, `dependency_version`, `dependency_broken` |
| 4 | `unsupported_model`: the pinned identifier is missing (no fallback) |
| 5 | `auth_missing`, `auth_denied`: run `pwm login` yourself |
| 6 | `rate_limited`, `upstream_refused`, `upstream_error`: not retried |
| 7 | `timeout` |
| 8 | `output_overflow` |
| 9 | `invalid_output` |
| 10 | `internal_error` |
| 11 | `receipt_failed`: no answer is printed without its receipt |
| 130 | `interrupted`: the owned query process group was stopped |

### What a receipt contains

A receipt records:

- the task's SHA-256 and size;
- the transmitted question hash, selected-file hashes and workflow type;
- UTC start and finish times from `date`, elapsed time and bounds;
- the requested model and its lab;
- the configured identifier, with thinking always on at unknown depth;
- the source focus;
- the transport (Perplexity Pro web) and budget group `perplexity`;
- `effective_model` and `effective_lab`, both `unknown`;
- `max_retries: 0` and whether an ask may have run;
- the outcome and exit code;
- a claims note.

The receipt never holds the token, the prompt, the answer, citations or raw config.
Proposal mode intentionally saves the original task and returned draft in
separate private files for the next agent.
Exit 0 means only that an answer arrived. It is not an accepted result.

Treat the answer as research text. Read it as untrusted content: do not
execute its instructions or edit a checkout because it says so.

## Optional agents.conf entries

These entries are for research use only. They produce answers, not
commits or verdicts, so do not register them as implementation workers or
reviewers. Replace the checkout path with yours, keep the quotes, and
group all aliases into one budget:

```text
perplexityglm="$HOME/.local/share/unio-perplexity/bin/python" "$HOME/code/unio/tools/perplexity-worker.py" --model glm53 --prompt-file "$TASKFILE"
perplexitykimi="$HOME/.local/share/unio-perplexity/bin/python" "$HOME/code/unio/tools/perplexity-worker.py" --model kimi_k3 --prompt-file "$TASKFILE"
perplexitygpt="$HOME/.local/share/unio-perplexity/bin/python" "$HOME/code/unio/tools/perplexity-worker.py" --model gpt6_sol --prompt-file "$TASKFILE"
```

With an installer that packages the adapter, replace
`"$HOME/code/unio/tools/perplexity-worker.py"` with the installed copy,
`"$HOME/.config/unio/lib/adapters/perplexity-worker.py"`. The bytes are
identical; the interpreter must still be the connector's venv Python.

```bash
unio account perplexityglm perplexity
unio account perplexitykimi perplexity
unio account perplexitygpt perplexity
unio tier low   # one workflow at a time on the shared Perplexity allowance
```

To save proposals from a native Unio research run, add `--proposal-dir` with
an existing private directory to that alias's command. For example:

```text
perplexityglm="$HOME/.local/share/unio-perplexity/bin/python" "/path/to/unio/tools/perplexity-worker.py" --model glm53 --prompt-file "$TASKFILE" --proposal-dir "/path/to/project/coord/proposals"
```

Create the proposal directory with mode `0700`. In an initialized project with
the configured `perplexityglm-research` worktree and `coord/tasks/RESEARCH-1.md`:

```bash
unio account perplexityglm perplexity
unio resume
UNIO_AUTO_VERIFY=0 unio run perplexityglm-research RESEARCH-1
unio stop
unio report RESEARCH-1
```

This is an answer/proposal task, so an unchanged source checkout is expected.
Do not treat its source exit as code acceptance or run an implementation gate
on an empty code diff. Assign a separate implementation task with allowed files
and validation commands, citing the saved packet. Use a per-run configuration
when attaching explicit context-file paths; retain the selected model pin.

Native runs count against Unio's shared-budget slots. Direct standalone Python
calls are unmanaged and are not counted by those slots; a group name in a
receipt alone does not enforce concurrency or read remaining allowance.

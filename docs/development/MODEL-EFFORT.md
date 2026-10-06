# Choosing model effort in Unio

This is the lead's operating guide for choosing how much reasoning a worker
or reviewer should use. Read it before assigning work. It also applies to
the lead's own next session when that session's settings are controllable.
Owner instructions and the project's run, retry and spending rules take
precedence. This guide does not authorize another invocation.

## Default and escalation

Start with **high**, or the supported **middle level** for a model whose
scale differs. Use medium for routine documentation, coordination and
well-understood edits when the model supports it. Do not default to low,
maximum effort or a model's more expensive implicit default. The route
table below identifies exceptions where a middle setting is unavailable.

Increase effort when evidence points to reasoning difficulty: an agent
misses interacting constraints, cannot explain a reproducible defect,
overlooks a demonstrated security boundary, or struggles with a genuinely
complex design. First give it the relevant evidence and a focused question.
Missing context and an overly broad task often need a clearer assignment.

Use the next **effective, supported** level. For Codex and Opus this can be
high → xhigh → max. Other routes have different scales. Reserve max for an
occasional, tightly scoped problem whose importance justifies extra tokens
and time. Record the reason, scope, time limit and known allowance before
dispatch. Return the next ordinary task to its default; escalation is not
a permanent fleet setting.

Authentication failures, usage limits, database locks, network errors,
prompt-size failures and missing tools are operational problems. Increasing
effort will not fix them. Preserve the actual failure and resolve its cause.
An elapsed reset estimate is not proof that capacity returned.

## Check the actual route

A model, its CLI and its gateway can expose different controls. Check the
exact model ID, installed CLI version and route metadata before choosing a
setting. A flag accepted by a CLI does not prove the model uses that level.
Likewise, a reasoning-capable model need not expose adjustable effort.

The following inventory was researched on **2026-10-06** using official
documentation and installed CLI help/model metadata. It covers the model
pins used in this project; it is not a promise of account availability.
Recheck it when a model, gateway or CLI changes. OpenCode observations below
come from `opencode models opencode-go --verbose` and
`opencode models opencode --verbose`, without generating model responses.

| Agent / exact route | Exposed controls | Starting choice | Escalation and limits |
| --- | --- | --- | --- |
| Codex / `gpt-6.1-sol` | Model: low, medium, high, xhigh, max; CLI configuration `model_reasoning_effort` | high; medium for routine work | xhigh, then exceptional max. Do not infer ultra support from another model or client. |
| Claude / `claude-opus-5-5` | low, medium, high, xhigh, max; installed Claude Code accepts `--effort` | high; medium for routine coordination or writing | xhigh, then exceptional max. The model's API default is medium; pin the chosen level explicitly. |
| Antigravity / `gemini-3.1-pro-high` | Installed `agy` advertises low, medium, high, xhigh, max; Google's Gemini 3.1 Pro API documents low, medium, high thinking levels | high on the existing high model route | Keep high on this pinned route. Its alias-to-API mapping for other levels is unverified; do not claim xhigh/max support from generic CLI help. |
| Grok / `grok-4.7` | low, medium, high, xhigh; installed Grok Build uses `--reasoning-effort` / `--effort` | high; medium for routine work | xhigh is the highest documented level. No documented max on this model. |
| GLM / `opencode-go/glm-5.3` | Installed variants: low, high, max; `reasoningEffort` | high, the middle of this scale | max only for a justified hard task. No medium/xhigh variant. Native Z.ai default is max, so pin high rather than omit it. |
| DeepSeek / `opencode-go/deepseek-v4-pro` | Installed variants: high, max; `reasoningEffort` | high | Exceptional max. Direct DeepSeek also documents low, but this installed route does not expose a low variant. Direct API xhigh maps to high, so it is not an escalation. |
| Kimi / `opencode-go/kimi-k3` | Installed variant: max only; `reasoningEffort` | No adjustable high/middle exposed; omit variant only if inherited gateway effort is acceptable and recorded as unknown | Explicit max is the only catalogued override. Do not manufacture high. Moonshot's direct K3 API offers low/high/max, but that is a different route. Prefer an already configured adjustable agent when budget control matters. |
| Qwen / `opencode-go/qwen3.8-max` | Installed variants: low, medium, xhigh; route option `effort` | medium, the middle of this scale | xhigh for harder work. Direct Alibaba API maps high/max to xhigh; those labels do not create extra levels. The word max in the model name is not the selected effort. |
| MiniMax / `opencode-go/minimax-m3` | Installed variants: none (thinking disabled), thinking (adaptive thinking) | thinking | A thinking toggle, not a graduated high/xhigh/max scale. M3.1 effort documentation must not be applied to this M3 pin. |
| NVIDIA / `opencode/nemotron-3-ultra-free` | Reasoning capability true; installed variants empty | Inherited route default; requested/effective effort unknown | No exposed effort override on this route. NVIDIA's self-hosted thinking controls do not prove Zen support. |
| InclusionAI / `opencode/ling-3.1-flash-free` | Installed variants: low, medium, high; `reasoningEffort` | high; medium for routine work | high is the highest exposed variant. Endpoint availability is a separate check. |
| Meituan / `opencode/longcat-2.5-preview-free` | Installed variants: low, medium, high; `reasoningEffort` | high; medium for routine work | high is the highest exposed variant. The direct LongCat API's thinking toggle is a different control. Gateway-effective depth needs response evidence. |
| Xiaomi / `opencode/mimo-v2.6-flash-free` | Reasoning capability true; installed variants empty | Inherited route default; requested/effective effort unknown | No exposed effort override. Research did not verify direct effort documentation for this exact V2.6 pin; do not borrow V2.5 settings. |

Empty variants mean **no exposed override**, not no reasoning and not high
by default. If a route cannot meet the requested high/middle policy, record
that exception. Do not silently translate labels or create a custom variant
without verifying the gateway actually supports its parameter.

## How the lead applies a choice

Use a separate per-run configuration and a wrapper pinned to the exact
model and setting. Avoid changing global CLI settings or a shared wrapper
under a running task. A frozen task's existing model/effort stays unchanged.

Examples of the effort portion of a wrapper are:

```bash
codex exec -m gpt-6.1-sol -c 'model_reasoning_effort="high"' -
claude --model claude-opus-5-5 --effort high
agy --model gemini-3.1-pro-high --effort high
grok --model grok-4.7 --reasoning-effort high
opencode run --model opencode-go/glm-5.3 --variant high
opencode run --model opencode-go/qwen3.8-max --variant medium
opencode run --model opencode-go/minimax-m3 --variant thinking
```

These illustrate flags; they are not complete unattended-run commands.
Preserve the project's permission mode, safe prompt transport, timeouts and
native Unio lifecycle. Quote paths, including the config directory. Check
installed help before using a command on a different machine.

For every new assignment, record:

- Exact model ID, AI lab, CLI version and gateway route.
- Requested effort, its actual flag/variant and the evidence supporting it.
- Effective effort if the response proves it; otherwise **unknown**.
- Why this level fits the task, especially any escalation or max exception.
- Time/spending bounds, observed capacity and the age of that observation.
- Task ID and any relationship to an earlier failed or corrected task.

Choosing another effort does not waive task scope, owner approval, retry
restrictions or review requirements. Under a one-invocation rule, do not
rerun an unchanged task merely to increase effort. A genuine correction
needs a bounded new task describing the demonstrated defect. Preserve the
original call, logs and result. Adjust the next authorized assignment;
mid-session changes require an explicitly supported, authorized mechanism.

Reviewers choose their own supported level for the task's risk. Keep their
reviews independent, check the same complete candidate, and honor the
project's required number of reviews from different AI labs. Higher effort
does not replace verification or guarantee that every mistake is caught.

## Primary references

- [GPT-6.1 Sol model controls](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
- [Claude effort and Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/effort).
- [Gemini thinking levels](https://ai.google.dev/gemini-api/docs/thinking).
- [Grok reasoning controls](https://docs.x.ai/developers/model-capabilities/text/reasoning).
- [GLM-5.3 reasoning parameters](https://docs.z.ai/guides/llm/glm-5.3).
- [DeepSeek thinking and effort mappings](https://api-docs.deepseek.com/guides/thinking_mode/).
- [Moonshot's Kimi K3 announcement](https://forum.moonshot.ai/t/kimi-k3-is-here-our-most-capable-model/480); its direct API differs from this project's Go route.
- [Alibaba's Qwen parameters and mappings](https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-chat-completions).
- [MiniMax model-specific controls](https://platform.minimax.io/docs/guides/text-generation).
- [NVIDIA's Nemotron Ultra model card](https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b/modelcard), [InclusionAI's Ling repository](https://github.com/inclusionAI/Ling), [LongCat's OpenCode integration](https://longcat.chat/platform/docs/OpenCode.html) and [Xiaomi's thinking guide](https://platform.xiaomimimo.com/docs/en-US/usage-guide/passing-back-reasoning_content). These do not establish every Zen gateway override.
- [OpenCode variants](https://opencode.ai/docs/models/) and [Zen routes](https://opencode.ai/docs/zen/). Match their current catalogue to the installed CLI's resolved metadata.

Provider documentation describes capabilities; local metadata describes the
exposed route; actual run receipts describe what was requested and observed.
Keep those three kinds of evidence distinct.

# Free model routes and project trials

Owner-approved candidate list, checked on 2026-10-07. These are exact OpenCode
Zen routes, separate from the owner's exhausted OpenCode Go subscription.
The owner now permits all listed routes when they are verifiably free; this
supersedes the earlier MiMo/LongCat-only exception for future assignments.
Use existing native authentication. No billing changes or paid fallback.

[OpenCode's official pricing](https://opencode.ai/docs/zen/#pricing) lists
all eleven as free. A read-only local `opencode models opencode --verbose`
on 2026-10-07 found ten with input, output, cache-read and cache-write costs
all zero. Exo Free was absent from the local catalog despite the screenshot
and official listing. Do not dispatch Exo until local route eligibility is
established. The catalog proves configuration/pricing metadata, not usable
quota, successful transport, code quality or permanent free access.

Before every assignment, recheck current official pricing and native costs.
Refuse missing/conflicting/nonzero prices. Pin both the primary and helper
`small_model` to the eligible route and disable paid fallback. Do not
silently switch a failed free call onto its paid model counterpart.

## Inventory and suggested first assignments

These task suggestions are **trial plans**, not established quality rankings.
Supported effort variants below come from this installed gateway, not guesses
from a different model, CLI or direct lab API. Start at high or the supported
middle for the task; when no override is exposed, record effort as unknown.

| Display name | Exact route | Price/availability evidence | Observed effort variants | Suggested first useful trial |
| --- | --- | --- | --- | --- |
| Exo Free | `opencode/exo-free` | Official free listing; missing locally | Not observed | Availability check before any assignment |
| Fledge Alpha Free | `opencode/fledge-alpha-free` | Native input/output/cache all 0 | low, high, max | Bounded coding or test-generation trial |
| Ling 3.1 Flash Free | `opencode/ling-3.1-flash-free` | Native input/output/cache all 0 | low, medium, high | Code/document analysis or focused test trial |
| LongCat 2.5 Preview Free | `opencode/longcat-2.5-preview-free` | Native input/output/cache all 0 | low, medium, high | Documentation consistency, context-heavy audit, then bounded code trial |
| Space Bunny Free | `opencode/space-bunny-free` | Native input/output/cache all 0 | low, medium, high, xhigh, max | Small code or UI trial; identity not verified |
| MiMo-V2.6-Flash Free | `opencode/mimo-v2.6-flash-free` | Native input/output/cache all 0 | No exposed override | Routine CLI/configuration, docs and bounded code changes |
| Muse Spark 1.3 Free | `opencode/muse-spark-1.3-contributor-free` | Native input/output/cache all 0 | minimal, low, medium, high, xhigh | Bounded multi-file code trial |
| Ling 3.0 Flash Fin Free | `opencode/ling-3.0-flash-fin-free` | Native input/output/cache all 0 | low, medium, high | Document/data interpretation trial; do not infer expertise from its name |
| Nemotron 3.5 Lightning Free | `opencode/nemotron-3.5-lightning-free` | Native input/output/cache all 0 | No exposed override | Small implementation or targeted regression-test trial |
| Nemotron 3 Ultra Free | `opencode/nemotron-3-ultra-free` | Native input/output/cache all 0 | No exposed override | Code analysis or a scoped implementation trial |
| Big Pickle | `opencode/big-pickle` | Native input/output/cache all 0 | No exposed override | Routine formatting/docs or a small code trial; identity not verified |

## What the small research establishes

The exact [LongCat 2.5 release notes](https://longcat.ai/platform/docs/ChangeLog.html)
describe coding, image understanding and development-tool integration. This
supports trying a code/context task; it does not prove superiority over
another agent or the same results through OpenCode's free gateway.

[NVIDIA's Lightning cookbook](https://github.com/NVIDIA-NeMo/Nemotron/blob/main/usage-cookbook/Nemotron-3.5-Lightning/README.md)
describes fast reasoning, coding and structured tool use. A focused code/test
assignment is a reasonable first experiment, rather than giving it a broad
architecture change before any local evidence exists.

The [Ling 3.1 gateway announcement](https://vercel.com/changelog/ling-3-1-flash-is-now-available-on-ai-gateway)
describes coding, multi-step analysis and tool use. That is capability context
from another gateway; its pricing, promotion dates and effort controls do not
apply to the OpenCode Zen route. Test the actual route used by Unio.

For MiMo, Muse Spark and the remaining candidates, gateway metadata provides
route and effort eligibility, while model quality is still a local question.
Do not apply another MiMo version's published scores to V2.6 Flash. Stealth
names such as Big Pickle and Space Bunny do not establish their underlying
AI lab: they cannot count as an independently identified review lab without
verified provenance. Fledge/Exo identity is likewise not established here.

## What Unio has actually observed

| Exact model and task | Actual outcome | What can be concluded |
| --- | --- | --- |
| MiMo V2.6 Flash: LEAD-POLICY-STARTUP-DOCS-1 review, 2026-10-06 | Native exit 0, complete material, APPROVE; candidate subsequently integrated. | It completed this bounded documentation review. This does not establish defect-detection accuracy or coding ability. |
| LongCat 2.5 Preview: ROADMAP-PRIORITIES-1 review, 2026-10-06 | Native exit 0 and APPROVE. | It completed one scoped roadmap assessment at high effort. |
| LongCat 2.5 Preview: LEAD-POLICY-STARTUP-DOCS-1 review, 2026-10-06 | Native exit 0, complete material, APPROVE at medium effort; candidate subsequently integrated. | It completed a second documentation review; the sample remains small. |
| Nemotron 3 Ultra: BROWSER-API-ERRORS-1 review, 2026-10-06 | Native exit 0, complete material, APPROVE. | It completed a code-review call; approval alone does not establish that it found all defects or that the whole workflow was shipped. |
| MiMo V2.6 Flash: WORK-POLICY-1 Source, 2026-10-07 | Native timeout exit 124 after the 1500-second worker bound, with delayed shutdown; zero commits or changed files. No verification/review/acceptance. | It did not deliver this broad CLI/state assignment. This is a task/route-specific failure, not a judgment of code that was never produced. |

The underlying private receipts remain in the workspace. Do not publish raw
prompts, log output or authentication to make these conclusions portable.
Update this table with exact checked outcomes after each Source finishes;
a model's final self-report is not sufficient evidence.

## Trials should deliver work, not consume it

Use pending useful project tasks: a documented bug fix, a small CLI feature,
a focused regression, a documentation correction or a UI refinement. Keep
scopes and expectations clear and compare similar work before recommending
one model over another. Avoid eleven-way races or benchmark chores invented
solely to fill a scoreboard. Each trial follows the current
[work mode and budget tier](WORK-MODES.md), invocation rules and owner scope.

Treat aliases sharing a gateway/account allowance as one budget group; in
low tier, one independent workflow may occupy that group at once. Internal
helpers can support the same authorized assignment. Different model names
and AI labs do not automatically establish different subscription budgets.
Do not launch a second Zen trial while another occupies that shared group.

The planned [project evidence feature](development/MODEL-EXPERIENCE.md)
will collect outcomes automatically and explain task-fit recommendations.
Until delivered, use native receipts, `unio score`, focused checks, actual
review findings and dated conclusions. No new rating engine is claimed here.

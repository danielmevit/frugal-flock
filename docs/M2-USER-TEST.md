# M2 user test: two new-user prototype sessions

A short facilitator guide and blank evidence sheet. The owner runs two
15–20 minute sessions, each with one person who has not used the Frugal
Flock CLI. The goal is to learn where the sample prototype confuses people.
It is not a sales demo.

This document wires no live execution. The prototype uses original sample
data only. It makes no provider calls, creates no real checkpoints, writes
no project files and performs no real merges. See the
[prototype README](../prototype/README.md).

## Before the session (2 minutes)

1. Open `prototype/index.html` directly in a modern browser: double-click
   the file, or drag it into a browser window. No installation, build,
   account or server is needed. Refresh restarts the demo.
2. Note the date, the repository commit or version, the browser and the
   device in a blank session record below.
3. Do not collect names, emails or other identifying details. Use
   "Participant A" and "Participant B".

## Opening script (1 minute)

Say, in your own words:

> "This is a simulation with made-up sample data. Nothing you click will
> touch real files or real AI tools. I am testing the design, not you.
> Please think aloud. I will give you goals, not instructions, and I may
> not answer questions until the end."

## Neutral task prompts (12–15 minutes)

Read one prompt at a time. Do not name buttons or point at the screen. If
the person is stuck for about a minute, ask "What are you looking for?"
first. Give a hint only if they are still stuck, and record it as
**coached**.

| # | Moment | Prompt to read |
| --- | --- | --- |
| 1 | Open/connect | "Open the sample project and get it ready for work." |
| 2 | Describe/review/approve plan | "Ask for a change to the journal search. Before anything starts, decide whether you agree with the plan." |
| 3 | Follow work/answer question | "Follow what is happening. If something needs your input, respond." |
| 4 | Simulated limit/replacement | "Something has changed with the work. Explain what happened, and decide how to continue." (Expected: they notice the simulated limit and explicitly choose the named Grok replacement.) |
| 5 | Review/request changes or apply | "Decide whether the result is good enough. Either ask for changes or apply it to the demo." |
| + | Stop/restart | "Imagine you need to stop this right now. Do that, then tell me what you think was kept." Refresh afterwards to restart if needed. |
| + | Narrow screen (optional) | Narrow the window or use a phone. "Find the details about the current work." |

## Understanding checks (3 minutes)

Ask openly, after the tasks. Record their words, not a yes/no:

1. "What is the difference between the worker finishing, the checks
   passing, the reviewer's opinion, your own acceptance, and the change
   being applied?" (worker process vs validation vs reviewer vs human
   acceptance vs integration)
2. "Could a tool start, or be swapped for another, without you agreeing?"
   (approval before starting or replacing tools)
3. "How much capacity was left, and when does it reset?" (the correct
   answer is that it is unknown)
4. "Did anything you did change real files on this computer?" (no)

## How to record

- **Outcome per moment:** `unassisted`, `coached` or `uncompleted`.
- **Observed confusion:** what you saw, not what you assume.
- **Participant words:** short exact quotes.
- **Severity:** `blocker` (cannot finish or misunderstands safety/approval),
  `major` (finished with coaching or a wrong mental model), `minor`
  (hesitation or wording).
- **Proposed fix:** one line; mark it as a proposal, not a decision.

## Session record A (blank)

- Date:
- Repository commit/version:
- Browser:
- Device and screen width:
- Facilitator notes on setup:

| Moment | Outcome | Observed confusion | Participant words | Severity | Proposed fix |
| --- | --- | --- | --- | --- | --- |
| 1 Open/connect | | | | | |
| 2 Plan approval | | | | | |
| 3 Follow/answer | | | | | |
| 4 Limit/Grok replacement | | | | | |
| 5 Review/apply or changes | | | | | |
| + Stop/restart | | | | | |
| + Narrow screen (optional) | | | | | |

| Understanding check | Participant words | Correct? |
| --- | --- | --- |
| Process/validation/reviewer/acceptance/integration | | |
| Approval before start or replacement | | |
| Unknown capacity/reset | | |
| Real files unchanged | | |

## Session record B (blank)

- Date:
- Repository commit/version:
- Browser:
- Device and screen width:
- Facilitator notes on setup:

| Moment | Outcome | Observed confusion | Participant words | Severity | Proposed fix |
| --- | --- | --- | --- | --- | --- |
| 1 Open/connect | | | | | |
| 2 Plan approval | | | | | |
| 3 Follow/answer | | | | | |
| 4 Limit/Grok replacement | | | | | |
| 5 Review/apply or changes | | | | | |
| + Stop/restart | | | | | |
| + Narrow screen (optional) | | | | | |

| Understanding check | Participant words | Correct? |
| --- | --- | --- |
| Process/validation/reviewer/acceptance/integration | | |
| Approval before start or replacement | | |
| Unknown capacity/reset | | |
| Real files unchanged | | |

## Gate status

M2 gates stay **pending**. They need two real completed sessions recorded
here and one clean installed-release dogfood cycle under the
[dogfood contract](M2-DOGFOOD-PLAN.md). See [TODO](../TODO.md) section 2.
Neither this guide nor a blank record counts as a session or approval.

## Next-task decision

After both sessions, choose exactly one next task:

- **Any blocker observed:** the next task is one small prototype fix for
  the most frequent blocker, followed by one more session with a new person.
- **No blocker:** record the result in TODO section 2 and move to the
  dogfood cycle or the next M2 step.

## License and credit

Existing [LICENSE](../LICENSE) and [NOTICE](../NOTICE) apply. Copyright
(C) 2026 **Daniel Mitev**, publicly **Daniel Mevit (@danielmevit)**.

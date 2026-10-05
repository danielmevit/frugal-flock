# Unio interactive prototype

Open `index.html` in a modern browser. No install, build, account, server or
provider call is needed. This is an original mock-data prototype, not the
live engine UI. It does not read project files, connect tools, send prompts,
create real checkpoints or apply real changes. Refresh restarts the demo.

Follow one Garden journal search task through these connected moments:

1. Open the sample project and connect the sample OpenCode Go worker.
2. Describe a change, create a sample plan and explicitly approve/start.
3. Advance sample activity and answer a search-behavior question.
4. Inspect the simulated limit/checkpoint and explicitly continue with Grok.
5. Watch separate process, validation and reviewer decisions, then apply
   the sample result or request changes. Stop preserves the visible history.

The right inspector collapses on narrow screens. All visible data and
provider connections are examples. Capacity and reset times are unknown;
there are no progress percentages. Applying affects the demo only. No
Toolcraft implementation, scaffolder, assets, templates or package is used.

## Checks

From the repository root:

```bash
node --check prototype/app.js
node --check prototype/scenario.js
node --test prototype/tests/scenario.test.cjs
```

Optional browser checks use Playwright as test tooling, not a runtime
dependency. Keep tooling and screenshots in the enclosing workspace's tmp
folder. From the repository root, install it locally if it is absent:

```bash
npm install --prefix ../tmp/prototype-browser-checks --no-audit --no-fund playwright
```

Install Chromium using that local Playwright CLI if no compatible browser
is installed, placing it under the same workspace, or point `M2_CHROMIUM_PATH`
at an existing Chromium executable. The browser script supports
`M2_PLAYWRIGHT_MODULE` (absolute path to the local playwright module),
`M2_CHROMIUM_PATH` and optional `M2_SCREENSHOTS` (workspace-local output).
For example, after setting those absolute paths:

```bash
node prototype/tests/browser.cjs
```

Checks cover the full journey, explicit recovery and acceptance, approval
invalidation, Stop, keyboard focus, escaped user text, a narrow viewport,
and absence of external requests/page errors. State tests reject applying
before the evidence passes and preserve history without inventing exits.

## Acceptance still needed

The owner explicitly waived the two-person feedback gate on 2026-10-04:
no testers are available, so proceed using judgment and automated checks.
No user sessions have occurred. The optional guide in docs/M2-USER-TEST.md
remains available for later feedback. When testers are available, ask them to create/approve a plan, respond to the question,
recover using the named replacement, and request changes or apply the demo.
Record whether they understand which work is simulated, which decisions
are theirs, and the difference between completion, checks and acceptance.
A live one-worker flock dogfood task also requires fresh quota approval.
The read-only local bridge and real provider handoff remain later milestones.

Copyright (C) 2026 Daniel Mitev; public attribution Daniel Mevit
(@danielmevit). Original: [Unio](https://github.com/danielmevit/unio).
AGPL-3.0-only; see the repository's LICENSE and NOTICE for full terms and
attribution/origin requirements. Distributed without warranty.

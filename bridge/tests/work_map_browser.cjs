// Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
// https://github.com/danielmevit/unio
// SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");

(async () => {
  assert.ok(process.env.TMPDIR, "Set TMPDIR to workspace-local tmp before running browser checks");
  const fixture = fs.mkdtempSync(path.join(process.env.TMPDIR, "activity-browser-"));
  for (const name of ["repo", "coord", "wt"]) fs.mkdirSync(path.join(fixture, name));
  const snapshotFile = path.join(fixture, "coord", "snapshot.json");

  // Make 30 tasks to test pagination, some finished, some active, different workers
  const results = [];
  for (let i = 0; i < 30; i++) {
    results.push({
      worker: "worker-" + (i % 3),
      task: "task-" + i + (i === 1 ? " <script>alert(1)</script>" : ""),
      recorded_at: "2026-10-04T21:00:00Z",
      activity: i % 2 === 0 ? "failed" : "running",
      process: { state: i % 2 === 0 ? "completed" : "running", exit_code: i % 2 === 0 ? 0 : null },
      validation: { state: "passed", checks_run: 1, checks_failed: 0 },
      review: { state: "unavailable", reviewer: null },
      worker_lock: "000" + i
    });
  }

  const document = {
    schema_version: 1,
    observed_at: "2026-10-04T21:00:00Z",
    stopped: false,
    agents: [],
    retries: [],
    results: results,
    recent_events: [],
    warnings: [],
    evidence: "recorded"
  };
  fs.writeFileSync(snapshotFile, JSON.stringify(document));

  const progressDoc = {
    schema_version: 1,
    workers: [
      {
        worker: "worker-0",
        task: "task-0", // matches one task
        worker_id: "w0_progress_id",
        run_id: "r0_run_id",
        observed_at: "2026-10-04T21:00:00Z",
        output: { state: "quiet", text: "Some output", generation: 1, excerpt: "foo" },
      },
      {
        worker: "worker-1",
        task: "task-new", // different task
        worker_id: "w1_progress_id",
        run_id: "r1_run_id",
        observed_at: "2026-10-04T21:00:00Z",
        output: { state: "quiet", text: "Other output", generation: 1, excerpt: "bar" },
      }
    ]
  };

  const engine = path.join(fixture, "watch-fixture");
  fs.writeFileSync(
    engine,
    `#!/usr/bin/env python3
import sys
from pathlib import Path
if sys.argv[1:] == ['watch','--once','--json']:
    sys.stdout.buffer.write((Path(__file__).parent/'coord/snapshot.json').read_bytes())
elif sys.argv[1:] == ['watch','--once','--json','--progress']:
    print('${JSON.stringify(progressDoc)}')
else:
    print('{"schema_version":1,"workers":[]}')
`,
    { mode: 0o755 },
  );

  const child = spawn("python3", ["-B", path.resolve(__dirname, "../server.py"), "--project", fixture, "--engine", engine], { stdio: ["ignore", "pipe", "pipe"] });
  let stderr = "";
  child.stderr.on("data", (chunk) => { stderr = (stderr + chunk.toString()).slice(-2000); });

  let browser, context;
  const problems = [], requests = [];
  try {
    const origin = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Timeout: " + stderr)), 10000);
      child.stdout.on("data", (chunk) => {
        const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
        if (match) { clearTimeout(timer); resolve(match[0]); }
      });
    });

    browser = await chromium.launch(process.env.M2_CHROMIUM_PATH ? { executablePath: process.env.M2_CHROMIUM_PATH } : {});

    // Denied storage safe behavior test first
    context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    await context.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', { get: () => { throw new Error('Denied'); } });
    });
    let page = await context.newPage();
    page.on("pageerror", (error) => { console.error("PAGE ERROR:", error); problems.push(error.message); });
    page.on("request", (req) => {
      if (!req.url().startsWith("http://127.0.0.1:")) problems.push("External request: " + req.url());
      if (req.method() !== "GET" && req.method() !== "HEAD") problems.push("Mutation call: " + req.method());
    });

    console.log("goto"); await page.goto(origin);
    console.log("waitForSelector map"); await page.waitForSelector("#tasks-map-container:not([hidden])"); // defaults to map on desktop

    // Test theme change
    console.log("theme dark"); await page.selectOption("#theme-selector", "dark");
    await page.waitForFunction(() => document.documentElement.dataset.theme === "dark");
    console.log("screenshot"); await page.screenshot({ path: path.join(process.env.TMPDIR, "dark_theme_map.png") });

    // Verify tasks are present
    console.log("counting nodes"); const nodes = await page.locator("g[id^='map-node-worker-']:not([id*=':::'])").count();
    assert.equal(nodes, 3, "Should show 3 workers");

    // The number of tasks should be capped by pagination.
    // 30 tasks, half are active (running), half are completed (finished).
    // mapHistoryVisible is false by default. So only 15 active tasks should be visible.
    let taskNodes = await page.locator("g[id^='map-node-worker-']:not([id*=':::'])").count(); // wait, map-node-worker-0:::task-X
    const totalTaskNodes = await page.locator("g[id*=':::']").count();
    assert.equal(totalTaskNodes, 15, "Should show 15 active tasks without history");

    // Check history toggle
    console.log("history toggle"); await page.locator("#map-history-toggle").check();
    // wait for counts to update
    await page.waitForFunction(() => document.getElementById("map-counts").textContent.includes("30"));
    const allTaskNodes = await page.locator("g[id*=':::']").count();
    assert.equal(allTaskNodes, 24, "Should be capped at 24");

    // Pagination
    console.log("next page"); await page.locator("#map-next-page").click();
    const secondPageNodes = await page.locator("g[id*=':::']").count();
    assert.equal(secondPageNodes, 6, "Should show remaining 6 tasks on second page");

    await page.locator("#map-prev-page").click();

    // Selection and details
    console.log("click node"); await page.locator("g[id='map-node-worker-0:::task-0']").click();
    await page.waitForSelector("#map-details:not([hidden])");
    const detailsHtml = await page.locator("#map-details").innerHTML();
    assert.ok(detailsHtml.includes("worker-0 / task-0"), "Details should show selected task");

    // Keyboard focus & selection
    await page.keyboard.press('Tab');

    // Test failure scenario (no stale current graph on observation failure)
    fs.writeFileSync(engine, `#!/usr/bin/env python3\nsys.exit(1)\n`, { mode: 0o755 });
    await page.waitForFunction(() => {
        const txt = document.getElementById("status").textContent;
        return txt.includes("unavailable");
    });
    const emptyNodes = await page.locator("g[id*=':::']").count();
    assert.equal(emptyNodes, 0, "Map should clear on observation failure");


    // Restore engine for mobile test
    fs.writeFileSync(
      engine,
      `#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\nif sys.argv[1:] == ['watch','--once','--json']:\n    sys.stdout.buffer.write((Path(__file__).parent/'coord/snapshot.json').read_bytes())\nelse:\n    print('{"schema_version":1,"workers":[]}')\n`,
      { mode: 0o755 },
    );
    // Test small viewport
    await page.setViewportSize({ width: 390, height: 844 });
    // Reload
    console.log("goto"); await page.goto(origin);
    // On mobile, it defaults to list
    await page.waitForSelector("#tasks .row");
    await page.locator("#view-map").click();
    console.log("waitForSelector map"); await page.waitForSelector("#tasks-map-container:not([hidden])");
    await page.selectOption("#theme-selector", "light");
    await page.waitForFunction(() => document.documentElement.dataset.theme === "light");
    console.log("screenshot"); await page.screenshot({ path: path.join(process.env.TMPDIR, "light_theme_map_mobile.png") });

    assert.deepEqual(problems, [], "No console errors, external requests or mutation calls");

  } finally {
    if (browser) await browser.close();
    child.kill();
  }
})().catch((err) => {
  console.error(err);
  process.exit(1);
});

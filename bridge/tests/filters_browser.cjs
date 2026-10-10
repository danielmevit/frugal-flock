// Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
// https://github.com/danielmevit/unio
// SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");

(async () => {
  assert.ok(process.env.TMPDIR, "Use workspace-local TMPDIR");
  const fixture = fs.mkdtempSync(path.join(process.env.TMPDIR, "filters-browser-"));
  for (const name of ["repo", "coord", "wt"]) fs.mkdirSync(path.join(fixture, name));
  const record = (worker, task, finished) => ({
    worker, task, recorded_at: "2026-10-10T17:00:00Z", activity: finished ? "succeeded" : "failed",
    worker_lock: "free", process: { state: finished ? "succeeded" : "failed", exit_code: finished ? 0 : 1 },
    validation: { state: finished ? "passed" : "not_run", checks_run: finished ? 1 : null, checks_failed: finished ? 0 : null },
    review: { state: finished ? "approved" : "not_run", reviewer: finished ? "other" : null },
  });
  const data = { schema_version: 1, observed_at: "2026-10-10T17:00:00Z", stopped: true,
    agents: [], results: [record("copilot-docs", "DOCS-GUIDE", false), record("vibeglm-build", "SAVE-FIX", true)],
    retries: [], recent_events: [], warnings: [], evidence: "recorded" };
  fs.writeFileSync(path.join(fixture, "coord/snapshot.json"), JSON.stringify(data));
  const engine = path.join(fixture, "watch-fixture");
  fs.writeFileSync(engine, "#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n"
    + "if sys.argv[1:] != ['watch','--once','--json']: raise SystemExit(2)\n"
    + "sys.stdout.buffer.write((Path(__file__).parent/'coord/snapshot.json').read_bytes())\n", { mode: 0o755 });
  const server = spawn("python3", ["-B", path.resolve(__dirname, "../server.py"), "--project", fixture, "--engine", engine],
    { stdio: ["ignore", "pipe", "pipe"] });
  let stderr = "", browser, context;
  const problems = [], requests = [];
  server.stderr.on("data", chunk => { stderr = (stderr + chunk).slice(-2000); });
  try {
    const origin = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Server startup: " + stderr)), 10000);
      server.once("error", error => { clearTimeout(timer); reject(error); });
      server.once("exit", code => { clearTimeout(timer); reject(new Error("Server exit " + code + ": " + stderr)); });
      server.stdout.on("data", chunk => {
        const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
        if (match) { clearTimeout(timer); resolve(match[0]); }
      });
    });
    browser = await chromium.launch(process.env.M2_CHROMIUM_PATH ? { executablePath: process.env.M2_CHROMIUM_PATH } : {});
    context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: "reduce" });
    const page = await context.newPage();
    page.on("pageerror", e => problems.push(e.message));
    page.on("request", r => requests.push({ url: r.url(), method: r.method() }));
    const ready = async () => page.waitForFunction(() => document.getElementById("status").textContent.includes("2026-10-10T17:00:00Z"));
    const choices = () => page.evaluate(() => Object.fromEntries(["search", "worker-filter", "state-filter", "category-filter"]
      .map(name => [name, document.getElementById("map-" + name).value])));
    const key = "unio-task-filters:v1";
    await page.goto(origin); await ready();
    await page.selectOption("#theme-selector", "dark");
    await page.selectOption("#map-worker-filter", "copilot-docs");
    await page.selectOption("#map-state-filter", "attention");
    await page.selectOption("#map-category-filter", "Other");
    await page.fill("#map-search", "DoCs");
    const expected = { search: "DoCs", "worker-filter": "copilot-docs", "state-filter": "attention", "category-filter": "Other" };
    await page.reload(); await ready();
    assert.deepEqual(await choices(), expected);
    assert.ok((await page.locator("#map-counts").textContent()).includes("1 shown"));
    assert.equal(await page.locator("#tasks").isVisible(), true);
    await page.click("#view-map");
    await page.reload(); await ready();
    assert.deepEqual(await choices(), expected);
    assert.equal(await page.locator("#tasks-map-container").isVisible(), true);
    assert.equal(await page.locator('#work-map [data-kind="task"]').count(), 1);
    await page.click("#map-reset-filters"); await page.reload(); await ready();
    assert.deepEqual(await choices(), { search: "", "worker-filter": "", "state-filter": "", "category-filter": "" });
    assert.equal(await page.locator("#tasks-map-container").isVisible(), true);
    assert.equal(await page.locator("#theme-selector").inputValue(), "dark");
    assert.ok((await page.locator("#map-counts").textContent()).includes("1 shown"), "Reset retains Current work, not All states");
    const valid = { version: 1, search: "", worker: "", state: "", category: "" };
    const invalid = ["{", "[]", "null", JSON.stringify({ ...valid, version: 2 }), JSON.stringify({ ...valid, search: 1 }),
      JSON.stringify({ ...valid, state: "future" }), JSON.stringify({ ...valid, worker: "x".repeat(129) }),
      JSON.stringify({ ...valid, search: "x".repeat(257) }), JSON.stringify({ ...valid, extra: true }),
      JSON.stringify({ ...valid, category: "bad\nvalue" }), "x".repeat(3000)];
    for (const raw of invalid) {
      await page.evaluate(([k, value]) => localStorage.setItem(k, value), [key, raw]);
      await page.reload(); await ready();
      assert.deepEqual(await choices(), { search: "", "worker-filter": "", "state-filter": "", "category-filter": "" });
      assert.equal(await page.evaluate(k => localStorage.getItem(k), key), null);
      assert.equal(await page.locator("#theme-selector").inputValue(), "dark");
    }
    await page.evaluate(([k, value]) => localStorage.setItem(k, JSON.stringify(value)),
      [key, { ...valid, worker: "missing-worker", category: "missing-kind", search: "DOCS", state: "attention" }]);
    let held;
    await page.route("**/api/activity", route => { held = route; });
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => document.getElementById("map-search").value === "DOCS");
    assert.equal((await choices())["worker-filter"], "missing-worker", "Restore survives until live data arrives");
    await page.waitForFunction(() => document.getElementById("status").textContent.includes("Loading"));
    for (let i = 0; !held && i < 100; i++) await new Promise(resolve => setTimeout(resolve, 10));
    assert.ok(held, "Activity request was held");
    await held.fulfill({ contentType: "application/json", body: JSON.stringify(data) });
    await page.unroute("**/api/activity"); await ready();
    assert.deepEqual(await choices(), { search: "DOCS", "worker-filter": "", "state-filter": "attention", "category-filter": "" });
    const saved = await page.evaluate(k => JSON.parse(localStorage.getItem(k)), key);
    assert.equal(saved.worker, ""); assert.equal(saved.category, "");
    const denied = await browser.newContext();
    try {
      await denied.addInitScript(() => {
        for (const method of ["getItem", "setItem", "removeItem"]) Storage.prototype[method] = () => { throw new Error("denied"); };
      });
      const deniedPage = await denied.newPage(); deniedPage.on("pageerror", e => problems.push(e.message));
      await deniedPage.goto(origin);
      await deniedPage.waitForFunction(() => document.getElementById("status").textContent.includes("2026-10-10T17:00:00Z"));
      await deniedPage.fill("#map-search", "DOCS");
      assert.ok((await deniedPage.locator("#map-counts").textContent()).includes("1 shown"));
      await deniedPage.click("#map-reset-filters");
    } finally { await denied.close(); }
    assert.deepEqual(problems, []);
    assert.ok(requests.every(r => r.url.startsWith(origin + "/") && r.method === "GET"));
    assert.deepEqual(fs.readdirSync(path.join(fixture, "coord")), ["snapshot.json"]);
    console.log("Filter persistence assertions PASS; closing fixture");
  } finally {
    if (context) await context.close();
    if (browser) await browser.close();
    if (server.exitCode === null) {
      server.kill("SIGINT");
      await Promise.race([once(server, "exit"), new Promise(resolve => setTimeout(resolve, 2000))]);
      if (server.exitCode === null) server.kill("SIGKILL");
    }
  }
  console.log("Filters browser: list/map reload, default reset, malformed/denied storage, deferred live reconciliation and read-only requests PASS");
})().catch(e => { console.error(e); process.exitCode = 1; });

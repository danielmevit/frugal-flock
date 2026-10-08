// Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
// https://github.com/danielmevit/unio
// SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");

const STORAGE_KEY = "unio-theme-preference";
const TAG = "TAG<img src=x>";
const SCRIPT = "<script>alert(1)</script>";

// Actual watch vocabularies: process not_run/running/succeeded/failed,
// validation not_run/passed/failed/incomplete, review
// not_run/approved/changes_requested/unknown/failed.
function task(worker, name, process, validation, review, activity) {
  return {
    worker,
    task: name,
    recorded_at: "2026-10-08T09:00:00Z",
    activity: activity || process,
    worker_lock: process === "running" ? "held" : "free",
    process: { state: process, exit_code: process === "failed" ? 1 : process === "succeeded" ? 0 : null },
    validation: { state: validation, checks_run: validation === "not_run" ? 0 : 2, checks_failed: validation === "failed" ? 1 : 0 },
    review: { state: review, reviewer: review === "not_run" ? null : "r1" },
  };
}
function baseResults() {
  const results = [
    task("worker-1", "TASK-1", "failed", "not_run", "not_run"),
    task("worker-1", "TASK-10", "running", "not_run", "not_run", "running_recorded"),
    task("worker-10", "TASK-1", "succeeded", "passed", "approved"),
    task("worker", TAG, "succeeded", "incomplete", "not_run"),
    task("worker", "FAILED", "failed", "failed", "not_run"),
    task("worker", SCRIPT, "succeeded", "passed", "unknown"),
    task("worker-2", "CHANGES", "succeeded", "passed", "changes_requested"),
    task("worker-2", "DONE-OK", "succeeded", "passed", "approved"),
    task("worker-2", "COMPLETION", "running", "not_run", "not_run", "completion_unknown"),
    task("worker-2", "UNRUN", "not_run", "not_run", "not_run"),
  ];
  for (let i = 0; i < 30; i++) results.push(task("zz-bulk", "bulk-" + String(i).padStart(2, "0"), "succeeded", "failed", "not_run"));
  return results;
}

(async () => {
  assert.ok(process.env.TMPDIR, "Set TMPDIR to workspace-local tmp before running browser checks");
  const fixture = fs.mkdtempSync(path.join(process.env.TMPDIR, "work-map-browser-"));
  const shots = path.join(process.env.TMPDIR, "work-map-screenshots");
  fs.mkdirSync(shots, { recursive: true });
  for (const name of ["repo", "coord", "wt"]) fs.mkdirSync(path.join(fixture, name));
  const snapshotFile = path.join(fixture, "coord", "snapshot.json");
  const failFlag = path.join(fixture, "coord", "FAIL");
  let tick = 0;
  let results = baseResults();
  function publish() {
    tick += 1;
    const observed = "2026-10-08T10:" + String(Math.floor(tick / 60)).padStart(2, "0") + ":" + String(tick % 60).padStart(2, "0") + "Z";
    fs.writeFileSync(snapshotFile, JSON.stringify({
      schema_version: 1, observed_at: observed, stopped: false, agents: [], retries: [],
      results, recent_events: [], warnings: [], evidence: "recorded",
    }));
    return observed;
  }
  publish();
  const engine = path.join(fixture, "watch-fixture");
  fs.writeFileSync(engine, `#!/usr/bin/env python3
import sys
from pathlib import Path
root = Path(__file__).parent
assert sys.argv[1:] == ['watch','--once','--json'], 'only read-only observation allowed'
if (root/'coord'/'FAIL').exists():
    sys.exit(1)
sys.stdout.buffer.write((root/'coord'/'snapshot.json').read_bytes())
`, { mode: 0o755 });

  const child = spawn("python3", ["-B", path.resolve(__dirname, "../server.py"), "--project", fixture, "--engine", engine], { stdio: ["ignore", "pipe", "pipe"] });
  let stderr = "";
  child.stderr.on("data", (chunk) => { stderr = (stderr + chunk.toString()).slice(-2000); });

  let browser;
  const problems = [];
  let failing = false;
  const passed = [];
  function ok(name) { passed.push(name); console.log("PASS " + name); }
  function watch(page) {
    page.on("pageerror", (error) => problems.push("pageerror: " + error.message));
    page.on("console", (message) => {
      if (message.type() !== "error") return;
      // 503 responses are expected only while the observer is failing.
      if (failing && message.text().includes("503")) return;
      problems.push("console: " + message.text());
    });
    page.on("request", (request) => {
      if (!request.url().startsWith("http://127.0.0.1:")) problems.push("External request: " + request.url());
      if (request.method() !== "GET" && request.method() !== "HEAD") problems.push("Mutation call: " + request.method() + " " + request.url());
    });
  }
  async function poll(page) {
    const observed = publish();
    await page.waitForFunction((stamp) => document.getElementById("status").textContent.includes(stamp), observed, { timeout: 10000 });
  }
  function node(page, worker, name) {
    return page.evaluateHandle(([w, t]) => [...document.querySelectorAll("#work-map [data-node-key]")]
      .find((g) => g.dataset.kind === "task" && g.dataset.worker === w && g.dataset.task === t) || null, [worker, name]);
  }
  async function taskTuples(page) {
    return page.evaluate(() => [...document.querySelectorAll("#work-map [data-node-key]")]
      .filter((g) => g.dataset.kind === "task").map((g) => [g.dataset.worker, g.dataset.task]));
  }
  async function field(page, name) {
    return page.evaluate((n) => { const el = document.querySelector('#map-details [data-field="' + n + '"]'); return el ? el.textContent : null; }, name);
  }

  try {
    const origin = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Timeout: " + stderr)), 10000);
      child.once("exit", (code) => { clearTimeout(timer); reject(new Error("server exit " + code + " " + stderr)); });
      child.stdout.on("data", (chunk) => {
        const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
        if (match) { clearTimeout(timer); resolve(match[0]); }
      });
    });
    browser = await chromium.launch(process.env.M2_CHROMIUM_PATH ? { executablePath: process.env.M2_CHROMIUM_PATH } : {});

    // --- Theme: stored preference reload and malformed storage -------------
    {
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
      const page = await context.newPage();
      watch(page);
      await page.goto(origin);
      assert.equal(await page.inputValue("#theme-selector"), "system");
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
      await page.emulateMedia({ colorScheme: "dark" });
      await page.waitForFunction(() => document.documentElement.dataset.theme === "dark");
      ok("system preference follows OS dark change");
      await page.selectOption("#theme-selector", "light");
      assert.equal(await page.evaluate((k) => localStorage.getItem(k), STORAGE_KEY), "light");
      await page.reload();
      assert.equal(await page.inputValue("#theme-selector"), "light");
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
      await page.emulateMedia({ colorScheme: "light" });
      await page.emulateMedia({ colorScheme: "dark" });
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
      ok("stored explicit Light reloads and ignores OS dark");
      await page.evaluate((k) => localStorage.setItem(k, "purple<script>"), STORAGE_KEY);
      await page.reload();
      assert.equal(await page.inputValue("#theme-selector"), "system");
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "dark");
      ok("malformed stored value falls back to System");
      await context.close();
    }
    // --- Theme: denied storage keeps the live explicit choice ---------------
    {
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "dark" });
      await context.addInitScript(() => {
        Object.defineProperty(window, "localStorage", { get: () => { throw new Error("Denied"); } });
      });
      const page = await context.newPage();
      watch(page);
      await page.goto(origin);
      assert.equal(await page.inputValue("#theme-selector"), "system");
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "dark");
      await page.selectOption("#theme-selector", "light");
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
      await page.emulateMedia({ colorScheme: "light" });
      await page.emulateMedia({ colorScheme: "dark" });
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "light");
      await page.selectOption("#theme-selector", "system");
      assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), "dark");
      await page.emulateMedia({ colorScheme: "light" });
      await page.waitForFunction(() => document.documentElement.dataset.theme === "light");
      ok("denied storage: explicit Light survives OS change; System follows OS");
      await context.close();
    }

    // --- Work map ------------------------------------------------------------
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "light", reducedMotion: "reduce" });
    const page = await context.newPage();
    watch(page);
    await page.goto(origin);
    await page.waitForSelector("#tasks-map-container:not([hidden])");
    await page.waitForFunction(() => document.querySelectorAll("#work-map [data-node-key]").length > 0);

    // Default view: attention/active stay visible; only passed+approved collapse.
    let tuples = await taskTuples(page);
    assert.equal(tuples.length, 24, "first page capped at 24 task nodes");
    assert.equal(await page.isVisible("#map-pagination"), true);
    for (const [w, t] of [["worker-1", "TASK-1"], ["worker-1", "TASK-10"], ["worker", TAG], ["worker", "FAILED"], ["worker", SCRIPT], ["worker-2", "CHANGES"], ["worker-2", "COMPLETION"], ["worker-2", "UNRUN"]])
      assert.ok(tuples.some(([a, b]) => a === w && b === t), "visible by default: " + w + " / " + t);
    for (const [w, t] of [["worker-10", "TASK-1"], ["worker-2", "DONE-OK"]])
      assert.ok(!tuples.some(([a, b]) => a === w && b === t), "finished hidden by default: " + w + " / " + t);
    const counts = await page.textContent("#map-counts");
    assert.ok(counts.includes("40 total tasks (37 need attention, 1 active, 2 finished)"), counts);
    assert.equal(await page.evaluate(() => [...document.querySelectorAll("#work-map [data-category]")].filter((g) => g.dataset.task === "FAILED")[0].dataset.category), "attention");
    ok("failed/unknown/changes-requested/incomplete/completion-unknown/not-run tasks visible; only 2 passed+approved collapsed");
    await page.click("#map-next-page");
    assert.equal((await taskTuples(page)).length, 14, "second page holds the rest of 38 visible");
    await page.click("#map-prev-page");
    ok("pagination 24 + 14");

    // Finished filter without the history toggle.
    assert.equal(await page.isChecked("#map-history-toggle"), false);
    await page.selectOption("#map-state-filter", "finished");
    assert.deepEqual((await taskTuples(page)).sort(), [["worker-10", "TASK-1"], ["worker-2", "DONE-OK"]]);
    await page.selectOption("#map-state-filter", "attention");
    tuples = await taskTuples(page);
    assert.ok(!tuples.some(([, t]) => t === "TASK-10" || t === "DONE-OK"), "attention excludes active and finished");
    await page.selectOption("#map-state-filter", "");
    ok("Finished filter exposes finished records with history toggle off");

    // Accessible node buttons and exact prefix-collision identities.
    const t1 = await node(page, "worker-1", "TASK-1");
    const t10 = await node(page, "worker-1", "TASK-10");
    assert.notEqual(await t1.evaluate((g) => g.dataset.nodeKey), await t10.evaluate((g) => g.dataset.nodeKey));
    assert.equal(await t1.evaluate((g) => g.getAttribute("role")), "button");
    assert.equal(await t1.evaluate((g) => g.getAttribute("aria-pressed")), "false");
    assert.equal(await t1.evaluate((g) => g.getAttribute("aria-label")), "Task TASK-1 on worker worker-1. Needs attention: process failed, validation not run, review not run.");
    await t1.evaluate((g) => g.focus());
    await page.keyboard.press("Enter");
    await page.waitForSelector("#map-details:not([hidden])");
    assert.equal(await field(page, "title"), "worker-1 / TASK-1");
    assert.ok((await field(page, "status")).startsWith("Needs attention · process failed"));
    assert.equal(await t1.evaluate((g) => g.getAttribute("aria-pressed")), "true");
    await t10.evaluate((g) => g.focus());
    await page.keyboard.press(" ");
    await page.waitForFunction(() => document.querySelector('#map-details [data-field="title"]').textContent === "worker-1 / TASK-10");
    assert.equal(await t1.evaluate((g) => g.getAttribute("aria-pressed")), "false");
    assert.equal(await t10.evaluate((g) => g.getAttribute("aria-pressed")), "true");
    assert.equal(await field(page, "status"), "Active · process running");
    ok("Enter opens worker-1/TASK-1, Space opens worker-1/TASK-10; aria-pressed follows exact key");

    // No grants: console stays unavailable and offers no action.
    assert.ok((await field(page, "console")).includes("unavailable"));
    assert.equal(await page.locator('#map-details [data-field="console-open"]').count(), 0);
    ok("default no grants keeps console unavailable without an action");

    // Root's reproduction: focus TAG, insert AAA before it, focus must stay.
    const tag = await node(page, "worker", TAG);
    await tag.evaluate((g) => g.focus());
    await page.keyboard.press("Enter");
    await page.waitForFunction((t) => document.querySelector('#map-details [data-field="title"]').textContent === "worker / " + t, TAG);
    const failedBefore = await node(page, "worker", "FAILED");
    results = [task("worker", "AAA", "failed", "not_run", "not_run"), task("worker-3", "NEW-1", "running", "not_run", "not_run", "running_recorded")].concat(results);
    await poll(page);
    assert.ok(await tag.evaluate((g) => g === document.activeElement && g.isConnected), "same TAG group keeps focus after AAA insertion");
    assert.equal(await page.evaluate(() => document.activeElement.dataset.task), TAG);
    assert.equal(await tag.evaluate((g) => g.getAttribute("aria-pressed")), "true");
    assert.ok(await failedBefore.evaluate((g) => g.isConnected && g.dataset.task === "FAILED"), "FAILED kept its own group");
    assert.equal(await field(page, "title"), "worker / " + TAG);
    assert.ok(await (await node(page, "worker", "AAA")).evaluate((g) => g !== null));
    ok("insertion preserves the SAME focused TAG group and selection (Root receipt reproduced and fixed)");

    // New worker appears in the filter options.
    assert.deepEqual(await page.evaluate(() => [...document.getElementById("map-worker-filter").options].map((o) => o.value)),
      ["", "worker", "worker-1", "worker-10", "worker-2", "worker-3", "zz-bulk"]);
    ok("worker filter options include newly observed worker-3");

    // A focused detail action survives an unchanged poll; values update in place.
    const clearBtn = await page.$("#map-clear-sel");
    await clearBtn.focus();
    const transforms = async () => page.evaluate(() => Object.fromEntries([...document.querySelectorAll("#work-map [data-node-key]")].map((g) => [g.dataset.nodeKey, g.getAttribute("transform")])));
    const positionsBefore = await transforms();
    const observedBefore = await field(page, "observed");
    await poll(page);
    assert.ok(await clearBtn.evaluate((b) => b === document.activeElement && b.isConnected), "clear button survives unchanged poll");
    assert.deepEqual(await transforms(), positionsBefore, "positions stable when topology unchanged");
    assert.notEqual(await field(page, "observed"), observedBefore, "current observation time updates");
    assert.equal(await field(page, "recorded"), "Task evidence recorded 2026-10-08T09:00:00Z");
    results = results.map((r) => r.worker === "worker" && r.task === TAG
      ? { ...r, recorded_at: "2026-10-08T09:30:00Z", validation: { state: "failed", checks_run: 3, checks_failed: 2 }, review: { state: "changes_requested", reviewer: "r2" } } : r);
    await poll(page);
    assert.ok(await clearBtn.evaluate((b) => b === document.activeElement && b.isConnected), "clear button survives evidence change");
    assert.equal(await field(page, "validation"), "failed · 3 checks / 2 failed");
    assert.equal(await field(page, "review"), "changes requested · reviewer r2");
    assert.equal(await field(page, "recorded"), "Task evidence recorded 2026-10-08T09:30:00Z");
    assert.ok(await tag.evaluate((g) => g.getAttribute("aria-label").includes("review changes requested")));
    ok("focused detail action survives unchanged and changed polls; state/review/recorded values update; positions stable");

    // Worker filter: selected worker disappears while the select is focused.
    await page.selectOption("#map-worker-filter", "worker-3");
    await page.focus("#map-worker-filter");
    results = results.filter((r) => r.worker !== "worker-3");
    await poll(page);
    assert.equal(await page.evaluate(() => document.activeElement.id), "map-worker-filter");
    assert.equal(await page.inputValue("#map-worker-filter"), "worker-3");
    assert.equal(await page.evaluate(() => document.getElementById("map-worker-filter").selectedOptions[0].textContent), "worker-3 (not in current observation)");
    assert.ok((await page.textContent("#map-counts")).includes("worker worker-3 is not in the current observation"));
    assert.equal((await taskTuples(page)).length, 0);
    // The selected TAG is now filtered: persistent explicit clear action.
    assert.ok((await field(page, "missing")).includes("is off-page or filtered out"));
    const missingClear = await page.$("#map-clear-sel");
    await poll(page);
    assert.ok(await missingClear.evaluate((b) => b.isConnected), "off-page clear action persists across polls");
    await page.selectOption("#map-worker-filter", "");
    assert.equal(await page.evaluate(() => [...document.getElementById("map-worker-filter").options].some((o) => o.value === "worker-3")), false);
    ok("focused worker filter keeps a truthful unavailable selection; off-page selection keeps a persistent clear action");

    // Off-page via search, then explicit clear.
    await page.fill("#map-search", "nonexistent");
    await page.waitForFunction(() => document.querySelectorAll("#work-map [data-node-key][data-kind='task']").length === 0);
    await page.click("#map-clear-sel");
    await page.waitForFunction(() => document.getElementById("map-details").hidden && !document.getElementById("map-details").childElementCount);
    await page.fill("#map-search", "");
    assert.equal(await page.evaluate(() => document.querySelectorAll('#work-map [aria-pressed="true"]').length), 0);
    ok("filtered selection cleared explicitly");

    // Literal malicious labels.
    await (await node(page, "worker", SCRIPT)).evaluate((g) => g.dispatchEvent(new MouseEvent("click", { bubbles: true })));
    await page.waitForFunction((t) => document.querySelector('#map-details [data-field="title"]')?.textContent === "worker / " + t, SCRIPT);
    assert.equal(await page.locator("#map-details script, #map-details img, #work-map script, #work-map img").count(), 0);
    assert.ok((await page.innerText("#map-details")).includes(SCRIPT));
    assert.ok((await field(page, "status")).includes("review unknown"));
    ok("literal <script>/<img> labels create no elements");

    // True camera controls: fit contains every rectangle; manual camera stays
    // unchanged across status polls, view toggles and responsive resizing.
    async function camera() {
      return page.evaluate(() => {
        const s = document.getElementById("work-map");
        return { view: s.dataset.view, x: +s.dataset.cameraX, y: +s.dataset.cameraY,
          scale: +s.dataset.scale, box: s.getAttribute("viewBox") };
      });
    }
    await page.click("#map-fit");
    await poll(page);
    assert.equal((await camera()).view, "fit");
    assert.equal(await page.getAttribute("#map-fit", "aria-pressed"), "true");
    assert.ok(await page.evaluate(() => {
      const s = document.getElementById("work-map"), v = s.viewBox.baseVal;
      return [...s.querySelectorAll('[data-node-key]')].every(g => {
        const m = g.transform.baseVal.getItem(0).matrix;
        return m.e - 80 >= v.x && m.e + 80 <= v.x + v.width &&
          m.f - 26 >= v.y && m.f + 26 <= v.y + v.height;
      });
    }), "Fit contains all node rectangles");
    const fitScale = (await camera()).scale;
    await page.click("#map-zoom-in");
    assert.ok(Math.abs((await camera()).scale - fitScale * 1.25) < 1e-9);
    await page.click("#map-zoom-out");
    assert.ok(Math.abs((await camera()).scale - fitScale) < 1e-9);
    await page.click("#map-reset");
    assert.deepEqual(await camera(), { view: "actual", x: 0, y: 0, scale: 1, box: (await camera()).box });
    assert.equal(await page.textContent("#map-zoom-level"), "100%");
    await page.focus("#work-map");
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("ArrowDown");
    const chosen = await camera();
    assert.deepEqual([chosen.x, chosen.y], [80, 80]);
    await poll(page);
    assert.deepEqual(await camera(), chosen);
    await page.click("#view-list");
    await page.click("#view-map");
    assert.deepEqual(await camera(), chosen);
    await page.setViewportSize({ width: 768, height: 720 });
    await page.waitForFunction(() => document.getElementById("work-map").clientWidth < 768);
    const resized = await camera();
    assert.deepEqual([resized.x, resized.y, resized.scale], [80, 80, 1]);
    await page.setViewportSize({ width: 1440, height: 900 });
    ok("Fit contains nodes; zoom, reset, keyboard pan and manual camera survive polls, view toggles and resizing");

    await page.focus("#work-map");
    for (let i = 0; i < 12; i++) await page.keyboard.press("+");
    assert.equal((await camera()).scale, 3);
    assert.equal(await page.isDisabled("#map-zoom-in"), true);
    for (let i = 0; i < 24; i++) await page.keyboard.press("-");
    assert.equal((await camera()).scale, 0.05);
    assert.equal(await page.isDisabled("#map-zoom-out"), true);
    await page.keyboard.press("Home");
    assert.deepEqual([(await camera()).x, (await camera()).y, (await camera()).scale], [0, 0, 1]);
    await page.keyboard.press("0");
    assert.equal((await camera()).view, "fit");
    ok("zoom clamps to 5–300%; Home resets and 0 fits");

    // Real pointer drag must pan without accidentally selecting its start node.
    await page.click("#map-fit");
    const dragNode = page.locator('#work-map [data-kind="task"]').first();
    const dragBox = await dragNode.boundingBox();
    const beforeDrag = await camera();
    const selectionBeforeDrag = await page.locator('#work-map [aria-pressed="true"]').getAttribute("data-node-key");
    await page.mouse.move(dragBox.x + dragBox.width / 2, dragBox.y + dragBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(dragBox.x + dragBox.width / 2 + 60, dragBox.y + dragBox.height / 2 + 40, { steps: 8 });
    await page.mouse.up();
    const afterDrag = await camera();
    assert.ok(Math.abs(afterDrag.x - (beforeDrag.x - 60 / beforeDrag.scale)) < 0.01);
    assert.ok(Math.abs(afterDrag.y - (beforeDrag.y - 40 / beforeDrag.scale)) < 0.01);
    assert.equal(await page.locator('#work-map [aria-pressed="true"]').getAttribute("data-node-key"), selectionBeforeDrag);
    await page.click("#map-fit");
    await dragNode.click();
    assert.equal(await dragNode.getAttribute("aria-pressed"), "true", "a normal click after dragging selects normally");
    ok("real pointer dragging pans without selecting; subsequent click selects the exact task");

    // Modified wheel zoom anchors a world point; ordinary wheel does not zoom.
    await page.click("#map-reset");
    await page.locator("#work-map").scrollIntoViewIfNeeded();
    const viewport = await page.locator("#work-map").boundingBox();
    const px = viewport.x + viewport.width / 2 + 30, py = viewport.y + viewport.height / 2 + 20;
    await page.evaluate(() => {
      const svg = document.getElementById("work-map");
      svg.addEventListener("wheel", event => {
        const before = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse());
        window.mapWheelProbe = { clientX: event.clientX, clientY: event.clientY, x: before.x, y: before.y };
      }, { capture: true, once: true });
    });
    await page.mouse.move(px, py);
    await page.keyboard.down("Control");
    await page.mouse.wheel(0, -100);
    await page.keyboard.up("Control");
    await page.waitForFunction(() => +document.getElementById("work-map").dataset.scale === 1.25);
    const wheelCamera = await camera();
    const wheelAnchor = await page.evaluate(() => {
      const before = window.mapWheelProbe;
      const after = new DOMPoint(before.clientX, before.clientY).matrixTransform(document.getElementById("work-map").getScreenCTM().inverse());
      return { before, after: { x: after.x, y: after.y } };
    });
    assert.ok(Math.abs(wheelAnchor.before.x - wheelAnchor.after.x) < 0.01, JSON.stringify(wheelAnchor));
    assert.ok(Math.abs(wheelAnchor.before.y - wheelAnchor.after.y) < 0.01, JSON.stringify(wheelAnchor));
    fs.writeFileSync(path.join(shots, "wheel-anchor.json"), JSON.stringify({ requested: { x: px, y: py }, ...wheelAnchor }, null, 2));
    console.log("Wheel anchor evidence " + JSON.stringify({ requested: { x: px, y: py }, ...wheelAnchor }));
    await page.mouse.wheel(0, 100);
    assert.deepEqual(await camera(), wheelCamera);
    await page.click("#map-fit");
    ok("Ctrl+wheel zoom anchors pointer; ordinary wheel preserves map camera");

    assert.ok(await page.evaluate(() => {
      const groups = [...document.querySelectorAll('#work-map [data-node-key]')];
      const point = g => { const m = g.transform.baseVal.getItem(0).matrix; return { x: m.e, y: m.f }; };
      const hub = point(groups.find(g => g.dataset.kind === "hub"));
      if (hub.x !== 0 || hub.y !== 0) return false;
      const workers = new Map(groups.filter(g => g.dataset.kind === "worker").map(g => [g.dataset.worker, point(g)]));
      return groups.filter(g => g.dataset.kind === "task").every(g => {
        const t = point(g), w = workers.get(g.dataset.worker);
        return Math.hypot(t.x, t.y) > Math.hypot(w.x, w.y) && t.x * w.x + t.y * w.y > w.x * w.x + w.y * w.y;
      }) && groups.every((g, i) => groups.slice(i + 1).every(h => {
        const a = point(g), b = point(h);
        return Math.abs(a.x - b.x) >= 160 || Math.abs(a.y - b.y) >= 52;
      }));
    }), "ownership branches grow outward from hub with no overlapping node rectangles");
    ok("radial hub/worker/task ownership geometry grows outward without node overlap");

    for (const theme of ["light", "dark"]) {
      await page.selectOption("#theme-selector", theme);
      assert.ok(await page.evaluate(() => {
        const style = getComputedStyle(document.documentElement);
        return [...style].filter(k => k.startsWith("--")).every(k => {
          const value = style.getPropertyValue(k).trim();
          return !/^#[0-9a-f]{6}$/i.test(value) || value.slice(1, 3) === value.slice(3, 5) && value.slice(3, 5) === value.slice(5, 7);
        });
      }), theme + " theme uses neutral grayscale tokens");
    }
    ok("Light and Dark semantic palette tokens are monochrome");

    // Desktop screenshots in Light and Dark with details open.
    await page.selectOption("#theme-selector", "light");
    await page.screenshot({ path: path.join(shots, "work-map-desktop-light.png"), fullPage: true });
    await page.selectOption("#theme-selector", "dark");
    await page.screenshot({ path: path.join(shots, "work-map-desktop-dark.png"), fullPage: true });
    ok("desktop Light and Dark screenshots captured");

    // Failure clears everything; no control resurrects it.
    await page.selectOption("#map-worker-filter", "worker");
    failing = true;
    fs.writeFileSync(failFlag, "");
    await page.waitForFunction(() => document.getElementById("status").textContent.includes("unavailable"), null, { timeout: 10000 });
    async function dead(step) {
      const state = await page.evaluate(() => ({
        nodes: document.querySelectorAll("#work-map [data-node-key]").length,
        details: document.getElementById("map-details").childElementCount,
        detailsHidden: document.getElementById("map-details").hidden,
        counts: document.getElementById("map-counts").textContent,
        pagination: document.getElementById("map-pagination").hidden,
        pageInfo: document.getElementById("map-page-info").textContent,
        rows: document.querySelectorAll("#tasks .row").length,
      }));
      assert.deepEqual(state, { nodes: 0, details: 0, detailsHidden: true, counts: "", pagination: true, pageInfo: "", rows: 0 }, "after " + step);
    }
    await dead("failure");
    await page.click("#view-list"); await dead("list view");
    await page.click("#view-map"); await dead("map view");
    await page.check("#map-history-toggle"); await dead("history toggle");
    await page.fill("#map-search", "task"); await dead("search");
    await page.fill("#map-search", ""); await dead("search clear");
    assert.deepEqual(await page.evaluate(() => [...document.getElementById("map-worker-filter").options].map((o) => o.textContent)),
      ["All Workers", "worker (not in current observation)"]);
    await page.selectOption("#map-worker-filter", ""); await dead("worker filter all");
    assert.equal(await page.evaluate(() => document.getElementById("map-worker-filter").options.length), 1);
    await page.selectOption("#map-state-filter", "finished"); await dead("state filter");
    await page.selectOption("#map-state-filter", ""); await dead("state filter all");
    await page.evaluate(() => { document.getElementById("map-next-page").click(); document.getElementById("map-prev-page").click(); }); await dead("paging");
    await page.click("#map-fit"); await dead("fit");
    await page.click("#map-reset"); await dead("reset");
    await page.click("#map-zoom-in"); await dead("zoom in");
    await page.click("#map-zoom-out"); await dead("zoom out");
    await page.uncheck("#map-history-toggle"); await dead("history off");
    ok("failure clears map/details/counts/pagination/list; list/map/history/search/filters/paging/fit/reset do not resurrect");

    // Recovery without reload.
    fs.rmSync(failFlag);
    await page.waitForFunction(() => document.querySelectorAll("#work-map [data-node-key][data-kind='task']").length > 0, null, { timeout: 10000 });
    failing = false;
    assert.ok((await page.textContent("#map-counts")).includes("total tasks"));
    ok("recovery without reload");

    // Mobile 390px: no horizontal document overflow.
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(origin);
    await page.waitForSelector("#tasks .row");
    await page.click("#view-map");
    await page.waitForFunction(() => document.querySelectorAll("#work-map [data-node-key]").length > 0);
    assert.equal(await page.inputValue("#theme-selector"), "dark");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), "no horizontal overflow at 390px");
    await page.screenshot({ path: path.join(shots, "work-map-mobile-390-dark.png"), fullPage: true });
    await page.selectOption("#theme-selector", "light");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.screenshot({ path: path.join(shots, "work-map-mobile-390-light.png"), fullPage: true });
    ok("390px map has no horizontal overflow; screenshots captured");

    // Resize the same live page: wide screens use their width, narrow controls
    // remain reachable, and a selected node survives without a reload.
    await page.locator('#work-map [data-kind="task"]').first().click();
    const selectedKey = await page.locator('#work-map [aria-pressed="true"]').getAttribute('data-node-key');
    for (const width of [1920, 768, 320, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForFunction(() => {
        const svg = document.getElementById('work-map');
        return Math.abs(svg.getBoundingClientRect().width - svg.parentElement.clientWidth) <= 1;
      });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'no overflow at ' + width);
      assert.ok(await page.evaluate(() => document.querySelector('main').getBoundingClientRect().width >= innerWidth - 1), 'workspace uses screen width at ' + width);
      assert.equal(await page.locator('#work-map [aria-pressed="true"]').getAttribute('data-node-key'), selectedKey);
      assert.ok(await page.evaluate(() => [...document.querySelectorAll('.map-controls > *, .map-details-header > *')].every(e => {
        const r = e.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth;
      })), 'controls remain within screen at ' + width);
    }
    assert.ok(!(await page.locator('footer').innerText()).includes('Daniel'));
    assert.equal(await page.locator('footer a').nth(0).getAttribute('href'), 'https://github.com/danielmevit/unio');
    assert.equal(await page.locator('footer a').nth(1).getAttribute('href'), 'https://github.com/danielmevit/unio/blob/main/LICENSE');
    ok('same page adapts from 320 to 1920px, preserves selection and displays repository/license footer');

    const touchContext = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
    const touchPage = await touchContext.newPage();
    watch(touchPage);
    await touchPage.goto(origin);
    await touchPage.click("#view-map");
    await touchPage.waitForSelector('#work-map [data-kind="task"]');
    await touchPage.locator("#work-map").scrollIntoViewIfNeeded();
    const touchBox = await touchPage.locator("#work-map").boundingBox();
    const touchCamera = () => touchPage.evaluate(() => {
      const s = document.getElementById("work-map");
      return [+s.dataset.cameraX, +s.dataset.cameraY, +s.dataset.scale];
    });
    const touchBefore = await touchCamera();
    const cdp = await touchContext.newCDPSession(touchPage);
    const tx = touchBox.x + touchBox.width / 2, ty = touchBox.y + touchBox.height / 2;
    await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: tx, y: ty }] });
    await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: tx + 40, y: ty + 30 }] });
    await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    const touchAfter = await touchCamera();
    assert.ok(Math.abs(touchAfter[0] - (touchBefore[0] - 40 / touchBefore[2])) < 0.01);
    assert.ok(Math.abs(touchAfter[1] - (touchBefore[1] - 30 / touchBefore[2])) < 0.01);
    assert.equal(await touchPage.locator('#work-map [aria-pressed="true"]').count(), 0);
    await touchContext.close();
    ok("one-finger touch input pans the map without selecting a node");

    assert.deepEqual(problems, [], "No page errors, console errors, external requests or mutation calls");
    ok("no page errors, console errors, external or mutation requests");
    fs.writeFileSync(path.join(shots, "browser-checks.json"), JSON.stringify({ passed, problems }, null, 2));
    await context.close();
    console.log("Work map browser: " + passed.length + " assertion groups passed. Screenshots: " + shots);
  } finally {
    if (browser) await browser.close();
    child.kill();
    fs.rmSync(fixture, { recursive: true, force: true });
  }
})().catch((err) => {
  console.error(err);
  process.exit(1);
});

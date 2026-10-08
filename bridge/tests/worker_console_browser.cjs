// Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
// https://github.com/danielmevit/unio
// SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { spawn, execFileSync } = require("node:child_process");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");

function sha(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}
function stamp(ms) {
  return new Date(ms).toISOString().replace("Z", "+00:00");
}

(async () => {
  assert.ok(process.env.TMPDIR, "Set workspace-local TMPDIR");
  const fixture = fs.mkdtempSync(path.join(process.env.TMPDIR, "console-ui-"));
  const worker = "w1";
  const task = "SOURCE-1";
  const attempt = "a".repeat(32);
  const start = Math.floor(Date.now() / 1000) * 1000 - 5000;
  const problems = [];
  const requests = [];
  let browser;
  let child;
  const engine = path.join(fixture, "engine");
  fs.writeFileSync(engine, `#!/usr/bin/env python3
import json, sys, os, fcntl
root = os.path.dirname(os.path.abspath(sys.argv[0]))
with open(os.path.join(root, "calls.lock"), "a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    with open(os.path.join(root, "calls.jsonl"), "a") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
if len(sys.argv) > 1 and sys.argv[1] == "watch":
    results = json.load(open(os.path.join(root, "map-results.json")))
    print(json.dumps({"schema_version":1,"observed_at":"2026-10-07T00:00:00Z","stopped":False,"agents":[],"results":results,"retries":[],"recent_events":[],"warnings":[],"evidence":"recorded only"}))
else:
    sys.exit(0)
`, { mode: 0o755 });
  function mapTask(w, t, proc, validation, review, activity) {
    return { worker: w, task: t, recorded_at: "2026-10-07T00:00:00Z", activity: activity || proc, worker_lock: "free",
      process: { state: proc, exit_code: proc === "running" ? null : proc === "failed" ? 1 : 0 },
      validation: { state: validation, checks_run: 0, checks_failed: 0 }, review: { state: review, reviewer: null } };
  }
  fs.writeFileSync(path.join(fixture, "map-results.json"), JSON.stringify([
    mapTask("w1", "SOURCE-1", "running", "not_run", "not_run", "running_recorded"),
    mapTask("w1", "SOURCE-0", "succeeded", "failed", "not_run"),
    mapTask("w1", "SOURCE-10", "failed", "not_run", "not_run"),
    mapTask("w10", "SOURCE-10", "running", "not_run", "not_run", "running_recorded"),
    mapTask("w10", "SOURCE-1", "failed", "not_run", "not_run"),
    mapTask("w2", "FILES-1", "succeeded", "incomplete", "not_run"),
    mapTask("w3", "NONE-1", "failed", "not_run", "not_run"),
  ]));
  const setup = path.join(fixture, "setup.py");
  fs.writeFileSync(setup, `
import json, os, subprocess, time
root = ${JSON.stringify(fixture)}
worker, task = ${JSON.stringify(worker)}, ${JSON.stringify(task)}
for name in ("repo", "coord", "coord/tasks", "coord/reports", "coord/retries/" + task, "coord/results/" + worker, "config", "wt"):
    os.makedirs(os.path.join(root, name), exist_ok=True)
def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)
repo, work = os.path.join(root, "repo"), os.path.join(root, "wt", worker)
git("init", "-q", "-b", "main", cwd=repo)
git("config", "user.email", "mock@invalid", cwd=repo)
git("config", "user.name", "Mock", cwd=repo)
open(os.path.join(repo, "base.txt"), "w").write("base\\n")
git("add", "base.txt", cwd=repo)
git("commit", "-qm", "base", cwd=repo)
git("worktree", "add", "-q", "-b", "agent/w1", work, cwd=repo)
git("config", "user.email", "mock@invalid", cwd=work)
git("config", "user.name", "Mock", cwd=work)
os.makedirs(os.path.join(work, "src"))
os.makedirs(os.path.join(work, "auth"))
open(os.path.join(work, "src", "hello.txt"), "w").write("hello source\\n")
open(os.path.join(work, "odd<name>.txt"), "w").write("plain <b>literal</b>\\n")
open(os.path.join(work, ".env"), "w").write("SECRET=do-not-show\\n")
open(os.path.join(work, "auth", "token.txt"), "w").write("SECRET-TOKEN\\n")
open(os.path.join(work, "src", "untracked.txt"), "w").write("UNTRACKED\\n")
git("add", "--", "src/hello.txt", "odd<name>.txt", ".env", "auth/token.txt", cwd=work)
git("commit", "-qm", "files", cwd=work)
open(os.path.join(root, "template.json"), "w").write(json.dumps({"schema_version":1,"instructions":"Do this","scope":["src/hello.txt"],"validate":["echo OK"]}))
open(os.path.join(root, "coord", "base"), "w").write("main\\n")
task_path = os.path.join(root, "coord", "tasks", task + ".md")
open(task_path, "w").write("Owner task\\n")
import hashlib
task_sha = hashlib.sha256(open(task_path, "rb").read()).hexdigest()
revision = {"base_commit":"a"*40,"candidate_commit":"b"*40,"task_sha256":task_sha,"worktree_sha256":"c"*64}
moment = ${start} / 1000
updated = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(moment))
retry_at = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(moment - 1))
native = {"schema_version":1,"worker":worker,"task":task,"updated_at":updated,"current_revision":revision,"revision":revision,
  "process":{"state":"running","exit_code":None,"revision":revision},
  "validation":{"state":"not_run","scope":"UNCHECKED","checks_run":0,"checks_failed":0,"reasons":[],"revision":None},
  "review":{"state":"not_run","reviewer":None,"process_exit_code":None,"material_complete":False,"reasons":[],"revision":None},
  "stale":False,"ready_for_human_review":False,"human":{"state":"pending"},"integration":{"state":"not_attempted"}}
retry = {"schema_version":1,"task":task,"failed_attempts":0,"retry_granted":False,"latest":{worker:{"id":${JSON.stringify(attempt)},"failed":False,"pending":True}},"updated_at":retry_at}
open(os.path.join(root, "coord", "results", worker, task + ".json"), "w").write(json.dumps(native))
open(os.path.join(root, "coord", "retries", task, "state.json"), "w").write(json.dumps(retry))
open(os.path.join(root, "coord", "reports", "ledger.jsonl"), "w").write(json.dumps({"event":"run_start","ts":updated,"worker":worker,"task":task}) + "\\n")
log = os.path.join(root, "coord", "reports", task + ".log")
open(log, "w").write("line-one\\n")
os.utime(log, (time.time(), time.time()))
# w10 shares the w1 prefix and owns SOURCE-10 (Source output only, no files grant).
w10, t10 = "w10", "SOURCE-10"
for name in ("wt/" + w10, "coord/results/" + w10, "coord/retries/" + t10):
    os.makedirs(os.path.join(root, name), exist_ok=True)
t10_path = os.path.join(root, "coord", "tasks", t10 + ".md")
open(t10_path, "w").write("Owner task ten\\n")
rev10 = dict(revision, task_sha256=hashlib.sha256(open(t10_path, "rb").read()).hexdigest())
native10 = dict(native, worker=w10, task=t10, current_revision=rev10, revision=rev10,
  process={"state":"running","exit_code":None,"revision":rev10})
retry10 = dict(retry, task=t10, latest={w10:{"id":"b"*32,"failed":False,"pending":True}})
open(os.path.join(root, "coord", "results", w10, t10 + ".json"), "w").write(json.dumps(native10))
open(os.path.join(root, "coord", "retries", t10, "state.json"), "w").write(json.dumps(retry10))
open(os.path.join(root, "coord", "reports", "ledger.jsonl"), "a").write(json.dumps({"event":"run_start","ts":updated,"worker":w10,"task":t10}) + "\\n")
open(os.path.join(root, "coord", "reports", t10 + ".log"), "w").write("w10-only-line\\n")
# w2 has a files grant only.
w2 = os.path.join(root, "wt", "w2")
git("worktree", "add", "-q", "-b", "agent/w2", w2, cwd=repo)
open(os.path.join(w2, "w2-file.txt"), "w").write("w2 tracked\\n")
git("-c", "user.email=mock@invalid", "-c", "user.name=Mock", "add", "w2-file.txt", cwd=w2)
git("-c", "user.email=mock@invalid", "-c", "user.name=Mock", "commit", "-qm", "w2", cwd=w2)
`);
  execFileSync("python3", ["-B", setup], { env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" } });
  child = spawn("python3", ["-u", "-B", path.resolve(__dirname, "../server.py"),
    "--project", fixture, "--engine", engine,
    "--enable-execution", "--worker", worker, "--reviewer", "r1",
    "--worker-company", "C1", "--reviewer-company", "C2",
    "--config-dir", path.join(fixture, "config"),
    "--task-template", path.join(fixture, "template.json"),
    "--enable-progress-output", "--progress-worker", worker, "--progress-worker", "w10",
    "--enable-worker-files", "--files-worker", worker, "--files-worker", "w2"],
    { stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" } });
  let stderr = "";
  child.stderr.on("data", (data) => { stderr = (stderr + data).slice(-2000); });
  try {
    const origin = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("startup timeout " + stderr)), 15000);
      child.once("error", (error) => { clearTimeout(timer); reject(error); });
      child.once("exit", (code) => { clearTimeout(timer); reject(new Error("startup exit " + code + " " + stderr)); });
      child.stdout.on("data", (data) => {
        const match = data.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
        if (match) { clearTimeout(timer); resolve(match[0]); }
      });
    });
    browser = await chromium.launch(process.env.M2_CHROMIUM_PATH ? { executablePath: process.env.M2_CHROMIUM_PATH } : {});
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: "reduce" });
    page.on("pageerror", (error) => problems.push(error.message));
    page.on("request", (request) => requests.push({ url: request.url(), method: request.method() }));
    page.on("console", (message) => {
      if (/Content Security Policy|Refused to/i.test(message.text())) problems.push("csp console: " + message.text());
    });
    // Record CSP violations and console scroll requests under the server's unchanged CSP.
    await page.addInitScript(() => {
      window.__csp = [];
      window.__scrolls = [];
      document.addEventListener("securitypolicyviolation", (event) => window.__csp.push(event.violatedDirective + " " + event.blockedURI));
      const original = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function (options) {
        if (this.id === "worker-console") window.__scrolls.push(options && typeof options === "object" ? options.behavior : String(options));
        return original.call(this, options);
      };
    });
    await page.goto(origin);
    const workerButton = page.locator("#console-workers").getByRole("button", { name: /^w1 \/ SOURCE-1/ });
    await workerButton.waitFor({ timeout: 10000 });
    await page.waitForFunction(() => {
      const button = [...document.querySelectorAll("#console-workers button")].find((node) => node.textContent.includes("line-one"));
      return button && button.textContent.includes("Recorded source running") && button.textContent.includes("liveness unknown");
    });
    fs.appendFileSync(path.join(fixture, "coord", "reports", "SOURCE-1.log"), "line-two\n");
    await page.waitForFunction(() => [...document.querySelectorAll("#console-workers button")].some((node) => node.textContent.includes("line-two")));
    await workerButton.click();
    await page.waitForFunction(() => {
      const node = document.getElementById("console-text");
      return node && node.textContent.includes("line-one") && node.textContent.includes("line-two");
    });
    assert.equal(await page.locator("#console-text b").count(), 0);
    assert.equal(await page.locator("#console-panel").isVisible(), true);
    await page.getByRole("tab", { name: "Files", exact: true }).click();
    await page.getByRole("button", { name: "src/hello.txt", exact: true }).waitFor();
    const listed = await page.locator("#console-file-list").textContent();
    assert.equal(listed.includes(".env"), false);
    assert.equal(listed.includes("SECRET"), false);
    assert.equal(listed.includes("auth/token.txt"), false);
    assert.equal(listed.includes("untracked.txt"), false);
    await page.getByRole("button", { name: "odd<name>.txt", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("console-file-text").textContent.includes("plain <b>literal</b>"));
    assert.equal(await page.locator("#console-file-text b").count(), 0);
    await page.getByRole("button", { name: "src/hello.txt", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("console-file-text").textContent === "hello source\n");
    let fileMode = "full";
    const fullText = "a".repeat(40000);
    const cutText = "b".repeat(20000);
    const previewRoute = /\/api\/worker-files\/workers\/[0-9a-f]{64}\/files\/[0-9a-f]{64}$/;
    await page.route(previewRoute, (route) => {
      const truncated = fileMode === "cut";
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          schema_version: 1,
          worker_id: "ignored",
          file_id: "ignored",
          relative_path: "src/hello.txt",
          observed_at: "2026-10-07T00:00:00+00:00",
          text: truncated ? cutText : fullText,
          truncated,
        }),
      });
    });
    await page.getByRole("button", { name: "src/hello.txt", exact: true }).click();
    await page.waitForFunction((expected) => {
      const text = document.getElementById("console-file-text").textContent;
      const meta = document.getElementById("console-file-meta").textContent;
      return text === expected && meta.includes("Full observed text is shown.") && !meta.includes("64 KiB");
    }, fullText);
    assert.equal(await page.locator("#console-file-text b").count(), 0);
    fileMode = "cut";
    await page.getByRole("button", { name: "src/hello.txt", exact: true }).click();
    await page.waitForFunction((expected) => {
      const text = document.getElementById("console-file-text").textContent;
      const meta = document.getElementById("console-file-meta").textContent;
      return text === expected && meta.includes("Preview truncated at 64 KiB.") && !meta.includes("Full observed text is shown.");
    }, cutText);
    await page.unroute(previewRoute);
    await page.getByRole("tab", { name: "Output", exact: true }).click();
    await page.waitForFunction(() => {
      const node = document.getElementById("console-text");
      return node && node.textContent.includes("line-one") && node.textContent.includes("line-two") && node.textContent.length <= 16384;
    });
    const postsBefore = requests.filter((item) => item.method === "POST").length;
    await page.route(origin + "/api/progress/workers", (route) => route.fulfill({
      status: 403, contentType: "application/json", body: JSON.stringify({ schema_version: 1, error: "session_refused" }),
    }), { times: 1 });
    await page.waitForFunction(() => document.getElementById("console-status").textContent.includes("Session refreshed. No action was replayed."));
    await page.waitForFunction(() => [...document.querySelectorAll("#console-workers button")].some((node) => node.textContent.includes("line-two")));
    assert.equal(requests.filter((item) => item.method === "POST").length, postsBefore);

    // --- Work map routing into this enabled console ---------------------------
    const shots = path.join(process.env.TMPDIR, "worker-console-screenshots");
    fs.mkdirSync(shots, { recursive: true });
    const consoleState = () => page.evaluate(() => ({
      flags: Object.fromEntries([...document.querySelectorAll("#console-workers button.console-worker")]
        .map((b) => [b.dataset.worker, [b.dataset.task, b.dataset.output, b.dataset.files]])),
      expanded: [...document.querySelectorAll("#console-workers button.console-worker")]
        .filter((b) => b.getAttribute("aria-expanded") === "true").map((b) => b.dataset.worker),
      panelHidden: document.getElementById("console-panel").hidden,
      scrolls: window.__scrolls.length,
    }));
    await page.waitForFunction(() => document.querySelectorAll("#console-workers button.console-worker").length === 3);
    assert.deepEqual((await consoleState()).flags, {
      w1: ["SOURCE-1", "true", "true"],
      w10: ["SOURCE-10", "true", "false"],
      w2: ["", "false", "true"],
    });
    console.log("PASS console buttons expose exact task and output/files booleans (w1 both, w10 output-only, w2 files-only)");

    // Malformed or non-exact local events are ignored.
    const before = await consoleState();
    await page.evaluate(() => {
      const send = (detail) => document.dispatchEvent(new CustomEvent("unio-open-console", { detail }));
      send(undefined); send(null); send("w1"); send(["w1", "SOURCE-1"]); send(42);
      send({ worker: 1, task: "SOURCE-1" }); send({ worker: "w1" }); send({ worker: "", task: "" });
      send({ worker: "w1", task: "SOURCE-10" }); send({ worker: "w", task: "SOURCE-1" });
      send({ worker: "w1 ", task: "SOURCE-1" }); send({ worker: "w10", task: "SOURCE-1" });
      send(Object.create({ worker: "w1", task: "SOURCE-1" }));
      send(new (class Detail { constructor() { this.worker = "w1"; this.task = "SOURCE-1"; } })());
      document.dispatchEvent(new Event("unio-open-console"));
    });
    await page.waitForTimeout(600);
    const after = await consoleState();
    assert.deepEqual([after.expanded, after.panelHidden, after.scrolls], [before.expanded, before.panelHidden, before.scrolls]);
    assert.deepEqual(after.expanded, []);
    console.log("PASS 15 malformed/non-exact unio-open-console events ignored (no selection, no scroll)");

    async function selectMapTask(w, t) {
      const handle = await page.evaluateHandle(([a, b]) => [...document.querySelectorAll("#work-map [data-node-key]")]
        .find((g) => g.dataset.kind === "task" && g.dataset.worker === a && g.dataset.task === b), [w, t]);
      await handle.evaluate((g) => g.focus());
      await page.keyboard.press("Enter");
      await page.waitForFunction((title) => document.querySelector('#map-details [data-field="title"]')?.textContent === title, w + " / " + t);
    }
    async function mapConsole() {
      return page.evaluate(() => {
        const open = document.querySelector('#map-details [data-field="console-open"]');
        return {
          text: document.querySelector('#map-details [data-field="console"]').textContent,
          label: open ? open.textContent : null,
          worker: open ? open.dataset.worker : null,
          task: open ? open.dataset.task : null,
        };
      });
    }
    async function openFromMap(expectedWorker) {
      const scrolls = (await consoleState()).scrolls;
      await page.click('#map-details [data-field="console-open"]');
      await page.waitForFunction((w) => {
        const b = [...document.querySelectorAll("#console-workers button.console-worker")].find((n) => n.dataset.worker === w);
        return b && b.getAttribute("aria-expanded") === "true" && !document.getElementById("console-panel").hidden;
      }, expectedWorker);
      const state = await consoleState();
      assert.deepEqual(state.expanded, [expectedWorker]);
      assert.equal(state.scrolls, scrolls + 1);
    }
    await page.waitForSelector("#tasks-map-container:not([hidden])");
    await page.waitForFunction(() => document.querySelectorAll("#work-map [data-kind='task']").length === 7);

    // Output-only exact task on the prefix-colliding worker w10.
    await selectMapTask("w10", "SOURCE-10");
    await page.waitForFunction(() => document.querySelector('#map-details [data-field="console-open"]'));
    assert.deepEqual(await mapConsole(), {
      text: "Source output is available for this task. Worktree files are not enabled.",
      label: "Open Source console for w10 / SOURCE-10", worker: "w10", task: "SOURCE-10",
    });
    await openFromMap("w10");
    await page.waitForFunction(() => document.getElementById("console-text").textContent.includes("w10-only-line"));
    assert.equal((await page.textContent("#console-text")).includes("line-one"), false);
    assert.equal(await page.evaluate(() => window.__scrolls[window.__scrolls.length - 1]), "auto");
    console.log("PASS map opens w10/SOURCE-10 (not w1) under unchanged CSP; output-only wording; reduced motion uses auto scroll");

    // Historical w10/SOURCE-1 names the actual latest task SOURCE-10, never w1/SOURCE-1.
    await selectMapTask("w10", "SOURCE-1");
    assert.deepEqual(await mapConsole(), {
      text: "Protected output is currently showing a different/latest task (SOURCE-10), not this historical record. Worktree files are not enabled.",
      label: "Open console for different/latest task SOURCE-10", worker: "w10", task: "SOURCE-10",
    });
    // Historical w1/SOURCE-10 names w1's latest SOURCE-1, never w10/SOURCE-10.
    await selectMapTask("w1", "SOURCE-10");
    assert.deepEqual(await mapConsole(), {
      text: "Protected output is currently showing a different/latest task (SOURCE-1), not this historical record. Tracked worktree files show the worker's current worktree, not this record.",
      label: "Open console for different/latest task SOURCE-1", worker: "w1", task: "SOURCE-1",
    });
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await openFromMap("w1");
    await page.waitForFunction(() => document.getElementById("console-text").textContent.includes("line-one"));
    assert.equal((await page.textContent("#console-text")).includes("w10-only-line"), false);
    assert.equal(await page.evaluate(() => window.__scrolls[window.__scrolls.length - 1]), "smooth");
    await page.emulateMedia({ reducedMotion: "reduce" });
    console.log("PASS historical labels name the actual latest task; w1/SOURCE-10 routes to w1/SOURCE-1; smooth scroll only without reduced motion");

    // Exact current task with both grants.
    await selectMapTask("w1", "SOURCE-1");
    assert.deepEqual(await mapConsole(), {
      text: "Source output and tracked worktree files are available for this task.",
      label: "Open Source console for w1 / SOURCE-1", worker: "w1", task: "SOURCE-1",
    });
    // Files-only worker.
    await selectMapTask("w2", "FILES-1");
    assert.deepEqual(await mapConsole(), {
      text: "Source output is not available for this worker. Only tracked worktree files are available; they show the worker's current worktree, not this record.",
      label: "Open worktree files for w2", worker: "w2", task: "",
    });
    await openFromMap("w2");
    await page.getByRole("button", { name: "w2-file.txt", exact: true }).waitFor();
    assert.equal(await page.getAttribute("#console-tab-files", "aria-selected"), "true");
    // No grant at all.
    await selectMapTask("w3", "NONE-1");
    assert.deepEqual(await mapConsole(), {
      text: "Protected output and worktree files are unavailable for this worker in the current session.",
      label: null, worker: null, task: null,
    });
    console.log("PASS both-grants, files-only (opens Files tab) and no-grant wording are exact");

    await selectMapTask("w10", "SOURCE-1");
    await page.screenshot({ path: path.join(shots, "console-map-desktop-light.png"), fullPage: true });
    await page.selectOption("#theme-selector", "dark");
    await page.screenshot({ path: path.join(shots, "console-map-desktop-dark.png"), fullPage: true });
    assert.deepEqual(await page.evaluate(() => window.__csp), []);
    console.log("PASS no CSP violations; desktop Light/Dark screenshots captured");

    await page.setViewportSize({ width: 390, height: 844 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), "no horizontal overflow at 390px");
    await page.screenshot({ path: path.join(shots, "console-map-mobile-390-dark.png"), fullPage: true });
    console.log("PASS 390px console page has no horizontal overflow. Screenshots: " + shots);
    assert.equal(await page.locator("#console-title").isVisible(), true);
    assert.equal(await workerButton.isVisible(), true);
    assert.deepEqual(problems, []);
    const calls = fs.readFileSync(path.join(fixture, "calls.jsonl"), "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line)[0]);
    assert.ok(calls.length > 0);
    assert.deepEqual([...new Set(calls)], ["watch"]);
  } finally {
    if (browser) await browser.close();
    if (child && child.exitCode === null) {
      child.kill("SIGTERM");
      await new Promise((resolve) => child.once("exit", resolve));
    }
    fs.rmSync(fixture, { recursive: true, force: true });
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

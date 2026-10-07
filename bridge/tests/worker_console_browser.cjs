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
    print(json.dumps({"schema_version":1,"observed_at":"2026-10-07T00:00:00Z","stopped":False,"agents":[],"results":[],"retries":[],"recent_events":[],"warnings":[],"evidence":"recorded only"}))
else:
    sys.exit(0)
`, { mode: 0o755 });
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
`);
  execFileSync("python3", ["-B", setup], { env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" } });
  child = spawn("python3", ["-u", "-B", path.resolve(__dirname, "../server.py"),
    "--project", fixture, "--engine", engine,
    "--enable-execution", "--worker", worker, "--reviewer", "r1",
    "--worker-company", "C1", "--reviewer-company", "C2",
    "--config-dir", path.join(fixture, "config"),
    "--task-template", path.join(fixture, "template.json"),
    "--enable-progress-output", "--progress-worker", worker,
    "--enable-worker-files", "--files-worker", worker],
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
    await page.goto(origin);
    const workerButton = page.getByRole("button", { name: /w1 \/ SOURCE-1/ });
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
    const postsBefore = requests.filter((item) => item.method === "POST").length;
    await page.route(origin + "/api/progress/workers", (route) => route.fulfill({
      status: 403, contentType: "application/json", body: JSON.stringify({ schema_version: 1, error: "session_refused" }),
    }), { times: 1 });
    await page.waitForFunction(() => document.getElementById("console-status").textContent.includes("Session refreshed. No action was replayed."));
    await page.waitForFunction(() => [...document.querySelectorAll("#console-workers button")].some((node) => node.textContent.includes("line-two")));
    assert.equal(requests.filter((item) => item.method === "POST").length, postsBefore);
    await page.setViewportSize({ width: 390, height: 844 });
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

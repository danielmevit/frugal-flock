// Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
// https://github.com/danielmevit/unio
// SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawn, execFileSync } = require("node:child_process");
const { once } = require("node:events");
const { chromium } = require(process.env.M2_PLAYWRIGHT_MODULE || "playwright");

(async () => {
  assert.ok(process.env.TMPDIR, "Set workspace-local TMPDIR");
  const fixture = fs.mkdtempSync(path.join(process.env.TMPDIR, "exec-ui-"));
  for (const name of ["repo", "coord", "wt", "config", "wt/w1", "coord/tasks", "coord/ui-execution"])
    fs.mkdirSync(path.join(fixture, name));
  
  const templatePath = path.join(fixture, "template.json");
  fs.writeFileSync(templatePath, JSON.stringify({
    schema_version: 1,
    instructions: "Do this",
    scope: ["file1.txt"],
    validate: ["echo OK"]
  }));

  const mockPython = `#!/usr/bin/env python3
import json, sys, os, hashlib, subprocess
root = os.path.dirname(sys.argv[0])
with open(os.path.join(root, 'calls.jsonl'), 'a') as f: f.write(json.dumps(sys.argv[1:]) + chr(10))
args = sys.argv[1:]
if args[0] == 'watch':
    print(json.dumps(dict(schema_version=1,observed_at='2026-10-05T00:00:00Z',stopped=False,agents=[],results=[],retries=[],recent_events=[],warnings=[],evidence='recorded only')))
elif args[0] in ('run', 'verify', 'review', 'kill'):
    if args[0] == 'run':
        for name in ('verify', 'review', 'kill'):
            if os.path.exists(os.path.join(root, name + '.marker')): os.unlink(os.path.join(root, name + '.marker'))
    if args[0] == 'kill' and os.path.exists(os.path.join(root, 'hold.marker')): os.unlink(os.path.join(root, 'hold.marker'))
    open(os.path.join(root, args[0] + '.marker'), 'w').write('fixture only')
    sys.exit(0)
elif args[0] == 'result':
    root = os.path.dirname(sys.argv[0])
    worker = args[1]
    task_id = args[2]
    def git(*a, cwd): return subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True).stdout.strip()
    base = git('rev-parse', 'HEAD', cwd=os.path.join(root, 'repo'))
    cand = git('rev-parse', 'HEAD', cwd=os.path.join(root, 'wt', worker))
    task_path = os.path.join(root, 'coord', 'tasks', task_id + '.md')
    task_sha256 = hashlib.sha256(open(task_path, 'rb').read()).hexdigest() if os.path.exists(task_path) else '0'*64
    revision = dict(base_commit=base, candidate_commit=cand, task_sha256=task_sha256, worktree_sha256='0'*64)
    res = dict(schema_version=1, worker=worker, task=task_id, updated_at='2026-10-05T00:00:00Z',
               current_revision=revision, process=dict(state='failed' if os.path.exists(os.path.join(root, 'kill.marker')) else 'running' if os.path.exists(os.path.join(root, 'hold.marker')) else 'succeeded', exit_code=137 if os.path.exists(os.path.join(root, 'kill.marker')) else None if os.path.exists(os.path.join(root, 'hold.marker')) else 0, revision=revision),
               validation=dict(state='passed' if os.path.exists(os.path.join(root, 'verify.marker')) else 'not_run', scope='OK' if os.path.exists(os.path.join(root, 'verify.marker')) else 'UNCHECKED', checks_run=1 if os.path.exists(os.path.join(root, 'verify.marker')) else 0, checks_failed=0, reasons=[], revision=revision if os.path.exists(os.path.join(root, 'verify.marker')) else None),
               review=dict(state='approved' if os.path.exists(os.path.join(root, 'review.marker')) else 'not_run', reviewer='r1' if os.path.exists(os.path.join(root, 'review.marker')) else None, process_exit_code=0 if os.path.exists(os.path.join(root, 'review.marker')) else None, material_complete=os.path.exists(os.path.join(root, 'review.marker')), reasons=[], revision=revision if os.path.exists(os.path.join(root, 'review.marker')) else None),
               stale=False, ready_for_human_review=not os.path.exists(os.path.join(root, 'hold.marker')) and not os.path.exists(os.path.join(root, 'kill.marker')) and os.path.exists(os.path.join(root, 'verify.marker')) and os.path.exists(os.path.join(root, 'review.marker')))
    print(json.dumps(res))
`;
  const engine = path.join(fixture, "engine");
  fs.writeFileSync(engine, mockPython, { mode: 0o755 });

  const setupPy = path.join(fixture, "setup.py");
  fs.writeFileSync(setupPy, `
import os, subprocess
def git(*args):
    subprocess.run(['git', *args], check=True, cwd=os.path.join('${fixture}', 'repo'))
git('init', '-q', '-b', 'main')
git('config', 'user.email', 'mock@invalid')
git('config', 'user.name', 'Mock')
open(os.path.join('${fixture}', 'repo', 'source.txt'), 'w').write('base\\n')
git('add', 'source.txt')
git('commit', '-qm', 'base')
git('worktree', 'add', '-q', '-b', 'agent/w1', os.path.join('${fixture}', 'wt', 'w1'))
open(os.path.join('${fixture}', 'coord', 'base'), 'w').write('main\\n')
`);
  execFileSync("python3", ["-B", setupPy], {env: {...process.env, PYTHONDONTWRITEBYTECODE: "1"}});

  
  const child = spawn(
    "python3",
    [
      "-u",
      "-B",
      path.resolve(__dirname, "../server.py"),
      "--project", fixture,
      "--engine", engine,
      "--enable-execution",
      "--worker", "w1",
      "--reviewer", "r1",
      "--worker-company", "C1",
      "--reviewer-company", "C2",
      "--config-dir", path.join(fixture, "config"),
      "--task-template", templatePath
    ],
    { stdio: ["ignore", "pipe", "pipe"], env: {...process.env, PYTHONDONTWRITEBYTECODE: "1"} },
  );
  
  let stderr = "",
    browser,
    context;
  child.stderr.on("data", (data) => {
    process.stderr.write(data);
    stderr = (stderr + data).slice(-2000);
  });
  
  try {
    const origin = await new Promise((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error("startup timeout " + stderr)),
        10000,
      );
      child.once("error", (error) => {
        clearTimeout(timer);
        reject(error);
      });
      child.once("exit", (code) => {
        clearTimeout(timer);
        reject(new Error("startup exit " + code + " " + stderr));
      });
      child.stdout.on("data", (data) => {
        const url = data.toString().match(/http:\/\/127\.0\.0\.1:\d+/);
        if (url) {
          clearTimeout(timer);
          resolve(url[0]);
        }
      });
    });
    
    browser = await chromium.launch(
      process.env.M2_CHROMIUM_PATH
        ? { executablePath: process.env.M2_CHROMIUM_PATH }
        : {},
    );
    context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const failures = [],
      requests = [];
    let posts = 0;
    
    page.on("pageerror", (error) => failures.push(error.message));
    page.on("request", (request) => {
      requests.push({ url: request.url(), method: request.method(), body: request.method() === "POST" ? request.postDataJSON() : null });
      if (request.method() === "POST") posts++;
    });
    
    const isPreparedResponse = (response) => response.url() === origin + "/api/jobs"
      && response.request().method() === "POST" && response.ok();
    // Hold the old asynchronous identity observer until explicit recovery has
    // completed. This forces the original race without sleeps or extra timeouts.
    let observedJobId, releasePreparedObserver, completePreparedObservation;
    const preparedObserverGate = new Promise((resolve) => releasePreparedObserver = resolve);
    const preparedObservation = new Promise((resolve) => completePreparedObservation = resolve);
    const observePreparedJob = (response) => {
      if (!isPreparedResponse(response)) return;
      page.off("response", observePreparedJob);
      completePreparedObservation((async () => {
        await preparedObserverGate;
        observedJobId = (await response.json()).job.id;
        return observedJobId;
      })());
    };
    page.on("response", observePreparedJob);

    const calls = (verb) => fs.readFileSync(path.join(fixture, "calls.jsonl"), "utf8")
      .trim().split("\n").map(JSON.parse).filter((argv) => argv[0] === verb);
    const stage = async (name) => {
      assert.equal(await page.locator('#job-stages [aria-current="step"]').count(), 1);
      assert.equal(await page.locator('#job-stages [aria-current="step"]').getAttribute("data-stage"), name);
      assert.ok((await page.locator("#stage-help").textContent()).length > 40);
    };
    const visual = [];
    async function inspect(label) {
      for (const [name, width, height] of [["desktop", 1440, 900], ["narrow", 390, 844]]) {
        await page.setViewportSize({width, height});
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), label + " " + name + " has no page overflow");
        assert.ok(await page.locator("#job-preview pre").evaluateAll((nodes) => nodes.every((node) => node.scrollWidth <= node.clientWidth + 1)), "Exact long preview wraps without clipping");
        for (const button of await page.locator("button:visible").all()) {
          const box = await button.boundingBox();
          assert.ok(box.height >= 44, "Touch target is at least 44px high");
        }
        if (process.env.M2_SCREENSHOTS) {
          fs.mkdirSync(process.env.M2_SCREENSHOTS, {recursive:true});
          const file = `execution-${label}-${name}.png`;
          await page.screenshot({path:path.join(process.env.M2_SCREENSHOTS, file), fullPage:true});
          visual.push({file, viewport:{width,height}, state:label, data:"local mock engine/API fixture; no provider calls"});
        }
      }
      await page.setViewportSize({width:1440,height:900});
    }
    await page.goto(origin);
    await page.waitForFunction(() => !document.getElementById("manual-drafts").hidden);
    assert.equal(await page.locator("#mode-label").textContent(), "Live execution");
    assert.ok((await page.locator(".notice").textContent()).includes("Approve run permits spending"));
    assert.ok(!(await page.locator("#mode-footer").textContent()).includes("read-only"));
    assert.ok((await page.locator("#mode-footer").textContent()).includes("current verified and reviewed revision"));
    await page.keyboard.press("Tab");
    assert.equal(await page.locator(":focus").textContent(), "Skip to workspace");
    await page.keyboard.press("Enter");
    assert.equal(await page.locator(":focus").getAttribute("id"), "workspace");
    await inspect("composer");

    // An unknown job ID from an empty workspace must show its error, retain
    // the entered ID and expose no action that could create a paid intent.
    await page.locator("#reopen-details > summary").click();
    await page.locator("#job-id").fill("a".repeat(32));
    await page.locator("#reopen-job").click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job not found"));
    assert.equal(await page.locator("#job-status").isVisible(), true);
    assert.equal(await page.locator("#job-id").inputValue(), "a".repeat(32));
    assert.equal(await page.locator("#job-start").isVisible(), false);
    assert.equal(posts, 0);
    await stage("preview");
    await page.locator("#reopen-details > summary").click();

    // Create a draft; the entire long request must survive literally.
    const literal = "Malicious <script>alert(1)</script> Café\n" + "long_unbroken_request_".repeat(120);
    await page.getByLabel("Describe the work to save").fill(literal);
    await page.getByRole("button", {name:"Save draft",exact:true}).click();
    await page.waitForFunction(() => document.getElementById("draft-status").textContent.includes("draft saved."));
    await stage("preview");
    assert.equal(await page.locator("#draft-text").textContent(), literal);
    // Prepare retains its original explicit journey assertion.
    const preparedResponse = page.waitForResponse(isPreparedResponse);
    await page.getByRole("button", {name:"Prepare preview",exact:true}).click();
    const preparedView = await (await preparedResponse).json();
    const currentJobId = preparedView.job.id;
    assert.match(currentJobId, /^[0-9a-f]{32}$/);
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job prepared."));
    assert.equal(await page.locator("#job-id").inputValue(), currentJobId,
      "Rendered identity matches the authoritative completed prepare response");
    assert.equal(observedJobId, undefined, "Response observer is still deliberately blocked");
    assert.ok(await page.locator("#job-preview").isVisible());
    assert.ok((await page.locator("#job-preview-text").textContent()).includes("Malicious"));
    assert.equal(await page.locator("#job-request-text").textContent(), literal);
    assert.equal(await page.locator("#job-preview script").count(), 0);
    for (const exact of ["file1.txt", "echo OK", "C1", "C2", "w1", "r1"])
      assert.ok((await page.locator("#job-preview-text").textContent()).includes(exact));
    await stage("approve");
    const approve = page.getByRole("button", {name:"Approve run",exact:true});
    // A rotated session never repeats a write and retains the same opaque intent.
    const approvalUrl = origin + `/api/jobs/${currentJobId}/approve`;
    const interceptedApprovals = [];
    await page.route(approvalUrl, (route) => {
      const request = route.request();
      assert.equal(request.method(), "POST");
      assert.equal(request.url(), approvalUrl);
      interceptedApprovals.push(request.postDataJSON());
      return route.fulfill({status:403,json:{schema_version:1,error:"session_refused"}});
    }, {times:1});
    const beforeSession = posts;
    const sessionReads = () => requests.filter((r) => r.url === origin + "/api/session" && r.method === "GET").length;
    const beforeSessionReads = sessionReads();
    const refusedApproval = page.waitForResponse((response) => response.url() === approvalUrl && response.request().method() === "POST");
    await approve.click();
    assert.equal((await refusedApproval).status(), 403, "The intended approval response was injected");
    assert.equal(interceptedApprovals.length, 1, "Exactly one approval POST reached the 403 interceptor");
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Session refreshed"));
    assert.equal(observedJobId, undefined, "Session recovery does not depend on the delayed observer");
    assert.equal(sessionReads(), beforeSessionReads + 1, "403 explicitly refreshes the session once");
    assert.equal(posts, beforeSession + 1);
    assert.equal(await approve.isDisabled(), true);
    const approvalKey = await page.evaluate((id) => sessionStorage.getItem(`unio_job_${id}_approval_key`), currentJobId);
    assert.match(approvalKey, /^[0-9a-f]{32}$/);
    assert.equal(interceptedApprovals[0].approval_key, approvalKey);
    assert.equal(requests.find((r) => r.url.endsWith("/approve")).body.approval_key, approvalKey);
    assert.equal(await page.getByLabel("Describe the work to save").inputValue(), literal);
    await inspect("session-error");
    await page.locator("#job-refresh").click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job refreshed."));
    assert.equal(posts, beforeSession + 1);
    assert.equal(await approve.isEnabled(), true);
    assert.equal(observedJobId, undefined, "Explicit GET-only job recovery completes before observer assignment");
    assert.equal(calls("run").length, 0, "Refused approval and read recovery never launch a worker");
    releasePreparedObserver();
    assert.equal(await preparedObservation, currentJobId, "The delayed observer eventually sees the same prepared job");
    // Double click approve protection, with explicit busy accessibility.
    let releaseApproval;
    const approvalGate = new Promise((resolve) => releaseApproval = resolve);
    await page.route(origin + `/api/jobs/${currentJobId}/approve`, async (route) => {await approvalGate; await route.continue();}, {times:1});
    await approve.dblclick();
    assert.equal(await page.locator("#execution-panel").getAttribute("aria-busy"), "true");
    assert.equal(await page.locator("#save-draft").isDisabled(), true);
    assert.equal(posts, beforeSession + 2);
    releaseApproval();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Run approved."));
    await stage("run");
    assert.equal(await page.locator(":focus").getAttribute("id"), "job-start", "Focus follows the next permitted explicit action");
    assert.equal(calls("run").length, 0, "Approval does not launch a worker");
    assert.deepEqual(requests.filter((r) => r.url.endsWith("/approve")).map((r) => r.body.approval_key), [approvalKey, approvalKey]);
    assert.equal(await page.evaluate((id) => sessionStorage.getItem(`unio_job_${id}_approval_key`), currentJobId), approvalKey);

    // Reload only reads durable selection; the original explicit reopen path remains usable.
    const beforeReload = posts;
    await page.reload();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("restored"));
    assert.equal(posts, beforeReload);
    await page.locator("#reopen-details > summary").click();
    await page.getByLabel("Reopen a job by ID").fill(currentJobId);
    await page.getByRole("button", {name:"Reopen job",exact:true}).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job reopened."));

    // Start once reaches the real fixture service, but its response is lost.
    await page.route(origin + `/api/jobs/${currentJobId}/start`, async (route) => {await route.fetch(); await route.abort("failed");}, {times:1});
    await page.getByRole("button", {name:"Start once",exact:true}).click();
    await page.waitForFunction(() => document.getElementById("job-status").classList.contains("error"));
    assert.equal(calls("run").length, 1);
    assert.equal(await page.locator("#job-start").isDisabled(), true);
    assert.ok((await page.locator("#job-status").textContent()).includes("No retry was sent"));
    const reservationKey = await page.evaluate((id) => sessionStorage.getItem(`unio_job_${id}_reservation_key`), currentJobId);
    const afterLostStart = posts;
    await page.reload();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("No POST was retried"));
    assert.equal(posts, afterLostStart);
    assert.equal(calls("run").length, 1);
    assert.equal(await page.locator("#job-start").isVisible(), false);
    assert.equal(await page.evaluate((id) => sessionStorage.getItem(`unio_job_${id}_reservation_key`), currentJobId), reservationKey);
    await stage("verify");
    assert.equal(await page.locator("#job-review").isVisible(), false);
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    assert.equal(await page.locator("#job-cancel").isVisible(), false);

    // Preserve explicit verify, review and acceptance with real fixture transitions.
    await page.getByRole("button", {name:"Verify changes",exact:true}).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Verification response recorded."));
    await stage("review");
    assert.equal(await page.locator(":focus").getAttribute("id"), "job-review");
    assert.equal(calls("verify").length, 1);
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    await page.getByRole("button", {name:"Request review",exact:true}).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Review response recorded."));
    await stage("accept");
    assert.equal(await page.locator(":focus").getAttribute("id"), "job-accept");
    assert.equal(calls("review").length, 1);
    await inspect("ready-current-revision");
    // Keyboard-triggered acceptance is of the exact current candidate.
    await page.locator("#job-refresh").focus();
    await page.keyboard.press("Shift+Tab");
    assert.equal(await page.locator(":focus").getAttribute("id"), "job-accept");
    assert.ok(await page.locator("#job-accept").evaluate((el) => getComputedStyle(el).outlineStyle !== "none"));
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Current revision accepted."));
    assert.ok((await page.locator("#job-evidence").textContent()).includes("Current revision accepted"));
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    assert.equal(await page.locator(":focus").getAttribute("id"), "job-refresh");

    // Exercise honest unavailable, live, unknown, stale, failed checks/review and
    // revision mismatch displays with isolated GET-only view fixtures.
    const session = await page.evaluate(async () => (await fetch("/api/session")).json());
    const response = await context.request.get(origin + `/api/jobs/${currentJobId}`, {headers:{"X-Unio-Session":session.token}});
    const acceptedView = await response.json();
    async function displayFixture(label, mutate, expectedStage) {
      const view = structuredClone(acceptedView);
      view.acceptance = {state:"pending",revision:null};
      mutate(view);
      await page.route(origin + `/api/jobs/${currentJobId}`, (route) => route.fulfill({json:view}), {times:1});
      const count = posts;
      await page.locator("#job-refresh").click();
      await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job refreshed."));
      await stage(expectedStage);
      assert.equal(posts, count);
      return view;
    }
    await displayFixture("missing", (v) => {v.native_result=null;v.warnings=["native_result_unavailable"];}, "run");
    assert.ok((await page.locator("#job-evidence").textContent()).includes("Unavailable; no completion claimed"));
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    await displayFixture("live", (v) => {v.native_result.process.state="running";v.native_result.process.exit_code=null;v.native_result.ready_for_human_review=false;}, "run");
    assert.equal(await page.locator("#job-stop").isEnabled(), true);
    assert.equal(await page.locator("#job-verify").isVisible(), false);
    await inspect("live-fixture");
    await displayFixture("unknown", (v) => {v.job.state="completion_unknown";v.execution.state="completion_unknown";v.warnings=["outcome_unknown"];}, "run");
    assert.ok((await page.locator("#stage-title").textContent()).includes("unknown"));
    assert.equal(await page.locator("#job-stop").isEnabled(), true);
    assert.equal(await page.locator("#job-start").isVisible(), false);
    await displayFixture("stale", (v) => {v.native_result.stale=true;v.acceptance.state="stale";}, "verify");
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    await inspect("stale-fixture");
    await displayFixture("failed-checks", (v) => {v.native_result.validation.state="failed";v.native_result.validation.checks_failed=1;v.native_result.validation.reasons=["check_failed"];v.native_result.ready_for_human_review=false;}, "verify");
    assert.equal(await page.locator("#job-verify").isDisabled(), true);
    assert.equal(await page.locator("#job-review").isVisible(), false);
    await displayFixture("unknown-review", (v) => {v.native_result.review.state="unknown";v.native_result.review.reasons=["unknown_verdict"];v.native_result.ready_for_human_review=false;}, "review");
    assert.equal(await page.locator("#job-review").isDisabled(), true);
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    await displayFixture("mismatched-revision", (v) => {v.native_result.review.revision.candidate_commit="f".repeat(40);}, "review");
    assert.equal(await page.locator("#job-accept").isVisible(), false);
    await page.locator("#job-refresh").click();
    await page.waitForFunction(() => document.getElementById("stage-title").textContent.includes("Current revision accepted"));
    // Failed GET keeps context but clearly labels cached evidence.
    await page.route(origin + `/api/jobs/${currentJobId}`, (route) => route.fulfill({status:503,json:{schema_version:1,error:"native_unavailable"}}), {times:1});
    await page.locator("#job-refresh").click();
    await page.waitForFunction(() => document.getElementById("job-status").classList.contains("error"));
    assert.ok((await page.locator("#result-title").textContent()).includes("Last observed evidence"));
    assert.equal(await page.getByLabel("Reopen a job by ID").inputValue(), currentJobId);
    assert.equal(calls("run").length, 1);
    assert.equal(calls("review").length, 1);
    // A waiting job can be cancelled, and a live fixture job can be stopped
    // only through its exact binding. These are additional explicit fixture tasks.
    async function prepareAnother(request, loseResponse = false) {
      await page.locator("#draft-request").fill(request);
      await page.locator("#save-draft").click();
      await page.waitForFunction(() => document.getElementById("draft-status").textContent.includes("draft saved."));
      if (loseResponse) await page.route(origin + "/api/jobs", async (route) => {
        if (route.request().method() === "POST") {await route.fetch(); await route.abort("failed");}
        else await route.continue();
      }, {times:1});
      await page.locator("#job-prepare").click();
      if (loseResponse) {
        await page.waitForFunction(() => document.getElementById("job-status").classList.contains("error"));
        assert.equal(await page.locator("#job-prepare").isDisabled(), true);
        const count = posts;
        const originalKey = requests.filter((r) => r.url === origin + "/api/jobs" && r.method === "POST").at(-1).body.request_key;
        await page.reload();
        await page.waitForFunction(() => !document.getElementById("job-preview").hidden);
        assert.equal(posts, count, "Lost prepare recovery only reads existing intent");
        assert.ok((await page.locator("#job-request-text").textContent()).includes(request));
        assert.equal(await page.evaluate((key) => Object.values(sessionStorage).includes(key), originalKey), true);
      } else await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job prepared."));
      return await page.locator("#job-id").inputValue();
    }
    const cancelId = await prepareAnother("Cancel this waiting local fixture task.", true);
    assert.equal(await page.locator("#job-stop").isVisible(), false);
    await page.locator("#job-cancel").click();
    await page.waitForFunction(() => document.getElementById("stage-title").textContent === "Job cancelled");
    assert.equal(calls("run").length, 1);
    assert.equal(calls("kill").length, 0);
    assert.equal(await page.locator("#job-start").isVisible(), false);
    const stopId = await prepareAnother("Stop only this live local fixture task.");
    assert.notEqual(stopId, cancelId);
    await page.locator("#job-approve").click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Run approved."));
    fs.writeFileSync(path.join(fixture,"hold.marker"), "local fixture stays running");
    await page.locator("#job-start").click();
    await page.waitForFunction(() => document.getElementById("stage-title").textContent.includes("running"));
    assert.equal(await page.locator("#job-cancel").isVisible(), false);
    assert.equal(await page.locator("#job-verify").isVisible(), false);
    await page.locator("#job-stop").click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Stop response recorded."));
    assert.deepEqual(calls("kill"), [["kill", "ui-" + stopId]]);
    assert.ok((await page.locator("#job-evidence").textContent()).includes("failed · exit 137"));
    assert.equal(await page.locator("#job-start").isVisible(), false);
    assert.equal(await page.locator("#job-stop").isVisible(), false);
    assert.deepEqual(failures, []);
    assert.ok(requests.every((r) => r.url.startsWith(origin + "/") && ["GET","POST"].includes(r.method)));
    assert.ok(requests.filter((r) => r.method === "POST").every((r) => /\/api\/(plans|jobs)/.test(r.url)));
    if (process.env.M2_SCREENSHOTS) fs.writeFileSync(path.join(process.env.M2_SCREENSHOTS,"execution-audit.json"), JSON.stringify({providerCalls:0,fixture,observations:visual},null,2));
    console.log("Execution browser: literal exact preview, all explicit stages, deterministic 403 interception with gated response observer, approve double-click/busy lock, session rotation and lost-start response/reload GET-only recovery, stable opaque keys, native readiness/revision guards, honest failed/stale/unknown/live states, keyboard focus, desktop/narrow wrapping and no provider calls passed");
  } finally {
    if (context) await context.close();
    if (browser) await browser.close();
    if (child.exitCode === null) {
      child.kill("SIGINT");
      await Promise.race([
        once(child, "exit"),
        new Promise((resolve) => setTimeout(resolve, 2000)),
      ]);
      if (child.exitCode === null) child.kill("SIGKILL");
    }
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

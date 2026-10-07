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
import json, sys, os, hashlib, subprocess, fcntl
root = os.path.dirname(sys.argv[0])
# Observer and execution fixtures can log concurrently. Lock before opening
# the append handle, and publish the complete record before releasing it.
with open(os.path.join(root, 'calls.lock'), 'a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    with open(os.path.join(root, 'calls.jsonl'), 'a') as f:
        f.write(json.dumps(sys.argv[1:]) + chr(10))
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
    context,
    page;
  let phase = "startup";
  const networkTrace = [];
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
    page = await context.newPage();
    const startedAt = performance.now();
    const requestTimes = new WeakMap();
    const traceRequest = (event, request, status) => {
      const route = new URL(request.url()).pathname.replace(/\/[0-9a-f]{32}(?=\/|$)/g, "/:id");
      if (!/^\/api\/(session|plans(?:\/:id)?|jobs(?:\/:id(?:\/(approve|start|verify|review|accept|stop|cancel))?)?)$/.test(route)) return;
      const now = performance.now();
      if (event === "request") requestTimes.set(request, now);
      networkTrace.push({event, route, method:request.method(), status,
        atMs:Math.round(now - startedAt), elapsedMs:Math.round(now - requestTimes.get(request))});
      if (networkTrace.length > 80) networkTrace.shift();
    };
    page.on("request", (request) => traceRequest("request", request));
    page.on("response", (response) => traceRequest("response", response.request(), response.status()));
    page.on("requestfinished", (request) => traceRequest("finished", request));
    page.on("requestfailed", (request) => traceRequest("failed", request));
    await page.addInitScript(() => {
      // Record fixed status labels and capability booleans, never event detail,
      // request/response bodies, storage, tokens or opaque action keys.
      const labels = ["Recording run approval", "Session refreshed", "session unavailable",
        "Refreshing job evidence", "Job refreshed", "Job context restored",
        "An earlier action response was not confirmed", "Job prepared",
        "Run approved", "Response not confirmed", "Saved execution context unavailable"];
      const label = (node) => labels.find((value) => node && node.textContent.startsWith(value)) || "other";
      const trace = [];
      const record = (data) => {
        trace.push({atMs:Math.round(performance.now()), ...data});
        if (trace.length > 80) trace.shift();
      };
      window.__executionDiagnostics = () => ({
        trace, documentAgeMs:Math.round(performance.now()),
        status:label(document.getElementById("job-status")),
        statusError:document.getElementById("job-status")?.classList.contains("error"),
        busy:document.getElementById("execution-panel")?.getAttribute("aria-busy"),
        panelHidden:document.getElementById("execution-panel")?.hidden,
        approveDisabled:document.getElementById("job-approve")?.disabled,
        refreshDisabled:document.getElementById("job-refresh")?.disabled,
      });
      for (const name of ["refresh-session", "unio-session", "execution-busy", "draft-idle"])
        document.addEventListener(name, (event) => record({event:name,
          ...(name === "unio-session" ? {execution:event.detail.execution === true,
            manualDrafts:event.detail.manual_drafts === true} : {}),
          ...(name === "execution-busy" ? {busy:event.detail === true} : {}),
        }));
      document.addEventListener("DOMContentLoaded", () => {
        const node = document.getElementById("job-status");
        new MutationObserver(() => record({status:label(node), error:node.classList.contains("error")}))
          .observe(node, {childList:true, subtree:true, characterData:true});
      });
    });
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

    // Take a locked snapshot of the exact fixture call evidence. Do not ignore
    // malformed records or read a partially published concurrent append.
    const calls = (verb) => JSON.parse(execFileSync("python3", ["-B", "-c", `
import fcntl, json, os, sys
with open(os.path.join(sys.argv[1], 'calls.lock'), 'a') as lock:
    fcntl.flock(lock, fcntl.LOCK_SH)
    with open(os.path.join(sys.argv[1], 'calls.jsonl')) as records:
        print(json.dumps([json.loads(line) for line in records]))
`, fixture], {encoding:"utf8", env:{...process.env, PYTHONDONTWRITEBYTECODE:"1"}}))
      .filter((argv) => argv[0] === verb);
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
    const sessionUrl = origin + "/api/session";
    let releaseSession;
    const sessionGate = new Promise((resolve) => releaseSession = resolve);
    await page.route(sessionUrl, async (route) => {
      assert.equal(route.request().method(), "GET");
      await sessionGate;
      await route.continue();
    }, {times:1});
    const pendingSession = page.waitForRequest((request) => request.url() === sessionUrl && request.method() === "GET");
    const refusedApproval = page.waitForResponse((response) => response.url() === approvalUrl && response.request().method() === "POST");
    phase = "403 refresh pending";
    await approve.click();
    assert.equal((await refusedApproval).status(), 403, "The intended approval response was injected");
    assert.equal(interceptedApprovals.length, 1, "Exactly one approval POST reached the 403 interceptor");
    await pendingSession;
    assert.equal(await page.locator("#execution-panel").getAttribute("aria-busy"), "true");
    assert.equal(await approve.isDisabled(), true);
    assert.equal(await page.locator("#job-refresh").isDisabled(), true);
    assert.equal(await page.locator("#save-draft").isDisabled(), true);
    assert.ok(!(await page.locator("#job-status").textContent()).includes("Session refreshed"),
      "Recovery cannot be announced before the held session response");
    assert.equal(posts, beforeSession + 1);
    assert.equal(calls("run").length, 0);
    assert.equal(calls("review").length, 0);
    const refreshedSession = page.waitForResponse((response) => response.url() === sessionUrl && response.request().method() === "GET");
    phase = "403 refresh completion";
    releaseSession();
    assert.equal((await refreshedSession).status(), 200, "The held refresh reaches the real session endpoint");
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Session refreshed"));
    assert.equal(await page.locator("#execution-panel").getAttribute("aria-busy"), "false");
    assert.equal(await page.locator("#job-refresh").isEnabled(), true);
    assert.equal(observedJobId, undefined, "Session recovery does not depend on the delayed observer");
    assert.equal(sessionReads(), beforeSessionReads + 1, "403 explicitly refreshes the session once");
    assert.equal(posts, beforeSession + 1);
    assert.equal(await approve.isDisabled(), true);
    const approvalKey = await page.evaluate((id) => sessionStorage.getItem(`unio_job_${id}_approval_key`), currentJobId);
    assert.match(approvalKey, /^[0-9a-f]{32}$/);
    assert.ok(interceptedApprovals[0].approval_key === approvalKey, "Intercepted approval carries the saved key");
    assert.ok(requests.find((r) => r.url.endsWith("/approve")).body.approval_key === approvalKey,
      "The exact intended approval request carries the saved key");
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

    // A second explicit approval is refused, and this time session recovery
    // fails. Hold that GET too: both pending and failed states must block writes.
    const savedIntent = () => page.evaluate(({jobId, draftId}) => [
      "unio_execution_context", "unio_pending_operation",
      `unio_action_${jobId}_approve`, `unio_job_${jobId}_approval_key`,
      `unio_draft_${draftId}_request`,
    ].map((key) => sessionStorage.getItem(key)), {jobId:currentJobId, draftId:preparedView.job.draft_id});
    const originalIntent = await savedIntent();
    const beforeFailedRefresh = posts;
    const beforeFailedSessionReads = sessionReads();
    const beforeFailedRequests = requests.length;
    let releaseFailedSession;
    const failedSessionGate = new Promise((resolve) => releaseFailedSession = resolve);
    await page.route(sessionUrl, async (route) => {
      assert.equal(route.request().method(), "GET");
      await failedSessionGate;
      await route.fulfill({status:503,json:{schema_version:1,error:"storage_unavailable"}});
    }, {times:1});
    const failedApprovals = [];
    await page.route(approvalUrl, (route) => {
      assert.equal(route.request().method(), "POST");
      assert.equal(route.request().url(), approvalUrl);
      failedApprovals.push(route.request().postDataJSON());
      return route.fulfill({status:403,json:{schema_version:1,error:"session_refused"}});
    }, {times:1});
    const failedApproval = page.waitForResponse((response) => response.url() === approvalUrl && response.request().method() === "POST");
    const failedSessionRequest = page.waitForRequest((request) => request.url() === sessionUrl && request.method() === "GET");
    phase = "failed refresh pending";
    await approve.click();
    assert.equal((await failedApproval).status(), 403);
    assert.equal(failedApprovals.length, 1);
    assert.ok(failedApprovals[0].approval_key === approvalKey, "Failed recovery keeps the same explicit approval key");
    await failedSessionRequest;
    const attemptBlockedWrites = () => page.evaluate(() => {
      for (const action of ["prepare", "approve", "start", "verify", "review", "accept", "stop", "cancel"])
        document.getElementById("job-" + action).dispatchEvent(new MouseEvent("click", {bubbles:true}));
      document.getElementById("draft-form").dispatchEvent(new Event("submit", {bubbles:true, cancelable:true}));
    });
    assert.equal(await page.locator("#execution-panel").getAttribute("aria-busy"), "true");
    assert.equal(await approve.isDisabled(), true);
    assert.equal(await page.locator("#save-draft").isDisabled(), true);
    await attemptBlockedWrites();
    assert.equal(posts, beforeFailedRefresh + 1, "Pending refresh blocks repeated execution and draft writes");
    assert.ok(JSON.stringify(await savedIntent()) === JSON.stringify(originalIntent), "Pending refresh preserves the complete saved intent");
    const failedSessionResponse = page.waitForResponse((response) => response.url() === sessionUrl && response.request().method() === "GET");
    phase = "failed refresh completion";
    releaseFailedSession();
    assert.equal((await failedSessionResponse).status(), 503, "The session GET failure is mandatory");
    await page.waitForFunction(() => document.getElementById("mode-label").textContent === "Mode unavailable"
      && document.getElementById("execution-panel").getAttribute("aria-busy") === "false"
      && document.getElementById("job-status").classList.contains("error"));
    assert.ok((await page.locator("#draft-status").textContent()).includes("Reload to reconnect"));
    assert.equal(await page.locator("#draft-status").isVisible(), true);
    assert.equal(await page.locator("#job-approve").isDisabled(), true);
    assert.equal(await page.locator("#save-draft").isDisabled(), true);
    assert.equal(await page.locator("#job-refresh").isDisabled(), true);
    assert.equal(await page.locator("#job-start").isVisible(), false);
    assert.equal(await page.locator("#job-review").isVisible(), false);
    assert.equal(await page.getByLabel("Describe the work to save").inputValue(), literal);
    assert.equal(await page.locator("#job-request-text").textContent(), literal);
    await attemptBlockedWrites();
    assert.equal(posts, beforeFailedRefresh + 1, "Failed refresh cannot retry writes or spend allowance");
    assert.equal(sessionReads(), beforeFailedSessionReads + 1, "Failed session refresh is not retried automatically");
    assert.ok(JSON.stringify(await savedIntent()) === JSON.stringify(originalIntent), "Failed refresh preserves request, action inputs, keys and selection");
    assert.equal(calls("run").length, 0);
    assert.equal(calls("review").length, 0);

    // Reload is an explicit user recovery. It reads the saved job and intent,
    // restores the literal saved request and never replays the refused POST.
    phase = "failed refresh explicit reload";
    await page.reload();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("No POST was retried")
      && !document.getElementById("job-approve").disabled);
    assert.equal(await page.locator("#mode-label").textContent(), "Live execution");
    assert.equal(await page.locator("#job-request-text").textContent(), literal);
    assert.equal(await page.locator("#job-id").inputValue(), currentJobId);
    assert.equal(posts, beforeFailedRefresh + 1);
    assert.equal(sessionReads(), beforeFailedSessionReads + 2, "Only explicit reload reconnects the failed session");
    assert.ok(JSON.stringify(await savedIntent()) === JSON.stringify(originalIntent), "Explicit reload reads without replacing saved action intent");
    assert.deepEqual(requests.slice(beforeFailedRequests).filter((r) => r.url !== origin + "/api/activity" && r.url.includes("/api/"))
      .map((r) => ({method:r.method, route:r.url === approvalUrl ? "approve" : r.url === sessionUrl ? "session" : "job"})),
      [{method:"POST",route:"approve"}, {method:"GET",route:"session"}, {method:"GET",route:"session"}, {method:"GET",route:"job"}],
      "Failed refresh and explicit recovery use only the refused approval and capability/job reads");
    assert.equal(calls("run").length, 0);
    assert.equal(calls("review").length, 0);
    await stage("approve");

    // Double click approve protection, with explicit busy accessibility.
    phase = "explicit next approval";
    let releaseApproval;
    const approvalGate = new Promise((resolve) => releaseApproval = resolve);
    await page.route(origin + `/api/jobs/${currentJobId}/approve`, async (route) => {await approvalGate; await route.continue();}, {times:1});
    await approve.dblclick();
    assert.equal(await page.locator("#execution-panel").getAttribute("aria-busy"), "true");
    assert.equal(await page.locator("#save-draft").isDisabled(), true);
    assert.equal(posts, beforeSession + 3);
    releaseApproval();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Run approved."));
    await stage("run");
    assert.equal(await page.locator(":focus").getAttribute("id"), "job-start", "Focus follows the next permitted explicit action");
    assert.equal(calls("run").length, 0, "Approval does not launch a worker");
    const approvalKeys = requests.filter((r) => r.url.endsWith("/approve")).map((r) => r.body.approval_key);
    assert.ok(approvalKeys.length === 3 && approvalKeys.every((key) => key === approvalKey),
      "Both refused approvals and the explicit next approval carry the original key");
    assert.ok(await page.evaluate((id) => sessionStorage.getItem(`unio_job_${id}_approval_key`), currentJobId) === approvalKey,
      "Successful explicit approval retains the original key");

    // Reload only reads durable selection; the original explicit reopen path remains usable.
    phase = "approved reload and reopen";
    const beforeReload = posts;
    await page.reload();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("restored"));
    assert.equal(posts, beforeReload);
    await page.locator("#reopen-details > summary").click();
    await page.getByLabel("Reopen a job by ID").fill(currentJobId);
    await page.getByRole("button", {name:"Reopen job",exact:true}).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job reopened."));

    // Start once reaches the real fixture service, but its response is lost.
    phase = "lost start and reload";
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
    phase = "verify review accept";
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
    phase = "readiness fixtures";
    const session = await page.evaluate(async () => (await fetch("/api/session")).json());
    const response = await context.request.get(origin + `/api/jobs/${currentJobId}`, {headers:{"X-Unio-Session":session.token}});
    const acceptedView = await response.json();
    async function displayFixture(label, mutate, expectedStage) {
      phase = "readiness fixture: " + label;
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
    phase = "failed job GET";
    await page.route(origin + `/api/jobs/${currentJobId}`, (route) => route.fulfill({status:503,json:{schema_version:1,error:"native_unavailable"}}), {times:1});
    await page.locator("#job-refresh").click();
    await page.waitForFunction(() => document.getElementById("job-status").classList.contains("error"));
    assert.ok((await page.locator("#result-title").textContent()).includes("Last observed evidence"));
    assert.equal(await page.getByLabel("Reopen a job by ID").inputValue(), currentJobId);
    assert.equal(calls("run").length, 1);
    assert.equal(calls("review").length, 1);
    // A waiting job can be cancelled, and a live fixture job can be stopped
    // only through its exact binding. These are additional explicit fixture tasks.
    phase = "lost prepare and cancel";
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
    phase = "explicit start and stop";
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
    console.log("Execution browser: literal exact preview, all explicit stages, deterministic 403 interception with gated response observer and session GET, mandatory failed-refresh intent/write guards and explicit GET-only reload recovery, approve double-click/busy lock, session rotation and lost-start response/reload GET-only recovery, stable opaque keys, native readiness/revision guards, honest failed/stale/unknown/live states, keyboard focus, desktop/narrow wrapping and no provider calls passed");
  } catch (error) {
    try {
      const ui = page && !page.isClosed() ? await page.evaluate(() => window.__executionDiagnostics?.()) : null;
      console.error("Execution browser sanitized diagnostics:", JSON.stringify({phase, networkTrace, ui}));
    } catch (_) {
      console.error("Execution browser sanitized diagnostics:", JSON.stringify({phase, networkTrace, ui:"unavailable"}));
    }
    // Preserve the first assertion/timeout and its original stack; diagnostics
    // neither retry a scenario nor replace the observed failure.
    throw error;
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

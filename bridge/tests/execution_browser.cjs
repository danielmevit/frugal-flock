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
args = sys.argv[1:]
if args[0] == 'watch':
    print(json.dumps(dict(schema_version=1,observed_at='2026-10-05T00:00:00Z',stopped=False,agents=[],results=[],retries=[],recent_events=[],warnings=[],evidence='recorded only')))
elif args[0] == 'run':
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
               current_revision=revision, process=dict(state='succeeded', exit_code=0, revision=revision),
               validation=dict(state='passed', scope='OK', checks_run=1, checks_failed=0, reasons=[], revision=revision),
               review=dict(state='approved', reviewer='r1', process_exit_code=0, material_complete=True, reasons=[], revision=revision),
               stale=False, ready_for_human_review=True)
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
  const { execSync } = require("node:child_process");
  execSync(`python3 "${setupPy}"`);

  
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
    { stdio: ["ignore", "pipe", "pipe"] },
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
      viewport: { width: 1440, height: 1000 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const failures = [],
      requests = [];
    let posts = 0;
    
    page.on("console", msg => console.log("PAGE LOG:", msg.text()));
    page.on("pageerror", (error) => failures.push(error.message));
    page.on("request", (request) => {
      requests.push({ url: request.url(), method: request.method() });
      if (request.method() === "POST") posts++;
    });
    
    let currentJobId;
    page.on("response", async (response) => {
      const url = response.url();
      if (url.endsWith("/api/jobs") && response.request().method() === "POST" && response.ok()) {
        try {
          const json = await response.json();
          if (json && json.job && json.job.id) currentJobId = json.job.id;
        } catch(e) {}
      }
    });

    await page.goto(origin);
    
    await page.waitForFunction(() => !document.getElementById("manual-drafts").hidden);
    
    // Create draft
    await page.getByLabel("Describe the work to save").fill("Malicious <script>alert(1)</script>");
    await page.getByRole("button", { name: "Save draft", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("draft-status").textContent.includes("draft saved."));
    
    // Prepare
    await page.getByRole("button", { name: "Prepare", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job prepared."));
    
    // Verify preview
    assert.ok(await page.locator("#job-preview").isVisible());
    assert.ok((await page.locator("#job-preview-text").textContent()).includes("Malicious"));
    
    // Double click approve protection
    const approveBtn = page.getByRole("button", { name: "Approve", exact: true });
    await approveBtn.dblclick();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job approved."));
    
    // Reopen job by ID
    await page.reload();
    await page.getByLabel("Reopen a job by ID").fill(currentJobId);
    await page.getByRole("button", { name: "Reopen job", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job reopened."));
    
    // Start job
    await page.getByRole("button", { name: "Start", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job started."));
    
    // Verify
    await page.getByRole("button", { name: "Verify", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job verify done."));
    
    // Review
    await page.getByRole("button", { name: "Review", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job review done."));
    
    // Accept
    await page.getByRole("button", { name: "Accept", exact: true }).click();
    await page.waitForFunction(() => document.getElementById("job-status").textContent.includes("Job accepted."));
    
    console.log("Basic execution test complete");
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
